# RTX USD Viewer — render proxy

Bridges the **landing-page viewer** (`landing-page/src/Viewer.tsx`, route `#/viewer`)
to the **existing OVRTX renderer** on EC2 (`:8001`). Browser sends camera orbit
angles → this proxy bakes a `/World/Camera` USDA → OVRTX `/render` → RTX PNG back.

No new heavy infra: reuses the same OVRTX container + nginx/cloudflared the WebXR
showcase already uses.

## Deploy on EC2 (where OVRTX is localhost:8001)

```bash
EC2_IP=<current public IP>
PEM=~/.ssh/trigunai_key.pem

# 1. copy the proxy up
scp -i $PEM viewer-backend/render_proxy.py ubuntu@$EC2_IP:/home/ubuntu/

# 2. seed at least one asset where OVRTX can resolve it.
#    OVRTX mounts host /tmp as /host_tmp, so assets go in /tmp/viewer_assets/.
ssh -i $PEM ubuntu@$EC2_IP '
  mkdir -p /tmp/viewer_assets
  # example: reuse an asset already on the box
  cp /tmp/cf2x.usd /tmp/viewer_assets/ 2>/dev/null || true
  ls /tmp/viewer_assets'

# 3. run the proxy (port 8010)
ssh -i $PEM ubuntu@$EC2_IP '
  pip install --break-system-packages -q fastapi "uvicorn[standard]" requests
  ASSET_DIR_HOST=/tmp/viewer_assets ASSET_DIR_OVRTX=/host_tmp/viewer_assets \
    nohup python3 /home/ubuntu/render_proxy.py > /tmp/viewer_proxy.log 2>&1 &'

# 4. expose :8010 publicly (quick tunnel) and copy the printed URL
ssh -i $PEM ubuntu@$EC2_IP 'cloudflared tunnel --url http://localhost:8010'
```

Then open the landing page → **RTX Viewer** (nav) → paste the `*.trycloudflare.com`
URL into the **EC2 viewer API** box → pick an asset → drag to orbit.

Shortcut: `#/viewer?api=https://xyz.trycloudflare.com` pre-fills the endpoint.

## Endpoints
- `GET  /viewer/health`  → `{proxy, ovrtx, asset_dir}`
- `GET  /viewer/assets`  → `{assets: [...]}` (USD files in `$ASSET_DIR_HOST`)
- `POST /viewer/render`  → `{png: "data:image/png;base64,...", camera: {...}}`
  body: `{asset, az, el, dist, target?, width, height, focal_length}`

## Notes / limits
- **Single-frame re-render**, not a live stream. Each orbit-settle = one OVRTX
  render (~hundreds ms–seconds). True WebRTC streaming (`ovstream`) is a later upgrade.
- Asset reference path must be OVRTX-resolvable (`/host_tmp/...`). `/tmp` is
  ephemeral on stop — re-seed `/tmp/viewer_assets` after every EC2 restart.
- CORS is open (`*`); tighten `allow_origins` to the landing-page origin for prod.
- Camera target defaults to origin; zoom (distance) frames the asset. A future
  pass can auto-frame from the asset bbox (needs `pxr` on the box).
