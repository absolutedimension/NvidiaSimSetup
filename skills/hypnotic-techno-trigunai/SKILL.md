---
name: hypnotic-techno-trigunai
description: >
  End-to-end factory for a TrigunAI HYPNOTIC TECHNO music visualizer video — generate
  copyright-clean continuous hypnotic techno (a "let-loose / lose-yourself" DJ-set vibe) with an
  embedded alpha isochronic flow tone, then burn a user-supplied audio-reactive GLSL shader on top
  into a finished MP4, any length (2 min to 2 hours). The skill ASKS YOU TO PASTE THE SHADER CODE
  to use for the visual. Use when the user wants: "hypnotic techno video", "techno session +
  visualizer", "let loose techno", "ecstatic dance techno", "isochronic techno", "make a techno
  visualizer", "continuous techno set with visuals", or to recreate the techno-+-shader video
  pipeline (Flow-Art / Movement II). For deep house / focus instead, use
  `isochronic-deephouse-trigunai`. Music engine = ACE-Step on the EC2 A10G; video engine = the
  shader renderer in video-creator/backend.
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

## 1. Generate the music (ACE-Step)

Tool: `make_music.py` (repo `music_pipeline/make_music.py`, on box `/home/ubuntu/make_music.py`,
runs in `~/acestep_venv`). Push the latest copy first: `scp -i $PEM music_pipeline/make_music.py ubuntu@$EC2_IP:/home/ubuntu/`.

```bash
ssh -i "$PEM" ubuntu@$EC2_IP 'cd /home/ubuntu && nohup ~/acestep_venv/bin/python make_music.py \
  --style techno-hypnotic --freq alpha --minutes <N> \
  --seg-len 240 --unique 12 --xfade 16 --bpm 130 \
  --out /home/ubuntu/music_out/techno_alpha_<N>min.mp3 > /tmp/tk.log 2>&1 & echo pid=$!'
```
- `--bpm 130` (locked) + long `--xfade 16` make it mix like a **continuous DJ set** — segments stay
  tempo-consistent so the groove never breaks ("continuous / hypnotic"). This is THE flow fix.
- `--freq alpha` = 10 Hz isochronic (flow/let-loose). Synthesizes a 210 Hz carrier gated at 10 Hz,
  mixes under the music at −20 dB; `techno-hypnotic` preset masters to club level (−12 LUFS).
- For 1 hr use `--unique 12`, `--seg-len 240`. Watch `grep '\[m1\]' /tmp/tk.log`; wait for `[m1] DONE`.

**Why copyright-clean:** ACE-Step is MIT-licensed, trained on licensed + royalty-free + synthetic
data — output is safe to monetize.

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

## 5. Render — the fast renderer

Tool: `render_visualizer.py` (repo `video-creator/backend/render_visualizer.py`, on box
`/home/ubuntu/render_visualizer.py`, runs in `audio_pipeline/venv`). NumPy vertical flip ≈66 fps
@1080p. **Output is VIDEO ONLY → mux the audio after.**

```bash
# PROTOTYPE FIRST (short clip → open for approval)
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && \
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
  --audio music_out/techno_alpha_<N>min.mp3 --out /home/ubuntu/proto.mp4 --dur 15 --fps 30 --w 1920 --h 1080'
# extract a frame, scp back, Read it; mux a short audio slice + open on Mac for approval.

# FULL high-quality render (CRF 16; medium preset; detached) + mux
ssh -i "$PEM" ubuntu@$EC2_IP 'source /home/ubuntu/audio_pipeline/venv/bin/activate; cd /home/ubuntu && nohup bash -lc "
  python3 render_visualizer.py --shader video-creator-backend/shaders/<name>.glsl \
    --audio music_out/techno_alpha_<N>min.mp3 --out /home/ubuntu/tk_silent.mp4 \
    --dur <N*60> --fps 30 --w 1920 --h 1080 --crf 16 --preset medium ;
  ffmpeg -y -i tk_silent.mp4 -i music_out/techno_alpha_<N>min.mp3 -map 0:v -map 1:a \
    -c:v copy -c:a aac -b:a 256k -shortest /home/ubuntu/techno_visual_<N>min.mp4 ;
  echo ALLDONE" > /tmp/tkrender.log 2>&1 & echo pid=$!'
```
- **CRF is the quality knob** (16–18 = high); preset only trades render-time for file-size at that
  quality (`medium` ≈ 34 fps; `veryfast` ≈ 66 fps; `slow` ≈ 20 fps).
- 60 min = 108k frames ≈ 30–45 min at CRF16/medium. Run detached; watch for `ALLDONE`.

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
