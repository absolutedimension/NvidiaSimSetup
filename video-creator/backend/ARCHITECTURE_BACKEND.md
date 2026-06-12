# Video Creator Backend — Scalable Queue + Agent Architecture

> Runs on single EC2 now. Deploys to Azure Container Apps later.
> GPU workers connect to queue — scale to zero when idle.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│              localhost:5174 / Azure Static Web App               │
└──────────────┬──────────────────────────────┬───────────────────┘
               │ REST API                     │ WebSocket
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API SERVER (FastAPI)                          │
│                   Port 8010 / Azure Container App               │
│                                                                 │
│  POST /api/project/create  → creates project + jobs             │
│  POST /api/job/submit      → adds job to queue                  │
│  GET  /api/job/{id}/status → poll status                        │
│  WS   /ws/project/{id}     → real-time progress stream          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              JOB QUEUE (SQLite / Redis)                  │   │
│  │                                                         │   │
│  │  Jobs: [voice_gen, slide_gen, music_gen, avatar_gen,    │   │
│  │         final_render]                                    │   │
│  │  States: queued → processing → completed / failed       │   │
│  │  Priority: voice > slides > music > avatar > render     │   │
│  └──────────┬──────────────────────────────┬───────────────┘   │
│             │                              │                    │
└─────────────┼──────────────────────────────┼────────────────────┘
              │ poll                          │ poll
              ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│   CPU WORKER          │      │   GPU WORKER                  │
│   (same machine or    │      │   (EC2 g5 / Azure GPU)        │
│    Azure Container)   │      │                                │
│                       │      │   Agents:                      │
│   Agents:             │      │   - VoiceAgent (F5-TTS, 4GB)  │
│   - SlideAgent        │      │   - MusicAgent (ACE-Step, 8GB) │
│   - RenderAgent       │      │   - AvatarAgent (Hallo2, 12GB) │
│     (ffmpeg)          │      │                                │
│                       │      │   Scales to 0 when idle        │
│                       │      │   Picks up jobs from queue     │
└──────────────────────┘      └──────────────────────────────┘
```

---

## Job Pipeline (what happens when user clicks "Render")

```
User clicks "Render Final Video"
  │
  ▼
API creates a PROJECT with child JOBS:
  ├── Job: voice_scene_01  (type: voice,  priority: 1)
  ├── Job: voice_scene_02  (type: voice,  priority: 1)
  ├── ...
  ├── Job: voice_scene_07  (type: voice,  priority: 1)
  ├── Job: slide_scene_01  (type: slide,  priority: 2)
  ├── ...
  ├── Job: slide_scene_07  (type: slide,  priority: 2)
  ├── Job: music_bg        (type: music,  priority: 3)
  ├── Job: avatar_gen      (type: avatar, priority: 4, depends_on: all voice jobs)
  └── Job: final_render    (type: render, priority: 5, depends_on: ALL above)
        │
        ▼
  Workers pick jobs from queue based on:
    - Priority (voice first, render last)
    - Dependencies (render waits for everything)
    - GPU availability (voice/music/avatar need GPU)
    - CPU tasks run in parallel (slides, ffmpeg)
        │
        ▼
  WebSocket pushes progress to frontend in real-time:
    { job_id, status, progress, step, eta }
```

---

## Scaling Strategy

### Phase 1: Single EC2 (NOW)
- API + Queue + Workers all on same g5.2xlarge
- SQLite for job queue (zero infra)
- Single GPU worker processes jobs sequentially
- Good for: personal use, course production

### Phase 2: Azure Container Apps (LATER)
- API Server: Azure Container App (CPU, always-on, $5/mo)
- Queue: Azure Queue Storage or Redis Cache ($2/mo)
- GPU Worker: Azure Container App with GPU (scale to zero)
  - Spot A10G: ~$0.50/hr when active, $0 when idle
- Storage: Azure Blob Storage for assets ($0.02/GB/mo)
- Frontend: Azure Static Web Apps (free tier)

### Phase 3: Multi-tenant SaaS
- User auth (Azure AD B2C or Clerk)
- Per-user job queues with rate limiting
- Multiple GPU workers for concurrent users
- CDN for delivered videos
- Stripe for billing
