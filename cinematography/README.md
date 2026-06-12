# Cinematography Drone Pipeline

Train an autonomous cinematography drone in Isaac Sim to film a dancer from compositionally good angles.

## Quick start (Phase A1+A2 smoke test)

```bash
# 1. Bake USDA locally (no EC2 needed)
python3 cinematography/render_dancer_mp4.py \
    --session mocap_handoff/Mocap/dance_20260519_213931 \
    --out /tmp/dancer_orbital.mp4 \
    --usda-only --duration 25

# 2. SCP the USDA + this script to EC2, then render via OVRTX
EC2_IP=<current public IP>
PEM="$HOME/.ssh/trigunai_key.pem"
scp -i $PEM cinematography/*.py ubuntu@$EC2_IP:/home/ubuntu/cinematography/
scp -i $PEM /tmp/dancer_orbital.usda ubuntu@$EC2_IP:/tmp/

# 3. On EC2: render + encode
ssh -i $PEM ubuntu@$EC2_IP 'python3 /home/ubuntu/cinematography/render_dancer_mp4.py \
    --session /home/ubuntu/mocap_session \
    --out /home/ubuntu/dancer_orbital.mp4 \
    --duration 25 --width 800 --height 450'

# 4. Pull back
scp -i $PEM ubuntu@$EC2_IP:/home/ubuntu/dancer_orbital.mp4 ./
```

## Scripts

| Script | Purpose |
|---|---|
| `parse_pose_bin.py` | Reads Gurulok mocap pose.bin (v1 33-joint and v2 84-joint), returns body arrays |
| `bake_dancer_usda.py` | Bakes dancer stick figure + orbital camera to animated USDA |
| `render_dancer_mp4.py` | End-to-end: load session → bake USDA → OVRTX render → ffmpeg MP4 |

## Coordinate systems

- Gurulok mocap (Unity): left-hand Y-up
- USD (OVRTX): right-hand Y-up → Z-negated from Unity
- Isaac Sim: right-hand Z-up (used for RL training, not for OVRTX rendering)
