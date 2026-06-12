# TrigunAI Asset Studio (Phase A)

React + Three Fiber frontend for the NVIDIA Content Agents pipeline.

Upload a USD asset → pick an agent (Material / Physics / Texture) → watch
the EC2 backend process it → see the rendered output back in a 3D viewport.

---

## One-Time Setup

```bash
cd asset-studio
npm install
```

## Each Time You Use It

You need **two terminals** open:

### Terminal 1 — SSH tunnel to EC2 (backend access)

```bash
npm run tunnel
```

This forwards `localhost:8000` → Material Agent, `:8002` → Physics, `:8004` → Texture.
Leave this terminal running. If the EC2 public IP has changed, set `EC2_IP=<new-ip>` before running.

### Terminal 2 — Frontend dev server

```bash
npm run dev
```

Opens `http://localhost:5173` automatically.

---

## How to Use

1. Pick an agent in the left panel — green dot = healthy
2. Click **Upload USD**, pick a `.usd` / `.usda` / `.usdz` file
3. Watch progress in the bottom-left panel
4. When complete:
   - Final render appears as a textured plane in the 3D viewport
   - Predictions table appears on the right
   - Orbit / pan with mouse to inspect

---

## Architecture

```
Browser (Vite dev server, localhost:5173)
   │
   │  axios POST/GET to localhost:8000/8002/8004
   │
   ▼
SSH tunnel (Terminal 1)
   │
   ▼
EC2 ubuntu@98.83.147.64
   ├── Material Agent  :8000  → LiteLLM :4000 → Azure gpt-4o-mini
   ├── Physics Agent   :8002  → LiteLLM :4000 → Azure gpt-4o-mini
   └── Texture Agent   :8004  → LiteLLM :4000 → Azure gpt-image-1.5
```

---

## What's Next (Phases B & C)

- Phase B: multi-asset scenes, lighting controls, keyframe camera paths
- Phase C: animation agent + render farm + ffmpeg video encode
