---
name: flowscape-video-trigunai
description: >
  Generate long-form AMBIENT DREAMSCAPE VIDEOS — celestial palaces, floating kingdoms,
  ethereal cloud realms drifting slowly for sleep / study / meditation, in the style of
  channels like YouTube @CleverSpacesGirl — 100% COPYRIGHT-CLEAN. The VIDEO analog of
  learn-dj-style-trigunai: it learns a reference channel's VISUAL GRAMMAR (the recipe:
  scene taxonomy, palette, motion, pacing) with a VLM, then RE-GENERATES everything clean
  (SDXL stills → Stable Video Diffusion living motion → motion-compensated smooth-slow →
  crossfade dissolves → your own ambient audio bed) on the EC2 A10G. Use when the user
  wants to: "make an ambient dreamscape / sleep / study / meditation video", "generate a
  CleverSpacesGirl-style video", "flowscape video", "celestial / floating-island / ethereal
  ambient loop", "learn a dreamscape channel's style", "make a calm background video", or to
  render/extend/upload one. Runs the flowscape_engine/ pipeline. Companion to
  shader-reactive-pattern-music (audio-reactive visuals) and trigunai-yt-flowart (upload).
---

# Flowscape — Ambient Dreamscape Video Engine (end to end)

Turns a reference channel's *look* into your own long-form ambient videos, copyright-clean.
Same philosophy as [[learn-dj-style-trigunai]]: **learn the GRAMMAR, regenerate clean.** The
reference videos are TEACHERS a VLM reads ONCE to extract the recipe — never source, never
trained on, never in the output. Every image is one WE generate; the audio is our own bed.

> **Copyright stance (non-negotiable):** downloaded reference videos live in `corpus/` and are
> read ONLY by the visual-grammar extractor. The trainer and the renderer touch ONLY images WE
> generated. Nothing from `corpus/` reaches a LoRA or an output frame. Audio = our own clean bed.

## 0. The box
- **EC2 A10G** `TrigunAI-Omniverse`, stable EIP **34.192.145.204** (won't change on stop/start).
  Key `~/.ssh/trigunai_key.pem`. Instance `i-047ebf759f2386e71`, us-east-1.
- **Start it:** `aws ec2 start-instances --instance-ids i-047ebf759f2386e71 --region us-east-1`
  (verify: `aws ec2 describe-instances ... --query 'Reservations[].Instances[].State.Name'`).
- Engine lives at `~/flowscape_engine/` on the box AND `flowscape_engine/` in the NvidiaSimSetup repo.
- VLM = gpt-4o-mini via the **LiteLLM proxy on :4000** (key `sk-trigunai-master-key-2026`) — the
  same proxy the Content Agents share; it auto-starts with the box (`docker ps` shows `litellm-proxy`).
- **DISK IS CHRONICALLY TIGHT** (other pipelines fill root). Check `df -h /` FIRST. Need ~15GB free
  for SDXL+SVD. If full, reclaim safely (see Gotchas) — never delete another pipeline blind.

## Pipeline (A→B→C, mirrors DJ_ENGINE)
```
pull_corpus.py         corpus/*.mp4   (TEACHER — analysis only, deletable)
  ↓ extract_keyframes.py
  ↓ visual_grammar_extract.py   → grammar/flowscape_grammar.json   (the RECIPE)
  ↓ seed_generate.py            → seeds/*.png                       (OUR clean images)
  ↓ vlm_critic.py --mode seeds  → seeds_clean/                      (curated set)
  ↓ train_lora.py               → loras/flowscape_v1/               (OUR aesthetic — Phase 2)
  ↓ scene_plan.py               → scene_plans/*.json                (shot arc)
  ↓ render_flowscape.py         → output/*.mp4                      (SDXL→SVD→smooth→+audio)
  ↓ vlm_critic.py --mode video  → gate, then trigunai-yt-flowart
```

## STAGE 1 — (optional) learn a specific channel's grammar
Needs a `cookies.txt` (YouTube bot-blocks the datacenter IP — same as the DJ engine). Export from
a logged-in browser, drop in `flowscape_engine/`.
```bash
python3 pull_corpus.py --channel https://www.youtube.com/@CleverSpacesGirl --max 12 --cookies cookies.txt
python3 extract_keyframes.py --every 20
python3 visual_grammar_extract.py --grids-per-video 3   # VLM → grammar/flowscape_grammar.json
```
**No channel handy?** A hand-seeded `grammar/flowscape_grammar.json` already ships (celestial
palace / floating island / ethereal realm + palette + prompt templates). It works well — skip
straight to Stage 3. Overwrite it with real grammar later for channel-specific fidelity.

## STAGE 2 — (optional, Phase 2) bake YOUR signature LoRA
```bash
python3 seed_generate.py --n 300              # SDXL makes clean seeds from the grammar
python3 vlm_critic.py --mode seeds --min-score 7   # auto-filter → seeds_clean/
python3 train_lora.py --name flowscape_v1 --steps 1500   # ~few A10G hrs → loras/flowscape_v1/
```
Then pass `--lora loras/flowscape_v1/pytorch_lora_weights.safetensors` to the render. Skip for a
base-model video.

## STAGE 3 — render a video  ⭐ (the PROVEN recipe, approved 2026-07-18)
```bash
python3 scene_plan.py --minutes 3 --name my_flowscape --hold 12
python3 render_flowscape.py \
  --plan scene_plans/my_flowscape.json \
  --audio /home/ubuntu/cosmic-hypnotic.mp3           # YOUR clean ambient bed
```
Per shot the renderer does exactly this (all baked into `render_flowscape.py` as the default):
1. **SDXL** still from the grammar prompt (1280×720) — the clean, on-aesthetic frame.
2. **Stable Video Diffusion** img→video, exported at **7 fps** so it's **3.5 s of real motion**
   (NOT 24 fps / 1 s — that was the bug that caused the loop-snap).
3. **Motion-compensated slow** (`ffmpeg minterpolate mci`) stretches that 3.5 s of living cloud
   drift to the full ~12 s scene — synthesizes true in-between frames along the motion, so the
   **clouds keep moving AND it's smooth** (no boomerang, no freeze).
4. **Crossfade dissolves** (`xfade`, 2 s) between scenes — no hard cuts.
5. Upscale to 1080p (NVENC) + mux YOUR ambient audio.

Output: `output/my_flowscape.mp4`. ~15 scenes for 3 min.

## STAGE 4 — verify + publish
```bash
python3 vlm_critic.py --mode video --mp4 output/my_flowscape.mp4   # frame-quality score (see caveat)
```
Then hand to [[trigunai-yt-flowart]] for upload. Caveat: the critic scores **frames only** — it is
blind to motion smoothness. Eyeball the motion yourself; the critic can't catch a boomerang.

## Dials (subjective — the user picks)
- **`--hold`** (scene length): shorter = less motion-stretch = smoother/livelier, but MORE SVD shots
  = more render time. 12 s is the validated sweet spot. 20 s stretches 3.5 s → visible softness.
- **`SVD_MOTION_BUCKET`** env (default 30): lower = calmer drift (good for sleep), higher = more motion.
- **`CROSSFADE`** env (default 2 s): longer = dreamier scene transitions.
- **Ken-Burns alternative:** `reassemble_smooth.py` fills scenes with a slow zoom on the still
  (perfectly smooth, but STATIC clouds). Deepak preferred the living SVD motion above — use Ken-Burns
  only when a scene's SVD motion is bad.

## Gotchas (hard-won, 2026-07-18)
- **Model licenses:** default **SDXL** (OpenRAIL++, commercial, ~7GB, disk-safe). Upgrade =
  FLUX.1-**schnell** (Apache-2.0, ~34GB, needs ~55GB free) via `IMAGE_MODEL=black-forest-labs/FLUX.1-schnell`.
  **NEVER** FLUX.1-**dev** commercially — its license is NON-commercial.
- **Video model = SVD, not LTX.** `snapshot_download("Lightricks/LTX-Video")` pulls the WHOLE repo
  (multi-checkpoint + 9GB T5) and blew the disk TWICE. SVD is image-conditioned, no T5, ~5GB fp16.
  Also: `imagegen.py` is model-agnostic (SDXL ⇄ Flux by env), so switching image models = one var.
- **Disk full → reclaim SAFELY:** `pip cache purge`; `docker image prune -f` (dangling only — NOT
  `container prune`, which would delete the dormant `isaaclab` container). To free real GB you must
  ask the user which big `~/` dirs are expendable — never delete another pipeline blind.
- **SVD is the cost bottleneck:** ~4 s/frame → ~110 s per 3.5 s clip. 3-min ≈ 15 shots ≈ ~27 min;
  30-min ≈ ~90 shots ≈ ~3.4 hr (render overnight, or revisit a faster motion model).
- **`export_to_video` needs opencv** — `pip install opencv-python-headless imageio imageio-ffmpeg`.
- **Transient CUDA OOM on SVD VAE decode** is harmless (chunked decode recovers) — ignore the warning.
- **Box can be stopped mid-render** (Avinash/cost). Completed `shot_*_raw.mp4` persist on EBS —
  restart + re-run the assembler (`reassemble_smooth.py` or re-render) from the finished shots.

## The honest ceiling → upgrade path
Base SDXL has no signature *consistency* across scenes — that's what the Phase-2 LoRA (Stage 2) buys.
Real channel fidelity needs the Stage-1 cookies grammar. SVD motion is subtle-drift only; for camera
moves through a scene, that's a bigger model (Wan/LTX) + more disk. Ship base first, refine per lever.

## Companion
- [[project-flowscape-engine]] — the checkpoint memory (state, recipe, lessons).
- `flowscape_engine/FLOWSCAPE_ENGINE.md` — the full engine doc.
- [[learn-dj-style-trigunai]] — the audio analog this mirrors.
- [[shader-reactive-pattern-music]] — audio-reactive visuals (different look).
- [[trigunai-yt-flowart]] — publishes the finished video.
