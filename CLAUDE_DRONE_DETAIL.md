# Drone pipeline — full inline detail (archived from CLAUDE.md §17–18)

> Moved out of `CLAUDE.md` on 2026-07-30 to cut per-session reused-input cost.
> The authoritative, expanded drone doc is **`DRONE_CLAUDE.md`** (42KB). This file
> preserves the two anchors DRONE_CLAUDE.md was missing: the `_debug_vis_callback`
> patch and the §17.5 end-to-end run sequence. Read DRONE_CLAUDE.md first; consult
> this only for those specifics.

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
