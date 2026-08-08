#!/usr/bin/env python3
"""
Stage A -- plantri driver (SPEC-1).

For a target order k (edges e = k+1), enumerate every valid (v, f) planar-map
class -- ceil((e+6)/3) <= v <= floor(2e/3), f = e+2-v -- and generate the
v >= f side directly via plantri. The v < f side is never separately run
through plantri; SPEC-1: "derive the f>v duals post-generation rather than
asking plantri for cubic graphs directly (plantri makes triangulations far
more cheaply; the dual is the same dissection rotated 90 degrees)".

v == f is the self-dual boundary: Euler's formula fixes f = e+2-v for every
graph plantri emits at fixed (v, e), so for v == f every graph's dual has the
same vertex count as the class itself -- non-self-dual partners show up
*within the same plantri run* and must be deduped by canonical hash rather
than tagged-and-derived like the v > f classes.

Output per order, under <out-dir>/order=<order>/:
  class_v{v}_f{f}.planar_code        -- raw plantri output, one file per v>=f class
  class_v{v}_f{f}.planar_code.hashes.txt
                                      -- one nauty canonical hash per line, in the
                                         same raw file order plantri (and so sqt)
                                         reads the graphs -- this is Stage B's graph
                                         linkage sidecar (SPEC-1's "one allowed change")
  graphs.csv                         -- one row per graph (generated + elided dual),
                                         feeds the Stage C loader
  provenance.json                    -- plantri version + exact invocation per class
"""
import argparse
import csv
import json
import subprocess
from pathlib import Path

from squaringlib.planar import (
    PLANTRI_BIN,
    canonical_hash_codes_batch,
    dual_rotation_system,
    run_plantri_sharded,
    valid_vf_classes,
    write_planar_code,
)

GRAPH_FIELDS = [
    "hash_code", "num_vertices", "num_edges",
    "is_self_dual", "dual_of_hash_code", "source_class",
]


def plantri_version():
    proc = subprocess.run([PLANTRI_BIN, "--help"], capture_output=True)
    first_line = (proc.stdout or proc.stderr).decode().splitlines()[0]
    return first_line.strip()


def process_v_gt_f_class(v, f, e, shards=1):
    """v > f: generate directly, derive the (f, v) dual for every graph. No dedup needed (dual vertex count f != v)."""
    invocation = [PLANTRI_BIN, "-p", "-c3", f"-e{e}:{e}", str(v)]
    if shards > 1:
        invocation.append(f"[sharded x{shards}]")
    rotations = run_plantri_sharded(v, e=e, extra_args=["-c3"], shards=shards)
    raw = write_planar_code(rotations)

    hashes = canonical_hash_codes_batch(rotations)
    dual_hashes = canonical_hash_codes_batch([dual_rotation_system(r) for r in rotations])

    rows = []
    for h, h_dual in zip(hashes, dual_hashes):
        rows.append({
            "hash_code": h, "num_vertices": v, "num_edges": e,
            "is_self_dual": False, "dual_of_hash_code": "", "source_class": f"v{v}_f{f}",
        })
        rows.append({
            "hash_code": h_dual, "num_vertices": f, "num_edges": e,
            "is_self_dual": False, "dual_of_hash_code": h, "source_class": f"v{f}_f{v}_derived",
        })
    return raw, invocation, rows, hashes


def process_v_eq_f_class(v, e, shards=1):
    """v == f: dedup self-dual and paired graphs by canonical hash within the single (possibly sharded) plantri run."""
    invocation = [PLANTRI_BIN, "-p", "-c3", f"-e{e}:{e}", str(v)]
    if shards > 1:
        invocation.append(f"[sharded x{shards}]")
    rotations = run_plantri_sharded(v, e=e, extra_args=["-c3"], shards=shards)
    raw = write_planar_code(rotations)

    hashes = canonical_hash_codes_batch(rotations)
    dual_hashes = canonical_hash_codes_batch([dual_rotation_system(r) for r in rotations])
    hash_set = set(hashes)

    rows = []
    seen = set()
    for h, h_dual in zip(hashes, dual_hashes):
        if h in seen:
            continue
        if h == h_dual:
            rows.append({
                "hash_code": h, "num_vertices": v, "num_edges": e,
                "is_self_dual": True, "dual_of_hash_code": "", "source_class": f"v{v}_f{v}",
            })
            seen.add(h)
        elif h_dual in hash_set:
            # both members of the pair are in this run; keep the lexicographically
            # smaller as the stored representative, elide the other
            stored, elided = sorted([h, h_dual])
            rows.append({
                "hash_code": stored, "num_vertices": v, "num_edges": e,
                "is_self_dual": False, "dual_of_hash_code": "", "source_class": f"v{v}_f{v}",
            })
            rows.append({
                "hash_code": elided, "num_vertices": v, "num_edges": e,
                "is_self_dual": False, "dual_of_hash_code": stored, "source_class": f"v{v}_f{v}_derived",
            })
            seen.add(h)
            seen.add(h_dual)
        else:
            # dual not present in this run at all -- shouldn't happen given Euler's
            # formula fixes every graph in this run to f == v faces, but don't
            # silently drop a graph if it does.
            raise RuntimeError(
                f"v==f class v={v}: graph {h}'s dual {h_dual} not found among "
                f"the {len(rotations)} graphs plantri emitted for this class"
            )
    return raw, invocation, rows, hashes


def run_stage_a(order, out_dir, shards=1):
    e = order + 1
    classes = valid_vf_classes(e)
    order_dir = Path(out_dir) / f"order={order}"
    order_dir.mkdir(parents=True, exist_ok=True)

    provenance = {
        "stage": "A", "order": order, "num_edges": e, "shards": shards,
        "plantri_version": plantri_version(), "classes": [],
    }
    all_rows = []

    for (v, f) in classes:
        if v < f:
            continue  # derived from (f, v) above, never separately run through plantri
        if v > f:
            raw, invocation, rows, hashes = process_v_gt_f_class(v, f, e, shards=shards)
        else:
            raw, invocation, rows, hashes = process_v_eq_f_class(v, e, shards=shards)

        class_file = order_dir / f"class_v{v}_f{f}.planar_code"
        class_file.write_bytes(raw)
        hash_file = order_dir / f"class_v{v}_f{f}.planar_code.hashes.txt"
        hash_file.write_text("\n".join(hashes) + "\n")
        num_generated = sum(1 for r in rows if r["dual_of_hash_code"] == "")
        provenance["classes"].append({
            "v": v, "f": f, "invocation": " ".join(invocation),
            "num_graphs_generated": num_generated, "num_graphs_total": len(rows),
            "file": class_file.name,
        })
        all_rows.extend(rows)

    with open(order_dir / "graphs.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=GRAPH_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    with open(order_dir / "provenance.json", "w") as fh:
        json.dump(provenance, fh, indent=2)

    return provenance, all_rows


def main():
    parser = argparse.ArgumentParser(description="Stage A -- plantri driver (SPEC-1)")
    parser.add_argument("order", type=int, help="target order (num_edges = order + 1)")
    parser.add_argument("--out-dir", default="data/planar_code", help="output root directory")
    parser.add_argument("--shards", type=int, default=1,
                         help="run plantri's own res/mod sharding across this many parallel "
                              "processes per class (verified: union of shards == unsharded "
                              "output, zero overlap). Match to available CPU cores.")
    args = parser.parse_args()

    provenance, rows = run_stage_a(args.order, args.out_dir, shards=args.shards)
    generated = sum(1 for r in rows if r["dual_of_hash_code"] == "")
    elided = len(rows) - generated
    self_dual = sum(1 for r in rows if r["is_self_dual"])
    print(f"order {args.order} (e={provenance['num_edges']}): "
          f"{len(provenance['classes'])} classes run, "
          f"{generated} graphs generated, {elided} elided duals, "
          f"{self_dual} self-dual, {len(rows)} total graph rows")


if __name__ == "__main__":
    main()
