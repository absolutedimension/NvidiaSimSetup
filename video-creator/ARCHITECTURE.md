# TrigunAI Video Creator — Architecture

> A React-based frontend that turns a script into a professional learning video
> in a step-by-step flow. Wraps the entire pipeline built on EC2.

---

## The 5-Step Flow (what the user sees)

```
Step 1: SCRIPT          Step 2: VOICE         Step 3: VISUALS       Step 4: MUSIC         Step 5: RENDER
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Write/paste  │──▶│ Pick voice   │──▶│ Pick template│──▶│ Pick mood    │──▶│ Preview &    │
│ script with  │   │ per scene    │   │ per scene    │   │ Generate     │   │ Render final │
│ scene breaks │   │ Preview tone │   │ Assign slides│   │ background   │   │ MP4          │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React + Vite + TailwindCSS | Fast, modern, beautiful UI |
| **State** | Zustand | Simple state management, no Redux bloat |
| **API** | FastAPI (Python) on EC2 | Wraps F5-TTS, ACE-Step, Hallo2, ffmpeg, slide renderer |
| **Rendering** | EC2 GPU (A10G) | All heavy work happens server-side |
| **Storage** | EC2 local + S3 (future) | Generated videos stored on EC2, downloadable |

---

## Frontend Pages

### Page 1: Script Editor
- Textarea for full script
- "Add Scene Break" button splits into scenes
- Each scene gets:
  - Scene title (auto-numbered)
  - Text content
  - Tone selector dropdown (confident/excited/calm/friendly)
  - Gender selector (male/female)
  - Template selector (T1-T7 from template system)
  - Duration estimate (auto-calculated from word count)
- Import from JSON / Export to JSON
- "Proceed to Voice" button

### Page 2: Voice Studio
- Shows each scene with its text + selected tone
- "Generate Voice" button per scene (calls F5-TTS API)
- Audio player per scene — listen, re-generate if not happy
- Speed slider (0.65 – 1.0, default 0.75)
- "Generate All" button for batch
- Waveform visualization
- "Proceed to Visuals" button

### Page 3: Visual Builder
- Shows each scene with its template type
- For T6 (motion graphics / animated slides):
  - Slide editor: title text, body text, accent color, layout
  - Live preview of the slide
  - Background particle toggle
  - Screenshot upload for credibility slides
- For T1 (talking head):
  - Upload presenter image
  - Hallo2 will animate it
- For T2 (screen recording):
  - Upload screen recording file
  - Trim controls
- For T3 (tablet annotation):
  - Upload drawing/annotation video
- "Proceed to Music" button

### Page 4: Music & Audio
- Text prompt for background music mood
  - Presets: "Inspiring corporate", "Calm ambient", "Energetic tech", "Emotional piano"
- Generate button (calls ACE-Step API)
- Audio player for generated music
- Music volume slider (vs voice)
- Fade in/out controls
- "Proceed to Render" button

### Page 5: Preview & Render
- Timeline view: all scenes laid out with thumbnails + waveforms
- Drag to reorder scenes
- Play preview (approximate — slides + voice, no Hallo2 yet)
- "Render Final Video" button
  - Shows progress bar
  - Assembles: slides with animation + voice + music + Hallo2 avatar
- Download MP4 when done
- Also: export project as JSON (for re-editing later)

---

## Backend API Endpoints (FastAPI on EC2)

```
POST /api/voice/generate
  body: { text, tone, gender, speed }
  returns: { audio_url, duration }

POST /api/voice/generate-all
  body: { scenes: [{text, tone, gender, speed}, ...] }
  returns: { segments: [{audio_url, duration}, ...] }

POST /api/slides/generate
  body: { scenes: [{title, body, accent_color, layout, template}, ...] }
  returns: { slides: [{image_url}, ...] }

POST /api/slides/preview
  body: { title, body, accent_color, layout }
  returns: { image_url }

POST /api/music/generate
  body: { prompt, duration_seconds }
  returns: { audio_url, duration }

POST /api/avatar/generate
  body: { image_url, audio_url }
  returns: { video_url } (long-running, returns job_id)

POST /api/avatar/status/{job_id}
  returns: { status, progress, video_url }

POST /api/render/final
  body: { project_json }  (full project with all scenes, voice, slides, music)
  returns: { job_id }

GET /api/render/status/{job_id}
  returns: { status, progress, video_url, download_url }

GET /api/voices
  returns: { voices: [{name, gender, tone, tags, preview_url}, ...] }

POST /api/upload/screenshot
  body: multipart file
  returns: { file_url }

POST /api/upload/recording
  body: multipart file
  returns: { file_url }
```

---

## Project Structure

```
video-creator/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── index.html
├── public/
│   └── trigunai-logo.png
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts              # API client for EC2 backend
│   ├── store/
│   │   └── projectStore.ts        # Zustand store for project state
│   ├── types/
│   │   └── project.ts             # TypeScript types
│   ├── pages/
│   │   ├── ScriptEditor.tsx        # Step 1
│   │   ├── VoiceStudio.tsx         # Step 2
│   │   ├── VisualBuilder.tsx       # Step 3
│   │   ├── MusicAudio.tsx          # Step 4
│   │   └── RenderPreview.tsx       # Step 5
│   ├── components/
│   │   ├── StepProgress.tsx        # Top progress bar (Step 1 of 5)
│   │   ├── SceneCard.tsx           # Reusable scene card
│   │   ├── AudioPlayer.tsx         # Waveform audio player
│   │   ├── ToneSelector.tsx        # Voice tone dropdown
│   │   ├── TemplateSelector.tsx    # T1-T7 template picker
│   │   ├── SlidePreview.tsx        # Live slide preview
│   │   ├── Timeline.tsx            # Scene timeline view
│   │   └── ProgressModal.tsx       # Render progress overlay
│   └── styles/
│       └── globals.css
│
├── backend/                         # FastAPI backend (runs on EC2)
│   ├── main.py                      # FastAPI app
│   ├── routes/
│   │   ├── voice.py                 # F5-TTS endpoints
│   │   ├── slides.py                # Slide generator endpoints
│   │   ├── music.py                 # ACE-Step endpoints
│   │   ├── avatar.py                # Hallo2 endpoints
│   │   └── render.py                # Final video assembly
│   ├── services/
│   │   ├── f5tts_service.py         # Wraps F5-TTS
│   │   ├── slide_service.py         # Wraps slide renderer
│   │   ├── music_service.py         # Wraps ACE-Step
│   │   ├── hallo2_service.py        # Wraps Hallo2
│   │   └── render_service.py        # ffmpeg assembly
│   ├── models/
│   │   └── project.py               # Pydantic models
│   └── requirements.txt
│
└── ARCHITECTURE.md                  # This file
```

---

## Build Plan (5 days)

| Day | What | Deliverable |
|---|---|---|
| 1 | Backend API: voice + slides endpoints | F5-TTS + slide generator wrapped in FastAPI, tested with curl |
| 2 | Backend API: music + render endpoints | ACE-Step + ffmpeg assembly wrapped, full pipeline testable via API |
| 3 | Frontend: Script Editor + Voice Studio | Steps 1-2 working in browser |
| 4 | Frontend: Visual Builder + Music + Render | Steps 3-5 working, end-to-end flow |
| 5 | Polish + test full flow | Create a complete video from the UI, fix bugs, deploy |

---

## Key Design Decisions

1. **EC2 is the backend** — all GPU work (voice, avatar, music, rendering) happens on EC2. Frontend is pure React, can run anywhere.

2. **Project = JSON file** — the entire project state (script, voice settings, slide configs, music prompt) is a single JSON. Export/import. Version control. Reproducible.

3. **Scene-based architecture** — everything is organized by scene. A scene has: text, tone, template, voice audio, visual asset, and timing.

4. **Progressive rendering** — voice generates fast (~10s/scene), slides generate fast (~2s/slide), music generates in ~2 min, Hallo2 is slow (~10 min for full video). Show progress for each.

5. **Tone library is the voice system** — the 8 pre-built voice references (4 female, 4 male, 4 tones each) are the voice palette. No need to upload reference audio — just pick from the dropdown.
