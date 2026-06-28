---
name: isochronic-deephouse-trigunai
description: >
  End-to-end factory for a TrigunAI isochronic DEEP HOUSE music visualizer video — generate
  copyright-clean deep/upbeat house music with an embedded beta isochronic focus tone, then
  burn a user-supplied audio-reactive GLSL shader on top into a finished MP4, any length
  (2 min to 2 hours). The skill ASKS YOU TO PASTE THE SHADER CODE to use for the visual.
  Use when the user wants: "deep house focus video", "study music video", "isochronic deep
  house", "house focus track + visualizer", "make a deep house visualizer", "focus music
  video", "house music with isochronic tones", or to recreate the deep-house-+-shader video
  pipeline. For hypnotic techno instead, use `hypnotic-techno-trigunai`. Music engine =
  ACE-Step on the EC2 A10G; video engine = the shader renderer in video-creator/backend.
---

# Isochronic Deep House Visualizer — end to end

Produces a finished **deep house (focus) music video**: copyright-clean house music with a
**beta (15 Hz) isochronic focus layer**, plus a user-supplied audio-reactive shader rendered
on top. Mirrors `production-music-trigunai` (music) + the shader renderer (video) into one flow.

> **Style identity of THIS skill:** upbeat/deep house, ~122 BPM, **beta isochronic** (focus/alert).
> Everything else (pipeline, box, shader contract) is shared with `hypnotic-techno-trigunai`.

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

**GPU OOM gotcha (important):** ACE-Step music gen needs ~7–11 GB. **ComfyUI (port 8188) holds
8–15 GB when a model is loaded** and is the usual cause of `CUDA out of memory`. Check free VRAM
before generating. If <9 GB free and ComfyUI is the hog, DO NOT kill it without asking — the user
may be using it. Options: wait, ask them to free it, or run `make_music.py --cpu-offload --seg-len 120`
(lower VRAM, slower). The video render barely uses the GPU, so it coexists fine.

---

## 1. Generate the music (ACE-Step)

Tool: `make_music.py` (repo `music_pipeline/make_music.py`, on box `/home/ubuntu/make_music.py`,
runs in `~/acestep_venv`). Push the latest copy first: `scp -i $PEM music_pipeline/make_music.py ubuntu@$EC2_IP:/home/ubuntu/`.

```bash
ssh -i "$PEM" ubuntu@$EC2_IP 'cd /home/ubuntu && nohup ~/acestep_venv/bin/python make_music.py \
  --style focus-house --freq beta --minutes <N> \
  --seg-len 240 --unique 10 --xfade 12 --bpm 122 \
  --out /home/ubuntu/music_out/deephouse_beta_<N>min.mp3 > /tmp/dh.log 2>&1 & echo pid=$!'
```
- `--bpm 122` (locked) keeps every segment tempo-consistent so crossfade joins don't break the
  groove — this is THE fix for "loses flow at some points." Longer `--xfade` smooths joins further.
- `--freq beta` = 15 Hz isochronic (focus). It synthesizes a 210 Hz carrier gated at 15 Hz,
  mixes it under the music at −20 dB, then masters to −14 LUFS. Output is one MP3.
- For 1 hr use `--unique 10–12`, `--seg-len 240`. Generation ≈ ~40 s/segment; assembly+master a few min.
- Watch progress: `grep '\[m1\]' /tmp/dh.log` (ignore tqdm bars). Wait for `[m1] DONE`.

**Why copyright-clean:** ACE-Step is MIT-licensed, trained on licensed + royalty-free + synthetic
data — output is safe to monetize.

---

## 2. Verify the isochronic layer is actually present

Don't trust the flag — confirm the gating frequency is in the audio (STFT the 210 Hz carrier bin,
FFT its envelope, expect a line at the gating freq ≥3× the band median):
```python
import numpy as np, librosa
y,sr=librosa.load(MP3, sr=22050, mono=True, offset=300, duration=120)
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=64)); fr=librosa.fft_frequencies(sr=sr,n_fft=2048)
env=S[np.argmin(abs(fr-210))]; env=env-env.mean()
f=np.fft.rfftfreq(len(env),64/sr); P=abs(np.fft.rfft(env*np.hanning(len(env))))
b=(f>=4)&(f<=25); i=np.argmin(abs(f-15.0))   # 15 Hz for beta
print(P[i]/(np.median(P[b])+1e-9), "x  (>3 = present)")
```
Run with `~/acestep_venv/bin/python`. Report the ratio to the user.

---

## 3. ASK THE USER FOR THE SHADER CODE  ⭐

This skill is shader-agnostic. **Ask the user to paste the GLSL fragment shader** they want for
the visual (they may give a Shader-Studio / GLSL-ES shader with `gl_FragColor` and many custom
uniforms). Then **adapt it to the pipeline contract** (§4) and save to
`video-creator/backend/shaders/<name>.glsl` (+ scp to `/home/ubuntu/video-creator-backend/shaders/`).

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
4. Declare ONLY the 6 bound uniforms. **Map the shader's custom audio uniforms** to them as locals
   at the TOP of `main()` — typical mapping:
   `uTime→u_time · uRes→u_resolution · uBass/uSubBass→u_bass · uMids→u_rms · uHighs/uCentroid→u_treble ·
   uBeat/uOnset/uFlux→u_onset · uRMS→u_rms · uSilence→clamp(1-u_rms*2,0,1) · uFlatness→u_treble*0.5`.
5. **Bake every tuning/param uniform as a `const`** at file scope (center radius, speeds, breath
   timings, particle counts, etc.) with sensible values — let the user tune them later.
6. Palette colors `uColA..D` → `const vec3`.
7. Any uniform-array (e.g. `uBands[8]`) that's unused → delete.

(Helper functions that don't touch uniforms are copied verbatim.)

---

## 5. Render — the fast renderer

Tool: `render_visualizer.py` (repo `video-creator/backend/render_visualizer.py`, on box
`/home/ubuntu/render_visualizer.py`, runs in `audio_pipeline/venv` which has moderngl+librosa).
It uses a NumPy vertical flip (≈66 fps @1080p) — the stock `shader_service` per-frame Python flip
is far too slow for hour-long renders. **Output is VIDEO ONLY → mux the audio after.**

```bash
# PROTOTYPE FIRST (short clip → open for approval; never full-render an unapproved look)
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && \
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
  --audio music_out/deephouse_beta_<N>min.mp3 --out /home/ubuntu/proto.mp4 --dur 12 --fps 30 --w 1920 --h 1080'
# extract a frame, scp back, Read it to verify the look; mux 12s audio + open on Mac for the user.

# FULL high-quality render (CRF 16 = high quality; medium preset; detached) + mux
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && nohup bash -lc "
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
    --audio music_out/deephouse_beta_<N>min.mp3 --out /home/ubuntu/dh_silent.mp4 \
    --dur <N*60> --fps 30 --w 1920 --h 1080 --crf 16 --preset medium ;
  ffmpeg -y -i dh_silent.mp4 -i music_out/deephouse_beta_<N>min.mp3 -map 0:v -map 1:a \
    -c:v copy -c:a aac -b:a 256k -shortest /home/ubuntu/deephouse_visual_<N>min.mp4 ;
  echo ALLDONE" > /tmp/dhrender.log 2>&1 & echo pid=$!'
```
- **CRF is the quality knob** (16–18 = high, near-transparent); preset only trades render-time for
  file-size at that quality (`medium` ≈ 34 fps; `veryfast` ≈ 66 fps; `slow` ≈ 20 fps).
- 60 min = 108k frames ≈ 30–45 min at CRF16/medium. Run detached; watch for `ALLDONE`.

---

## 6. Deliver
`scp` the muxed MP4 to `course_assets/intro_out/` on the Mac and `open` it. Verify a frame and the
streams (`ffprobe`: h264 1080p30 + aac). Tell the user duration/size/CRF + the isochronic ratio.

---

## 7. Gotchas (hard-won)
- **IP changes every stop/start** — re-fetch first. **`/tmp` on the box is wiped on stop** — keep
  assets under `/home/ubuntu/`; the mp3s/scripts persist on EBS.
- **`torchcodec` required** for any `--ref` audio2audio / Demucs path: `~/acestep_venv/bin/pip install torchcodec` (one-time, done).
- **Killing procs over SSH sometimes returns exit 255** (connection resets) — the kill usually still
  ran; reconnect and verify with `pgrep` rather than retrying blindly.
- **Prototype before the full render** — always show a short clip and get approval; an hour-long
  render is too expensive to redo for a look tweak.
- **ACE-Step model load** ~5–65 s (warm/cold); generation ≈ 0.25× realtime.
- Box bills ~$1/hr — offer to stop it when the job's done.

---

## 8. Companion skills
`hypnotic-techno-trigunai` (techno sibling) · `production-music-trigunai` (general music tool) ·
`production-video-trigunai` (narrated video). Reference docs: `MUSIC_PIPELINE_RESEARCH.md`,
memory `project-music-pipeline`.
</content>
