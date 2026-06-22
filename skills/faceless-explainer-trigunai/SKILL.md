---
name: faceless-explainer-trigunai
description: >
  Faceless photoreal-b-roll explainer video factory for TrigunAI — the "ask different
  perspectives / explain it at every level" style proven on What_is_an_AI_Agent_v2.mp4.
  Turns a scene-segmented script into a finished narrated MP4 with REAL-LIFE photoreal
  AI-generated b-roll (gpt-image-1.5 → LTX-Video), a clear voiceover, word-synced
  kinetic lower-third captions, scene labels, and a soft music bed — all on the EC2
  A10G. NO talking-head / lip-sync (that's a paid-tool job; deliberately faceless).
  Use when the user wants this style: "make a perspective video", "explain it to a
  6-year-old / school / college / expert", "faceless explainer", "b-roll explainer",
  "same style as the agent video", "concept video with real footage", or to render a
  script written for this engine (e.g. course_scripts/video_scripts/*_perspective.md).
---

# Faceless Explainer Video Factory (TrigunAI)

The locked pipeline behind **What_is_an_AI_Agent_v2.mp4**. Faceless by design — real-life
photoreal b-roll carries the narration; multiple distinct shots per scene (sized to the
narration length), **no boomerang**, word-synced captions, scene labels, music bed.

> **Why faceless:** open-source lip-sync (Hallo2, etc.) on a single A10G cannot hit natural
> talking-head quality — reference-grade avatars are paid tools (HeyGen/D-ID). Decision on
> record (2026-06-19): drop the talking head, ship faceless. Don't re-litigate.

## Pipeline scripts (repo: `course_scripts/video_scripts/`, run on EC2)

| Stage | Script | What it does |
|---|---|---|
| 0. Box | — | Get current EC2 IP (changes on stop/start). `ssh ubuntu@$IP nvidia-smi`. Start ComfyUI (does NOT auto-start). |
| 1. **Audio (gate)** | `gen_agent_audio.py` | edge-tts → per-scene `sNN.mp3` + `full_preview.mp3`. **Default voice `en-GB-SoniaNeural` (clear modern British F); alt `en-GB-RyanNeural` (M).** User approves voice+pace before ANY GPU work. |
| 2. **Images** | `gen_variants.py` | Per scene, `N = clamp(round(dur/5), 1, 3)` photoreal stills via gpt-image-1.5 (1536×1024). Distinct shot prompts per scene. Writes `manifest.json` {dur, N, images, audio, label}. |
| 3+4. **Animate + composite** | `build_agent_video2.py` | Per image → LTX clip (`image_to_clip.py`, frames sized to slot, **cap 137**); concat N clips per scene (hard cut, **no boomerang**); freeze-pad to audio length; overlay scrim + Poppins lower-third **label** + faster-whisper **phrase captions** (clamped non-overlapping); per-scene audio; concat scenes; mix `bg_ambient.mp3` bed at −6%. |

## EC2 facts
- Instance `i-047ebf759f2386e71` (TrigunAI-Omniverse, A10G 24GB, us-east-1). IP changes on stop/start.
- Key: `~/.ssh/trigunai_key.pem`. Build dir `/home/ubuntu/agent_vid_build/`.
- **ComfyUI (LTX, :8188) must be started manually** after a box restart:
  `cd ~/ComfyUI && nohup ~/comfyenv/bin/python main.py --listen 127.0.0.1 --port 8188 > ~/comfy_run.log 2>&1 &` then poll `curl localhost:8188/system_stats` for 200 (~25s).
- gpt-image via LiteLLM proxy `localhost:4000` (auto-starts). Fonts: Poppins in `~/.local/share/fonts`. Music: `~/welcome_voice/bg_ambient.mp3`.

## The staged flow (follow in order)
1. **Write/segment the script** — markdown with frontmatter (voice, length, aspect) + scenes; each scene = `label`, `narration`, and 1–3 `shots` (photoreal prompts). See `school_perspective.md` / `college_perspective.md` as templates.
2. **Set the SCENES/VARIANTS/LABEL** in `gen_agent_audio.py` + `gen_variants.py` from the script (or generalize them to read the manifest).
3. **Audio first** → generate, pull, **user approves** (open the mp3). Per-scene mp3s freeze and drive all timing.
4. **Images** → `gen_variants.py`; review a contact sheet (optional gate).
5. **Build** → `build_agent_video2.py` (background + poll; ~5–15 min). Reuses existing `_vN.mp4` clips on re-runs.
6. **Verify** frames (montage + Read), pull MP4 to `course_assets/intro_out/`, user watches with sound.

## Gotchas (hard-won — respect these)
- **Azure gpt-image blocks photoreal minors** → child/young scenes must be **face-free** (teddy bear, hands, toys, objects). Reframe, don't fight the filter.
- **ComfyUI OOM/crash on long LTX clips** → frame cap 137 (~5.5s). One crash takes the whole build down unless you have the fallback.
- **Ken-Burns fallback** — if LTX fails for an image, `build_agent_video2.py` does a slow zoompan from the still (NOT a boomerang). Every image yields a clip.
- **No boomerang** — multiple distinct shots per scene fill long narration. Single-image scenes get freeze-pad to audio length (never loop/boomerang).
- **Captions** — faster-whisper word timing → phrase groups (≤4 words / ≤2s), clamp each end to the next start (`e = min(e, next_start - 0.06)`) so two captions never overlap.
- **Reuse clips on re-runs** — `build_agent_video2.py` skips LTX if `{sid}_vN.mp4` exists. To re-voice: regen audio, update `manifest.json` durations, delete `work2/*_scene.mp4` + `*_base*.mp4` (keep `_vN.mp4`), rebuild.
- **Voice swap is cheap** — clips are silent; only audio + timing change. Regen audio, update manifest dur, clear scene/base, rebuild (reuses clips).
- **Detached jobs / SSH** — launch with `setsid nohup … >log 2>&1 </dev/null & disown`; don't `pkill -f main.py` (matches your own launcher). Poll the log/output file, not stdout.

## Output
Finished MP4 → `course_assets/intro_out/`. State duration, scenes, voice. Stop the EC2 box when done rendering.

## Reference renders
- `What_is_an_AI_Agent_v2.mp4` — 5-level montage (6yo→expert), 77s, the canonical example.
- `school_perspective.md`, `college_perspective.md` — single-perspective deep-dives (next to render).
