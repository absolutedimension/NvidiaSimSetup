#!/bin/bash
# Curriculum training for Lower Body Physics
# Runs 3 phases with graduating AMP style weight:
#   Phase 1: 95% task / 5% style  (3000 iters) — learn to stand
#   Phase 2: 80% task / 20% style (3000 iters) — add natural motion
#   Phase 3: 65% task / 35% style (4000 iters) — full AMP
#
# Usage (inside isaaclab container):
#   cd /workspace/isaaclab
#   bash /workspace/isaaclab/run_curriculum_training.sh
#
# Total: 10000 iterations, ~3h on A10G at 256 envs

set -e

TASK="Isaac-Humanoid-AMP-LowerBody-Direct-v0"
ENVS=256
LOG_DIR="/tmp/curriculum_training.log"
TASK_DIR="source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp_lower_body"
AGENTS_DIR="${TASK_DIR}/agents"

echo "=============================================="
echo "  Lower Body Curriculum Training"
echo "  $(date -u)"
echo "=============================================="

# Phase 1: Stand first (95% task / 5% style)
echo ""
echo ">>> PHASE 1: Stand first (95/5 split, 3000 iters) <<<"
echo "    Start: $(date -u)"
cp ${AGENTS_DIR}/skrl_amp_curriculum_phase1.yaml ${AGENTS_DIR}/skrl_amp_cfg.yaml
./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
    --task $TASK --algorithm AMP \
    --num_envs $ENVS --max_iterations 3000 --headless 2>&1 | tee -a $LOG_DIR
echo "    Phase 1 done: $(date -u)"

# Find Phase 1 best checkpoint
P1_DIR=$(ls -td logs/skrl/humanoid_amp_lower_body_curriculum/*phase1* 2>/dev/null | head -1)
P1_CKPT="${P1_DIR}/checkpoints/best_agent.pt"
if [ ! -f "$P1_CKPT" ]; then
    echo "ERROR: Phase 1 checkpoint not found at $P1_CKPT"
    exit 1
fi
echo "    Phase 1 checkpoint: $P1_CKPT"

# Persist Phase 1
cp "$P1_CKPT" /home/ubuntu/lb_curriculum_phase1_best.pt 2>/dev/null || true

# Phase 2: Add natural motion (80% task / 20% style)
echo ""
echo ">>> PHASE 2: Natural motion (80/20 split, 3000 iters) <<<"
echo "    Start: $(date -u)"
echo "    Resuming from: $P1_CKPT"
cp ${AGENTS_DIR}/skrl_amp_curriculum_phase2.yaml ${AGENTS_DIR}/skrl_amp_cfg.yaml
./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
    --task $TASK --algorithm AMP \
    --num_envs $ENVS --max_iterations 3000 --headless 2>&1 | tee -a $LOG_DIR
echo "    Phase 2 done: $(date -u)"

# Find Phase 2 best checkpoint
P2_DIR=$(ls -td logs/skrl/humanoid_amp_lower_body_curriculum/*phase2* 2>/dev/null | head -1)
P2_CKPT="${P2_DIR}/checkpoints/best_agent.pt"
if [ ! -f "$P2_CKPT" ]; then
    echo "ERROR: Phase 2 checkpoint not found at $P2_CKPT"
    exit 1
fi
echo "    Phase 2 checkpoint: $P2_CKPT"
cp "$P2_CKPT" /home/ubuntu/lb_curriculum_phase2_best.pt 2>/dev/null || true

# Phase 3: Full AMP (65% task / 35% style)
echo ""
echo ">>> PHASE 3: Full AMP (65/35 split, 4000 iters) <<<"
echo "    Start: $(date -u)"
echo "    Resuming from: $P2_CKPT"
cp ${AGENTS_DIR}/skrl_amp_curriculum_phase3.yaml ${AGENTS_DIR}/skrl_amp_cfg.yaml
./isaaclab.sh -p scripts/reinforcement_learning/skrl/train.py \
    --task $TASK --algorithm AMP \
    --num_envs $ENVS --max_iterations 4000 --headless 2>&1 | tee -a $LOG_DIR
echo "    Phase 3 done: $(date -u)"

# Find Phase 3 best checkpoint
P3_DIR=$(ls -td logs/skrl/humanoid_amp_lower_body_curriculum/*phase3* 2>/dev/null | head -1)
P3_CKPT="${P3_DIR}/checkpoints/best_agent.pt"
if [ ! -f "$P3_CKPT" ]; then
    echo "ERROR: Phase 3 checkpoint not found at $P3_CKPT"
    exit 1
fi
echo "    Phase 3 checkpoint: $P3_CKPT"
cp "$P3_CKPT" /home/ubuntu/lb_curriculum_phase3_best.pt 2>/dev/null || true
cp "$P3_CKPT" /home/ubuntu/lb_curriculum_final.pt 2>/dev/null || true

echo ""
echo "=============================================="
echo "  CURRICULUM TRAINING COMPLETE"
echo "  $(date -u)"
echo "  Final checkpoint: /home/ubuntu/lb_curriculum_final.pt"
echo "=============================================="
