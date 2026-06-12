# Local LTX-Video image→clip stage (ComfyUI on the A10G)

Animates our generated still images (party, brain, spotlight, …) into short clips —
self-hosted, **$0/clip** (just GPU time you already pay), ~30s per 4-second clip.
Installed 2026-06-12. Validated on `img_party_crowd.png` → `party_test.mp4`.

## What's installed (on EC2, persists on EBS)
- **ComfyUI** at `/home/ubuntu/ComfyUI` + venv `/home/ubuntu/comfyenv` (torch 2.6.0+cu124)
- **LTX node:** `custom_nodes/ComfyUI-LTXVideo`
- **Model:** `models/checkpoints/ltxv-2b-0.9.8-distilled.safetensors` (2B distilled — fast, fits 24 GB)
- **Text encoder:** `models/text_encoders/t5xxl_fp8_e4m3fn.safetensors`
- **Pipeline script:** `/home/ubuntu/image_to_clip.py` (also in repo `youtube_series/`)

## Start the ComfyUI server (REQUIRED after every box stop/start)
```bash
cd /home/ubuntu/ComfyUI && nohup /home/ubuntu/comfyenv/bin/python main.py \
  --listen 127.0.0.1 --port 8188 --disable-auto-launch > /tmp/comfy_server.log 2>&1 &
# wait ~30s, confirm:  curl -s http://127.0.0.1:8188/system_stats
```

## Make a clip from a still
```bash
/home/ubuntu/comfyenv/bin/python /home/ubuntu/image_to_clip.py \
  --image youtube_series/assets/img_party_crowd.png \
  --prompt "a crowded party, dark silhouettes, gentle ambient motion, one figure glowing warmly, cinematic" \
  --out /home/ubuntu/youtube_series/clips/party.mp4 \
  --frames 89 --width 768 --height 448 --steps 10
```
- `--frames` (8k+1): 89 ≈ 3.5s, 121 ≈ 4.8s · `--width/--height` multiples of 32, 16:9-ish
- Output is mp4. ~30s/clip at 768×448.

## How it wires into the video pipeline
It **replaces the Ken-Burns step** for the image (“imagine this”) scenes. In the Manim
driver (`render_ep0N_manim.py`), for image scenes, instead of zoompan on the *still*,
generate a clip first and use the clip as the backdrop under the Manim text overlay:
`image → image_to_clip.py → clip.mp4 → [clip][manim_overlay]overlay → scene clip`.
Keep Manim for teaching diagrams; use LTX clips only for the evocative hero scenes.

## Honest notes
- Quality: good for stylized/illustrated (our style). Not photoreal-grade — fine, we don't need it.
- Distilled 2B + KSampler(steps=10, cfg=1, sgm_uniform) validated. For higher quality, try the
  13B model or LTXVScheduler+SamplerCustom (slower).
- This is **Phase-2 polish.** The Manim engine already delivers dynamism. Use LTX clips on
  hero scenes *after* the episodes are published — let real viewers tell you which scenes need it.
