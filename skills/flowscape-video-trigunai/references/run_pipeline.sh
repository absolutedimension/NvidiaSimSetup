#!/usr/bin/env bash
# Flowscape Engine — end-to-end (mirror of dj_engine/batch_5tracks.sh).
# Run on the EC2 A10G box. Assumes flowscape_engine/ is synced there and the
# litellm-proxy container is up on :4000 (CLAUDE.md §3).
set -euo pipefail
cd "$(dirname "$0")"

CHANNEL="${1:-https://www.youtube.com/@CleverSpacesGirl}"
MINUTES="${2:-30}"
AUDIO="${3:-}"                 # your own copyright-clean ambient bed (mp3)
COOKIES="${COOKIES:-}"        # cookies.txt to beat YouTube bot-block (optional)

echo "== 0. GATHER (analysis-only corpus) =="
python3 pull_corpus.py --channel "$CHANNEL" --max 12 ${COOKIES:+--cookies "$COOKIES"}

echo "== A. keyframes + visual grammar =="
python3 extract_keyframes.py --every 20
python3 visual_grammar_extract.py --grids-per-video 3

echo "== B. clean seeds (Flux) + VLM auto-filter =="
python3 seed_generate.py --n 300
python3 vlm_critic.py --mode seeds --min-score 7

echo "== C.1 train flowscape LoRA (our aesthetic) =="
python3 train_lora.py --name flowscape_v1 --steps 1500

echo "== C.2 scene plan + C.3 render =="
python3 scene_plan.py --minutes "$MINUTES" --name "flowscape_${MINUTES}min"
python3 render_flowscape.py \
  --plan "scene_plans/flowscape_${MINUTES}min.json" \
  --lora "loras/flowscape_v1/pytorch_lora_weights.safetensors" \
  ${AUDIO:+--audio "$AUDIO"}

echo "== verify =="
python3 vlm_critic.py --mode video --mp4 "output/flowscape_${MINUTES}min.mp4"
echo "DONE. Upload via trigunai-yt-flowart."
