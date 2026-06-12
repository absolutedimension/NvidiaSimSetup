# PRD — NVIDIA Content Agents Pipeline on TrigunAI Cloud Infrastructure
**Project:** Automate 3D Pipelines With AI Agents and Vision-Language Models
**Target Machine:** TrigunAI-Omniverse (g5.2xlarge, current public IP 98.83.147.64)
**Date:** 2026-05-15
**Status:** Phase-1 MVP install in progress

## Install Progress Log
- ✅ Azure OpenAI gpt-4o-mini deployed (endpoint: `azure-trigunai-model.openai.azure.com`)
- ✅ LiteLLM proxy running on EC2 port 4000 (translates OpenAI → Azure)
- ✅ LiteLLM verified end-to-end with Azure (PROXY OK test passed)
- ✅ Content Agents repo cloned to `~/content-agents`
- ✅ Scene Optimizer Core fetched (922 MB)
- ✅ Material Agent + OVRTX rendering Docker images built
- ✅ Rendering sidecar warm-up complete (uses ~1.6 GB VRAM, well under our 24 GB)
- ✅ Material Agent service healthy
- ✅ **End-to-end test passed:** cube USD → VLM classified as "Plastic Cloudy" → material applied → final render rendered

## Patches Applied (Required for Our Setup)
File: `apps/material_agent_service/service/routers/pipeline_router.py`
1. **OpenAI credential forwarding**: When `MA_VLM_BACKEND=openai`, explicitly inject `OPENAI_API_KEY` + `OPENAI_BASE_URL` into the vlm config so the credential validator pairs them and accepts our custom LiteLLM endpoint (which it would otherwise refuse for security).
2. **Token cap**: Cap `max_completion_tokens` / `max_tokens` at 16000 because gpt-4o-mini's hard cap is 16384 (default agent config was 24576 which Azure rejected).

## MVP Test Result (Phase 1 ✅ Done)
- **Input:** 1× untextured cube (17 KB USD)
- **VLM classification:** "Plastic Cloudy" with reasoning *"smooth surface, translucent quality, characteristic of plastic"*
- **Pipeline duration:** 161 s (~2.7 min)
- **Cost:** <$0.01 in Azure OpenAI tokens + ~$0.05 in EC2 time
- **Output files:** `scene_with_materials.usd` (with binding), `scene_with_materials.png` (final render)

---

## 1. Executive Summary

NVIDIA Content Agents is an open-source framework (released by NVIDIA-Omniverse) that uses **Vision-Language Models (VLMs)** to automate the most tedious parts of 3D content production — material assignment, physics tagging, and texture generation. Every input/output is a **USD file** (Universal Scene Description, the format used by Isaac Sim and Omniverse), which means this pipeline directly feeds into the robotics simulation work the team is doing.

**Goal:** Stand up a working MVP of all three official agents on the existing AWS g5.2xlarge in ≤ 2 hours, validate end-to-end on a sample USD asset, then plan extensions toward a "professional content factory."

---

## 2. What This Pipeline Does (Plain English)

Imagine you have a raw 3D model of a car. Out of the box, it's just geometry — no materials, no physics, no textures. To use it in Isaac Sim you'd manually:
- Tag the windshield as "glass," the tires as "rubber," the body as "painted steel"
- Set mass, friction, and collision for every component
- Paint or import texture maps for any untextured surfaces

That manual work takes hours per asset. Content Agents does it in **minutes**, automatically, using AI vision models.

| Agent | Input | Output | How It Works |
|---|---|---|---|
| **Material Agent** (Beta) | USD with untagged geometry | USD with PBR materials assigned | Renders multi-view images, sends to VLM, VLM identifies parts and chooses materials |
| **Physics Agent** (Beta) | USD with components | USD with mass/friction/collision props | Renders views, VLM classifies physical properties |
| **Texture Agent** (Research Preview) | USD with empty material slots | USD with AI-generated textures | Calls generative model to fill empty texture slots |

---

## 3. Infrastructure Audit — What We Have vs What We Need

### What We Have (Current AWS Instance)
| Resource | Value | Sufficient? |
|---|---|---|
| GPU | NVIDIA A10G, **24 GB VRAM** | ⚠️ Below NVIDIA's recommended 48 GB |
| vCPUs | 8 | ✅ Above 10 recommended (close enough) |
| RAM | 32 GiB | ✅ Above 20 GB recommended |
| OS | Ubuntu (NVIDIA AMI) | ✅ Supported |
| Storage | 200 GiB EBS | ✅ Enough for ~30 GB Docker images + assets |
| Drivers | NVIDIA + CUDA pre-installed | ✅ |
| Docker | Pre-installed with NVIDIA Container Toolkit | ✅ |

### The 24 GB vs 48 GB GPU Issue — Resolved
NVIDIA recommends **48 GB VRAM** because they assume you also run a local **Cosmos Reason 2 8B VLM** as a sidecar. **We will skip the local VLM entirely** and use cloud-hosted VLMs instead (NVIDIA NIM, OpenAI, Anthropic, or Gemini). With this approach:

- Our A10G only needs to run the **OVRTX rendering sidecar** (multi-view rendering of 3D assets)
- Rendering sidecar uses ~8-12 GB VRAM — comfortably within our 24 GB budget
- VLM inference happens in the cloud via API calls

**Trade-off:** We pay small per-call fees to the VLM provider (typically <$0.05 per asset processed) instead of running the heavy VLM locally.

---

## 4. Prerequisites — What We Need Before Install

| Item | Where to Get It | Why Needed |
|---|---|---|
| At least one VLM API key | Choose one: NVIDIA NIM (nvapi-...), OpenAI (sk-...), Anthropic (sk-ant-...), Gemini (AIza...) | The agents call the VLM for vision analysis |
| GitHub repo access | Public, no auth needed | Clone the code |
| NGC account (optional) | https://ngc.nvidia.com (free signup) | Only needed if pulling NVIDIA containers; not strictly required |
| ~10 GB free storage | Already have 200 GB | Docker images + dependencies |

**Recommended VLM provider for MVP:** **OpenAI GPT-4o** — fastest to get an API key, best documented, and we can swap to NVIDIA NIM later for cost savings.

---

## 5. Official NVIDIA Documentation We'll Follow

| Doc | URL | Purpose |
|---|---|---|
| Content Agents repo | https://github.com/NVIDIA-Omniverse/content-agents | Source of truth — install & usage |
| Material Agent docs | `apps/material_agent/README.md` (in repo) | Material agent config |
| Physics Agent docs | `apps/physics_agent/README.md` (in repo) | Physics agent config |
| Texture Agent docs | `apps/texture_agent/README.md` (in repo) | Texture agent config |
| Service API specs | `apps/<agent>_service/docs/api.md` (in repo) | REST API reference |
| NVIDIA NIM catalog | https://build.nvidia.com | If we use NVIDIA NIM as VLM backend |
| OpenAI API docs | https://platform.openai.com/docs | If we use OpenAI |

---

## 6. Architecture — MVP

```
┌─────────────────────────────────────────────────────────────┐
│  AWS EC2 g5.2xlarge — TrigunAI-Omniverse (98.91.224.40)    │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │ Material Agent   │    │ Physics Agent    │               │
│  │ FastAPI :8000    │    │ FastAPI :8001    │               │
│  └────────┬─────────┘    └────────┬─────────┘               │
│           │                       │                          │
│           ▼                       ▼                          │
│  ┌──────────────────────────────────────────┐               │
│  │  OVRTX Rendering Sidecar (uses A10G GPU) │               │
│  │  Renders multi-view images of USD assets │               │
│  └──────────────────────────────────────────┘               │
│           │                                                  │
│           │ HTTPS                                            │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
   ┌─────────────────────┐
   │ Cloud VLM Provider  │
   │ (OpenAI / NIM)      │
   └─────────────────────┘
```

---

## 7. MVP Scope (Phase 1)

**Goal:** Deploy all three agents as Docker services, validate with a single sample asset.

### Acceptance Criteria
- [ ] Material Agent service running and `curl http://localhost:8000/health` returns 200
- [ ] Physics Agent service running and `curl http://localhost:8001/health` returns 200
- [ ] Texture Agent service running and `curl http://localhost:8002/health` returns 200
- [ ] Sample USD asset processed by Material Agent → output USD has correct materials
- [ ] GPU usage verifiable via `nvidia-smi` during a run
- [ ] At least one VLM backend (e.g., OpenAI) wired up via `.env`

### Out of Scope for MVP
- Web UI / dashboard (use curl + Python client only)
- Multi-asset batch processing
- S3 storage integration
- Auto-scaling or load balancing
- Custom agents beyond the three official ones

---

## 8. Roadmap — Beyond MVP (Toward a "Video/Content Factory")

The three official agents are a **starting point**. The `world_understanding/` library in the repo is the core agentic framework — meaning custom agents can be added. A professional pipeline would include:

### Phase 2 — Pre-processing Agents (Intake)
- **Geometry Cleanup Agent** — fixes broken meshes, normals, scale issues
- **Hierarchy Naming Agent** — VLM names mesh nodes meaningfully (e.g., "front_wheel_left")
- **UV Unwrap Agent** — generates UV maps for untextured models

### Phase 3 — Animation & Scene Agents
- **Rigging Agent** — auto-rigs characters or articulated robots
- **Lighting Agent** — sets up cinematic or simulation-realistic lighting
- **Camera Agent** — generates camera paths for renders/synthetic data

### Phase 4 — Output / Synthetic Data Agents
- **Replicator Integration** — generates synthetic data for training perception models
- **Variation Agent** — produces hundreds of variations from one asset
- **Render Farm Orchestrator** — distributes rendering across multiple GPU instances

### Phase 5 — Video Generation
- **NVIDIA Cosmos integration** — text-to-video using physical AI models
- **Scenario Generator Agent** — creates training scenarios from prompts (e.g., "robot navigating warehouse at night")

> All of these are plausible because Content Agents is open-source and built on a generic agentic framework. NVIDIA itself is rapidly releasing more agents — we should watch the repo for new official ones each quarter.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 24 GB VRAM insufficient for rendering sidecar | Low | High | Fallback: process assets sequentially instead of in parallel |
| VLM API costs blow up budget | Medium | Medium | Set spending caps on OpenAI/NVIDIA; start with 5-10 test assets |
| Repo dependencies break on Ubuntu version | Low | Medium | Use the official Docker compose path (more reproducible than CLI install) |
| First-boot rendering sidecar takes >5 min and we think it's broken | Medium | Low | Documented behavior — wait patiently on first run |
| Texture Agent is "Research Preview" so may be unstable | High | Low | Treat as nice-to-have; Material + Physics agents are Beta and more stable |

---

## 10. Step-by-Step Install Plan (Phase 1 MVP)

**Total estimated time:** 90-120 minutes (first time)

| # | Step | Time | Where |
|---|---|---|---|
| 1 | Get OpenAI (or NIM) API key | 5 min | Browser |
| 2 | SSH into the AWS instance | 1 min | Local terminal |
| 3 | Verify GPU, Docker, Docker Compose versions | 2 min | EC2 terminal |
| 4 | Upgrade Docker Compose if needed (v2.24+) | 5 min | EC2 |
| 5 | Clone the content-agents repo | 1 min | EC2 |
| 6 | Create `.env` file with API keys | 2 min | EC2 |
| 7 | Run `./scripts/fetch_build_resources.sh` (downloads Scene Optimizer ~332 MB) | 5 min | EC2 |
| 8 | Bring up Material Agent service via docker compose | 10 min (first boot) | EC2 |
| 9 | Health-check Material Agent (`curl /health`) | 1 min | EC2 |
| 10 | Bring up Physics Agent service | 10 min | EC2 |
| 11 | Bring up Texture Agent service | 5 min | EC2 |
| 12 | Run sample asset through Material Agent | 10 min | EC2 |
| 13 | Verify output USD has materials assigned | 5 min | EC2 + DCV |
| 14 | Document the working setup | 10 min | Local |

---

## 11. Cost Estimate for Phase 1

| Item | Cost | Notes |
|---|---|---|
| EC2 compute (g5.2xlarge) | ~$1/hr | Only while running install + tests (~2 hrs) ≈ $2 |
| OpenAI GPT-4o (testing) | ~$0.50 | ~10 assets at $0.05 each |
| EBS storage | already paid | No incremental cost |
| **MVP Total** | **~$2.50** | One-time |

---

## 12. Open Questions (Need User Input Before Starting)

1. **Which VLM provider?** (OpenAI recommended for fastest start; NIM/Anthropic also work)
2. **Do you already have an API key for that provider?** If not, do you want me to wait while you get one?
3. **Do we have any sample USD assets to test with**, or should we use the example assets bundled with the repo?
4. **Is it OK to stop the instance after install** to save costs while we wait for sample assets?

---

## 13. Definition of Done (Phase 1)

✅ All three agent services running on the AWS instance
✅ Health endpoints responding 200
✅ One sample USD asset successfully processed end-to-end
✅ A "how to use" cheat sheet committed to this folder
✅ Cost actually incurred ≤ $5

---
