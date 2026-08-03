#!/usr/bin/env bash
# Render every content/batch_*.json on this box, N at a time. Clean quoting (no inline ssh hell).
#   bash render_batch.sh [N]
set -u
cd "$(dirname "$0")"
N="${1:-6}"
mkdir -p out
rm -f out/BATCH_DONE
ls content/batch_*.json 2>/dev/null | xargs -P "$N" -I{} bash -c '
  f="$1"; b=$(basename "$f" .json)
  python3 make_kids_quiz_video.py "$f" "out/$b.mp4" > "out/$b.log" 2>&1
' _ {}
touch out/BATCH_DONE
