# NvidiaSimSetup — Project Handoff (TrigunAI)

> **Read this first.** Everything a new session needs to continue. Covers AWS setup, NVIDIA Content Agents, Azure OpenAI bridge, React Asset Studio, USD→MP4 video pipeline, and WebXR Quest 3 showcase.

---

## 🧭 Session pointer (start here based on your focus)

There are now **four parallel workstreams** living in this repo. New sessions should pick ONE and stick to it:

| If your session is about… | Read this file as your sole entry point |
|---|---|
| 🛸 **Drone training** (Crazyflie A→B in city, GLB to WebXR) | **`DRONE_CLAUDE.md`** (self-contained handoff) |
| 🤖 **Robotics teleoperation B2B** (Quest 3 → robot, the NEW main bet from 2026-05-21) | **`ROBOTICS_CLAUDE.md`** (self-contained handoff) |
| 🦿 **Lower body physics prediction** (Quest upper body → full body via Isaac AMP) | **`lower_body_physics/SESSION_LOWER_BODY.md`** + skill `trigunai-lower-body-physics` |
| 💃 **Music → character animation** (dance, AMP, Daphne, Phase 3) — **PAUSED 2026-05-21** | **`DANCE_CLAUDE.md`** — paused, resumable, do NOT discard |
| 🎬 **Video rendering** (Blender EEVEE/Cycles, OVRTX, ffmpeg) | **`VIDEO_RENDERING.md`** (master reference for all video work) |
| 🏗️ Shared infrastructure (EC2, container, Content Agents, WebXR app) | This file §2–§16 |

The workstreams share infrastructure (same EC2, same `isaaclab` container, same WebXR app) but the **code paths are isolated** — drone code at `/workspace/isaaclab/.../quadcopter_city_a2b/`, dance code at `/workspace/isaaclab/.../humanoid_amp/`, robotics teleop is mostly a new layer above all of these (Quest app + PC bridge + URDF retargeting + ROS 2 / Isaac Lab integration). Edits in one should not affect the others.

**Current active session focus (2026-05-21): 🤖 Robotics teleoperation.** Dance work is fully checkpointed and resumable but no longer the priority — see `DANCE_CLAUDE.md §19.10` for the pause note and `ROBOTICS_CLAUDE.md` for the pivot strategy.

---

## 1. What this project is

A **TrigunAI content factory** that turns OpenUSD assets into AI-enriched 3D content (materials, physics, textures), renders animation to mp4 video, and serves immersive WebXR demos to Quest 3.

Built across one long session 2026-05-14/15/16. Everything runs on **one AWS EC2 g5.2xlarge** (TrigunAI-Omniverse) plus an **Azure OpenAI** resource for the VLM/LLM/image-gen models.

Three apps in this project tree, all working:

1. **`asset-studio/`** — React + R3F desktop app, drives the 3 NVIDIA agents via the running EC2 backends. Tested end-to-end on cube + Franka + HumanFemale.
2. **`webxr-showcase/`** — React + R3F + `@react-three/xr` Quest 3 WebXR app. Browser-based (no Unity, no APK), served via nginx + Cloudflare Tunnel. Tested on Quest 3 with Ragnarok + IsaacWarehouse.
3. **Video pipeline (CLI)** — Python script that walks USD timeline, calls OVRTX renderer per frame, ffmpeg-encodes to mp4. Demo: 29-frame walking animation rendered end-to-end.

A separate Quest VR Unity project (`GurulokInnerJourney`, already in Meta alpha) has its own `CLAUDE_FlowArtdance_VR.md` and is unrelated to this content factory.

---

## 2. Critical environment

| Item | Value |
|---|---|
| EC2 instance name | **TrigunAI-Omniverse** |
| EC2 instance ID | `i-047ebf759f2386e71` |
| EC2 type | g5.2xlarge (NVIDIA A10G, 24 GB VRAM, 8 vCPUs, 30 GB RAM) |
| EC2 region | us-east-1 |
| EC2 AMI | NVIDIA GPU Cloud VMI Base 2026.4.1 (ami-059e868ce2e616dab) |
| EC2 storage | 200 GiB EBS gp3 + 450 GiB ephemeral NVMe |
| EC2 public IP | **CHANGES on every stop/start** — current was `98.83.147.64`, but verify after any restart |
| EC2 private IP | `172.31.32.216` (stable) |
| SSH key (local Mac) | `~/.ssh/trigunai_key.pem` (also in iCloud at `~/Library/Mobile Documents/com~apple~CloudDocs/TrigunSAI/trigunai_key.pem`) |
| AWS account ID | `253571483681` |
| AWS account name | `TrigunAIAWS` (root: deepak@trigunai.com) |
| IAM user for co-founder | `avinash` (can start/stop EC2; no other perms) |
| Sign-in URL | `https://253571483681.signin.aws.amazon.com/console` |
| Monthly budget | $100 (alerts at 85%, 100%, forecast 100%; email = deepak@trigunai.com, avinash@trigunai.com) |
| Vcpus quota for G/VT | 8 in us-east-1 (only ONE g5.2xlarge in this region; quota increase to 16 was requested but not yet approved) |

**Second instance — Mumbai (Avinash, parallel work):**

| Item | Value |
|---|---|
| Name | TrigunAI-Omniverse-Mumbai |
| Instance ID | `i-05d9104a0d7bf56be` |
| Region | ap-south-1 (Mumbai) — separate quota pool from us-east-1 |
| Public IP | `52.66.243.120` (also changes on stop/start) |
| Private IP | `172.31.7.203` |
| State at session end | Running (Avinash was using; **also bills ~$1/hr** — tell him to stop when not in use) |
| Setup | Completely separate from the us-east-1 instance — fresh, none of our content factory installed |

**Azure OpenAI** (the LLM/VLM/image-gen brain behind everything):

| Item | Value |
|---|---|
| Azure resource (chat) | `azure-trigunai-model` (eastus, region: eastus) |
| gpt-4o-mini endpoint | `https://azure-trigunai-model.openai.azure.com` |
| gpt-4o-mini API version | `2024-12-01-preview` |
| Rate limit | 250 K tokens/min, 2500 req/min |
| Azure resource (image gen) | `deepa-mmq3sitb` (eastus2) — DIFFERENT resource, different key |
| gpt-image-1.5 endpoint | `https://deepa-mmq3sitb-eastus2.cognitiveservices.azure.com` |
| gpt-image-1.5 API version | `2025-04-01-preview` |
| API keys | stored in `~/litellm/config.yaml` on EC2 (rotate periodically in Azure Foundry) |

---

## 3. Running services on EC2 (current state)

Every service is in a Docker container. All start automatically on instance boot.

| Port (host) | Container | Purpose |
|---|---|---|
| 4000 | `litellm-proxy` | Translates OpenAI API → Azure OpenAI (chat + image gen). Master key: `sk-trigunai-master-key-2026` |
| 8000 | `material-agent-service` | NVIDIA Material Agent (assigns PBR materials) |
| 8001 | `ovrtx-rendering-api` | OVRTX renderer for Material Agent (shared with video pipeline) |
| 8002 | `physics-agent-service` | NVIDIA Physics Agent (mass/friction/collision) |
| 8003 | `physics-ovrtx-rendering-api` | OVRTX renderer for Physics Agent |
| 8004 | `texture-agent-service` | NVIDIA Texture Agent (AI-generated PBR textures) |
| 8005 | `scene-composer-service` | TrigunAI Scene Composer (OSM → textured city USD). Wraps `osm_to_usd.py` + `city_add_colliders.py` + `city_enrich_textures.py` behind the same `/pipeline` + `/artifacts/{sid}/*` contract as the NVIDIA agents. Calls the Texture Agent on :8004 internally. Source: `scene_composer_service/` in this repo. |
| 8080 | `nginx` (host) | Serves WebXR app + GLB assets from `/var/www/showcase/` |
| (random) | `cloudflared` (host) | Public HTTPS tunnel — prints a `*.trycloudflare.com` URL. These quick tunnels are **not stable** — re-run `start_tunnel.sh` when they disconnect (a "530" error). |

**Security group** `sg-09c8965b2567b844d`:
- Port 22 (SSH) from anywhere
- Port 8443 (NICE DCV — unused but configured)
- Agent ports (8000/8002/8004) are NOT publicly exposed; reached via SSH tunnel from your Mac

---

## 4. The one-key gotcha you'll keep hitting

**Public IP changes whenever the EC2 stops/starts.** Allocate an Elastic IP and attach it (free while attached, ~$0.005/hr unattached) the next time you start a session, so you stop chasing IPs.

Until then, when you resume:
1. AWS Console → EC2 → Instances → TrigunAI-Omniverse → note current Public IPv4
2. Update `EC2_IP=<new-ip>` env var in any of these scripts:
   - `asset-studio/scripts/ssh_tunnel.sh`
   - `webxr-showcase/scripts/setup_ec2_serving.sh`
   - `webxr-showcase/scripts/deploy_to_ec2.sh`
   - `webxr-showcase/scripts/start_tunnel.sh`

---

## 5. asset-studio — desktop NVIDIA agents UI

React + Vite app on the Mac. Talks to the 3 agent services over an SSH tunnel.

### Each-time workflow

Terminal 1: tunnel to EC2
```bash
cd asset-studio
npm run tunnel    # forwards localhost:8000/8002/8004 to EC2 agents
```

Terminal 2: dev server
```bash
npm run dev       # opens http://localhost:5173
```

Drop a USD into the file picker → pick agent → watch the pipeline run → see the agent's rendered output in the R3F viewport plus a predictions table.

### What's been validated

- **Material Agent** on a 1-prim cube (`test_cube_output.usd`) → classified "Plastic Cloudy", final render in `test_cube_render.png`
- **Material Agent** on the 11-component Franka Panda robot → all 11 prims classified, 8 got material bindings, see `franka_render.png` + `franka_view_link0.png`
- **Physics Agent** on cube → density 1200 kg/m³, mass 60 kg, static friction 0.4, dynamic 0.3, restitution 0.4, classification "plastic"
- **Texture Agent** on cube-with-Plastic-Cloudy-material → 5 PBR maps generated (albedo / normal / roughness / metalness / orm), see `cube_texture_*.png`

---

## 6. NVIDIA Content Agents — the on-EC2 backend

Cloned from https://github.com/NVIDIA-Omniverse/content-agents into `~/content-agents` on EC2.

### The patches we wrote (required — agents won't work otherwise with Azure)

Three `# TRIGUNAI PATCH` blocks in agent source. All address the same problem: NVIDIA's credential validator refuses to forward `OPENAI_API_KEY` to a non-`api.openai.com` endpoint, and our LiteLLM proxy at `172.31.32.216:4000` is a private-IP non-OpenAI endpoint.

| File | What it does |
|---|---|
| `apps/material_agent_service/service/routers/pipeline_router.py` | Injects explicit `api_key` + `base_url` into the openai vlm config, caps `max_completion_tokens` at 16000 (gpt-4o-mini's hard cap is 16384, default agent config was 24576 → Azure rejected) |
| `apps/physics_agent_service/service/routers/pipeline_router.py` | Same fix but injects vlm config into BOTH the top-level config AND each step (`identify_asset` + `predict`), because the Physics agent's `apply_defaults` clobbered top-level vlm |
| `apps/texture_agent/texture_agent/functions/texture_generation.py` | In `_ensure_model()`, adds an `openai` branch that pulls `TA_IMAGE_GEN_API_KEY` + `TA_IMAGE_GEN_BASE_URL` from env and passes them explicitly to `create_image_generation_model` |

Grep `# TRIGUNAI PATCH` to find them in the source. They survive image rebuilds because we edit the source files on the host before `docker compose build`.

### Critical config files

| File | Purpose |
|---|---|
| `~/litellm/config.yaml` | Maps the alias names `gpt-4o-mini` / `gpt-4o` / `gpt-image-1.5` / `gpt-image-1` / `dall-e-3` to actual Azure endpoints + keys |
| `~/litellm/docker-compose.yml` | LiteLLM service definition (port 4000, master key `sk-trigunai-master-key-2026`) |
| `~/content-agents/.env` | Routes all 3 agents' VLM/LLM/image-gen at the LiteLLM proxy (`http://172.31.32.216:4000/v1`) using master key as `OPENAI_API_KEY` |

### Restart commands

Always pass `--env-file ../../.env` — without it Compose substitutes the hardcoded `nim` defaults instead of our openai overrides.

```bash
# Material Agent
cd ~/content-agents/apps/material_agent_service
docker compose --env-file ../../.env up -d

# Physics Agent
cd ~/content-agents/apps/physics_agent_service
docker compose --env-file ../../.env up -d

# Texture Agent
cd ~/content-agents/apps/texture_agent_service
docker compose --env-file ../../.env up -d

# Scene Composer Agent (TrigunAI — not from NVIDIA's repo)
cd ~/NvidiaSimSetup/scene_composer_service
docker compose up -d --build
# No --env-file needed; the composer calls the Texture Agent over loopback
# and uses no Azure credentials itself.
```

The OVRTX rendering sidecars take **~6 min cold start** to flip `gpu_initialized` to true. The agent service won't transition to "healthy" until OVRTX is healthy.

---

## 7. Video pipeline (Phase C MVP)

Script: `/tmp/render_video.py` on EC2. Source: `webxr-showcase/scripts/render_video.py` in this repo (also has identical copy).

```bash
# Example: render Pixar HumanFemale walk cycle (29 frames @ 24 fps)
ssh ubuntu@<EC2_IP>
python3 /tmp/render_video.py \
  --usd /tmp/walk_with_cam.usd \
  --out /tmp/walk.mp4 \
  --start 101 --end 129 --fps 24 \
  --width 512 --height 512 \
  --mode rt2 --samples 30 \
  --camera /World/RenderCam
```

Output: `walk.mp4` (in this repo) — 1.2 sec walk cycle, character horizontal (because flatten lost the original up-axis transform), materials look dark/silhouetted (textures were external PNGs that didn't survive flatten).

### Gotchas the script handles

- **OVRTX URL must be a `data:`, `s3:`, or `https://` scheme** — file paths and private IPs blocked. Script base64-encodes the USD into a data URI like the Material Agent does.
- **OVRTX rejects direction shortcuts like `+x`** — needs an actual UsdGeom.Camera prim path. Script `webxr-showcase/scripts/usd_to_glb.py` is for GLB, NOT video — for video, pre-add a camera to the USD via pxr (see commit that created `walk_with_cam.usd` for the pattern).
- **OVRTX response is nested** — `body["images"][str(frame)][camera_path]["images"]` is the base64 PNG, NOT `body["images"][camera]`.
- **Daemon state pollutes on failed renders** — restart the `ovrtx-rendering-api` container if you see "Failed to remove sensor from scheduler".

### Phase C remaining work

| Open item | Effort |
|---|---|
| Fix camera orientation (character was horizontal in output) | 10 min — adjust `add_cam.py` math |
| Bake/embed textures before flatten | 20 min — extend `usd_to_glb.py`'s sister `flatten_for_render.py` |
| Wire into Asset Studio frontend as a 4th tab | 30 min |
| FBX → USD inbound conversion | 30 min (Blender headless step) |

---

## 8. webxr-showcase — WebXR app for Quest 3

Pure browser. No Unity, no Quest APK, no app store.

### Stack

- React 18 + Vite + TypeScript
- `@react-three/fiber` + `@react-three/drei` + `@react-three/xr` (^6.6)
- Zustand for state
- Asset manifest at `/assets/manifest.json` lists showcases; each has a `glbUrl`
- nginx on EC2 serves the built app + GLB assets from `/var/www/showcase/`
- Cloudflare Tunnel provides public HTTPS (free, quick-tunnel mode; `*.trycloudflare.com`)

### USD → GLB conversion

Blender 4.5 LTS (installed at `/opt/blender45` on EC2, symlinked as `blender45`).

```bash
ssh ubuntu@<EC2_IP> \
  "blender45 --background --python /tmp/usd_to_glb.py -- \
     --input /tmp/showcases/Samples/Showcases/2023_2_1/Ragnarok/Koenigsegg_Ragnarok.usd \
     --output /var/www/showcase/assets/ragnarok.glb \
     --decimate 0.4 --max-texture 1024"
sudo chmod 644 /var/www/showcase/assets/*.glb
```

System Blender 4.0.2 does NOT have USD support — we installed 4.5 LTS from blender.org tarball specifically for USD.

### Each-time workflow

```bash
cd webxr-showcase
./scripts/setup_ec2_serving.sh    # ONE-TIME — configures nginx + installs cloudflared
./scripts/deploy_to_ec2.sh        # build + rsync dist/ to EC2
./scripts/start_tunnel.sh         # prints https://*.trycloudflare.com URL
# Open the URL on Quest Browser → tap "Enter VR"
```

### Showcase content (live on EC2 at `/tmp/showcases/`)

Pulled from `Showcases_Content_NVD@10011.zip` (9.2 GB) — already SCP'd to EC2 then unzipped. Original zip can be deleted from local Mac.

| Showcase | Original USD | Converted GLB | Status |
|---|---|---|---|
| Koenigsegg Ragnarok | 495 MB | `/var/www/showcase/assets/ragnarok.glb` (182 MB) | ✅ Tested on Quest 3. Geometry visible but materials FLAT WHITE — Ragnarok uses NVIDIA MDL shaders, not standard PBR, so Blender's USD importer can't translate textures. |
| Isaac Warehouse | 1.9 GB | `/var/www/showcase/assets/warehouse.glb` (569 MB) | ✅ Built. Has full local PBR PNGs (T_Floor_Albedo, T_GlossyMetal_Normal, T_Ceiling_*, etc.) — should render with proper textures. NOT YET TESTED on Quest — Cloudflare quick tunnel was up briefly with URL `https://sticks-operating-pine-radar.trycloudflare.com` then user stopped EC2 before they could test. **Resume:** start EC2, run `webxr-showcase/scripts/start_tunnel.sh` for a fresh URL, then pick "Isaac Warehouse" from the panel. |
| ConceptCar | 7.7 GB | not converted | ⏳ Would need very aggressive decimation; deferred. Source remains on EC2 at `/tmp/showcases/Samples/Showcases/2023_2_1/ConceptCar/` so it survives EC2 stop (ephemeral /tmp is wiped on stop, so this point is wrong — see §15 below). |

### Frontend gotchas we hit

| Issue | Fix |
|---|---|
| Saw a placeholder cube instead of the model | Bug in `SuspenseCommit` caused React error #185 (infinite update loop). Rewrote `ShowcaseModel.tsx` to set `loaded=true` from inside the loaded `Model` component itself, not a wrapper. |
| Model loaded but invisible (tiny dot) | `scale: 0.01` in manifest was wrong for the asset's USD units. Now `ShowcaseModel` computes a Box3 and auto-fits the longest dimension to 3 m, regardless of source units. |
| Quest 3 leaked passthrough (saw the room) | Canvas was transparent by default. Set `gl={{ alpha: false }}` in the `<Canvas>` props + `Environment preset="warehouse" background` so the skybox fills the 360°. |
| GLB returned HTTP 403 from nginx | File written with `0600` perms (Blender output). Fix is `sudo chmod 644 /var/www/showcase/assets/*.glb` after every conversion. Built into the convert step now. |
| `deploy_to_ec2.sh` wiped the GLBs | `rsync --delete` from `dist/` (which has no .glb) was deleting them on the target. Fixed: deploy script now excludes `*.glb`, `*.gltf`, `*.usd`, `*.usdz`, `*.ktx2`, `*.bin`. |
| Cloudflare quick tunnel disconnected ("530" error) | These are free unmanaged tunnels and disconnect under load. Re-run `start_tunnel.sh` to get a new URL. For production, set up a named cloudflared tunnel with a real domain. |

---

## 9. Cost-so-far snapshot

| Component | Spend during this session |
|---|---|
| EC2 g5.2xlarge | ~6 hours runtime × $1.006/hr ≈ $6 |
| EBS storage (200 GiB) | not yet billed (monthly cycle) |
| Azure gpt-4o-mini tokens | <$0.50 across all agent runs |
| Azure gpt-image-1.5 | ~$0.20 for the cube + 1 test |
| Cloudflare Tunnel | $0 (free quick-tunnel) |
| **Total session** | **~$7** |

Free AWS credit balance was $1000 — comfortably remains. Azure usage in pennies.

---

## 10. Things that still don't work / known issues

| Issue | Status | Severity |
|---|---|---|
| Quota increase 8 → 16 vCPUs requested but not yet approved | Pending AWS review | Blocks Deepak from running his own instance alongside Avinash |
| Cloudflare quick tunnel was disconnected at end of session | Re-run `start_tunnel.sh` | Easy |
| Public IP changes on every EC2 stop/start | Allocate Elastic IP | Easy |
| Ragnarok materials are flat white | NVIDIA MDL not translated by Blender USD importer | Cosmetic — IsaacWarehouse path is the workaround |
| Video pipeline character was horizontal | Camera math bug in `add_cam.py` | 10-min fix |
| Material Agent missed 3 of 11 Franka prims | gpt-4o-mini sometimes returns non-JSON text the parser can't read | Use gpt-4o instead, or harden the response parser |
| `has_required_api_keys` health flag reports `false` for Material Agent | Cosmetic — runtime works (our patch bypasses it), but the health endpoint still says false because the validator code is unchanged | Don't touch — it's working as patched |
| Quest 3 latency on 190 MB Ragnarok GLB | Mobile GPU is loaded | Re-convert with `--decimate 0.15` and `--max-texture 512` if needed |

---

## 11. Resume sequence — when you come back to this project

```bash
# 1. Check EC2 is running, note its current public IP from AWS console
EC2_IP=<current_ip>

# 2. SSH in and verify services
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
  "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Expected: litellm-proxy, material-agent-service, ovrtx-rendering-api,
#           physics-agent-service, physics-ovrtx-rendering-api,
#           texture-agent-service all Up (healthy)

# 3. If any service is missing, restart with --env-file (see §6)

# 4. For asset-studio:
cd asset-studio
EC2_IP=$EC2_IP npm run tunnel    # in one terminal
npm run dev                        # in another

# 5. For webxr-showcase:
cd webxr-showcase
EC2_IP=$EC2_IP ./scripts/deploy_to_ec2.sh
EC2_IP=$EC2_IP ./scripts/start_tunnel.sh    # prints public URL
# Open URL on Quest 3 Browser
```

---

## 12. File tree (this Mac repo)

```
NvidiaSimSetup/
├── CLAUDE.md                                # ← you are here
├── Content_Agents_PRD.md                    # Phase 1 PRD + patches log
├── Content_Agents_Cheatsheet.md             # Operator commands
├── TrigunAI_Cloud_Infrastructure_Report.md  # Developer handoff (for Isaac Sim dev)
├── HumanFemale_flat.usd                     # Flattened Pixar HumanFemale (14 MB)
├── test_cube.usda                           # 1-prim test cube
├── test_cube_output.usd                     # Material Agent output
├── test_cube_render.png                     # Material Agent final render
├── cube_texture_albedo.png                  # Texture Agent output (albedo)
├── cube_texture_normal.png                  # Texture Agent output (normal)
├── cube_texture_roughness.png               # Texture Agent output (roughness)
├── franka_render.png                        # Franka Material Agent final render (black, framing issue)
├── franka_view_link0.png                    # One of 55 multi-view dataset images, with orange highlight
├── walk.mp4                                 # 29-frame walk cycle, Phase C output
├── walk_frame_first.png                     # Frame 1 of walk.mp4
├── walk_frame_middle.png                    # Frame 14 of walk.mp4
│
├── UsdSkelExamples/                         # Pixar UsdSkel sample (HumanFemale + animations)
│   └── HumanFemale/
│
├── asset-studio/                            # React desktop UI for NVIDIA agents
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── README.md
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api/agents.ts
│   │   ├── store/store.ts
│   │   └── components/
│   │       ├── Viewport.tsx
│   │       ├── AgentControls.tsx
│   │       ├── StatusPanel.tsx
│   │       └── ResultsPanel.tsx
│   └── scripts/ssh_tunnel.sh                # SSH port-forward to EC2 agents
│
└── webxr-showcase/                          # React+R3F+@react-three/xr Quest app
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    ├── README.md
    ├── public/
    │   └── assets/manifest.json             # Showcase list (warehouse + ragnarok)
    ├── src/
    │   ├── App.tsx
    │   ├── main.tsx
    │   ├── api/showcases.ts
    │   ├── store/store.ts
    │   └── components/
    │       ├── Scene.tsx
    │       ├── ShowcaseModel.tsx
    │       └── HUD.tsx
    └── scripts/
        ├── usd_to_glb.py                    # Blender headless converter
        ├── setup_ec2_serving.sh             # One-time nginx + cloudflared install
        ├── deploy_to_ec2.sh                 # Build + rsync to EC2 webroot
        └── start_tunnel.sh                  # Cloudflare quick-tunnel → public HTTPS
```

---

## 13. Active roadmap (where to take this next)

### Phase 1 — In-progress polish
- Verify IsaacWarehouse converts with full PBR textures and is walkable on Quest
- Reconvert Ragnarok via our Texture Agent → re-export → see AI-textured car in VR
- Allocate Elastic IP so we stop chasing public IPs
- Add domain + Let's Encrypt for stable HTTPS (Cloudflare quick-tunnel is too flaky for sharing)

### Phase 2 — Asset Studio inside VR
- In-VR spatial menu listing the EC2's `/var/www/showcase/assets/*.glb`
- Voice-command "make this materially X" → triggers Material/Texture agent re-run → live reload
- Reuse the patterns from the existing GurulokInnerJourney Unity project (see its `CLAUDE_FlowArtdance_VR.md`) — same `IJourney` style, same per-asset setup script per showcase

### Phase 3 — Real-time video / streaming
- Animation Render Agent: orchestrate multi-frame USD renders (extend `render_video.py` into a FastAPI service on port 8005)
- Camera path / timeline UI in the Asset Studio
- For high-end demos: NVIDIA CloudXR streaming (the cloud GPU does the rendering; Quest is a thin client). Heavy lift but unlocks full RTX path tracing in VR.

### Phase 4 — Content factory at scale
- Custom agents on top of NVIDIA's `world_understanding/` framework:
  - Geometry Cleanup, Hierarchy Naming, UV Unwrap
  - Rigging, Animation, Lighting
  - Variation Agent (one asset → N variations)
  - NVIDIA Cosmos integration (text → physically-grounded video)
- Asset library on S3
- Multi-user / SaaS-shape: customer drops a USD/FBX → factory processes → returns enriched USD + GLB + textured renders

---

## 14. Adjacent project — Unity Quest app

`GurulokInnerJourney/` (separate Mac/Windows project, not in this tree) is the team's already-shipping Meta alpha VR meditation app, documented at `/Users/deepakkumarrai/Downloads/CLAUDE_FlowArtdance_VR.md`. To wire **this content factory's USD output** into THAT Unity app: add `com.atteneder.gltfast` to its Packages/manifest.json, write a `TrigunAIAssetImporter.cs` editor script (mirror of its existing `StudioSceneImporter.cs`), and an `AIAssetShowcaseJourney` setup script (mirror of `RamChantingJourneySetup.cs`). The bridge format is the same GLB the WebXR app uses.

---

## 15. End-of-session state (2026-05-16) — STOPPED INSTANCE

User stopped the us-east-1 instance to save money before going to sleep.

### What was on disk and **must** be re-created on restart

The EC2 has both EBS (persistent) and `/tmp` (ephemeral — wiped on stop). Track what survives:

| Path | Survives stop? | Notes |
|---|---|---|
| Docker images + containers (`/var/lib/docker/`) | ✅ | All 7 services come back on next start |
| `~/content-agents/` + `~/litellm/` | ✅ | On the EBS root volume |
| `/var/www/showcase/` (nginx webroot + GLBs) | ✅ | EBS root |
| **`/tmp/showcases/`** (the 13 GB unzipped NVIDIA samples) | ❌ | **GONE on stop**; re-extract from `/tmp/showcases.zip` (also gone — re-SCP from local? But user deleted local zip. **WORKFLOW NEEDED: move to EBS before next stop**) |
| `/tmp/walk_with_cam.usd` etc. | ❌ | Per-session intermediate files; regenerate via the scripts |

**Resume-blocking issue:** the 9.2 GB Showcases zip was uploaded to `/tmp/showcases.zip` and unzipped to `/tmp/showcases/`. Both `/tmp` paths are ephemeral. **Before the next stop, move them to EBS** with `mv /tmp/showcases* /home/ubuntu/` (or under `/var/www/showcase/sources/`). User noted they may have deleted the local copy of the zip — if so, the showcases will need to be re-downloaded from NVIDIA marketplace (free) when they're needed again.

### Background processes killed on the Mac

- Vite dev server (was on `localhost:5173`) → killed
- SSH tunnel to EC2 (was forwarding 8000/8002/8004) → killed
- Cloudflared tunnel SSH → killed

### Latest tunnel URL (now dead, for reference)

`https://sticks-operating-pine-radar.trycloudflare.com` — was up briefly with the Isaac Warehouse loaded. Future sessions get a NEW random URL.

### Next-session checklist (in priority order)

1. **Move /tmp/showcases out of ephemeral storage** before doing anything else. One-liner:
   ```bash
   ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
     "[ -d /tmp/showcases ] && mv /tmp/showcases /home/ubuntu/showcases || echo 'already moved or never existed'"
   ```
2. Allocate an **Elastic IP** so we stop chasing IPs after each restart.
3. Test the IsaacWarehouse in Quest (file is at `/var/www/showcase/assets/warehouse.glb`, survives stop).
4. Re-convert Ragnarok via the Texture Agent so it doesn't render flat white.

---

## 16. Avinash's Mumbai instance — don't forget

A second g5.2xlarge spun up in **ap-south-1 (Mumbai)** for Avinash's parallel work — Instance ID `i-05d9104a0d7bf56be`, IP 52.66.243.120 (at last check). **It is unrelated to the content factory in this repo.** It also bills ~$1/hr while Running. Tell Avinash to **stop** it from his IAM login (https://253571483681.signin.aws.amazon.com/console → ap-south-1 region → EC2 → Stop instance) when he's done.

---

## 17. Paused / secondary workstreams — moved out to keep this file lean

The full inline write-ups for the drone and dance pipelines were **moved out of this
file on 2026-07-30** so `CLAUDE.md` isn't re-sent in full on every turn. Nothing was
lost — the content lives in dedicated handoffs. Read the relevant one *only* when your
session is about that workstream (see the §Session pointer table at the top):

| Workstream | Status | Entry point |
|---|---|---|
| 🛸 **Drone training** (Crazyflie A→B, PPO, VLM critic, GLB→WebXR) | secondary | **`DRONE_CLAUDE.md`** (authoritative, 42KB) + **`CLAUDE_DRONE_DETAIL.md`** (the two anchors DRONE_CLAUDE.md lacked: `_debug_vis_callback` patch + §17.5 run sequence) |
| 💃 **Music → character animation** (AMP dance, Daphne, Phase 3) | **PAUSED 2026-05-21** | **`DANCE_CLAUDE.md`** (was §19 here; fully resumable) |
| 🤖 **Robotics teleoperation** (the active bet) | **ACTIVE** | **`ROBOTICS_CLAUDE.md`** |

Shared infrastructure (EC2, `isaaclab` container, OVRTX renderer, Blender 4.5, WebXR
app) is documented in §2–§16 above and is used by all workstreams.

---
