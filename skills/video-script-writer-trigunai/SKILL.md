---
name: video-script-writer-trigunai
description: >
  Turns a course module, topic, or rough outline into a finished, scene-segmented
  VIDEO SCRIPT in the exact format the `production-video-trigunai` skill consumes.
  It writes the narration (tuned for TTS), breaks it into timed scenes, specifies
  the on-screen content + visual direction for each, and sets the production
  settings (mode, voice, shader background, presenter, music). Use whenever the
  user wants to: "write a video script", "generate the script", "script for module
  N", "turn this outline into a video script", "make a script for the production
  video", "prep a module for video", or asks for the input to the video factory.
  Output is a ready-to-render script the production skill reads directly.
---

# TrigunAI Video Script Writer

You convert teaching content → a **production-ready video script** that drops straight
into `production-video-trigunai`. You are the front of the pipeline:

```
topic / module outline  →  [video-script-writer-trigunai]  →  video script (.md)
                                                                     │
                                                                     ▼
                                                        [production-video-trigunai]  →  finished MP4
```

You do NOT render anything. You produce the **script file** (narration + scenes +
settings). When you're done, tell the user to run `/production-video-trigunai` on it.

---

## 1. Source content (read these first)

| Source | Use |
|---|---|
| `course_scripts/MODULE_NN_SCRIPT.md` | Full teaching script for a module (lectures, `[T1]–[T7]` tags) — the richest source |
| `course_scripts/SCRIPT_TEMPLATE.md` | Section/template conventions to respect |
| `COURSE_OUTLINE.md` | The 11-module course outline — pull a module's scope/objectives |
| `COURSE_SELECTION.md` | Course strategy / audience / positioning |
| `course_assets/WELCOME_VIDEO_SCREENPLAY.md` + `WELCOME_VOICEOVER_SCRIPT.txt` | The proven welcome-video script — reference for tone + scene shape |

If the user names a module, read its `MODULE_NN_SCRIPT.md`; if only a topic, draft from
the outline + your knowledge. Always ground in the **ZenSpace** project arc and the
"AI writes the code (Claude Code), you build in VR" differentiator the course leans on.

---

## 2. The OUTPUT FORMAT (the contract — produce exactly this)

Write to `course_scripts/video_scripts/<slug>.md`. Two parts: YAML frontmatter (global
production settings) + a `## scenes` list. `production-video-trigunai` reads narration
per scene (→ per-scene F5 voice for exact sync) and `on_screen` (→ slides / motion graphics).

```markdown
---
title: "Module 1 — Your First VR Scene"
video_type: module_intro        # welcome | module_intro | full_lesson | youtube_teaser | reel
length_target_sec: 270
mode: B                          # A = timed slides (fast)  |  B = motion graphics (rich)
voice: { name: female_confident, speed: 0.75 }   # F5 voices; default female_confident
background_shader: vocal_melt    # vocal_melt (premium) | sunlit_leaves (calm) | cosmic_drift | learn_focus | knowledge_flow | ...
presenter: hybrid                # none | circular | hallo | hybrid (Hallo 0-30s + circular after)
music: ambient_low               # ambient_low | none
aspect: 16:9                     # 16:9 | 9:16 (reels)
---

## scenes

### scene_01_hook
narration: |
  By the end of today, your first VR scene will be running on your Quest headset.
  Not a tutorial. YOUR scene, on YOUR headset.
on_screen:
  title: Your First VR Scene
  subtitle: Today
  body: Running on YOUR Quest headset
  layout: center
visual: logo top; fade-up titles; presenter circle bottom-right
duration_hint_sec: 16

### scene_02_promise
narration: |
  ...
on_screen:
  title: ...
  bullets: ["...", "..."]      # for build-up lists
  layout: bullets
visual: feature list builds one-by-one synced to narration
duration_hint_sec: 22
```

Field rules:
- **`narration`** is the spoken script — write it for the EAR and for **F5-TTS**:
  short sentences, natural rhythm, spell tricky terms phonetically if needed, no
  markdown/emoji/parentheticals inside it. One idea per scene.
- **`on_screen`** = what's drawn: `title` / `subtitle` / `body` / `bullets` /
  `layout` (`center|left|bullets|split|diagram`). Keep text short — it sits over a shader.
- **`visual`** = direction for the motion-graphics engine (Mode B) — animation intent.
- **`duration_hint_sec`** ≈ spoken length; the producer makes it exact from the rendered voice.
- **scene ids** like `scene_01_hook` … `scene_07_cta` (the motion-graphics engine maps
  per-scene voice files by this id — keep them ordered `scene_0N_...`).

---

## 3. How to write a good script (craft rules)

- **Hook in the first 8 seconds** — state the concrete outcome ("by the end of this you
  will have X"). Front-load the point; conclusion first, then the explanation.
- **One concept per scene.** 5–9 scenes for an intro/teaser; more for a full lesson.
- **Scene length 12–30s** for intros; never wall-of-text a slide.
- **Teach by showing the arc**: hook → what you'll build → why it's different → the
  journey/steps → credibility → CTA ("let's start").
- **Voice = Deepak's**: built EnergyField (Meta alpha), "I'll show you every step, every
  bug, every fix." Confident, practical, not hypey. Don't claim certifications carry
  market weight or invent student numbers.
- **Match settings to content**: coding/tech module → `vocal_melt` or `circuit_mind`;
  calm/wellness → `sunlit_leaves`; teaching-heavy → `learn_focus`/`knowledge_flow`.
  Reels → `aspect: 9:16`, Mode A. Flagship intro → Mode B + `presenter: hybrid`.
- **Honesty guardrails** (shared with the CEO OS): no inflated claims, no "industry-
  recognized certification," no fake metrics.

---

## 4. Workflow

1. Identify the target: which module / topic / video_type, and any settings the user
   specified. Ask only what you can't infer.
2. Read the source (`MODULE_NN_SCRIPT.md` / `COURSE_OUTLINE.md`).
3. Choose `mode`, `background_shader`, `presenter`, `length` to fit the content (recommend,
   let the user override).
4. Write the full script in the §2 format — real narration for every scene, real on-screen
   content, scene ids ordered.
5. Save to `course_scripts/video_scripts/<slug>.md`.
6. Tell the user: review/edit the narration if they want, then run
   **`/production-video-trigunai`** pointed at that file. Mention they can tweak any
   frontmatter setting (shader, voice, presenter, mode) before rendering.

---

## 5. Quick reference — production settings the producer understands

- **Shaders**: `vocal_melt`, `sunlit_leaves`, `cosmic_drift`, `calm_glow`, `energy_pulse`,
  `neon_grid`, `warm_bokeh`, `learn_focus`, `knowledge_flow`, `circuit_mind`, `deep_ocean`,
  `sacred_geometry` (+ any pasted Shader Studio shader).
- **Voices** (F5): `female_confident` (default), `female_excited`, `female_calm`,
  `female_friendly`, and `male_*` equivalents; `speed` ~0.75.
- **Modes**: A = timed slides (fast ~5 min build); B = motion graphics (rich, ~30–45 min build).
- **Presenter**: `hybrid` = Hallo lip-sync for the 0–30s intro, circular photo presenter
  after (the only reliable lip-sync path — full-length Hallo is unoptimized).

When the script is ready, the handoff line is: "Script saved at
`course_scripts/video_scripts/<slug>.md` — run `/production-video-trigunai` to render it."
