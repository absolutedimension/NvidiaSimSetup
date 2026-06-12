#!/usr/bin/env bash
# Opens an SSH tunnel from your Mac to the TrigunAI EC2 instance,
# forwarding all 3 agent ports to localhost. Keep this terminal open
# while using the Asset Studio.

set -e

EC2_IP="${EC2_IP:-98.83.147.64}"
KEY="${KEY:-$HOME/.ssh/trigunai_key.pem}"

if [ ! -f "$KEY" ]; then
  echo "❌ SSH key not found at $KEY"
  echo "   Set KEY=path/to/trigunai_key.pem"
  exit 1
fi

echo "🔗 Tunneling to $EC2_IP via $KEY"
echo "   localhost:8000 → Material Agent"
echo "   localhost:8002 → Physics Agent"
echo "   localhost:8004 → Texture Agent"
echo "   localhost:8005 → Scene Composer Agent"
echo ""
echo "Leave this terminal open. Open the Asset Studio at http://localhost:5173"
echo ""

exec ssh -N \
  -L 8000:localhost:8000 \
  -L 8002:localhost:8002 \
  -L 8004:localhost:8004 \
  -L 8005:localhost:8005 \
  -i "$KEY" \
  ubuntu@"$EC2_IP"
