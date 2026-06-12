#!/usr/bin/env bash
# Mirror the TrigunAI Claude skills (which live in ~/.claude/skills, outside this repo)
# into skills/ so they're version-controlled and recoverable with the rest of the project.
# Run standalone, or automatically via checkpoint.sh before each commit.
set -euo pipefail
cd "$(dirname "$0")"

SRC="$HOME/.claude/skills"
DST="skills"
mkdir -p "$DST"

count=0
for dir in "$SRC"/trigunai-* "$SRC"/production-video-trigunai \
           "$SRC"/video-script-writer-trigunai "$SRC"/add-openclaw-skill; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  rsync -a --delete "$dir/" "$DST/$name/"
  count=$((count+1))
done
echo "✓ synced $count skills -> $DST/"
