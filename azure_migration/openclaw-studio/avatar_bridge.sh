#!/usr/bin/env bash
# avatar_bridge.sh — the glue that lets the OpenClaw content box (A) talk to the T4 avatar box (B).
# Generates a talking-avatar clip (brand persona "Acharya") lip-synced to a reel's own voiceover,
# and drops it onto the EC2 render farm (C) for compositing.
#
# Usage:
#   avatar_bridge.sh --vo <path-on-EC2> --slug <name> [--role intro|corner] [--out-dir <dir-on-EC2>]
#
#   --vo    : path to full_voiceover.wav ON THE EC2 FARM (the reel's frozen narration)
#   --slug  : reel/video slug (names the output)
#   --role  : intro (reels, default) | corner (long videos) — advisory; passed through for the composite
#   --out-dir: where to place the clip on EC2 (default: $FARM_HOME/avatar_out)
#
# Prints on success:  AVATAR_CLIP=<path-on-EC2>   AVATAR_ROLE=<role>
# Fails SOFT: if B is unreachable it prints  AVATAR_CLIP=NONE  (rc 0) so the reel still renders shader-only.
set -uo pipefail

# ---- config ----
source "$HOME/.openclaw/avatar.env" 2>/dev/null || { echo "avatar.env missing → AVATAR_CLIP=NONE"; echo "AVATAR_CLIP=NONE"; exit 0; }
source "$HOME/.openclaw/farm.sh"    2>/dev/null || { echo "farm.sh missing → AVATAR_CLIP=NONE"; echo "AVATAR_CLIP=NONE"; exit 0; }

ROLE=intro; OUT_DIR=""; VO=""; SLUG="clip"
while [ $# -gt 0 ]; do case "$1" in
  --vo) VO="$2"; shift 2;;
  --slug) SLUG="$2"; shift 2;;
  --role) ROLE="$2"; shift 2;;
  --out-dir) OUT_DIR="$2"; shift 2;;
  *) shift;;
esac; done
[ -z "$OUT_DIR" ] && OUT_DIR="$FARM_HOME/avatar_out"

B(){ ssh -i "$AV_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$AV_USER@$AV_HOST" "$1"; }
C(){ ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" "$1"; }
soft_skip(){ echo "avatar step skipped: $1"; echo "AVATAR_CLIP=NONE"; exit 0; }

# ---- 1. ensure Box B (T4) is up ----
if ! B 'curl -sf 127.0.0.1:8080/health >/dev/null 2>&1'; then
  if [ "${AV_LIFECYCLE:-none}" = az ]; then
    echo "T4 down — starting via az…"
    az vm start -g "$AV_AZ_GROUP" -n "$AV_AZ_VM" >/dev/null 2>&1 || soft_skip "az vm start failed"
    for i in $(seq 1 20); do B 'curl -sf 127.0.0.1:8080/health >/dev/null 2>&1' && break; sleep 15; done
  fi
  B 'curl -sf 127.0.0.1:8080/health >/dev/null 2>&1' || soft_skip "T4 unreachable (provision ~/.ssh/t4_avatar.pem + AV_LIFECYCLE)"
fi

# ---- 2. ensure the brand face exists on B (generate once) ----
if ! B "test -f '$AV_FACE'"; then
  echo "generating brand persona face on B…"
  B "python3 ~/make_avatar_image.py \"$AV_FACE_PROMPT\" '$AV_FACE'" || soft_skip "face generation failed"
fi

# ---- 3. move the reel's voiceover  C → A → B ----
TMP="/tmp/avatar_$SLUG"; mkdir -p "$TMP"
scp -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP:$VO" "$TMP/vo.wav" 2>/dev/null || soft_skip "could not pull VO from farm ($VO)"
scp -i "$AV_KEY" -o StrictHostKeyChecking=no "$TMP/vo.wav" "$AV_USER@$AV_HOST:~/vo_$SLUG.wav" 2>/dev/null || soft_skip "could not push VO to T4"

# ---- 4. lip-sync WITH motion + cinematic camera move (on B) ----
B "curl -s -F image=@$AV_FACE -F audio=@\$HOME/vo_$SLUG.wav \
     '$AV_API/lipsync?still=false&preprocess=crop&enhancer=gfpgan' -o \$HOME/avatar_$SLUG.mp4 \
   && bash ~/make_cinematic.sh \$HOME/avatar_$SLUG.mp4 \$HOME/avatar_${SLUG}_final.mp4" \
   || soft_skip "SadTalker render failed on T4"

# ---- 5. bring the clip back  B → A → C (render farm) ----
scp -i "$AV_KEY" -o StrictHostKeyChecking=no "$AV_USER@$AV_HOST:~/avatar_${SLUG}_final.mp4" "$TMP/avatar_final.mp4" 2>/dev/null || soft_skip "could not pull clip from T4"
C "mkdir -p '$OUT_DIR'"
scp -i "$FARM_KEY" -o StrictHostKeyChecking=no "$TMP/avatar_final.mp4" "$FARM_USER@$FARM_IP:$OUT_DIR/${SLUG}.mp4" 2>/dev/null || soft_skip "could not push clip to farm"

# ---- 6. optionally stop B ----
if [ "${AV_LIFECYCLE:-none}" = az ] && [ "${AV_STOP_AFTER:-false}" = true ]; then
  az vm deallocate -g "$AV_AZ_GROUP" -n "$AV_AZ_VM" >/dev/null 2>&1 && echo "T4 deallocated (cost saved)"
fi

rm -rf "$TMP"
echo "AVATAR_CLIP=$OUT_DIR/${SLUG}.mp4"
echo "AVATAR_ROLE=$ROLE"
