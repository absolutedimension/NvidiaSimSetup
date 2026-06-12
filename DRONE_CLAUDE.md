# Drone Training — Standalone Session Handoff

**Read this first. Everything you need to resume the drone work is in this file or referenced from it.**

This is a **separate session focus** from the music→character-animation work happening in `CLAUDE.md` §19. Don't touch the dance/AMP work; this session is **drone only**.

---

## 1. The 60-second context

**Project goal:** Train a Crazyflie 2.X quadcopter to autonomously fly from Point A → Point B in a real city, then export the trajectory as an animated GLB that plays in WebXR (Quest 3) and any browser.

**Current state (as of 2026-05-19):**
- Phase 6a complete: trained in **NVIDIA Rivermark DRIVE Sim city**, reward **725** (5.5× hover baseline), drone traversed **0→115 m forward**
- Animated GLB exported: `drone_handoff/cf2x_city_a2b.glb` (250 KB) — *but has a rotation bug in WebXR (drone shown sideways)*
- All training infra on EC2 is persisted on EBS; instance is currently **stopped**
- Phase 2 hover-only GLB (`drone_handoff/cf2x_trained.glb`) shipped successfully and is visible in WebXR

**One-line problem:** Phase 6a's trained-in-city policy is real and working, the trajectory data is real, the rendering pipeline is real — **the only thing blocking ship is the GLB's orientation in WebXR**.

---

## 2. What's already built (do NOT redo)

| Component | Path | Status |
|---|---|---|
| Forked AMP env for A→B navigation in city | `/workspace/isaaclab/.../direct/quadcopter_city_a2b/` (in container, on EBS) | ✅ Works. Has all 4 surgical overrides (city scene, A=(0,0,30) → B=(100,0,30), progress + arrival reward, no `z>2.0` kill) |
| Trained checkpoint | EC2: `/workspace/isaaclab/logs/rl_games/quadcopter_direct/<latest>/` | ✅ Saved on EBS, persists across stop |
| Crazyflie USD asset | EC2: `/home/ubuntu/assets/Crazyflie/cf2x.usd` (EBS-persistent) AND `/tmp/cf2x.usd` (volatile) | ⚠ /tmp wiped on stop — re-copy from /home/ubuntu/assets at session start |
| Rivermark city USD | `/workspace/isaaclab/source/.../city/Rivermark/` (in container) | ✅ 11 GB, 12,125 meshes, ~2.3 × 2.7 km, Z-up |
| Trajectory export script | `webxr-showcase/scripts/export_drone_trajectory.py` | ✅ Runs play.py with `--num_envs 1`, loads checkpoint via rl_games Runner, steps env, captures `robot.data.root_pos_w[0]` + `root_quat_w[0]` per step → JSON |
| Render pipeline | `webxr-showcase/scripts/render_drone_demo.py` | ✅ Bakes animated USDA → sends to OVRTX → returns PNGs → ffmpeg → MP4. Has `--minimal-usda` (for GLB export), `--evaluate` (chains VLM critic), `--trajectory JSON_PATH`. Auto-frames camera from trajectory bounds |
| VLM critic | `webxr-showcase/scripts/evaluate_drone_trajectory.py` | ✅ Extracts 6 keyframes via ffmpeg, stitches 2×3 grid, base64-encodes, POSTs to LiteLLM proxy at `localhost:4000` with gpt-4o-mini. Returns `{reach, smoothness, stability, efficiency, overall, issues, verdict}` |
| USD → GLB converter | `webxr-showcase/scripts/usd_to_glb.py` (with `--animated` flag) | ✅ Pushes Blender actions to NLA strips, exports with `export_animation_mode="NLA_TRACKS"` |
| Phase 2 GLB (hover, ships) | `drone_handoff/cf2x_trained.glb` (local, 250 KB) | ✅ VLM ship-it 8/10 |
| Phase 6a GLB (city, rotation bug) | `drone_handoff/cf2x_city_a2b.glb` (local, 250 KB) | ⚠ Rotation bug in WebXR |
| WebXR app | `webxr-showcase/` | ✅ Live, served from EC2 nginx → cloudflared tunnel |

---

## 3. The single open bug — RESOLVED 2026-05-20

**Status:** fixed. The real bug was NOT the rotation track itself; it was the **entire USDA → GLB pipeline silently dropping all animation**, with the visible-tilt symptom being two separate issues stacking:

1. **All shipping "animated" GLBs were actually static.** Both `cf2x_trained.glb` and `cf2x_city_a2b.glb` had `animations: []` in their glTF — `push_actions_to_nla()` always found zero actions because Blender 4.5's USD importer does **not** translate `xformOp:*.timeSamples` into Blender actions/F-curves. The hover GLB looked OK only because its static frame-0 pose happened to land upright; the city GLB's frame-0 pose landed tilted ~86° about X.
2. **The drone's parent Xform got a Transform Cache constraint.** What Blender's USD importer *does* do with time samples is attach a `Transform Cache` constraint (pointing at `bpy.data.cache_files['...usda']`) to the imported Empty. The constraint evaluates time-sampled transforms per frame *after* F-curves, so naively adding F-curves does nothing — the cache constraint wins. Removing the constraint is required before F-curves take effect.

**The fix (in `webxr-showcase/scripts/usd_to_glb.py`):**
- New `--inject-trajectory PATH` CLI flag — reads the raw Isaac-Z-up trajectory JSON (same one used by `export_drone_trajectory.py`) and writes `location` + `rotation_quaternion` F-curves directly onto the named Empty (default `Drone`).
- Before writing F-curves, walks `obj.constraints` and removes any `TRANSFORM_CACHE` constraint.
- Blender's `export_yup=True` then correctly converts the F-curve track from Z-up to Y-up via basis conjugation `(w, x, y, z) → (w, x, z, -y)` for quaternions and `(x, y, z) → (x, z, -y)` for positions. Verified numerically against the Isaac frame-0 quat.

**Pipeline (canonical) for the WebXR ship path:**
```bash
# 1. Bake USDA referencing the real Crazyflie asset (USDA still needed for OVRTX render path)
python3 render_drone_demo.py \
  --trajectory drone_city_trajectory.json --out /tmp/_ignored.mp4 \
  --skip-render --minimal-usda --keep-usda \
  --drone-asset /tmp/cf2x.usd

# 2. Convert USDA → animated GLB. Crucial: --inject-trajectory and chmod 644 on the asset file
sudo chmod 644 /tmp/cf2x.usd /tmp/cf2x_robot_schema.usd   # root-owned after `docker cp` from container; Blender silently fails the reference otherwise
/opt/blender45/blender --background --python usd_to_glb.py -- \
  --input  /tmp/cf2x_city_a2b.usda \
  --output /tmp/cf2x_city_a2b.glb \
  --inject-trajectory /tmp/drone_city_trajectory.json
```

**Verified output (v6 GLB on the box, deployed to nginx at `cf2x_city_a2b_v6.glb`):**
- `animations: 1` with 2 channels (translation + rotation), 360 keyframes
- Rotation samples are the basis-conjugated Isaac values, not the static frame-0 pose
- Blender-rendered stills at frames 0/180/359 show the drone in real trained-policy orientations (aggressive banking mid-flight is the policy's behavior, not a pipeline artifact)

**Pre-existing Blender ≠ system Blender — DO NOT use `/usr/bin/blender`** (4.0.2, no USD support compiled in). The right binary is `/opt/blender45/blender` (4.5 LTS).

---

## 4. EC2 infrastructure (current state)

### 4a. Primary: `TrigunAI-Omniverse` (us-east-1)
- **Instance ID**: `i-047ebf759f2386e71`, g5.2xlarge with NVIDIA A10G (23 GB VRAM, 31 GB RAM, 193 GB EBS root)
- **AMI**: NVIDIA GPU Cloud VM Base 2026.4.1 (`ami-059e868ce2e616dab`)
- **Container**: `isaaclab-v2:custom` running Isaac Sim 6.0 + Isaac Lab 3.0, configured to `sleep infinity` so it doesn't exit
- **Status**: stopped between sessions. New public IP on start.
- **Key**: `/tmp/trigunai_key.pem` (symlinked from `~/Library/Mobile Documents/com~apple~CloudDocs/TrigunSAI/trigunai_key.pem`)
- **Most recent IP (varies)**: `54.162.225.64` (2026-05-23 evening)
- **Use for**: drone training (Phase 6a checkpoint + Tier 2 future training), Rivermark decimation, OVRTX renders, Blender renders
- **Persistent assets on EBS** (survive stop/start, do NOT depend on /tmp):
  - `/opt/blender45/blender` — Blender 4.5.5 LTS
  - `/var/www/showcase/assets/rivermark_lite.glb` — 640 MB decimated Rivermark (7.25M tris)
  - `/var/www/showcase/assets/cf2x_city_a2b_v7.glb` — 264 KB animated drone (360 frames, trained-policy F-curves)
  - `/home/ubuntu/cf2x.usd` — Crazyflie USD (also at `/home/ubuntu/assets/Crazyflie/`)
  - `/home/ubuntu/assets/Rivermark/` — full 11 GB Rivermark USD source

### 4b. Secondary: `deepak-mumbai-server` (ap-south-1 Mumbai)
- **Instance ID**: `i-09e1596cbfd080b91`, g5.2xlarge, A10G, **500 GB EBS root**
- **AMI**: NVIDIA GPU Cloud VM Base 2026.4.1 (same as us-east-1)
- **SG**: `trigunai-mumbai-deepak-sg` (sg-03ab8294a471566ae) — SSH + CloudXR ports (TCP/UDP 47998-48000, 48010, 49100, UDP 49100-49200) all from My IP
- **Key**: `/Users/deepakkumarrai/Downloads/deepak-mum-key.pem` ⚠️ EXPOSED in 2026-05-23 transcript — rotate before next use
- **Status**: stopped between sessions, sometimes hung from OOM (reboot from AWS console if SSH timeouts)
- **What's installed on this box (per 2026-05-23 session)**:
  - **Proprietary NVIDIA driver 595.71.05** (swapped from open kernel module 595.58.03 via apt unhold + pin-file workaround + version pinning, see gotcha §8 #18)
  - 16 GB swap at `/swapfile`, persistent in `/etc/fstab`
  - `/opt/cloudxr/` — CloudXR Runtime 6.2.0 + registered at `/etc/xdg/openxr/1/active_runtime.json`
  - NGC CLI configured with a Personal Key (key was rotated 2026-05-23)
  - `nvcr.io/nvidia/omniverse/ov-kit-kernel:106.5.0` + `:106.4.0-release.156974` Docker images pulled
  - Blender NOT installed by default; install via `wget https://download.blender.org/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz` + extract to `/opt/blender45/`
- **Use for**: future Omniverse work once Enterprise eval lands; CloudXR streaming experiments
- **NOT currently usable for**: production rendering (NVIDIA gates headless RTX behind Omniverse Enterprise — see §13 below)

### 4c. Hyderabad (ap-south-2): quota approved but no GPU instances
- **Status**: G/VT quota approved (L-DB2E81BA, 8 vCPU), but `aws ec2 describe-instance-type-offerings --region ap-south-2` returns ZERO G-family instances in this region as of 2026-05-23. The quota is hypothetical until AWS expands GPU offerings to Hyderabad.

### Running services on `TrigunAI-Omniverse` (us-east-1, auto-start with container/docker)
- `litellm-proxy` on port 4000 — routes to Azure gpt-4o-mini for VLM critic
- `ovrtx-rendering-api` on port 8001 — OVRTX USD → MP4 rendering
- `material-agent-service`, `physics-agent-service`, `texture-agent-service`, `physics-ovrtx-rendering-api` — Content Agents (not used by drone work directly)
- `nginx` on port 8080 — serves WebXR app from `/var/www/showcase/`

Container `isaaclab` does NOT auto-start; you must `sudo docker start isaaclab` after EC2 starts.

---

## 5. Resume sequence (do this every session)

```bash
# 1. Start EC2 (or verify it's running) → get the new public IP from AWS console
EC2_IP=<new IP>

# 2. Quick connectivity check
ssh -o StrictHostKeyChecking=no -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'uptime'

# 3. Start the isaaclab container (auto-starts agents; isaaclab does not)
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 4. CRITICAL: re-copy Crazyflie USD from EBS-persistent path to /tmp (wiped on stop)
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP '\
  sudo docker cp isaaclab:/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/cf2x.usd /tmp/cf2x.usd && \
  sudo docker cp isaaclab:/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd'

# 5. Verify everything is up
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'sudo docker ps --format "table {{.Names}}\t{{.Status}}"'
# Should show: isaaclab, ovrtx-rendering-api, litellm-proxy, etc. all Up

# 6. (Optional) start cloudflared tunnel for WebXR public access
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'pkill cloudflared 2>/dev/null; \
  nohup cloudflared tunnel --url http://localhost:8080 --no-autoupdate > /tmp/tunnel.log 2>&1 &' && \
  sleep 8 && \
  ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/tunnel.log | head -1'
```

---

## 6. The canonical training/render/evaluate loop

(All scripts live in `webxr-showcase/scripts/`. scp them to EC2 before running, or run via `sudo docker exec isaaclab ...` if already in container.)

```bash
# 1. TRAIN (if continuing or running a new experiment)
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
     --task Isaac-Quadcopter-City-A2B-Direct-v0 \
     --num_envs 4096 --max_iterations 500 --headless \
     > /tmp/quad_train.log 2>&1"'
# 4096 envs → batch_size 24576. Yaml is at agents/rl_games_ppo_cfg.yaml
# (note: NOT --algorithm AMP — this is pure PPO via rl_games, not skrl)

# 2. EXPORT TRAJECTORY
scp -i /tmp/trigunai_key.pem webxr-showcase/scripts/export_drone_trajectory.py ubuntu@$EC2_IP:/tmp/
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p /tmp/export_drone_trajectory.py \
     --checkpoint /workspace/isaaclab/logs/rl_games/quadcopter_direct/<run>/nn/best.pth \
     --steps 600 --out /tmp/city_trajectory.json"'
scp -i /tmp/trigunai_key.pem ubuntu@$EC2_IP:/tmp/city_trajectory.json .

# 3. RENDER (animated USDA + MP4 via OVRTX, then convert to GLB)
scp -i /tmp/trigunai_key.pem webxr-showcase/scripts/render_drone_demo.py ubuntu@$EC2_IP:/tmp/
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p /tmp/render_drone_demo.py \
     --trajectory /tmp/city_trajectory.json \
     --out /tmp/cf2x_city_a2b.usda \
     --minimal-usda --evaluate"'

# 4. CONVERT USDA → GLB (animated, NLA strips for Unity/Three.js)
scp -i /tmp/trigunai_key.pem ubuntu@$EC2_IP:/tmp/cf2x_city_a2b.usda .
blender --background --python webxr-showcase/scripts/usd_to_glb.py -- \
  --input cf2x_city_a2b.usda --output drone_handoff/cf2x_city_a2b.glb --animated

# 5. DEPLOY to WebXR
scp -i /tmp/trigunai_key.pem drone_handoff/cf2x_city_a2b.glb \
  ubuntu@$EC2_IP:/var/www/showcase/assets/cf2x_city_a2b.glb
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo chmod 644 /var/www/showcase/assets/cf2x_city_a2b.glb'
# Visit the cloudflared URL, select "City Drone" showcase
```

---

## 7. The environment fork (for reference — already in container)

`/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_city_a2b/quadcopter_city_a2b_env.py` has 4 surgical overrides on top of the stock `QuadcopterEnv`:

1. **`_setup_scene`** — references Rivermark city + strips RigidBodyAPI / CollisionAPI / MassAPI / MeshCollisionAPI from /World/City prims (PhysX silent death fix at scale)
2. **`_reset_idx`** — locks goal to B=(100,0,30), spawns drone at A=(0,0,30)
3. **`_get_rewards`** — replaces parent's saturating `tanh(d/0.8)` with `1 - tanh(d/100)` + progress reward (delta-distance × 5.0) + arrival bonus (+50 when within 2m)
4. **`_get_dones`** — removes parent's `z > 2.0` insta-kill (it was killing the drone instantly at z=30 spawn). Uses `z < 0.5 OR z > 100` instead.

Plus a lazy-init pattern in `_reset_idx` for the new reward keys (`progress`, `arrived`) since they didn't exist in the parent's `_episode_sums` dict.

---

## 8. Critical gotchas (lessons from earlier sessions, do NOT re-learn)

1. **`/tmp/cf2x.usd` is wiped on EC2 stop.** Always re-copy from `/home/ubuntu/assets/Crazyflie/cf2x.usd` (EBS-persistent) at session start. The OVRTX container only mounts `/tmp → /host_tmp` so this matters for rendering.

2. **`isaaclab` container CMD is `[/bin/sleep] [infinity]`.** Do NOT override with `--entrypoint` or `cmd` args on `docker start`. Just `sudo docker start isaaclab`.

3. **rl_games requires `batch_size % minibatch_size == 0`.** With `num_envs=4`, the yaml's default minibatch causes AssertionError. Use `num_envs=1024` or `4096` (yaml's defaults work).

4. **rl_games log dir is named `quadcopter_direct` not `quadcopter_city_a2b_direct`.** The dir name comes from `config.name` inside the PPO yaml, not from the env task name. Confused me for an hour.

5. **PhysX silent death on city RigidBody props with `replicate_physics=True`.** DRIVE Sim USD has RigidBodyAPI on building props. With 1024+ envs PhysX hangs/dies silently. Strip the APIs in `_setup_scene` — already done in the env fork.

6. **Drone dies instantly at `z=30` spawn** under stock `_get_dones` (`died = z > 2.0`). The override is in the fork — don't accidentally regress.

7. **Reward saturated at distance > 2m.** Parent's `tanh(d/0.8)` is flat past 2m so the policy gets no gradient toward the goal once it's any distance away. Fixed with `tanh(d/100)` + progress reward. **Do not undo.**

8. **KeyError in `_episode_sums`** for new reward keys ("progress", "arrived") — they don't exist in the parent dict. Fixed with lazy-init: `if key not in self._episode_sums: self._episode_sums[key] = torch.zeros_like(value)`.

9. **VLM hallucinated 8/10 on blank scene.** gpt-4o-mini will default to neutral-positive when it can't see the drone. The prompt in `evaluate_drone_trajectory.py` has a CRITICAL visibility check now that demands `verdict="broken"` if drone isn't visible. **Don't remove that.**

10. **VLM false-negative on drone vs black background.** My initial visibility check was too strict (demanded floor + markers visible too). The relaxed prompt grades drone visibility alone. Do not over-tighten.

11. **Auto-frame camera 190m from drone → 2px drone in 640x360 video.** Fix is in `render_drone_demo.py`: subsample trajectory + bump `drone_scale` to 50. Auto-framing formula: `cam_z = cz + max(span*1.4, 6.0)`.

12. **OVRTX chokes on 360-frame single request.** Subsample to ≤60 frames per render call. Loop if needed.

13. **ffmpeg seek fails at EOF for low-fps videos.** Use output-seek (`-ss` after `-i`) and limit last keyframe to 95% of duration.

14. **SSH connection drops on long-running commands.** Use `tmux new-session -d -s tunnel` (or background via `sudo docker exec -d`) so commands survive disconnects.

15. **Blender USD import does NOT create F-curve animation from `xformOp:*.timeSamples`.** It attaches a `Transform Cache` constraint on the imported Empty that reads time samples from `bpy.data.cache_files[...]` per-frame instead. Naively adding F-curves does nothing because the constraint evaluates *after* F-curves. To inject an animation cleanly, walk `obj.constraints` and remove every `TRANSFORM_CACHE` constraint *before* writing F-curves. (Codified in `usd_to_glb.py --inject-trajectory`.)

16. **Two Blenders on the EC2 host.** `/usr/bin/blender` (4.0.2) was packaged without USD support — `bpy.ops.wm.usd_import` is registered but errors with "could not be found" on call. Use **`/opt/blender45/blender`** (4.5.5 LTS) for any USD work.

17. **`/tmp/cf2x.usd` ends up root-owned after `docker cp`.** Blender (running as ubuntu) then silently fails to resolve `@references = @/tmp/cf2x.usd@` from a USDA — geometry is dropped, no error. Always `sudo chmod 644 /tmp/cf2x.usd /tmp/cf2x_robot_schema.usd` after the docker cp step in §5.

18. **NVIDIA driver swap on the GPU Cloud AMI is non-trivial.** The AMI ships `nvidia-driver-595-server-open` (open kernel module). The proprietary `nvidia-driver-595-server` is needed for Omniverse RTX rendering. Three obstacles when swapping (all hit on 2026-05-23 on Mumbai box):
   (a) Many `libnvidia-*-595-server` packages are HELD (`apt-mark showhold` → unhold first).
   (b) `/etc/apt/preferences.d/nvidia-cuda-repo-priority` pins all `nvidia-*` to `developer.download.nvidia.com` which ships open-only at 595.58.03; the proprietary 595.71.05 is in Ubuntu's `multiverse` archive but loses the pin contest.
   (c) Apt's resolver won't auto-upgrade the libs even with pin removed; needs explicit version pins on every package in the install command.
   Working recipe codified in `/tmp/swap_driver_v2.sh` (move pin file → preemptive purge of open kernel-source → `apt install` with `=595.71.05-0ubuntu0.24.04.1` on every package → restore pin → hold new packages → reboot).
   **Verify post-reboot**: `modinfo nvidia | grep license` should say `NVIDIA` (not `Dual MIT/GPL`).

19. **Headless RTX rendering with public `ov-kit-kernel` doesn't work.** `omni.hydra.rtx` crashes at init (within 400 ms) in `librtx.scenedb.plugin.so / carbOnPluginShutdown` regardless of:
   - Driver (tested both Open Kernel Module 595.58.03 and Proprietary 595.71.05)
   - Kit version (tested 106.4 and 106.5)
   - RTX flag combinations (tried `--/renderer/multiGpu/autoEnable=false`, `--/rtx/post/dlss/enabled=false`, several others)
   - `omni.hydra.pxr` (Storm) is the fallback but needs OpenGL interop which fails headless without an X server.
   **Root cause**: NVIDIA gates supported headless-RTX setups inside the **Omniverse Enterprise** containers (`omniverse/streaming`, `omniverse/usd-composer`) which require enterprise entitlement separate from NVAIE. The public ov-kit-kernel container is intentionally minimal.
   **Implication**: Phase 6a's MP4 render path (OVRTX) is the path of least resistance for cloud rendering; do NOT try to substitute Kit + RTX without Omniverse Enterprise access.

20. **Blender Cycles + rivermark_lite.glb (640 MB, 7.25M tris) OOMs g5.2xlarge** (32 GB RAM). Blender import alone consumes 12-16 GB; Cycles' BVH build pushes it over. Use **Eevee Next** instead — same Blender binary, GPU-accelerated, ~3-5× less memory. Confirmed working 2026-05-23 (5 smoke frames at 1280×720, ~12 GB RAM steady).

21. **NVAIE evaluation trial does NOT include Omniverse Enterprise.** Despite the registration page implying Omniverse is bundled, the actual entitlement (`NVAIE_Licensing-1.0`, 60 seats, 90-day) is only NVIDIA AI Enterprise licensing — it does NOT unlock the gated `nvidia/omniverse/usd-composer`, `nvidia/omniverse/streaming`, `nvidia/omniverse/usd-explorer`, `nvidia/omniverse/isaac-sim` containers (all still 403 after activation). Apply for Omniverse Enterprise separately if you need those.

---

## 9. Background context (read if you have time)

These files have the full historical narrative of how the drone work evolved. You don't need them to operate, but they're useful for understanding *why* things are the way they are.

| File | Purpose |
|---|---|
| `CLAUDE.md` §15–18 | Full project history: drone Phase 0–6a, all the rabbit holes (driver 595 incompatibility, AMI choice, the cf2x.usd ephemeral-wipe lesson) |
| `DRONE_TRAINING_STRATEGY.md` | The 6-phase roadmap as written before training started. Phases 0–6a are done. Phase 6b (rotation bug fix + WebXR ship) is the open work |
| `DRONE_PIPELINE_HANDOFF.md` | Handoff written to Avinash explaining the AWS quota issues and pipeline status before training |
| `~/Downloads/deepak_unblock_reply.md` | Avinash's solution recommendation that unblocked us (use TrigunAI-Omniverse box, not new mumbai box) |
| `~/Downloads/CLAUDE (2).md` | Snapshot of CLAUDE.md from earlier in this project; useful for context but **not authoritative** — current state is in this file + CLAUDE.md §15-18 |

---

## 10. What to do FIRST in this new session

> **As of 2026-05-23**: Phase 6a (Tier 0 — pipeline validation) is **complete**.
> The next legitimate workstream is **Tier 2: vision-based collision-avoiding navigation**.
> Full engineering plan is in **[DRONE_TIER2_ROADMAP.md](DRONE_TIER2_ROADMAP.md)** — read that first.

### A. (Recommended) Start Tier 2, Stage A: depth-camera vision-RL in a procedural 1-obstacle corridor

This is the smallest deliverable that proves the new vision + collision + reward + curriculum pipeline works end-to-end. Per the roadmap §10:

> **Week 1 target**: "In a procedural 1-obstacle corridor scene with collision physics enabled, train a vision-PPO policy that successfully avoids the obstacle ≥80% of the time over 100 evaluation episodes, with the depth-camera observation pipeline fully wired into the env."

Concrete first-day tasks (from roadmap §4 file-by-file list):

1. In the `isaaclab` container on us-east-1 (`TrigunAI-Omniverse`):
   - Fork `quadcopter_city_a2b_env.py` → `quadcopter_corridor_v1_env.py` for the new corridor task
   - Add a `CameraCfg` for forward-facing 84×84 depth on the Crazyflie body
   - Replace the Rivermark city reference with a procedural-obstacle scene generator (`scene_generators/procedural_obstacles.py` — needs to be written)
2. Write `network_vision_ppo.py` — custom `ModelA2CContinuousLogStd` with state MLP + tiny CNN
3. Update `agents/rl_games_ppo_cfg.yaml` to use the new network and reduce `num_envs` to 1024-2048 (vision-RL is GPU-VRAM-bound)
4. Add reward shaping for collision penalty + proximity penalty (roadmap §3.5)
5. Train, evaluate, hit ≥80% obstacle-avoidance success rate

Compute budget per roadmap §5: ~$5-10 of EC2 (Stage A only).

### B. Things from earlier roadmap that are now lower-priority

- **Random goals / start positions** (Tier 1) — useful but de-prioritized in favor of Tier 2's perception work, since Tier 2 already requires the vision pipeline and that's the bigger unlock.
- **Train longer at current single-goal task** — diminishing returns; the policy already converged. Not worth more iterations of the same task.
- **Sim-to-real on physical Crazyflie** (Tier 3) — deferred until Tier 2 has a checkpoint worth deploying.
- **WebXR / Quest streaming demos** — see §13 below for honest status. Blocked on NVIDIA Omniverse Enterprise gating until that lands.

---

## 11. What this session should NOT touch

- Anything in `mocap_handoff/` (dance/AMP work)
- Anything in `/workspace/isaaclab/.../humanoid_amp/` (in container)
- The patches to `motion_loader.py`, `humanoid_amp_env.py`, `humanoid_amp_env_cfg.py`
- Any `*music*` files
- Any `*daphne*` files
- The `gurulok_dance_v*.npz` files

Dance work has its own session/context. Stay in your lane.

---

## 12. Companion docs

- **[DRONE_TIER2_ROADMAP.md](DRONE_TIER2_ROADMAP.md)** — engineering plan for the next training workstream (vision-RL with collision avoidance). Hand to an engineer; it has file diffs, compute budget, acceptance criteria. **The primary next-session reading for new training work.**
- **[SHOWCASE_PIPELINE.md](SHOWCASE_PIPELINE.md)** — self-contained runbook to produce a polished MP4 of the Phase 6a drone flying through Rivermark city. Blender Eevee Next on us-east-1, ~1-2 hours end-to-end. **Use this when you want a visible deliverable for marketing / investors / landing page.**
- `DRONE_TRAINING_STRATEGY.md` — original 6-phase roadmap (phases 0-6a done; rest superseded by Tier 2 roadmap above)
- `DRONE_PIPELINE_HANDOFF.md` — historical pre-training handoff to Avinash
- `webxr-showcase/scripts/render_drone_demo.py` — OVRTX render path (used for Phase 6a baked MP4)
- `webxr-showcase/scripts/usd_to_glb.py` — USDA → animated GLB (the rotation-bug fix lives here, see §3)

---

## 13. Session log: 2026-05-23 (Saturday)

Long session focused on attempting "EC2 → Quest VR streaming" pipeline. Honest outcome: **infrastructure validated, supported path requires Omniverse Enterprise access we don't have**. Tier 2 training is now the clearer next workstream. Lessons documented in §8 gotchas 18-21.

What we attempted and learned:

| Attempt | Result |
|---|---|
| Mumbai EC2 g5.2xlarge launched (`deepak-mumbai-server`, ap-south-1) | ✅ Provisioned with proprietary driver, 16 GB swap, NGC CLI, Docker + GPU, CloudXR Runtime 6.2.0 |
| CloudXR Runtime install + OpenXR registration | ✅ Installed cleanly, registered as system OpenXR runtime |
| LÖVR + CloudXR build (smoke test for streaming) | ✅ Built successfully; ❌ Vulkan VK_ERROR_DEVICE_LOST during render on Xvfb (LÖVR needs real display) |
| NVAIE eval registration | ✅ Approved (90-day, 60 seats), but does NOT include Omniverse Enterprise containers (gotcha §8 #21) |
| NGC Personal Key issued | ✅ Works for Kit Kernel access; ❌ still 403 on `omniverse/usd-composer`, `omniverse/streaming`, `omniverse/usd-explorer`, `omniverse/isaac-sim` |
| Driver swap (open → proprietary on Mumbai) | ✅ Driver 595.58.03 (open) → 595.71.05 (proprietary), see gotcha §8 #18 |
| Kit Kernel headless boot (omni.app.empty.kit) | ✅ Cleanly boots, no crash |
| Kit + omni.hydra.rtx headless render | ❌ Plugin crashes at init regardless of driver/flags/version (gotcha §8 #19) |
| Kit + omni.hydra.pxr (Storm) headless render | ❌ Needs OpenGL interop, fails without X server |
| pip `usd-core` + usdrecord | ❌ usdrecord CLI not shipped in PyPI distribution |
| Blender Cycles + rivermark_lite.glb (Mumbai box) | ❌ OOM on 32 GB RAM (gotcha §8 #20) |
| **Blender Eevee Next + rivermark_lite.glb (us-east-1)** | **✅ Renders headless cleanly, 5 smoke frames at 1280×720, memory stable at ~12 GB.** Static camera at default position makes drone too small to see in frame — but the pipeline works. |

Bottom line: **the Blender Eevee path on `TrigunAI-Omniverse` (us-east-1) is the working render-to-MP4 pipeline for cloud rendering.** Set up a chase camera (Track-To constraint on Drone empty) to make the drone visible in frame. Render Tier 2 trajectories with this pipeline.

The "stream Rivermark to Quest in real time" goal is blocked behind Omniverse Enterprise gating until that eval lands. For now, the rendered MP4 path is the achievable output.

---

## 14. Session log: 2026-05-23 (later — Tier 2 Stage A scaffolding)

**Scope:** Started Tier 2 Stage A from `DRONE_TIER2_ROADMAP.md` §10. Wrote the full env + vision-PPO scaffolding, pushed to the `isaaclab` container, and ran a 16-env / 1-iter smoke test. **Smoke passed.** Full Stage A training run (task #10) is the next move.

### Code layout (source-of-truth = local Mac)

```
/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/stage_a/
  quadcopter_corridor_v1/
    __init__.py                          gym.register Isaac-Quadcopter-Corridor-V1-v0
    quadcopter_corridor_v1_env_cfg.py    env config + obstacle/camera/contact cfgs
    quadcopter_corridor_v1_env.py        env class (forks QuadcopterEnv)
    networks_vision.py                   skrl VisionPolicy + VisionValue (state MLP + 84x84 depth CNN)
    agents/__init__.py                   (marker, no yaml — PPO config is inline in train script)
    scripts/train_stage_a.py             train driver (skrl PPO + SequentialTrainer)
  reference/                             Phase 6a a2b source pulled for diff reference
  smoke4.log                             (when pulled — currently still in container)
```

In the container the same package lives at:
`/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_corridor_v1/`

### Design decisions (deviations from roadmap)

| Question | Roadmap said | Chose | Why |
|---|---|---|---|
| RL library | rl_games (§3.4 Option A — "continuity") | **skrl** | Phase 6a checkpoint isn't portable to vision (input shape changes). skrl's custom Model API is cleaner for state+CNN fusion. skrl is already wired into `__init__.py`. |
| `num_envs` for Stage A | 2048 | **512** (smoke at 16) | Vision + real-collision is new. Start small, scale after smoke passes. |
| Episode length | 15s | **20s** | Avoidance maneuvers cost time. |
| Obstacle | "randomize position" | x ∈ [25,75], y ∈ [-5,5], z=30, size 5×5×10, kinematic body | Stage A keeps a single box. Stages B/C will procedurally generate 10/100. |
| PPO config | yaml | **Embedded in train script as a dict** | Custom CNN+MLP Models can't be expressed via skrl's yaml-based model_instantiator. |

### Bugs caught by smoke (and fixed)

These are the gotchas to NOT re-hit in Stage B/C:

22. **`AppLauncher` has no `.device` attribute**. Use `args.device` (added automatically by `AppLauncher.add_app_launcher_args(parser)`). Old Isaac Lab API had `app_launcher.device`; current 3.0 has `device_id` (an int).

23. **ContactSensor fails with "could not find any bodies with contact reporter API"** unless the spawned articulation has `activate_contact_sensors=True` in its spawn cfg. For Crazyflie:
    ```python
    robot = CRAZYFLIE_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        spawn=CRAZYFLIE_CFG.spawn.replace(activate_contact_sensors=True),
    )
    ```

24. **`ContactSensor.data.net_forces_w` returns a `warp.array`, not `torch.Tensor`**. Same convention as `Articulation.data.*` — must `wp.to_torch(...)` before calling tensor methods like `.norm()`. Camera output (`distance_to_image_plane`) is sometimes already torch (when `enable_cameras=True` is set); normalize both with a helper:
    ```python
    def _as_torch(x):
        return x if isinstance(x, torch.Tensor) else wp.to_torch(x)
    ```

25. **`--headless` CLI arg is deprecated in current Isaac Lab.** Default is already headless when no `--viz` is passed. Use `--viz none` only when forcing headless against an enabled viz config.

### Smoke test result (smoke4)

- Cmd: `isaaclab.sh -p .../train_stage_a.py --num_envs 16 --iters 1`
- Wall time: ~2 min (Isaac Sim boot ~90s, training 27s)
- Throughput: **14 it/s @ 16 envs** = ~225 env-steps/s. With 32× more envs (512), expect 5-10k env-steps/s with sub-linear scaling.
- Checkpoints written at `/workspace/isaaclab/stage_a_runs/stage_a_corridor_v1/checkpoints/` (incl. `best_agent.pt`)
- All 7 reward terms wired (`lin_vel`, `ang_vel`, `distance_to_goal`, `progress`, `arrived`, `collision`, `proximity`)
- Policy + value: 175 k params each
- Observation: 12 state + 84×84 depth = 7068 flat floats per env, split inside `VisionPolicy.trunk`

### Next session: launch the full Stage A run

```bash
EC2=54.162.225.64
KEY=~/.ssh/trigunai_key.pem
ssh -i $KEY ubuntu@$EC2 '
sudo docker exec -d isaaclab bash -lc "
cd /workspace/isaaclab
nohup /workspace/isaaclab/isaaclab.sh -p \
  /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_corridor_v1/scripts/train_stage_a.py \
  --num_envs 512 --iters 1000 \
  > /workspace/isaaclab/stage_a_runs/full_run_1.log 2>&1 &
"
'
```

Estimated wall time: 30 min - 2 hr (depending on scaling efficiency). Cost: $2-10.

Acceptance criteria (`DRONE_TIER2_ROADMAP.md` §7 Stage A): **≥80% success / ≤10% collision over 100 eval episodes.**

---

---

## 15. Session log: 2026-05-23 (latest — Stage A full training + eval, FAILED acceptance, diagnosis below)

**Scope:** Ran the full Stage A training, evaluated, hit Isaac Lab renderer limits along the way, and got a clean diagnostic failure. Pipeline validated end-to-end. Policy did not learn to navigate.

### What ran

Three crashed attempts before a successful run, two crashed eval attempts before a successful one. Cost summary: ~$2 EC2 for ~1.5 hr of GPU time spread across the night.

| Attempt | num_envs | Outcome | Cost |
|---|---|---|---|
| full_run_1 | 512 | ❌ Vulkan descriptor sets exhausted ~camera 460 (`Unable to allocate descriptor sets`) | $0.40 |
| full_run_2 | 128 | ❌ RTX PerViewState pool exhausted at view 128 exactly (`Failed to allocate ProjectedAreaCullingData::PerViewState gpu slot`) | $0.10 |
| full_run_3 | 64 | killed for `total_timesteps` bug — wrong unit in skrl trainer cfg | $0.20 |
| **full_run_4** | **64** | **✅ Completed: 1000 iters × 24 horizon = 24,000 sim-steps in 1:01:38 at 6.49 it/s** | **$1.30** |
| eval_pass1 | 64 | ❌ device mismatch (model on CPU, tensors on cuda:0) | $0.05 |
| eval_pass2 | 64 | ❌ broadcast shape mismatch — `_collision_mask()` returns (N, N) outside env's own callbacks | $0.05 |
| **eval_pass3** | **64** | **✅ Completed: 64 episodes evaluated** | $0.05 |

### Renderer ceiling discoveries (NEW gotchas)

26. **Isaac Lab spawns one `Replicator` per camera at scene init.** Each Replicator is a full `omni.hydratexture` + viewport + runloop thread. Spawn cost is ~1 sec/camera serial. At 512 cameras you spend 10+ min in setup alone before any training, and you risk hitting Vulkan limits.

27. **Two distinct GPU resource ceilings cap multi-camera envs on an A10G:**
    - **PerViewState pool** caps at exactly **127 views** (kit log: `Failed to allocate ProjectedAreaCullingData::PerViewState gpu slot` fires on view 128). Smaller of the two.
    - **Vulkan descriptor sets** cap around **~460** (`Unable to allocate descriptor sets`). Hits later in the pipeline.
    - **Safe num_envs for camera-bearing direct envs on A10G: ≤96 (2× headroom under PerViewState cap), with 64 proven through full training.**

28. **skrl SequentialTrainer's `cfg["timesteps"]` is sim-steps, NOT env-steps.** One sim-step = all envs step in parallel. For 1000 PPO iters × 24-step rollouts, set `timesteps = 24_000`, NOT `iters * rollouts * num_envs`. Getting this wrong inflates ETA by num_envs× (we saw 65-hour ETA before fix; real wall time was 1 hour).

29. **skrl Model subclasses are not on GPU after `load_state_dict`.** The training-time PPO Agent moves models to device during agent init; an eval script that bypasses Agent setup needs explicit `.to(device)` after `load_state_dict`.

30. **`_collision_mask()` (or any env helper that returns (num_envs,)) can return higher-dim shapes (N, N) when called from outside the env's own step/reset callbacks.** Likely because some Isaac Lab buffers are double-batched in the wrapped path. Squeeze/reshape masks to `.view(-1)[:num_envs]` defensively in eval code.

### Training result

- Total wall time: 1:01:38 at steady 6.49 it/s
- Throughput: 416 env-steps/sec @ 64 envs (vs Phase 6a's ~6800 env-steps/sec @ 4096 envs without cameras)
- GPU stable at 7.9 GB / 14-17% util
- 10 periodic checkpoints saved + `best_agent.pt` at `/workspace/isaaclab/stage_a_runs/full_run_4_64envs/checkpoints/`
- **Tell-tale signal: `best_agent.pt` last updated at iter 500 / 12,000 sim-steps and did NOT improve for the remaining 500 iters.** The policy peaked early and either plateaued or regressed.

### Eval result — FAILED

```json
{
  "episodes_completed": 64,
  "successes": 0,         "success_rate": 0.0,    target ≥0.80 ❌
  "collisions": 16,       "collision_rate": 0.25, target ≤0.10 ❌
  "mean_final_distance_m": 100.0,
  "overall_pass": false
}
```

Local report: `stage_a/eval_pass3.json`. Container path: `/workspace/isaaclab/stage_a_runs/eval_pass3.json`.

### Diagnosis (high-confidence)

**`mean_final_distance_m: 100.0` is the smoking gun.** That's the exact A→B distance. The drone barely moves from spawn. 0 successes + 25% collisions + drone-stays-put = the policy converged to a degenerate **"hover near spawn"** strategy.

This is the curriculum-collapse failure mode that `DRONE_TIER2_ROADMAP.md` §6 risk #4 explicitly flagged: skipping the no-obstacle curriculum stage and going straight to "navigate around a randomly-placed box" is exactly what fails.

Why PPO got trapped:
- `collision_penalty = -50` is a large discrete punishment for moving wrong
- `proximity_penalty = -1 / min_depth²` produces continuous punishment for getting close to anything
- The `progress` reward (delta-distance per step) is small in absolute terms
- A naive policy that hovers at spawn earns a steady `distance_mapped` term (`1 - tanh(100/100) ≈ 0.24`) plus zero collision risk
- Exploration noise (entropy_coef=0) wasn't enough to break out of this attractor

The policy genuinely learned the wrong thing. More training would not fix it; more reward-shaping/curriculum would.

### What worked, what didn't

| Layer | Status |
|---|---|
| Env construction (corridor + obstacle + camera + contact sensor, all replicated 64×) | ✅ Working |
| Camera rendering (84×84 depth, NaN-safe) | ✅ Working |
| Contact sensor (kinematic box collision detection) | ✅ Working |
| Vision policy network (12-state MLP + 84×84 CNN, 175k params, fuses correctly) | ✅ Working |
| PPO training loop (skrl SequentialTrainer, 24-step rollouts, KL-adaptive LR) | ✅ Working |
| Checkpointing + best-agent tracking | ✅ Working |
| Eval harness (deterministic policy mean, per-episode success/collision tracking) | ✅ Working |
| **The trained policy navigates A→B** | **❌ Hover-at-spawn local optimum** |

### Next session plan — Stage A.0 curriculum

The user-approved next move is **stop here, document, hand off** for tonight. The unambiguous next-session priority is:

1. **Train a Stage A.0 "no-obstacle" baseline first.** Move the obstacle out of the corridor (e.g. `obstacle_y_range = (50.0, 60.0)` so it's never in the A→B path). Same env, same network, same hyperparams. Goal: confirm the drone can learn the basic A→B navigation given the vision policy. ~1 hr, ~$1.30. Expect success rate ≥80% — if THIS fails, the issue is bigger than reward shaping (probably the vision encoder isn't learning useful features at all).

2. **If A.0 passes:** load A.0 checkpoint as init, train Stage A (obstacle in path). Should adapt faster because the policy already knows how to fly toward B.

3. **If A.0 also fails:** debugging mode. Pull tensorboard, look at per-component reward curves, possibly drop to a state-only baseline (no vision) to confirm the base env reward shaping isn't broken.

4. **Independently of the above:** investigate whether 96 envs is actually safe (Roadmap §6 risk #1 territory). Current safe-band is 64; 96 might be safe-ish; would give us 50% more throughput.

### Concrete next-session launch command

```bash
# Train Stage A.0 (no-obstacle baseline) — edit env_cfg.py first to move obstacle off-path
EC2=54.162.225.64
KEY=~/.ssh/trigunai_key.pem

# 1. Edit obstacle_y_range to (50.0, 60.0) in quadcopter_corridor_v1_env_cfg.py
# 2. Push, then:
ssh -i $KEY ubuntu@$EC2 'sudo docker exec -d isaaclab bash -lc "
cd /workspace/isaaclab
nohup /workspace/isaaclab/isaaclab.sh -p \
  /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_corridor_v1/scripts/train_stage_a.py \
  --num_envs 64 --iters 1000 --experiment_name stage_a0_no_obstacle \
  > /workspace/isaaclab/stage_a_runs/stage_a0.log 2>&1 &
"'

# 3. Then eval:
# ... evaluate_stage_a.py --checkpoint /workspace/isaaclab/stage_a_runs/stage_a0_no_obstacle/checkpoints/best_agent.pt
```

### Cleanup owed

- **Stop the EC2 instance** from AWS console to halt the $1.30/hr meter — user's call.
- **Rotate SSH key** `deepak-mum-key.pem` — still exposed in transcript, still unrotated.

---

*Last updated: 2026-05-23 (session: Stage A pipeline validated end-to-end; policy training FAILED acceptance — hover-at-spawn local optimum diagnosed; curriculum approach required for next attempt).*
*Owner: TrigunAI Innovations / TrigunRoboticsLab (Deepak + Avinash).*
*Open work: Stage A.0 no-obstacle baseline → re-attempt Stage A with curriculum init → Stage B (see [DRONE_TIER2_ROADMAP.md](DRONE_TIER2_ROADMAP.md) §3.7).*
