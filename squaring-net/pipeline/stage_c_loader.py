#!/usr/bin/env python3
"""
Stage C -- loader (SPEC-1).

Loads one order's Stage A/B output into Postgres:
  1. graphs.csv (Stage A)                  -> graphs table (two-pass: rows first,
                                               then dual_of resolved by hash_code join)
  2. sqt's hash-tagged tablecode files (Stage B) -> dissections table, joining
     graph_hashcode -> graphs.graph_id (graph_id NOT NULL, never skipped)
  3. degenerate counts + type pivot         -> order_counts (SPEC-2 gate bookkeeping)

Enforced at load, per SPEC-1 Stage C:
  - graph_id NOT NULL (hard fail if a hash doesn't resolve -- no row is loaded
    with a missing link, the file-boundary corruption never recurs)
  - bouwkamp_code UNIQUE per partition (idx_dissections_bouwkamp does this;
    ON CONFLICT DO NOTHING here is the belt-and-braces dedup, not silent data loss)
  - area check (sum of element squares == width * height) -- reject, don't load
  - is_crossed / corner_elements / boundary_square_indices computed once via
    squaringlib.geometry.place_elements(), same call the renderer uses (SPEC-4)

Bulk-loads via psycopg's COPY protocol (text-format COPY, not row INSERT) --
satisfies SPEC-1's "COPY, never row INSERT" by using the same PG COPY path;
hand-rolling the binary sub-format wasn't warranted at this row scale.
"""
import argparse
import json
import os
import re
from pathlib import Path

import psycopg

from squaringlib.geometry import (
    boundary_square_indices,
    corner_elements,
    is_crossed,
    place_elements,
)

# filename suffix -> (simple, perfect, is_square, d_type)
TYPE_MAP = {
    "spss": (True, True, True, "SPSS"),
    "spsr": (True, True, False, "SPSR"),
    "siss": (True, False, True, "SISS"),
    "sisr": (True, False, False, "SISR"),
    "cpss": (False, True, True, "CPSS"),
    "cpsr": (False, True, False, "CPSR"),
    "ciss": (False, False, True, "CISS"),
    "cisr": (False, False, False, "CISR"),
}


def db_connect():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        dbname=os.environ.get("PGDATABASE", "squaring_net"),
        user=os.environ.get("PGUSER", "squaring_admin"),
        password=os.environ["PGPASSWORD"],
    )


def continued_fraction(width, height):
    """Continued-fraction terms of width/height -- the Stern-Brocot path. NULL (None) for squares."""
    if width == height:
        return None
    a, b = width, height
    terms = []
    while b:
        terms.append(a // b)
        a, b = b, a % b
    return terms


def load_graphs(conn, order_dir):
    graphs_csv = order_dir / "graphs.csv"
    rows = []
    with open(graphs_csv) as fh:
        next(fh)  # header
        for line in fh:
            hash_code, num_vertices, num_edges, is_self_dual, dual_of_hash, source_class = \
                line.rstrip("\n").split(",")
            rows.append((hash_code, int(num_edges), is_self_dual == "True", dual_of_hash or None))

    with conn.cursor() as cur:
        with cur.copy("COPY graphs (hash_code, num_edges, is_self_dual) FROM STDIN") as copy:
            for hash_code, num_edges, is_self_dual, _ in rows:
                copy.write_row((hash_code, num_edges, is_self_dual))

        # second pass: resolve dual_of by hash_code join, now that every graph has a graph_id
        cur.execute("""
            CREATE TEMP TABLE _dual_links (hash_code TEXT, dual_of_hash_code TEXT) ON COMMIT DROP
        """)
        with cur.copy("COPY _dual_links (hash_code, dual_of_hash_code) FROM STDIN") as copy:
            for hash_code, _, _, dual_of_hash in rows:
                if dual_of_hash:
                    copy.write_row((hash_code, dual_of_hash))
        cur.execute("""
            UPDATE graphs g SET dual_of = p.graph_id
            FROM _dual_links dl JOIN graphs p ON p.hash_code = dl.dual_of_hash_code
            WHERE g.hash_code = dl.hash_code
        """)
    conn.commit()
    return len(rows)


def hash_to_graph_id(conn, num_edges):
    with conn.cursor() as cur:
        cur.execute("SELECT hash_code, graph_id FROM graphs WHERE num_edges = %s", (num_edges,))
        return dict(cur.fetchall())


TABLECODE_LINE = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$")


def parse_tablecode_file(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = TABLECODE_LINE.match(line)
            if not m:
                raise ValueError(f"{path}: unparseable line: {line!r}")
            hash_code, order, width, height, rest = m.groups()
            elements = [int(x) for x in rest.split()]
            yield hash_code, int(order), int(width), int(height), elements


def load_order(order, out_dir):
    order_dir = Path(out_dir) / f"order={order}"
    provenance = json.loads((order_dir / "provenance.json").read_text())

    conn = db_connect()
    try:
        num_graphs_loaded = load_graphs(conn, order_dir)
        hash_map = hash_to_graph_id(conn, provenance["num_edges"])

        degn_count = 0
        rejected_area_check = []
        missing_graph_id = []
        rows_to_copy = []

        for class_info in provenance["classes"]:
            class_stem = class_info["file"]  # e.g. class_v13_f11.planar_code
            for suffix, (simple, perfect, is_square, d_type) in TYPE_MAP.items():
                type_file = order_dir / f"{class_stem}-{suffix}.txt"
                if not type_file.exists():
                    continue
                for hash_code, o, width, height, elements in parse_tablecode_file(type_file):
                    if sum(e * e for e in elements) != width * height:
                        rejected_area_check.append((type_file.name, hash_code, width, height))
                        continue
                    graph_id = hash_map.get(hash_code)
                    if graph_id is None:
                        missing_graph_id.append((type_file.name, hash_code))
                        continue

                    placed = place_elements(elements, width, height)
                    bouwkamp_code = " ".join(str(e) for e in elements).encode()
                    rows_to_copy.append((
                        order, graph_id, d_type, simple, perfect, is_square,
                        width, height, bouwkamp_code,
                        continued_fraction(width, height),
                        is_crossed(width, height, placed),
                        corner_elements(width, height, placed),
                        boundary_square_indices(width, height, placed),
                    ))

            degen_file = order_dir / f"{class_stem}-degenerate.txt"
            if degen_file.exists():
                degn_count += sum(1 for _ in parse_tablecode_file(degen_file))

        if missing_graph_id:
            raise RuntimeError(
                f"order {order}: {len(missing_graph_id)} tablecode rows have no matching "
                f"graphs.hash_code (first: {missing_graph_id[:5]}) -- refusing to load any "
                f"row with a NULL graph_id; fix the graph-linkage gap and re-run"
            )

        with conn.cursor() as cur:
            # COPY into an unlogged staging table first: COPY itself can't express
            # ON CONFLICT, and SPEC-1 frames bouwkamp_code UNIQUE as a "cross-class
            # dedup safety net" -- a duplicate across classes is expected on occasion
            # and should be silently rejected, not crash the load.
            cur.execute("""
                CREATE TEMP TABLE _dissections_stage (
                    order_val SMALLINT, graph_id BIGINT, d_type CHAR(4),
                    simple BOOLEAN, perfect BOOLEAN, is_square BOOLEAN,
                    width BIGINT, height BIGINT, bouwkamp_code BYTEA,
                    ratio_cf INTEGER[], is_crossed BOOLEAN,
                    corner_elements SMALLINT[], boundary_square_indices SMALLINT[]
                ) ON COMMIT DROP
            """)
            with cur.copy("""
                COPY _dissections_stage (order_val, graph_id, d_type, simple, perfect, is_square,
                                          width, height, bouwkamp_code, ratio_cf,
                                          is_crossed, corner_elements, boundary_square_indices)
                FROM STDIN
            """) as copy:
                for row in rows_to_copy:
                    copy.write_row(row)

            cur.execute("""
                INSERT INTO dissections (order_val, graph_id, d_type, simple, perfect, is_square,
                                          width, height, bouwkamp_code, ratio_cf,
                                          is_crossed, corner_elements, boundary_square_indices)
                SELECT order_val, graph_id, d_type, simple, perfect, is_square,
                       width, height, bouwkamp_code, ratio_cf,
                       is_crossed, corner_elements, boundary_square_indices
                FROM _dissections_stage
                ON CONFLICT (order_val, bouwkamp_code) DO NOTHING
            """)
            duplicate_bouwkamp_codes = len(rows_to_copy) - cur.rowcount

            cur.execute(
                "SELECT d_type, count(*) FROM dissections WHERE order_val = %s GROUP BY d_type",
                (order,),
            )
            type_counts = dict(cur.fetchall())

            cur.execute("""
                INSERT INTO order_counts
                    (order_val, d_type_counts, degn_count, graph_count,
                     tool_version, plantri_version, plantri_classes_fed, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                ON CONFLICT (order_val) DO UPDATE SET
                    d_type_counts = EXCLUDED.d_type_counts,
                    degn_count = EXCLUDED.degn_count,
                    graph_count = EXCLUDED.graph_count,
                    tool_version = EXCLUDED.tool_version,
                    plantri_version = EXCLUDED.plantri_version,
                    plantri_classes_fed = EXCLUDED.plantri_classes_fed,
                    status = 'pending',
                    recorded_at = now()
            """, (
                order, json.dumps(type_counts), degn_count, num_graphs_loaded,
                "sqt v4.3", provenance["plantri_version"],
                [f"v{c['v']}_f{c['f']}" for c in provenance["classes"]],
            ))
        conn.commit()

        if rejected_area_check:
            print(f"  WARNING: {len(rejected_area_check)} rows rejected on area check "
                  f"(first: {rejected_area_check[:5]})")
        if duplicate_bouwkamp_codes:
            print(f"  NOTE: {duplicate_bouwkamp_codes} rows rejected as duplicate "
                  f"(order_val, bouwkamp_code) -- SPEC-1's cross-class dedup safety net")

        return {
            "order": order, "graphs_loaded": num_graphs_loaded,
            "dissections_loaded": sum(type_counts.values()), "degn_count": degn_count,
            "type_counts": type_counts, "area_check_rejects": len(rejected_area_check),
            "duplicate_bouwkamp_codes": duplicate_bouwkamp_codes,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Stage C -- loader (SPEC-1)")
    parser.add_argument("order", type=int)
    parser.add_argument("--out-dir", default="data/planar_code")
    args = parser.parse_args()

    result = load_order(args.order, args.out_dir)
    print(f"order {result['order']}: loaded {result['graphs_loaded']} graphs, "
          f"{result['dissections_loaded']} dissections, {result['degn_count']} degenerate "
          f"(discarded), {result['area_check_rejects']} area-check rejects, "
          f"{result['duplicate_bouwkamp_codes']} duplicate bouwkamp_code rejects")
    print(f"  type counts: {result['type_counts']}")


if __name__ == "__main__":
    main()
