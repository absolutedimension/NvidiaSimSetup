#!/usr/bin/env bash
# sync_skills.sh — keep the TrigunAI Claude skills in sync between this machine's
# active skill folder (~/.claude/skills) and the version-controlled copy in this repo (skills/).
#
# The repo is the single source of truth that travels between machines (Mac, Windows box, …)
# via git. On each machine you keep the ACTIVE copy in ~/.claude/skills; this script moves
# skills between that folder and the repo in either direction.
#
#   ./sync_skills.sh                 # PUSH  (default): ~/.claude/skills  ->  repo/skills/
#                                    #   (used by checkpoint.sh before each commit, to back up edits)
#   ./sync_skills.sh --install       # PULL: repo/skills/  ->  ~/.claude/skills
#                                    #   (run this after `git pull` on ANY machine to install/refresh
#                                    #    the skills locally — this is how the Windows box gets them)
#   ./sync_skills.sh --pull          # alias for --install
#
# Windows (PowerShell) equivalent for the --install direction: sync_skills.ps1
set -euo pipefail
cd "$(dirname "$0")"

ACTIVE="$HOME/.claude/skills"   # where Claude actually loads skills from, on this machine
REPO="skills"                   # version-controlled copy in this repo

# Our skills (so we never vacuum up unrelated plugin skills). Globs are matched in $ACTIVE for
# PUSH and in $REPO for PULL; non-matches are skipped silently.
OURS=( "trigunai-*" "content-*" "production-*" "faceless-*" \
       "video-script-writer-trigunai" "add-openclaw-skill" )

MODE="push"
case "${1:-}" in
  --install|--pull|pull|install) MODE="pull" ;;
  ""|--push|push)                MODE="push" ;;
  -h|--help)
    grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "Unknown arg: $1  (use --install to pull repo -> ~/.claude/skills)"; exit 1 ;;
esac

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync not found — install it, or on Windows use sync_skills.ps1"; exit 1
fi

count=0
if [ "$MODE" = "push" ]; then
  mkdir -p "$REPO"
  for pat in "${OURS[@]}"; do
    for dir in $ACTIVE/$pat; do
      [ -d "$dir" ] || continue
      name=$(basename "$dir")
      rsync -a --delete "$dir/" "$REPO/$name/"
      count=$((count+1))
    done
  done
  echo "✓ PUSH: synced $count skill(s)  ~/.claude/skills  ->  $REPO/"
else
  mkdir -p "$ACTIVE"
  for pat in "${OURS[@]}"; do
    for dir in $REPO/$pat; do
      [ -d "$dir" ] || continue
      name=$(basename "$dir")
      rsync -a --delete "$dir/" "$ACTIVE/$name/"
      count=$((count+1))
    done
  done
  echo "✓ INSTALL: synced $count skill(s)  $REPO/  ->  ~/.claude/skills"
  echo "  Restart / reopen Claude if a newly-installed skill doesn't appear yet."
fi
