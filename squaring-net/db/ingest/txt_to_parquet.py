"""
Convert Bouwkamp text files from Orders_5-26/code/ to partitioned Parquet.

Output layout:
    data/parquet/
        order=06/tilings.parquet
        order=07/tilings.parquet
        ...
        order=26/tilings.parquet
        wheel/tilings.parquet        ← wheel-graph tilings (all orders together)

Usage:
    python db/ingest/txt_to_parquet.py [--data-dir PATH] [--out-dir PATH]
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

# --- schema ----------------------------------------------------------------

SCHEMA = pa.schema([
    pa.field("order_n",      pa.int16()),
    pa.field("width",        pa.int64()),   # wheel tilings have Fibonacci-scale dims
    pa.field("height",       pa.int64()),
    pa.field("type_code",    pa.dictionary(pa.int8(), pa.string())),
    pa.field("simple",       pa.bool_()),
    pa.field("perfect",      pa.bool_()),
    pa.field("is_square",    pa.bool_()),
    pa.field("bouwkamp",     pa.string()),
    pa.field("aspect_ratio", pa.float64()),
    pa.field("source",       pa.dictionary(pa.int8(), pa.string())),
])

TYPE_PROPS = {
    "spsr": (True,  True,  False),
    "spss": (True,  True,  True),
    "cpsr": (False, True,  False),
    "cpss": (False, True,  True),
    "sisr": (True,  False, False),
    "siss": (True,  False, True),
    "cisr": (False, False, False),
    "ciss": (False, False, True),
    "degenerate": (None, None, None),
}

# Filename patterns
RE_REGULAR   = re.compile(r"^(\d+)\.bin-(\w+)\.txt$")
RE_WHEEL     = re.compile(r"^wheel_(\d+)\.bin-(\w+)\.txt$")
RE_ORDER_DIR = re.compile(r"^o(\d+)(\w+)\.txt$")

# --- parsing ---------------------------------------------------------------

def parse_rows(path: Path, type_code: str, source: str):
    simple, perfect, is_square = TYPE_PROPS.get(type_code, (None, None, None))
    with path.open() as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline annotations (e.g. "* 25 : 198 x 196 b: 8")
            if " * " in line:
                line = line[:line.index(" * ")].strip()
            try:
                nums = list(map(int, line.split()))
            except ValueError:
                continue  # skip parenthesised / non-integer lines
            if len(nums) < 4:
                continue
            order_n, width, height = nums[0], nums[1], nums[2]
            ar = width / height if height else 0.0
            yield {
                "order_n":      order_n,
                "width":        width,
                "height":       height,
                "type_code":    type_code,
                "simple":       simple,
                "perfect":      perfect,
                "is_square":    is_square,
                "bouwkamp":     line,
                "aspect_ratio": ar,
                "source":       source,
            }

# --- batched collection by partition key -----------------------------------

def collect_by_partition(data_root: Path):
    """
    Scan all known file locations under data_root and collect rows by partition.
    Partitions: 'order=NN' for regular/order-dir files, 'wheel' for wheel files.
    data_root should be the Orders_5-26 directory (i.e. data/orders).
    """
    by_partition: dict[str, list[dict]] = defaultdict(list)

    def ingest_file(path, type_code, source, partition):
        if type_code not in TYPE_PROPS:
            print(f"  skip unknown type: {path.name}", file=sys.stderr)
            return
        for row in parse_rows(path, type_code, source):
            by_partition[partition].append(row)

    # 1. code/ subdirectory — orders 6-9, wheel graphs
    code_dir = data_root / "code"
    if code_dir.exists():
        for path in sorted(code_dir.glob("*.txt")):
            m = RE_REGULAR.match(path.name)
            if m:
                ingest_file(path, m.group(2), "regular",
                            f"order={int(m.group(1)):02d}")
                continue
            m = RE_WHEEL.match(path.name)
            if m:
                ingest_file(path, m.group(2), "wheel", "wheel")
                continue
            print(f"  skip non-standard: {path.name}", file=sys.stderr)

    # 2. order-NN/ subdirectories — orders 10-26
    for order_dir in sorted(data_root.glob("order-*")):
        if not order_dir.is_dir():
            continue
        order_num = int(order_dir.name.split("-")[1])
        partition = f"order={order_num:02d}"
        for path in sorted(order_dir.glob("*.txt")):
            m = RE_ORDER_DIR.match(path.name)
            if not m:
                continue  # skip logs, ratios, bk2nice files etc
            type_code = m.group(2)
            if type_code == "b":
                type_code = "spsr"   # annotated beautiful tilings are spsr
                source = "annotated"
            elif type_code == "_composition_log":
                continue
            else:
                source = "regular"
            ingest_file(path, type_code, source, partition)

    return by_partition

# --- write Parquet ---------------------------------------------------------

def write_partition(out_dir: Path, partition: str, rows: list[dict]):
    if not rows:
        return
    dest = out_dir / partition
    dest.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(
        table,
        dest / "tilings.parquet",
        compression="zstd",
        row_group_size=100_000,
    )
    print(f"  {partition:12s}  {len(rows):>10,} rows  →  {dest/'tilings.parquet'}")

# --- main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default="data/orders",
                    help="Path to Orders_5-26/ root directory")
    ap.add_argument("--out-dir",  default="data/parquet",
                    help="Output root for Parquet partitions")
    args = ap.parse_args()

    code_dir = Path(args.data_dir)
    out_dir  = Path(args.out_dir)

    if not code_dir.exists():
        sys.exit(f"ERROR: data directory not found: {code_dir}")

    print(f"Reading from : {code_dir}")
    print(f"Writing to   : {out_dir}")
    print()

    print("Collecting rows...")
    by_partition = collect_by_partition(code_dir)

    total = sum(len(v) for v in by_partition.values())
    print(f"Total rows parsed: {total:,}\n")

    print("Writing Parquet files:")
    for partition in sorted(by_partition):
        write_partition(out_dir, partition, by_partition[partition])

    print(f"\nDone. {len(by_partition)} partition(s) written.")


if __name__ == "__main__":
    main()
