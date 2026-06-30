---
name: hypnotic-techno-trigunai
description: >
  End-to-end factory for a TrigunAI HYPNOTIC TECHNO music visualizer video — generate
  copyright-clean continuous hypnotic techno (a "let-loose / lose-yourself" DJ-set vibe) with an
  embedded alpha isochronic flow tone, then burn a user-supplied audio-reactive GLSL shader on top
  into a finished MP4, any length (2 min to 2 hours). The skill ASKS YOU TO PASTE THE SHADER CODE
  to use for the visual. ALSO makes the MUSIC alone (structured Burmeister-style hypnotic techno —
  one locked groove, slow build, breakdowns, wind-down) via the DJ arrangement engine; the shader
  burn is optional. Use when the user wants: "make hypnotic techno", "make a techno track / set",
  "1-hour techno set", "hypnotic techno music", "Burmeister-style techno", "hypnotic techno video",
  "techno session + visualizer", "let loose techno", "ecstatic dance techno", "isochronic techno",
  "make a techno visualizer", "continuous techno set", or to recreate the techno (+optional shader)
  pipeline (Flow-Art / Movement II). For deep house / focus instead, use `isochronic-deephouse-trigunai`;
  to learn a NEW DJ's style use `learn-dj-style-trigunai`. Music engine = ACE-Step + arrangement engine
  on the EC2 A10G; video engine = the shader renderer in video-creator/backend.
---

# Hypnotic Techno Visualizer — end to end

Produces a finished **hypnotic techno music video**: copyright-clean continuous techno with an
**alpha (10 Hz) isochronic flow layer** (for the "let loose / lose yourself" state), plus a
user-supplied audio-reactive shader rendered on top. This is the Flow-Art / Movement II music tool.

> **Style identity of THIS skill:** hypnotic/driving techno, ~130 BPM, **alpha isochronic** (flow,
> ego-loosening — not too sleepy like theta, not too alert like beta). Pipeline/box/shader contract
> are shared with `isochronic-deephouse-trigunai`.

---

## 0. The box (first action every session)

Render + music run on **EC2 g5.2xlarge `i-047ebf759f2386e71` (TrigunAI-Omniverse, us-east-1, A10G 24GB)**.
**Public IP changes on every stop/start** — get the current IP from the AWS console first.

```bash
EC2_IP=<current public IP>
PEM=~/.ssh/trigunai_key.pem
ssh -i "$PEM" ubuntu@$EC2_IP 'nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader'
```
If SSH fails the box is stopped — ask the user to start it.

**GPU OOM gotcha (important):** ACE-Step needs ~7–11 GB. **ComfyUI (port 8188) holds 8–15 GB when a
model is loaded** and is the usual `CUDA out of memory` cause. Check free VRAM before generating. If
<9 GB free and ComfyUI is the hog, DO NOT kill it without asking — the user may be using it. Options:
wait, ask them to free it, or `make_music.py --cpu-offload --seg-len 120` (lower VRAM, slower). The
video render barely uses the GPU, so it coexists fine.

---

## 1. Generate the music — STRUCTURED arrangement (the proven Burmeister-style recipe) ⭐

Do **NOT** just loop `make_music.py` — that gives a flat groove that "constantly changes / never builds".
Use the **DJ arrangement engine** so the track has a real journey: **ONE locked groove** + slow
filter-OPEN build → long hypnotic hold with **breakdowns** → gradual wind-down, mastered. This is the
proven v3→v9 recipe (a learned Burmeister grammar drives it). Box: stable EIP `34.192.145.204`. Push the
latest `make_music.py` + `dj_engine/grammar_generate.py` first.

```bash
PEM=~/.ssh/trigunai_key.pem; EC2_IP=34.192.145.204
# a) clean CORE groove (dark, bass-dominant, 123 BPM). One core = one distinct track; vary --seed for variety.
ssh -i $PEM ubuntu@$EC2_IP '~/acestep_venv/bin/python make_music.py --style techno-hypnotic \
  --minutes 4 --seg-len 240 --unique 1 --bpm 123 --seed 11 --out music_out/techno_core.mp3'

# b) ARRANGE it into a structured track (runs in audio_pipeline/venv). --breaks = breakdown positions.
ssh -i $PEM ubuntu@$EC2_IP 'source ~/audio_pipeline/venv/bin/activate; cd ~ && \
  python3 -u dj_engine/grammar_generate.py --core music_out/techno_core.mp3 --minutes <N> \
    --breaks 0.40,0.70 --out dj_engine/techno_<N>min.wav'

# c) MASTER chain (punch + clarity + glue + loud) -> final mp3
ssh -i $PEM ubuntu@$EC2_IP 'ffmpeg -y -i dj_engine/techno_<N>min.wav -af \
  "highpass=f=28,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150:makeup=2,treble=g=2.5:f=3500,loudnorm=I=-10:TP=-1:LRA=9" \
  -b:a 192k dj_engine/techno_<N>min.mp3 && rm dj_engine/techno_<N>min.wav'
```
- **The recipe (proven):** single core, seamless-loop crossfade (consistent hypnotic rhythm); slow build
  with a low-pass filter that OPENS up (kick stays OUT of the filter = clear beat from early); drone→kick
  →bass→hats enter gradually; hold the peak; breakdowns drop kick+hats but KEEP the bass; gradual wind-down.
- **No constant piano** (the melodic stem is removed) and **isochronic is OFF by default** for this
  style (pure music — user pref). To add a *light* flow tone, mix a **−30 dB** 10 Hz-gated 210 Hz carrier
  before loudnorm (§2 has the synth); keep it faint, never heavy.
- **Length:** prototype ~15 min, open it, get approval, then render full 30/60 min. 60-min needs ~10 GB RAM
  (`free -g`); `rm` the `.wav` after mastering. More breakdowns for longer tracks (e.g. `--breaks 0.33,0.58,0.80`).
- **5 tracks at once:** `dj_engine/batch_5tracks.sh` (one per core, varied breakdowns).
- **To learn a NEW DJ's style** (not just make this one) → use the `learn-dj-style-trigunai` skill.

**Why copyright-clean:** ACE-Step (MIT, royalty-free/synthetic training data) makes the cores; the
arrangement is ours. Safe to monetize. Tools: `~/make_music.py`, `~/dj_engine/grammar_generate.py` (repo `music_pipeline/`).

---

## 2. Verify the isochronic layer is actually present

Confirm the gating frequency is really in the audio (STFT the 210 Hz carrier bin, FFT its envelope,
expect a line at the gating freq ≥3× the band median):
```python
import numpy as np, librosa
y,sr=librosa.load(MP3, sr=22050, mono=True, offset=300, duration=120)
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=64)); fr=librosa.fft_frequencies(sr=sr,n_fft=2048)
env=S[np.argmin(abs(fr-210))]; env=env-env.mean()
f=np.fft.rfftfreq(len(env),64/sr); P=abs(np.fft.rfft(env*np.hanning(len(env))))
b=(f>=4)&(f<=25); i=np.argmin(abs(f-10.0))   # 10 Hz for alpha
print(P[i]/(np.median(P[b])+1e-9), "x  (>3 = present)")
```
Run with `~/acestep_venv/bin/python`. Report the ratio to the user. (Techno alpha typically reads
very strong, ~10×+.)

---

## 3. ASK THE USER FOR THE SHADER CODE  ⭐

This skill is shader-agnostic. **Ask the user to paste the GLSL fragment shader** they want for the
visual (often a Shader-Studio / GLSL-ES shader with `gl_FragColor` + many custom uniforms). Then
**adapt it to the pipeline contract** (§4) and save to `video-creator/backend/shaders/<name>.glsl`
(+ scp to `/home/ubuntu/video-creator-backend/shaders/`).

---

## 4. The shader contract + adaptation rules

`shader_service` binds ONLY these uniforms, so the final shader must use exactly them:
```glsl
#version 330
precision highp float;
uniform float u_time;        uniform vec2 u_resolution;
uniform float u_rms;         // overall / mids
uniform float u_bass;        // 20-300 Hz
uniform float u_treble;      // 2-8 kHz
uniform float u_onset;       // beat (0/1)
out vec4 fragColor;          // NOT gl_FragColor
// uv example: (gl_FragCoord.xy - 0.5*u_resolution) / min(u_resolution.x,u_resolution.y);
```
**To adapt an arbitrary pasted shader:**
1. Set `#version 330` header (keep `precision highp float;`).
2. `gl_FragColor` → declare `out vec4 fragColor;` and assign to it.
3. Remove `texture2D`/`sampler2D`/photo blocks (or `texture2D`→`texture`); photo modes aren't wired.
4. Declare ONLY the 6 bound uniforms. **Map the shader's custom audio uniforms** to them as locals at
   the TOP of `main()` — typical mapping:
   `uTime→u_time · uRes→u_resolution · uBass/uSubBass→u_bass · uMids→u_rms · uHighs/uCentroid→u_treble ·
   uBeat/uOnset/uFlux→u_onset · uRMS→u_rms · uSilence→clamp(1-u_rms*2,0,1) · uFlatness→u_treble*0.5`.
5. **Bake every tuning/param uniform as a `const`** at file scope (radii, speeds, breath timings,
   particle counts, etc.) with sensible values — the user tunes later.
6. Palette colors `uColA..D` → `const vec3`.
7. Unused uniform-arrays (e.g. `uBands[8]`) → delete.

(Helper functions that don't touch uniforms are copied verbatim.)

---

## 5. Render — the fast renderer (ALWAYS GPU-encode with `--encoder nvenc`)

Tool: `render_visualizer.py` (repo `video-creator/backend/render_visualizer.py`, on box
`/home/ubuntu/render_visualizer.py`, runs in `audio_pipeline/venv`). The shader is drawn on the A10G
(instant); the only slow step is the H.264 **encode**. **Always pass `--encoder nvenc`** so the
encode runs on the A10G's hardware H.264 chip (NVENC) instead of the CPU's `libx264` — that's the
difference between ~16 fps and ~80–100 fps at 1080p (≈6× faster). `--push` the latest renderer first;
old copies on the box may lack the `--encoder` flag. **Output is VIDEO ONLY → mux the audio after.**

```bash
# PROTOTYPE FIRST (short clip → open for approval) — GPU-encoded
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && \
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
  --audio music_out/techno_alpha_<N>min.mp3 --out /home/ubuntu/proto.mp4 \
  --dur 15 --fps 30 --w 1920 --h 1080 --crf 16 --encoder nvenc'
# extract a frame, scp back, Read it; mux a short audio slice + open on Mac for approval.

# FULL high-quality render (cq 16; GPU NVENC; detached) + mux
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && nohup bash -lc "
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
    --audio music_out/techno_alpha_<N>min.mp3 --out /home/ubuntu/tk_silent.mp4 \
    --dur <N*60> --fps 30 --w 1920 --h 1080 --crf 16 --encoder nvenc ;
  ffmpeg -y -i tk_silent.mp4 -i music_out/techno_alpha_<N>min.mp3 -map 0:v -map 1:a \
    -c:v copy -c:a aac -b:a 256k -shortest /home/ubuntu/techno_visual_<N>min.mp4 ;
  echo ALLDONE" > /tmp/tkrender.log 2>&1 & echo pid=$!'
```
- **`--encoder nvenc`** = GPU hardware encode (default for every render). `--crf 16` becomes NVENC's
  `-cq 16` (high quality, `-rc vbr -tune hq -preset p5` baked in). `--encoder x264` is the CPU
  fallback only — slower, and the only reason to use it is if NVENC is unavailable.
- The slow path was never the GPU drawing or the shader — it was CPU `libx264`. A strong GPU does
  **nothing** for software encoding; you must move the encode onto NVENC to get the speedup.
- 60 min = 108k frames ≈ **~18–20 min with `--encoder nvenc`** (was ~30–105 min on CPU x264,
  depending on shader weight). Run detached; watch for `ALLDONE`. Confirm it's really GPU-encoding
  with `nvidia-smi --query-gpu=utilization.encoder --format=csv,noheader` (should be >0%).

---

## 6. Deliver
`scp` the muxed MP4 to `course_assets/intro_out/` on the Mac and `open` it. Verify a frame + streams
(`ffprobe`: h264 1080p30 + aac). Report duration/size/CRF + the isochronic ratio.

---

## 7. Gotchas (hard-won)
- **IP changes every stop/start**; **`/tmp` wiped on stop** — keep assets under `/home/ubuntu/` (EBS).
- **`torchcodec` required** for `--ref` audio2audio / Demucs: `~/acestep_venv/bin/pip install torchcodec`.
- **Killing procs over SSH sometimes returns exit 255** (connection resets) — the kill usually still
  ran; reconnect and verify with `pgrep`.
- **Prototype before the full render** — always.
- A breath/meditation-type shader can look sparse against driving techno (long rest gaps); if so, the
  fixes are: shorten the rest phase, add particles/background fill, or recolor — all shader-`const`
  tweaks + a re-render.
- Box bills ~$1/hr — offer to stop it when done.

---

## 8. Companion skills
`isochronic-deephouse-trigunai` (deep house sibling) · `production-music-trigunai` (general music) ·
`production-video-trigunai` (narrated video). Reference: `MUSIC_PIPELINE_RESEARCH.md`,
memory `project-music-pipeline`.
</content>
