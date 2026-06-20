# TrigunAI LMS — Deployment (Azure)

Deployed 2026-06-19 to the existing `trigunai-env` Container Apps environment.

## Live URLs
- Azure default: `https://lms.redflower-9a33748c.eastus.azurecontainerapps.io`
- Target custom domain: `https://lms.trigunai.com` (binding pending DNS — see below)

## Azure resources (all in resource group `trigunai-video-creator`)

| Resource | Name | Notes |
|---|---|---|
| Container App | `lms` | env `trigunai-env`, image `trigunaicr.azurecr.io/lms:v2`, 1 replica, 0.5 vCPU / 1 GiB |
| Container Registry | `trigunaicr` (reused) | image repo `lms` |
| Postgres flexible server | `trigunai-lms-pg` | **Central US** (East US/EUS2 were capacity-restricted), B1ms, v16, db `lms`, user `lmsadmin` |
| Email (ACS) | `trigunai-lms-acs` + `trigunai-lms-email` | free Azure-managed domain, sender `DoNotReply@29dd5f73-309b-46d8-9719-782b5bc14bef.azurecomm.net` |
| Azure OpenAI | `trigunai-lms-aoai` (East US) | `gpt-4o-mini` deployment (GlobalStandard), powers the TrigunAI guide. Endpoint `https://trigunai-lms-aoai.openai.azure.com`. Pay-per-token (~₹0/idle). |

## Secrets (stored as Container App secrets — not in git)
- `dburl` — full Postgres connection string (contains the DB admin password)
- `seckey` — session signing key
- `acsconn` — ACS connection string
Retrieve/rotate via `az containerapp secret ...` or the Azure portal. The Postgres admin
password can be reset with `az postgres flexible-server update --admin-password`.

## Env vars on the app
`DATABASE_URL=secretref:dburl` · `SECRET_KEY=secretref:seckey` ·
`ACS_CONNECTION_STRING=secretref:acsconn` · `ACS_SENDER=DoNotReply@…azurecomm.net` ·
`BASE_URL=https://lms.trigunai.com` · `ADMIN_EMAILS=deepak@trigunai.com`

## Redeploy after a code change
```bash
cd lms
az acr build --registry trigunaicr --image lms:vN --file Dockerfile .
az containerapp update -n lms -g trigunai-video-creator --image trigunaicr.azurecr.io/lms:vN
```

## Bind the custom domain lms.trigunai.com  (after the DNS records are added)

DNS records to add at the trigunai.com DNS host:
- `CNAME  lms        -> lms.redflower-9a33748c.eastus.azurecontainerapps.io`
- `TXT    asuid.lms  -> D1F2B9D34280A5304D9E846DBFE52C8415A7E85968AE352F42661222BBC99D74`

Then run:
```bash
az containerapp hostname add  -n lms -g trigunai-video-creator --hostname lms.trigunai.com
az containerapp hostname bind -n lms -g trigunai-video-creator --hostname lms.trigunai.com \
  --environment trigunai-env --validation-method CNAME
```
(Managed TLS cert auto-provisions; `https://lms.trigunai.com` goes green in a few minutes.)

## Follow-ups / hardening
- Restrict Postgres firewall from allow-all (`0.0.0.0-255.255.255.255`) to the env's static
  outbound IP `48.206.251.175/32` once confirmed stable.
- Add Alembic migrations before the schema changes post-launch (currently `create_all` on boot).
