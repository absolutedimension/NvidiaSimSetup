#!/usr/bin/env bash
# One-command orchestrator for the RAG-vs-fine-tune experiment ON the A10G box.
# Assumes: run from question_bank_engine/experiments/rag_vs_finetune, LLM proxy on :4000,
# CUDA + deps installed. Idempotent-ish; re-running regenerates artifacts.
set -euo pipefail
cd "$(dirname "$0")"

export QBANK_LLM=on
export QBANK_LLM_BASE_URL="${QBANK_LLM_BASE_URL:-http://localhost:4000/v1}"
export QBANK_LLM_API_KEY="${QBANK_LLM_API_KEY:-sk-trigunai-master-key-2026}"
export BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
export JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o}"

echo "== 0. prepare data =="; python3 prepare_data.py

echo "== 1. Arm A: RAG generation =="; python3 gen_rag.py

echo "== 2. train LoRA ($BASE_MODEL) =="; python3 train_lora.py

echo "== 3. Arm B: fine-tuned generation =="
FT_MODEL_DIR=artifacts/lora-qwen python3 gen_ft.py

echo "== 4. judge both arms (blind, $JUDGE_MODEL) =="
python3 judge.py artifacts/out_rag.json artifacts/scored_rag.json
python3 judge.py artifacts/out_ft.json  artifacts/scored_ft.json

echo "== 5. report =="
python3 judge.py --report artifacts/scored_rag.json artifacts/scored_ft.json
