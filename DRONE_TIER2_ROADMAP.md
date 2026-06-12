# Drone Training — Tier 2 Roadmap

> Vision-based collision-avoiding navigation in NVIDIA Rivermark city.
> The next legitimate workstream after the Phase 6a Tier 0 pipeline-validation result.

**Owner:** TrigunRoboticsLab
**Status:** Planned (Phase 6a / Tier 0 complete; Tier 2 not started)
**Last updated:** 2026-05-23

---

## 1. The honest starting point

What we shipped in Phase 6a (the result the trained policy demonstrates):

- **Algorithm**: PPO via `rl_games`, no demonstration data, no adversarial motion priors
- **Task**: single fixed point-to-point, A=(0, 0, 30 m) → B=(100, 0, 30 m), hard-coded in `_reset_idx`
- **Observation**: state-only (16 floats: position, velocity, attitude quaternion, angular velocity, goal vector). **No camera, no depth, no lidar.**
- **Action**: 4 rotor thrusts (continuous)
- **Reward**: `1 − tanh(d/100)` distance + Δdistance progress + `+50` arrival bonus
- **Scene**: NVIDIA Rivermark city loaded as `/World/City` — **with all PhysX collision APIs stripped** (RigidBodyAPI, CollisionAPI, MassAPI, MeshCollisionAPI) from every building prim (gotcha §5 of `DRONE_CLAUDE.md`)
- **Done conditions**: `z < 0.5` or `z > 100` only — no collision termination because there is no collision

**What this means in plain language:** the trained policy is a **goal-seeking flier in empty space**. It has no perception of its surroundings. Buildings are visual props, not physical obstacles. The result is reproducible and clean for what it is (Tier 0 = pipeline proof), but it does not constitute "drone navigates the city."

Tier 2 is the work to make the drone actually see and avoid obstacles.

---

## 2. Tier 2 scope (one-line)

**A Crazyflie 2.X policy that uses simulated forward-facing depth camera input to navigate from A to B through a populated city scene with real collision physics, without crashing into buildings, trained end-to-end with PPO.**

---

## 3. Architectural changes from Tier 0

Every component changes. Listing them in dependency order:

### 3.1 Scene physics
- **Currently**: collision APIs stripped from `/World/City` (only ground-plane collision remains)
- **Tier 2**: real collision APIs on a curated subset of obstacles
- **The PhysX-at-scale wall**: original Rivermark has ~12,125 collidable building meshes; with `replicate_physics=True` and 1024+ envs, PhysX silently dies. This is the wall §5 was working around.
- **Mitigations** (pick one):
  1. **Procedural simpler scenes** — generate 10-100 box-shaped obstacles per env algorithmically. Loses Rivermark visual fidelity, gains trainability. **Recommended for v1.**
  2. **Convex hulls on Rivermark** — replace each building's detailed mesh with its convex hull for collision (visual mesh stays detailed). Cuts PhysX cost ~50-100×. Real engineering effort.
  3. **Voxel/grid representation** — represent obstacles as 3D occupancy grid checked manually in `_get_rewards`, no PhysX involvement. Cheapest but loses realism.

### 3.2 Sensor model — depth camera on the drone

Add to `cf2x.usd` (or wrap with overrides in `_setup_scene`):

```python
from isaaclab.sim.spawners.sensors import CameraCfg
camera_cfg = CameraCfg(
    prim_path="/World/envs/env_.*/Robot/cf2x/cf2x_body/depth_cam",
    update_period=0.0,                    # every step
    height=84, width=84,                  # cheap; same as DeepMind drone work
    data_types=["distance_to_image_plane"],
    spawn=sim_utils.PinholeCameraCfg(
        focal_length=15.0,
        focus_distance=400.0,
        clipping_range=(0.05, 30.0),       # max useful depth = 30 m
    ),
    offset=CameraCfg.OffsetCfg(
        pos=(0.05, 0.0, 0.0),              # 5 cm forward of body
        rot=(1.0, 0.0, 0.0, 0.0),          # forward-facing
        convention="ros",
    ),
)
```

The Crazyflie AI deck has a real HiMax 80×80 monochrome RGB. Depth (84×84) is the cheaper sim equivalent that's both easier to train on and easier to sim-to-real (less domain gap than RGB).

**Optional**: add a downward-facing depth (altitude awareness) and 32-ray sphere lidar (proximity ring). Each is a tradeoff between observation richness and training cost.

### 3.3 Observation space

```python
# Tier 0 (current):
obs = ObservationCfg(state=[pos(3), vel(3), quat(4), ang_vel(3), goal_vec(3)])  # 16 floats

# Tier 2:
obs = ObservationCfg(
    state=[pos(3), vel(3), quat(4), ang_vel(3), goal_vec(3)],   # 16 floats unchanged
    depth=[depth_84x84],                                         # 7,056 floats new
)
```

The state vector stays. The depth is added as a separate stream; the policy network combines them.

### 3.4 Policy network

`rl_games`' default MLP can't handle image input directly. Two paths:

**Option A**: stay on `rl_games`, write a custom `ModelBuilder` with a tiny CNN encoder:

```python
# pseudo-code for the network head
class DroneVisionPPO(ModelA2CContinuousLogStd):
    def __init__(self, params, **kwargs):
        # state branch: small MLP
        self.state_mlp = MLP([16, 64, 64])
        # vision branch: tiny CNN (84x84 → 64-dim latent)
        self.vision_cnn = nn.Sequential(
            nn.Conv2d(1, 16, 5, stride=2), nn.ReLU(),
            nn.Conv2d(16, 32, 5, stride=2), nn.ReLU(),
            nn.Conv2d(32, 32, 3, stride=2), nn.ReLU(),
            nn.Flatten(), nn.Linear(32 * 8 * 8, 64),
        )
        self.policy_head = MLP([64 + 64, 128, 4])    # 4 = rotor thrusts
        # value head similar
```

**Option B**: switch to `skrl` which has built-in vision-RL templates.

Option B is cleaner code but means re-deriving the Phase 6a baseline from a different RL library. Pick A for continuity with what's already working.

### 3.5 Reward shaping

Add to `_get_rewards`:

```python
# Existing rewards (kept):
distance_reward = ...
progress = ...
arrived = ...
lin_vel_penalty = ...
ang_vel_penalty = ...

# NEW: collision penalty
contact_sensor = self.scene["contact_forces"]
collided = (contact_sensor.data.net_forces_w.norm(dim=-1) > 0.1).any(dim=-1)
collision_penalty = collided.float() * -50.0       # large negative spike

# NEW: proximity penalty (encourages safe clearance)
depth = self._depth_camera.data.output["distance_to_image_plane"]  # [n_envs, 84, 84]
min_obstacle_dist = depth.reshape(self.num_envs, -1).min(dim=-1).values
proximity_penalty = -1.0 / (min_obstacle_dist.clamp(min=0.5) ** 2)  # blows up as d→0

# NEW: smoothness bonus when near obstacles
near_obstacle = (min_obstacle_dist < 5.0).float()
smoothness = -ang_vel.norm(dim=-1) * near_obstacle * 2.0
```

### 3.6 Done conditions

```python
# Existing: died = z < 0.5 OR z > 100
# Add:      died = died OR collided
```

### 3.7 Curriculum

**Critical** — vision-RL with collision doesn't train from scratch. Start simple, ramp up:

1. **Stage A**: 1 box obstacle in path, simple corridor scene. ~500-1000 iters.
2. **Stage B**: 5-10 random box obstacles in a 100m corridor. Load Stage A checkpoint, continue. ~2000-3000 iters.
3. **Stage C**: 50-100 procedural building-shaped obstacles, urban-like layout. Load B, continue. ~3000-5000 iters.
4. **Stage D**: convex-hull Rivermark (real city geometry, simplified collision). Load C, continue. ~3000-5000 iters.
5. **Stage E** (stretch): full Rivermark with all original meshes (if PhysX cooperates). Load D, fine-tune.

Each stage is a separate training run that bootstraps from the previous checkpoint. **Do not skip stages.** Skipping is the #1 reason vision-RL fails.

---

## 4. File-by-file change list

For someone implementing Tier 2 starting from the Phase 6a codebase:

| File | Change |
|---|---|
| `/workspace/isaaclab/.../direct/quadcopter_city_a2b/quadcopter_city_a2b_env_cfg.py` | Add `camera_cfg`, replace `city_usd_path` with procedural-scene config for early curriculum stages, set `replicate_physics=True/False` per stage |
| `/workspace/isaaclab/.../direct/quadcopter_city_a2b/quadcopter_city_a2b_env.py` | Add camera sensor in `_setup_scene`; modify `_get_observations` to include depth; modify `_get_rewards` for collision + proximity; modify `_get_dones` to include collision termination; replace `_setup_scene` city ref with curriculum scene generator |
| `agents/rl_games_ppo_cfg.yaml` (or new vision config) | Increase `network` config for state + vision encoder; reduce `num_envs` from 4096 → 1024-2048 (vision RL is GPU-VRAM-bound) |
| NEW: `network_vision_ppo.py` | Custom `ModelA2CContinuousLogStd` with state MLP + vision CNN branches |
| NEW: `scene_generators/procedural_obstacles.py` | Programmatic obstacle placement for curriculum stages A-C |
| NEW: `scene_generators/rivermark_convex.py` | One-time prep: walk Rivermark USD, replace MeshCollisionAPI with ConvexHullAPI on building props |

---

## 5. Compute budget — realistic

Phase 6a baseline numbers (the closest reference point):
- 4,096 envs, A10G GPU, 500 PPO iterations, ~4-6 hours wall time, reward 725

Tier 2 vision-RL costs more per env-step due to camera rendering and CNN forward passes:

| Stage | Envs | GPU | Iters | Wall time per stage | GPU-hr cost (g5.2xlarge @ $1.30) |
|---|---|---|---|---|---|
| A (1 obstacle) | 2048 | A10G | 1000 | 4-8 hrs | $5-10 |
| B (10 obstacles) | 2048 | A10G | 3000 | 12-24 hrs | $15-30 |
| C (procedural city) | 1024 | A10G | 5000 | 24-48 hrs | $30-60 |
| D (Rivermark convex) | 512 | A10G | 5000 | 48-96 hrs | $60-125 |
| E (full Rivermark stretch) | 256-512 | A10G | open-ended | open-ended | open-ended |

**Realistic total compute cost on g5.2xlarge: $100-250 spread over 2-4 weeks**, depending on how many iterations of hyperparameter tuning you need. Could be cut roughly in half with a g5.12xlarge (4× A10G) doing the heavy stages in parallel.

This is for **one drone going from A to B**. For productizing (multiple agents, multiple cities, random goals), multiply.

---

## 6. Risks and how to retire them, in order

1. **PhysX-at-scale collision instability (the §5 wall returning)**
   *Risk*: even with curriculum and convex hulls, real-collision Rivermark may still crash PhysX.
   *Retire by*: Stage A & B use procedural obstacles only. Don't touch Rivermark until Stage D. Have procedural-only as a permanent fallback if Rivermark never cooperates.

2. **Vision encoder doesn't learn useful features from 84×84 depth**
   *Risk*: tiny CNN may not represent obstacle geometry sufficiently.
   *Retire by*: at end of Stage A, plot the encoder's latent activations. If the encoder has degenerate features (all neurons identical), it's not learning; try larger CNN, normalize depth differently, or switch to 96×96 RGB.

3. **Sim-to-real gap on depth sensor**
   *Risk*: real Crazyflie AI deck's camera is 80×80 mono RGB; sim is 84×84 depth. Policies trained on sim depth don't transfer.
   *Retire by*: don't sim-to-real in Tier 2 — that's Tier 3. For Tier 2, target "good sim performance" only. If real-world deployment becomes a goal, add depth-from-mono pretraining (MiDaS-style) as a Tier 3 step.

4. **Curriculum collapse — agent over-fits to Stage A obstacles, fails on B**
   *Risk*: small obstacle sets are easy to memorize.
   *Retire by*: randomize obstacle positions every episode within Stage A. Use diverse seeds. Evaluate held-out validation scenes between iterations.

5. **rl_games doesn't support image obs cleanly**
   *Risk*: custom `ModelBuilder` requires deep `rl_games` knowledge.
   *Retire by*: prototype the network architecture in `skrl` first (it has working examples). Once the architecture is validated, port to `rl_games` for production training, OR just commit to `skrl` if it works (and accept the codebase fork).

6. **Compute budget overrun**
   *Risk*: $100-250 estimate balloons to $1000+ with hyperparameter sweeps.
   *Retire by*: hard budget of $500 for Tier 2. Track GPU-hours per stage. If a stage takes >2× estimate, stop and analyze before continuing.

---

## 7. Acceptance criteria per stage

What "Tier 2 done" looks like at each milestone:

**Stage A done**:
- ✅ Drone navigates a 50m corridor with 1 box obstacle from A→B, success rate ≥80% over 100 validation episodes
- ✅ Collision rate ≤10%
- ✅ Trained checkpoint saved, exports as animated glTF (same pipeline as Phase 6a)

**Stage B done**:
- ✅ 100m corridor, 10 random box obstacles, success rate ≥70%
- ✅ Collision rate ≤15%
- ✅ Validation against 5 unseen obstacle layouts

**Stage C done**:
- ✅ Procedural urban-like scene (50-100 obstacles), full A=(0,0,30)→B=(100,0,30) trajectory, success ≥60%
- ✅ Collision rate ≤20%
- ✅ VLM-critic ship-it score ≥7/10 on the rendered MP4

**Stage D done (real Tier 2 win)**:
- ✅ Real Rivermark (convex-hull collision), reach point B without crashing, success ≥50%
- ✅ Glb export shows drone visibly avoiding visible buildings
- ✅ Marketing-quality rendered trajectory MP4 produced via existing OVRTX or Blender pipeline

---

## 8. What this DOESN'T cover (deliberately)

- **Sim-to-real on physical Crazyflie** — that's Tier 3. Different problems (domain randomization, IMU noise, motor torque mismatches, latency).
- **Multi-drone coordination** — Tier 4-ish. Single-agent first.
- **Different cities / generalization across scenes** — Tier 4. Tier 2 stays within "make ONE Rivermark variant work."
- **Real-time replanning / adaptive goals** — out of scope. Tier 2 is fixed goal, fixed environment.
- **Reinforcement learning from human feedback (RLHF)** — out of scope.
- **Foundation-model-conditioned policies (Cosmos Reason 2.0 / VLA models)** — out of scope. Pure PPO+CNN is the Tier 2 architecture.

---

## 9. Dependencies and prerequisites before starting

Required infrastructure (some already in place from Phase 6a):

- ✅ EC2 g5.2xlarge with NVIDIA driver, Isaac Sim 6.0, Isaac Lab 3.0 (have on `TrigunAI-Omniverse` us-east-1 + `deepak-mumbai-server` ap-south-1)
- ✅ rl_games (or skrl) installed in `isaaclab` container
- ✅ Phase 6a checkpoint (used as a sanity baseline for "does the goal-seeking still work after env changes?")
- ⏳ Procedural obstacle scene generator (NEW — must build)
- ⏳ Vision-RL network module (NEW — must build)
- ⏳ Camera sensor config + Isaac Lab `CameraCfg` integration (NEW — straightforward)
- ⏳ ~$250 of EC2 budget allocated for training compute
- ⏳ Time budget: ~2-4 weeks of focused engineering

---

## 10. First-step deliverable (Week 1 target)

If someone starts this Monday, the right Week 1 milestone is:

> **"In a procedural 1-obstacle corridor scene with collision physics enabled, train a vision-PPO policy that successfully avoids the obstacle ≥80% of the time over 100 evaluation episodes, with the depth-camera observation pipeline fully wired into the env."**

That's the smallest deliverable that proves:
- ✅ Camera sensor works in Isaac Lab
- ✅ Vision encoder is implemented and learning
- ✅ Collision physics integrates cleanly
- ✅ Reward shaping behaves
- ✅ The new env + network can train at all

Everything Stage B onward is incremental scaling from there.

---

## Appendix A — Why this approach and not [X]

**Why not Imitation Learning from a planner-based expert?**
- Cleaner data, but you need a good planner (RRT*, A* on voxel grid) producing expert trajectories. The planner is its own engineering project.
- Imitation alone doesn't recover from out-of-distribution states; needs DAgger or behavior cloning + RL fine-tuning.
- **Reasonable Tier 3 add-on**, premature for Tier 2.

**Why not AMP (Adversarial Motion Priors)?**
- AMP needs expert demonstration data. For drone navigation, that means actual recorded flight trajectories that demonstrate "good" navigation in obstacle-rich environments. Don't have that data.
- The dance workstream uses AMP because Quest mocap provides natural expert demos. Drone has no equivalent corpus.
- **Could revisit if NVIDIA ships a drone-AMP dataset in the future.**

**Why not just use Cosmos Reason 2.0 (NVIDIA's foundation model)?**
- Cosmos is for scene understanding from video; it's a perception/reasoning module, not a control policy.
- Could be a Tier 3 add-on: use Cosmos to extract scene semantics, feed those into the policy as additional observation. But Tier 2 should prove vanilla CNN+PPO first.

**Why 84×84 depth and not full RGB?**
- RGB needs significantly larger encoder (3 channels, higher resolution effectively required for textures to be useful). 5-10× more compute per step.
- Depth maps directly to "obstacle distance," which is what the reward function uses. RGB requires the policy to infer depth from texture cues — harder to learn.
- Real Crazyflie hardware doesn't have RGB-D; it has mono RGB. So sim-to-real argues for either mono RGB or estimated depth, not sim-depth. **But for sim-only Tier 2, depth is the right pick — fastest training, cleanest signal.**

---

## Appendix B — Quick-look summary table

| Layer | Tier 0 (current) | Tier 2 |
|---|---|---|
| Observation | 16 floats (state only) | 16 floats + 84×84 depth |
| Scene | Visual city (no physics) | Procedural obstacles → real city w/ convex collision |
| Network | MLP only | CNN + MLP (vision encoder) |
| Reward | Distance + progress + arrive | + collision penalty + proximity penalty + smoothness |
| Curriculum | None (single fixed task) | 5 stages, each builds on previous |
| Done conditions | z bounds only | z bounds + collision |
| Training cost | ~$5-10 / run | ~$100-250 / full curriculum |
| Time to baseline | 4-6 hours | 2-4 weeks |
| Output | Goal-seeking flier in empty space | Vision-aware obstacle-avoiding navigator |

---

*This doc is the engineering plan for the next legitimate piece of robotics-lab work after the Phase 6a Tier 0 pipeline-validation milestone. It is not a research grant proposal or marketing copy — it's what you'd actually hand to an engineer to execute.*
