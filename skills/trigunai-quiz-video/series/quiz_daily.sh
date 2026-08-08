#!/usr/bin/env bash
# Acharya daily quiz-Shorts cron: resolve today's 2 topics -> render 4 on EC2 -> upload 2 EN + 2 HI.
# Runs on an ALWAYS-ON box (studio-daily). That box needs: ssh to EC2 (trigunai_key), and the
# youtube_series/ dir with token.json + token_hi.json + client_secret.json.
#
#   ./quiz_daily.sh                # full run (render + upload) for today (IST)
#   ./quiz_daily.sh --date 2026-07-24
#   ./quiz_daily.sh --dry-run      # just resolve today's topics, write JSONs/manifests, no render/upload
#   ./quiz_daily.sh --no-upload    # render only, skip upload (verify videos first)
set -euo pipefail

SERIES_DIR="$(cd "$(dirname "$0")" && pwd)"
: "${EC2_IP:=34.192.145.204}"
: "${EC2_USER:=ubuntu}"
: "${EC2_KEY:=$HOME/.ssh/trigunai_key.pem}"
: "${EC2_QUIZDIR:=/home/ubuntu/quiz_video}"
: "${YT_DIR:=$SERIES_DIR/../../../youtube_series}"     # override on the studio box
: "${PY:=/usr/bin/python3}"
WORK="/tmp/quizday_$(date +%Y%m%d)"

DATE_ARG=""; DRY=0; NOUP=0
while [ $# -gt 0 ]; do case "$1" in
  --date) DATE_ARG="--date $2"; shift 2;;
  --dry-run) DRY=1; shift;;
  --no-upload) NOUP=1; shift;;
  *) echo "unknown arg $1"; exit 1;;
esac; done

SSH(){ ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=25 "$EC2_USER@$EC2_IP" "$1"; }

echo "[quiz-daily] resolving topics…"
PLAN=$(python3 "$SERIES_DIR/quiz_daily.py" $DATE_ARG --workdir "$WORK")
echo "$PLAN"
POST=$(echo "$PLAN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('post'))")
[ "$POST" != "True" ] && { echo "[quiz-daily] nothing to post today."; exit 0; }

# list of engine json + mp4 names
mapfile -t JSONS < <(python3 -c "import json;d=json.load(open('$WORK/plan.json')) if False else None" 2>/dev/null; echo "$PLAN" | python3 -c "import sys,json;[print(e['json']) for e in json.load(sys.stdin)['engine_files']]")
mapfile -t MP4S  < <(echo "$PLAN" | python3 -c "import sys,json;[print(e['mp4']) for e in json.load(sys.stdin)['engine_files']]")

[ "$DRY" = 1 ] && { echo "[quiz-daily] DRY RUN — JSONs + manifests in $WORK"; ls -1 "$WORK"; exit 0; }

echo "[quiz-daily] farm reachability…"
UP=0; for i in 1 2 3 4 5; do SSH 'echo up' 2>/dev/null | grep -q up && { UP=1; break; }; sleep 8; done
[ "$UP" != 1 ] && { echo "[quiz-daily] EC2 unreachable — start TrigunAI-Omniverse (IP stays $EC2_IP)"; exit 1; }

echo "[quiz-daily] push engine JSONs + render 4 videos…"
for i in "${!JSONS[@]}"; do
  scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "${JSONS[$i]}" "$EC2_USER@$EC2_IP:$EC2_QUIZDIR/content/"
done
# render sequentially (absolute paths — cwd-independent), each ~7 min
for i in "${!JSONS[@]}"; do
  base="$(basename "${JSONS[$i]}")"; out="${MP4S[$i]}"
  echo "  rendering $out"
  SSH "cd $EC2_QUIZDIR && python3 $EC2_QUIZDIR/make_quiz_video.py $EC2_QUIZDIR/content/$base $EC2_QUIZDIR/$out"
  SSH "chmod 644 $EC2_QUIZDIR/$out"
  scp -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP:$EC2_QUIZDIR/$out" "$YT_DIR/$out"
done

[ "$NOUP" = 1 ] && { echo "[quiz-daily] --no-upload: videos in $YT_DIR ($(printf '%s ' "${MP4S[@]}"))"; exit 0; }

echo "[quiz-daily] upload — 2 EN to English channel, 2 HI to Hindi channel…"
cp "$WORK/manifest_en.json" "$YT_DIR/manifest_day_en.json"
cp "$WORK/manifest_hi.json" "$YT_DIR/manifest_day_hi.json"
( cd "$YT_DIR" && $PY yt_upload.py run manifest_day_en.json --substack "https://acharya.trigunai.com/exam-prep/quick" )
( cd "$YT_DIR" && YT_TOKEN=token_hi.json $PY yt_upload.py run manifest_day_hi.json --substack "https://acharya.trigunai.com/exam-prep/quick" )
echo "[quiz-daily] done for $(date +%F)."
