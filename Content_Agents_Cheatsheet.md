# Content Agents — Operator Cheatsheet
**Target machine:** ubuntu@98.83.147.64 (TrigunAI-Omniverse, g5.2xlarge)

> ⚠️ **The public IP changes every time the instance restarts.** Allocate an Elastic IP in AWS to lock it in once you're past MVP.

---

## SSH In
```bash
ssh -i ~/.ssh/trigunai_key.pem ubuntu@98.83.147.64
```

## What's Running
| Service | Container | Port | Purpose |
|---|---|---|---|
| LiteLLM proxy | `litellm-proxy` | 4000 | Translates OpenAI API → Azure OpenAI |
| OVRTX Rendering API | `ovrtx-rendering-api` | 8001 (host) | GPU-rendered multi-view images |
| Material Agent | `material-agent-service` | 8000 | Assigns materials to USD via VLM |

## Management Commands

### LiteLLM
```bash
cd ~/litellm
docker compose ps              # status
docker logs -f litellm-proxy   # logs
docker compose restart         # restart
docker compose down            # stop
docker compose up -d           # start
```

### Material Agent
**IMPORTANT:** Always pass `--env-file ../../.env` so VLM backend overrides (MA_VLM_BACKEND=openai, etc.) take effect. Without it, Compose uses the hardcoded `nim` defaults and ignores .env.

```bash
cd ~/content-agents/apps/material_agent_service
docker compose --env-file ../../.env ps
docker compose --env-file ../../.env logs -f
docker compose --env-file ../../.env restart
docker compose --env-file ../../.env down
docker compose --env-file ../../.env up -d
docker compose --env-file ../../.env up --build -d
```

## Health Checks
```bash
# LiteLLM
curl -s http://localhost:4000/health/liveness -H "Authorization: Bearer sk-trigunai-master-key-2026"

# Rendering API (from host)
curl -s http://localhost:8001/health

# Material Agent (from host, once running)
curl -s http://localhost:8000/health
```

## Test VLM Through LiteLLM Proxy
```bash
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-trigunai-master-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

## Run an Asset Through Material Agent
```bash
# Example: process a USD file through the REST API
curl -X POST http://localhost:8000/v1/material/run \
  -H "Content-Type: application/json" \
  -d '{"input_usd_path": "/path/to/your.usd"}'

# Or use the CLI (if installed via uv)
cd ~/content-agents
source .venv/bin/activate
material-agent run apps/material_agent/configs/unified_example.yaml
```

## GPU Monitoring
```bash
watch -n 2 nvidia-smi    # live GPU usage
```

## Cost Control
**Stop the instance when not using it** to avoid the ~$1/hr EC2 cost:
- AWS Console → EC2 → Instances → TrigunAI-Omniverse → Instance state → Stop

EBS storage continues billing (~$16/mo) even when stopped. Terminate only when fully done.

## Config Files on EC2
| File | Purpose |
|---|---|
| `~/litellm/config.yaml` | LiteLLM → Azure model mapping |
| `~/litellm/docker-compose.yml` | LiteLLM container config |
| `~/content-agents/.env` | API keys + backend overrides for all agents |
| `~/content-agents/apps/material_agent_service/docker-compose.yml` | Material agent compose |

## Rotating the Azure API Key (do this periodically)
1. Azure Foundry → your model → Manage keys → Regenerate
2. SSH in, edit `~/litellm/config.yaml`, replace the `api_key:` value
3. `cd ~/litellm && docker compose restart`
