# DJ Arrangement-Learning Engine — TrigunAI

**Goal:** don't just *generate* hypnotic techno — learn **how a specific DJ arranges** it (which
elements, introduced in what order, with what build/breakdown structure), so our engine composes
*tracks* (with a story arc) instead of loops. Get stronger as more of this DJ's tracks are fed in.

Reference DJ/track seed: `cosmic-hypnotic.mp3` (72 min, 123 BPM, F# minor — see fingerprint in
`MUSIC_PIPELINE_RESEARCH.md`).

**The teacher DJ = Michael Burmeister** (Wiesbaden/Frankfurt; hypnotic/chill dub-techno ~120–140 BPM).
His own bio names the exact skill we're learning: *"a strong sense for dramaturgy and timing... building
tension and releasing it... evolving layers, rolling percussion."* Catalog: **33 sets** (mostly 1–1.5 hr,
a few 2–3.5 hr) ≈ 40+ hrs. **Corpus download:** YouTube ([channel](https://www.youtube.com/channel/UCO4ZN3_WDIDD2HbytexL1-w))
bot-blocks the AWS datacenter IP ("confirm you're not a bot"), so we pull from **SoundCloud**
([user-448192862](https://soundcloud.com/user-448192862/tracks)) via `yt-dlp` (HLS aac 160k) →
`/home/ubuntu/dj_engine/burmeister/*.mp3`. Corpus is TEACHER material only (per copyright stance).

> **Copyright stance (non-negotiable):** the reference tracks are *teachers*, never source material
> in our output. We learn the STYLE/STRUCTURE (not copyrightable) and the ELEMENT CHARACTER, then
> RECREATE everything clean. We never ship stems separated from a copyrighted recording.

---

## The three parts

### Part A — Structural analysis ✅ TOOL BUILT
`dj_arrangement_analysis.py` reads a full track and outputs:
- **Element sequencing grid** — 6 element bands (sub / kick+bass / bassline / drone / stab / hats)
  × time bins, each cell = that element's activity 0–8. Shows exactly when the DJ brings each
  element in/out across the whole track.
- **Sections** — auto-detected boundaries (big changes in the element vector) → labeled
  intro / breakdown / build / peak with the active element set + energy.
- Machine-readable `*.json` timeline (feeds Part C).

Run: `python3 dj_arrangement_analysis.py --in TRACK.mp3 --out report.md --json t.json --bin 30`
First output: `cosmic_arrangement.md` / `.json`.

### Part B — Copyright-clean element library ⏳ method proven
For each element in the DJ's palette, build a clean recreated version (the reference is the target,
not the source). **Proven method** (on the intro drone): ACE-Step `--ref <element clip> --ref-strength
0.6` to match character → band-limit (ffmpeg `highpass`/`lowpass`) to the element's measured frequency
range → verify the band profile matches. Library lives in `dj_engine/elements/`:
- `drone` (dark low pad, 60–900 Hz, no beat) — ✅ v3 done (`intro_element_v3_filtered`)
- `kick+bass`, `bassline` (rolling sub-bass), `stab` (synth chord/lead), `hats/perc`, `sub` — ⏳ TODO
Each element = a short (≈30–45 s) clean loop tagged with its band range + role.

### Part C — Sequencing grammar ⏳ needs multiple tracks
From the Part-A timelines of several tracks by the DJ, learn the *grammar*:
- typical section lengths + order (intro→peak→breakdown→… )
- element-introduction order (what enters first, what marks a drop, what's the breakdown signature)
- build lengths, breakdown frequency, energy-curve shape, hat-usage pattern
Encode as a template/Markov-ish model the arranger samples from → drives a rebuild of
`progressive_arrange.py` so the automation follows the *DJ's* grammar, not a hand-guessed curve.

---

## What the cosmic track's arrangement reveals (first read)
(from `cosmic_arrangement.md`, 23 sections)
- **Long ambient intro** (0–2:00): drone + faint bassline, **no full kick** — the dark drone we
  recreated. The DJ opens on atmosphere, not the beat.
- **Drone is the constant bed** — almost always present; it's the glue, not a "dominant" lead.
- **Hats are the main energy lever** — the most *sequenced* element: pulled OUT for breakdowns,
  pushed IN to lift peaks (big hat sections ~23–38 min, ~60–71 min).
- **Breakdowns = kick drops out** (9:00, 53:30) — short (60 s) resets, then rebuild.
- **Structure:** intro → 7-min peak → breakdown → rolling peaks/builds with periodic breakdowns →
  sustained hat-driven peak → **ambient outro** (71:30). Long-form: slow, patient, hypnotic.
- **Stabs** come and go to add motion mid-track; **sub** swells in waves under the peaks.

→ The DJ's signature = patient long-form, drone-bedded, **hat-and-breakdown-driven** energy control.

---

## ⭐ FINAL DELIVERABLE — a reusable "learn-any-DJ" SKILL (Deepak's req 2026-06-30)
Once the pipeline (A→B→C→generation) is proven end-to-end on Burmeister, **wrap it as a skill**
(working name `learn-dj-style-trigunai`) so Deepak can point it at ANY DJ and get a style engine:
1. **Input** = a DJ name / channel / SoundCloud profile (or a folder of their sets).
2. **Gather** = yt-dlp the catalog (SoundCloud preferred — YT bot-blocks the AWS IP) → corpus folder.
3. **Analyze** = run `dj_arrangement_analysis.py` on every set → JSON timelines.
4. **Learn grammar** = extract the shared arrangement rules (section lengths, element-entry order,
   breakdown/build signatures, energy-curve, hat/percussion usage) → a per-DJ `grammar.json`.
5. **Element library** = recreate the DJ's element palette copyright-clean (audio2audio + band-limit).
6. **Generate** = arranger samples the DJ's grammar + clean elements → a new track *in that DJ's style*,
   copyright-clean.
The skill stores each DJ as a profile under `dj_engine/<dj-slug>/` (corpus refs, grammar.json,
elements/) so the library of learnable DJs grows. Build the skill only AFTER C + generation work on
Burmeister — a skill must encode a PROVEN flow, not a hoped-for one.

## Status / next
- ✅ A: analyzer built + first track mapped.
- ⏳ B: recreate the remaining elements clean (kick+bass, bassline, stab, hats) like the drone.
- ⏳ C: **needs 3–5+ more tracks from this DJ** → run the analyzer on each → learn the shared grammar.
- Then: rebuild `progressive_arrange.py` to follow the learned grammar + clean element library =
  the arrangement engine.

**When Deepak adds tracks:** drop them on the box, run the analyzer on each (`--out`/`--json`),
collect the JSONs, and move to Part C grammar extraction. Keep everything copyright-clean per the stance above.
</content>
