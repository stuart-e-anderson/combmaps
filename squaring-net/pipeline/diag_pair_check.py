#!/usr/bin/env python3
"""
Diagnostic (not part of the frozen pipeline): pick real (stored, elided)
graph/dual pairs from an order's v==f class and check whether they actually
produce the same dissections (true geometric rotation/reflection of each
other) or genuinely different ones.

v1 of this check compared sorted element multisets, which is inadequate --
tablecodes are ORDERED (element position encodes the actual layout), so two
dissections with the same size inventory can still be geometrically
different. This version compares actual (x, y, size) placements under all 8
dihedral transforms (4 rotations x reflect-or-not) via
squaringlib.geometry.place_elements(), which is a real geometric equality
check, not a bag-of-sizes fingerprint.

Isolates whether Stage C's elision fix is correct (SPEC-1: "process only one
of each graph/dual pair -- they yield the same dissections up to rotation")
or whether v==f-class pairs behave differently from that model.

Usage: python3 diag_pair_check.py <order> --out-dir data/planar_code -n 8
"""
import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path

from squaringlib.geometry import place_elements
from squaringlib.planar import parse_planar_code, write_planar_code

SQT_BIN = Path(__file__).parent / "sqt"

TYPE_SUFFIXES = ["spss", "spsr", "siss", "sisr", "cpss", "cpsr", "ciss", "cisr", "degenerate"]


def load_graphs_csv(order_dir):
    rows = []
    with open(order_dir / "graphs.csv") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


def find_veq_f_pairs(rows, n):
    """
    Real (stored, elided) pairs from a v==f class only -- excludes self-dual
    rows (dual_of_hash_code empty) and v>f-derived pairs (where the elided
    partner has a *different* vertex count, f != v, so it isn't the same
    kind of pairing this diagnostic is checking).
    """
    by_hash = {r["hash_code"]: r for r in rows}
    pairs = []
    for r in rows:
        if not r["dual_of_hash_code"]:
            continue
        stored = by_hash.get(r["dual_of_hash_code"])
        if stored and stored["num_vertices"] == r["num_vertices"]:
            pairs.append((stored, r))
        if len(pairs) >= n:
            break
    return pairs


def load_class_rotations(order_dir, class_file_stem):
    data = (order_dir / f"{class_file_stem}").read_bytes()
    rotations = parse_planar_code(data)
    hashes = (order_dir / f"{class_file_stem}.hashes.txt").read_text().splitlines()
    return dict(zip(hashes, rotations))


def run_sqt_alone(sqt_bin, work_dir, name, hash_code, rotation):
    """
    Each graph gets its OWN sqt process (own std::map instance). Running both
    members of a pair through one shared invocation would silently no-op the
    second graph's tablecodes via map::emplace if they're byte-identical to
    the first's -- that's not a bug, it's the pipeline's real dedup behaviour,
    but it means a shared run can't tell us whether the two graphs *independently*
    produce the same dissections. Isolating them is the actual test.
    """
    planar_file = work_dir / f"{name}.planar_code"
    planar_file.write_bytes(write_planar_code([rotation]))
    (work_dir / f"{name}.planar_code.hashes.txt").write_text(f"{hash_code}\n")
    subprocess.run([str(sqt_bin), "-scpirS", planar_file.name], cwd=work_dir,
                    capture_output=True, check=True)
    return planar_file


def read_lines_by_hash(work_dir, planar_file_name):
    """hash -> list of (d_type, width, height, elements-in-canonical-order)."""
    result = defaultdict(list)
    for suffix in TYPE_SUFFIXES:
        f = work_dir / f"{planar_file_name}-{suffix}.txt"
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            parts = line.split()
            hash_code, order, width, height = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
            elements = tuple(int(x) for x in parts[4:])  # order preserved -- position encodes layout
            result[hash_code].append((suffix.upper(), width, height, elements))
    return result


def dihedral_placements(width, height, elements):
    """
    All 8 dihedral transforms (4 rotations x reflect-or-not) of a dissection's
    actual square placement, as (transformed_width, transformed_height,
    frozenset of (x, y, size)) -- true geometric equality, not a size fingerprint.
    """
    placed = place_elements(elements, width, height)
    squares = [(sq["x"], sq["y"], sq["size"]) for sq in placed]

    variants = []
    w, h = width, height
    cur = squares
    for _ in range(4):
        # current rotation, unreflected and reflected (flip x within current w)
        variants.append((w, h, frozenset(cur)))
        variants.append((w, h, frozenset((w - x - s, y, s) for x, y, s in cur)))
        # rotate 90 deg CW into an h x w canvas: (x,y,s) -> (h-y-s, x, s)
        cur = [(h - y - s, x, s) for x, y, s in cur]
        w, h = h, w
    return variants


def same_dissection(width_a, height_a, elements_a, width_b, height_b, elements_b):
    """True if (width_b, height_b, elements_b) is some dihedral transform of (width_a, height_a, elements_a)."""
    target = (width_b, height_b, frozenset(
        (sq["x"], sq["y"], sq["size"]) for sq in place_elements(elements_b, width_b, height_b)
    ))
    for w, h, squares in dihedral_placements(width_a, height_a, elements_a):
        if (w, h, squares) == target:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("order", type=int)
    parser.add_argument("--out-dir", default="data/planar_code")
    parser.add_argument("-n", type=int, default=8, help="number of pairs to test")
    args = parser.parse_args()

    order_dir = Path(args.out_dir) / f"order={args.order}"
    rows = load_graphs_csv(order_dir)
    pairs = find_veq_f_pairs(rows, args.n)
    print(f"found {len(pairs)} (stored, elided) v==f pairs to test")

    class_stem = f"class_v{pairs[0][0]['num_vertices']}_f{pairs[0][0]['num_vertices']}.planar_code"
    rot_by_hash = load_class_rotations(order_dir, class_stem)

    work_dir = Path("/tmp/diag_pair_check")
    work_dir.mkdir(exist_ok=True)

    matches, mismatches = 0, 0
    for idx, (stored, elided) in enumerate(pairs):
        h_a, h_b = stored["hash_code"], elided["hash_code"]
        rot_a, rot_b = rot_by_hash[h_a], rot_by_hash[h_b]

        file_a = run_sqt_alone(SQT_BIN, work_dir, f"pair{idx}a", h_a, rot_a)
        file_b = run_sqt_alone(SQT_BIN, work_dir, f"pair{idx}b", h_b, rot_b)
        rows_a = read_lines_by_hash(work_dir, file_a.name).get(h_a, [])
        rows_b = read_lines_by_hash(work_dir, file_b.name).get(h_b, [])

        # multiset match: every stored dissection must pair, under some dihedral
        # transform, with a distinct (not-yet-consumed) elided dissection of the
        # same d_type, and the counts must match exactly.
        unmatched_b = list(rows_b)
        unmatched_a = []
        for d_type_a, width_a, height_a, elements_a in rows_a:
            found_idx = None
            for i, (d_type_b, width_b, height_b, elements_b) in enumerate(unmatched_b):
                if d_type_a != d_type_b:
                    continue
                if same_dissection(width_a, height_a, elements_a, width_b, height_b, elements_b):
                    found_idx = i
                    break
            if found_idx is not None:
                unmatched_b.pop(found_idx)
            else:
                unmatched_a.append((d_type_a, width_a, height_a, elements_a))

        same = not unmatched_a and not unmatched_b
        matches += same
        mismatches += not same
        print(f"pair {idx}: stored={h_a} ({len(rows_a)} rows, run alone) "
              f"elided={h_b} ({len(rows_b)} rows, run alone) -- "
              f"{'SAME (true geometric rotation of each other)' if same else 'DIFFERENT'}")
        if not same:
            print(f"    unmatched in stored: {len(unmatched_a)}  unmatched in elided: {len(unmatched_b)}")
            if unmatched_a:
                print(f"    e.g. stored-only: {unmatched_a[0]}")
            if unmatched_b:
                print(f"    e.g. elided-only: {unmatched_b[0]}")

    print(f"\n{matches}/{len(pairs)} pairs match (stored's dissections == elided's, "
          f"true 90-degree geometric rotation); {mismatches} differ")


if __name__ == "__main__":
    main()
