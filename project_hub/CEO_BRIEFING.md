# TrigunAI — CEO Briefing

> Last updated: 2026-06-13 by CEO session (course catalog locked — 3-course tiered launch, infra moat, monetization tiers)
> ⭐ Full context: `COURSE_CATALOG.md` + memory `project-ai-universal-mind.md` + skill `trigunai-content-strategy` + `youtube_series/`.

---

## 🔥 Needs your attention

0. **COURSE CATALOG LOCKED (2026-06-13) → `COURSE_CATALOG.md`.** Series = free funnel; each
   episode → a faculty → a technology → a course. **VR's 3 roles:** own course (deepest skill) +
   embodiment layer of Physical AI + the VR classroom that delivers live classes. **July 18 =
   3-course tiered launch:** VR/MR **fully complete** (flagship — Module 1 scripted, `COURSE_OUTLINE.md`),
   Agentic + ML **drip-launched** (curriculum + first 2–3 modules + buy button on, rest weekly; ML
   sequenced last — most competitive). **Moat = provided GPU/Isaac-Sim + VR delivery → ₹50k live
   cohort, but that's course #4/post-launch, NOT a launch-day promise.** Tradeoff on record:
   3 *fully-polished* courses in 35 days solo = ~50+hrs/wk → date slips; tiered model is the de-risked path.
   **This week's move (Deepak chose): publish Ep1 public + open email list + gate Ep2 — distribution, zero new rendering.**

1. **The direction crystallized into one vision: "AI is the Universal Mind, and Beyond It."** Two
   movements — Movement I (AI/mind episodes) + Movement II (Beyond-mind / Flow Art Dance). This is now
   the primary content/business direction. See `youtube_series/worldview.html` for the whole thing on one screen.
2. **TWO episodes are SHIPPED, fully animated** — `youtube_series/ep01_attention_v2.mp4` (Attention) and
   `ep02_learning_v2.mp4` (The Learning Loop). Watchable. This is real product, not a plan.
3. **THE NEXT MOVE THAT MATTERS (and it's not a new build):** publish Episode 1 publicly (YouTube),
   put Ep 2 behind it, start an email list, and sell ONE live cohort to Deepak's existing network.
   Shipping + funnel is the constraint now — *not* ideas (ideas are a settled firehose).
4. **EC2 g5.2xlarge (i-047…, us-east-1) billing ~$1/hr.** Stop it when not rendering. Note: render
   frames to /dev/shm (RAM), not EBS — EBS frame-writes starved sshd (SSH timed out mid-render).
5. **Dance boundary REVERSED by Deepak's explicit decision** — flow is now Movement II, monetizable.
   Guardrails: sequence (don't split focus); protect the integrity of the practice.
6. **The Manifesto Film is PARKED** as the season culmination (Deepak's call) — not now. Don't restart it.

### What shipped this session (2026-06-12)
- Unified worldview locked (4 pillars + agnostic-but-pointed stance + two movements) across the
  `SERIES_BIBLE.md`, `trigunai-content-strategy` skill, and CEO OS.
- Ep 1 (v1 static + v2 animated) and Ep 2 (animated) rendered end-to-end; `worldview.html` dashboard.
- `FLOW_ART_METHOD.md` — Deepak's flow technique captured + mapped to the framework.
- Staged audio-gated pipeline + RAM-disk render fix codified in `production-video-trigunai`.
- CEO tooling: `ceo_work_scan.py` (work scanner), `checkpoint.sh` (one-command git checkpoint +
  skill mirror), `skills/` mirrored into repo, git initialized (14 checkpoints).
- Business model researched (income stack, drop Udemy, live cohorts, AI-literacy tailwind).

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
