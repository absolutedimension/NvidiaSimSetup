---
name: studio-flowart
description: "Turn a MUSIC track into a finished audio-reactive SHADER VIDEO (sacred-geometry / Flower-of-Life patterns that breathe and bloom to the music) for the FlowArt channel. Use for 'make a visualizer', 'flowart video', 'sacred geometry / flower of life video', 'turn this track into a video', 'focus music video', or the daily engine's FlowArt music drops (plan days 8 & 15). Renders 1080p on the EC2 A10G with NVENC, muxes the audio, hands the MP4 to studio-youtube (FlowArt channel). NOT for making the music (studio-track/studio-music) or reels (studio-reel)."
metadata: { "openclaw": { "emoji": "🌀", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-flowart — Music → Audio-Reactive Shader Video

Drives `render_visualizer_bands.py` on the EC2 A10G (NVENC, ~80fps 1080p). Bass pulses zoom, mids open the pattern, onsets trigger blooms. **EC2-only** (NVENC on the A10G; not the T4).

## When to Use
✅ A finished music track → a FlowArt visualizer video (focus/flow music drops, sacred-geometry visuals).

## Step 0 — EC2 up (NVENC-only)
```bash
source ~/.openclaw/farm.sh
[ "$FARM_NAME" != ec2 ] && { echo "FlowArt render needs EC2 (NVENC) up"; exit 1; }
SSH(){ ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"; }
```

## Render
```bash
# 0. have a track on the box (from studio-track / studio-music), e.g. ~/music_out/track.mp3
# 1. compute duration (MUST match track length or the video cuts short)
DUR=$(SSH "$FARM_VID_PY -c \"import librosa;print(round(librosa.get_duration(path='$FARM_HOME/music_out/track.mp3'),1))\"")
# 2. render the reactive shader (video-only), then mux the audio
SSH "cd $FARM_HOME && python3 render_visualizer_bands.py \
     --shader shaders/emantra_pattern.glsl --audio $FARM_HOME/music_out/track.mp3 \
     --out /tmp/vid.mp4 --dur $DUR --fps 30 --w 1920 --h 1080 --encoder nvenc \
     --nbands 8 --release 0.90 --tint 1.12,1.0,0.78 && \
     ffmpeg -y -i /tmp/vid.mp4 -i $FARM_HOME/music_out/track.mp3 -c:v copy -c:a aac -b:a 256k -shortest $FARM_HOME/flowart_out.mp4"
scp -i "$EC2_KEY" "$EC2_USER@$EC2_IP:$FARM_HOME/flowart_out.mp4" /tmp/flowart.mp4
```

## Shaders (`--shader shaders/<name>.glsl`)
`emantra_pattern` (default, Flower-of-Life), `flower_of_life_flow`, `enso_flow`, `bowl_ripples`, `sacred_geometry`, `kaleido_flow`, `lotus_deephouse`, `mercury_techno`, `vocal_melt`, `cosmic_drift`. Optional `--bg <png>` melted background; `--seed`, `--foldlo/--foldhi` for kaleidoscope, `--tint r,g,b`.

## Deliver / hand off
→ `studio-youtube` on the **FlowArt channel** (the plan's days 8 & 15 focus-music drops). For a 1-hr drop, generate an hour track first (`studio-track` / `studio-music --minutes 60`) then render.

## Gotchas
- **EC2 only** (NVENC). If the box is stopped, start it (studio-daily ensure_farm).
- **`--dur` must equal the track length** (compute via librosa) or the video ends early.
- 1080p mandala detail resists compression (~600–800 MB for a long track) — fine for upload.
