# 🔒 REFERENCE — Burmeister v15 (locked 2026-07-19)

The locked reference track for the arrangement-RL engine. Everything below reproduces it exactly.
Critic: **8.6/10 SHIP-IT**, liveliness 9.1, hat_clarity 9.7. Human-ear approved (bass clean, hats
clear, low-end solid, in sync, full rise-and-fall).

**Artifact:** `REFERENCE_burmeister_v15.mp3` (6 min) · composed from `REFERENCE_burmeister_v15_grid.json`

## What v15 is (the whole pipeline in one track)

```
RL policy composes the arrangement (learned from Burmeister's 18 real per-track grids)
  + policy's LEARNED dynamics (intro build, mid-track hats-dropout, DJ-faithful densities, energy arc +0.46)
  + AUTHORED --structure  (breakdowns -> DROPS @ 2:25 & 4:12, intro build, outro)
  + CLEAN SYNTH low end    (sub = rich tonal drone; bassline = offbeat filtered-saw, both synthesized -> zero AI-stem smear)
  + BASS LOCKED to the real kick phase (auto-detected 499 ms lead-in)
  + de-hazed low-mid + decluttered highs (from the ear-feedback loop)
  + critic-verified (calibrated to the DJ's real spectral balance + low-haze + hat-clutter)
```

## Reproduce it exactly

```bash
# 1) compose the arrangement (train + emit the learned-arc grid) — local, pure numpy, ~90s
cd music_pipeline/dj_engine/arrangement_rl
python3 arrangement_rl.py --real-dir ../burmeister/analysis \
  --iters 300 --seed 1 --arc-weight 15 --emit-grid REFERENCE_burmeister_v15_grid.json

# 2) render to audio WITH the rise-and-fall structure — on EC2 (audio venv)
PEM=~/.ssh/trigunai_key.pem ; EC2_IP=34.192.145.204
scp -i $PEM render_from_grid.py REFERENCE_burmeister_v15_grid.json ubuntu@$EC2_IP:~/arrangement_rl/
ssh -i $PEM ubuntu@$EC2_IP '
 cd ~/arrangement_rl
 ~/audio_pipeline/venv/bin/python render_from_grid.py \
   --grid REFERENCE_burmeister_v15_grid.json --stems ~/dj_engine/burmeister/stems_fs \
   --minutes 6 --bpm 123 --structure --out REFERENCE_burmeister_v15.wav
 ffmpeg -y -i REFERENCE_burmeister_v15.wav -af \
  "highpass=f=25,acompressor=threshold=-18dB:ratio=2.2:attack=8:release=180:makeup=1.5,treble=g=1.4:f=6000,loudnorm=I=-10:TP=-1:LRA=12" \
  -b:a 192k REFERENCE_burmeister_v15.mp3'
```

## Key params (frozen)
- policy: `--iters 300 --seed 1 --arc-weight 15` (no `--bd-weight` — breakdowns come from `--structure`)
- render: `--minutes 6 --bpm 123 --structure`
- drops snap to downbeats; bass locked to detected kick phase (499 ms)
- master: `loudnorm I=-10 TP=-1 LRA=12`, gentle treble g=1.4 f=6000

## Verify a re-render
```bash
critique_track.py --track REFERENCE_burmeister_v15.mp3 --grammar burmeister_grammar.json --bpm 123
# expect ~8.6/10 SHIP-IT; only flag "more bass-heavy than DJ" (faithful — Burmeister is bass-heavy)
```

## The journey (v1 -> v15), for context
v1 first RL-composed audio · v4 fixed muddy/density (critic recalibrated to DJ) · v6 de-hazed bass ·
v7 decluttered hats · v8 fixed the "hazy background" (weak sub + bloated low-mid) · v9 rich sub drone ·
v10 replaced the SMEARED AI bass stem with a clean synth bass (the real root cause) · v11 fixed bass
SYNC (kick-phase lock) · v13 tuned rise-and-fall arc · v14 policy LEARNS the arc (#4) · **v15 = v14
learned arc + authored structure = the reference.**

Full design + honest findings: `ARRANGEMENT_RL_DESIGN.md`.
