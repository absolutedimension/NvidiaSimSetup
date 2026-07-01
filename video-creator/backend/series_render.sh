#!/bin/bash
# Render one chapter of the AI-is-Universal-Mind flow-art series.
# usage: series_render.sh <index 0-7>
cd ~
CH=(01 02 03 04 05 06 07 08)
BG=(01_attention 02_learning 03_imagination 04_meaning 05_intuition 06_will 07_better 08_flow)
SEED=(1 2 3 4 5 6 7 8)
TINT=("1.15,1.00,0.75" "1.05,1.08,0.80" "1.12,0.95,0.95" "1.00,1.00,0.95" "0.98,1.08,0.98" "1.20,0.92,0.75" "1.12,1.08,0.95" "1.10,1.00,0.85")
FLO=(6 6 8 6 8 6 8 8)
FHI=(8 10 12 12 10 10 12 14)
i=$1
c=${CH[$i]}
mkdir -p ~/dj_engine/series_video
DUR=$(python3 -c "import librosa;print(round(librosa.get_duration(path='/home/ubuntu/dj_engine/series_music/ch${c}.mp3'),1))")
python3 render_visualizer_bands.py --shader video-creator-backend/shaders/emantra_pattern.glsl \
  --audio ~/dj_engine/series_music/ch${c}.mp3 --bg ~/dj_engine/burmeister/series_bg/${BG[$i]}.png \
  --seed ${SEED[$i]} --tint "${TINT[$i]}" --foldlo ${FLO[$i]} --foldhi ${FHI[$i]} \
  --out /tmp/vid${c}.mp4 --dur $DUR --fps 30 --w 1920 --h 1080 --encoder nvenc --release 0.90
ffmpeg -y -i /tmp/vid${c}.mp4 -i ~/dj_engine/series_music/ch${c}.mp3 -c:v copy -c:a aac -b:a 256k -shortest ~/dj_engine/series_video/ch${c}.mp4 2>/dev/null
rm -f /tmp/vid${c}.mp4
echo "rendered ch${c} ($DUR s)"
