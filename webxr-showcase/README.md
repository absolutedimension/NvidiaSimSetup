# TrigunAI WebXR Showcase

A fully immersive WebXR app for **Quest 3 / Quest 3S / Quest Pro browsers**, built with React + Three Fiber + `@react-three/xr`. Loads OpenUSD scenes (auto-converted to GLB on the EC2 backend by headless Blender) and lets you walk through them in VR — **no Unity, no APK, no app store**.

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│  Quest 3 Browser                                   │
│                                                    │
│  https://*.trycloudflare.com                       │
│  → React + R3F + @react-three/xr → "Enter VR"      │
└─────────────────┬──────────────────────────────────┘
                  │ HTTPS (mandatory for WebXR)
                  ▼
┌────────────────────────────────────────────────────┐
│  Cloudflare Tunnel  (free, no domain needed)       │
└─────────────────┬──────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────┐
│  EC2 nginx :8080                                   │
│  /var/www/showcase/                                │
│   ├── index.html   ← Vite production build         │
│   ├── assets/*.js                                  │
│   └── assets/*.glb ← Blender-converted USDs        │
└────────────────────────────────────────────────────┘
```

---

## First-Time Setup (Mac side)

```bash
cd webxr-showcase
npm install
```

## One-Time Setup (EC2 side)

```bash
./scripts/setup_ec2_serving.sh    # installs nginx config + cloudflared
```

## Workflow Each Time You Iterate

```bash
# 1. Convert your USD → GLB (runs Blender on EC2)
ssh -i ~/.ssh/trigunai_key.pem ubuntu@98.83.147.64 \
  "blender --background --python /tmp/usd_to_glb.py -- \
     --input  /tmp/showcases/IsaacWarehouse/IsaacWarehouse.usd \
     --output /var/www/showcase/assets/warehouse.glb \
     --decimate 0.25 --max-texture 1024"

# 2. Build + deploy the React app
./scripts/deploy_to_ec2.sh

# 3. Start public HTTPS tunnel (keep this terminal open)
./scripts/start_tunnel.sh
# → prints https://<random>.trycloudflare.com

# 4. On your Quest 3:
#    Open Browser → paste the URL → tap "Enter VR"
```

## How to Use the App

**Desktop (sanity-check first):**
- Drag to orbit, scroll to zoom
- Pick a showcase from the panel

**Quest:**
- Open the URL in the Quest browser
- Tap "Enter VR" → fully immersive
- Teleport with controller pointer or hand pointer
- Walk around the OpenUSD scene with thumbsticks

---

## Performance Notes for Quest

Quest 3's Adreno 740 budget:
- **Geometry:** stay under ~1.5M triangles per scene
- **Textures:** clamp to **1024×1024** for non-hero materials (`--max-texture 1024`)
- **GLB total:** under **80 MB** for fast loads over Cloudflare
- **Frame rate:** target 72 fps (90 fps for premium feel)

The `usd_to_glb.py` decimator + texture-clamp keeps even the IsaacWarehouse showcase within budget.

---

## Roadmap

- Phase 1 ✅ Static USD showcase in immersive VR
- Phase 2 ⏳ Live update — trigger Material/Texture agents from inside VR
- Phase 3 ⏳ Multi-room navigation (showcase carousel)
- Phase 4 ⏳ Hand tracking + spatial UI panels in VR
