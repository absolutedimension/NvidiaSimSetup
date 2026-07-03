---
name: studio-reel
description: "Make a finished vertical 9:16 REEL / SHORT (1080x1920) on the render farm — 3s hook, punchy 2-5s cuts, F5 voiceover, shader background or photoreal b-roll, BIG kinetic captions, music bed. For product/ad reels AND concept/thought-leadership reels. Use for 'make a reel', 'make a short', 'reel on <topic>', 'vertical video', or when the daily engine needs the day's hero reel. Pairs with studio-social (IG/FB) + studio-youtube (Short). NOT for long-form teaching video (studio-video) or audio-only (studio-music)."
metadata: { "openclaw": { "emoji": "🎞️", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-reel — Vertical Reels / Shorts

Re-aims the produced-video pipeline for **9:16 short-form**. Same engine as `studio-video`, tuned: 1080×1920, hook in first 3s, 2–5s cuts, BIG center captions, music-forward. Farm-aware (EC2→T4).

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
3. **Visual** — two styles:
   - **Shader bg** (fast, default): render a 1080×1920 shader reacting to the VO (`render_shader_video` in `$FARM_BACKEND/services/shader_service.py`, width=1080 height=1920), then overlay kinetic captions (slide_service transparent PNGs) + mux VO + music bed.
   - **Photoreal b-roll**: use `studio-faceless` at 9:16 (EC2-only; LTX).
4. **Compose** — the Mode-A composite (`compose_welcome.py`-style: shader bg + scrim + BIG captions + music bed), aspect **9:16**. Output `$FARM_HOME/reel_out/<slug>.mp4`.

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
