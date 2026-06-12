---
name: trigunai-table-read-director
description: >
  AI film director that turns a table read (dialogue + background music MP3) into a complete
  cinematic animated short. Transcribes dialogue, analyzes emotional arc, generates camera
  mode schedule, renders character on stage with mood-matched lighting/environments, and
  composites final video with synced audio + subtitles. Use when the user says "animate this
  audio", "make a video from this MP3", "table read to animation", "direct this scene",
  "turn this into a film", "animate the audiobook", or provides an audio file and says
  "create animation on top of this".
---

# TrigunAI Table Read Director

You are an **AI film director**. Given an audio file (dialogue + music), you produce a
complete cinematic animation — camera, lighting, stage, character, subtitles — all driven
by the audio content.

**One input, one output:**
```
INPUT:  audiobook.mp3 (dialogue + background music)
OUTPUT: cinematic_short.mp4 (animated character on stage, camera moves match dialogue emotion,
        lighting shifts with mood, subtitles show dialogue, original audio as soundtrack)
```

---

## Architecture: 6-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: AUDIO INTELLIGENCE                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Source Sep.   │  │ Deepgram     │  │ librosa            │    │
│  │ (demucs)     │  │ Nova-2 STT   │  │ beat/energy/spec   │    │
│  │ → voice stem │  │ → transcript │  │ → music features   │    │
│  │ → music stem │  │ + timestamps │  │ per frame          │    │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘    │
│         │                 │                     │               │
│  STAGE 2: SCRIPT ANALYSIS (LLM)                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ GPT-4o-mini reads transcript + music features           │    │
│  │ → Identifies scenes/beats with emotional labels         │    │
│  │ → Maps each beat to a cinematographic mode              │    │
│  │ → Generates shot notes (e.g., "push in on speaker")     │    │
│  │ → Outputs: scene_breakdown.json                         │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  STAGE 3: CINEMATOGRAPHY PLANNING                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ scene_breakdown.json → mode_schedule string             │    │
│  │ → export_cinematographer_trajectory.py (existing)       │    │
│  │ → Full camera trajectory with mode-synced switches      │    │
│  │ → Snap transitions to beat boundaries                   │    │
│  │ → Output: trajectory.json (per-frame pos + quat + mode) │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  STAGE 4: VISUAL PRODUCTION                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ render_demo_blender.py (existing, extended)             │    │
│  │ → Per-mode HDRI environment (stage_design/hdri/)        │    │
│  │ → Per-mode lighting presets (lighting/presets.py)        │    │
│  │ → Daphne character on stage                             │    │
│  │ → Camera path from trajectory                           │    │
│  │ → HDRI crossfade at mode transitions                    │    │
│  │ → Blender EEVEE headless render → PNG sequence          │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  STAGE 5: POST-PRODUCTION                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ffmpeg composite:                                       │    │
│  │ → PNG sequence → video stream                           │    │
│  │ → Original MP3 → audio track (synced)                   │    │
│  │ → Transcript → .srt subtitles (burned in or sidecar)    │    │
│  │ → Mode indicator overlay (which mode is active)         │    │
│  │ → Optional: title card + end credits                    │    │
│  │ → Output: final_cinematic.mp4                           │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  STAGE 6: QUALITY & DELIVERY                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ → VLM quality check (gpt-4o-mini grades 6 keyframes)   │    │
│  │ → Extract hero frames for thumbnails/marketing          │    │
│  │ → Generate delivery package (video + srt + thumbnails)  │    │
│  │ → Cost report                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Audio Intelligence

### 1A. Source Separation (Optional — enhances quality)

Separate dialogue from background music using `demucs` (Meta's open-source model).
This lets us analyze music features WITHOUT speech energy contaminating the signal,
and produce a clean transcript.

```bash
# On EC2 (or Mac if demucs installed):
pip install demucs
python3 -m demucs --two-stems=vocals "/path/to/audiobook.mp3" -o /tmp/separated/
# Produces: vocals.wav (dialogue) + no_vocals.wav (background music)
```

**Fallback if demucs unavailable:** Skip separation, run Deepgram on the mixed audio
(Nova-2 handles background music well), and run librosa on the mixed audio (the music
features will be noisier but still usable).

### 1B. Transcription (Deepgram Nova-2)

```python
# transcribe_audio.py
import requests, json, os

DEEPGRAM_KEY = os.environ.get("DEEPGRAM_API_KEY") or open(".env").read().split("=")[1].strip()

def transcribe(audio_path, output_json):
    """Transcribe audio via Deepgram Nova-2 with word-level timestamps."""
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "model": "nova-2",
        "language": "en",
        "punctuate": "true",
        "diarize": "true",        # speaker detection
        "paragraphs": "true",     # natural paragraph breaks
        "smart_format": "true",
        "utterances": "true",     # group into utterances
    }
    headers = {
        "Authorization": f"Token {DEEPGRAM_KEY}",
        "Content-Type": "audio/mpeg",
    }
    with open(audio_path, "rb") as f:
        resp = requests.post(url, headers=headers, params=params, data=f)
    result = resp.json()

    # Extract structured transcript
    transcript = {
        "full_text": result["results"]["channels"][0]["alternatives"][0]["transcript"],
        "paragraphs": result["results"]["channels"][0]["alternatives"][0].get("paragraphs", {}),
        "utterances": result.get("results", {}).get("utterances", []),
        "words": result["results"]["channels"][0]["alternatives"][0]["words"],
    }
    with open(output_json, "w") as f:
        json.dump(transcript, f, indent=2)
    return transcript
```

**Cost:** ~$0.0043/min × 8.5 min = ~$0.04

### 1C. Music Feature Extraction (librosa)

Use the existing `music_director.py` on the music stem (or mixed audio):

```bash
/Library/Developer/CommandLineTools/usr/bin/python3 cinematography/music_director.py \
    --mp3 /tmp/separated/no_vocals.wav \
    --fps 50 --snap-to-beats \
    --json-out /tmp/music_features.json
```

---

## Stage 2: Script Analysis (LLM)

The core intelligence — an LLM reads the transcript and decides the emotional arc.

### Prompt Template

```
You are an expert film director analyzing a script for a cinematic animation.

TRANSCRIPT (with timestamps):
{transcript_with_timestamps}

MUSIC ANALYSIS:
- Tempo: {tempo} BPM
- Energy curve: {energy_summary}
- Beat density: {beat_summary}

AVAILABLE CINEMATOGRAPHIC MODES:
1. HERO — dramatic, powerful, center-stage, red/gold lighting, arena setting
2. INTIMATE — close, personal, warm amber, jazz club, quiet moments
3. EPIC — grand, sweeping, blue/white lasers, stadium, big reveals
4. ENERGY — intense, fast, neon strobes, underground rave, action
5. SOLITUDE — isolated, reflective, single ghost light, empty theater, pauses
6. BEAUTY — elegant, flowing, pink/gold, fashion runway, graceful moments

Analyze the dialogue and create a scene breakdown. For each scene:
1. Identify the start timestamp (from word-level timestamps)
2. Label the emotion (dramatic, tender, revelatory, intense, reflective, graceful)
3. Choose the best cinematographic mode
4. Write a one-line shot note for the camera operator

Output STRICT JSON:
{
  "scenes": [
    {
      "start_time": 0.0,
      "end_time": 15.3,
      "emotion": "reflective",
      "mode": "INTIMATE",
      "dialogue_excerpt": "first 10 words...",
      "shot_note": "Slow push-in as narrator sets the scene"
    },
    ...
  ],
  "emotional_arc": "brief description of the overall narrative arc",
  "suggested_title": "a cinematic title for this piece"
}
```

**Implementation:**

```python
# scene_analyzer.py
import json, requests

def analyze_script(transcript_json, music_features_json, litellm_url="http://localhost:4000/v1"):
    """Use GPT-4o-mini to analyze the transcript and generate scene breakdown."""
    with open(transcript_json) as f:
        transcript = json.load(f)
    with open(music_features_json) as f:
        music = json.load(f)

    # Format transcript with timestamps
    formatted = ""
    for word in transcript["words"]:
        formatted += f"[{word['start']:.1f}s] {word['word']} "

    # Build the prompt (use template above)
    messages = [
        {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": f"TRANSCRIPT:\n{formatted}\n\nMUSIC: tempo={music['tempo']:.0f}BPM, duration={music['duration']:.0f}s"}
    ]

    resp = requests.post(
        f"{litellm_url}/chat/completions",
        headers={"Authorization": "Bearer sk-trigunai-master-key-2026"},
        json={
            "model": "gpt-4o-mini",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 4000,
        }
    )
    return json.loads(resp.json()["choices"][0]["message"]["content"])
```

**Cost:** ~$0.002 per call (one call for the full transcript)

### Scene Breakdown → Mode Schedule

```python
def scene_breakdown_to_schedule(scenes, fps=50):
    """Convert LLM scene breakdown to mode schedule string for trajectory export."""
    parts = []
    for scene in scenes:
        step = int(scene["start_time"] * fps)
        mode = scene["mode"]
        parts.append(f"{step}:{mode}")
    return ",".join(parts)
```

---

## Stage 3: Cinematography Planning

Use the existing pipeline — no new code needed:

```bash
# Inside isaaclab container on EC2:
cd /workspace/isaaclab
./isaaclab.sh -p cinematography/export_cinematographer_trajectory.py \
    --checkpoint /workspace/isaaclab/logs/.../cinematographer_v4_best.pth \
    --task Isaac-Cinematographer-Direct-v4 \
    --mode-schedule "$SCHEDULE_STRING" \
    --steps $((DURATION_SEC * 50)) \
    --fps 50 \
    --out /workspace/isaaclab/cinematography/audiobook_trajectory.json
```

The trained v4 policy handles mode switches automatically — it receives the mode one-hot
in observation space (33-dim = 20 state + 6 mode + 7 music) and adapts its camera behavior.

---

## Stage 4: Visual Production

Use the existing Blender render pipeline, extended for multi-mode HDRI switching:

```bash
# On EC2:
blender45 --background --python stage_design/render_demo_blender.py -- \
    --character /home/ubuntu/Daphne_Blender.fbx \
    --trajectory /home/ubuntu/audiobook_trajectory.json \
    --hdri-dir /home/ubuntu/hdri/ \
    --lighting-preset AUTO \
    --out /home/ubuntu/audiobook_render.mp4 \
    --width 1920 --height 1080 --fps 30 --engine EEVEE --samples 64
```

**Key extension needed:** `--hdri-dir` + `--lighting-preset AUTO` mode that reads the
mode field from each trajectory frame and swaps HDRI + lighting accordingly.

### HDRI Map (already downloaded):

```python
HDRI_MAP = {
    "HERO":     "hero_hdri.jpg",      # 5.4 MB, concert arena, red/gold
    "INTIMATE": "intimate_hdri.jpg",   # 5.3 MB, jazz club, warm amber
    "EPIC":     "epic_hdri.jpg",       # 4.8 MB, Olympic stadium, lasers
    "ENERGY":   "energy_hdri.jpg",     # 4.7 MB, underground rave, neon
    "SOLITUDE": "solitude_hdri.jpg",   # 4.6 MB, empty theater, ghost light
    "BEAUTY":   "beauty_hdri.jpg",     # 5.1 MB, fashion runway, pink/gold
}
```

**Video rendering:** See `VIDEO_RENDERING.md` for the master reference. Use Blender EEVEE (0.33s/frame) instead of OVRTX (6s/frame) — 18x faster.

### Render Time Estimates (Blender EEVEE on A10G):

| Duration | Resolution | FPS | Frames | Est. Time |
|---|---|---|---|---|
| 90s | 1920×1080 | 30 | 2700 | ~45 min |
| 8.5 min (507s) | 1920×1080 | 30 | 15210 | ~4.2 hours |
| 8.5 min | 1280×720 | 24 | 12168 | ~2.0 hours |
| 8.5 min | 1920×1080 | 24 | 12168 | ~3.4 hours |

**Recommendation for first pass:** 1280×720 @ 24fps = ~2 hours. Upgrade to 1080p for final.

---

## Stage 5: Post-Production

All ffmpeg — zero additional cost:

### 5A. Generate SRT from Deepgram transcript

```python
def transcript_to_srt(transcript_json, output_srt):
    """Convert Deepgram word timestamps to SRT subtitle file."""
    with open(transcript_json) as f:
        data = json.load(f)

    # Group words into subtitle chunks (max 8 words, max 4 seconds)
    srt_entries = []
    chunk = []
    chunk_start = None

    for word in data["words"]:
        if chunk_start is None:
            chunk_start = word["start"]
        chunk.append(word["word"])

        if len(chunk) >= 8 or (word["end"] - chunk_start) > 4.0:
            srt_entries.append({
                "start": chunk_start,
                "end": word["end"],
                "text": " ".join(chunk)
            })
            chunk = []
            chunk_start = None

    if chunk:
        srt_entries.append({
            "start": chunk_start,
            "end": data["words"][-1]["end"],
            "text": " ".join(chunk)
        })

    # Write SRT
    with open(output_srt, "w") as f:
        for i, entry in enumerate(srt_entries, 1):
            start = format_srt_time(entry["start"])
            end = format_srt_time(entry["end"])
            f.write(f"{i}\n{start} --> {end}\n{entry['text']}\n\n")
```

### 5B. Composite Final Video

```bash
# Combine rendered video + original audio + subtitles
ffmpeg -y \
  -i /home/ubuntu/audiobook_render.mp4 \
  -i "/home/ubuntu/audiobook.mp3" \
  -vf "subtitles=audiobook.srt:force_style='FontSize=22,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'" \
  -c:v libx264 -crf 20 -preset medium \
  -c:a aac -b:a 192k \
  -map 0:v -map 1:a \
  -shortest \
  /home/ubuntu/audiobook_final.mp4
```

### 5C. Mode Indicator Overlay (optional)

Burn a small mode badge in the corner showing which mode is active:

```bash
# Generate drawtext filter from mode schedule
# e.g., "drawtext=text='HERO':enable='between(t,10,30)':x=50:y=50:fontsize=24:fontcolor=white"
```

---

## Stage 6: Quality & Delivery

### Quality Gate (VLM)

```bash
python3 evaluate_drone_trajectory.py \
    --mp4 /home/ubuntu/audiobook_final.mp4 \
    --out /home/ubuntu/audiobook_evaluation.json
```

Evaluation criteria for table read:
- Character visible and properly lit in all scenes
- Mode transitions feel motivated by the dialogue content
- Camera movement matches the emotional tone
- Subtitles are readable and properly timed
- Audio/video sync is correct

### Delivery Package

```
audiobook_cinematic/
├── audiobook_final.mp4          # Full cinematic with audio + subtitles
├── audiobook_nosubs.mp4         # Clean version without subtitles
├── audiobook.srt                # Sidecar subtitle file
├── scene_breakdown.json         # LLM analysis (for debugging/editing)
├── audiobook_timeline.json      # Full mode schedule + music features
├── thumbnails/
│   ├── hero_frame.png           # Best frame per mode (for marketing)
│   ├── intimate_frame.png
│   ├── epic_frame.png
│   ├── energy_frame.png
│   ├── solitude_frame.png
│   └── beauty_frame.png
├── cost_report.json             # Total cost breakdown
└── README.md                    # What this is, how it was made
```

---

## Master Orchestration Script

The entire pipeline in one command:

```bash
# table_read_to_cinema.py — the one-shot orchestrator
python3 table_read_to_cinema.py \
    --audio "/path/to/audiobook.mp3" \
    --character /home/ubuntu/Daphne_Blender.fbx \
    --checkpoint /workspace/isaaclab/logs/.../cinematographer_v4_best.pth \
    --hdri-dir /home/ubuntu/hdri/ \
    --output-dir /home/ubuntu/audiobook_cinematic/ \
    --resolution 1920x1080 \
    --fps 24 \
    --quality draft|final
```

### Pipeline Steps (automated):

```
1. [LOCAL]  Transcribe audio → transcript.json           (~30s, $0.04)
2. [LOCAL]  Extract music features → music_features.json  (~10s, $0)
3. [LOCAL]  LLM scene analysis → scene_breakdown.json     (~5s, $0.002)
4. [LOCAL]  Generate mode schedule string                  (instant)
5. [EC2]    Export trajectory → trajectory.json            (~2 min)
6. [EC2]    Blender render → PNG sequence                  (~2-4 hours)
7. [EC2]    ffmpeg composite → final.mp4                   (~1 min)
8. [EC2]    VLM quality check → evaluation.json            (~10s, $0.0001)
9. [LOCAL]  Download final package                         (~5 min)
```

**Total cost per 8.5-min short: ~$0.05 API + ~$4 EC2 (4 hours × $1/hr) = ~$4**

---

## Quality Controls

### Transition Smoothness Rules

Mode switches should ONLY happen at:
1. **Sentence boundaries** — never mid-word or mid-phrase
2. **Musical beats** — snap to nearest beat for clean visual transitions
3. **Emotional inflection points** — where the dialogue tone genuinely shifts
4. **Minimum 5 seconds per segment** — no rapid-fire switching (disorienting)

The LLM scene analyzer enforces rules 1 and 3. The `--snap-to-beats` flag in
`music_director.py` enforces rule 2. Rule 4 is enforced by `--min-segment 5.0`.

### Camera Continuity

Between mode switches, the camera trajectory should be **continuous** — no jump cuts.
The trained v4 policy handles this naturally because it's a continuous control policy
that receives mode changes as observation updates, not discrete commands. The camera
smoothly transitions from one mode's behavior to the next.

### Audio-Visual Sync

Critical: the rendered video frame rate MUST match the audio duration exactly.
```
total_frames = int(audio_duration_seconds * render_fps)
trajectory_steps = int(audio_duration_seconds * policy_fps)  # 50 fps
# Downsample trajectory to render fps for Blender keyframes
```

---

## Supported Input Formats

| Format | How Handled |
|---|---|
| MP3 (dialogue + music mix) | Direct — Deepgram handles mixed audio well |
| MP3 (dialogue only, no music) | Works — music features will be flat, modes driven purely by dialogue emotion |
| WAV/FLAC/M4A | Convert to MP3 first (`ffmpeg -i input.wav -q:a 2 input.mp3`) |
| Separate dialogue + music tracks | Best quality — skip source separation, use each directly |
| Script text + music (no audio) | Use TTS to generate dialogue audio first (Deepgram Aura or similar) |

---

## Dependencies

### Local Mac
- Python 3.9+ with librosa, numpy, requests, soundfile
- ffmpeg (for format conversion if needed)
- Internet (for Deepgram API + LiteLLM proxy)

### EC2 (TrigunAI-Omniverse)
- isaaclab container with trained v4 cinematographer checkpoint
- Blender 4.5 LTS at /opt/blender45
- ffmpeg
- 6 stage HDRIs in stage_design/hdri/
- 6 lighting HDRI presets in lighting/hdri/
- Character FBX/GLB (Daphne or custom)
- LiteLLM proxy on port 4000 (for VLM quality check)

### API Keys (in .env)
- `DEEPGRAM_API_KEY` — for transcription ($200 free credit)
- LiteLLM master key — for GPT-4o-mini scene analysis (already configured on EC2)

---

## Extension: Multi-Character Scenes

For future versions with multiple characters:
- Deepgram's `diarize=true` identifies individual speakers
- Each speaker maps to a character position on stage
- Camera mode adapts based on WHO is speaking:
  - Speaker A talking → INTIMATE (close-up on A)
  - Speaker B responds → cut to B (still INTIMATE)
  - Both speaking / argument → ENERGY
  - Dramatic reveal → HERO
  - Silence / pause → SOLITUDE

---

## Extension: Real-Time / Interactive Mode

For live performances or live table reads:
- Deepgram streaming STT (existing `voice_commander.py` pattern)
- Real-time emotion detection from voice tone (pitch, pace, volume)
- Policy receives mode updates in real-time
- Camera moves adapt within 0.5s of dialogue shift
- WebSocket bridge to running simulation

This is the v2 vision — v1 is batch/offline.

---

## Files Created By This Skill

| File | Purpose | Location |
|---|---|---|
| `table_read_to_cinema.py` | Master orchestrator | `cinematography/` |
| `transcribe_audio.py` | Deepgram STT wrapper | `voice/` |
| `scene_analyzer.py` | LLM scene breakdown | `cinematography/` |
| `music_director.py` | Music → mode schedule | `cinematography/` (already exists) |
| `render_demo_blender.py` | Multi-mode Blender render | `stage_design/` (extend existing) |
| `composite_final.py` | ffmpeg post-production | `cinematography/` |

---

## Product Positioning

This is **"Upload audio → Get cinematic animation"** as a service.

No other product does this:
- **AI camera direction** — trained RL policy, not scripted camera paths
- **Emotion-driven modes** — dialogue content drives the visual treatment
- **Music-synced transitions** — mode switches land on beats
- **Full production pipeline** — lighting, stage, character, subtitles, all automated

**Target users:**
1. Audiobook publishers → animated audiobooks
2. Podcast producers → visual podcast episodes
3. Screenwriters → pre-visualization of scripts
4. Musicians → AI music videos
5. Corporate → animated training/presentation videos

**Pricing model:** $X per minute of output video. Cost to produce: ~$0.50/min.
