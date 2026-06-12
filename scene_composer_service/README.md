# Scene Composer Agent

A 4th NVIDIA Content Agent in the TrigunAI factory: takes an OSM lat/lon/radius
plus a façade prompt and returns a textured, collision-ready USD city.

Mirrors the API contract of the existing Material/Physics/Texture agents so the
Asset Studio can drive it the same way.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/pipeline` | submit (form fields: `lat`, `lon`, `radius_m`, `name`, `facade_prompt`) → `{session_id, cached}` |
| `GET`  | `/pipeline/{sid}/status` | step + percent + elapsed |
| `GET`  | `/artifacts/{sid}/usd` | the final `city.usd` |
| `GET`  | `/artifacts/{sid}/textures` | zip of PBR maps |
| `GET`  | `/artifacts/{sid}/meta` | `meta.json` (bbox + building stats) |
| `GET`  | `/artifacts/{sid}/preview-glb` | best-effort decimated GLB |
| `GET`  | `/health` | `{status: "healthy"}` |

Steps reported by `/status`: `osm_fetch → geometry_extrude → collider_bake → texture_generate → texture_apply → completed`.

## Caching

A `(round(lat,6), round(lon,6), round(radius_m,1), lowercased prompt)` tuple is
hashed; the second submission with the same fingerprint reuses the prior
`session_id` and returns `cached: true`.

## Deploy on EC2

The container has no GPU dependency — it's a thin orchestrator. Put it on the
host alongside the existing agents:

```bash
ssh ubuntu@$EC2_IP
cd ~/NvidiaSimSetup/scene_composer_service     # this directory, rsynced over
docker compose up -d --build
curl localhost:8005/health
```

Verifying end to end:

```bash
SID=$(curl -s -X POST -F lat=40.7580 -F lon=-73.9855 -F radius_m=500 \
            -F name=manhattan_smoke \
            -F facade_prompt='weathered Manhattan high-rise façade' \
            http://localhost:8005/pipeline | jq -r .session_id)

watch -n 5 "curl -s http://localhost:8005/pipeline/$SID/status | jq"
# When status=completed:
curl -OJ http://localhost:8005/artifacts/$SID/usd
curl -OJ http://localhost:8005/artifacts/$SID/textures
curl http://localhost:8005/artifacts/$SID/meta | jq
```

## Local dev

```bash
pip install -r requirements.txt
COMPOSER_SCRIPTS_DIR=../webxr-showcase/scripts \
COMPOSER_OUT_BASE=/tmp/cities \
COMPOSER_TEXTURE_AGENT_BASE=http://localhost:8004 \
uvicorn app:app --reload --port 8005
```

The Texture Agent needs to be reachable (SSH-forward `-L 8004:localhost:8004`
the same way Asset Studio does it).
