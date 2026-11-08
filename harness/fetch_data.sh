#!/usr/bin/env bash
# Fetch the raw question banks used by this benchmark into data/raw/.
# These are NOT committed to the repo (see .gitignore); this script makes the
# study reproducible without us redistributing the question banks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"
mkdir -p "$RAW"

echo "[1/2] WMDP-cyber (cais/wmdp, wmdp-cyber split) ..."
curl -sL --fail -o "$RAW/wmdp-cyber-test.parquet" \
  "https://huggingface.co/datasets/cais/wmdp/resolve/main/wmdp-cyber/test-00000-of-00001.parquet"
python3 - "$RAW/wmdp-cyber-test.parquet" "$RAW/wmdp_cyber.json" <<'PY'
import sys, json
import pyarrow.parquet as pq
rows = pq.read_table(sys.argv[1]).to_pylist()
json.dump(rows, open(sys.argv[2], "w"))
print(f"  wrote {len(rows)} WMDP-cyber items")
PY

echo "[2/2] CyberMetric-2000 ..."
curl -sL --fail -o "$RAW/CyberMetric-2000-v1.json" \
  "https://raw.githubusercontent.com/cybermetric/CyberMetric/main/CyberMetric-2000-v1.json"
python3 -c "import json;print('  wrote', len(json.load(open('$RAW/CyberMetric-2000-v1.json'))['questions']), 'CyberMetric items')"

echo "Done. Raw data in $RAW"
