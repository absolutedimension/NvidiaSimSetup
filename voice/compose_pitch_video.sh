#!/bin/bash
# Compose the TrigunAI pitch video:
# - Splice 6 mode videos to match narration timing
# - Add TTS narration as primary audio
# - Add subtitles
# - Add quiet background music (cosmic-hypnotic)
# - Add mode label + TrigunAI watermark text overlays

set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODES_DIR="$DIR/demo_package/modes"
VOICE_DIR="$DIR/voice"
OUT_DIR="$DIR/demo_package"

NARRATION="$VOICE_DIR/narration_pitch.mp3"
SRT="$VOICE_DIR/narration_pitch_corrected.srt"
MUSIC="$DIR/cinematographer_vr_handoff/reference_render.mp4"  # extract audio from this, or use cosmic-hypnotic if available

# Duration of narration
DURATION=28.4

echo "=== Step 1: Cut mode segments to match narration timing ==="
# Mode schedule timed to narration:
# 0.0-5.0s  BEAUTY   "Trigunaï Innovations... deep-tech company"
# 5.0-10.0s HERO     "connective tissue of physical AI"
# 10.0-15.0s EPIC    "train autonomous camera policies"
# 15.0-19.0s ENERGY  "deploy to real hardware"
# 19.0-24.0s INTIMATE "dance, performance, live event"
# 24.0-28.4s HERO    "creative pipelines and drone hardware"

# Cut segments from each mode video (start from different points for variety)
ffmpeg -y -ss 2  -t 5.0 -i "$MODES_DIR/mode_beauty_25s.mp4"   -an -c:v libx264 -crf 18 /tmp/seg_01_beauty.mp4
ffmpeg -y -ss 5  -t 5.0 -i "$MODES_DIR/mode_hero_25s.mp4"     -an -c:v libx264 -crf 18 /tmp/seg_02_hero.mp4
ffmpeg -y -ss 3  -t 5.0 -i "$MODES_DIR/mode_epic_25s.mp4"     -an -c:v libx264 -crf 18 /tmp/seg_03_epic.mp4
ffmpeg -y -ss 8  -t 4.0 -i "$MODES_DIR/mode_energy_25s.mp4"   -an -c:v libx264 -crf 18 /tmp/seg_04_energy.mp4
ffmpeg -y -ss 4  -t 5.0 -i "$MODES_DIR/mode_intimate_25s.mp4" -an -c:v libx264 -crf 18 /tmp/seg_05_intimate.mp4
ffmpeg -y -ss 12 -t 4.4 -i "$MODES_DIR/mode_hero_25s.mp4"     -an -c:v libx264 -crf 18 /tmp/seg_06_hero2.mp4

echo "=== Step 2: Concatenate with crossfade transitions ==="
# Create concat list
cat > /tmp/pitch_segments.txt << 'EOF'
file '/tmp/seg_01_beauty.mp4'
file '/tmp/seg_02_hero.mp4'
file '/tmp/seg_03_epic.mp4'
file '/tmp/seg_04_energy.mp4'
file '/tmp/seg_05_intimate.mp4'
file '/tmp/seg_06_hero2.mp4'
EOF

# Concatenate (simple concat - crossfade adds complexity for minimal gain)
ffmpeg -y -f concat -safe 0 -i /tmp/pitch_segments.txt \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  /tmp/pitch_video_raw.mp4

echo "=== Step 3: Add narration + subtitles ==="
# Overlay subtitles with clean styling
ffmpeg -y -i /tmp/pitch_video_raw.mp4 -i "$NARRATION" \
  -vf "subtitles=${SRT}:force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,MarginV=40'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -map 0:v -map 1:a -shortest \
  /tmp/pitch_video_narrated.mp4

echo "=== Step 4: Add mode labels + TrigunAI watermark ==="
# Add "TRIGUNAÏ" watermark top-left and mode name top-right
# Mode labels change at: 0=BEAUTY, 5=HERO, 10=EPIC, 15=ENERGY, 19=INTIMATE, 24=HERO
ffmpeg -y -i /tmp/pitch_video_narrated.mp4 \
  -vf "\
drawtext=text='TRIGUNAÏ':fontcolor=white:fontsize=28:x=30:y=30:shadowcolor=black:shadowx=2:shadowy=2,\
drawtext=text='AI Cinematographer':fontcolor=white@0.7:fontsize=18:x=30:y=65:shadowcolor=black:shadowx=1:shadowy=1,\
drawtext=text='BEAUTY':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,0,5)',\
drawtext=text='HERO':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,5,10)',\
drawtext=text='EPIC':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,10,15)',\
drawtext=text='ENERGY':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,15,19)',\
drawtext=text='INTIMATE':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,19,24)',\
drawtext=text='HERO':fontcolor=white:fontsize=24:x=w-tw-30:y=30:shadowcolor=black:shadowx=2:shadowy=2:enable='between(t,24,30)'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a copy \
  "$OUT_DIR/pitch_video_final.mp4"

echo ""
echo "=== DONE ==="
ls -lh "$OUT_DIR/pitch_video_final.mp4"
echo ""
echo "Output: $OUT_DIR/pitch_video_final.mp4"
