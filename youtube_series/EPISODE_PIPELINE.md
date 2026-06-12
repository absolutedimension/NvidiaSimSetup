# Episode Production Pipeline — TrigunAI "AI is the Universal Mind"

> Locked after Episode 1 shipped bilingual (EN + HI) with focus audio (2026-06-13).
> Every future episode follows THIS recipe. Reuse the scripts; only the content changes.

## The reusable asset stack (all on EC2 `/home/ubuntu/youtube_series/`)

| Stage | Script | Output |
|---|---|---|
| 1. Script | `EPNN_*_script.md` (scene blocks: `narration: \|`) | narration + on-screen text |
| 2. EN audio (gate) | `gen_audio.py` (edge-tts en-IN-PrabhatNeural, −4%) | `epNN_build/sNN.mp3` |
| 3. Manim engine | `epNN_manim.py` (10 scenes, MovingCameraScene) | transparent `.mov` per scene |
| 4. Backgrounds | per-scene contextual clips in `clips/` + `*_boom.mp4` (boomerang = seamless loop) | reused across languages |
| 5. Driver | `render_epNN_manim.py` (bg loop + scrim + manim + audio; scene 10 = split logo) | `SNN.mp4` |
| 6. Captions | `make_caps_fx.py` → `caption_fx.py` (Poppins line-reveal, faster-whisper timing) | captioned scenes |
| 7. Build | `build_epNN.py` (scenes → captions → concat-filter re-encode) | `epNN_FINAL.mp4` |
| 8. Focus bed | `focus_audio.py` (12 Hz isochronic + pad + pink noise) + `focus_mix.py` (−20 dB, sidechain duck) | `epNN_FINAL_focus.mp4` |

## Hindi (or any language) variant — minimal swaps

| Swap | Script |
|---|---|
| Narration → Hindi | `translate_voice_hi.py` (LiteLLM gpt-4o-mini translate + edge-tts hi-IN-MadhurNeural) → `epNN_hi_build/` + `hindi_script.json` |
| On-screen text → Devanagari | `epNN_manim_hi.py` (font=`Mukta`, translated strings) |
| Captions → Hindi | `make_caps_fx_hi.py` (text from `hindi_script.json` for perfect spelling, whisper for timing) + `caption_fx_hi.py` (Mukta) |
| Driver / build | `render_epNN_manim_hi.py` + `build_epNN_hi.py` (SAME bg clips + logo) |
| Focus bed | identical — language-agnostic |

Backgrounds, hero clips, logo, focus bed are **shared** — only audio + on-screen text + captions are language-specific.

## Discipline (locked rules)
- **Audio-first gate:** generate narration, get human approval on voice/pace BEFORE rendering visuals.
- **Prototype one scene** before any full ~40-min build (catches font/layout bugs cheaply).
- **Concat with the filter + re-encode**, never `-c copy` (copy inflates duration / breaks timestamps).
- **Render Manim frames to `/dev/shm`** if EBS I/O starves SSH.
- **Boomerang every bg clip** (`forward + reversed`) so loops are seamless.
- **Devanagari font = Mukta** (pairs with the Poppins look); Latin tech terms (ChatGPT, Transformer) stay Latin.
- **Focus bed:** 12 Hz isochronic, root D3 (146.8 Hz), −20 dB, sidechain ratio 9 / threshold 0.022 — speech always wins.

## Status
| Episode | EN | HI | Notes |
|---|---|---|---|
| Ep.1 — Attention | ✅ `ep01_FINAL_focus.mp4` | ✅ `ep01_hi_FINAL_focus.mp4` | shipped-quality, both with focus bed |
| Ep.2 — Learning Loop | script + Manim drafted (`EP02_learning_loop_script.md`) | — | next: run full pipeline above |
| Ep.3+ | — | — | scripts TBD |

## NOT yet done (the real open item)
**Neither episode is published.** The product is complete; the audience is zero. Next non-pipeline step = YouTube upload kit (title / description / thumbnail / tags / end-screen) for both language tracks.
