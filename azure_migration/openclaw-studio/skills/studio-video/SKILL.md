---
name: studio-video
description: "Produce finished narrated VIDEO on the EC2 render farm — explainer / course / module / welcome videos with audio-reactive shader backgrounds, motion graphics, real F5-TTS voices, optional lip-synced or circular presenter, kinetic captions, music bed, EN/Hindi. Use for: 'make a video', 'course/module/welcome/intro video', 'explainer video', 'narrated video', 'video with shader background', 'animated motion graphics video', 'talking-head / lip-sync video', 'YouTube video from this script', 'series episode', 'kinetic captions', 'bilingual/Hindi version'. NOT for faceless photoreal b-roll (use studio-faceless) or audio-only (use studio-music)."
metadata: { "openclaw": { "emoji": "🎬", "requires": { "bins": ["ssh", "scp"] } } }
---

# studio-video — Produced Video

Drive the TrigunAI video pipeline on the EC2 render farm: shader backgrounds + motion graphics + real voices + captions → finished MP4.

## When to Use
✅ Narrated explainers, course/module/welcome videos, series episodes, talking-head (hybrid lip-sync), reels.

## When NOT to Use
❌ Photoreal "real footage" b-roll → `studio-faceless`. ❌ Audio only → `studio-music`. ❌ No script yet → `studio-script` first.

## Modes
- **Mode A** — timed slides over a reactive shader. Fast (~5 min render). Good for reels, quick teasers.
- **Mode B** — per-scene motion graphics + shader + optional presenter. Rich, ~30–45 min render @1080p.
- **Mode C** — premium series (Manim + contextual backgrounds + word-synced captions + focus bed + EN/Hindi). ~40 min.

## Step 0 — resolve the farm (auto EC2 → T4 fallback)
Produced-video runs on EITHER farm (both have the F5/video venv + `video-creator-backend`). Resolve:
```bash
source ~/.openclaw/farm.sh   # exports FARM_NAME, FARM_IP, FARM_USER, FARM_KEY, FARM_HOME, FARM_VID_PY, FARM_BACKEND, FARM_ENV
```
- `FARM=ec2` → fast. `FARM=t4` → works but **slower** (tell Deepak: "EC2 down, rendering on the T4 fallback — slower"). `FARM=none` → both down, ask him to start one. Don't fake renders.

## Input
A scene-segmented script at `course_scripts/video_scripts/<slug>.md` (frontmatter + `## scenes`). If none exists, use `studio-script` to write one first, show Deepak, get a yes.

## Options
- **voice** (F5-TTS): `female_confident`(default) / `female_calm` / `female_friendly` / `female_excited` / `male_*`. Speed ~0.75.
- **shader**: `vocal_melt`(premium, default for tech) · `sunlit_leaves`(calm/wellness) · `cosmic_drift` · `calm_glow` · `energy_pulse` · `neon_grid` · `warm_bokeh` · `learn_focus` · `knowledge_flow` · `circuit_mind` · `deep_ocean` · `sacred_geometry`.
- **presenter**: `none` / `circular` (static photo bottom-right) / `hybrid` (Hallo lip-sync 0–30s + circular after — the stable lip-sync path). ⚠️ never full `hallo` (broken).
- **captions**: kinetic / fixed lower-third / none.
- **music**: `ambient_low` / `none`.   **aspect**: `16:9` / `9:16` (reels).

## Pipeline (farm-agnostic — uses the resolved farm)
After `source ~/.openclaw/farm.sh`, target whichever farm is up. Use `$FARM_VID_PY` (the F5/video venv) instead of `python3`, `$FARM_HOME` for paths, and `$FARM_USER@$FARM_IP`.
```bash
source ~/.openclaw/farm.sh
[ "$FARM_NAME" = none ] && { echo "both farms down — ask Deepak to start one"; exit 1; }
SSH(){ ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" "$1"; }
```
1. **Audio first (mandatory gate).** Generate per-scene narration with F5 (`$FARM_VID_PY $FARM_HOME/generate_voice_f5.py --script <script.json> --output $FARM_HOME/<build>/`), pull `full_voiceover.wav`, get Deepak's approval BEFORE the visual render.
2. **Render** (long → detached):
   - Mode A (timed slides + shader): `SSH "cd $FARM_HOME && $FARM_VID_PY compose_welcome.py"`
   - Mode B (motion graphics): `SSH "cd $FARM_HOME && $FARM_VID_PY patch_v4.py && setsid nohup $FARM_VID_PY render_v4.py > /tmp/render_v4.log 2>&1 </dev/null &"` then poll `/tmp/render_v4.log`.
   - Mode C (Manim + LTX series): **EC2 only** — Manim/LTX aren't on the T4. If `FARM=t4`, tell Deepak Mode C needs EC2.
3. **Verify:** pull 1–2 frames, Read for legibility.
4. **Deliver:** `scp -i "$FARM_KEY" "$FARM_USER@$FARM_IP:$FARM_HOME/<name>.mp4" /tmp/out.mp4` → SendUserFile. Have Deepak watch with sound.

> **T4 fallback notes:** shaders render fast (EGL); F5 voice is fine; Mode A/B work but overall slower than EC2. Mode C (Manim+LTX) and faceless (`studio-faceless`, LTX) are **EC2-only** — not replicated on the T4.

## Gotchas
- **Render on EC2 only** (no GPU here). **Audio-first gate** saves hours.
- Per-scene voice files are the frozen timing source — all visuals sync to them.
- Transparent slides are mandatory over a shader; overlays must be RGBA (`alpha_composite`, not `ImageChops.add`).
- Lip-sync: **hybrid only** (30s `avatar30.mp4` intro + circular after). Full Hallo is blown-out/broken.
- Mode B is slow (~3 fps PIL); run detached, poll the log, avoid many concurrent SSH sessions.
- EC2 `/tmp` is ephemeral; keep assets under `/home/ubuntu/`.
