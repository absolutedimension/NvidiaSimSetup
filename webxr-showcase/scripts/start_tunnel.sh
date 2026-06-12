#!/usr/bin/env bash
# Starts a free public HTTPS tunnel via Cloudflare to the EC2 nginx
# Prints a https://<random>.trycloudflare.com URL. Keep this terminal open.

set -e

EC2_IP="${EC2_IP:-98.83.147.64}"
KEY="${KEY:-$HOME/.ssh/trigunai_key.pem}"

echo "🌐 Starting public HTTPS tunnel to EC2 nginx :8080"
echo "   The URL will appear below. Open it on your Quest browser."
echo ""

exec ssh -i "$KEY" -t ubuntu@"$EC2_IP" \
  "cloudflared tunnel --url http://localhost:8080 --no-autoupdate"
