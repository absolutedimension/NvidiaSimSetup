#!/bin/bash
# Generate 5 distinct Burmeister-style tracks (one per core, varied breakdowns), v9 recipe + master.
source /home/ubuntu/audio_pipeline/venv/bin/activate 2>/dev/null
cd /home/ubuntu
mkdir -p dj_engine/tracks
CORES=(11 22 33 44 55)
BREAKS=("0.38,0.66" "0.45,0.72" "0.40" "0.33,0.58,0.80" "0.50,0.75")
MIN=(30 30 30 30 30)
MASTER="highpass=f=28,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150:makeup=2,treble=g=2.5:f=3500,loudnorm=I=-10:TP=-1:LRA=9"
for i in 0 1 2 3 4; do
  c=${CORES[$i]}; b=${BREAKS[$i]}; m=${MIN[$i]}; n=$((i+1))
  echo "=== TRACK $n  (core $c, breaks $b, ${m}min) ==="
  python3 -u dj_engine/grammar_generate.py --core music_out/burmcore_$c.mp3 --minutes $m --breaks "$b" \
    --out dj_engine/tracks/_t$n.wav 2>&1 | grep -E "\[gen\]"
  ffmpeg -y -i dj_engine/tracks/_t$n.wav -af "$MASTER" -b:a 192k dj_engine/tracks/burmeister_track$n.mp3 2>/dev/null
  rm -f dj_engine/tracks/_t$n.wav
  echo "TRACK$n DONE"
done
echo ALL5DONE
