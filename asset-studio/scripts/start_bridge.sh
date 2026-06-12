#!/usr/bin/env bash
# Starts the City Builder bridge — a small Node HTTP server that SSH's into
# EC2 to run the OSM → city.usd → colliders → AI textures → GLB pipeline,
# then serves the resulting GLB to the Asset Studio frontend.
#
# Required: EC2_IP (current public IP of TrigunAI-Omniverse)
# Optional: SSH_KEY (default ~/.ssh/trigunai_key.pem), BRIDGE_PORT (default 8765),
#           SYNC_SCRIPTS=1 to push local .py scripts to /home/ubuntu/ on every start.

set -e

if [ -z "$EC2_IP" ]; then
  echo "❌ EC2_IP not set."
  echo "   Get the current public IP of TrigunAI-Omniverse from the AWS console,"
  echo "   then re-run:"
  echo "     EC2_IP=<ip> ./scripts/start_bridge.sh"
  exit 1
fi

KEY="${SSH_KEY:-$HOME/.ssh/trigunai_key.pem}"
if [ ! -f "$KEY" ]; then
  ICLOUD_KEY="$HOME/Library/Mobile Documents/com~apple~CloudDocs/TrigunSAI/trigunai_key.pem"
  if [ -f "$ICLOUD_KEY" ]; then
    KEY="$ICLOUD_KEY"
  else
    echo "❌ SSH key not found at $KEY or in iCloud."
    echo "   Set SSH_KEY=path/to/trigunai_key.pem"
    exit 1
  fi
fi

export EC2_IP
export SSH_KEY="$KEY"
export BRIDGE_PORT="${BRIDGE_PORT:-8765}"
export SYNC_SCRIPTS="${SYNC_SCRIPTS:-0}"

DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec node "$DIR/bridge/server.mjs"
