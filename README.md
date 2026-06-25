# TrigunAI — Drone Sim-to-Policy Pipeline + Agentic Ops Hub

Multi-disciplinary production infrastructure for **TrigunAI Innovations**:

1. **Drone sim-to-policy training** — NVIDIA Isaac Lab on AWS GPU → PPO policy → ONNX export → Meta Quest deployment
2. **Course & content platform** — AI-generated cinematography, narration, and video rendering pipeline
3. **Agentic ops** — daily routines, content agents, marketing automation via Claude Code skills

Built and maintained by [Deepak Kumar](https://github.com/absolutedimension) · NVIDIA Inception Member

---

## System Map

```
┌─────────────────────────────────────────────────────┐
│                  NvidiaSimSetup Hub                  │
├────────────────┬────────────────┬───────────────────┤
│  Robotics      │  Course        │  Agentic Ops      │
│  Pipeline      │  Platform      │                   │
│                │                │                   │
│  Isaac Lab 3.0 │  Cinemato-     │  Claude Code      │
│  PyTorch 2.7   │  graphy        │  Skills           │
│  RL_games 1.6  │  pipeline      │                   │
│  AWS EC2 GPU   │  ffmpeg        │  Content agents   │
│  NICE DCV      │  Blender       │  Marketing        │
│  USD/USDA      │  USD assets    │  pipeline         │
│                │                │                   │
│  → ONNX policy │  → MP4 videos  │  → Daily routines │
│  → Meta Quest  │  → LMS         │  → SEO / outreach │
└────────────────┴────────────────┴───────────────────┘
```

---

## 1. Drone Sim-to-Policy Pipeline

Train a quadrotor navigation policy in simulation, export to ONNX, deploy on device.

### Stack
- **Simulator:** NVIDIA Isaac Lab 3.0 (Isaac Sim 4.5)
- **RL framework:** RL_games 1.6.1 with PPO
- **Hardware:** AWS EC2 `g6e.2xlarge` (NVIDIA L40S GPU), CUDA 12.8, Ubuntu 22.04
- **Remote rendering:** NICE DCV for headless Isaac Sim
- **Export:** PyTorch → ONNX → Meta Quest / edge deployment

### Key files
```
DroneRoboticsTraining/   # Setup guides + onboarding docs
drone_handoff/           # Handoff docs for the training pipeline
drone_demo.usda          # USD scene for quadrotor training
DRONE_PIPELINE_HANDOFF.md
DRONE_TRAINING_STRATEGY.md
DRONE_TIER2_ROADMAP.md
```

### AWS Setup (summary)
```bash
# EC2 instance: g6e.2xlarge, Ubuntu 22.04, CUDA 12.8
# Install Isaac Lab 3.0 + RL_games
pip install torch==2.7.0+cu128 --index-url https://download.pytorch.org/whl/cu128
# Clone Isaac Lab, install in developer mode
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab && ./isaaclab.sh --install
```

See [`DRONE_PIPELINE_HANDOFF.md`](./DRONE_PIPELINE_HANDOFF.md) for full setup.

---

## 2. Course & Content Platform

AI-powered pipeline to author, narrate, and render TrigunAI's video courses.

```
Script (MD) → AI narration (TTS) → Blender/USD scene → ffmpeg composite → MP4
```

### Key directories
```
cinematography/          # Blender-based scene builders
course_assets/           # Raw assets per module
course_scripts/          # Narration scripts (MD)
video-creator/           # ffmpeg composition pipeline
music_pipeline/          # Background music generation
landing-page/            # Course landing pages (Next.js)
lms/                     # LMS backend
```

### Docs
- [`CINEMATOGRAPHY_HANDOFF.md`](./CINEMATOGRAPHY_HANDOFF.md)
- [`COURSE_OUTLINE.md`](./COURSE_OUTLINE.md)
- [`VIDEO_RENDERING.md`](./VIDEO_RENDERING.md)

---

## 3. Agentic Ops

Claude Code skills + daily automation routines that run TrigunAI's operations.

```
skills/              # Claude Code custom skills
daily_routine/       # Daily schedule + task templates
marketing_pipeline/  # Content → SEO → social publish
outreach/            # Student + partner outreach sequences
project_hub/         # Project status tracking
```

Skills are synced to `~/.claude/` via `sync_skills.sh`. Each skill is a self-contained instruction set for a Claude Code agent.

---

## Infrastructure

| Resource | Spec |
|----------|------|
| GPU training | AWS EC2 g6e.2xlarge (L40S, 48GB VRAM) |
| Remote desktop | NICE DCV (headless Isaac Sim rendering) |
| Course hosting | Azure Container Apps |
| Asset pipeline | Blender 4.x + USD (Pixar) |
| CI | GitHub Actions |

---

## Related Projects

| Repo | Connection |
|------|-----------|
| [ShaderStudio](https://github.com/absolutedimension/ShaderStudio) | Production SaaS built on this infrastructure |
| [Blender-Antigravity](https://github.com/absolutedimension/Blender-Antigravity) | VR cinematography pipeline (sister project) |

---

## Author

**Deepak Kumar** — Founder-CTO, TrigunAI Innovations · NVIDIA Inception Member  
[github.com/absolutedimension](https://github.com/absolutedimension) · dkrai.action@gmail.com
