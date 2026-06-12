# Data Inventory — 2026-05-24

> Last updated: 2026-05-24 14:15 by Project Hub (bootstrapped)

---

## Mac (always safe)

| Category | Path | Key files | Size |
|---|---|---|---|
| Project root | `~/Documents/01_Active/NvidiaSimSetup/` | CLAUDE.md, DRONE_CLAUDE.md, ROBOTICS_CLAUDE.md | — |
| Cinematography scripts | `cinematography/` | render_trained_cinematographer.py, export_*.py, parse_pose_bin.py, bake_dancer_usda.py | — |
| Cinematography outputs | `cinematography/` | drone_pov_5s.mp4 (41KB), cinematographer_fixed_5s.mp4 (14KB), fixed_frame0.png | ~70 KB |
| Drone handoff | `drone_handoff/` | cf2x.glb, cf2x_trained.glb, DRONE_GUROLOK_HANDOFF*.md | — |
| Mocap sessions | `mocap_handoff/Mocap/dance_20260519_194*` | 9 sessions (pose.bin + predicted/ + meta.json) | ~50 MB |
| Mocap converters | `mocap_handoff/` | pose_bin_to_amp_motion_v2.py, add_music_features_to_npz.py | — |
| Daphne retargeter | `mocap_handoff/` | bake_daphne_animation.py | — |
| IK predictor | `mocap_handoff/predictor/` | predict_lower_body.py | — |
| Checkpoint backups | `checkpoints/` | ckpt_backup.tgz (225MB), music_v1/ (63MB), *.npz files | ~350 MB |
| Lower body physics | `lower_body_physics/` | SESSION_LOWER_BODY.md (just created) | — |
| Project hub | `project_hub/` | CEO_BRIEFING.md, ARTIFACT_REGISTRY.md, this file | — |
| SSH key | `~/.ssh/trigunai_key.pem` | Also in iCloud | — |

## EC2 — EBS persistent (/home/ubuntu/)

| Category | Path | Key files | Size |
|---|---|---|---|
| Content agents | `~/content-agents/` | NVIDIA agent source + TrigunAI patches | ~2 GB |
| LiteLLM config | `~/litellm/` | config.yaml, docker-compose.yml | — |
| Crazyflie asset (persistent) | `~/assets/Crazyflie/` | cf2x.usd, cf2x_robot_schema.usd | — |
| Crazyflie GLB | `~/cf2x.glb` | Static converted GLB | — |
| Render script | `~/render_trained_cinematographer.py` | Latest copy from Mac | 13 KB |
| Trajectory backup | `~/cinematographer_trajectory.json` | ✅ Backed up from /tmp | 423 KB |
| 25s USDA | `~/drone_pov_25s.usda` | Full 25s scene (138K chars) | ~138 KB |
| 25s video (rendering) | `~/drone_pov_25s.mp4` | 🔄 Being written | ~200 KB est |
| 5s video | `~/drone_pov_5s.mp4` | Approved test | 41 KB |
| Nginx webroot | `/var/www/showcase/` | ragnarok.glb (182MB), warehouse.glb (569MB) | ~750 MB |

## EC2 — EPHEMERAL (/tmp/) ⚠️

| File | Purpose | Backed up? | Backup location |
|---|---|---|---|
| `/tmp/cinematographer_trajectory.json` | Trajectory from trained policy | ✅ Yes | `/home/ubuntu/cinematographer_trajectory.json` |
| `/tmp/cf2x.usd` | Crazyflie USD for OVRTX reference | ⚠️ Must restore after stop | Copy from `~/assets/Crazyflie/cf2x.usd` |
| `/tmp/cf2x_robot_schema.usd` | Crazyflie schema | ⚠️ Must restore after stop | Copy from `~/assets/Crazyflie/` |

## EC2 — Container (isaaclab)

| Path | Purpose | Backed up? |
|---|---|---|
| `/workspace/isaaclab/logs/rl_games/cinematographer_direct/2026-05-24_09-37-23/nn/cinematographer_direct.pth` | Trained cinematographer checkpoint | ❌ Should backup |
| `/workspace/isaaclab/source/isaaclab_tasks/.../humanoid_amp/motions/humanoid_dance.npz` | Built-in AMP reference | ✅ Part of image |
| `/workspace/isaaclab/source/isaaclab_tasks/.../humanoid_amp/motions/gurulok_dance_v2_with_music.npz` | Music-conditioned reference | ✅ Also on Mac |
| Patched `motion_loader.py`, `humanoid_amp_env.py`, `humanoid_amp_env_cfg.py` | Music conditioning patches | ✅ On EBS root |

## Quest 3

| Path | Purpose |
|---|---|
| `com.trigunai.gurulokinnerjourney/files/Mocap/` | Raw mocap recordings (already pulled to Mac) |
| GurulokInnerJourney app | Meta alpha, build v63 |

## Windows (VR Agent)

| Path | Purpose |
|---|---|
| `GurulokInnerJourney/` | Unity project source |
| `Assets/_App/DroneJourney/Models/` | Where trained GLBs go |

---

## Rescue checklist (before EC2 stop)

```bash
EC2_IP=<current public IP>
PEM=~/.ssh/trigunai_key.pem

# 1. Check /tmp for anything important
ssh -i $PEM ubuntu@$EC2_IP 'ls -la /tmp/*.json /tmp/*.npz /tmp/*.usd* /tmp/*.mp4 /tmp/*.pth 2>/dev/null'

# 2. Copy anything not yet backed up
ssh -i $PEM ubuntu@$EC2_IP 'for f in /tmp/*.json /tmp/*.npz /tmp/*.mp4; do
  [ -f "$f" ] && [ ! -f "/home/ubuntu/$(basename $f)" ] && cp "$f" /home/ubuntu/ && echo "Saved: $f"
done'

# 3. Backup cinematographer checkpoint from container
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker cp isaaclab:/workspace/isaaclab/logs/rl_games/cinematographer_direct/ /home/ubuntu/cinematographer_checkpoints/ 2>/dev/null && echo "Checkpoints saved" || echo "No checkpoints to save"'

# 4. Note the current IP (it WILL change)
echo "Current IP: $EC2_IP — will change after stop/start"
```
