#!/bin/bash
# Render + upload tracks 2-5 to FlowArt, one after another. Box-direct (no Mac transfer).
set -u
cd /home/ubuntu
RV=~/audio_pipeline/venv/bin/python
YP=~/acestep_venv/bin/python
SHD=/home/ubuntu/video-creator-backend/shaders
MASTER_OK=1

IDS=(bowl enso flower portal)
TRACKS=(burmeister_track1 burmeister_track2 burmeister_track3 burmeister_track4)
SHADERS=(bowl_ripples enso_flow flower_of_life_flow question_portal_flow)
TITLES=(
"30 Min Hypnotic Techno — Singing Bowl Ripples | Deep Flow & Letting Go"
"30 Min Hypnotic Techno — Zen Ensō | Deep Focus & Meditation"
"30 Min Hypnotic Techno — Flower of Life | Sacred Geometry Flow"
"30 Min Hypnotic Techno — Cosmic Portal | Deep Focus & Flow"
)
VISUALS=(
"singing-bowl ripples that radiate with every beat"
"a single Zen ink-ring breathing with the music"
"the Flower of Life sacred-geometry mandala rippling and blooming"
"a cosmic portal — a glowing beacon with light-bubbles drifting in"
)

for i in 0 1 2 3; do
  id=${IDS[$i]}; tr=${TRACKS[$i]}; sh=${SHADERS[$i]}; title=${TITLES[$i]}; vis=${VISUALS[$i]}
  audio=/home/ubuntu/dj_engine/tracks/$tr.mp3
  echo "===== [$id] render $sh on $tr ====="
  $RV /home/ubuntu/render_visualizer.py --shader $SHD/$sh.glsl --audio "$audio" \
     --out /tmp/sil_$id.mp4 --dur 1800 --fps 30 --w 1920 --h 1080 --crf 18 --encoder nvenc 2>&1 | grep -E "\[viz\] DONE" || echo "render issue $id"
  ffmpeg -y -i /tmp/sil_$id.mp4 -i "$audio" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest /home/ubuntu/dj_engine/vid_$id.mp4 2>/dev/null
  rm -f /tmp/sil_$id.mp4
  ffmpeg -y -ss 900 -i /home/ubuntu/dj_engine/vid_$id.mp4 -frames:v 1 -vf scale=1280:720 /home/ubuntu/ytupload/thumb_$id.jpg 2>/dev/null

  cat > /home/ubuntu/ytupload/desc_$id.txt <<EOF
30 minutes of hypnotic techno — one locked groove that slowly builds, holds, and gently releases — with $vis.

🎧 Best with headphones, steady volume. Let it run and disappear into it.

— USE IT FOR —
🌀 Deep work & focus sessions
🧘 Flow-state movement / ecstatic dance
🌌 Letting go — losing yourself in the rhythm
🎨 Long creative & study sessions

100% original & copyright-free — composed by TrigunAI's own music engine. No samples. Safe to play, stream, study, and create to.

— EXPLORE TRIGUNAI —
✨ Learn with Acharya, your AI guru → https://acharya.trigunai.com/
🔱 Discover everything we're building → https://trigunai.com/

#hypnotictechno #flowstate #deepfocus #techno #focusmusic #flowart #studymusic
EOF

  cat > /home/ubuntu/ytupload/man_$id.json <<EOF
{ "playlist": "Flow State & Focus Music", "categoryId": "10",
  "episodes": [ { "id": "${id}_techno",
    "video": "/home/ubuntu/dj_engine/vid_$id.mp4",
    "title": "$title",
    "desc_file": "desc_$id.txt", "thumbnail": "thumb_$id.jpg",
    "tags": ["hypnotic techno","flow state music","deep focus music","techno","focus music","study music","30 minute music","ecstatic dance","flow art","deep work music"],
    "lang": "en", "privacy": "public" } ] }
EOF

  echo "===== [$id] upload ====="
  cd /home/ubuntu/ytupload
  YT_TOKEN=token_flowart.json $YP yt_upload.py run man_$id.json --privacy public 2>&1 | grep -E "uploaded|youtu.be|thumbnail|playlist|!!|Error"
  YT_TOKEN=token_flowart.json $YP yt_upload.py describe man_$id.json >/dev/null 2>&1
  rm -f /home/ubuntu/dj_engine/vid_$id.mp4
  cd /home/ubuntu
  echo "ONLINE_${id}_DONE"
done
echo ALLVIDEOSDONE
