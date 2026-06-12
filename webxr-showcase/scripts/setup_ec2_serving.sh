#!/usr/bin/env bash
# One-time setup: nginx static-serve config + cloudflared install.
# Run this from your Mac. It SSHes to EC2 and does everything there.

set -e

EC2_IP="${EC2_IP:-98.83.147.64}"
KEY="${KEY:-$HOME/.ssh/trigunai_key.pem}"

echo "▶ Configuring nginx on EC2 to serve /var/www/showcase on port 8080"

ssh -i "$KEY" ubuntu@"$EC2_IP" 'bash -s' <<'REMOTE'
set -e
sudo mkdir -p /var/www/showcase/assets
sudo chown -R ubuntu:ubuntu /var/www/showcase

sudo tee /etc/nginx/sites-available/showcase >/dev/null <<'NGINX'
server {
    listen 8080;
    server_name _;
    root /var/www/showcase;
    index index.html;

    # WebXR + SharedArrayBuffer require these:
    add_header Cross-Origin-Opener-Policy same-origin;
    add_header Cross-Origin-Embedder-Policy require-corp;
    add_header Cross-Origin-Resource-Policy cross-origin;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(glb|gltf|usdz|bin|ktx2)$ {
        expires 1d;
        add_header Cache-Control "public";
        add_header Cross-Origin-Resource-Policy cross-origin;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/showcase /etc/nginx/sites-enabled/showcase
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx

echo "✓ nginx serving /var/www/showcase on :8080"

# Install cloudflared if missing
if ! command -v cloudflared >/dev/null 2>&1; then
    echo "▶ Installing cloudflared"
    curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
    sudo dpkg -i /tmp/cloudflared.deb
    rm /tmp/cloudflared.deb
fi
cloudflared --version
REMOTE

echo ""
echo "✅ Done. Next:"
echo "   1) Build + deploy the app:    ./scripts/deploy_to_ec2.sh"
echo "   2) Start the public HTTPS tunnel (in a separate Terminal):"
echo "         ./scripts/start_tunnel.sh"
echo "      That will print a https://*.trycloudflare.com URL."
echo "      Open it in your Quest 3 Browser → tap 'Enter VR'."
