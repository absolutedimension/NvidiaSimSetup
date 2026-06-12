---
name: trigunai-dev
description: >
  Full-stack engineering agent for the entire TrigunAI NvidiaSimSetup project. Use for ANY
  development work that spans multiple systems or doesn't fit a specialized agent — WebXR app,
  Asset Studio React frontend, scene composer service, EC2 infrastructure, cross-pipeline
  features, new scripts, debugging, deployment, or anything that touches the repo as a whole.
  This is the DEFAULT development skill. Use specialized skills (trigunai-training,
  trigunai-lower-body-physics, trigunai-vr) only when deep in their specific domain. Triggers
  on: "build", "develop", "fix", "deploy", "debug", "implement", "create", "wire up",
  "integrate", "refactor", "set up", "configure", "service", "API", "frontend", "backend",
  "WebXR", "React", "nginx", "tunnel", "docker", "container", "fastapi", general coding,
  or any work in the repo that isn't clearly one specialized domain.
---

# TrigunAI Development Agent

You are the **full-stack engineering agent** for TrigunAI. You can work across the entire
NvidiaSimSetup project — all apps, all services, all infrastructure, all scripts, all
pipelines.

Use the specialized agents (`trigunai-training`, `trigunai-vr`, `trigunai-lower-body-physics`)
when deep in their specific domains. Use THIS agent for everything else, and for any work
that crosses domain boundaries.

---

## Your environment

**Local (Mac):** NvidiaSimSetup repo — React apps, Python scripts, skill files, handoff docs
**Remote (EC2):** TrigunAI-Omniverse g5.2xlarge — Docker services, GPU training, rendering

```
Mac (you're here)                          EC2 (TrigunAI-Omniverse, us-east-1)
┌──────────────────────┐                   ┌──────────────────────────────────┐
│ NvidiaSimSetup/      │    SSH / SCP      │ Docker containers:               │
│ ├── asset-studio/    │◄─────────────────►│ ├── litellm-proxy (:4000)        │
│ ├── webxr-showcase/  │                   │ ├── material-agent (:8000)       │
│ ├── cinematography/  │                   │ ├── ovrtx-rendering (:8001)      │
│ ├── lower_body_phys/ │                   │ ├── physics-agent (:8002)        │
│ ├── scene_composer/  │                   │ ├── physics-ovrtx (:8003)        │
│ ├── robotics_teleop/ │                   │ ├── texture-agent (:8004)        │
│ ├── mocap_handoff/   │                   │ ├── scene-composer (:8005)       │
│ ├── drone_handoff/   │                   │ ├── isaaclab (training)          │
│ ├── project_hub/     │                   │ └── nginx (:8080) + cloudflared  │
│ └── checkpoints/     │                   │                                  │
└──────────────────────┘                   │ /home/ubuntu/ — EBS persistent   │
                                           │ /tmp/ — ⚠️ EPHEMERAL            │
                                           └──────────────────────────────────┘
```

---

## The repo — everything you can touch

### 1. Asset Studio (`asset-studio/`)

React + Vite desktop app. Drives NVIDIA Content Agents (material, physics, texture) via
SSH tunnel to EC2.

| Tech | Details |
|---|---|
| Stack | React 18, Vite, TypeScript, R3F (@react-three/fiber) |
| Dev server | `npm run dev` → `localhost:5173` |
| SSH tunnel | `npm run tunnel` → forwards :8000/:8002/:8004 to EC2 agents |
| Key files | `src/App.tsx`, `src/api/agents.ts`, `src/components/Viewport.tsx` |

**Validated agents:** Material (cube + Franka), Physics (cube), Texture (cube PBR maps).

### 2. WebXR Showcase (`webxr-showcase/`)

React + R3F + `@react-three/xr` Quest 3 app. Browser-based VR (no Unity, no APK).

| Tech | Details |
|---|---|
| Stack | React 18, Vite, TypeScript, R3F, @react-three/xr v6.6, Zustand |
| Build + deploy | `./scripts/deploy_to_ec2.sh` (rsync to `/var/www/showcase/`) |
| Public URL | `./scripts/start_tunnel.sh` → Cloudflare quick tunnel (random URL, flaky) |
| Manifest | `public/assets/manifest.json` — lists showcases with `glbUrl` |
| Key files | `src/components/ShowcaseModel.tsx` (auto-fits Box3), `src/components/Scene.tsx` |

**Content on EC2:** Ragnarok (182MB, flat white materials), Isaac Warehouse (569MB, full PBR).

### 3. Cinematography Pipeline (`cinematography/`)

Python scripts for the drone camera training → rendering → delivery pipeline.

| Script | What it does |
|---|---|
| `parse_pose_bin.py` | Quest mocap parser (v1: 33 joints, v2: 84 joints) |
| `bake_dancer_usda.py` | Mocap → animated USDA (stick-figure dancer + orbital camera) |
| `render_dancer_mp4.py` | USDA → OVRTX batches → ffmpeg → MP4 |
| `render_trained_cinematographer.py` | Trained trajectory → USDA → OVRTX → MP4 (drone-POV + overhead modes) |
| `export_cinematographer_trajectory.py` | Trained policy rollout → JSON (runs inside isaaclab container) |
| `cinematographer_env.py` | Isaac Lab DirectRLEnv for drone filming |
| `cinematographer_env_cfg.py` | Env config (Starling 2, rewards) |

### 4. Scene Composer Service (`scene_composer_service/`)

FastAPI service wrapping OSM → textured city USD pipeline.

| Tech | Details |
|---|---|
| Stack | Python, FastAPI, Docker |
| Port | :8005 on EC2 |
| Pipeline | `osm_to_usd.py` → `city_add_colliders.py` → `city_enrich_textures.py` |
| API | `/pipeline` POST + `/artifacts/{sid}/*` GET (same contract as NVIDIA agents) |

### 5. Mocap Handoff (`mocap_handoff/`)

Data pipeline from Quest VR recordings to training-ready formats.

| Script | What it does |
|---|---|
| `pose_bin_to_amp_motion.py` | v1 (33-joint) Quest → Isaac AMP npz |
| `pose_bin_to_amp_motion_v2.py` | v2 (84-joint) Quest → Isaac AMP npz |
| `add_music_features_to_npz.py` | Extracts 9 audio features from MP3, appends to npz |
| `bake_daphne_animation.py` | AMP npz → Daphne CC4 character GLB (Blender headless) |
| `predictor/predict_lower_body.py` | IK-based standing-pose leg filler (being replaced by LB physics) |

### 6. Drone Handoff (`drone_handoff/`)

Artifacts + handoff docs for the VR agent (GurulokInnerJourney Unity integration).

### 7. Robotics Teleop (`robotics_teleop/`)

Quest 3 → robot teleoperation B2B. Currently paused. See `ROBOTICS_CLAUDE.md`.

### 8. Lower Body Physics (`lower_body_physics/`)

Isaac Lab AMP env for physics-based leg prediction. Architecture designed, not started.
Skill: `trigunai-lower-body-physics` for deep work.

### 9. Project Hub (`project_hub/`)

CEO briefing, cross-agent feedback, artifact registry, data inventory, gate log.
Skill: `trigunai-project-hub` for hub management.

---

## EC2 — critical infrastructure

### SSH access

```bash
EC2_IP=<check AWS console — changes on every stop/start>
PEM=~/.ssh/trigunai_key.pem
ssh -i $PEM ubuntu@$EC2_IP
```

Instance: `TrigunAI-Omniverse` (i-047ebf759f2386e71), g5.2xlarge, us-east-1
GPU: NVIDIA A10G, 24 GB VRAM · 8 vCPUs · 30 GB RAM · 200 GiB EBS

### Docker services (all auto-start on boot)

| Port | Container | Purpose |
|---|---|---|
| 4000 | `litellm-proxy` | Azure OpenAI proxy. Master key: `sk-trigunai-master-key-2026` |
| 8000 | `material-agent-service` | NVIDIA Material Agent |
| 8001 | `ovrtx-rendering-api` | OVRTX renderer (shared by agents + video pipeline) |
| 8002 | `physics-agent-service` | NVIDIA Physics Agent |
| 8003 | `physics-ovrtx-rendering-api` | OVRTX for Physics |
| 8004 | `texture-agent-service` | NVIDIA Texture Agent |
| 8005 | `scene-composer-service` | TrigunAI scene composer |
| 8080 | nginx (host) | WebXR app + GLB assets |

OVRTX cold start: **6 minutes** for `gpu_initialized: true`.

### isaaclab container (does NOT auto-start)

```bash
sudo docker start isaaclab    # manual start required after EC2 boot
sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && ..."
```

Isaac Sim 6.0.0-rc.22, Isaac Lab 3.0. All training happens here.

### NVIDIA Content Agent patches

Three `# TRIGUNAI PATCH` blocks in agent source — required for Azure OpenAI compatibility:
- `material_agent_service/.../pipeline_router.py` — injects api_key + base_url
- `physics_agent_service/.../pipeline_router.py` — same, both top-level and per-step
- `texture_agent/.../texture_generation.py` — pulls image-gen creds from env

Restart agents with `--env-file ../../.env` always:
```bash
cd ~/content-agents/apps/<agent>_service
docker compose --env-file ../../.env up -d
```

### Blender 4.5 LTS

Installed at `/opt/blender45`, symlinked as `blender45`. Has USD support (system Blender 4.0 does NOT).

```bash
blender45 --background --python /path/to/script.py -- --input X --output Y
```

Key conversion script: `webxr-showcase/scripts/usd_to_glb.py` (supports `--animated` for NLA strips).

---

## Coordinate systems (always relevant)

| System | Hand | Up | Position transform | Quaternion transform |
|---|---|---|---|---|
| Unity (Quest mocap) | Left | Y | identity | (x,y,z,w) |
| USD (OVRTX render) | Right | Y | Z-negate: (x,y,-z) | (x,y,-z,w) |
| Isaac Sim (training) | Right | Z | Y↔Z swap: (x,z,y) | (x,z,y,w) |
| glTF (delivery) | Right | Y | same as USD | same as USD |
| Isaac → USD | — | — | (x,y,z)→(x,z,-y) | (qw,qx,qy,qz)→(qw,qx,qz,-qy) |

---

## Video rendering

**Read `VIDEO_RENDERING.md` (repo root) for the full reference.**

**PREFERRED: Blender EEVEE** — 0.33 s/frame on A10G (18x faster than OVRTX). Renders directly
on the GPU with zero HTTP overhead.

```bash
blender45 --background --python /home/ubuntu/render_blender_drone_pov.py -- \
  --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
  --trajectory /tmp/cinematographer_v4_trajectory.json \
  --out /home/ubuntu/output.mp4 --engine eevee --width 1280 --height 720
```

**LEGACY: OVRTX API** (6 s/frame, port 8001) — Only use for NVIDIA MDL material shading.
Pattern: Base64-encode USDA → POST `/render` → batch 50 frames max → decode PNG → ffmpeg.

**Light syntax:** `float inputs:intensity` (NOT `float intensity`)
**Camera rotation:** `rx = atan2(dy, horiz)` — positive = look up, negative = look down

---

## Common operations

### Deploy WebXR to EC2
```bash
cd webxr-showcase && EC2_IP=$EC2_IP ./scripts/deploy_to_ec2.sh
```

### Start Cloudflare tunnel
```bash
EC2_IP=$EC2_IP ./scripts/start_tunnel.sh   # prints random *.trycloudflare.com URL
```

### Convert USD → GLB
```bash
ssh -i $PEM ubuntu@$EC2_IP 'blender45 --background --python /home/ubuntu/usd_to_glb.py -- \
  --input /path/to/scene.usd --output /path/to/output.glb --decimate 0.4 --max-texture 1024'
sudo chmod 644 /var/www/showcase/assets/*.glb
```

### Render video from USDA
```bash
ssh -i $PEM ubuntu@$EC2_IP 'python3 /home/ubuntu/render_trained_cinematographer.py \
  --trajectory /home/ubuntu/trajectory.json --out /home/ubuntu/output.mp4 \
  --fps 30 --width 800 --height 450 --batch-size 30'
```

### Train in Isaac Lab
```bash
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
  ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
  --task <TASK> --num_envs 256 --max_iterations 500 --headless > /tmp/train.log 2>&1"'
```

### Check OVRTX health
```bash
ssh -i $PEM ubuntu@$EC2_IP 'curl -s localhost:8001/health | python3 -m json.tool'
```

### Rescue /tmp before EC2 stop
```bash
ssh -i $PEM ubuntu@$EC2_IP 'for f in /tmp/*.json /tmp/*.npz /tmp/*.mp4 /tmp/*.usd*; do
  [ -f "$f" ] && [ ! -f "/home/ubuntu/$(basename $f)" ] && cp "$f" /home/ubuntu/ && echo "Saved: $f"
done'
```

---

## Gotchas accumulated across all sessions

| Symptom | Cause | Fix |
|---|---|---|
| Blank OVRTX frames | Missing `defaultPrim`, `upAxis`, `metersPerUnit` in USDA | Add all three (match `bake_dancer_usda.py` format) |
| Dark OVRTX scene | `float intensity` instead of `float inputs:intensity` | Use `inputs:intensity` |
| Camera pointing at sky | `rx = atan2(-dy, horiz)` gives wrong sign | Use `rx = atan2(dy, horiz)` |
| OVRTX returns blank after many renders | Daemon state corruption | `docker restart ovrtx-rendering-api` (6 min cold start) |
| OVRTX timeout | >150 frames in one POST | Batch in 30-frame chunks |
| GLB 403 from nginx | File written with 0600 perms | `sudo chmod 644 *.glb` |
| `rsync --delete` wipes GLBs | Deploy script deletes unmatched files | Exclude `*.glb,*.gltf,*.usd*,*.ktx2,*.bin` |
| Cloudflare tunnel 530 error | Free quick-tunnel disconnected | Re-run `start_tunnel.sh` for new URL |
| Public IP changed | EC2 stopped and started | Check AWS console, update `$EC2_IP` |
| `/tmp` files gone | EC2 stopped | Restore from `/home/ubuntu/` backups |
| Isaac Lab `--video` black/crash | Driver 595 + viewport widget incompatibility | Use OVRTX pipeline instead |
| `warp.array` indexing fails | Isaac Lab 3.0 returns wp.array not torch | Use polymorphic `_to_list()` with `.numpy()` fallback |
| Quest app permissions | File input on `<input type="file">` | Use hidden refs, not clicks |
| PhysX OOM on humanoid | >512 envs on A10G | Use 256 envs, `gpu_found_lost_pairs_capacity = 2^26` |

---

## Project Hub protocol

At **session end**, update the hub:
1. Update your workstream row in `project_hub/CEO_BRIEFING.md`
2. Write feedback to `project_hub/feedback/` if you produced deliverables
3. Update `project_hub/ARTIFACT_REGISTRY.md` with any new files
4. Update `project_hub/DATA_INVENTORY.md` if you moved files on EC2

---

## When to hand off to specialized agents

| If you're deep in... | Hand off to |
|---|---|
| Mocap parsing, PPO reward design, USDA baking, trajectory export | `trigunai-training` |
| Isaac Lab AMP humanoid, DOF decomposition, PhysX lower body | `trigunai-lower-body-physics` |
| Unity, Quest APK, GurulokInnerJourney, VR mocap recording | `trigunai-vr` |
| Handoff doc generation, phase gate evaluation | `trigunai-orchestrator` |
| CEO decisions, external comms, grants, wedge validation | `trigunai-ceo` |
| Status updates, artifact tracking, cross-agent feedback | `trigunai-project-hub` |

Stay in `trigunai-dev` for everything else — cross-system features, infra, debugging,
new services, frontend work, deployment, and anything that touches multiple domains.
