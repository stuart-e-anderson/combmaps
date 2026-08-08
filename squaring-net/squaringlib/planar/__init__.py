"""
planar — planar graph utilities for squared rectangle work.

Depends on combmapcore for combinatorial map representation.
Provides:
  - Conversion between plantri output and combmapcore graphs
  - Duality operations
  - Graph canonicalisation (via nauty labelg)
"""
import io
import shutil
import subprocess

from combmapcore.dual import compute_dual_adjacency
from combmapcore.parser import plantri_graphs_planarcode_stream

__all__ = [
    "run_plantri",
    "parse_planar_code",
    "write_planar_code",
    "dual_rotation_system",
    "graph6_encode",
    "canonical_hash_code",
    "valid_vf_classes",
]

PLANTRI_BIN = shutil.which("plantri") or "/usr/local/bin/plantri"
LABELG_BIN = shutil.which("nauty-labelg") or shutil.which("labelg") or "nauty-labelg"


def run_plantri(n, e=None, extra_args=None):
    """Run plantri for n vertices (optionally pinned to e edges), return raw planar_code bytes."""
    args = [PLANTRI_BIN, "-p"]
    if extra_args:
        args += list(extra_args)
    if e is not None:
        args.append(f"-e{e}:{e}")
    args.append(str(n))
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"plantri failed ({' '.join(args)}): {proc.stderr.decode()}")
    return proc.stdout


def parse_planar_code(binary_data):
    """Parse planar_code bytes (with header) into a list of rotation systems (vertex -> ordered neighbor list, 0-based)."""
    if not binary_data.startswith(b">>planar_code<<"):
        raise ValueError("Missing planar_code header")
    # plantri_graphs_planarcode_stream skips the 15-byte header itself.
    stream = io.BytesIO(binary_data)
    return list(plantri_graphs_planarcode_stream(stream))


def write_planar_code(rotations):
    """
    Inverse of parse_planar_code: encode a list of rotation systems back into
    planar_code bytes (header + one n-byte/neighbor-list-with-0-terminator
    record per graph, 1-indexed neighbors), so a subset of graphs pulled out
    of a larger file can be fed to sqt standalone.
    """
    out = bytearray(b">>planar_code<<")
    for rotation in rotations:
        n = len(rotation)
        out.append(n)
        for i in range(n):
            for neighbor in rotation[i]:
                out.append(neighbor + 1)
            out.append(0)
    return bytes(out)


def dual_rotation_system(rotation):
    """Derive the dual graph's rotation system from a primal rotation system (no second plantri call)."""
    return compute_dual_adjacency(rotation)


def graph6_encode(rotation):
    """Encode a rotation system (embedding order ignored) as a graph6 string."""
    n = len(rotation)
    edges = set()
    for u, neighbors in rotation.items():
        for v in neighbors:
            edges.add((u, v) if u < v else (v, u))
    bits = []
    for j in range(1, n):
        for i in range(j):
            bits.append(1 if (i, j) in edges else 0)
    while len(bits) % 6 != 0:
        bits.append(0)
    chars = []
    for k in range(0, len(bits), 6):
        val = 0
        for b in bits[k:k + 6]:
            val = (val << 1) | b
        chars.append(chr(val + 63))
    if n > 62:
        raise ValueError("graph6_encode only supports n <= 62 (single-byte header)")
    return chr(n + 63) + "".join(chars)


def canonical_hash_code(rotation):
    """Nauty canonical certificate for a rotation system's underlying simple graph. Sound join key for graphs.hash_code."""
    return canonical_hash_codes_batch([rotation])[0]


def canonical_hash_codes_batch(rotations):
    """
    Canonical certificates for many rotation systems in one nauty-labelg process.
    One-process-per-graph does not scale past a few hundred graphs (Stage A
    classes at order ~20+ run into the thousands); labelg reads/writes graph6
    line-by-line so order is preserved across the batch.
    """
    if not rotations:
        return []
    g6_lines = "\n".join(graph6_encode(r) for r in rotations) + "\n"
    proc = subprocess.run([LABELG_BIN, "-q"], input=g6_lines.encode(), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"nauty-labelg batch of {len(rotations)} failed: {proc.stderr.decode()}")
    out_lines = proc.stdout.decode().splitlines()
    if len(out_lines) != len(rotations):
        raise RuntimeError(
            f"nauty-labelg returned {len(out_lines)} lines for {len(rotations)} input graphs"
        )
    return out_lines


def valid_vf_classes(e):
    """
    Every valid (v, f) planar-map class for e edges, per SPEC-1 Stage A.
    v + f = e + 2 (Euler), with both v and f (by primal/dual symmetry) subject
    to the simple 3-connected planar bound e <= 3n - 6 (min face size 3) and
    its dual e >= ceil(3n/2) (min degree 3, i.e. n <= 2e/3):
        ceil((e + 6) / 3) <= v <= floor(2e / 3)
    Replaces the old driver's buggy `if v > f: skip`, which dropped classes
    like Duijvestijn's order-21 112^2 (v=13, f=11), AND fixes a missing lower
    bound (e >= 3v/2) that would otherwise admit combinatorially impossible
    classes such as (v=9, f=3) at e=10 (plantri rejects: no 3-connected simple
    planar graph has 9 vertices and only 10 edges).
    """
    min_v = -(-(e + 6) // 3)  # ceil
    max_v = (2 * e) // 3      # floor
    classes = []
    for v in range(min_v, max_v + 1):
        f = e + 2 - v
        classes.append((v, f))
    return classes
