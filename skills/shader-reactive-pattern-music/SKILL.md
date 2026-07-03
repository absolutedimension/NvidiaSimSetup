---
name: shader-reactive-pattern-music
description: >
  Turn any MUSIC track into a finished audio-reactive SHADER VIDEO (sacred-geometry / Flower-of-Life
  "circle of life" patterns that breathe, bloom and ring out to the music) and publish it to the
  TrigunFlowArt YouTube channel. Give it an audio file; it analyzes the audio into frequency bands,
  drives a GLSL shader's parameters from those bands (bass pulses the zoom, mids open the pattern,
  onsets trigger blooms/echoes), renders 1080p on the EC2 A10G with NVENC (~80fps), muxes the audio,
  and hands the MP4 to the FlowArt uploader. Ships a library of flow shaders (emantra_pattern /
  flower_of_life_flow / enso_flow / bowl_ripples / kaleido_flow / sacred_geometry / lotus / mercury
  techno / vocal_melt ...) and takes a user-pasted shader too, with an optional melted background
  image behind the pattern, per-chapter seed/tint/fold controls, and tone-mapping so it never blows
  out. Use when the user wants: "make a visualizer for this track", "shader-reactive video", "circle
  of life / flower of life video", "sacred geometry visualizer", "FlowArt video", "turn this music
  into a video", "audio-reactive shader", "visualize this song", "make a flow-art video and upload it".
  This is the VIDEO/visual half — the music itself comes from track-studio-trigunai / hypnotic-techno
  -trigunai / learn-dj-style-trigunai. Upload goes through trigunai-yt-flowart. Runs on EC2 (EIP
  34.192.145.204, A10G, NVENC).
---

# shader-reactive-pattern-music — music → audio-reactive shader video → FlowArt

Take a finished **music track** and produce a **finished audio-reactive shader video**, then publish
it to **TrigunFlowArt** (@trigunflowart). The visual engine drives a GLSL shader's parameters from
the music's frequency bands so the pattern (a Flower-of-Life / "circle of life" mandala, an enso ring,
singing-bowl ripples, a kaleidoscope, etc.) **breathes with the bass, opens with the mids, and blooms
on onsets**. Rendered 1080p on the EC2 A10G with NVENC.

**Scope:** this skill owns the PIXELS + the upload. The MUSIC comes from elsewhere
(`track-studio-trigunai`, `hypnotic-techno-trigunai`, `learn-dj-style-trigunai`). Keep them separate.

---

## Environment (verify first)

| Item | Value |
|---|---|
| EC2 (stable EIP) | `34.192.145.204` (A10G, NVENC). Start the box if SSH times out. |
| SSH key | `~/.ssh/trigunai_key.pem` |
| Render engine (EC2) | `video-creator/backend/render_visualizer_bands.py` (also bundled in `scripts/`) |
| Shaders | bundled in this skill's `shaders/` (+ full library at `video-creator/backend/shaders/`) |
| FlowArt uploader | `~/yt_flowart/` on the Mac (`yt_upload.py` + `token_flowart.json`) — driven by the `trigunai-yt-flowart` skill |
| Local delivery | pull the MP4 to `music_pipeline/dj_engine/burmeister/` (or wherever the track lives) |

Boot check: `ssh -i ~/.ssh/trigunai_key.pem -o ConnectTimeout=15 ubuntu@34.192.145.204 'echo OK'`
→ if it times out the box is stopped; ask the user to start it, poll until up.

---

## The renderer — `render_visualizer_bands.py`

```
--audio    <mp3/wav>     REQUIRED  the music track
--out      <mp4>         REQUIRED  output (video-only; audio muxed after)
--shader   <glsl>        REQUIRED  path to the shader (see library below)
--dur      <sec>                   render length (default 12; set to the track duration)
--fps      30            --w 1920  --h 1080
--encoder  nvenc         (GPU, ~80fps 1080p)  |  x264 (CPU fallback)
--nbands   8             frequency bands the audio is split into
--release  0.86          per-band decay — higher = longer ring-out / smoother
--bg       <png>         optional background image, "melted" behind the pattern
--seed     0.0           per-chapter flowering seed (vary per section/track)
--tint     r,g,b         color tint, e.g. 1.12,1.0,0.78 (warm gold)
--foldlo 6 --foldhi 12   kaleidoscope fold range
--crf      20            x264 quality (nvenc uses its own)
```

**Standard render + mux (the proven recipe):**
```bash
PEM=~/.ssh/trigunai_key.pem; EC2=34.192.145.204
DUR=$(python3 -c "import librosa;print(round(librosa.get_duration(path='TRACK.mp3'),1))")
ssh -i $PEM ubuntu@$EC2 'bash -lc "
  python3 render_visualizer_bands.py --shader shaders/emantra_pattern.glsl \
    --audio ~/path/TRACK.mp3 --bg ~/path/bg.png \
    --seed 2 --tint 1.12,1.0,0.78 --foldlo 6 --foldhi 10 \
    --out /tmp/vid.mp4 --dur '$DUR' --fps 30 --w 1920 --h 1080 --encoder nvenc --release 0.90 && \
  ffmpeg -y -i /tmp/vid.mp4 -i ~/path/TRACK.mp3 -c:v copy -c:a aac -b:a 256k -shortest ~/OUT.mp4
"'
```
Then pull `OUT.mp4` to the Mac. For chat delivery only, also make a 720p copy
(`ffmpeg -i OUT.mp4 -vf scale=1280:720 -c:v libx264 -crf 30 -c:a aac -b:a 160k OUT_720.mp4`) —
the full 1080p is what gets uploaded.

---

## Shader library (bundled in `shaders/`)

| Shader | Look |
|---|---|
| `emantra_pattern.glsl` | **Flower-of-Life mandala** ("circle of life") — band-driven pattern, blooms on peaks. The flagship. |
| `flower_of_life_flow.glsl` | Flower-of-Life rings/zoom that bloom at peaks |
| `enso_flow.glsl` | Ink enso ring that breathes, echoes on onsets |
| `bowl_ripples.glsl` | Singing-bowl Mel-ripple concentric waves |
| `sacred_geometry.glsl` | General sacred-geometry field |
| `kaleido_flow.glsl` | Audio-reactive kaleidoscope (use `--foldlo/--foldhi`) |
| `question_portal_flow.glsl` | Portal beacon + incoming bubbles rise with energy |
| `lotus_deephouse.glsl` / `neon_tunnel_lotus.glsl` | Lotus forms (deep-house feel) |
| `mercury_techno.glsl` | Liquid-metal techno |
| `vocal_melt.glsl` | Melts/warps with vocal energy |
| `emantra_flow.glsl` / `emantra_multi.glsl` / `cosmic_drift.glsl` | More flow variants |

All are tone-mapped so they never blow out. The user may also **paste their own GLSL** — save it and
pass it as `--shader`.

---

## Step-by-step flow (offer 3 options where it helps)

1. **Get the music.** The user gives a track (or it's the output of `track-studio-trigunai`). Get its
   path on EC2 (scp up if it's only local). Compute duration with librosa.
2. **Pick the shader — 3 options:** (a) **Flower-of-Life / circle-of-life** (`emantra_pattern`, the
   flagship) · (b) another from the library (enso / bowl / kaleido / lotus / sacred_geometry …) ·
   (c) **paste your own GLSL**. Show the look table; let them choose.
3. **Background & color — 3 options:** (a) no background (pure pattern on black) · (b) a melted image
   `--bg` (nebula / AI-generated art) · (c) generate a fresh background image for the vibe. Set
   `--tint` for mood (warm gold `1.12,1.0,0.78`, cool, etc.) and `--seed` per track.
4. **Render** on EC2 (NVENC, full track length) → **mux the audio** → pull the MP4 → play/preview.
   Iterate on tint/seed/release/shader until the user likes it.
5. **Upload — 3 options:** (a) **publish to TrigunFlowArt now** (hand off to `trigunai-yt-flowart`
   with a title + description) · (b) save the MP4 only · (c) upload as **unlisted/private** first for
   review. FlowArt uploader lives at `~/yt_flowart/` (`yt_upload.py`, `token_flowart.json`).

---

## Publishing to FlowArt
Use the **`trigunai-yt-flowart`** skill (brand account @trigunflowart). It needs a title, description,
and the MP4. Typical FlowArt framing: a flow-state / focus / sacred-geometry piece — name the vibe
(e.g. "Hypnotic Techno + Flower of Life · 7 min flow"), tag it, set the thumbnail. Keep the first
publish **unlisted** if the user wants to review on the channel before going public.

## Gotchas
- **NVENC only on the A10G box** — if the box is stopped, SSH fails; start it, poll, retry.
- **Mandala detail resists compression** — 7-min 1080p ≈ 600–800 MB. That's the *upload* master;
  make a 720p copy only for chat preview.
- **Duration must match the track** — always set `--dur` from librosa, else the video is cut short.
- **`--release` is the smoothing knob** — raise toward 0.9 for smooth ring-out, lower for snappy.
- **Keep music + video separate** — this skill never generates the audio; it consumes a finished track.
