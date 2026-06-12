---
name: trigunai-lower-body-physics
description: >
  Physics-based lower body prediction from Quest 3 upper-body tracking data using Isaac Lab
  AMP (Adversarial Motion Priors). Creates a new Isaac Lab environment where upper body joints
  are pinned to Quest mocap and an RL policy learns natural lower body motion (walking, dancing,
  balance) with PhysX simulation. Use when the user mentions "lower body", "leg prediction",
  "physics legs", "pinned upper body", "AMP lower body", "quest legs", "full body from upper",
  "predict legs", "lower body physics", or works on files in lower_body_physics/ directory.
  Proactively trigger when mocap sessions arrive with tracking_quality=1 (upper body only).
---

# TrigunAI Lower Body Physics Prediction Agent

You build a **physics-based lower body prediction system** that takes Quest 3 upper-body
tracking (head + hands + torso) and produces natural, physically plausible lower body motion
(hips, knees, ankles, feet) using Isaac Lab's PhysX simulation + AMP discriminator.

You operate on a **Mac** (data prep, converters, file management) and an **AWS EC2 g5.2xlarge**
(Isaac Lab training, PhysX simulation). You are part of the TrigunAI agent ecosystem alongside
the Training Agent, VR Agent, and Orchestrator.

---

## The problem

Quest 3 in `BodyJointSet.UpperBody` mode captures head + hands + torso but lower body joints
(hips, knees, ankles, feet) are NaN. Current workaround (`predict_lower_body.py`) uses simple
IK to generate static standing-pose legs — no walking, dancing, weight shifting, or balance.

**Goal:** Replace the IK filler with a physics-based RL policy that produces natural, dynamic
lower body motion matching the upper body's energy and style.

---

## Architecture: Pinned-Upper-Body AMP Environment

```
Quest 3 upper body (head + hands + torso)
   ↓ pose_bin_to_amp_motion_v2.py (convert to Isaac coords)
   ↓ quest_to_upper_body_dof.py (body quats → 14 DOF angles)
   ↓
┌──────────────────────────────────────────────────────┐
│  Isaac Lab: HumanoidAmpLowerBodyEnv                  │
│                                                       │
│  UPPER BODY (14 DOFs) ← PINNED to Quest data         │
│    abdomen_xyz(3), neck_xyz(3),                       │
│    L/R_shoulder_xyz(3×2), L/R_elbow(1×2)             │
│    via high-stiffness PD (1000 N·m/rad)              │
│                                                       │
│  LOWER BODY (14 DOFs) ← RL POLICY controls           │
│    L/R_hip_xyz(3×2), L/R_knee(1×2),                  │
│    L/R_ankle_xyz(3×2)                                 │
│    via normal PD (40 N·m/rad)                         │
│                                                       │
│  AMP DISCRIMINATOR ← trained on humanoid_dance.npz   │
│    "do these legs look natural?"                      │
│                                                       │
│  PhysX ← ground contact, balance, no foot sliding     │
└──────────────────────────────────────────────────────┘
   ↓ rollout → full-body trajectory
   ↓ bake_daphne_animation.py / bake_dancer_usda.py
   ↓
animated GLB with natural legs → WebXR / Gurulok VR
```

---

## Phase map with gates

| Phase | What you build | Key script | Acceptance gate |
|---|---|---|---|
| **LB1** | DOF decomposition: Quest body quats → upper body DOF angles | `quest_to_upper_body_dof.py` | FK reconstruction matches Quest body positions within 2cm |
| **LB2** | Environment + config + task registration | `humanoid_amp_lower_body_env.py` + cfg + `__init__.py` | Smoke test: 20 iters, no crash, humanoid stands |
| **LB3** | Upper body pinning validation | test script | Pinned upper body tracks Quest data within 5° per joint |
| **LB4** | Balance-only training (no AMP) | training run, 500 iters | Humanoid doesn't fall, feet make ground contact |
| **LB5** | Full AMP training + discriminator | training run, 3000 iters | Legs visually match dance style, no foot sliding (**SUBJECTIVE**) |
| **LB6** | Integration with baking pipeline | inference script + GLB export | Full-body GLB plays in WebXR with natural legs |
| **LB7** | ONNX distillation for on-device | `distill_lower_body_onnx.py` | <50 MB, <10 ms on Snapdragon, action diff <1% |

**LB5 has a SUBJECTIVE approval gate.** The user must explicitly say the legs look natural.

---

## DOF split (exact indices)

The Isaac AMP humanoid has **28 DOFs** and **15 bodies**.

### Upper body DOFs — PINNED (indices 0–13, 14 DOFs)

| DOF index | Name | Joint |
|---|---|---|
| 0 | abdomen_x | torso-to-pelvis X |
| 1 | abdomen_y | torso-to-pelvis Y |
| 2 | abdomen_z | torso-to-pelvis Z |
| 3 | neck_x | head-to-torso X |
| 4 | neck_y | head-to-torso Y |
| 5 | neck_z | head-to-torso Z |
| 6 | right_shoulder_x | right arm X |
| 7 | right_shoulder_y | right arm Y |
| 8 | right_shoulder_z | right arm Z |
| 9 | right_elbow | right elbow |
| 10 | left_shoulder_x | left arm X |
| 11 | left_shoulder_y | left arm Y |
| 12 | left_shoulder_z | left arm Z |
| 13 | left_elbow | left elbow |

### Lower body DOFs — POLICY-CONTROLLED (indices 14–27, 14 DOFs)

| DOF index | Name | Joint |
|---|---|---|
| 14 | right_hip_x | right hip X |
| 15 | right_hip_y | right hip Y |
| 16 | right_hip_z | right hip Z |
| 17 | right_knee | right knee |
| 18 | right_ankle_x | right ankle X |
| 19 | right_ankle_y | right ankle Y |
| 20 | right_ankle_z | right ankle Z |
| 21 | left_hip_x | left hip X |
| 22 | left_hip_y | left hip Y |
| 23 | left_hip_z | left hip Z |
| 24 | left_knee | left knee |
| 25 | left_ankle_x | left ankle X |
| 26 | left_ankle_y | left ankle Y |
| 27 | left_ankle_z | left ankle Z |

### Body hierarchy (parent → child)

```
pelvis (root — world pose from Quest + policy Z delta)
  ├→ torso: abdomen_x/y/z
  │   ├→ head: neck_x/y/z
  │   ├→ right_upper_arm: right_shoulder_x/y/z
  │   │   └→ right_lower_arm: right_elbow
  │   │       └→ right_hand (leaf)
  │   └→ left_upper_arm: left_shoulder_x/y/z
  │       └→ left_lower_arm: left_elbow
  │           └→ left_hand (leaf)
  ├→ right_thigh: right_hip_x/y/z
  │   └→ right_shin: right_knee
  │       └→ right_foot: right_ankle_x/y/z
  └→ left_thigh: left_hip_x/y/z
      └→ left_shin: left_knee
          └→ left_foot: left_ankle_x/y/z
```

---

## Observation space (75 dims)

| Component | Dims | Source |
|---|---|---|
| Lower body DOF positions | 14 | policy-controlled joints |
| Lower body DOF velocities | 14 | finite difference or sim readback |
| Foot contact forces (L/R) | 2 | PhysX contact sensor |
| Upper body DOF positions (Quest) | 14 | pinned from trajectory |
| Upper body DOF velocities | 14 | finite difference from trajectory |
| Root height + XY velocity | 6 | pelvis state |
| Projected gravity in body frame | 3 | orientation sensor |
| Root linear velocity | 3 | pelvis |
| Root angular velocity | 3 | pelvis |
| Gait phase (sin/cos) | 2 | internal clock |
| **Total** | **75** | |

---

## Action space

**14 continuous actions** = PD position targets (radians) for the 14 lower body DOFs.
Same actuation model as existing AMP humanoid — the PD controller converts to torques.

---

## Reward function

```python
reward = (
    0.30 * r_amp           # AMP discriminator: "do legs look natural?"
    + 0.20 * r_balance     # CoM over support polygon
    + 0.15 * r_foot_contact  # at least one foot on ground
    + 0.10 * r_foot_slide  # penalize horizontal foot vel when in contact
    + 0.10 * r_energy      # penalize excessive joint torques
    + 0.05 * r_upright     # pelvis up-vector · world up-vector
    + 0.10 * r_root_height # pelvis Z in [0.8, 1.0] m range
)
```

### Individual reward terms

- **r_amp** (0.30): AMP discriminator on full 15-body state. Reference: `humanoid_dance.npz`.
- **r_balance** (0.20): `exp(-k * max(0, dist_com_to_support)^2)`. Project CoM onto ground, distance to foot contact polygon.
- **r_foot_contact** (0.15): `max(left_contact, right_contact)`. At least one foot touching.
- **r_foot_slide** (0.10): `exp(-k * ||v_foot_xy||^2)` for feet in contact. Anti-skating.
- **r_energy** (0.10): `exp(-k * sum(tau^2))`. Efficient motion.
- **r_upright** (0.05): `max(0, dot(pelvis_up, world_up))`.
- **r_root_height** (0.10): `exp(-k * (z - z_target)^2)` where z_target from user height.

---

## Upper body pinning mechanism

**Use high-stiffness PD controllers, NOT direct position writes.**

Direct `write_joint_position_to_sim()` bypasses PhysX constraint solver and causes instability.
Instead, set PD gains extremely high on upper body so the controller effectively pins:

```python
# In _pre_physics_step():
upper_dof_targets = self._quest_trajectory_at(self._env_time)  # (N, 14)

# High-stiffness PD makes these joints track Quest data rigidly
self._humanoid.set_joint_position_target(
    target=upper_dof_targets,
    joint_ids=self._upper_body_dof_ids,
)
# Upper body stiffness: 1000 N·m/rad, damping: 100 N·m·s/rad
# Lower body stiffness: 40 N·m/rad, damping: 5 N·m·s/rad (normal RL control)
```

---

## Key files

### Existing files you depend on

| File | What | Where |
|---|---|---|
| `mocap_handoff/pose_bin_to_amp_motion.py` | Gurulok → Isaac AMP converter. Has GUROLOK_TO_ISAAC_BODY mapping, 28 DOF names, quat math | Mac repo |
| `mocap_handoff/pose_bin_to_amp_motion_v2.py` | v129 (84-joint) converter | Mac repo |
| `cinematography/parse_pose_bin.py` | Core pose.bin parser, 15-body extraction | Mac repo |
| `cinematography/cinematographer_env.py` | Best reference for DirectRLEnv with external trajectory loading + per-env time index | Mac repo |
| `mocap_handoff/predictor/predict_lower_body.py` | Current IK filler (what we're replacing) | Mac repo |
| `mocap_handoff/add_music_features_to_npz.py` | Music feature extraction (for future music-conditioned legs) | Mac repo |

### Files you will create

| File | What | Where |
|---|---|---|
| `lower_body_physics/quest_to_upper_body_dof.py` | Quest body rotations → 14 upper body DOF angles | Mac repo |
| `lower_body_physics/humanoid_amp_lower_body_env.py` | The Isaac Lab DirectRLEnv | Deploy to container |
| `lower_body_physics/humanoid_amp_lower_body_env_cfg.py` | Environment config | Deploy to container |
| `lower_body_physics/deploy/__init__.py` | Task registration | Deploy to container |
| `lower_body_physics/deploy/agents/skrl_amp_cfg.yaml` | skrl AMP training config | Deploy to container |
| `lower_body_physics/predict_lower_body_physics.py` | Inference script: Quest trajectory → full-body output | EC2 |
| `lower_body_physics/validate_dof_decomposition.py` | FK reconstruction test for LB1 gate | Mac repo |
| `lower_body_physics/SESSION_LOWER_BODY.md` | Session notes for CEO agent | Mac repo |

---

## AMP discriminator reference motions

**Priority order:**

1. **`humanoid_dance.npz` (built-in)** — already at `/workspace/isaaclab/.../humanoid_amp/motions/humanoid_dance.npz`. Zero conversion work. Sufficient for bootstrapping.
2. **AMASS dataset** — thousands of full-body motions. Academic license at https://amass.is.tue.mpg.de/. Requires SMPL → Isaac retargeting. Phase 2 enhancement.
3. **CMU MoCap Database** — public domain BVH/ASF/AMC. More conversion work. Phase 3 fallback.

**Start with option 1.** The discriminator only needs to see "what natural legs look like" — even one good clip bootstraps the prior.

---

## Training recipe

### Hardware

EC2 g5.2xlarge (A10G, 24 GB VRAM, 8 vCPUs, 30 GB RAM)

### PhysX OOM constraints (CRITICAL — learned from prior sessions)

| num_envs | gpu_found_lost_pairs_capacity | Buffer cost | Status |
|---|---|---|---|
| 4096 | needs 2²⁹ | ~4 GB | OOMs on A10G |
| 2048 | needs 2²⁸ | ~2 GB | OOMs at 23 GB total |
| 512 | needs 2²⁶ | ~512 MB | System RAM OOM at ~8 min |
| **256** | **2²⁶** | **~256 MB** | **Safe — use this** |

### Training commands

```bash
# Validation (LB4): 500 iters, ~15 min
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
     --task Isaac-Humanoid-AMP-LowerBody-Direct-v0 --algorithm AMP \
     --num_envs 256 --max_iterations 500 --headless > /tmp/lb_train.log 2>&1"'

# Full training (LB5): 3000 iters, ~45 min
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
  'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
   ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
     --task Isaac-Humanoid-AMP-LowerBody-Direct-v0 --algorithm AMP \
     --num_envs 256 --max_iterations 3000 --headless > /tmp/lb_train_full.log 2>&1"'
```

### Hyperparameters (starting point)

| Param | Value | Notes |
|---|---|---|
| Learning rate | 3e-4 | Adaptive schedule |
| PPO clip | 0.2 | Standard |
| Entropy coeff | 0.005 | |
| Gamma | 0.99 | |
| Horizon | 48 | |
| Minibatch | 4096 | For 256 envs |
| AMP disc LR | 1e-5 | Standard |
| AMP reward weight | 0.3 | Of total reward |

---

## Deployment pipeline (after training)

1. **Inference script** (`predict_lower_body_physics.py`):
   - Input: Quest upper-body trajectory npz
   - Runs trained policy in Isaac Lab (single env, deterministic)
   - Output: full-body 15-body npz (all positions/rotations/velocities)

2. **Integration** — output feeds directly into:
   - `bake_dancer_usda.py` (stick figure visualization)
   - `bake_daphne_animation.py` (CC4 character retargeting)
   - No changes needed to the rendering pipeline

3. **ONNX distillation** (LB7):
   - Input: upper body state (14 DOFs + root pose) = 21 floats
   - Output: lower body DOF targets = 14 floats
   - Target: <50 MB, <10 ms on Snapdragon 865

---

## Coordinate systems

| System | Hand | Up | Position transform | Quaternion transform |
|---|---|---|---|---|
| Unity (Quest mocap) | Left | Y | identity | (x,y,z,w) |
| Isaac Sim (training) | Right | Z | (x,z,y) | (x,z,y,w) |
| USD (rendering) | Right | Y | (x,y,-z) | (x,y,-z,w) |

---

## EC2 quick ref

**Video rendering:** See `VIDEO_RENDERING.md` for the master reference. Use Blender EEVEE (0.33s/frame) instead of OVRTX (6s/frame) — 18x faster.

```
Instance: TrigunAI-Omniverse (i-047ebf759f2386e71), g5.2xlarge, us-east-1
SSH: ssh -i ~/.ssh/trigunai_key.pem ubuntu@<CURRENT_IP>
OVRTX: localhost:8001 (check gpu_initialized; 6 min cold start)
isaaclab container: sudo docker start isaaclab
PUBLIC IP CHANGES ON EVERY STOP/START — always check AWS console
/tmp IS EPHEMERAL — wiped on EC2 stop, persist to /home/ubuntu/
AMP training needs --algorithm AMP flag (not default PPO)
```

---

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| PhysX OOM at 256 envs with humanoid | Medium | Blocks training | Start at 128 envs, scale up |
| Upper body pinning causes instability | Medium | Poor physics | High-stiffness PD (not direct write); reduce sim dt to 1/200 if needed |
| DOF decomposition from body quats wrong | Medium | Wrong pose | Validate FK reconstruction vs Quest body positions (LB1 gate) |
| Built-in `humanoid_dance.npz` insufficient | Low | AMP doesn't learn feet | Fallback: AMASS walking/dancing clips |
| Foot sliding persists | Medium | Unrealistic | Increase r_foot_slide weight; add post-processing foot lock |

---

## Mocap data format

Quest sessions in `mocap_handoff/Mocap/dance_<UTC>/`:

| File | Format | Content |
|---|---|---|
| `meta.json` | JSON | schema, joint count, music context |
| `pose.bin` | binary | 84 joints × 40B/joint/frame @ 60 Hz |
| `predicted/pose.bin` | binary | Same but with IK-filled lower body |
| `aux.bin` | binary | Eye gaze + body confidence |
| `xr_hands.bin` | binary | 52 finger joints |

Use `predicted/` subfolder for upper-body-only sessions (tracking_quality=1).

---

## Session management

After each work session, update `lower_body_physics/SESSION_LOWER_BODY.md` with:
- What was accomplished (phase progress)
- Bugs found and fixed
- EC2 state (container status, checkpoint paths, what's ephemeral)
- Next steps
- Any subjective gate results

This file is readable by the CEO orchestrator agent for cross-pipeline status.

---

## Project Hub protocol

At **session start**:
1. Read `project_hub/CEO_BRIEFING.md` for cross-agent context
2. Check `project_hub/feedback/*_to_lower_body*.md` or `*_to_lb*.md` for unread messages
3. Mark any feedback as `Status: acknowledged` after reading

At **session end**:
1. Update your row in `project_hub/CEO_BRIEFING.md` workstream status table
2. Write feedback to `project_hub/feedback/` if you produced deliverables (full-body npz, etc.)
3. Update `project_hub/ARTIFACT_REGISTRY.md` with any new files created
4. Update `project_hub/DATA_INVENTORY.md` if you added/moved files on EC2
5. If LB5 gate was reached (subjective leg naturalness), add to `project_hub/GATE_LOG.md`
6. Update `lower_body_physics/SESSION_LOWER_BODY.md` with session progress
