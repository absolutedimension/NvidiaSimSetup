# TrigunAI Studio — Product Requirements Document

> **One-liner:** An AI-powered platform that turns mocap data into cinematic drone footage
> and production-ready USD/GLB scenes — powered by Claude agents orchestrating Isaac Sim,
> OVRTX rendering, and Blender on GPU cloud infrastructure.

**Author:** Deepak Kumar Rai, TrigunAI Innovations
**Date:** 2026-05-24
**Status:** Draft v1

---

## 1. Problem

Creating cinematic 3D content today requires:
- A simulation engineer to set up Isaac Sim environments
- A cinematographer to design camera paths
- A VFX artist to render and composite
- A Unity developer to integrate into VR
- Weeks of back-and-forth between all of them

**TrigunAI Studio collapses this into one API call.** Upload your mocap or scene description,
get back a rendered MP4, an animated GLB, or a trained drone policy — in minutes, not weeks.

---

## 2. Users

### Phase 1: Internal (Deepak + Avinash)
- Replace the current manual SSH + script workflow
- Dashboard instead of terminal commands
- Same EC2 backend, just wrapped in a web UI

### Phase 2: Closed Beta (5-10 users)
- VR/XR developers who need cinematic camera paths for their Quest apps
- Indie game devs who want AI-generated USD scenes with PBR materials
- Motion capture studios that want instant visualization of their captures

### Phase 3: Public SaaS
- Anyone who wants AI-powered 3D content creation
- API customers who want to embed this in their own products

---

## 3. Product Capabilities

### Capability 1: Mocap → Cinematic Video
**User flow:** Upload pose.bin + meta.json → see stick-figure preview → choose camera style
(orbital / tracking / cinematic AI) → get rendered MP4

**Backend:** parse_pose_bin.py → bake_dancer_usda.py → OVRTX render → ffmpeg → MP4

### Capability 2: Scene Builder
**User flow:** Describe a scene in text ("a warehouse with a dancing humanoid and dramatic
lighting") → AI agent builds the USD → renders preview → user tweaks → download GLB/USDA

**Backend:** Claude agent generates USD scene graph → OVRTX renders → Blender converts to GLB

### Capability 3: Cinematographer Training
**User flow:** Upload 5+ mocap sessions → system trains a PPO drone policy → returns 10
sample MP4s for user voting → exports winning policy as GLB (VR) + ONNX (hardware)

**Backend:** The full A1-A6 pipeline, automated with human-in-the-loop approval gates

### Capability 4: Asset Enrichment (existing NVIDIA agents)
**User flow:** Upload a USD/GLB → choose: add materials / add physics / generate textures
→ get enriched asset back

**Backend:** NVIDIA Content Agents (Material, Physics, Texture) already running on EC2

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│                                                              │
│   React + Vite + TailwindCSS                                │
│   ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐      │
│   │ Mocap   │ │ Scene    │ │ Training │ │ Asset     │      │
│   │ Studio  │ │ Builder  │ │ Lab      │ │ Enricher  │      │
│   └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘      │
│        └────────────┴────────────┴─────────────┘             │
│                          │ REST + WebSocket                  │
│   Host: Vercel (free) or EC2 nginx                          │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                    API GATEWAY                                │
│                                                              │
│   FastAPI (Python 3.11)                                     │
│   ├── POST /api/jobs              (create a job)            │
│   ├── GET  /api/jobs/{id}         (poll status)             │
│   ├── GET  /api/jobs/{id}/stream  (SSE live updates)        │
│   ├── POST /api/jobs/{id}/approve (subjective gate)         │
│   ├── GET  /api/artifacts/{id}    (download result)         │
│   ├── POST /api/chat              (free-form agent chat)    │
│   └── GET  /api/health            (system status)           │
│                                                              │
│   Auth: API key (Phase 1) → Supabase JWT (Phase 3)         │
│   Host: EC2 (port 9000)                                     │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                  AGENT ORCHESTRATOR                          │
│                                                              │
│   3 Claude agents (via Anthropic API)                       │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│   │ Orchestrator │ │ Training     │ │ VR Agent     │       │
│   │ Agent        │ │ Agent        │ │              │       │
│   │              │ │              │ │ (generates   │       │
│   │ Routes jobs  │ │ Runs tools:  │ │  handoff     │       │
│   │ to the right │ │ - ssh_ec2    │ │  docs for    │       │
│   │ agent, tracks│ │ - render     │ │  Unity side) │       │
│   │ phase gates  │ │ - parse      │ │              │       │
│   └──────────────┘ │ - train      │ └──────────────┘       │
│                     │ - convert    │                         │
│                     └──────────────┘                         │
│                                                              │
│   Each agent = system prompt (SKILL.md) + tools + loop      │
│   Anthropic API: Claude Sonnet for speed, Opus for complex  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                GPU COMPUTE LAYER (existing EC2)              │
│                                                              │
│   TrigunAI-Omniverse (g5.2xlarge, A10G 24GB)               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│   │ OVRTX    │ │ Material │ │ Physics  │ │ Texture  │     │
│   │ :8001    │ │ Agent    │ │ Agent    │ │ Agent    │     │
│   │          │ │ :8000    │ │ :8002    │ │ :8004    │     │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│   ┌──────────┐ ┌──────────┐ ┌──────────────────────┐      │
│   │ isaaclab │ │ Blender  │ │ LiteLLM :4000        │      │
│   │ container│ │ 4.5 LTS  │ │ (Azure OpenAI proxy) │      │
│   └──────────┘ └──────────┘ └──────────────────────┘      │
│                                                              │
│   ALL EXISTING — no new infra needed for Phase 1            │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Data Model

### Job

```json
{
  "id": "job_abc123",
  "type": "mocap_render | scene_build | train_policy | enrich_asset",
  "status": "queued | running | awaiting_approval | completed | failed",
  "agent": "orchestrator | training | vr",
  "created_at": "2026-05-24T10:00:00Z",
  "updated_at": "2026-05-24T10:05:00Z",
  "input": {
    "files": ["pose.bin", "meta.json"],
    "params": {"duration": 25, "fps": 30, "camera": "orbital"}
  },
  "output": {
    "artifacts": [
      {"name": "dancer_orbital.mp4", "size_mb": 2.1, "url": "/api/artifacts/art_xyz"}
    ],
    "agent_log": ["Parsed 3984 frames...", "Baking USDA...", "Rendering batch 1/15..."]
  },
  "approval_gate": {
    "required": true,
    "prompt": "Does this look like a drone filming a dancer?",
    "response": null
  },
  "cost_tokens": 15420,
  "user_id": "user_deepak"
}
```

### Artifact

```json
{
  "id": "art_xyz",
  "job_id": "job_abc123",
  "filename": "dancer_orbital_v1.mp4",
  "format": "video/mp4",
  "size_bytes": 2200000,
  "storage_path": "/home/ubuntu/studio_artifacts/art_xyz/dancer_orbital_v1.mp4",
  "download_url": "/api/artifacts/art_xyz",
  "created_at": "2026-05-24T10:05:00Z"
}
```

---

## 6. API Design

### Create a job

```
POST /api/jobs
Content-Type: multipart/form-data

{
  "type": "mocap_render",
  "params": {
    "duration": 25,
    "fps": 30,
    "camera_style": "orbital",
    "resolution": "800x450"
  },
  "files": [pose.bin, meta.json]
}

→ 201 Created
{
  "id": "job_abc123",
  "status": "queued",
  "stream_url": "/api/jobs/job_abc123/stream"
}
```

### Stream job progress (SSE)

```
GET /api/jobs/job_abc123/stream
Accept: text/event-stream

data: {"type": "log", "message": "Parsed 3984 frames @ 60Hz"}
data: {"type": "log", "message": "Baking USDA: 750 frames @ 30fps"}
data: {"type": "progress", "percent": 45, "step": "Rendering batch 3/15"}
data: {"type": "approval_needed", "prompt": "Does this look like a drone filming a dancer?", "preview_url": "/api/artifacts/preview_abc"}
data: {"type": "completed", "artifacts": [...]}
```

### Approve a gate

```
POST /api/jobs/job_abc123/approve
{
  "approved": true,
  "feedback": "Looks great, move to A3"
}
```

### Chat with an agent

```
POST /api/chat
{
  "agent": "training",
  "message": "What phase are we in?",
  "job_context": "job_abc123"
}

→ 200 OK
{
  "response": "We're in Phase A2. The 25s orbital baseline USDA is baked...",
  "agent": "training"
}
```

---

## 7. Agent Tool Definitions

Each Claude agent gets a set of tools it can call. The backend executes them.

### Training Agent Tools

| Tool | Input | What it does |
|---|---|---|
| `ssh_ec2` | command: string | Runs a bash command on EC2 via SSH |
| `parse_mocap` | session_path: string | Runs parse_pose_bin.py, returns frame count + body positions |
| `bake_usda` | session_path, duration, fps, camera_style | Runs bake_dancer_usda.py, returns USDA path |
| `render_mp4` | usda_path, width, height | Runs render_dancer_mp4.py via OVRTX, returns MP4 path |
| `convert_glb` | usda_path, animated: bool | Runs Blender usd_to_glb.py, returns GLB path |
| `start_training` | config: dict | Launches Isaac Lab PPO training in isaaclab container |
| `check_training` | — | Checks training progress (latest checkpoint, reward curve) |
| `export_onnx` | checkpoint_path | Distills PyTorch policy to ONNX |
| `read_file` | path: string | Reads a file from EC2 or local |
| `write_file` | path, content | Writes a file |
| `download_artifact` | ec2_path | SCPs file from EC2 to artifact storage |

### Orchestrator Tools

| Tool | Input | What it does |
|---|---|---|
| `check_phase_status` | — | Returns current phase + gate checklist |
| `generate_handoff` | direction: "training_to_vr" or "vr_to_training", version: int | Generates handoff doc from template |
| `list_artifacts` | version: int | Lists all artifacts for a training version |
| `update_phase` | phase: string, status: string | Updates phase status in status.json |

### VR Agent Tools

| Tool | Input | What it does |
|---|---|---|
| `generate_integration_guide` | glb_path, version | Generates Unity integration steps |
| `generate_feedback_template` | version | Generates structured VR test feedback template |
| `list_mocap_sessions` | — | Lists available mocap sessions with metadata |

---

## 8. Security

| Concern | Solution |
|---|---|
| API key exposure | Server-side only; frontend never sees Anthropic key |
| EC2 SSH access | Agent tools use a locked-down SSH key; no root |
| File access | Sandboxed to `/home/ubuntu/studio_artifacts/` |
| User isolation (Phase 3) | Job directories per user; no cross-user access |
| Rate limiting | 10 jobs/hour per user (Phase 1: unlimited for internal) |
| Cost control | Token budget per job; kill after 100K tokens |

---

## 9. Cost Model

### Per-job cost estimate

| Job type | Claude tokens | EC2 time | Total cost |
|---|---|---|---|
| Mocap → MP4 render | ~20K tokens (~$0.05) | ~5 min ($0.08) | **~$0.13** |
| Scene build | ~50K tokens (~$0.15) | ~10 min ($0.17) | **~$0.32** |
| Full training pipeline | ~200K tokens (~$0.60) | ~2 hr ($2.00) | **~$2.60** |
| Asset enrichment | ~30K tokens (~$0.09) | ~5 min ($0.08) | **~$0.17** |

### Monthly infrastructure

| Component | Cost |
|---|---|
| EC2 g5.2xlarge (running 8hr/day) | ~$240/mo |
| Anthropic API (internal use) | ~$20/mo |
| Vercel frontend (free tier) | $0 |
| Supabase auth (free tier) | $0 |
| **Total Phase 1** | **~$260/mo** |

### Pricing (Phase 3)

| Tier | Price | Includes |
|---|---|---|
| Free | $0 | 3 renders/month, 720p |
| Pro | $29/mo | 50 renders, 1080p, training |
| Enterprise | Custom | API access, priority GPU |

---

## 10. Implementation Plan

### Sprint 1: API Backend (this week)
- [ ] FastAPI server with job queue
- [ ] Claude agent loop with tool execution
- [ ] Training Agent with ssh_ec2, parse_mocap, render_mp4 tools
- [ ] Orchestrator Agent with phase tracking
- [ ] Artifact storage + download endpoint
- [ ] SSE streaming for job progress
- [ ] Deploy on EC2 port 9000

### Sprint 2: Web Frontend (next week)
- [ ] React + Vite + Tailwind dashboard
- [ ] File upload (drag & drop pose.bin)
- [ ] Job status with live log streaming
- [ ] Artifact preview (video player, 3D viewer)
- [ ] Approval gate UI (approve/reject with feedback)
- [ ] Agent chat panel

### Sprint 3: Polish + Beta (week 3)
- [ ] Supabase auth (email + Google login)
- [ ] User isolation (per-user job directories)
- [ ] Rate limiting + token budgets
- [ ] Error handling + retry logic
- [ ] Landing page + onboarding flow
- [ ] Invite 5 beta users

### Sprint 4: Scale (week 4+)
- [ ] Job queue persistence (SQLite → Postgres)
- [ ] Multiple EC2 instances (auto-scaling)
- [ ] Stripe billing integration
- [ ] API key management for enterprise
- [ ] Usage analytics dashboard

---

## 11. Success Metrics

| Metric | Phase 1 target | Phase 3 target |
|---|---|---|
| Job completion rate | >90% | >95% |
| Mocap → MP4 latency | <10 min | <5 min |
| Render quality (user approval) | >80% first-pass | >90% |
| Monthly active users | 2 (internal) | 50+ |
| API calls/month | ~100 | ~5000 |
| Revenue | $0 | $1K+ MRR |

---

## 12. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| EC2 single point of failure | High | EBS snapshots + launch template for quick recovery |
| Anthropic API cost overrun | Medium | Token budget per job + kill switch |
| OVRTX render timeout | Medium | Batch rendering (already solved) |
| User uploads malicious files | Medium | Sandbox execution + file type validation |
| SSH key compromise | High | Rotate keys quarterly; no root access for agent |

---

*This PRD is the contract between the product vision and the engineering work.
Start with Sprint 1 — the API backend. Everything else builds on top.*
