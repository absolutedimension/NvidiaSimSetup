---
name: kids-animation-story-creator
description: >
  Turn a concept or rough idea into a fully animated, narrated kids STORY VIDEO —
  multiple cartoon characters, motion/actions, backgrounds, and voice narration
  (no lip-sync; narration carries it). Script-first: articulates & confirms the
  script, then the script drives cast, actions, scenes. Built on the AnimatedDrawings
  character factory + gpt-image + edge/Azure TTS + ffmpeg compositing on the EC2 GPU.
---

# kids-animation-story-creator

Make animated concept-explainer / storytelling videos for kids. The **script is the
source of truth** — it decides the concept, the number of characters, and each
scene's background, actions/animation, and narration. Lip-sync is intentionally NOT
used; a warm narrator/character voice is enough.

Companion to **`trigunai-kids-education`** (control tower) and **`trigunai-kids-quiz`**
(quiz shorts). Reuses the character factory + AnimatedDrawings pipeline documented in
the `project-kids-quiz-video` memory.

---

## When to invoke
"make a story to teach <concept> for kids", "animate a story about…", "explain
<concept> with cartoon characters", "kids story video", "/kids-story".

---

## STEP 0 — Articulate the script FIRST (before generating anything)

If the user gives only a concept or a vague idea, DRAFT a structured script and get a
thumbs-up before rendering (or auto-proceed if they say "just make it"). Ask ONLY for
what's missing:

- **Concept / learning goal** — what should the child understand by the end?
- **Age / grade** — default: ICSE Class 3 (~8 yrs)
- **Language** — EN / HI / both
- **Length** — default 4–6 scenes, ~60–90s
- **Characters** — reuse the house cast (Ellie 🐘 / Rio 🐯 / Milo 🐒 / Bruno 🐻) or new animals?
- **Format** — vertical 1080×1920 (Shorts/app) or landscape 1920×1080 (YouTube/app player)

Then write the script in the SCHEMA below, show it, confirm. A clear script prevents
wasted GPU renders.

---

## Script schema (drives the whole pipeline)

```json
{
  "title": "The Water Cycle Adventure",
  "concept": "how water evaporates, forms clouds, and rains back down",
  "language": "en",
  "format": "landscape",              // or "vertical"
  "characters": [
    {"id":"ellie","animal":"baby elephant","voice":"en-US-AnaNeural","personality":"curious"},
    {"id":"milo","animal":"baby monkey","voice":"en-US-AnaNeural","personality":"funny"}
  ],
  "scenes": [
    {
      "background": "sunny riverbank with green hills, flat cartoon style",
      "narration": "One hot day, Ellie saw the river water slowly disappearing!",
      "narrator_voice": "en-US-AnaNeural",     // optional; else use a character voice
      "cast": [
        {"char":"ellie","action":"think","pos":"left","enter":"none","scale":1.0},
        {"char":"milo","action":"wave","pos":"right","enter":"walk_in_right","scale":0.9}
      ],
      "caption": "Evaporation",                // optional on-screen keyword
      "duration": "auto"                        // auto = fit to narration length (min 3s)
    }
  ]
}
```

Rules the drafter follows:
- One clear idea per scene; narration ≤ ~2 sentences.
- `cast` positions: left / center / right (auto-spread if >1). `enter`: none / walk_in_left / walk_in_right / pop.
- Reuse existing characters by `id` when possible (cheaper, consistent); only generate new ones when the story needs them.
- End with a recap scene stating the concept in one kid-friendly line.

---

## Action → motion vocabulary (CURRENT — fixed set)

AnimatedDrawings BVH usable with the `fair1_ppf` retarget (the reliable set):

| Story action | Motion clip | Notes |
|---|---|---|
| wave / greet | `wave_hello` | |
| celebrate / excited / yay | `jumping` | |
| dance / silly | `dab` | |
| walk / move / travel | `zombie` | walk-in-place → slide overlay X in compositing |
| think / idle | (hold a mid frame + gentle bob) | no dedicated BVH yet |

⚠️ `jumping_jacks` (cmu1) and `jesse_dance` (rokoko) need their OWN retarget cfg, not
`fair1_ppf` — using fair1_ppf throws `'RightArm' is not in list`. To ADD actions:
drop a new **fair1** `.bvh` into `examples/bvh/fair1/` + a motion yaml, OR wire the
matching retarget (`cmu1_pfp.yaml` / rokoko) for other skeletons. Document additions here.

---

## Pipeline (on EC2 GPU — EIP 34.192.145.204, `ubuntu@`, `~/.ssh/trigunai_key.pem`)

Prereq: AnimatedDrawings env at `/mnt/work` (rebuild per session — `/mnt/work` is the
EPHEMERAL instance-store NVMe; recipe in `project-kids-quiz-video` memory).

1. **Characters** — reuse `lms/app/static/kids/characters/*` sources, or
   `factory.build(name, animal, motion)` for new ones. For each (character, action) the
   scene needs, render a **transparent clip** (one render per distinct char+action).
2. **Backgrounds** — gpt-image via litellm (`localhost:4000`, key `sk-trigunai-master-key-2026`,
   model `gpt-image-1.5`) → per-scene backdrop PNG (16:9 or 9:16, flat cartoon, no text).
3. **Compose each scene** (ffmpeg/moviepy): backdrop + overlay each character clip at
   pos/scale, loop the clip to the scene duration; `walk_in_*` = animate overlay X across.
4. **Narration** — edge-tts (`en-US-AnaNeural` kid voice; HI: `hi-IN-SwaraNeural`) or
   Azure per scene → scene audio. Scene duration = max(narration length, 3s).
5. **Assemble** — concat scenes, mux narration (+ optional soft bg music), burn `caption`
   keywords → `story.mp4` (format per script).
6. **Publish** — kids app (`lms/app/static/kids/`), YouTube kids channel via
   `publish_kids.py` (made_for_kids=True, no exam CTA), or WhatsApp.

Build status: steps 1–2, 4 = DONE/proven. Steps 3, 5 (scene compositor + assembler) =
NEW code, ~1–2 sessions. Recommended: implement as `kids_story/build_story.py` taking a
script JSON → story.mp4.

---

## Honest limitations (set expectations)
- **Fixed action set** (above) — expandable by adding BVH.
- **No character interaction** — they act side-by-side, can't hand objects / touch.
- **Static faces** — no expression changes.
- **No lip-sync** — voice narration only (by design).
- Good for **narrated concept explainers & simple stories**; not for dialogue-heavy or physically-interactive scenes.

## Guardrails
- EC2 bills **~$1/hr** — start, render the whole batch, then STOP.
- Kids-safe: gentle themes, made_for_kids, no exam CTA in kids output.
- Keep character generation prompts consistent (T-pose, white bg, thick outline) so the
  mask-based auto-rigger works — see factory prompt template in memory.

## Related
- Control tower: `trigunai-kids-education` · quiz shorts: `trigunai-kids-quiz`
- Pipeline detail + factory + gotchas: `project-kids-quiz-video` memory
- Video/publish reuse: `youtube_series/yt_upload.py`, `kids_quiz/publish_kids.py`
