# TrigunAI Music Pipeline — Research + Build Plan (2026-06-15)

> Goal: an end-to-end, **fully automatic, copyright-clean** music pipeline (mirror of the
> existing video pipeline) running on our own A10G GPU box — plus **two owned AI singers**
> (one male, one female) with a consistent identity across every song.
>
> Owner: Deepak. Infra: same EC2 g5.2xlarge (A10G, 24 GB VRAM) that runs the agents +
> video pipeline. LLM brain: existing LiteLLM proxy → Azure (for lyric writing).

---

## 0. The one fact that anchors everything

**ACE-Step 1.5 is already installed on our box** (CEO briefing: "ACE-Step (installed, not
yet tested)"). It is the current open-source state-of-the-art for full songs *with vocals*,
it is **MIT-licensed**, and it was **trained exclusively on licensed music + royalty-free /
public-domain + synthetic MIDI-to-audio data** — so output is safe to monetize on YouTube /
Spotify / ads. First action is not "install something," it's **"smoke-test what we have."**

---

## 1. The model landscape (open-source, today)

### Tier 1 — Full song WITH vocals + lyrics (the core engine)

| Model | License | Vocals+Lyrics | VRAM | Speed | Notes |
|---|---|---|---|---|---|
| **ACE-Step 1.5** ⭐ | **MIT** (commercial OK) | ✅ 50+ langs | 2B turbo ≤6 GB · 2B sft 6–16 GB · **XL/4B 12 GB (offload) / 20 GB rec** | **<2 s/song A100, <10 s RTX 3090** | Trained on licensed+royalty-free+synthetic → **commercially clean**. Has voice-clone via reference audio, lyric2vocal, vocal2BGM (auto-accompaniment), stem split, cover/repaint. **Fits A10G 24 GB comfortably.** Already on our box. |
| **YuE (7B)** | **Apache 2.0** | ✅ EN/中文/粤/日/韓 | 16 GB fp16 (GP build <10 GB) | Slow: ~360 s/30 s on 4090 | Strongest *structured* lyric→song; much slower than ACE-Step. Good as a quality cross-check / B-roll generator, not the default. |
| **HeartMuLa-7B** | open | ✅ multilingual | ~7B class (≈16–20 GB) | — | New (2026), claims Suno-comparable musicality. Worth benchmarking once ACE-Step is running. |
| **DiffRhythm 2** | open | ✅ | moderate | fast | Fast full-song diffusion; alternative to ACE-Step. |

### Tier 2 — Instrumental / texture only (support roles)

| Model | License | What | VRAM | Use for us |
|---|---|---|---|---|
| **MusicGen (stereo)** | **CC-BY-NC** ❌ | text→instrumental, ~30 s | 12 GB | **Avoid for commercial output** (non-commercial license). Experiments only. |
| **Stable Audio Open 1.5** | Stability Community (commercial under revenue cap) | sound design, risers, ambience, ≤47 s | 12 GB | SFX, transitions, drone/atmos beds, Flow-Art textures. |

### Tier 3 — Singing Voice Synthesis (melody you control precisely)

| Model | What | Why it matters |
|---|---|---|
| **DiffSinger** (openvpi) | score (lyrics+pitch+timing) → singing | You compose the melody (MIDI) → full control of the tune, not a dice-roll. |
| **YingMusic-Singer** (2026) | zero-shot SVS + editing, annotation-free melody | Newer, easier — clone a timbre + hum/MIDI a melody. |
| **VISinger 2** | high-fidelity end-to-end SVS | Strong quality baseline. |

> **SVS vs generation:** ACE-Step/YuE *invent* the melody from a text/lyrics prompt (fast,
> less control). SVS (DiffSinger) *renders a melody you specify* (full control, more setup).
> We want both lanes: **ACE-Step for speed/volume, SVS for "I need this exact tune."**

### Tier 4 — Voice identity / "our own singer" (the differentiator)

| Tool | License | What | Dataset need |
|---|---|---|---|
| **RVC v2** (Retrieval-based Voice Conversion) ⭐ | open (MIT-ish) | Convert ANY vocal → target singer's timbre (HuBERT + CREPE pitch). | ~20–40 min clean 44.1 kHz mono of the target voice. |
| **so-vits-svc 4.0** | open | Singing voice conversion + trained f0 predictor (auto pitch). | similar; heavier train. |
| **Ultimate RVC** | open | App wrapper: song covers + speech via RVC, batch. | — |

**This is how we get a persistent named singer.** Train one RVC model per persona →
run *every* generated vocal through it → same voice on every track. Cheap to train (small
model), runs easily on the A10G.

### Tier 5 — Production finishing (makes it "production-level")

| Tool | License | Role |
|---|---|---|
| **Demucs** (`htdemucs_ft` / **BS-RoFormer**) | MIT | Stem separation (split vocal / drums / bass / other). Best open quality in 2026. Needed to isolate the vocal before RVC, and for remixing. |
| **Matchering** | GPLv3 | Reference-based mastering — match loudness/EQ/dynamics to a reference track automatically. |
| **pyloudnorm / ffmpeg loudnorm** | open | LUFS loudness normalization (−14 LUFS for YouTube/Spotify). |
| **Ultimate Vocal Remover** | open | GUI front-end over Demucs/MDX-Net if we want manual passes. |

---

## 2. How we build "our own male + female AI singer"

The identity comes from **RVC voice models we train and own.** Two architectures, we'll use both:

### Architecture A — Generate then "singer-ize" (default, highest volume)
```
lyrics (LLM) ──▶ ACE-Step 1.5 XL ──▶ full song (vocal + instrumental)
                                          │
                            Demucs split ─┤
                                          ├─▶ instrumental stem ──────────────┐
                                          └─▶ raw vocal stem                   │
                                                   │                           │
                                  RVC convert ─────┘  (→ "Trigun-Maya" F       │
                                                        or "Trigun-Ravi" M)    │
                                                   │                           │
                                          singer-ized vocal ──── remix ◀───────┘
                                                   │
                                  Matchering + LUFS master ──▶ final.wav / .mp3
```
Same voice on every track regardless of what ACE-Step rolls. This is the consistent-persona trick.

### Architecture B — Compose then sing (full melodic control)
```
lyrics + melody (MIDI) ──▶ DiffSinger / YingMusic (with our singer's voicebank)
                                  │
                                  └─▶ vocal ── + ACE-Step instrumental (vocal2BGM) ── master
```
Use when a song needs an *exact* tune (hooks, branded jingle, a specific Flow-Art motif).

### Where the singer's VOICE comes from — copyright-safe sourcing
Do **NOT** clone a real famous artist (legal + brand risk). Build **synthetic personas**:
- **Record a consenting human** (Deepak, a friend, a hired singer) ~30 min → train RVC. Cleanest, fully owned.
- **Or synthesize a base voice** (neutral TTS / public-domain or permissively-licensed singing dataset) → train RVC on that → a 100% synthetic owned singer.
- Lock two personas: **one male, one female**, each with a name, a voicebank, and a 1-line "character" so prompts stay consistent.

---

## 3. Infra fit — does it run on our A10G (24 GB)?

| Stage | VRAM | Fits 24 GB? |
|---|---|---|
| ACE-Step 1.5 **XL** (the good one) | ~20 GB rec | ✅ yes (alone) |
| ACE-Step 1.5 **2B sft** (safe default) | 6–16 GB | ✅ easily |
| Demucs `htdemucs_ft` | ~4 GB | ✅ |
| RVC inference | <4 GB | ✅ |
| RVC training | small | ✅ |
| Matchering / LUFS | CPU | ✅ |
| YuE (cross-check) | 16 GB (GP <10 GB) | ✅ |

Everything fits on the **existing box** — no new instance. Run stages sequentially (one model
in VRAM at a time), exactly like the video pipeline does. LLM lyric-writing goes through the
**existing LiteLLM proxy** (port 4000 → Azure), $-pennies.

---

## 4. Staged build plan (mirror of the video pipeline)

| Phase | Deliverable | Effort | Gate |
|---|---|---|---|
| **M0 — Validate** ✅ DONE 2026-06-15 | Smoke-test ACE-Step on the box: text prompt → 40 s song with vocals. **Result: works.** Model loads 65 s (one-time), then **40 s of vocal music in ~7 s of diffusion**, **7.4 GB VRAM** (of 24). Installed version = **ACE-Step v1 3.5B** (MIT), model cached at `~/.cache/ace-step`. Invoke: `~/acestep_venv/bin/python` calling `acestep.pipeline_ace_step.ACEStepPipeline` (see `music_pipeline/m0_smoke.py`). Output: `m0_smoke.mp3` (brand-themed female vocal). | "Does it sound good enough to ship?" |
| **M1 — Core auto-pipeline** ✅ DONE 2026-06-15 | `make_music.py` (on box, runs in `~/acestep_venv`): preset/prompt → ACE-Step → **extend to any length** (N unique segments + seamless ffmpeg `acrossfade`) → optional **isochronic tones** (beta/alpha/theta/delta) + **432Hz tuning** (`rubberband`) → **loudnorm master** → WAV+MP3. **Validated: 30-min house+beta from one command** (5 segs → 12 crossfaded → 30:00, −14 LUFS). Presets: focus-house, meditation-432, sitar-heal, lofi, ambient, ghazal, pop. Needs `torchcodec` (installed) for `--ref` audio2audio. | One command → finished track ✅ |
| **M2 — Our singers** | Source 2 datasets (M+F, consenting/synthetic) → train 2 RVC models `Trigun-Ravi` / `Trigun-Maya` → `singerize.py` (vocal stem in → persona vocal out). | 2 sessions | Same voice across 3 different songs |
| **M3 — Full song automation** | Lyrics via LiteLLM → ACE-Step → split → RVC singer → remix → master. Plus DiffSinger lane for exact-melody jobs. | 2 sessions | Lyrics theme in → finished branded song out, no manual steps |
| **M4 — Integrate** | (a) Replace episode isochronic beds with generated score; (b) Flow-Art Movement II EDM/techno tracks; (c) wrap as a `production-music-trigunai` skill mirroring the video skill. | ongoing | Used in a shipped episode / Flow set |

---

## 5. Where this fits the company (honest framing)

This is a **tool/workshop capability, not a new product line** (same rule as the video
pipeline — we teach/use it, we don't pivot the company to it). Its real near-term value:
1. **Music beds for episodes** — replace the isochronic focus bed with original, owned score.
2. **Flow Art / Movement II** — EDM/techno/ambient for the dance practice + content. We
   literally need music for that arc; this supplies it, copyright-clean.
3. **Brand sonic identity** — owned singers can voice a channel theme / course intro sting.
4. Optional later: a **Course 5-adjacent "AI music studio"** teaching module, *parked* like
   the AI-video-studio course — not sold as SaaS.

Sequencing guard: M0+M1 are cheap and high-leverage (better episode audio now). M2–M4 are the
"own singer" investment — fun and differentiating, but schedule them **around** the July 18
course launch, not instead of it.

---

## Sources
- [Best Open Source Music Generation Models 2026 — SiliconFlow](https://www.siliconflow.com/articles/en/best-open-source-music-generation-models)
- [Deploy Open-Source AI Music Generation on GPU Cloud (YuE/ACE-Step/MusicGen/Stable Audio) — Spheron](https://www.spheron.network/blog/deploy-open-source-ai-music-generation-gpu-cloud-2026/)
- [ACE-Step 1.5 GitHub](https://github.com/ace-step/ACE-Step-1.5) · [ACE-Step 1.5 paper site](https://ace-step.github.io/ace-step-v1.5.github.io/) · [ACE-Step license/training-data — HF](https://huggingface.co/ACE-Step/Ace-Step1.5) · [ComfyUI: ACE-Step 1.5 XL commercial-grade](https://blog.comfy.org/p/ace-step-15-xl-commercial-grade-music)
- [YuE GitHub](https://github.com/multimodal-art-projection/YuE) · [YuE GPU-poor build](https://github.com/deepbeepmeep/YuEGP)
- [DiffSinger GitHub (openvpi)](https://github.com/openvpi/DiffSinger) · [Best SVS models 2026 — SiliconFlow](https://www.siliconflow.com/articles/en/best-open-source-models-for-singing-voice-synthesis) · [YingMusic-Singer paper](https://arxiv.org/pdf/2512.04779)
- [RVC GitHub (rvc-project)](https://www.eachlabs.ai/rvc-project/rvc/rvc-v2) · [so-vits-svc GitHub](https://github.com/svc-develop-team/so-vits-svc) · [Ultimate RVC](https://github.com/JackismyShephard/ultimate-rvc) · [SVS vs RVC — ACE Studio](https://acestudio.ai/blog/ai-vocal-svs-comparison-rvc/)
- [Best open-source voice cloning 2026 — Resemble](https://www.resemble.ai/resources/best-open-source-ai-voice-cloning-tools)
- [Demucs/BS-RoFormer/Spleeter 2026 benchmark](https://dev.to/codesugar_lin_037a57b06a4/htdemucs-vs-bs-roformer-vs-spleeter-a-2026-audio-source-separation-benchmark-2ll8) · [Stem separation in Python 2026](https://dev.to/stevecase430/the-best-resources-for-audio-stem-separation-in-python-2026-i5j)
</content>
</invoke>
