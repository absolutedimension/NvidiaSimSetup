# TrigunAI — Skill Hub System Map

> The whole system on one page: every skill, what it does, how they stack into layers, and
> which machine each drives. Router = **`trigunai-project-hub`** (load first when unsure).
> Interactive version: Artifact "TrigunAI — Skill Hub System Map".
> Source of truth: `skills/trigunai-project-hub/SKILL.md` §A–§C. Generated 2026-07-03.

**At a glance:** 39 skills · 8 layers · 6 machines. Live revenue gate = **Teacher B2B2C PMF test, Day 1 / 21** (0 paid → 1 by Jul 23).

---

## Layer 01 — Command & Strategy  *(the brain: decides & routes, doesn't build)*

| Skill | What it does |
|---|---|
| **trigunai-project-hub** ⭐ | THE router / front door. Any request → the one skill that owns it + the VM/repo it lives on. Also the multi-agent project hub (CEO briefing, artifact registry). |
| **trigunai-ceo** | Founder OS — strategy, the revenue gate, grants/DPIIT, pricing, brand, investor prep, and the "Witness" honesty gate before hard-to-reverse decisions. |
| **maintain-trigunai-system** | Master ops map for every live trigunai.com property — which repo/Azure sub/deploy/verify, what not to break. |
| **trigunai-daily-discipline** | Your daily front door — locks the 5 work blocks, routes each, logs what shipped (streak + gate-days). |
| **trigunai-orchestrator** | Cross Mac↔Windows handoffs + mission phase gates for the sim/VR pipeline. |
| **trigunai-executor** | Autonomously executes a locked sprint/ADR end-to-end. |
| **trigunai-bizdev** | Business development & partnerships. |

## Layer 02 — Autonomous Engines  *(the self-running boxes — where revenue moves today)*

| Skill | What it does | Status |
|---|---|---|
| **content-marketing-bot** | Master ops map for the OpenClaw box: daily content engine + teacher automation + Maya voice-calling + render farm. | 🟢 Live |
| **teacher-outreach-engine** | Source exam-prep teachers, call, log every call, track the 21-day PMF test. **The live gate.** | 🟡 GATE |
| **content-daily-engine** | Resolves today's content slot → emotion OS → render → auto-post IG/FB/YouTube w/ CTA. | 🟢 Live |

## Layer 03 — Live Product & Web  *(the trigunai.com surfaces)*

| Skill | What it does |
|---|---|
| **maintain-trigunai-system** | (also Layer 01) How to change LMS courses, lessons, Razorpay billing, Acharya bridge, pricing, SEO — safely. |
| **add-trigunai-course** | Adds a new course end-to-end: tutor concept bank + LMS catalog + detail page. No bridge restart. |
| **aipm-study** | AI Product Management study companion (course content). |

## Layer 04 — Content Creation  *(make the asset)*

| Skill | What it does |
|---|---|
| **content-marketing-emotion-connect** | The emotional OS for ALL marketing creative — brand feeling, buyer arc, hook bank, guardrails. **Run first.** |
| **trigunai-content-strategy** | Episode catalog & series strategy ("AI is the Universal Mind"). |
| **video-script-writer-trigunai** | Topic/module → scene-segmented, TTS-tuned script + visual direction (feeds production). |
| **production-video-trigunai** | Script → finished narrated MP4 (shader bg, motion graphics, lip-sync presenter, music) on EC2 GPU. |
| **talking-avatar-trigunai** | Photo (or AI-generated gpt-image face) + text/audio → lively cinematic lip-sync/talking-head MP4 (SadTalker + Azure voice) on the T4 box. Also lives as an OpenClaw Telegram bot skill. |
| **faceless-explainer-trigunai** | Faceless explainer videos. |
| **reel-shorts-video-trigunai** | Reel/Shorts preset over the video engine. |

## Layer 05 — Music & FlowArt  *(sound → visualizer, Movement II)*

| Skill | What it does |
|---|---|
| **track-studio-trigunai** | Step-by-step interactive track builder from scratch (design each element → rhythm → merge → vocals → master). |
| **learn-dj-style-trigunai** | Reverse-engineer a DJ's arrangement grammar → generative engine (proven on Burmeister, 33 sets). |
| **hypnotic-techno-trigunai** | One-shot hypnotic-techno set (+ optional isochronic tone & shader). |
| **isochronic-deephouse-trigunai** | Deep-house / focus / isochronic sessions. |
| **production-music-trigunai** | Raw music-production engine (ACE-Step + DawDreamer). |
| **shader-reactive-pattern-music** | Track → audio-reactive sacred-geometry shader video → FlowArt uploader. |

## Layer 06 — Distribution & Publish  *(get it in front of people)*

| Skill | What it does |
|---|---|
| **trigunai-marketing** | Multi-channel publisher — email/Telegram/Discord/YouTube in one command. |
| **trigunai-social-reels** | IG + FB Reels via Meta Graph API. |
| **trigunai-youtube** | Umbrella uploader — both YouTube channels (EN + HI). |
| **trigunai-yt-english** | English channel @TrigunAI-Innovations. |
| **trigunai-yt-hindi** | Hindi channel @trigunai-हिंदी. |
| **trigunai-yt-flowart** | FlowArt music channel @trigunflowart. |

## Layer 07 — Engineering & Simulation  *(the deep-tech IP — feeds fundraise, not this week's revenue)*

| Skill | What it does | Status |
|---|---|---|
| **trigunai-dev** | Default full-stack dev — anything in the repo not clearly one domain. | Default |
| **trigunai-training** | Isaac Sim/Lab RL training, reward design, OVRTX render, EC2. | 🟡 On-demand |
| **trigunai-drone-pipeline** | Drone A→B: PPO train → export → render → VLM gate → animated GLB. | ⏸ Paused |
| **trigunai-lower-body-physics** | Full-body motion from Quest upper-body via Isaac AMP. | ⏸ Paused |
| **trigunai-vr** | VR/Unity/Quest 3 on the Gurulok app (Meta alpha). |  |
| **trigunai-lighting** | Intelligent lighting design (content production). |  |
| **trigunai-stage** | Stage / scene design system. |  |
| **trigunai-table-read-director** | Table-read / performance direction. |  |
| **add-openclaw-skill** | Scaffolds a new skill onto the autonomous OpenClaw box. |  |

---

## Layer 08 — Physical Topology  *(where every system actually lives)*

| System | Host | Region · Sub | Repo (edit here) | Owning skill |
|---|---|---|---|---|
| Acharya WhatsApp bridge | Gurukul VM `20.219.2.53` | Central India · gurukul-prod | `agentic_cohort/` | maintain-trigunai-system |
| Maya voice-calling | same Gurukul VM | Central India | `azure_migration/openclaw-studio/` | content-marketing-bot |
| Content + teacher engines | OpenClaw box `20.120.226.5` | westus2 · hearmenow | `azure_migration/openclaw-studio/` | content-marketing-bot |
| LMS / Acharya site | Azure Container App `lms` | registry trigunaicr | `lms/` | maintain-trigunai-system |
| Public sites (trigunai · studio · learn) | Azure Container App `frontend` | triguai-prod | **`ShaderStudio/`** (not NvidiaSimSetup) | maintain-trigunai-system |
| Render / training farm | EC2 A10G `34.192.145.204` | AWS us-east-1 | `NvidiaSimSetup/` | trigunai-training |

⚠️ **Traps:** the Gurukul VM hosts BOTH Acharya and Maya — never break `/webhook`→Acharya when touching Maya. Public landing lives in **ShaderStudio**, not `NvidiaSimSetup/landing-page/` (stale). LMS edits never go in ShaderStudio and vice-versa.

---

## How a request flows  *(router → owner → machine)*

```
Revenue :  "who do I call today"   → project-hub → teacher-outreach-engine → OpenClaw box + Maya
Content :  "make a reel"           → content-daily-engine → emotion-connect → production-video → EC2 GPU → yt/social
Product :  "add a new course"      → project-hub → add-trigunai-course → LMS container + Acharya bridge
```

**Check live status anytime:** `bash skills/trigunai-project-hub/hub_status.sh` (5 sites + Gurukul VM + OpenClaw box, ~15s).
