#!/bin/bash
# Phase A1+A2 smoke test — end-to-end dancer orbital video via OVRTX
#
# Prerequisites:
#   - EC2 TrigunAI-Omniverse running (check AWS console for current public IP)
#   - OVRTX container healthy on port 8001
#   - Set EC2_IP env var before running
#
# Usage:
#   EC2_IP=<current-ip> bash cinematography/run_smoke_test.sh

set -euo pipefail

EC2_IP="${EC2_IP:?Set EC2_IP to the current EC2 public IP}"
PEM="${PEM:-$HOME/.ssh/trigunai_key.pem}"
SESSION_NAME="dance_20260519_213931"
SESSION_DIR="$(cd "$(dirname "$0")/../.." && pwd)/NvidiaSimSetup/mocap_handoff/Mocap/$SESSION_NAME"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Phase A1+A2 Smoke Test ==="
echo "EC2: $EC2_IP"
echo "Session: $SESSION_NAME"

# 1. SCP scripts + session to EC2
echo "[1/5] Uploading scripts + mocap session to EC2..."
ssh -i "$PEM" ubuntu@"$EC2_IP" "mkdir -p /home/ubuntu/cinematography /home/ubuntu/mocap_session"
scp -i "$PEM" "$SCRIPT_DIR"/*.py ubuntu@"$EC2_IP":/home/ubuntu/cinematography/
scp -i "$PEM" "$SESSION_DIR"/meta.json "$SESSION_DIR"/pose.bin ubuntu@"$EC2_IP":/home/ubuntu/mocap_session/
# aux.bin is optional
[ -f "$SESSION_DIR/aux.bin" ] && scp -i "$PEM" "$SESSION_DIR"/aux.bin ubuntu@"$EC2_IP":/home/ubuntu/mocap_session/

# 2. Check OVRTX health
echo "[2/5] Checking OVRTX health..."
HEALTH=$(ssh -i "$PEM" ubuntu@"$EC2_IP" "curl -s localhost:8001/health 2>/dev/null || echo 'UNREACHABLE'")
echo "       OVRTX: $HEALTH"

# 3. Run the render pipeline on EC2
echo "[3/5] Rendering on EC2 (this takes a few minutes for 750 frames)..."
ssh -i "$PEM" ubuntu@"$EC2_IP" "cd /home/ubuntu && python3 cinematography/render_dancer_mp4.py \
    --session /home/ubuntu/mocap_session \
    --out /home/ubuntu/dancer_orbital.mp4 \
    --duration 25 --target-fps 30 \
    --width 800 --height 450 \
    --keep-usda"

# 4. Pull back MP4 + USDA
echo "[4/5] Downloading results..."
scp -i "$PEM" ubuntu@"$EC2_IP":/home/ubuntu/dancer_orbital.mp4 "$SCRIPT_DIR/../dancer_orbital.mp4"
scp -i "$PEM" ubuntu@"$EC2_IP":/home/ubuntu/dancer_orbital.usda "$SCRIPT_DIR/../dancer_orbital.usda" 2>/dev/null || true

# 5. Report
echo "[5/5] Done!"
echo "       MP4: $SCRIPT_DIR/../dancer_orbital.mp4"
ls -lh "$SCRIPT_DIR/../dancer_orbital.mp4"
echo ""
echo "Next: open the MP4 and check if it looks like 'a drone filmed a person dancing.'"
echo "If yes → proceed to Phase A3 (reward function)."
echo "If no  → debug the playback or rigging before writing reward code."
