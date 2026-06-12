#!/usr/bin/env bash
# Builds the WebXR app locally, rsyncs to EC2 nginx webroot,
# and (re)starts the public HTTPS tunnel via cloudflared.
#
# Usage:  ./scripts/deploy_to_ec2.sh

set -e

EC2_IP="${EC2_IP:-98.83.147.64}"
KEY="${KEY:-$HOME/.ssh/trigunai_key.pem}"
WEBROOT="/var/www/showcase"

cd "$(dirname "$0")/.."

echo "▶ Building production bundle"
npm run build

echo "▶ Ensuring webroot exists on EC2"
ssh -i "$KEY" ubuntu@"$EC2_IP" "sudo mkdir -p $WEBROOT/assets && sudo chown -R ubuntu:ubuntu $WEBROOT"

echo "▶ Rsyncing dist/ to EC2:$WEBROOT (preserving *.glb, *.gltf, *.usd asset files)"
rsync -avz --delete \
  --exclude '*.glb' --exclude '*.gltf' --exclude '*.usd' --exclude '*.usdz' --exclude '*.ktx2' --exclude '*.bin' \
  -e "ssh -i $KEY" \
  dist/ ubuntu@"$EC2_IP":"$WEBROOT/"

echo "✅ Deployed. Open the public URL on your Quest browser."
