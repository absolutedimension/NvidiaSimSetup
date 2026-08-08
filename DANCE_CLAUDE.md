# Dance / Music→Character-Animation — PAUSED handoff (archived from CLAUDE.md §19)

> Moved out of `CLAUDE.md` on 2026-07-30 to cut per-session reused-input cost.
> This is the sole home of the dance-pipeline detail. PAUSED 2026-05-21 (see §19.10
> below); fully resumable. Robotics is the active bet — see `ROBOTICS_CLAUDE.md`.

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
