#!/bin/bash
# deploy_v4.sh — Push v4 mode-conditioned cinematographer env to EC2 + container
#
# Usage:
#   EC2_IP=52.23.151.219 ./cinematography/deploy_v4.sh
#
# After deploy, start training with:
#   ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP \
#     'sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
#      ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
#      --task Isaac-Cinematographer-Direct-v4 --num_envs 2048 --max_iterations 1000 \
#      --headless > /tmp/cinematographer_train_v4.log 2>&1"'

set -euo pipefail

EC2_IP="${EC2_IP:?Set EC2_IP first}"
PEM="${PEM:-$HOME/.ssh/trigunai_key.pem}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploying v4 mode-conditioned cinematographer to $EC2_IP ==="

# 1. SCP files to EC2 host
echo "[1/4] Copying v4 files to EC2 host..."
scp -i "$PEM" \
    "$SCRIPT_DIR/cinematographer_env_v4.py" \
    "$SCRIPT_DIR/cinematographer_env_cfg_v4.py" \
    "$SCRIPT_DIR/__init__v4.py" \
    "$SCRIPT_DIR/rl_games_ppo_v4_cfg.yaml" \
    "ubuntu@$EC2_IP:/home/ubuntu/"

# 2. Copy into container
echo "[2/4] Copying into isaaclab container..."
TASK_DIR="/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/cinematographer"
AGENT_DIR="$TASK_DIR/agents"

ssh -i "$PEM" "ubuntu@$EC2_IP" "bash -s" << REMOTE
set -e

# Copy env files
sudo docker cp /home/ubuntu/cinematographer_env_v4.py isaaclab:$TASK_DIR/cinematographer_env_v4.py
sudo docker cp /home/ubuntu/cinematographer_env_cfg_v4.py isaaclab:$TASK_DIR/cinematographer_env_cfg_v4.py

# Replace __init__.py with v4 version (registers both v0 and v4)
sudo docker cp /home/ubuntu/__init__v4.py isaaclab:$TASK_DIR/__init__.py

# Copy rl_games config
sudo docker cp /home/ubuntu/rl_games_ppo_v4_cfg.yaml isaaclab:$AGENT_DIR/rl_games_ppo_v4_cfg.yaml

echo "Files copied into container"

# Verify
sudo docker exec isaaclab bash -lc "ls -la $TASK_DIR/cinematographer_env_v4.py $TASK_DIR/cinematographer_env_cfg_v4.py $TASK_DIR/__init__.py $AGENT_DIR/rl_games_ppo_v4_cfg.yaml"
REMOTE

# 3. Quick syntax check inside container
echo "[3/4] Syntax check..."
ssh -i "$PEM" "ubuntu@$EC2_IP" \
    'sudo docker exec isaaclab bash -lc "python3 -c \"compile(open(\"'$TASK_DIR'/cinematographer_env_v4.py\").read(), \"env_v4.py\", \"exec\"); print(\"env_v4 OK\")\" && python3 -c \"compile(open(\"'$TASK_DIR'/cinematographer_env_cfg_v4.py\").read(), \"cfg_v4.py\", \"exec\"); print(\"cfg_v4 OK\")\""'

# 4. Test import (quick — just check the task registers)
echo "[4/4] Testing task registration..."
ssh -i "$PEM" "ubuntu@$EC2_IP" \
    'sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && ./isaaclab.sh -p -c \"import gymnasium as gym; import isaaclab_tasks; print(gym.spec(\\\"Isaac-Cinematographer-Direct-v4\\\"))\"" 2>&1 | tail -3'

echo ""
echo "=== v4 deployed! ==="
echo ""
echo "Start training:"
echo "  ssh -i $PEM ubuntu@$EC2_IP \\"
echo "    'sudo docker exec -d isaaclab bash -lc \"cd /workspace/isaaclab && \\"
echo "     ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \\"
echo "     --task Isaac-Cinematographer-Direct-v4 --num_envs 2048 --max_iterations 1000 \\"
echo "     --headless > /tmp/cinematographer_train_v4.log 2>&1\"'"
