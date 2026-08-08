---
name: studio-reel
description: "Make a finished vertical 9:16 REEL / SHORT (1080x1920) on the render farm — 3s hook, punchy 2-5s cuts, F5 voiceover, shader background or photoreal b-roll, BIG kinetic captions, music bed. For product/ad reels AND concept/thought-leadership reels. Use for 'make a reel', 'make a short', 'reel on <topic>', 'vertical video', or when the daily engine needs the day's hero reel. Pairs with studio-social (IG/FB) + studio-youtube (Short). NOT for long-form teaching video (studio-video) or audio-only (studio-music)."
metadata: { "openclaw": { "emoji": "🎞️", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-reel — Vertical Reels / Shorts

Re-aims the produced-video pipeline for **9:16 short-form**. Same engine as `studio-video`, tuned: 1080×1920, hook in first 3s, 2–5s cuts, BIG center captions, music-forward. Farm-aware (EC2→T4).

## 🚦 MANDATORY RAILS — read before doing anything
1. **NEVER write an ad-hoc / custom render script** (`render_*.py` you invent on the fly). You MUST use the steps below in order. If a step's tool is missing, STOP and report — do not improvise a replacement pipeline.
2. **The avatar talking intro (Step 2b) is REQUIRED on every reel** unless `avatar_bridge.sh` returns `AVATAR_CLIP=NONE` (T4 genuinely unreachable — it fails soft on its own). You do not get to skip it because it's faster. Always call `~/.openclaw/avatar_bridge.sh`.
3. The brand presenter "Acharya" is generated on the **T4 avatar box** — the reel is not "correct" without either the avatar clip composited in OR a logged `AVATAR_CLIP=NONE`. See `AVATAR_INTEGRATION.md`.

## When to Use
✅ Reels/Shorts (concept or product/ad), 15–40s, vertical.

## Step 0 — resolve farm
```bash
source ~/.openclaw/farm.sh            # FARM_NAME / FARM_IP / FARM_KEY / FARM_HOME / FARM_VID_PY / FARM_BACKEND
[ "$FARM_NAME" = none ] && { echo "no farm up"; exit 1; }
SSH(){ ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" "$1"; }
```
(For the daily engine, EC2 is preferred because IG/FB posting is EC2-only — see studio-daily.)

## Build (audio-first)
1. **Script** — a short punchy scene set (use `studio-script`; 6–9 scenes for 25–35s; hook lands its payload in 3s; narration TTS-friendly). Write it to `$FARM_HOME/reel_script.json`.
2. **Voiceover (F5)** — `SSH "cd $FARM_HOME && $FARM_VID_PY generate_voice_f5.py --script $FARM_HOME/reel_script.json --output $FARM_HOME/reel_build/"` → `full_voiceover.wav`.
2b. **Avatar talking intro (default ON)** — hand the reel's OWN voiceover to the T4 avatar box so the brand presenter "Acharya" delivers the hook, lips matched to the narration:
   ```bash
   eval "$(bash ~/.openclaw/avatar_bridge.sh --vo $FARM_HOME/reel_build/full_voiceover.wav --slug <slug> --role intro)"
   # → sets AVATAR_CLIP=<path-on-farm>/…mp4 (or NONE if the T4 is unreachable — fails soft, reel still renders)
   ```
   The clip is a full-frame talking-avatar cinematic MP4; the composite prepends its **first 3–5s as the hook**, then cuts to the shader/b-roll content. If `AVATAR_CLIP=NONE`, skip the intro and render shader-only (log it). See `AVATAR_INTEGRATION.md`.
3. **Visual** — two styles:
   - **Shader bg** (fast, default): render a 1080×1920 shader reacting to the VO (`render_shader_video` in `$FARM_BACKEND/services/shader_service.py`, width=1080 height=1920), then overlay kinetic captions (slide_service transparent PNGs) + mux VO + music bed.
   - **Photoreal b-roll**: use `studio-faceless` at 9:16 (EC2-only; LTX).
4. **Compose** — the Mode-A composite (`compose_welcome.py`-style: shader bg + scrim + BIG captions + music bed), aspect **9:16**. If `AVATAR_CLIP` is set (not NONE), **prepend the avatar hook** (its first 3–5s) before the shader body — one continuous VO. Output `$FARM_HOME/reel_out/<slug>.mp4`.

## Deliver / hand off
```bash
scp -i "$FARM_KEY" "$FARM_USER@$FARM_IP:$FARM_HOME/reel_out/<slug>.mp4" /tmp/reel.mp4
```
Then: SendUserFile to Deepak, and/or → `studio-social` (IG+FB), `studio-youtube` (Short).

## Reel craft
- **Hook in 3s** (concrete promise or provocative line). One idea per cut. End on the CTA card.
- Captions BIG, center, 1–4 words/beat. Music-forward bed (`studio-track` for a custom bed, or `ambient_low`).
- 1080×1920, 24–30 fps. Keep it 15–40s.

## Gotchas
- On the T4 fallback shaders are fast but F5/compose slower; EC2 preferred for daily runs (also required for IG/FB posting).
- Verify the output is truly 1080×1920 before handing to `studio-social` (Reels spec).
