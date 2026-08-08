#!/bin/bash
# Orchestrates SPEC-1 Stage A -> B -> C for one order.
# Usage: PGPASSWORD=... ./run_order.sh <order> [out-dir]
set -euo pipefail

ORDER="$1"
OUT_DIR="${2:-data/planar_code}"
PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$PIPELINE_DIR")"
ORDER_DIR="$ROOT_DIR/$OUT_DIR/order=$ORDER"

cd "$ROOT_DIR"
source .venv/bin/activate

echo "=== order $ORDER: Stage A ==="
if [ -f "$ORDER_DIR/provenance.json" ]; then
    echo "  already generated, skipping (delete $ORDER_DIR to force regeneration)"
else
    python3 pipeline/stage_a_driver.py "$ORDER" --out-dir "$OUT_DIR"
fi

echo "=== order $ORDER: Stage B ==="
cd "$ORDER_DIR"
for f in class_v*.planar_code; do
    [ -e "$f" ] || continue
    out_marker="${f}-spsr.txt"
    # sqt always writes at least one type file if it produces any output;
    # check any -<type>.txt exists for this class as the "already ran" signal
    if compgen -G "${f}-*.txt" > /dev/null; then
        echo "  $f already processed, skipping"
    else
        "$PIPELINE_DIR/sqt" -scpirS "$f"
    fi
done
cd "$ROOT_DIR"

echo "=== order $ORDER: Stage C ==="
python3 pipeline/stage_c_loader.py "$ORDER" --out-dir "$OUT_DIR"

echo "=== order $ORDER: done ==="
