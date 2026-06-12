---
name: production-video-trigunai
description: >
  Production-grade video factory for TrigunAI. Turns a topic or script into a
  finished, narrated MP4 with an audio-reactive shader background, synced motion
  graphics / slides, an optional lip-synced (Hallo) or circular presenter, a
  music bed, and final compositing — all on the EC2 A10G GPU box. Use whenever
  the user wants to MAKE a video: "production video", "make a video", "course
  video", "module video", "explainer video", "welcome video", "intro video",
  "talking head / lip-sync video", "video with shader background", "animated
  motion graphics video", "narrated video", "YouTube video from this script",
  "series episode", "Manim episode", "kinetic captions", "focus / background
  music", "bilingual / Hindi version", "localize / translate a video", or asks
  to render / compose / assemble a video. The agent gathers the brief, then
  drives the full pipeline to a verified final MP4. For the premium series
  recipe (Manim engine + contextual AI backgrounds + word-synced captions +
  focus-audio bed + EN/Hindi localization) see Mode C / §9.
---

# TrigunAI Production Video Agent

You own and drive the complete video-production pipeline built in this project.
You take a brief from the user (topic / script / style / length / voice / shader /
presenter) and produce a **finished, verified, production-level MP4**.

This is not a planning agent — you **execute the pipeline** end to end: write/segment
the script, generate per-scene voiceover, render the background shader, render the
slides or motion graphics, composite everything (shader + content + presenter +
audio + music), pull verification frames, and deliver the MP4.

**Input — the video script.** Your preferred input is a script file produced by the
`video-script-writer-trigunai` skill at `course_scripts/video_scripts/<slug>.md`:
YAML frontmatter (`mode`, `voice`, `background_shader`, `presenter`, `music`,
`length_target_sec`, `aspect`) + a `## scenes` list where each `scene_0N_*` has
`narration` (→ per-scene F5 voice for exact sync), `on_screen` (title/subtitle/body/
bullets/layout → slides or motion graphics), `visual` (animation direction), and
`duration_hint_sec`. If the user gives a raw topic or hands you a long teaching doc
instead, either segment it yourself or ask them to run the script-writer first.

---

## 0. First action every session

The render GPU lives on AWS EC2 and **its public IP changes on every stop/start.**

```bash
# Confirm the box + get the CURRENT IP (AWS console: instance i-047ebf759f2386e71,
# name "TrigunAI-Omniverse", us-east-1) — then set:
EC2_IP=<current public IP>
PEM=~/.ssh/trigunai_key.pem            # also in iCloud TrigunSAI/
ssh -i "$PEM" ubuntu@$EC2_IP 'nvidia-smi --query-gpu=name --format=csv,noheader'
# Expect: NVIDIA A10G
```

If SSH fails, the box is stopped — ask the user to start it (or start via AWS).
Always re-verify the IP at the start of a job; never trust a cached one.

---

## 1. Environment (the workshop)

| Item | Value |
|---|---|
| EC2 instance | `i-047ebf759f2386e71` · TrigunAI-Omniverse · g5.2xlarge · **A10G 24 GB** · us-east-1 |
| SSH | `ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP` |
| Backend code (EC2) | `/home/ubuntu/video-creator-backend/` (services/, shaders/) |
| Backend code (repo) | `NvidiaSimSetup/video-creator/backend/` — edit here, `scp` to EC2 |
| GPU deps on EC2 | `moderngl`, `librosa` installed (`pip install --break-system-packages`), `ffmpeg` in AMI, Blender 4.5 at `blender45` |
| Python venv (fastapi etc.) | `source /home/ubuntu/audio_pipeline/venv/bin/activate` |
| Fonts (EC2) | `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` |

**Critical platform facts**
- Shader rendering needs a real GPU + EGL → **EC2 only.** It does NOT run on the Mac
  (stripped ffmpeg, no moderngl) or on Azure Container Apps (no GPU). Do all rendering
  + compositing **on EC2**, then `scp` the result to the Mac.
- The live Video Creator app (`learn.trigunai.com`) is on Azure (no GPU) — fine for the
  React UI, but its shader/render must point at the EC2 backend (`apiUrl` / SSH tunnel).

---

## 2. The pipeline components (your toolkit)

All under `video-creator/backend/services/` (repo) → `/home/ubuntu/video-creator-backend/services/` (EC2):

| Service | What it does | Key call |
|---|---|---|
| `shader_service.py` | Renders a GLSL shader → MP4, audio-reactive | `render_shader_video(shader_name, audio_path, output_path, duration, fps, width, height)` |
| `shader_translate.py` | Shader Studio (studio.trigunai.com) GLSL → pipeline GLSL | `translate_glsl(src, params) -> (glsl, report)` |
| `slide_service.py` | Renders a slide PNG; **`transparent=True`** = RGBA + scrim for shader bg | `render_slide(title, body, subtitle, layout, transparent, output_path)` |
| `render_service.py` | Assembles scenes (shader bg + transparent slide + voice) → MP4 | `render_video(project, output_path)` — set `project["background_shader"]` |
| `compositor_service.py` | Layered composite (skybox/shader/slide/presenter PiP) | `composite_scene(...)` |
| `f5tts_service.py` | F5-TTS voice (8 voices, tone+speed) | via `/api/voice/generate` or `generate_voiceover.py` |
| `hallo2_service.py` | Hallo2 lip-sync talking head (image+audio→video) | `generate_avatar(image_path, audio_path, output_path)` |
| `music_service.py` | Background music bed | `generate_music(prompt, duration, output_path)` |

**Shader contract** (every pipeline shader must fit this — `shader_service` binds ONLY these):
```glsl
#version 330
precision highp float;
uniform float u_time;        uniform vec2 u_resolution;
uniform float u_rms;  // voice volume   uniform float u_bass;
uniform float u_treble;                  uniform float u_onset; // syllables
out vec4 fragColor;          // NOT gl_FragColor
// uv = gl_FragCoord.xy / u_resolution;
```
Built-in shaders (in `SHADER_TEMPLATES`): learning set (`learn_focus`, `knowledge_flow`,
`circuit_mind`, `deep_ocean`, `sacred_geometry`), cinematic set (`energy_pulse`,
`calm_glow`, `cosmic_drift`, `neon_grid`, `warm_bokeh`), plus `vocal_melt` (premium,
liquid melt) and `sunlit_leaves` (calm botanical, original/no-copyright).
Add a Shader Studio shader: `translate_glsl(rawGLSL)` → write to `shaders/<id>.glsl` →
register in `SHADER_TEMPLATES` (or POST `/api/shader/custom`).

---

## 3. Two production modes — pick per brief

### Mode A — Timed slides (fast, ~5 min build)
Best for: a clean narrated video, talking-head intro, simple section slides.
Pattern: **keep narration intact** + one full-length shader bg + transparent slides
that fade in/out on timed windows.
Reference script: `reference/compose_welcome.py` (in this skill). It:
1. defines `SEGMENTS = [(spoken_text, slide_kwargs), ...]`
2. durations ∝ spoken length (or use per-segment audio for exact sync — preferred)
3. renders transparent slides (`render_slide(transparent=True)`)
4. renders full-length `vocal_melt` bg reactive to the narration
5. ffmpeg: shader bg + timed slide overlays (`fade=alpha`, `overlay=enable='between(t,s,e)'`) + audio
Adapt `SEGMENTS`, `AUDIO`, `SHADER`, then run on EC2.

### Mode B — Motion graphics (rich, ~30–45 min build at 1080p/30fps)
Best for: a flagship/"full-fledged" video — animated cards, build-up lists, diagrams,
glows, journey timelines — **synced to per-scene voiceover** + shader bg + Hallo/circular presenter.
Engine: `render_animated_video.py` (frame-by-frame, `render_scene_1..7`, timed to
per-scene voice files in `VOICE_DIR`). To add the shader bg + Hallo hybrid, apply
`reference/patch_v4.py` (in this skill), which rewrites the engine to:
- render every scene on a **transparent scrim** (RGBA, so the shader shows behind)
- fix `draw_glow` for RGBA (alpha_composite, not RGB `ImageChops.add`)
- composite frames over a full-length `vocal_melt` background
- overlay the 30s Hallo clip (`avatar30.mp4`) circular bottom-right for `t<30`, circular
  static presenter after
Run: `python3 patch_v4.py` → `python3 render_v4.py` (nohup, it's long).

---

## 4. The STAGED PIPELINE (the canonical flow — follow this order)

This is the production line. **Audio is generated and APPROVED before any visual work** —
because every visual is timed to the narration, so locking audio first means a pace/quality
fix never forces a visual re-render. Do NOT generate images, shaders, or frames until the
audio gate passes.

**Stage 0 — Brief + box.** Gather what's missing (script/scenes, length, target, voice +
speed, shader, presenter, mode, music). Confirm the EC2 IP + GPU (§0); `scp` any edited
services. Prefer a script file from `video-script-writer-trigunai`.

**Stage 1 — AUDIO FIRST.** Generate the **per-scene** narration (one MP3 per scene, so
timing is exact) AND a concatenated full narration. Pull the audio to the Mac.
→ **HUMAN GATE (mandatory): the user listens and approves quality + pace.**
   - Wait for explicit "audio is good" before spending a single GPU-second on visuals.
   - If not approved: adjust voice / speed / wording, regenerate, re-present. Loop here only.
   - Once approved, the per-scene MP3s are **frozen** and drive all downstream timing.
     (They persist at `ep01_build/sNN.mp3`-style paths and are reused across visual re-renders.)

**Stage 2 — ASSET GENERATION (analyze script → make every asset).** Walk the script
scene-by-scene and, for each scene, decide + generate the visual that *represents what the
narrator says* (goal: the viewer SEES it). Three asset types, each in its lane:
   - **Image-gen** (Azure gpt-image-1.5 via LiteLLM proxy :4000) → evocative *scene* art
     (a crowd, a brain, a place). Dark/cinematic, negative space for text. See `gen_assets.py`.
   - **Shaders** (GLSL, §2 contract) → living *fields* / ambient reactive backgrounds.
     Reuse a built-in or author a new one per the script's needs.
   - **Motion graphics** (programmatic PIL/numpy, per-scene) → precise *teaching diagrams*
     (labeled grids, token links, kinetic text). The bespoke build.
   Produce an **asset manifest**: scene → {shader, image(s), mg-module}. (Optional human
   gate: review generated images before rendering.)

**Stage 3 — RENDER + COMPOSITE (per-scene clips → concat).** For each scene: render its
content frames (RGBA) → composite over its reactive shader bg + its frozen audio →
**one scene clip**. Then `ffmpeg concat` all scene clips into the final MP4.
   - **Render scene-by-scene and concat** — do NOT build one giant N-overlay filtergraph
     over the whole timeline (it's O(N) slow and fragile; v1's 10-overlay stitch took ~20 min).
     Per-scene clips render fast and concat is instant. Reference engine: `render_ep01_v2.py`.
   - Presenter (if Hallo): hybrid only (30s `avatar30.mp4` + circular after).
   - Encode `libx264 -crf 20 -pix_fmt yuv420p`, `-c:a aac -b:a 192k`.

**Stage 4 — VERIFY + DELIVER.** Extract frames across several scenes, **Read them** to
confirm legibility/layout. Pull the MP4 to the Mac and `open` it. Ask the user to **watch
with sound** (frames can't confirm audio sync). Then lock or tune.

> Long renders: run with `nohup` in the background, poll artifacts (not just the log —
> Python buffers stdout). Avoid spawning many concurrent SSH sessions to the box (it trips
> sshd connection limits and SSH starts timing out even while the box is healthy).

---

## 5. Compositing recipes (ffmpeg, run on EC2)

Transparent content over shader + circular presenter for an intro window:
```
[0:v][1:v]overlay=0:0[mg];                              # shader + motion-graphics(alpha)
[2:v]scale=300:300,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(hypot(X-150,Y-150),150),0,255)'[h];
[mg][h]overlay=W-370:H-370:enable='lt(t,30)',format=yuv420p[v]
```
Timed slide windows (Mode A): per slide
`fade=t=in:st=S:d=0.4:alpha=1,fade=t=out:st=E-0.4:d=0.4:alpha=1` then
`overlay=0:0:enable='between(t,S,E)'`.
Audio: concat per-scene voice (+ silence gaps) → mix bg music
`[1:a]volume=0.07,afade=in:0:3,afade=out:end-3:3[m];[0:a][m]amix=inputs=2:duration=first`.

---

## 6. Gotchas (hard-won — respect these)

- **IP changes every stop/start** — re-fetch it first (§0).
- **Render on EC2 only** — Mac ffmpeg lacks `drawtext`/full filters; no moderngl. Composite on EC2.
- **Transparent slides are mandatory for shader bg** — `render_slide(transparent=True)`.
  Opaque slides hide the shader. Knocking out an opaque bg via colorkey looks muddy — don't.
- **`draw_glow` / RGBA** — any PIL frame meant to overlay a shader must be RGBA; `ImageChops.add`
  with an RGB overlay throws "images do not match". Use `alpha_composite` (see `patch_v4.py`).
- **Hallo is a rabbit hole** — only the 30s `avatar30.mp4` (chunk00) is clean; full-length
  lip-sync is unoptimized and came out blown-out/white. **Use the hybrid** (Hallo intro + circular).
  And the Hallo clip's lips must match the audio under it — if the intro audio changed,
  regenerate the clip from that exact segment (`scene_01` audio).
- **Per-scene voice = exact sync.** Estimating slide timing by text length drifts off the
  narration. Generate one audio file per scene and time slides to those durations.
- **Motion-graphics render is slow** (~3 fps PIL → ~30–45 min for 4.5 min @1080p/30fps).
  Run with `nohup` in the background; watch the frame count + log; pull frames at the end.
  Shader render itself is fast (~28s per 30s @1080p).
- **Local temp fills up** — you pull many frames/MP4s; periodically `rm /tmp/*.jpg /tmp/*.mp4`
  and clear large files in the session tasks dir.
- **`/tmp` on EC2 is ephemeral** (wiped on stop) — keep source assets under `/home/ubuntu/`.
- **Verify by frames, but lip-sync + audio-sync need the user's ears** — always end by
  asking them to watch with sound.

---

## 7. Key assets on EC2 (reusable)

- `/home/ubuntu/render_animated_video.py` — motion-graphics engine (v3)
- `/home/ubuntu/render_v4.py` + `patch_v4.py` — shader+Hallo version
- `/home/ubuntu/welcome_voice/` — per-scene F5 voice (`scene_01_hook.mp3` … `scene_07_cta.mp3`), `bg_ambient.mp3`
- `/home/ubuntu/presenter_avatar.png` — presenter still (circular)
- `/home/ubuntu/avatar30.mp4` — clean 30s Hallo lip-sync clip
- `/home/ubuntu/full_voiceover.mp3` — full narration (shader reactivity source)
- `video-creator-backend/shaders/*.glsl` — shader library

Reference scripts shipped with this skill: `reference/compose_welcome.py` (Mode A),
`reference/patch_v4.py` (Mode B shader+Hallo), `reference/shader_translate.py` (GLSL import).

---

## 8. Output + handoff

Deliver finished MP4 to `NvidiaSimSetup/course_assets/intro_out/`. State duration, size,
which shader/voice/presenter/mode were used, and the verification frames you checked.
Then ask the user to watch with sound and say **"lock it"** or what to tune (timing,
copy, colors, shader, music, presenter). Once locked, that build is the reusable template
for the next videos in the series.

---

## 9. Mode C — SERIES EPISODE pipeline (latest · the flagship "AI is the Universal Mind" recipe)

The premium recipe used to ship **Episode 1: Attention** bilingual (EN + हिंदी). Richer than
Modes A/B: it replaces PIL motion-graphics + shader bg with a **Manim engine + contextual AI
backgrounds + word-synced kinetic captions + a research-grounded focus-audio bed**, and adds a
**one-swap localization** path. All files live in `NvidiaSimSetup/youtube_series/` (Mac) and
`/home/ubuntu/youtube_series/` (EC2). **Full reference: `youtube_series/EPISODE_PIPELINE.md`.**

### The stack (per language)
| Stage | Script | Output |
|---|---|---|
| Script | `EPNN_*_script.md` (scene blocks with `narration: \|`) | narration + on-screen text |
| **Audio gate** | `gen_audio.py` (edge-tts `en-IN-PrabhatNeural`, rate −4%) | `epNN_build/sNN.mp3` + full preview → **human approves** |
| Manim engine | `epNN_manim.py` — 10 `MovingCameraScene` scenes, rendered `--transparent` (.mov w/ alpha) | per-scene motion graphics |
| Backgrounds | per-scene **contextual** clips: image-gen (gpt-image-1.5) → **LTX-Video i2v** (`gen_scene_bgs.py`, `image_to_clip.py`); hero scenes use LTX hero clips. Then **boomerang** each clip (`forward + reversed`) for seamless loops | `clips/bg_sNN_boom.mp4` |
| Driver | `render_epNN_manim.py` — per scene: loop bg (native speed) + text-safe scrim + manim overlay + frozen audio; **final scene = split layout** (text top / spinning Trigun logo bottom) | `SNN.mp4` |
| Captions | `make_caps_fx.py` (faster-whisper word timing) → `caption_fx.py` (Poppins **line-reveal** kinetic caption, fixed lower-third) | captioned scenes |
| Build | `build_epNN.py` (scenes → captions → **concat-FILTER re-encode**) | `epNN_FINAL.mp4` |
| **Focus bed** | `focus_audio.py` (12 Hz isochronic + warm pad + pink noise) + `focus_mix.py` (−20 dB, sidechain duck under voice) | `epNN_FINAL_focus.mp4` |

### Bilingual / localization — minimal swaps (backgrounds, logo, focus bed are SHARED)
| Swap | Script |
|---|---|
| Narration → target lang | `translate_voice_hi.py` (LiteLLM `gpt-4o-mini` translate + edge-tts `hi-IN-MadhurNeural`) → `epNN_hi_build/` + `hindi_script.json` |
| On-screen text → script | `epNN_manim_hi.py` (font **`Mukta`** for Devanagari; keep Latin tech terms in Latin) |
| Captions → target lang | `make_caps_fx_hi.py` (**caption TEXT from the approved `hindi_script.json` = perfect spelling**, whisper for TIMING only) + `caption_fx_hi.py` (Mukta) |
| Driver / build | `render_epNN_manim_hi.py` + `build_epNN_hi.py` (reuse the SAME bg clips + logo) |

### Mode-C gotchas (in addition to §6)
- **Concat with the filter + re-encode, never `-c copy`** — chained `-c copy` inflates duration /
  corrupts timestamps. Use `[i:v][i:a]…concat=n=N:v=1:a=1` in one pass.
- **Boomerang every bg clip** — a native `-stream_loop` hard-cuts at the seam (visible "replay");
  `forward + reversed` removes it. (Do NOT `setpts`-stretch a short clip to fill — it stutters.)
- **Manim frames can starve EBS I/O** → render to `/dev/shm` (RAM disk) if SSH freezes.
- **Devanagari = Mukta** (installed in `~/.local/share/fonts`, pairs with the Poppins look);
  Noto Sans Devanagari is the fallback.
- **Captions: use the script for TEXT, whisper for TIMING** — auto-transcription drops Hindi
  nukta/diacritics (e.g. पढ़ते→पडते). The approved script text is the source of truth.
- **Focus bed is language-agnostic** — generate at each video's exact duration; settings locked:
  12 Hz isochronic, root D3 (146.8 Hz), −20 dB, `sidechaincompress threshold=0.022:ratio=9:attack=5:release=320` so speech always wins. Evidence: amplitude-modulation 12–20 Hz boosts sustained attention (Northeastern 2024); pink noise masks distraction.
- **Prototype ONE scene** (manim + bg + caption) before any full ~40-min build — catches font/
  layout/order bugs cheaply.

### Status
Ep1 shipped bilingual: `ep01_FINAL_focus.mp4` (EN, 341s) + `ep01_hi_FINAL_focus.mp4` (HI, 408s),
both surfaced in `youtube_series/worldview.html` (embedded player w/ EN/हिंदी toggle).
Next episodes: drop a new script into this exact machine.
