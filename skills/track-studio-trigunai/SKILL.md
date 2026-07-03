---
name: track-studio-trigunai
description: >
  Step-by-step, interactive TRACK BUILDER that walks the user through making an original,
  copyright-clean song from scratch — guiding them one decision at a time and offering THREE
  options at every step. The flow: (1) brief/genre, (2) design the BASIC ELEMENTS (kick, bass,
  hats, drone, stab) — synthesize from scratch, use CC0 samples, or the user's own recording,
  (3) choose the RHYTHM — generate a MIDI here, upload a recorded MIDI, or pick a groove preset,
  (4) MERGE elements + rhythm into a sample, (5) add VOCALS (mantra/female) or keep instrumental,
  (6) PRODUCE/master through the DawDreamer DAW, (7) FINISH as audio / +visualizer video / +upload.
  Everything is generated (DSP synthesis + your MIDI + your recordings) so it's 100% copyright-clean.
  Also ANALYZES a reference MP3 the user drops in (tempo, key, elements, timbre) and recreates its
  STYLE. Runs on the EC2 A10G box; auditions play locally via afplay. Use when the user wants to:
  "build a track step by step", "make my first track", "track studio", "design my own sounds",
  "make a song from scratch", "build a song element by element", "generate basic elements",
  "make a bass/kick/drone", "turn this MIDI into a track", "analyze this reference and recreate it",
  "guide me through making music". Companion to hypnotic-techno-trigunai (one-shot set generator)
  and learn-dj-style-trigunai (learn a DJ). This skill is the HANDS-ON, choose-as-you-go studio.
---

# track-studio-trigunai — the step-by-step song studio

Guide the user through building an original track **one step at a time**, always presenting
**exactly three options** at each decision point (via the `AskUserQuestion` tool). Run the
synthesis/rendering on the EC2 box, **play every result locally with `afplay`**, and only advance
to the next step once the user approves the current one. Everything produced is copyright-clean
(DSP synthesis + the user's own MIDI/recordings + CC0 samples).

**Interaction rules (important):**
- One step at a time. Never skip ahead. Confirm the result of a step before moving on.
- Every choice = an `AskUserQuestion` with **3 options** (first option = recommended).
- After each render, `afplay` it so the user hears it immediately. Offer to tweak or accept.
- Keep the user oriented: say which step they're on ("Step 2 of 7 — Rhythm").
- Track the running choices in a small config (see §Config) so a full render is reproducible.

---

## Environment (verify first, every session)

| Item | Value |
|---|---|
| EC2 (stable EIP) | `34.192.145.204` (start the box if SSH times out; it's the A10G) |
| SSH key | `~/.ssh/trigunai_key.pem` |
| Python (has librosa/scipy/soundfile/mido) | `~/audio_pipeline/venv/bin/python` on EC2 |
| Work dir on EC2 | `~/midi_demo/` (renders), `~/stems_synth/` (synth stems), `~/sb_samples/` (previews) |
| CC0 sample bank | `~/dj_engine/burmeister/{stems_fs,vocals,voices,accents}` |
| Local delivery dir | `music_pipeline/dj_engine/burmeister/` (pull mp3s here, `afplay` them) |
| Scripts | bundled in this skill's `scripts/` — scp to `~/` on EC2 before running |

Boot check:
```bash
PEM=~/.ssh/trigunai_key.pem; EC2=34.192.145.204
ssh -i "$PEM" -o ConnectTimeout=15 ubuntu@$EC2 'echo OK' || echo "START THE BOX (AWS console) then retry"
```
If the box was stopped, tell the user to start it; poll until SSH answers. `mido` auto-installs
on first use (`pip install --break-system-packages mido`).

---

## The 7 steps

### STEP 0 — Brief (and optional reference)
Ask genre/vibe with 3 options, e.g.:
1. **Hypnotic techno + mantra** (the proven vibe) · 2. **Melodic / ambient** (like a reference) · 3. **My own idea** (free-form)

Also collect **BPM**, **key/mode**, **length** — or use defaults (123 BPM, F# minor, 90s). Defaults
are fine; don't over-ask.

**Reference branch:** if the user drops a reference MP3, FIRST analyze it:
```bash
scp -i "$PEM" ref.mp3 ubuntu@$EC2:/home/ubuntu/ref_open.mp3
scp -i "$PEM" scripts/analyze_ref.py ubuntu@$EC2:/home/ubuntu/
ssh -i "$PEM" ubuntu@$EC2 '~/audio_pipeline/venv/bin/python ~/analyze_ref.py'
```
Report tempo / key / harmonic-vs-percussive / band-energy / instrument verdict, and carry the
detected BPM+key forward into the steps below. Use `scripts/recreate_ref.py` to recreate the STYLE
with a NEW melody (copyright-clean) — never copy the reference's exact melody unless it's the user's own.

### STEP 1 — Design the BASIC ELEMENTS  (kick · bass · hats · drone · stab)
This is the heart. For the palette source, ask 3 options:
1. **Synthesize from scratch** (unique, recommended) — `scripts/gen_unique_stems.py` (full set) or
   `scripts/synth_elements.py` (individual presets). Edit the synth params to taste.
2. **CC0 samples** (real-world texture) — pick from `~/dj_engine/burmeister/stems_fs` / previews in `~/sb_samples`.
3. **My own recording** (Yamaha etc.) — user uploads a WAV/MIDI; load it as the element.

Then, to pick the **timbre** of a synth element, render variants and let them choose by ear:
```bash
# 4 timbres of the same line: saw / soft-round / plucked-string(KS) / mallet
~/audio_pipeline/venv/bin/python ~/timbre_variants.py
# -> timbre_1saw / 2soft / 3pluck / 4mallet .mp3   (afplay each, ask which)
```
`afplay` each variant, ask "which number?", then tune (darker/brighter = move the lowpass;
pluckier = shorter decay; buzzier = more saw vs sub). Iterate per element until approved.

### STEP 2 — Choose the RHYTHM (MIDI)
Ask 3 options:
1. **Generate a MIDI here** (recommended) — `scripts/gen_rhythms.py` makes driving / broken / tribal
   grooves as real `.mid` + rendered `.mp3`; play all three, let them pick. Or `scripts/midi_demo.py`
   for a full drums+bass+lead pattern.
2. **Upload a recorded MIDI** — user drops a `.mid` (from their Yamaha or a DAW). scp it up; render it
   through the chosen elements (see the track-mapping in `midi_demo.py`: track0=drums note36→kick /
   42→hat, track1=bass, track2=lead). MIDI = clean (note data only); only avoid MIDI that copies a
   known song's melody — generic rhythms are always fine.
3. **Pick a groove preset / external tool** — reuse a saved groove, or fold in a pattern from an
   external rhythm source the user names.

Render the chosen MIDI with the Step-1 elements → `afplay` → confirm.

### STEP 3 — MERGE into a sample
Ask 3 options for scope:
1. **Short loop** (8–16 bars) — quick audition of the palette+groove together.
2. **~90s sample with arrangement** (recommended) — `scripts/driving_track.py` pattern: intro build →
   groove → breakdown → drop → outro (adapt element choices + BPM/key).
3. **Full track** (3–7 min) — drive `scripts/grammar_generate_burmeister_stems.py --stems <dir>
   --minutes N --bpm B` for the learned build/drop/peak/outro arrangement.

Render → master → `afplay` → confirm.

### STEP 4 — VOCALS (optional)
Ask 3 options:
1. **Mantra + female** (the proven human vocal) — `scripts/dd_produce.py` vocal block: real CC0 mantra
   + Magnus-choir female, gentle-pitched to key, EQ+notch+reverb, rotated. User picks the chant.
2. **Instrumental** — skip vocals.
3. **My own vocal** — user uploads; load + process it.

### STEP 5 — PRODUCE / master (the DAW)
Run `scripts/dd_produce.py` (DawDreamer): real EQ / high-pass / notch / reverb / glue compression /
master limiter, then `ffmpeg loudnorm=I=-10:TP=-1:LRA=9`. This is the polish that makes it sound
produced, not raw. (DawDreamer is installed in `~/audio_pipeline/venv`.)

### STEP 6 — FINISH
Ask 3 options:
1. **Mastered audio only** (deliver the mp3).
2. **+ Visualizer video** — burn a shader (Flower-of-Life etc.) over it via the video-creator renderer.
3. **+ Upload to FlowArt** — hand to the `trigunai-yt-flowart` skill.

---

## Config (running state — keep this so a final render is reproducible)
Track the user's choices as JSON as you go (the bundled `assets/song_builder.html` produces exactly
this shape if the user prefers a visual picker — open it locally, they fill it, paste it back):
```json
{ "bpm":123, "key":"F# minor", "length_min":1.5,
  "elements":{ "kick":"synth:punchy", "bass":"synth:sub", "hats":"synth", "drone":"synth:warm", "stab":"synth" },
  "synth_elements":["uniq_kick","uniq_bass",...],
  "rhythm":{ "source":"generated", "groove":"driving", "midi":"rhythm1_driving.mid" },
  "scope":"90s",
  "vocals":{ "mantra":"mantra_2", "female":"female_choir" },
  "finish":"audio" }
```

## Bundled scripts (scp to `~/` on EC2 before use)
| Script | Role |
|---|---|
| `analyze_ref.py` | Analyze a reference MP3 → tempo/key/bands/timbre/melody |
| `synth_elements.py` | 8 designed element presets (kick/bass/drone/stab/hats) |
| `gen_unique_stems.py` | Full unique 7-stem set (kick,bass,bass2,hats,perc,drone,stab) → `~/stems_synth` |
| `timbre_variants.py` | Same line in 4 timbres (saw/soft/pluck-KS/mallet) for picking |
| `midi_demo.py` | Build a multi-track MIDI + render it through synth elements |
| `gen_rhythms.py` | 3 groove MIDIs (driving/broken/tribal) + rendered mp3s |
| `driving_track.py` | 90s arranged sample from a groove (intro→drop→outro) |
| `recreate_ref.py` | Recreate a reference's STYLE with a new (clean) melody |
| `grammar_generate_burmeister_stems.py` | Full-length arranger (build/drop/peak/outro) |
| `dd_produce.py` | DawDreamer mix + master (EQ/notch/reverb/glue) + vocal block |
| `assets/song_builder.html` | Visual picker — audition samples, pick combos, emits the config JSON |

## Gotchas
- **Public box:** if SSH times out, the EC2 is stopped — tell the user to start it, poll until up.
- **Play locally:** always `afplay` the pulled mp3 (the user is on the Mac; renders happen on EC2).
- **Paths with spaces:** copy reference files to `/tmp/ref_open.mp3` first to dodge quoting issues.
- **Copyright line:** synthesis + user MIDI/recordings + CC0 = clean. The only risk is a MIDI that
  reproduces a known song's *melody* — generic rhythms and original lines are always fine.
- **Timbre tuning cheat-sheet:** darker=lower the lowpass; brighter=raise it; pluckier=shorter decay;
  buzzier=more saw vs sub; warmer=more saturation/sub.
