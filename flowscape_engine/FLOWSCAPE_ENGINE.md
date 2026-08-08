# Flowscape Engine — TrigunAI

**Goal:** don't just *generate* an ambient dreamscape video — learn **how a specific
channel builds its look** (scene taxonomy, palette, lighting, motion, pacing), so our
engine produces long-form ambient videos *in that style*, and gets stronger as more of
that channel's videos are analyzed. The video analog of `music_pipeline/dj_engine/`.

Reference channel seed: **[@CleverSpacesGirl](https://www.youtube.com/@CleverSpacesGirl)**
— AI-generated celestial/fantasy dreamscapes (floating kingdoms, star-built palaces) as
long slow ambient loops for sleep / study / meditation.

> **Copyright stance (non-negotiable — identical to dj_engine):** the reference videos are
> **TEACHERS, never source material** in our output. The VLM reads them ONCE to learn the
> STYLE/GRAMMAR (not copyrightable) and the SCENE CHARACTER, then we **RECREATE everything
> clean** — every training image is one WE generated (Part B), never a downloaded frame.
> Nothing from `corpus/` is ever fed to `train_lora.py` or ends up in an output video.
> Audio is our own copyright-clean bed (ACE-Step / FlowArt stack).

Why this is clean while a naive LoRA-on-her-frames is NOT: same reason the DJ engine is
clean. We learn the **recipe** (grammar → JSON), then regenerate. We never train on, or
ship, the copyrighted pixels.

---

## The three parts (mirror of DJ_ENGINE.md A→B→C)

### Part A — Structural analysis ✅ TOOLS BUILT
`extract_keyframes.py` + `visual_grammar_extract.py`. Video analog of
`dj_arrangement_analysis.py`. A VLM (gpt-4o-mini via the LiteLLM proxy on :4000 — the
same critic the drone pipeline uses, CLAUDE.md §17.9) reads keyframe grids and emits a
machine-readable **visual grammar**:
- **scene taxonomy** (celestial_palace / floating_island / ethereal_realm / …)
- **palette** (dominant hex), **lighting**, **mood** tags
- **motion signature** (slow drift / push-in / orbit), pacing, loop feel
- **reusable prompt templates** to regenerate the look *without referencing the source*

Output: `grammar/flowscape_grammar.json` — the video engine's "element grid." Feeds Part B.

### Part B — Copyright-clean seed library ✅ TOOLS BUILT
`seed_generate.py` + `vlm_critic.py`. Video analog of the clean element library.
- Generate our OWN images from the grammar's prompt templates using a
  commercially-licensed base (**Flux.1-dev**). These live in `seeds/`.
- **VLM auto-filter** (the cheap-80%-of-RL move) scores each seed on-aesthetic /
  calming / artifact-free and copies keepers to `seeds_clean/`. This is the reward-model
  curation loop — no DDPO/DRaFT instability. Report: `seeds_clean/critic_report.json`.

`seeds_clean/` is the ONLY thing the trainer ever sees. Paper trail = "trained only on
images we generated ourselves."

### Part C — Style engine ✅ TOOLS BUILT
- **C.1 `train_lora.py`** — the "our own model" step. LoRA on `seeds_clean/` so Flux
  carries OUR signature aesthetic (consistency = the moat). Wraps diffusers' official
  Flux LoRA trainer. ~150+ images → a few A10G hours → `loras/flowscape_v1/`.
- **C.2 `scene_plan.py`** — grammar → **shot list** with a slow arc
  (establish→drift→reveal→hold→wind_down), so the video breathes instead of being one
  flat loop. Video analog of the DJ arrangement (intro→peak→breakdown→outro).
- **C.3 `render_flowscape.py`** — the assembly line: per shot, Flux+LoRA still →
  **LTX-Video** gentle 5 s motion → slow-loop pad to hold time → concat → upscale → mux
  our ambient audio → long-form MP4. Then `vlm_critic.py --mode video` gates it, and it
  hands to `trigunai-yt-flowart`.

Optional **C.2 motion LoRA**: train a second LoRA on LTX-Video using 3–5 s clips WE
generated from the seeds, to lock the *motion* signature too. Same clean principle.

---

## Pipeline at a glance

```
pull_corpus.py         corpus/*.mp4   (TEACHER — analysis only, deletable)
   ↓ extract_keyframes.py
   ↓ visual_grammar_extract.py   → grammar/flowscape_grammar.json   (RECIPE)
   ↓ seed_generate.py            → seeds/*.png                       (OUR clean images)
   ↓ vlm_critic.py --mode seeds  → seeds_clean/                      (curated trainset)
   ↓ train_lora.py               → loras/flowscape_v1/               (OUR aesthetic)
   ↓ scene_plan.py               → scene_plans/*.json                (shot arc)
   ↓ render_flowscape.py         → output/*.mp4  (Flux+LoRA → LTX → loop → +audio)
   ↓ vlm_critic.py --mode video  → gate, then trigunai-yt-flowart
```

One-shot: `./run_pipeline.sh <channel_url> <minutes> <your_ambient_audio.mp3>`

---

## Run it (on the EC2 A10G — CLAUDE.md §2)

```bash
# sync + deps
rsync -av flowscape_engine ubuntu@$EC2_IP:/home/ubuntu/
ssh ubuntu@$EC2_IP
cd ~/flowscape_engine && pip install -r requirements.txt --break-system-packages --user
# LiteLLM proxy (:4000) must be up — it already is if the Content Agents are (docker ps)

# Phase 1 — assembly line only, off-the-shelf weights, NO training yet:
python3 pull_corpus.py --channel https://www.youtube.com/@CleverSpacesGirl --max 8 --cookies cookies.txt
python3 extract_keyframes.py
python3 visual_grammar_extract.py
python3 seed_generate.py --n 40          # small, just to prove the look
python3 scene_plan.py --minutes 5
python3 render_flowscape.py --plan scene_plans/flowscape_5min.json --audio my_bed.mp3
#   → ship one 5-min video BEFORE training anything.

# Phase 2 — the real "our model": grow seeds, curate, LoRA, render 30 min:
python3 seed_generate.py --n 300
python3 vlm_critic.py --mode seeds --min-score 7
python3 train_lora.py --name flowscape_v1 --steps 1500
python3 scene_plan.py --minutes 30
python3 render_flowscape.py --plan scene_plans/flowscape_30min.json \
    --lora loras/flowscape_v1/pytorch_lora_weights.safetensors --audio my_bed.mp3
```

## Models (VERIFY each license before commercial ship)
| Role | Default | Fits A10G? |
|---|---|---|
| text→image | `black-forest-labs/FLUX.1-dev` (+ our LoRA) | ✅ cpu-offload |
| image→video | `Lightricks/LTX-Video` (+ optional motion LoRA) | ✅ easily |
| VLM critic | `gpt-4o-mini` via LiteLLM :4000 | n/a (Azure) |

Swap higher-quality motion (`Wan 2.1/2.2`) via `VIDEO_MODEL` env if you accept tighter VRAM.

## Cost
Phase 1 ≈ existing GPU hours (~$1/hr). Phase 2 LoRA train ≈ a few A10G hrs (<$20).
VLM analysis+critic ≈ pennies. No new infra — piggybacks the running LiteLLM proxy +
your ffmpeg/NVENC + FlowArt audio stack.

## ⭐ FINAL DELIVERABLE — a reusable "learn-any-dreamscape-channel" skill
Once proven end-to-end on CleverSpacesGirl, wrap A→B→C as a skill (working name
`learn-flowscape-style-trigunai`), exactly like `learn-dj-style-trigunai`: point it at any
ambient/dreamscape channel → get a clean style engine + a long-form video. Companion to
[[shader-reactive-pattern-music]] (audio-reactive visuals) and `trigunai-yt-flowart` (upload).

---
*Owner: TrigunAI Innovations. Video analog of `music_pipeline/dj_engine/`.*
