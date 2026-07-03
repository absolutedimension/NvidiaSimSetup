---
name: studio-tableread
description: "Turn an MP3 (dialogue / table-read / audiobook + music) into a cinematic ANIMATED SHORT — transcribe, analyze the emotional arc, schedule camera modes, render an animated character on a lit stage in Blender, composite with synced audio + subtitles. Use for 'animate this audio', 'make a film from this MP3', 'table read to animation', 'turn this audiobook into a video', 'direct this scene'. HEAVY + slow (~4 hrs, ~$4 on EC2) — occasional showcase piece, NOT for daily reels. EC2-only (Blender + isaaclab cinematographer checkpoint). NOT for reels (studio-reel) or explainers (studio-video/faceless)."
metadata: { "openclaw": { "emoji": "🎥", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-tableread — Audio → Cinematic Animated Short

Drives `table_read_to_cinema.py` on EC2: Deepgram transcribe → LLM emotional scene breakdown → camera-mode schedule → Blender EEVEE render of the character on a mode-lit stage → composite + subtitles. **EC2-only, heavy** (~4 hrs / ~$4 for an 8.5-min short).

## When to Use
✅ An MP3 with dialogue/narration → a cinematic animated short. Occasional showcase, not daily.

## When NOT to Use
❌ Reels/Shorts → `studio-reel`. ❌ Explainers → `studio-video`/`studio-faceless`. ❌ Anything on a schedule/budget — this is slow + costs GPU hours.

## Requires (on EC2)
- `DEEPGRAM_API_KEY` in `.env` (transcription, ~$0.004/min).
- LiteLLM proxy on `localhost:4000` (scene analysis) — already running.
- `Daphne_Blender.fbx`, `hdri/` (6 mood HDRIs), trained cinematographer v4 checkpoint (isaaclab logs), `blender45`.

## Step 0 — EC2 up
```bash
source ~/.openclaw/farm.sh
[ "$FARM_NAME" != ec2 ] && { echo "table-read render needs EC2 up"; exit 1; }
SSH(){ ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"; }
```

## Run (one orchestrator, all 6 stages) — DETACHED (long)
```bash
scp -i "$EC2_KEY" /tmp/scene.mp3 "$EC2_USER@$EC2_IP:$FARM_HOME/scene.mp3"
SSH "cd $FARM_HOME && setsid nohup python3 table_read_to_cinema.py \
     --audio $FARM_HOME/scene.mp3 \
     --character $FARM_HOME/Daphne_Blender.fbx \
     --hdri-dir $FARM_HOME/hdri/ \
     --output-dir $FARM_HOME/tableread_out/ \
     --resolution 1920x1080 --fps 24 --quality final \
     > /tmp/tableread.log 2>&1 </dev/null & echo started"
# poll (this runs for hours): SSH 'tail -n 20 /tmp/tableread.log'
```
Output: `$FARM_HOME/tableread_out/audiobook_final.mp4` (+ `.srt`, `scene_breakdown.json`, thumbnails, `cost_report.json`).

## Deliver
```bash
scp -i "$EC2_KEY" "$EC2_USER@$EC2_IP:$FARM_HOME/tableread_out/audiobook_final.mp4" /tmp/short.mp4
```
→ SendUserFile, and/or `studio-youtube`.

## Gotchas
- **Very slow** (~0.33s/frame EEVEE; hours for minutes of video). Always detached + poll. Warn Deepak on cost/time before starting.
- Duration MUST match audio (`frames = int(dur_sec*fps)`). Mode switches land on beats, ≥5s per segment.
- All paths absolute; needs the v4 checkpoint + isaaclab container healthy.
- EC2-only (Blender + GPU + checkpoint) — no T4 fallback.
