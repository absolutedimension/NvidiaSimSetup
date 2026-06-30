---
name: learn-dj-style-trigunai
description: >
  Reverse-engineer ANY DJ's arrangement style into a generative engine, then produce new
  copyright-clean tracks (any length, incl. full 1-hour sets) IN THAT DJ'S STYLE. Point it at a DJ
  (SoundCloud / YouTube / a folder of their sets): it gathers the catalog, analyzes each track's
  element-sequencing, learns the shared arrangement grammar (section structure, element-entry order,
  breakdown/build signatures, energy arc), then generates a new track that follows that grammar with
  ONE locked groove (slow filter-open build → long hold with breakdowns → wind-down). Use when the
  user wants to: "learn a DJ", "learn <name>'s style", "make a track like <DJ>", "analyze this DJ",
  "generate a set in X's style", "build a DJ engine", "hypnotic techno like Burmeister", or to add a
  new DJ to the engine. Proven on Michael Burmeister (18 sets). Runs on the EC2 A10G box.
---

# Learn-a-DJ Style Engine — end to end

Turns a DJ's catalog into a **generative arrangement engine**: learn HOW they compose (not copy any
one track), then generate new tracks in that style. Each DJ becomes a reusable profile under
`music_pipeline/dj_engine/<dj-slug>/`. Full design + the Burmeister worked example: `dj_engine/DJ_ENGINE.md`.

> **Copyright stance (non-negotiable):** the DJ's tracks are TEACHERS, never source material in the
> output. We learn the STYLE/STRUCTURE (not copyrightable) and recreate everything clean. We never
> ship stems separated from a copyrighted recording. (Same logic as the Suno/Udio lawsuits.)

## 0. The box
EC2 g5.2xlarge `i-047ebf759f2386e71` (us-east-1, A10G). **Stable EIP `34.192.145.204`** (TrigunAI-Omniverse-RTX);
older notes had changing IPs. `PEM=~/.ssh/trigunai_key.pem`. Tools live in `~/dj_engine/` + `~/make_music.py`;
audio analysis/arrangement runs in `~/audio_pipeline/venv` (librosa+soundfile+scipy), demucs in `~/m2_venv`,
music gen in `~/acestep_venv`. Repo copy of every tool: `music_pipeline/dj_engine/`.
**GPU OOM gotcha:** ComfyUI (port 8188) holds 8–15 GB → check free VRAM before generating cores; don't kill it without asking.

---

## STAGE 1 — Gather the catalog
`yt-dlp` the DJ's sets to `~/dj_engine/<slug>/`. **YouTube bot-blocks the AWS datacenter IP**
("confirm you're not a bot") → **prefer SoundCloud** (downloads cleanly from the box).
```bash
yt-dlp --flat-playlist --print "%(title)s" "https://soundcloud.com/<user>/tracks"   # scope it first
yt-dlp --ignore-errors --extract-audio --audio-format mp3 --audio-quality 5 \
  --download-archive _sc_archive.txt -o "%(playlist_index)02d - %(title).80s.%(ext)s" \
  "https://soundcloud.com/<user>/tracks"
```
HLS is slow (~40 hrs of audio = a while); run detached. ~10–20 sets is plenty to learn a grammar.

## STAGE 2 — Analyze every set
`dj_engine/batch_analyze.sh` runs `dj_arrangement_analysis.py` on each track → per-track JSON timeline
(element-sequencing grid over time: sub / kick+bass / bassline / drone / stab / hats, + auto sections
labelled intro/build/peak/breakdown). Edit `SRC`/`OUT` in the script for the DJ's folder, then:
`nohup bash dj_engine/batch_analyze.sh > /tmp/ba.log 2>&1 &` (≈25 s/set; idempotent — skips done).

## STAGE 3 — Learn the grammar
`grammar_extract.py` aggregates the JSONs → `grammar.json` + a readable `<DJ>_GRAMMAR.md`:
track length, sections/track, **element-entry order**, **element active-fraction** (the constant bed
vs the levers), **breakdown rate + what they retain**, section durations, the **energy arc**, transitions.
```bash
python3 dj_engine/grammar_extract.py --dir <slug>/analysis --out <slug>/grammar.json --md <slug>/GRAMMAR.md
```
*(Burmeister learned: ~74min/24-section template; bass+drone+kick = constant bed (0.87–0.94); hats =
the energy lever (0.62, drop to 33% in breakdowns); breakdowns ~1.3/hr × 60 s keeping bass+drone;
plateau energy arc. This is the teacher signal.)*

## STAGE 4 — Generate a track in the DJ's style  ⭐ (the PROVEN recipe)
Two steps: make clean core grooves with ACE-Step, then arrange them per the style.

**a) Core groove(s)** — `make_music.py` (copyright-clean ACE-Step). Tune the preset/prompt + `--bpm` to
the DJ's measured fingerprint (e.g. dark bass-dominant 123-BPM for Burmeister → `--style techno-hypnotic`).
```bash
~/acestep_venv/bin/python make_music.py --style techno-hypnotic --minutes 4 --seg-len 240 --unique 1 \
  --bpm 123 --seed 11 --out music_out/<slug>_core.mp3
```

**b) Arrange** — `grammar_generate.py` (runs in `audio_pipeline/venv`). THE recipe that worked:
**ONE locked groove** (single core, seamless-loop crossfade = consistent hypnotic rhythm) →
Demucs split → **slow filter-OPEN build** (intro muffled low-pass, opens to full by the peak; kick stays
OUT of the filter so the beat is crisp from early) → drone→kick→bass→hats enter gradually → **hold the
peak** → **breakdowns** (drop kick+hats, KEEP bass — the DJ's signature) → **gradual wind-down** (end on
the bed). Then a **master chain** for punch/clarity/glue.
```bash
source ~/audio_pipeline/venv/bin/activate
python3 -u dj_engine/grammar_generate.py --core music_out/<slug>_core.mp3 --minutes 60 \
  --breaks 0.40,0.70 --out dj_engine/<slug>_60min.wav
ffmpeg -y -i dj_engine/<slug>_60min.wav -af \
  "highpass=f=28,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150:makeup=2,treble=g=2.5:f=3500,loudnorm=I=-10:TP=-1:LRA=9" \
  -b:a 192k dj_engine/<slug>_60min.mp3
```
**Iterate with the user on feel** (we did v3→v9): build slower/faster, breakdown count/timing, filter
open point, isochronic ON/OFF (the DJ-engine default is OFF — pure music). Always prototype ~15 min,
open it, get approval before the full 60-min render.

## STAGE 5 (optional) — clean element library
Recreate the DJ's signature elements clean (drone, etc.) via audio2audio (`make_music.py --ref <clip>
--ref-strength 0.6`) + band-limit to the measured range. Stored in `<slug>/elements/`.

---

## Gotchas (hard-won)
- **Hypnotic = ONE locked groove.** Do NOT rotate/slice multiple cores per section — it changes the
  rhythm and kills the hypnotic feel. One core, seamlessly looped; interest comes from the arrangement
  arc, not the groove changing.
- **Demucs cache** lives in `dj_engine/_genwork/dem/` — don't delete it between runs (re-split is slow).
- **No synth-kick / no librosa beat-detection in the arranger** — it hung + mis-detected tempo (locked to
  hats at 172 BPM) and risks misalignment. Get beat punch from the **master chain** instead.
- **Killing procs over SSH often returns exit 255** (connection resets) — the kill usually still ran;
  reconnect and verify with `pgrep`. Run long jobs detached with `nohup`; Python buffers stdout → use
  `python3 -u` if you need live logs.
- **Long renders are RAM-heavy** (60 min @ 44.1 kHz ≈ several GB/array) — check `free -g` (need ~10 GB);
  `rm` the intermediate `.wav` after mastering.

## The honest ceiling → the upgrade path
This rebuilds tracks from **AI-generated + Demucs-separated** stems, which carry some smear — the master
chain tightens it but can't fully match native drum-machine crispness. For pro-tight source quality, the
real fix is **LoRA fine-tuning ACE-Step on the DJ's corpus** (see `MUSIC_PIPELINE_RESEARCH.md` §2) so the
model generates native in-style grooves. The *arrangement engine* (this skill) is the novel part and is
done; the LoRA is the source-quality upgrade.

## Companion
`production-music-trigunai` (general music) · `hypnotic-techno-trigunai` / `isochronic-deephouse-trigunai`
(style+visualizer). Memory: `project-dj-arrangement-engine`. Worked example: Michael Burmeister
(`dj_engine/burmeister/`, `burmeister_grammar.json`, `BURMEISTER_GRAMMAR.md`).
</content>
