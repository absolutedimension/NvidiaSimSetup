---
name: trigunai-drone-pipeline
description: >
  Drone training pipeline for TrigunAI — the full chain from Isaac Lab RL training through
  trajectory export, OVRTX rendering, VLM evaluation, and animated GLB delivery for WebXR
  and Quest 3. Use this skill when working on: quadcopter training, Crazyflie, drone
  trajectory, PPO policy, Isaac-Quadcopter-Direct-v0, city navigation A→B, OVRTX drone
  rendering, drone evaluation/critic, animated GLB export for drone, render_drone_demo.py,
  export_drone_trajectory.py, evaluate_drone_trajectory.py, drone_handoff/, or any
  drone-related RL training and delivery task. Triggers on: "drone train", "drone pipeline",
  "quadcopter", "Crazyflie", "drone trajectory", "drone render", "drone GLB", "drone
  evaluation", "ship-it verdict", "city training", "Rivermark", "drone A to B", "drone
  policy", "cf2x", "drone checkpoint". Proactively use when working in drone_handoff/,
  or touching render_drone_demo.py / export_drone_trajectory.py / evaluate_drone_trajectory.py.
---

# TrigunAI Drone Training Pipeline

You own the **end-to-end drone RL training pipeline**: from PPO training in Isaac Lab through
trajectory capture, OVRTX-rendered verification video, VLM quality gate, and animated GLB
delivery to WebXR / Quest 3 / GurulokInnerJourney Unity app.

This pipeline runs on the **TrigunAI-Omniverse EC2 g5.2xlarge** (us-east-1) using the
`isaaclab` Docker container (Isaac Sim 6.0.0-rc.22, Isaac Lab 3.0).

---

## Pipeline overview

```
Isaac Lab PPO training (inside `isaaclab` container, GPU)
    │ saves .pth checkpoint
    ▼
export_drone_trajectory.py (inside container)
    │ writes drone_trajectory.json (per-frame pos + quat)
    ▼
render_drone_demo.py (EC2 host)
    ├── full scene → drone_trained.mp4 (OVRTX at :8001)
    └── --minimal-usda → drone_trained_minimal.usda
                              │
                              ▼
evaluate_drone_trajectory.py (EC2 host, optional --evaluate flag)
    │ 6 keyframes → 2×3 grid → gpt-4o-mini via LiteLLM :4000
    │ returns {reach, smoothness, stability, efficiency, overall, verdict}
    ▼
usd_to_glb.py --inject-trajectory (Blender 4.5 on EC2)
    │ animated GLB with NLA strips
    ▼
cf2x_trained.glb → WebXR / Quest 3 / GurulokInnerJourney
```

---

## Key scripts (all in `webxr-showcase/scripts/`)

| Script | What it does |
|---|---|
| `export_drone_trajectory.py` | Runs inside the `isaaclab` container. Loads .pth checkpoint, steps env at `num_envs=1`, captures `root_pos_w` + `root_quat_w` per step. Outputs JSON. Handles both `warp.array` and `torch.Tensor` returns. |
| `render_drone_demo.py` | Two modes: hardcoded smoothstep A→B (smoke test) and `--trajectory JSON` (trained policy). Bakes animated USDA (floor + camera + markers + drone ref). Renders via OVRTX at :8001. Outputs MP4. `--minimal-usda` for GLB-only path. `--evaluate` chains VLM critic. Auto-frames camera from trajectory bounds. |
| `evaluate_drone_trajectory.py` | VLM quality gate. Extracts 6 keyframes → 2x3 grid JPEG → gpt-4o-mini (via LiteLLM proxy :4000). Scores reach/smoothness/stability/efficiency on 1-10. Returns verdict: `ship-it`, `needs-more-training`, or `broken`. |
| `usd_to_glb.py` | Blender 4.5 headless (`/opt/blender45/blender`). `--animated` pushes to NLA strips. `--inject-trajectory` writes F-curves directly from the JSON (bypasses Blender's broken USD time-sample import). Removes `TRANSFORM_CACHE` constraints. |

---

## Training environments

| Task | Use case | Env count |
|---|---|---|
| `Isaac-Quadcopter-Direct-v0` | Hover-to-goal (Crazyflie, basic) | 4096 |
| Custom `quadcopter_city_a2b` | A→B navigation in Rivermark city | 256–512 (city scene is heavy) |

**Training command (basic hover):**
```bash
sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
  ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
  --task Isaac-Quadcopter-Direct-v0 --viz none --num_envs 4096 --max_iterations 500 \
  > /tmp/drone_train.log 2>&1"
```

**Checkpoints** land at `/workspace/isaaclab/logs/rl_games/quadcopter_direct/<timestamp>/nn/`.

---

## VLM critic — the quality gate

The VLM critic closes the loop between training and visual evaluation. Key design decisions:

1. **Visibility check is mandatory in the prompt.** Without it, gpt-4o-mini hallucinates mid-range
   scores when the drone is invisible (off-frame, missing reference). The system prompt explicitly
   requires "if you can't see the drone, return broken."

2. **Camera auto-frames from trajectory bounds.** Fixed cameras fail when the trained policy drifts
   away from origin. The camera computes bounding box of all positions and places itself to frame the
   entire flight.

3. **VLM score can diverge from RL reward.** Numerical reward may drop while VLM scores improve — the
   VLM measures what humans care about (looks-like-good-flying), the reward optimizes a formula. This
   divergence is expected and is exactly why the VLM gate matters.

| Verdict | Action |
|---|---|
| `ship-it` | GLB is ready — proceed to drone_handoff/ |
| `needs-more-training` | More iterations, re-export, re-render, re-evaluate |
| `broken` | Inspect the grid JPEG; usually a missing asset, camera bug, or crash |

---

## Coordinate systems

| System | Convention | Transform to USD Y-up |
|---|---|---|
| Isaac Sim | Z-up, right-hand | pos: `(x,y,z) → (x,z,-y)`, quat: `(qw,qx,qy,qz) → (qw,qx,qz,-qy)` |
| USD (for OVRTX) | Y-up | native |
| Blender (export) | `export_yup=True` handles the conversion from Z-up internally |

---

## Critical gotchas

1. **`/tmp/cf2x.usd` is wiped on EC2 stop.** The OVRTX container mounts host `/tmp` as `/host_tmp`.
   After every EC2 start, restore: `cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/cf2x.usd`

2. **Blender 4.5 is at `/opt/blender45/blender`**, not `/usr/bin/blender` (4.0.2, no USD support).

3. **OVRTX cold start takes ~6 min.** Check `curl -s localhost:8001/health` for `gpu_initialized: true`.

4. **After `docker cp`, chmod 644 the USD files.** Root-owned files cause Blender's USD reference to
   silently fail.

5. **Blender's USD importer does NOT translate `xformOp:*.timeSamples` into F-curves.** It creates a
   `Transform Cache` constraint instead. Use `--inject-trajectory` to write F-curves directly.

6. **The `isaaclab` container does NOT auto-start.** Run `sudo docker start isaaclab` after EC2 boot.

---

## EC2 resume sequence

```bash
EC2_IP=<current public IP from AWS console>
PEM="$HOME/.ssh/trigunai_key.pem"

# 1. Start container
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 2. Restore volatile assets
ssh -i $PEM ubuntu@$EC2_IP 'cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/cf2x.usd && \
  cp /home/ubuntu/assets/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd'

# 3. Upload latest scripts
for f in render_drone_demo.py export_drone_trajectory.py usd_to_glb.py evaluate_drone_trajectory.py; do
  scp -i $PEM webxr-showcase/scripts/$f ubuntu@$EC2_IP:/home/ubuntu/$f
done

# 4. Verify OVRTX health
ssh -i $PEM ubuntu@$EC2_IP 'curl -s localhost:8001/health | python3 -m json.tool'
```

---

## Shipped artifacts

| Artifact | Path | Status |
|---|---|---|
| Phase 2 GLB (hover, ship-it 8/10) | `drone_handoff/cf2x_trained.glb` | Shipped to WebXR |
| Phase 6a GLB (city A→B, v6 fixed) | `drone_handoff/cf2x_city_a2b.glb` | Rotation bug fixed, deployed to nginx |
| Static Crazyflie GLB | `drone_handoff/cf2x.glb` | Static model, no animation |
| Drone evaluation grid | `drone_trained.evaluation_grid.jpg` | Sample VLM input |

---

## Relationship to other pipelines

This drone pipeline **coexists** with the dance/AMP pipeline (CLAUDE.md §19) and the NVIDIA
Content Agents (CLAUDE.md §3–6) on the same EC2 box. They share the OVRTX renderer on :8001
and the `isaaclab` container. Code paths are isolated:
- Drone: `/workspace/isaaclab/.../quadcopter_city_a2b/`
- Dance: `/workspace/isaaclab/.../humanoid_amp/`
- Content Agents: `~/content-agents/`

The drone pipeline is a **production tool** for the company — it produces cinematography content
for courses and VR demos. The trained policy (ONNX, ~80KB, 50Hz on-device) is a validated
research asset under Engine B (Physical AI). Hardware deployment (Modal AI Starling 2 + GoPro)
is gated on seed funding.
