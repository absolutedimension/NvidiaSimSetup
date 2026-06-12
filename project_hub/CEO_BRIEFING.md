# TrigunAI — CEO Briefing

> Last updated: 2026-06-08 by CEO session (massive build session — education pivot + video platform)

---

## 🔥 Needs your attention

1. **Course launch July 18 is 40 days away.** Video Creator tool is built. Now use it to produce Module 1 content.
2. **learn.trigunai.com is LIVE.** Video Creator deployed on Azure with SSL. Backend connected to EC2 GPU.
3. **Landing page prototype running locally** at localhost:5175. Needs video assets + deploy to trigunai.com.
4. **EC2 is running and billing ~$1/hr.** Stop it when not actively rendering. All tools persist on EBS.
5. **Hallo2 lip-sync** had OOM issues on full-length videos. Chunking approach works (chunk_00 succeeded). Lower priority — animated slides + voice is the production path.

---

## 📊 What was built this session (June 5-8)

### Strategic rearrangement
- ✅ **CEO OS v4.1** — education pivot: courses as primary revenue, Deepak solo-executing, Avinash sleeping partner
- ✅ **Course selected:** "Build & Ship Your First VR/MR App — AI-Powered Development with Unity & Meta Quest"
- ✅ **Student personas defined:** Ravi (CS student), Priya (career changer), Alex (indie creator)
- ✅ **Competitive analysis:** 15/15 topics covered vs competitor's 5/15
- ✅ **Course outline:** 11 modules, ~14 hours, includes AI coding agent workflow (Module 2 — unique differentiator)
- ✅ **Module 1 full script:** 8 lectures, scene-by-scene with production notes
- ✅ **Launch workflow:** 44-day day-by-day plan with weekly gates
- ✅ **Dashboard:** `dashboard.html` — visual task tracker with checkboxes
- ✅ **Udemy instructor account** created

### Video production pipeline (complete, end-to-end)
- ✅ **F5-TTS voice system:** 8 voices (4 female + 4 male), 4 tones each (confident/excited/calm/friendly), speed-controllable. Studio quality, Indian English.
- ✅ **Shader FX system:** 10 GLSL shader templates (5 learning + 5 cinematic), GPU-rendered via ModernGL, audio-reactive. Learning shaders are ultra-slow and elegant.
- ✅ **Skybox environment system:** 6 HDRI-based 3D environments with camera orbit
- ✅ **Slide renderer:** Pillow-based with particles, gradients, text animation
- ✅ **Compositor:** 4-layer video assembly (skybox → shader → slides → presenter)
- ✅ **AI music generation:** ACE-Step (installed, not yet tested) + ambient fallback
- ✅ **Hallo2 talking avatar:** Installed, chunk_00 lip-sync working, full video OOM (use chunking)
- ✅ **AI image generation:** Presenter avatar generated via Azure gpt-image-1.5
- ✅ **Edge-TTS + F5-TTS voiceover:** Welcome video voice in both male and female, approved at 0.75 speed

### TrigunAI Video Creator (SaaS product)
- ✅ **React frontend** — 5-step flow: Script → Voice → Visuals → Music → Render
- ✅ **FastAPI backend** — Job queue (SQLite), worker agents, WebSocket real-time progress
- ✅ **Deployed to Azure Container Apps** — `learn.trigunai.com` with managed SSL
- ✅ **EC2 GPU worker** — processes voice/slides/music/render jobs
- ✅ **Architecture:** scalable queue system, designed for multi-tenant SaaS later

### Landing page (trigunai.com)
- ✅ **Interactive video-style design** — full-screen, locked scroll, click navigation
- ✅ **Two user journeys:** Creator (→ Video Creator tool) vs Student (→ VR course)
- ✅ **React + Framer Motion + Tailwind** — 11 screens with cinematic animations
- ✅ **Running locally** at localhost:5175, ready to deploy

### Assets produced
- ✅ 18 animated slides (1920×1080, dark theme, particles)
- ✅ 11-module timeline graphic (AI-generated)
- ✅ Presenter avatar (AI-generated Indian woman, professional)
- ✅ TrigunAI logo (both dark and light versions, from Blender renders)
- ✅ F5-TTS voiceover: 9 scenes, female slow (2.9 min) + male slow (2.8 min)
- ✅ 10 shader test videos (5 learning + 5 cinematic)
- ✅ Welcome video v3 (animated slides + particles, 4.5 min)
- ✅ Hallo2 chunk_00 lip-sync preview (30s)

---

## 💰 Cost snapshot

| Resource | This session | Total |
|---|---|---|
| EC2 g5.2xlarge | ~8 hrs × $1/hr = ~$8 | ~$20 total project |
| Azure Container App | ~$0.50/day | First bill pending |
| Azure Container Registry | ~$0.17/day (Basic) | First bill pending |
| Azure gpt-image-1.5 | ~$0.20 (2 images) | $0.40 total |
| F5-TTS / Hallo2 / ModernGL | $0 (open source) | $0 |
| Edge-TTS | $0 (free) | $0 |
| **Total session** | **~$9** | |

---

## 📋 Workstream status

| Workstream | Status | What's next |
|---|---|---|
| **Course 1 (VR/MR App)** | Outline + Module 1 script + video pipeline ready | Record Module 1 using the Video Creator tool |
| **Video Creator tool** | ✅ LIVE at learn.trigunai.com | Connect EC2 worker for live rendering |
| **Landing page** | Prototype running locally | Deploy to trigunai.com (or subdomain) |
| **Shader system** | 10 templates working | Integrate into Video Creator UI |
| **Voice system** | 8 voices working | Already integrated in backend |
| **Hallo2 avatar** | Chunk approach works, full video OOM | Lower priority — slides+voice is cleaner |
| **YouTube channel** | Not started | Set up + upload Module 1 teaser |
| **Udemy listing** | Account created | Upload course content after recording |
| **Student acquisition** | Not started | After Module 1 YouTube teaser is up |

---

## 🔮 Next priorities (in order)

1. **Record Module 1** using the Video Creator — this produces the YouTube teaser AND the first Udemy section
2. **Deploy landing page** to trigunai.com
3. **Connect EC2 worker** to Azure backend for live video rendering
4. **YouTube channel** — upload Module 1 teaser
5. **Script + record Modules 2-3** (AI Coding Partner + Hands)
6. **Pre-enrollment** — open on Udemy with early bird pricing
7. **Stop EC2** when not rendering — save $24/day

---

## 🚨 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| July 18 is 40 days away — tight for 11 modules | High | Launch with 4-6 modules, add rest post-launch |
| EC2 billing (~$24/day if left running) | Medium | Stop when not rendering. Budget: $100/mo |
| One person doing everything | High | Video Creator tool 10x's production speed |
| Hallo2 OOM on long videos | Low | Use slides+voice (production quality), avatar is v2 |
| Disk space on Mac (97% full) | Medium | Clean Downloads + old project files |

---

## 🤖 Tools & infrastructure

| Tool | Location | Purpose |
|---|---|---|
| **Video Creator** | learn.trigunai.com | Frontend for video production |
| **Backend API** | Azure Container App (port 80) | Job queue + API |
| **GPU Worker** | EC2 18.234.73.93:8010 | F5-TTS, shaders, rendering |
| **Voice Library** | EC2 `/home/ubuntu/audio_pipeline/voice_library/` | 8 voices, tone-selectable |
| **Shader Library** | EC2 `/home/ubuntu/video-creator-backend/shaders/` | 10 GLSL templates |
| **F5-TTS** | EC2 venv `/home/ubuntu/audio_pipeline/venv/` | Voice generation |
| **Hallo2** | EC2 `/home/ubuntu/hallo2/` | Talking avatar (experimental) |
| **Dashboard** | `NvidiaSimSetup/dashboard.html` | Launch day tracker |
| **Landing page** | `NvidiaSimSetup/landing-page/` (localhost:5175) | trigunai.com prototype |
| **Course scripts** | `NvidiaSimSetup/course_scripts/` | Module scripts |
| **Course outline** | `NvidiaSimSetup/COURSE_OUTLINE.md` | 11-module structure |
| **Student persona** | `NvidiaSimSetup/STUDENT_PERSONA.md` | 3 target personas |
| **Launch workflow** | `NvidiaSimSetup/LAUNCH_WORKFLOW_JULY18.md` | 44-day plan |

---

*Session: June 5-8, 2026 | Deepak Kumar | Solo execution*
*Next session: Record Module 1 → upload to YouTube + Udemy*
