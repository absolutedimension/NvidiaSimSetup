#!/usr/bin/env bash
# checkpoint.sh — one command to save your work.
#   ./checkpoint.sh "recorded module 1 lecture 3"
#   ./checkpoint.sh                      (auto timestamp message)
#
# Does: refresh the work log -> stage everything -> commit -> show result.

set -euo pipefail
cd "$(dirname "$0")"

MSG="${*:-checkpoint $(date '+%Y-%m-%d %H:%M')}"

# 1. refresh the work digest + mirror skills (best-effort; never blocks a commit)
python3 project_hub/tools/ceo_work_scan.py --days 14 >/dev/null 2>&1 || true
./sync_skills.sh >/dev/null 2>&1 || true

# 2. stage everything (respecting .gitignore)
git add -A

# 3. nothing to commit? say so and exit clean
if git diff --cached --quiet; then
  echo "✓ Nothing changed since last checkpoint — working tree clean."
  echo "  Last: $(git log --oneline -1)"
  exit 0
fi

# 4. show what's about to be saved
echo "Saving $(git diff --cached --name-only | wc -l | tr -d ' ') changed file(s):"
git diff --cached --name-only | sed 's/^/  • /' | head -20
EXTRA=$(( $(git diff --cached --name-only | wc -l) - 20 ))
[ "$EXTRA" -gt 0 ] && echo "  …and $EXTRA more"

# 5. commit
git commit -q -m "$MSG

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

echo ""
echo "✅ Checkpoint saved: $(git log --oneline -1)"
echo "   Total checkpoints: $(git rev-list --count HEAD)"
