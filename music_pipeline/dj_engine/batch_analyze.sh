#!/bin/bash
# Batch-analyze a folder of DJ sets -> per-track arrangement JSONs (idempotent: skips done).
cd /home/ubuntu
SRC=dj_engine/burmeister
OUT=$SRC/analysis
mkdir -p "$OUT"
for f in "$SRC"/*.mp3; do
  b=$(basename "$f" .mp3)
  o="$OUT/$b.json"
  if [ -f "$o" ]; then echo "SKIP: $b"; continue; fi
  if python3 dj_engine/dj_arrangement_analysis.py --in "$f" --json "$o" --bin 30 >/dev/null 2>&1; then
    echo "OK: $b ($(date +%H:%M:%S))"
  else
    echo "FAIL: $b"
  fi
done
echo BATCHDONE
