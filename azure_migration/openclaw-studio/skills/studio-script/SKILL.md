---
name: studio-script
description: "Write the scene-segmented SCRIPT (or song LYRICS) that the production skills consume. Use BEFORE studio-video / studio-faceless when there is no script yet, or when the user says 'write a script', 'script for a video about X', 'turn this outline/topic into a video script', 'write lyrics', 'write a song about X'. Produces the exact frontmatter+scenes format studio-video/studio-faceless read. Runs locally on this box (no GPU/SSH needed)."
metadata: { "openclaw": { "emoji": "✍️" } }
---

# studio-script — Scripts & Lyrics

Writing-only. Produce the input that the production skills render. No SSH/GPU.

## When to Use
✅ Need a video script before rendering; need lyrics before `studio-music`.

## A. Video script format (for studio-video / studio-faceless)
Save to `course_scripts/video_scripts/<slug>.md`. Frontmatter + ordered `## scenes`.

### Produced video (studio-video):
```markdown
---
title: "Module 1 — Your First VR Scene"
video_type: module_intro        # welcome | module_intro | full_lesson | youtube_teaser | reel
length_target_sec: 270
mode: B                          # A=fast slides | B=motion graphics | C=premium series
voice: { name: female_confident, speed: 0.75 }
background_shader: vocal_melt
presenter: hybrid                # none | circular | hybrid
music: ambient_low               # ambient_low | none
aspect: 16:9                     # 16:9 | 9:16
---

## scenes

### scene_01_hook
narration: |
  By the end of today, your first VR scene runs on your Quest headset.
on_screen:
  title: Your First VR Scene
  subtitle: Today
  layout: center
visual: fade-up titles; presenter circle bottom-right
duration_hint_sec: 16
```

### Faceless explainer (studio-faceless) — per scene uses `label` + `shots`:
```markdown
---
title: What is an AI Agent? — for a college student
slug: college_perspective
voice: en-GB-SoniaNeural, rate -2%
length_target_sec: 95
aspect: 16:9
---

## scenes

### s01_frame
label: "Ask a college student"
narration: |
  You've used ChatGPT — one call, text in, text out. An agent wraps that model
  in a loop and gives it hands: tools it can actually call.
shots:
  - A college student at a laptop with a chat UI, campus, candid
  - Close-up of a terminal glowing on a laptop in a warm room
```

### Rules
- **Scene IDs ordered** `scene_01_… / s01_…` — the engine maps per-scene voice by this id.
- **narration** is for TTS: short sentences, natural rhythm, spell tricky terms phonetically, NO markdown/emoji/parentheticals inside.
- **on_screen.layout** mandatory for produced video (`center|left|bullets|split|diagram`).
- **shots** (faceless): 1–3 distinct photoreal prompts per scene; face-free for child scenes.
- **Craft:** hook in first 8s (concrete outcome) → one concept/scene → arc: hook → promise → why different → steps → credibility → CTA. Deepak's voice: practical, no hype, no fake metrics.

## B. Lyrics (for studio-music)
Plain text file. Tag sections; native scripts OK (Romanized Hindi often sounds crisper on v1):
```
[verse]
line one ...
line two ...
[chorus]
hook line ...
[bridge]
...
```
Instrumental → a single `[inst]` line. Save to a file, then hand off to `studio-music --lyrics-file`.

## Handoff
After writing: "Script ready at `<slug>.md` — want me to render it with studio-video / studio-faceless?" (or for lyrics, "→ studio-music").
