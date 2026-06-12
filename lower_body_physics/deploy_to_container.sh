#!/bin/bash
# Deploy Lower Body Physics env to the isaaclab container on EC2.
#
# Usage:
#   EC2_IP=<ip> ./deploy_to_container.sh
#
# What it does:
#   1. SCPs all env files to EC2 host /tmp/lb_deploy/
#   2. Docker-copies them into the isaaclab container at the correct task path
#   3. Patches isaaclab_tasks/direct/__init__.py to import the new task
#   4. Copies lb_trajectory_v1.npz into the container
#
# After running:
#   ssh -i $PEM ubuntu@$EC2_IP 'sudo docker exec isaaclab bash -lc \
#     "cd /workspace/isaaclab && ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
#      --task Isaac-Humanoid-AMP-LowerBody-Direct-v0 --algorithm AMP \
#      --num_envs 256 --max_iterations 20 --headless"'

set -euo pipefail

EC2_IP="${EC2_IP:?Set EC2_IP first}"
PEM="${PEM:-$HOME/.ssh/trigunai_key.pem}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_NAME="humanoid_amp_lower_body"
CONTAINER_TASKS="/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct"
CONTAINER_DEST="${CONTAINER_TASKS}/${TASK_NAME}"

echo "=== Deploying Lower Body Physics env to EC2 ${EC2_IP} ==="

# 1. Create staging dir and SCP files
echo "[1/4] Uploading files to EC2..."
ssh -i "$PEM" ubuntu@"$EC2_IP" 'rm -rf /tmp/lb_deploy && mkdir -p /tmp/lb_deploy/agents'

scp -i "$PEM" \
    "$SCRIPT_DIR/__init__.py" \
    "$SCRIPT_DIR/humanoid_amp_lower_body_env.py" \
    "$SCRIPT_DIR/humanoid_amp_lower_body_env_cfg.py" \
    "$SCRIPT_DIR/lb_trajectory_v1.npz" \
    ubuntu@"$EC2_IP":/tmp/lb_deploy/

scp -i "$PEM" \
    "$SCRIPT_DIR/agents/skrl_amp_cfg.yaml" \
    ubuntu@"$EC2_IP":/tmp/lb_deploy/agents/

# 2. Docker-copy into the container
echo "[2/4] Copying into isaaclab container..."
ssh -i "$PEM" ubuntu@"$EC2_IP" "
    sudo docker exec isaaclab bash -c 'mkdir -p ${CONTAINER_DEST}/agents'
    sudo docker cp /tmp/lb_deploy/__init__.py isaaclab:${CONTAINER_DEST}/__init__.py
    sudo docker cp /tmp/lb_deploy/humanoid_amp_lower_body_env.py isaaclab:${CONTAINER_DEST}/humanoid_amp_lower_body_env.py
    sudo docker cp /tmp/lb_deploy/humanoid_amp_lower_body_env_cfg.py isaaclab:${CONTAINER_DEST}/humanoid_amp_lower_body_env_cfg.py
    sudo docker cp /tmp/lb_deploy/lb_trajectory_v1.npz isaaclab:${CONTAINER_DEST}/lb_trajectory_v1.npz
    sudo docker cp /tmp/lb_deploy/agents/skrl_amp_cfg.yaml isaaclab:${CONTAINER_DEST}/agents/skrl_amp_cfg.yaml
"

# 3. Patch the direct/__init__.py to import our task (idempotent)
echo "[3/4] Registering task in isaaclab_tasks..."
ssh -i "$PEM" ubuntu@"$EC2_IP" "
    sudo docker exec isaaclab bash -c '
        INIT_FILE=\"${CONTAINER_TASKS}/__init__.py\"
        IMPORT_LINE=\"from .${TASK_NAME} import *\"
        if ! grep -qF \"\$IMPORT_LINE\" \"\$INIT_FILE\" 2>/dev/null; then
            echo \"\" >> \"\$INIT_FILE\"
            echo \"# Lower Body Physics AMP task\" >> \"\$INIT_FILE\"
            echo \"\$IMPORT_LINE\" >> \"\$INIT_FILE\"
            echo \"  Added import to \$INIT_FILE\"
        else
            echo \"  Import already present in \$INIT_FILE\"
        fi
    '
"

# 4. Verify deployment
echo "[4/4] Verifying deployment..."
ssh -i "$PEM" ubuntu@"$EC2_IP" "
    sudo docker exec isaaclab bash -c '
        echo \"Files deployed:\"
        ls -la ${CONTAINER_DEST}/
        echo \"\"
        echo \"Checking import...\"
        cd /workspace/isaaclab && python3 -c \"
import isaaclab_tasks.direct.${TASK_NAME}
import gymnasium as gym
spec = gym.spec(\\\"Isaac-Humanoid-AMP-LowerBody-Direct-v0\\\")
print(f\\\"✓ Task registered: {spec.id}\\\")
print(f\\\"  entry_point: {spec.entry_point}\\\")
\" 2>&1 || echo \"⚠ Import check failed — see errors above\"
    '
"

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Smoke test (20 iters):"
echo "  ssh -i $PEM ubuntu@$EC2_IP 'sudo docker exec isaaclab bash -lc \\"cd /workspace/isaaclab && \\"
echo "    ./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \\"
echo "      --task Isaac-Humanoid-AMP-LowerBody-Direct-v0 --algorithm AMP \\"
echo "      --num_envs 256 --max_iterations 20 --headless\\"'"
