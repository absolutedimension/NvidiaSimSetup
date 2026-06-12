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
| 💃 **Music → character animation** (dance, AMP, Daphne, Phase 3) — **PAUSED 2026-05-21** | This file (`CLAUDE.md`) §19 — paused, resumable, do NOT discard |
| 🎬 **Video rendering** (Blender EEVEE/Cycles, OVRTX, ffmpeg) | **`VIDEO_RENDERING.md`** (master reference for all video work) |
| 🏗️ Shared infrastructure (EC2, container, Content Agents, WebXR app) | This file §2–§16 |

The workstreams share infrastructure (same EC2, same `isaaclab` container, same WebXR app) but the **code paths are isolated** — drone code at `/workspace/isaaclab/.../quadcopter_city_a2b/`, dance code at `/workspace/isaaclab/.../humanoid_amp/`, robotics teleop is mostly a new layer above all of these (Quest app + PC bridge + URDF retargeting + ROS 2 / Isaac Lab integration). Edits in one should not affect the others.

**Current active session focus (2026-05-21): 🤖 Robotics teleoperation.** Dance work is fully checkpointed and resumable but no longer the priority — see `CLAUDE.md §19.10` for the pause note and `ROBOTICS_CLAUDE.md` for the pivot strategy.

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

## 17. Drone training pipeline (2026-05-18 — current focus)

A second pipeline added on top of the same `TrigunAI-Omniverse` box. Trains a PPO policy in Isaac Lab for a quadcopter task, captures the learned trajectory, bakes an animated USDA, renders a verification MP4 via OVRTX, and exports an animated GLB for VR playback inside the **GurulokInnerJourney** Unity app (live in Meta alpha — see `/Users/deepakkumarrai/Downloads/CLAUDE_FlowArtdance_VR.md`).

This pipeline coexists with the §3 services; it just uses Avinash's separate `isaaclab` Docker container (image `isaaclab-v2:custom`, 25 GB) which sits idle on the same box.

### 17.1 What this pipeline does (one diagram)

```
[Isaac Lab + rl_games train.py]            <-- AWS, in `isaaclab` container, GPU-only
        │ saves .pth checkpoint
        ▼
[export_drone_trajectory.py]               <-- our script, runs IN container
        │ writes drone_trajectory.json (per-frame world-space t + q)
        ▼
[render_drone_demo.py --trajectory]        <-- our script, runs on EC2 host
        ├── full scene mode  ──> drone_trained.mp4    (OVRTX renderer at :8001)
        └── minimal-usda     ──> drone_trained_minimal.usda
                                       │
                                       ▼
                              [blender45 usd_to_glb.py --animated]
                                       │
                                       ▼
                              cf2x_trained.glb  (animated, NLA-strip exported)
                                       │
                                       ▼
                              MetaSpatialSDKTest assets/ OR
                              GurulokInnerJourney/Assets/_App/DroneJourney/Models/
```

### 17.2 The hard lesson — why we don't use Isaac Lab's `--video`

Driver 595 (April 2026, what AWS bundles in every NVIDIA AMI) has a **hard incompatibility** with the `rtx.scenedb` plugin used by `omni.kit.widget.viewport-107.0.7` in Isaac Sim 4.5/4.2. Symptom: TLAS allocation rejected with `valid true, within false`, then `Segmentation fault`. This kills:
- `isaaclab.sh -s` (the standalone editor)
- `play.py --video` (anything that touches the viewport widget)
- `tutorials/00_sim/create_empty.py` (any SimulationApp that loads the viewport)

What still works on driver 595:
- Pure headless training (no rendering, just physics + tensors) — **360–370k FPS** on g5.2xlarge A10G.
- The OVRTX rendering API container (`material_agent_service-ovrtx-rendering-api` on :8001) — NVIDIA's custom direct-to-buffer renderer that bypasses `omni.kit.widget.viewport`.

**Isaac Sim 6.0.0-rc.22 (in Avinash's `isaaclab-v2:custom` image) fixes the viewport widget bug.** Inside that container, both training and the `_debug_vis_callback` -based viewport now work. But for visual eval we still don't use Isaac Lab's `--video` — we use the OVRTX → USDA → MP4 path described below, because it composes cleanly with the Quest WebXR / GurulokInnerJourney delivery path.

### 17.3 Critical environment

| Item | Value |
|---|---|
| Trained Isaac Sim version | 6.0.0-rc.22 (inside `isaaclab-v2:custom` container, NOT installed on host) |
| Isaac Lab version | 3.0.0 (in same container, `/workspace/isaaclab/`) |
| Container start | `sudo docker start isaaclab` (was Exited 137 after 42 h idle; comes back cleanly with the X11 mounts intact) |
| Quadcopter env | `Isaac-Quadcopter-Direct-v0` (Crazyflie / cf2x, 4-rotor) |
| Crazyflie USD | inside container: `/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/cf2x.usd` |
| Crazyflie USD (host copies) | `/tmp/cf2x.usd` (visible to OVRTX as `/host_tmp/cf2x.usd`) + `/home/ubuntu/assets/Crazyflie/cf2x.usd` (EBS-persistent) |
| Crazyflie GLB (already converted) | `/home/ubuntu/cf2x.glb` on EC2 + `~/Documents/NvidiaSimSetup/drone_handoff/cf2x.glb` on Mac |
| Patch in Isaac Lab source | `~/IsaacLab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter/quadcopter_env.py` — `_debug_vis_callback` wrapped with `try/except RuntimeError: pass` so headless+camera doesn't die when the viewport widget never spawned the goal marker prim |

### 17.4 Scripts (all live in `webxr-showcase/scripts/`)

| File | What it does |
|---|---|
| `export_drone_trajectory.py` | Runs **inside** the isaaclab container. Loads a `.pth` checkpoint, instantiates the env at `num_envs=1`, steps it for N frames, captures `robot.data.root_pos_w` + `root_quat_w` per step via a `.numpy()` -or- `.cpu()` polymorphic accessor (Isaac Lab 3.0 returns `wp.array`; older builds returned `torch.Tensor`). Writes JSON. |
| `render_drone_demo.py` | Two modes. (a) hardcoded smoothstep A→B (for smoke tests with no training) and (b) `--trajectory drone_trajectory.json` to bake the trained motion. Two output templates: full-scene (floor + camera + lights + green/red markers + drone, for verification MP4) and `--minimal-usda` (just the animated Drone Xform, for GLB export). Coordinate remap: Isaac Sim's Z-up → USD's Y-up via `(x, z, -y)` for positions and `(qw, qx, qz, -qy)` for quats. |
| `usd_to_glb.py` | Blender 4.5 headless. New `--animated` flag pushes USD-imported actions to NLA strips (per GurulokInnerJourney CLAUDE PRIMITIVE 3 rule: "action must be in NLA strip or Unity's Animated() won't play it") and exports with `export_animation_mode="NLA_TRACKS", export_nla_strips=True`. |

### 17.5 End-to-end run sequence

```bash
EC2_IP=<current public IP>
PEM="/Users/deepakkumarrai/Library/Mobile Documents/com~apple~CloudDocs/TrigunSAI/trigunai_key.pem"

# 0. start container if needed
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 1. train policy (writes to /workspace/isaaclab/logs/rl_games/quadcopter_direct/<timestamp>/nn/*.pth)
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
  ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
  --task Isaac-Quadcopter-Direct-v0 --viz none --num_envs 4096 --max_iterations 100 \
  > /tmp/drone_train.log 2>&1"'
# wait ~3-4 min, then check the latest dir under .../quadcopter_direct/

# 2. export trajectory (writes to in-container path, then docker cp out)
scp -i $PEM webxr-showcase/scripts/export_drone_trajectory.py ubuntu@$EC2_IP:/home/ubuntu/
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker cp /home/ubuntu/export_drone_trajectory.py isaaclab:/workspace/isaaclab/export_drone_trajectory.py'
CKPT="/workspace/isaaclab/logs/rl_games/quadcopter_direct/<TIMESTAMP>/nn/last_quadcopter_direct_ep_100_rew_<REWARD>.pth"
ssh -i $PEM ubuntu@$EC2_IP "sudo docker exec isaaclab bash -lc 'cd /workspace/isaaclab && \
  ./isaaclab.sh -p export_drone_trajectory.py --checkpoint $CKPT --steps 180 --fps 24 \
  --out /workspace/isaaclab/exports/drone_trajectory.json'"
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker cp isaaclab:/workspace/isaaclab/exports/drone_trajectory.json /tmp/drone_trajectory.json && sudo chown ubuntu:ubuntu /tmp/drone_trajectory.json'

# 3. verification MP4 via OVRTX (full scene with cf2x + markers + camera)
scp -i $PEM webxr-showcase/scripts/render_drone_demo.py ubuntu@$EC2_IP:/home/ubuntu/
ssh -i $PEM ubuntu@$EC2_IP 'python3 /home/ubuntu/render_drone_demo.py \
  --trajectory /tmp/drone_trajectory.json --fps 0 \
  --drone-asset /host_tmp/cf2x.usd --drone-scale 5.0 \
  --width 800 --height 450 --keep-usda \
  --out /home/ubuntu/drone_trained.mp4'

# 4. minimal USDA + Blender → animated GLB (no floor/camera/lights — Quest scene provides them)
ssh -i $PEM ubuntu@$EC2_IP 'python3 /home/ubuntu/render_drone_demo.py \
  --trajectory /tmp/drone_trajectory.json --fps 0 \
  --drone-asset /home/ubuntu/cf2x.usd --drone-scale 5.0 \
  --minimal-usda --skip-render --keep-usda \
  --out /home/ubuntu/drone_trained_minimal.mp4'
scp -i $PEM webxr-showcase/scripts/usd_to_glb.py ubuntu@$EC2_IP:/home/ubuntu/
ssh -i $PEM ubuntu@$EC2_IP 'blender45 --background --python /home/ubuntu/usd_to_glb.py -- \
  --input /home/ubuntu/drone_trained_minimal.usda \
  --output /home/ubuntu/cf2x_trained.glb \
  --animated --max-texture 1024'

# 5. pull back to Mac
scp -i $PEM ubuntu@$EC2_IP:/home/ubuntu/drone_trained.mp4 ~/Documents/NvidiaSimSetup/drone_trained.mp4
scp -i $PEM ubuntu@$EC2_IP:/home/ubuntu/cf2x_trained.glb ~/Documents/NvidiaSimSetup/drone_handoff/cf2x_trained.glb
```

### 17.6 Gotchas accumulated so far

| Symptom | Cause | Fix |
|---|---|---|
| Isaac Lab `--video` produces black MP4 | Default RecordVideo viewport is not aimed at the drone (the camera-prim-points-at-empty-space bug Avinash warned about for Franka v2) | Don't use `--video`. Use the OVRTX pipeline. |
| `RuntimeError: Accessed schema on invalid prim` during `play.py` | `quadcopter_env.py _debug_vis_callback` calls `goal_pos_visualizer.visualize()` after the viewport widget removed the marker prim | Patched in-place: wrapped in `try: ... except RuntimeError: pass` |
| `Item indexing is not supported on wp.array objects` | Isaac Lab 3.0 returns `warp.array` from `robot.data.root_pos_w`; old indexing `[0]` fails | `export_drone_trajectory.py` uses a polymorphic `_to_list()` that handles `.numpy()` (warp) / `.cpu()` (torch) / raw indexing |
| `Image is not available' from OVRTX container | `/tmp` host directory was wiped on EC2 stop/start; `cf2x.usd` was at `/tmp/cf2x.usd` so the OVRTX-side `/host_tmp/cf2x.usd` reference broke | Re-copy from container (`docker cp isaaclab:/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/`) to BOTH `/tmp` (visible to OVRTX) and `/home/ubuntu/assets/Crazyflie/` (EBS persistent) |
| Drone slides sideways instead of flying up | Coordinate system: Isaac Sim is Z-up, USD scene is Y-up | `load_trajectory_json` remaps `(x, y, z) -> (x, z, -y)` for positions and `(qw, qx, qy, qz) -> (qw, qx, qz, -qy)` for quats |
| `play.py` exits with code 0 but no fps/epoch logs in stdout | rl_games stdout is buffered+suppressed in Isaac Lab 3.0; outputs go only to TensorBoard | Don't trust stdout silence — check `logs/rl_games/<task>/<timestamp>/nn/` for `.pth` files instead |
| GLB animation not playing in Unity | Blender's gltf exporter drops "loose" actions; only NLA strips survive | `usd_to_glb.py --animated` pushes actions to NLA strips before export, sets `export_animation_mode="NLA_TRACKS", export_nla_strips=True` |

### 17.7 Where the Quest VR side lives

The trained drone's GLB ships to **GurulokInnerJourney** (Unity, Quest 3, already live in Meta alpha — App ID `24914535711578182`, build v63). The handoff doc for that agent is at `drone_handoff/DRONE_GUROLOK_HANDOFF.md`. It tells the Windows-side Claude to:
1. Drop the GLB at `Assets/_App/DroneJourney/Models/cf2x.glb` (or `cf2x_trained.glb` once Phase 2 ships)
2. Write `DroneJourneyController.cs` implementing `IJourney` (mirror of `CosmicJourneyController`)
3. Write `DroneJourneySetup.cs` editor script (mirror of `RamChantingJourneySetup.cs`, with v46 menu-rebuild + v62 orphan-cleanup safeguards from CLAUDE_FlowArtdance_VR.md §8 baked in)
4. Build v64 via `QuestBuildAndUpload.BuildQuestAPK`
5. Upload to alpha via `ovr-platform-util upload-quest-build`

The user does this on a regular cadence (per testing iteration), so:
- **Phase 1 (static drone, no training)** = static cf2x.glb in the Quest scene + hover bob animation written in Kotlin/C#. Built in NvidiaSimSetup, shipped to MetaSpatialSDKTest first (handoff doc at `MetaSpatialSDKTest/DRONE_HANDOFF.md`), then pivoted to GurulokInnerJourney (same GLB, different handoff doc).
- **Phase 2 (trained trajectory, animated GLB)** = this section's pipeline. Replaces the static GLB with `cf2x_trained.glb` carrying the trained policy's motion as a glTF animation clip.

### 17.8 Reused infrastructure (do NOT duplicate)

| Asset | Already exists | Path |
|---|---|---|
| OVRTX rendering API | running on :8001 as part of NVIDIA Content Agents (§3) | `material_agent_service-ovrtx-rendering-api` container |
| Blender 4.5 LTS with USD support | installed at `/opt/blender45`, symlinked `blender45` | per §8 |
| nginx + Cloudflare quick tunnel | for serving GLB to non-Quest browsers if needed | per §3 + `webxr-showcase/scripts/start_tunnel.sh` |
| `usd_to_glb.py` | originally written for §8 WebXR Showcases; v2 adds `--animated` for the drone path | `webxr-showcase/scripts/usd_to_glb.py` |
| Crazyflie GLB (static) | already converted + staged | `drone_handoff/cf2x.glb` (Mac) + `/home/ubuntu/cf2x.glb` (EC2) |

The drone pipeline does **not** introduce any new long-running services or containers. It piggybacks entirely on the existing OVRTX rendering api + the dormant `isaaclab` container that Avinash had built.

### 17.9 VLM critic — closing the training-feedback loop (Approach A)

The pipeline now includes a **post-training quality gate** using gpt-4o-mini (via the existing LiteLLM proxy on port 4000). After rendering a trained-policy MP4, the VLM grades the flight on four dimensions and returns a structured JSON verdict. This is the same vision-language pattern the NVIDIA Content Agents already use to classify materials / predict physics on rendered USDs — we just pointed it at our drone footage.

#### Script: `evaluate_drone_trajectory.py`

```bash
# Standalone — grade an existing MP4
python3 /home/ubuntu/evaluate_drone_trajectory.py \
  --mp4 /home/ubuntu/drone_trained.mp4 \
  --out /home/ubuntu/drone_evaluation.json \
  --save-grid /home/ubuntu/drone_evaluation_grid.jpg
```

How it works (one screen of prose):
1. Extracts 6 keyframes via `ffmpeg`, evenly spaced across the MP4
2. Stitches them into a 2×3 grid JPEG (`tile_w=512`, ≈20 KB encoded)
3. POSTs the grid as a base64 data URI to `http://localhost:4000/v1/chat/completions` with a vision message (OpenAI format, LiteLLM proxies to Azure gpt-4o-mini)
4. System prompt explains the task, the markers (green = A, red = B), the drone model, and asks for JSON only
5. `response_format = {"type": "json_object"}` + temperature 0.2 → consistent structured output

Sample real output (against our 100-iter `drone_trained.mp4`):
```json
{
  "reach": 6, "smoothness": 5, "stability": 7, "efficiency": 6,
  "overall": 6,
  "issues": ["Drifted away from goal", "Some oscillation in movement"],
  "verdict": "needs-more-training"
}
```

Cost: ~$0.0001/call. Latency: 3–8 sec. Calibrated on the actual `Isaac-Quadcopter-Direct-v0` task footage. The verdict above is **correct** — at 100 iterations the policy oscillates around the goal; needs ~500 to settle into a clean hover.

#### Integration with `render_drone_demo.py`

Pass `--evaluate` to auto-run the critic after the MP4 is encoded:

```bash
python3 render_drone_demo.py \
  --trajectory /tmp/drone_trajectory.json --fps 0 \
  --drone-asset /host_tmp/cf2x.usd --drone-scale 5.0 \
  --out /home/ubuntu/drone_trained.mp4 \
  --evaluate
# Produces drone_trained.mp4 + drone_trained.evaluation.json + drone_trained.evaluation_grid.jpg
```

#### Operational shape

| Verdict | What to do |
|---|---|
| `ship-it` | `cf2x_trained.glb` is ready — proceed to drone_handoff/ + Gurulok integration |
| `needs-more-training` | run another `train.py --max_iterations 100` cycle, re-export trajectory, re-render, re-evaluate |
| `broken` | something failed (crashes / didn't move / wrong direction). Inspect the grid JPEG; usually a reward-function bug or env-config drift |

Future: wrap into `train_until_ship_it.sh` that loops `train → export → render → evaluate` until verdict is `ship-it` or iteration budget exhausted. The grid composite + JSON verdict can travel with the GLB in `drone_handoff/` so the Gurulok agent knows what to expect in VR.

#### Dependencies

On the EC2 box (one-time, persists on EBS):
```bash
pip install --break-system-packages --user pillow requests
```

`ffmpeg` is already in the AMI. LiteLLM master key + Azure endpoint live in `~/litellm/config.yaml` (already configured for the Content Agents). The proxy is the same `litellm-proxy` container that the Material / Physics / Texture agents already share on port 4000.

#### Why this matters

Closes the loop between training and visual eval **without humans in the path**. Every new policy iteration produces a measurable score — you can plot reward-over-iterations alongside VLM-score-over-iterations and see if the optimizer is actually producing visually better flights, not just higher numerical reward. Catches the classic RL failure mode where the policy games the reward but looks terrible.

This is **Approach A** of three. Approach B (in-loop VLM reward shaping during training) and Approach C (VLM-designed reward function, Eureka-style — see Nvidia's 2023 paper) are research-grade extensions if/when Approach A reaches its quality ceiling.

### 17.10 Lessons from the first ship-it run (2026-05-18)

The first successful `ship-it` verdict (500-iter PPO, overall 8/10) required three fixes after the naive setup. These now live in code; this section is the documentation of *why*.

#### Lesson 1: `/tmp/cf2x.usd` is ephemeral; the asset has to be restored after every box stop/start

Per §15 the host `/tmp/` is wiped on instance stop. Our USDA references `references = @/host_tmp/cf2x.usd@` which is the OVRTX container's view of host `/tmp/`. When that file is missing, **OVRTX silently renders the Drone Xform as an empty prim — no error, just an invisible drone.**

The first 500-iter render produced a completely blank scene (markers only, no drone). Took 20 minutes to diagnose because the symptom was "VLM scores 8/10 but the drone isn't visible" — both layers failed silently.

**Fix in workflow:** after every `sudo docker start isaaclab` (or every box restart), restore the asset:

```bash
# from EBS-persistent home back to host /tmp so OVRTX's /host_tmp mount sees it
cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/cf2x.usd
cp /home/ubuntu/assets/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd
```

Or pass `--drone-asset /home/ubuntu/assets/Crazyflie/cf2x.usd` to `render_drone_demo.py` directly — but the USDA's data-URI request still needs paths that OVRTX can resolve, and OVRTX only mounts `/host_tmp` → host `/tmp`. So path inside the data URI must remain `/host_tmp/...`.

#### Lesson 2: Camera must auto-frame from trajectory bounds, not be fixed

`render_drone_demo.py` originally hard-coded the camera at `(0, 3.5, 7)`. That works for hardcoded A→B trajectories that stay near origin, but trained policies actually move — the 500-iter policy drifted to USD X = -1.4 m, which is outside the fixed camera's frustum.

Symptom: scene rendered fine, markers visible, but no drone. **The VLM then hallucinated 8/10** because gpt-4o-mini, given a blank scene and a prompt explaining "the drone is in this scene", will default to neutral-positive grades.

**Fix in `bake_drone_usda`:** when `--trajectory` is set, compute the bounding box of all trajectory positions, place the camera at `(cx, cy + max(span*0.7, 3), cz + max(span*1.4, 6))` looking down 20°. Always frames the drone regardless of where the policy flew it.

#### Lesson 3: VLM prompt must explicitly say "if you can't see the drone, return broken"

Even with the camera fixed, the VLM-as-critic pattern has a failure mode: when the drone is invisible (off-frame, occluded, missing reference), gpt-4o-mini happily returns mid-range scores like `reach=6, smoothness=5`. It will not flag invisibility on its own.

**Fix in `evaluate_drone_trajectory.py`:** the system prompt now has a critical preamble:

```
**CRITICAL: First, confirm the drone is actually visible in the frames.** If you
cannot see a small grey quadcopter in any of the keyframes — only the floor + the
A/B markers — then the policy flew the drone out of the camera's framing OR
crashed below the floor. In that case set every dimension to 1, list "drone not
visible in any keyframe" as the first issue, and set verdict = "broken". Do NOT
hallucinate a drone you cannot see.
```

After this, the SAME blank scene that previously scored 8/10 now correctly returns `verdict: "broken"`, `overall: 1`, `issues: ["drone not visible in any keyframe"]`.

This is a general lesson for **any** VLM-as-critic: gpt-4o-mini will hallucinate task fulfillment from textual context if you don't explicitly require it to verify the subject is visible. Bake the visibility check into the prompt.

#### Sanity: 100-iter vs 500-iter v3 comparison

After all three fixes:

| Metric | 100-iter | 500-iter v3 | Δ |
|---|---|---|---|
| reach | 6 | 8 | +2 |
| smoothness | 5 | 7 | +2 |
| stability | 7 | 9 | +2 |
| efficiency | 6 | 8 | +2 |
| overall | 6 | 8 | +2 |
| issues count | 2 | 0 | -2 |
| verdict | needs-more-training | **ship-it** | ✓ |
| reward (rl_games) | 130.45 | 113.90 | -16.55 ← drop! |

**Note the divergence between reward and VLM score.** Numerical reward DROPPED from epoch 100 (peak 130.45) to epoch 500 (113.90) due to performance collapse around epoch 325. But the VLM judges the 500-iter policy as visually *better* — bigger range of motion, cleaner attitude. **The VLM is measuring what humans care about (looks-like-good-flying); the reward is measuring what PPO is optimizing (a particular formula). They diverge by design.** This is exactly why Approach A matters: you need an eye outside the optimizer.

### 17.11 Open / on the radar

- **City scene backdrop:** downloading `Simple_Warehouse.usd` from NVIDIA's public S3 bucket worked but renders black because it references `../../Props/*` directories we don't have. For Phase 3 we'll either pull the Props folder too (sibling files on same S3 path), procedurally add box buildings, or use the existing IsaacWarehouse GLB at `/var/www/showcase/assets/warehouse.glb` as a Unity backdrop.
- **Animated GLB animation track:** confirmed via Blender's `export_animation_mode="NLA_TRACKS"`, but Quest playback needs Unity-side `Animated()` component wiring per CLAUDE_FlowArtdance_VR.md PRIMITIVE 3. Owner: the GurulokInnerJourney agent.
- **Avinash's review** of Phase 1 + Phase 2 deliverables — see [DRONE_PIPELINE_HANDOFF.md](DRONE_PIPELINE_HANDOFF.md), unread at time of writing.
- **Phase 3:** real drone-A-to-B with a city scene. The training task `Isaac-TrackPositionNoObstacles-ARL-Robot-1-v0` exists in Isaac Lab 3.0 and is closer to the production goal than `Isaac-Quadcopter-Direct-v0` (which is just hover-to-goal).

---

## 18. Resume sequence for the drone pipeline

```bash
# 1. start EC2 + grab current IP
EC2_IP=<current public IP from AWS console, $TrigunAI-Omniverse>

# 2. start the isaaclab container (the agents auto-start; isaaclab does not)
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 3. confirm Crazyflie USD is in BOTH host /tmp and /home/ubuntu/assets/
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
  'ls /tmp/cf2x.usd /home/ubuntu/assets/Crazyflie/cf2x.usd 2>&1'
# If /tmp/cf2x.usd is missing (always after EC2 stop), re-copy from the EBS-persistent path:
#   sudo docker cp isaaclab:/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/cf2x.usd /tmp/cf2x.usd
#   sudo docker cp isaaclab:/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd

# 4. all scripts live at $REPO/webxr-showcase/scripts/ — scp the three latest:
PEM="$HOME/.ssh/trigunai_key.pem"
for f in render_drone_demo.py export_drone_trajectory.py usd_to_glb.py; do
  scp -i $PEM webxr-showcase/scripts/$f ubuntu@$EC2_IP:/home/ubuntu/$f
done

# 5. run the chain documented in §17.5
```

If something looks broken, the first checks in order are:
1. `docker ps` shows all 6+ agent containers + `isaaclab` Up (healthy)
2. `curl -s localhost:8001/health` returns `gpu_initialized: true`
3. `nvidia-smi` shows A10G, ECC enabled (disabled state was tested in earlier diagnosis but didn't fix anything — leave it enabled to match Avinash's setup)
4. The patch in `quadcopter_env.py` is still in place (`try: ... except RuntimeError: pass` around `goal_pos_visualizer.visualize`)

---

---

## 19. PIVOT — Music → Character Animation product (2026-05-19)

**Drone work is paused.** Phase 6a Rivermark city training shipped (reward 725, drone flew 0→115 m forward), but the city-trained GLB has a rotation bug in WebXR and the user decided to pivot rather than debug. Drone artifacts kept on disk; can be resumed later.

**New product, one-liner:** user uploads music → service returns a stylized character GLB dancing to that music. Surfaces as a web demo + a "Dance Partner" journey inside the Gurulok Quest 3 app.

### 19.1 Pipeline

```
Gurulok VR mocap (Quest 3 + IOBT, 33 joints, pose.bin)
   ↓ pose_bin_to_amp_motion.py (LH/Y-up → RH/Z-up, 33j → 15 bodies)
Isaac Lab AMP .npz (motion_loader.py contract)
   ↓ skrl AMP discriminator + PPO (Isaac-Humanoid-AMP-Dance-Direct-v0 template)
trained dance policy (.pt)
   ↓ music conditioning (Phase 3: beat features → audio CLIP)
music-aware policy
   ↓ rollout in headless Isaac Sim → USD timeline → Blender → GLB (NLA strips)
animated dance GLB → WebXR + Gurulok Unity app
```

Full roadmap: `/Users/deepakkumarrai/NvidiaSimSetup/MUSIC_TO_CHARACTER_ANIMATION_STRATEGY.md` (5 phases, ~$30 to demo).

### 19.2 Current state (as of 2026-05-19)

| Phase | Status |
|---|---|
| 0 — pull mocap from Gurulok | ✅ 9 clean sessions (~6.8 min, `cosmic-hypnotic`) in `mocap_handoff/Mocap/dance_20260519_194*` |
| 0 — Gurulok mocap recorder bug | ✅ **UNBLOCKED** — Gurulok build `446ad0f4` (2026-05-19 19:40) fixed socket serialization. Upper body real, lower body IK-predicted into `predicted/` subfolder per session. See `mocap_handoff/STATUS_2026-05-19_UNBLOCKED.md`. |
| 1 — `pose_bin_to_amp_motion.py` converter | ✅ verified on real data — `dance_20260519_194152/predicted/` → `(2274, 28)` DOFs + `(2274, 15, 3)` bodies; dof_names + body_names exact match against built-in `humanoid_dance.npz` |
| 1 — AMP smoke test on EC2 (built-in dance) | ✅ 20 iters, no crash |
| 2 — AMP smoke train on real Gurulok mocap | ✅ 50 iters / 800 timesteps in 42s on 4096 envs, checkpoints saved to `/workspace/isaaclab/logs/skrl/humanoid_amp_dance/2026-05-19_14-44-13_amp_torch/` |
| 2 — AMP full train on Gurulok mocap | ✅ 500 iters / 8000 timesteps in ~6 min on 4096 envs (A10G). Log: `/workspace/isaaclab/logs/skrl/humanoid_amp_dance/2026-05-19_14-46-28_amp_torch/`, `best_agent.pt` + `agent_8000.pt` saved. |
| 2 — concat all 9 sessions for richer training | ⏳ next — extend converter `--sessions <list>` or motion-set in env cfg |
| 3 — music conditioning | ⏳ Phase 3 (input ready: `music_track="cosmic-hypnotic"` in every session's `meta.json`; MP3 at `GurulokInnerJourney/Assets/_Core/Audio/cosmic-hypnotic.mp3`) |
| 4 — inference API + product | ⏳ Phase 4 |

### 19.3 Critical gotchas discovered this round

1. **AMP needs `--algorithm AMP`** — default `train.py` looks for `skrl_cfg_entry_point` (PPO). AMP envs register under `skrl_amp_cfg_entry_point` only, so without the flag you get `ValueError: Could not find configuration for the environment`.
   ```
   ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
     --task Isaac-Humanoid-AMP-Dance-Direct-v0 --algorithm AMP \
     --num_envs 1024 --max_iterations 20 --headless
   ```

2. **Mocap session duration mismatch** — `dance_20260519_124105` reports 238.5 s in session metadata but the pose.bin contains 9946 frames @ 60 fps = 165.8 s. Either wall-clock drift in the recorder or dropped frames. Flagged to the VR agent alongside the T-pose bug.

3. **Coord transform Unity → Isaac Lab** — Unity is left-hand Y-up; Isaac Lab is right-hand Z-up. Positions: `(x, y, z) → (x, z, y)`. Quaternions: `(qx, qy, qz, qw) → (qx, qz, qy, qw)`. This is encoded in `pose_bin_to_amp_motion.py`.

4. **33 Gurulok joints → 15 Isaac humanoid bodies** — only the subset Isaac's AMP humanoid asset has (pelvis, torso, head, 2× upper_arm/lower_arm/hand, 2× thigh/shin/foot). Fingers, spine sub-joints, etc. are dropped. Mapping is in `GUROLOK_TO_ISAAC_BODY` dict at the top of the converter.

5. **DOF positions/velocities are zeros for first pass** — proper inverse kinematics to decompose body rotations into joint angles is deferred. The AMP discriminator works primarily on body-level features (positions + rotations + linear/angular velocities), so first-pass quality should be OK without DOF data.

6. **Lower body is IK-predicted, not measured** — Quest is in `BodyJointSet.UpperBody` mode (`tracking_quality=1`), so `joints[25–32]` in raw `pose.bin` are NaN. The VR agent ships a Mac-side IK filler at `mocap_handoff/predictor/predict_lower_body.py` that produces standing-pose legs (head + wrist heading + user_height → hips/knees/ankles/feet). Use the `predicted/` subfolder of each session, not the raw `pose.bin`. If/when VR agent switches to `BodyJointSet.FullBody` (IOBT), `tracking_quality=2` will appear and the raw pose.bin becomes usable.

### 19.4 Key files for the new pipeline

| File | Purpose |
|---|---|
| `/Users/deepakkumarrai/NvidiaSimSetup/MUSIC_TO_CHARACTER_ANIMATION_STRATEGY.md` | 5-phase roadmap, budget, risk table, decision tree |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/pose_bin_to_amp_motion.py` | Gurulok pose.bin → Isaac AMP .npz converter |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/HANDOFF_VR_CODING_AGENT.md` | Bug report for Gurulok VR agent (T-pose-frozen recorder) |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/HANDOFF_NVIDIA_TRAINING_AGENT.md` | Bug context for whoever picks up the NVIDIA side |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/Mocap/` | 8 raw sessions (currently buggy) |
| `/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp/` | Isaac Lab's reference AMP humanoid task (template we're forking) |
| `/workspace/isaaclab/.../humanoid_amp/motions/humanoid_dance.npz` | Built-in reference dance motion (used for smoke test) |
| `/workspace/isaaclab/.../humanoid_amp/motions/gurulok_dance_v1.npz` | Our converted Gurulok mocap (single session, 2274 frames / 37.9 s) |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/predictor/predict_lower_body.py` | Mac-side IK filler — populates lower body NaN from head + wrist heading + user_height |
| `/Users/deepakkumarrai/NvidiaSimSetup/mocap_handoff/STATUS_2026-05-19_UNBLOCKED.md` | The unblock report — 9 clean sessions, music tagged, predictor + session inventory |

### 19.5 Resume sequence for the dance pipeline

```bash
# 1. start EC2 (us-east-1 box, public IP changes after stop)
EC2_IP=<from AWS console>

# 2. start isaaclab container (everything persists on EBS root volume)
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 3. (Phase 3b) resume music-conditioned training — patches already applied
#     to /workspace/isaaclab/source/isaaclab_tasks/.../humanoid_amp/
#     observation_space=90, motion_file=gurulok_dance_v2_with_music.npz
#     If host /tmp lost the music npz, re-push from local backup first:
#       scp -i /tmp/trigunai_key.pem \
#         ~/NvidiaSimSetup/checkpoints/gurulok_dance_v2_with_music.npz \
#         ubuntu@$EC2_IP:/tmp/
#       ssh ubuntu@$EC2_IP 'sudo docker cp /tmp/gurulok_dance_v2_with_music.npz \
#         isaaclab:/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp/motions/'

ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
     --task Isaac-Humanoid-AMP-Dance-Direct-v0 --algorithm AMP \
     --num_envs 256 --max_iterations 3000 --headless > /tmp/amp_train_music_resume.log 2>&1"'

# 4. render trained policy on Daphne (CC4 character) — see §19.6
```

### 19.6 Phase 3 progress (2026-05-20)

**Phase 3 music conditioning is wired end-to-end and validated.** First training run completed 600 iters before an OOM kill — checkpoints saved locally.

| Subtask | Status |
|---|---|
| Extract 9 audio features per frame from `cosmic-hypnotic.mp3` | ✅ `mocap_handoff/add_music_features_to_npz.py` produces `gurulok_dance_v2_with_music.npz` (63 MB). Features: bpm, beat_phase, onset, rms, spectral centroid+rolloff, bass/mid/treble energy. Z-scored. |
| Patch `MotionLoader` for music features | ✅ Adds `music_features`, `num_music_features`, `sample_music_features(times)`. Back-compat if npz lacks the key. |
| Patch `HumanoidAmpEnv` for per-env motion clock + 9-feature obs append | ✅ `env_motion_t` advances by `sim_dt` each step, wraps at clip duration. On reset, time is set from `_reset_strategy_random`'s sampled times so policy obs and reference obs are time-synced. |
| Patch `humanoid_amp_env_cfg.py` for 90-dim obs | ✅ `observation_space=90`, `amp_observation_space=90`, motion_file points at `_with_music.npz`. |
| Phase 3a — train first music-conditioned policy | ✅ 600 iters (= 9600 timesteps) at 512 envs. Crashed via OS OOM (system RAM ~31GB tight with music npz loaded). Checkpoints + tensorboard backed up locally. |
| Phase 3b — train longer at lower env count | ⏳ Stopped before completing — 256 envs target, ~70 min wallclock for 3000 iters. Patches already in place; just rerun the training command. |
| Phase 3c — render music-conditioned rollout | ⏳ Next session. Use existing rollout chain → Daphne retargeter. |

### 19.7 CC4 character retargeting (Daphne)

User has a Reallusion Character Creator 4 character `Daphne_Blender.fbx` (196 MB, ~75K verts, full body + face + 15 finger bones per hand + 5 toe bones per foot). v7 retargeter shipped and visible in WebXR. Approach:

- **Position-only retargeting** (no quaternion copying — caused contortion in earlier passes). 12 empty markers at key Quest joints (pelvis, torso, head + head-up, L/R hand, L/R elbow).
- **IK on `L/R_Forearm`** with chain length 2 (Forearm + Upperarm), pole vectors offset 30 cm behind the elbow for natural bend.
- **DampedTrack on spine bones** (`Spine01`, `Spine02`, `Waist`, `Neck*`, `Head`) toward head/torso targets.
- **Lock to rest pose**: clavicles, all `*Twist*` and `*ShareBone*` aux bones, entire leg chain (thighs/calves/feet/toes). Result: feet stay planted on the floor.
- **Pelvis-relative targets + delta from user's own mean pose**: Daphne always starts at her natural upright rest, only the user's *deltas* layer on as motion. Spine-length scale correction (~1.08× for the v129 capture).
- **Z-axis damping** on spine/head deltas (0.20× / 0.30×) so vertical pose drift doesn't fold Daphne forward; hands keep 0.85× Z pass-through for raised arms.
- **Mesh trimming**: Jacket + tongue/teeth/eye-occlusion/tear-line removed. Textures clamped to 1024 px → **GLB drops from 186 MB to 14 MB**.

**Side-by-side compound showcase** in WebXR (`/assets/manifest.json` → "Daphne vs Stick"): Daphne on the left, raw stick figure on the right, both driven from the same npz, 1.6 m apart. Use this to A/B which retargeting choices preserve vs distort the captured motion.

### 19.8 PhysX OOM lessons (memo for future training runs)

PhysX's `gpu_found_lost_pairs_capacity` setting scales with humanoid collision complexity AND env count, AND it allocates a GPU buffer proportional to the cap:

| num_envs | PhysX cap that works | Buffer cost | Wallclock crash at default 2²³ |
|---|---|---|---|
| 4096 | needs 2²⁹ — but buffer alloc OOMs | ~4 GB | warmup |
| 2048 | needs 2²⁸ — buffer alloc OOMs at 23 GB total | ~2 GB | 7 min |
| 512 | needs 2²⁶ — survives buffer-wise, **but system RAM OOMs at ~8 min** | ~512 MB | 8 min |
| **256** | **2²⁶ probably sufficient, lower RAM pressure** | ~256 MB | (next session) |

Pattern: bigger envs → bigger cap → either GPU buffer OOM or PhysX warning + silent kill. System RAM is also tight on 31 GB instance because the 63 MB music npz loads into Isaac + each parallel env holds derived tensors. **Run at 256 envs going forward.**

### 19.9 Local backups (safe across EC2 stop)

| Local path | Content |
|---|---|
| `~/NvidiaSimSetup/checkpoints/ckpt_backup.tgz` | 225 MB — pre-music v1 baseline (500-iter policy, gurulok_dance_v1.npz) |
| `~/NvidiaSimSetup/checkpoints/music_v1/music_ckpt_v1.tgz` | 63 MB — **music-conditioned v1 (600-iter), 90-dim obs, the actual Phase 3 output** |
| `~/NvidiaSimSetup/checkpoints/gurulok_dance_v1.npz` | 2.2 MB — single-session reference (37.9 s) |
| `~/NvidiaSimSetup/checkpoints/gurulok_dance_v2.npz` | 62 MB — 6-session reference (226 s, no music yet) |
| `~/NvidiaSimSetup/checkpoints/gurulok_dance_v2_with_music.npz` | 63 MB — **Phase 3 reference, 226 s + 9 audio features/frame** |
| `~/NvidiaSimSetup/mocap_handoff/bake_daphne_animation.py` | Daphne v7 retargeter (Blender headless) |
| `~/NvidiaSimSetup/mocap_handoff/add_music_features_to_npz.py` | Music feature extractor (librosa on `/usr/bin/python3` — Python 3.9) |
| `~/NvidiaSimSetup/mocap_handoff/pose_bin_to_amp_motion_v2.py` | v129 (84-joint) → Isaac AMP (15-body) converter |
| `~/NvidiaSimSetup/mocap_handoff/verify_session_v2.py` | v129 session sanity check |

The patches inside the container (`motion_loader.py`, `humanoid_amp_env.py`, `humanoid_amp_env_cfg.py`) live on the EBS root volume so they persist across EC2 stop. To restore them on a fresh container, re-run the 3 patch scripts from `/tmp/*.py` on EC2 — local copies of the patch scripts: `/tmp/motion_loader_patch.py`, `/tmp/env_patch.py`, `/tmp/cfg_patch.py` (also gone from /tmp host on stop — keep copies in repo if you want them durable).

---

*Last updated: 2026-05-20 — Phase 3 wired end-to-end. Music-conditioned policy v1 (600 iters) checkpointed locally. EC2 safe to stop; resume by starting the box, running §19.5 step 3.*
*Owner: TrigunAI Innovations.*

### 19.10 PAUSE — 2026-05-21

**Dance / music-to-character-animation work is paused.** Pivoted to robotics teleoperation B2B (see `ROBOTICS_CLAUDE.md`). All Phase 3 outputs checkpointed and resumable.

**Why paused:**
- Robotics teleop has 10× the budgets (humanoid labs paying $25/hr per human teleoperator; rigs cost $5k–50k)
- Same underlying tech stack (Quest mocap + Isaac Lab + retargeting) serves both markets
- Robotics is B2B with longer cycles but bigger contracts; dance is consumer with smaller ARPU
- Founder bandwidth focuses on B2B first; dance becomes the "data flywheel + consumer demo" later

**What's preserved (everything still recoverable):**
- ✅ All 3 npz files on local Mac (`~/NvidiaSimSetup/checkpoints/`)
- ✅ 600-iter music-conditioned checkpoint (`music_v1/music_ckpt_v1.tgz`)
- ✅ Patches in `mocap_handoff/isaaclab_patches/`
- ✅ Daphne retargeter (`bake_daphne_animation.py`)
- ✅ Music feature extractor (`add_music_features_to_npz.py`)
- ✅ WebXR live demos (Daphne + policy + fingers GLB)
- ✅ Inside container on EBS: patched env files, gurulok_dance_v2_with_music.npz

**To resume the dance work:**
1. Read this section first
2. Run `§19.5 resume sequence` — start EC2, container, push npz if /tmp empty
3. Continue from Phase 3b (longer training with stability fixes — `learning_rate 2e-5`, `grad_norm_clip 1.0`) OR jump to Phase 4 (style-conditioned multi-dance with Mixamo data)

**Why robotics first instead:** see `ROBOTICS_CLAUDE.md §1` for the pivot strategy.

---
