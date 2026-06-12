# Artifact Registry

> Last updated: 2026-05-24 14:15 by Project Hub (bootstrapped)

---

## Trained models & checkpoints

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |
|---|---|---|---|---|---|---|
| Cinematographer PPO (500 ep) | `/workspace/isaaclab/logs/rl_games/cinematographer_direct/2026-05-24_09-37-23/nn/cinematographer_direct.pth` | container | No | ~5 MB | ✅ Active | Cinematography |
| AMP dance policy (baseline, 500 it) | `checkpoints/ckpt_backup.tgz` | mac-backup | No | 225 MB | ✅ Archived | Dance |
| AMP music-conditioned v1 (600 it) | `checkpoints/music_v1/music_ckpt_v1.tgz` | mac-backup | No | 63 MB | ✅ Archived | Dance |
| Drone A→B (Rivermark, 725 rew) | `drone_handoff/` | mac | No | — | ⏸️ Paused | Drone |

## Motion data (mocap, npz, trajectories)

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |
|---|---|---|---|---|---|---|
| Cinematographer trajectory (1250f@50fps) | `/tmp/cinematographer_trajectory.json` | ec2-tmp | ⚠️ YES | 423 KB | ✅ Backed up | Cinematography |
| Cinematographer trajectory (backup) | `/home/ubuntu/cinematographer_trajectory.json` | ec2-ebs | No | 423 KB | ✅ Safe | Cinematography |
| Gurulok dance v1 npz (single session) | `checkpoints/gurulok_dance_v1.npz` | mac-backup | No | 2.2 MB | ✅ Archived | Dance |
| Gurulok dance v2 npz (6 sessions) | `checkpoints/gurulok_dance_v2.npz` | mac-backup | No | 62 MB | ✅ Archived | Dance |
| Gurulok dance v2 + music features | `checkpoints/gurulok_dance_v2_with_music.npz` | mac-backup | No | 63 MB | ✅ Archived | Dance |
| 9 Quest mocap sessions (raw) | `mocap_handoff/Mocap/dance_20260519_194*` | mac | No | ~50 MB | ✅ Available | Dance / LB |
| Isaac Lab built-in dance ref | `/workspace/isaaclab/.../humanoid_amp/motions/humanoid_dance.npz` | container | No | — | ✅ Available | LB Physics |

## Videos & renders

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |
|---|---|---|---|---|---|---|
| Drone POV 5s test (approved) | `cinematography/drone_pov_5s.mp4` | mac | No | 41 KB | ✅ Approved | Cinematography |
| Overhead static 5s test | `cinematography/cinematographer_fixed_5s.mp4` | mac | No | 14 KB | ✅ Done | Cinematography |
| Overhead frame 0 | `cinematography/fixed_frame0.png` | mac | No | 13 KB | ✅ Done | Cinematography |
| Drone POV 25s full (rendering) | `/home/ubuntu/drone_pov_25s.mp4` | ec2-ebs | No | ~200 KB est | 🔄 Rendering | Cinematography |
| Walk cycle demo | `walk.mp4` | mac | No | — | ✅ Done | Video pipeline |

## GLBs & USD

| Artifact | Path | Location | Ephemeral? | Size | Status | Workstream |
|---|---|---|---|---|---|---|
| Crazyflie GLB (static) | `drone_handoff/cf2x.glb` | mac | No | — | ✅ Done | Drone |
| Crazyflie GLB (trained A→B) | `drone_handoff/cf2x_trained.glb` | mac | No | — | ⏸️ Has rotation bug | Drone |
| Drone POV 25s USDA | `/home/ubuntu/drone_pov_25s.usda` | ec2-ebs | No | 138 KB | ✅ Saved | Cinematography |
| Ragnarok GLB | `/var/www/showcase/assets/ragnarok.glb` | ec2-ebs | No | 182 MB | ✅ Done (flat white materials) | WebXR |
| Isaac Warehouse GLB | `/var/www/showcase/assets/warehouse.glb` | ec2-ebs | No | 569 MB | ✅ Done | WebXR |

## Config & scripts (source of truth)

| Artifact | Path | Location | Purpose | Workstream |
|---|---|---|---|---|
| CLAUDE.md | `CLAUDE.md` | mac | Master project handoff | All |
| DRONE_CLAUDE.md | `DRONE_CLAUDE.md` | mac | Drone pipeline handoff | Drone |
| ROBOTICS_CLAUDE.md | `ROBOTICS_CLAUDE.md` | mac | Robotics teleop handoff | Robotics |
| Cinematographer env | `cinematography/cinematographer_env.py` | mac + container | DirectRLEnv for drone filming | Cinematography |
| Render script | `cinematography/render_trained_cinematographer.py` | mac + ec2-ebs | Trajectory → USDA → OVRTX → MP4 | Cinematography |
| Export script | `cinematography/export_cinematographer_trajectory.py` | mac + container | Trained policy → JSON trajectory | Cinematography |
| Pose bin parser | `cinematography/parse_pose_bin.py` | mac | Core Quest mocap parser | All mocap |
| AMP motion converter | `mocap_handoff/pose_bin_to_amp_motion_v2.py` | mac | Quest → Isaac AMP npz | Dance / LB |
| Daphne retargeter | `mocap_handoff/bake_daphne_animation.py` | mac | NPZ → Daphne CC4 GLB | Dance |
| LiteLLM config | `~/litellm/config.yaml` | ec2-ebs | Azure OpenAI proxy config | Infra |
| Lighting skill | `.claude/skills/trigunai-lighting/SKILL.md` | mac | Lighting agent skill definition (L1-L4) | Lighting |
| Lighting session log | `lighting/SESSION_LIGHTING.md` | mac | Lighting agent session progress | Lighting |
| v1 product spec (ADR-002) | `project_hub/decisions/ADR-002_v1_product_spec.md` | mac | Locked: 6 modes + voice + fly-to-mark | Product |
| Capability one-pager | `outreach/CAPABILITY_ONE_PAGER.md` | mac | Customer-facing, updated with voice + fly-to-mark | Product |
| Stage design skill | `.claude/skills/trigunai-stage/SKILL.md` | mac | Stage agent skill definition (S1-S4) | Stage |
| Stage session log | `stage_design/SESSION_STAGE.md` | mac | Stage agent session progress | Stage |
