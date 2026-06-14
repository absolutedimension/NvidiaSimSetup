---
name: production-music-trigunai
description: >
  Production-grade MUSIC factory for TrigunAI. Turns a prompt, style, lyrics, or
  reference track into a finished, mastered, copyright-clean audio file — songs
  with vocals, instrumental beds, focus/study music with isochronic tones, 432Hz
  meditation ragas, ghazals, lofi, ambient — any length (2 min to 2 hours), all on
  the EC2 A10G GPU box via ACE-Step. Use whenever the user wants to MAKE music or
  audio: "make music", "create a song", "generate a track", "music for the episode",
  "background music", "focus music", "study music", "meditation music", "isochronic
  tones", "432Hz", "binaural", "ghazal", "lofi", "ambient", "instrumental", "beat",
  "music bed", "background score", "sound bed", "AI singer", "sing this", "song from
  these lyrics", "make a track like <reference>", "royalty-free music", "copyright-free
  music", "music for YouTube". The agent picks a style/preset, drives make_music.py to
  a verified final MP3, and delivers it. For building NEW singers (RVC voices) see §6 (M2).
---

# TrigunAI Production Music Agent

A music pipeline that mirrors the video pipeline (`production-video-trigunai`): one
command → finished, mastered, **copyright-clean** audio on the existing EC2 A10G box.

> **Companion doc:** `MUSIC_PIPELINE_RESEARCH.md` in the repo holds the full model-landscape
> research + staged roadmap (M0–M4). This skill is the operator's manual for the M1 tool.

---

## 1. What it can make (all validated)

| Want | How |
|---|---|
| Song WITH vocals (EN/Hindi/50+ langs) | `--style pop`/`ghazal` + `--lyrics`/`--lyrics-file` |
| Hindi ghazal of viraha/love | `--style ghazal --lyrics-file couplets.txt` |
| "Make it like THIS reference" | `--ref reference.mp3 --ref-strength 0.5` (style-match, not melody-copy) |
| Upbeat house / study / focus music + isochronic tones | `--style focus-house --freq beta` |
| 432Hz Indian-classical meditation | `--style meditation-432` |
| Sitar / sarangi deep-relaxation | `--style sitar-heal` |
| Lofi chill beats | `--style lofi` |
| Ambient drone / score bed | `--style ambient` |
| ANY length (2 min → 2 hr) | `--minutes N` (seamless crossfade extend) |

---

## 2. The engine (already installed — do NOT reinstall)

- **ACE-Step v1 (3.5B)** at `/home/ubuntu/ACE-Step`, venv `~/acestep_venv`, model cached at
  `~/.cache/ace-step` (7.8 GB). **MIT license**, trained on **licensed + royalty-free +
  synthetic** data → every output is **safe to monetize** (YouTube/Spotify/ads). v1.5 exists
  (multilingual vocal clarity upgrade) — upgrade later if needed.
- Fits the **A10G (24 GB)** with huge headroom: generation uses ~7.4 GB. Coexists with the
  Content Agents + video pipeline on the same box.
- Model load ~5–65 s (warm/cold); generation ≈ **0.25× realtime** (40 s music in ~7 s; 3-min
  segment in ~30 s).

---

## 3. The tool — `make_music.py` (the whole pipeline)

Lives at `music_pipeline/make_music.py` in the repo; runs **on the box** in `~/acestep_venv`.

```bash
# the canonical examples (all work):
make_music.py --style focus-house --freq beta --minutes 30 --out study.mp3
make_music.py --style meditation-432 --minutes 20 --out morning_raga.mp3
make_music.py --style sitar-heal --minutes 30 --out sitar.mp3
make_music.py --style lofi --freq alpha --minutes 45 --out lofi.mp3
make_music.py --style ghazal --lyrics-file couplets.txt --ref ref.wav --minutes 4 --out ghazal.mp3
make_music.py --prompt "epic orchestral, taiko drums, rising tension" --minutes 2 --out trailer.mp3
```

**What it does end-to-end, automatically:**
1. **Generate** — ACE-Step from a preset or custom `--prompt` (+ `--lyrics`/`--lyrics-file` for vocals).
2. **Extend to length** — generates `--unique N` distinct segments (different seeds) and
   **seamlessly crossfades** them with ffmpeg `acrossfade` (no looping clicks). Repeats the
   set to fill `--minutes`, then trims to exact length.
3. **432Hz tuning** (optional) — `rubberband=pitch=0.981818` (auto for `meditation-432`, or `--tune432`).
4. **Isochronic tones** (optional) — `--freq beta|alpha|theta|delta` → a 210 Hz carrier gated
   at {15,10,6,3} Hz mixed under the track at `--iso-db` (default −20 dB).
5. **Master** — `loudnorm` to the preset's LUFS target (−14 music / −16 meditation), TP −1.5.
6. **Export** — `<out>.master.wav` + final `<out>.mp3` (192 kbps).

**Key flags:** `--minutes` `--seg-len`(180) `--unique`(4) `--xfade`(6) `--freq` `--iso-db`
`--tune432`/`--tune440` `--lufs` `--ref`/`--ref-strength` `--seed` `--steps`(60) `--prompt` `--lyrics`/`--lyrics-file`.

**Presets:** `focus-house · meditation-432 · sitar-heal · lofi · ambient · ghazal · pop`
(edit the `PRESETS` dict at the top of make_music.py to add more).

---

## 4. Each-session workflow

```bash
EC2_IP=<current public IP from AWS console — CHANGES on stop/start>
PEM=~/.ssh/trigunai_key.pem

# 1. box running? (agents auto-start; ACE-Step needs no service — it's a script)
ssh -i $PEM ubuntu@$EC2_IP 'nvidia-smi --query-gpu=memory.used --format=csv,noheader'

# 2. push the latest tool (after any edit)
scp -i $PEM music_pipeline/make_music.py ubuntu@$EC2_IP:/home/ubuntu/make_music.py

# 3. run a job (detached for long ones; logs to /tmp)
ssh -i $PEM ubuntu@$EC2_IP 'cd /home/ubuntu && nohup ~/acestep_venv/bin/python make_music.py \
   --style focus-house --freq beta --minutes 30 --out /home/ubuntu/music_out/out.mp3 \
   > /tmp/m1.log 2>&1 & echo pid=$!'
# watch: grep "\[m1\]" /tmp/m1.log   (ignore the tqdm bars)

# 4. deliver: pull the mp3 back, SendUserFile it
scp -i $PEM ubuntu@$EC2_IP:/home/ubuntu/music_out/out.mp3 music_pipeline/out.mp3
```

For vocals: write lyrics with `[verse]` / `[chorus]` / `[bridge]` tags; native scripts work
(Devanagari for Hindi). Audio outputs are **gitignored** (`*.mp3/*.wav`) — only scripts commit.

---

## 5. Gotchas (accumulated)

| Symptom | Fix |
|---|---|
| `--ref` fails: "TorchCodec is required" | `~/acestep_venv/bin/pip install torchcodec` (done once; needs system ffmpeg, present). |
| Hindi/Urdu vocals sound slurred | bump `guidance_scale_lyric` (make_music sets 2.5 for vocals), OR write **Romanized** Hindi ("tere jaane ke baad…") — v1 pronounces Latin more crisply. v1.5 fixes this. |
| Want instrumental, got vocals | lyrics must be `[inst]` (presets already set this for instrumental styles). |
| Reference track is long | trim a representative 60–90 s clip first (`ffmpeg -ss <t> -t 90`), upload that as `--ref`. |
| `/tmp/*.usd`-style ephemerality | host `/tmp` wipes on EC2 stop; keep refs/outputs under `/home/ubuntu/` (EBS). |
| Output too repetitive over long durations | raise `--unique` (more distinct segments) and/or `--seg-len`. |
| Isochronic tone inaudible / too loud | `--iso-db` (−20 default; −16 = clearly audible, −24 = subliminal). |

---

## 6. Roadmap beyond M1 (what's NOT built yet)

- **M2 — Own AI singers (synthetic personas):** train 2 RVC voice models (`Trigun-Ravi` M /
  `Trigun-Maya` F) so vocals carry a consistent owned identity. Pipeline: ACE-Step vocal →
  Demucs stem-split → RVC convert → remix → master. Decision on record (2026-06-15): **fully
  synthetic** voices (no human recording dependency). Tools: RVC v2, Demucs `htdemucs_ft`.
- **M3 — Full automation:** LLM (LiteLLM proxy :4000 → Azure) writes lyrics from a theme →
  song → singer → master, zero manual steps.
- **M4 — Integrate:** original music beds for YouTube episodes (replace isochronic), Flow-Art /
  Movement II tracks, and a **dedicated music YouTube channel** (faceless, copyright-clean —
  the proven Raga-Heal / Jason-Lewis format).

---

## 7. CEO framing (honest)

This is a **tool / workshop capability, not a product** (same rule as the video pipeline). Its
value: (a) original owned music beds for episodes, (b) music for the Flow-Art / Movement II arc,
(c) optional later: a faceless copyright-clean music channel as a passive owned asset. Do **not**
let it become a B2B "music-SaaS" pivot or derail the July 18 course launch — schedule M2–M4 around
it. See `trigunai-ceo` OS + `project-music-pipeline` memory.
</content>
