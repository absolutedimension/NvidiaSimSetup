---
name: studio-track
description: "Generate original, copyright-clean BACKGROUND MUSIC / beds for reels and videos (and full tracks) on the render farm — from the track-studio DSP builder (synth stems + MIDI groove + DawDreamer master) or a fast ACE-Step instrumental. Use when content needs a music bed, background score, or a custom track: 'background music', 'music bed', 'make a bed for this reel', 'a track for X', 'instrumental'. Everything is generated (DSP synthesis + generated MIDI) so it's 100% copyright-clean. Delivers an MP3/WAV. NOT for songs-with-vocals from lyrics (studio-music) or the audio-reactive video (studio-flowart)."
metadata: { "openclaw": { "emoji": "🎚️", "requires": { "bins": ["ssh","scp"] } } }
---

# studio-track — Background Music / Beds (copyright-clean)

The headless engine behind `track-studio-trigunai`. Two paths, both copyright-clean (synthesis + generated MIDI, no samples of others' work):

- **Fast bed (default for the daily engine)** — ACE-Step instrumental via `make_music.py` (already on both farms). Good for reel beds.
- **Bespoke DSP track** — the track-studio pipeline: unique synth stems → MIDI groove → arrange → DawDreamer master. Richer, for FlowArt/feature tracks.

## Step 0 — resolve farm
```bash
source ~/.openclaw/farm.sh
[ "$FARM_NAME" = none ] && { echo "no farm up"; exit 1; }
SSH(){ ssh -i "$FARM_KEY" -o StrictHostKeyChecking=no "$FARM_USER@$FARM_IP" "$1"; }
```

## A. Fast bed (ACE-Step instrumental) — use this for reel/video beds
```bash
SSH "cd $FARM_HOME && $FARM_ENV $FARM_PY_ACE make_music.py --style ambient --minutes 1 $FARM_OFFLOAD \
     --workdir $FARM_HOME/music_work --out $FARM_HOME/music_out/bed.mp3"
scp -i "$FARM_KEY" "$FARM_USER@$FARM_IP:$FARM_HOME/music_out/bed.mp3" /tmp/bed.mp3
```
Styles for beds: `ambient` (neutral bed), `lofi` (chill), `focus-house` (energetic), or `--prompt "<mood, instruments>"`. Keep it instrumental (presets already do).

## B. Bespoke DSP track (track-studio pipeline) — for FlowArt / feature music
The track-studio scripts must be on the box once (scp the skill's `scripts/` → `$FARM_HOME/`): `gen_unique_stems.py`, `gen_rhythms.py`, `driving_track.py`, `dd_produce.py` (+ `grammar_generate_burmeister_stems.py` for full-length). Then, non-interactively:
```bash
V=$FARM_HOME/audio_pipeline/venv/bin/python
SSH "cd $FARM_HOME && $V gen_unique_stems.py"            # -> stems_synth/ (kick,bass,hats,drone,stab...)
SSH "cd $FARM_HOME && $V gen_rhythms.py"                 # -> driving/broken/tribal .mid + mp3
SSH "cd $FARM_HOME && $V driving_track.py"               # -> ~90s arranged sample (intro->drop->outro)
SSH "cd $FARM_HOME && $V dd_produce.py"                  # DawDreamer EQ/notch/reverb/glue + loudnorm master
scp -i "$FARM_KEY" "$FARM_USER@$FARM_IP:$FARM_HOME/<out>.mp3" /tmp/track.mp3
```
Config knobs (BPM/key/length/elements) live at the top of the scripts; edit for the brief (defaults: 123 BPM, F# minor, ~90s). For a full-length arranged track use `grammar_generate_burmeister_stems.py --minutes N --bpm B`.

## Deliver / hand off
- As a **bed**: hand `/tmp/bed.mp3` to `studio-reel`/`studio-video` as the music bed.
- As a **FlowArt track**: hand to `studio-flowart` (adds the audio-reactive shader video) → `studio-youtube` (FlowArt channel).

## Gotchas
- Copyright-clean = synthesis + generated MIDI only. Never fold in others' recordings.
- On the T4 fallback, ACE-Step needs `$FARM_OFFLOAD` (cpu-offload) and is ~7× realtime — fine for short beds, slow for long tracks (prefer EC2 for long).
- Keep outputs under `$FARM_HOME/` (EC2 `/tmp` is wiped on stop).
