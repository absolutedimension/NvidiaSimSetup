# WhatsApp Gurukul — setup runbook

> Deploy the AI Gurukul tutor (see AI_GURUKUL_DESIGN.md) on a fresh Azure VM, channel = **WhatsApp
> Cloud API (official, direct)**, WhatsApp-only. Tutor = OpenClaw skill `gurukul-tutor` (Learner
> Model in OpenClaw memory + concept bank + spaced-retrieval + curiosity hooks).
>
> **Key cost fact:** proactive pings are business-initiated → need Meta-approved templates (~₹0.15
> each in India). A `{{1}}` variable lets ONE template carry any concept, so ~3 templates total.
> Student replies open a free 24h window for full free-form tutoring. ~₹3/day for a 20-student cohort.

---

## Phase 0 — VM networking (finish the Azure create with these)
- Image: **Ubuntu Server 24.04 LTS** (Canonical stock — NOT a marketplace OpenClaw image)
- Size: **Standard_B2s** (burstable, 2 vCPU / 4 GB). B2ms if more headroom wanted.
- **Public IP: Static** (Networking tab) — the webhook domain must resolve to a stable IP.
- **NSG inbound: allow 22 (SSH) + 443 (HTTPS webhook).** (Caddy handles the :80 ACME challenge.)
- Auth: SSH public key. User: `dk_trigun`.

## Phase 1 — Meta / WhatsApp account (do in parallel with the VM)
1. Meta Business account → business.facebook.com (likely already have one for TrigunAI).
2. developers.facebook.com → **Create App** → add the **WhatsApp** product.
3. Get a **WhatsApp Business Account (WABA)** + phone number. Start with Meta's **free test number**;
   add your real number later (needs business verification for production volume).
4. Collect + store securely (these go in the VM `.env`, never commit):
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_BUSINESS_ACCOUNT_ID` (WABA ID)
   - `WHATSAPP_ACCESS_TOKEN` — use a **System User permanent token**, not the 24h dev token
   - `WHATSAPP_APP_SECRET` (to verify webhook signatures)
   - `WHATSAPP_VERIFY_TOKEN` — a random string YOU pick for webhook handshake
5. Complete **Meta business verification** (needed for your own number + higher limits).

## Phase 2 — VM base + domain + TLS
1. SSH in: `ssh -i <key.pem> dk_trigun@<static-ip>`
2. `sudo apt update && sudo apt upgrade -y` ; install runtime per OpenClaw (Node and/or Python, git).
3. DNS: add an **A record** `gurukul.trigunai.com → <static-ip>`.
4. Install **Caddy** (auto Let's Encrypt TLS) reverse-proxying to OpenClaw's webhook port:
   ```
   gurukul.trigunai.com {
       reverse_proxy localhost:<openclaw_webhook_port>
   }
   ```
   (Same Caddy+systemd pattern already used for rtx.trigunai.com.)

## Phase 3 — OpenClaw + WhatsApp connector
1. Install OpenClaw (mirror the proven setup on 20.17.160.162).
2. Enable/add the **WhatsApp Cloud API connector**:
   - **Inbound:** a `GET /webhook` that echoes `hub.challenge` when `hub.verify_token` matches
     `WHATSAPP_VERIFY_TOKEN`; a `POST /webhook` that verifies the `X-Hub-Signature-256` against
     `WHATSAPP_APP_SECRET`, then routes the message to the orchestrator.
   - **Outbound:** POST to `https://graph.facebook.com/v21.0/<PHONE_NUMBER_ID>/messages` with the
     access token — free-form text inside the 24h window, **template** messages outside it.
   - ⚠ Confirm whether the existing OpenClaw has a WhatsApp connector or if this needs adding.
3. In Meta App → WhatsApp → Configuration: set **Callback URL** = `https://gurukul.trigunai.com/webhook`,
   **Verify token** = your `WHATSAPP_VERIFY_TOKEN`, then **Subscribe** to the `messages` field.
4. Run OpenClaw as a **systemd** service (auto-restart, survives reboot).

## Phase 4 — Gurukul skill + templates
1. Deploy the `gurukul-tutor` skill: Learner Model (OpenClaw memory, one record/student) + the
   concept bank from AI_GURUKUL_DESIGN.md §5 + grading + SRS update logic.
2. Submit WhatsApp **message templates** for approval (Meta → WhatsApp Manager → Templates),
   category **Utility**:
   - `daily_recall` — body: `🧠 TrigunAI Gurukul — quick recall (no peeking): {{1}}  Reply with your answer.`
   - `curiosity_hook` — body: `🤔 Before today's lesson: {{1}}  Take a guess — reply your hunch.`
   - `streak_nudge` — body: `🔥 {{1}}-day streak! One quick question keeps it alive: {{2}}`
   (One variable carries any concept → 3 templates cover everything.)
3. **Cron** (daily): scan all Learner Models → for each student with an SRS item due, send the
   `daily_recall` template with the due concept's question. New concept → `curiosity_hook` first.
4. **Inbound reply** (inside 24h window, free): grade vs answer-gist → update mastery + SRS interval
   (correct → ×2.5, miss → reset to 1d + send the micro-explanation) → optionally hook next concept.

## Phase 5 — verify
- Message the WABA number from a test phone → confirm inbound hits the webhook → bot replies.
- Force an SRS item due → confirm the cron sends the `daily_recall` template → reply → confirm
  grading + Learner Model update.
- Add the real cohort students (their WhatsApp numbers) to the roster.

---

## Open items to confirm before building Phase 3
- [ ] Does the existing OpenClaw have a WhatsApp Cloud API connector, or add one?
- [ ] Real sending number (vs Meta test number) — needs business verification; start on test number.
- [ ] Student opt-in: WhatsApp requires users to have messaged first OR opted in. Cohort students
      enrolled, so capture an explicit "message YES to start" opt-in at onboarding.

*Runbook owner: Deepak. Companion to AI_GURUKUL_DESIGN.md.*

---

## ⚙️ DEPLOYMENT STATE (live — update as you go)

**Decision change (2026-06-26):** OpenClaw's native WhatsApp is **WhatsApp Web (QR-link)**, NOT the
Cloud API. Chose **Path A — native WhatsApp Web on a dedicated number**. So Phases 1/4 (Meta Cloud
API, webhooks, templates) are NO LONGER NEEDED. No domain/443/template/business-verification required.
Proactive SRS pings work freely over WhatsApp Web (no 24h-window/template limits). Trade-off accepted:
unofficial path, moderate ban risk — mitigated by dedicated number + opt-in + low conversational volume.

**The new (simpler) channel reality:**
- OpenClaw `cron` (native Gateway scheduler) drives the SRS pings — no external cron needed.
- WhatsApp via `openclaw channels login --channel whatsapp` (scan QR with the dedicated number).

### VM coordinates
| Item | Value |
|---|---|
| Public IP | **20.219.2.53** (static) |
| SSH | `ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53` |
| Resource group | `trigunai-gurukul-rg` (Central India) · subscription `AzurePayAsgo` (cc469e97) |
| VM | `gurukul-prod` · Standard_B2s · Ubuntu 24.04 · ports 22+443 open |

### Done ✅
- [x] VM provisioned (B2s, static IP, NSG 22+443, SSH key `~/.ssh/gurukul_key`)
- [x] Base: Node 22.23.1, npm prefix `~/.npm-global`, build tools
- [x] **OpenClaw 2026.6.10** installed (`npm i -g openclaw`)
- [x] **WhatsApp plugin** installed + registered — status: installed, not configured, disabled
- [x] Confirmed native `openclaw cron` scheduler exists (drives SRS pings)
- [x] **BRAIN: Azure OpenAI via `microsoft-foundry` provider (bundled plugin) — LIVE + verified**
  - Resource `trigunai-lms-aoai` (eastus, sub cb656d95, RG trigunai-video-creator), endpoint
    `https://trigunai-lms-aoai.openai.azure.com`. Key = **key2** (key1 was accidentally printed → REGENERATE key1).
  - Config: `models.providers."microsoft-foundry"` = { baseUrl, models:[{gpt-5.5},{gpt-5.3-codex, api:"azure-openai-responses"}] };
    default model `microsoft-foundry/gpt-5.5`; auth via `openclaw models auth paste-api-key --provider microsoft-foundry`.
  - ✅ gpt-5.5 → BRAIN_OK · ✅ gpt-5.3-codex → CODEX_OK (codex needs `api: azure-openai-responses`).
  - Persists without env vars (key in auth profile). `~/.aoai_key` removed.
- [x] **`trigun-ai-coding` skill deployed + "✓ ready"** — `~/.openclaw/workspace/skills/trigun-ai-coding/`,
  routes coding to gpt-5.3-codex / design to gpt-5.5. Local copy: `azure_migration/openclaw-studio/skills/trigun-ai-coding/`.
- [x] Workspace set: `agents.defaults.workspace = /home/dk_trigun/.openclaw/workspace`.

### Remaining ⏳ (in order)
1. **Memory index needs an embeddings provider.** `openclaw memory index` failed — wants provider "openai"
   embeddings. `trigunai-lms-aoai` has no embedding deployment. Either add a text-embedding deployment in
   Azure, or point memory embeddings at another provider. Needed for the Learner Model's semantic recall.
2. **Workspace identity** — `IDENTITY.md`/`SOUL.md`/`USER.md` for the *Gurukul tutor* persona.
3. **Deploy `gurukul-tutor` skill** — from AI_GURUKUL_DESIGN.md (Learner Model + concept bank + SRS + hooks).
4. **Gateway as systemd service** — auto-restart, survives reboot. (Config changes say "Restart the gateway to apply.")
5. **Cron job** for daily SRS scan → `daily_recall` to due students (`openclaw cron add`).
6. **[needs user] Link WhatsApp** — `openclaw channels login --channel whatsapp` → scan QR with the DEDICATED number.
7. **[needs user] Verify** end-to-end with a test student message.

### 🔐 Security TODO: regenerate key1 on `trigunai-lms-aoai` (was printed in a failed command). Using key2 now.

---

## 🔀 PIVOT to Direct Meta Cloud API (2026-06-26) — WhatsApp Web was too unstable

WhatsApp Web session logged out repeatedly (3×/90min) — unofficial-path fragility. Pivoted to the
**official Meta WhatsApp Cloud API** (server-to-server, no logouts/bans). OpenClaw has no native
direct-Meta channel, so built a **webhook bridge**.

**Architecture:** Meta Cloud API → webhook `https://gurukul.trigunai.com/webhook` →
`bridge.mjs` (Node, systemd `wa-bridge`) → `openclaw agent --to +<student> --message ... --json`
(per-student session = context, full persona+skills) → reply via Meta Graph API.

**Built + verified (server side):**
- [x] `bridge.mjs` deployed → `~/wa_bridge.mjs`, systemd `wa-bridge.service` (running, health ok on :8788).
  Repo copy: `agentic_cohort/whatsapp_cloud_bridge/bridge.mjs`.
- [x] Env `~/.openclaw/wa_cloud.env` (chmod 600): VERIFY_TOKEN=`8a402878d8b2bfd63bc2f4ecb1b1c1f6`,
  PORT=8788, GRAPH_VERSION=v21.0. **META_TOKEN + PHONE_NUMBER_ID = placeholders (fill after Meta setup).**
- [x] Caddy installed + Caddyfile (`gurukul.trigunai.com` → :8788). NSG ports 80+443 open.
- [x] DNS `gurukul.trigunai.com` → 20.219.2.53. **Let's Encrypt cert obtained.**
- [x] Webhook verified end-to-end: health 200, handshake echoes challenge, bad token → 403.

**Remaining (user does on Meta + then me):**
1. [user] Meta app (Business) + WhatsApp product → free **test number** → copy **Phone Number ID** + **temp token**;
   add +918454964893 as test recipient; set webhook URL+verify-token, subscribe to `messages`.
2. [me] Paste token+PhoneNumberID into `wa_cloud.env` → `systemctl --user restart wa-bridge` → test.
3. Old WhatsApp Web channel (`openclaw channels`) now unused — can disable to stop reconnect noise.

Webhook URL: `https://gurukul.trigunai.com/webhook` · Verify token: `8a402878d8b2bfd63bc2f4ecb1b1c1f6`

### ✅ WORKING END-TO-END (2026-06-26 06:02 UTC)
Full loop verified: inbound "hi" from +918454964893 → bridge → openclaw gpt-5.5 → reply sent via Graph API.
- Test number `+1 555 662-2646`, Phone Number ID `1205009339362440`, WABA `1060787129847082`, App ID `1047742064872397`.
- Webhook registered via API: `POST /{app-id}/subscriptions` (object=whatsapp_business_account, fields=messages) + `POST /{WABA}/subscribed_apps`. `messages` confirmed subscribed.
- Reply latency ~15s (gpt-5.5). Server-to-server → NO logouts.

### ⚠️ TODO before it matters
1. ✅ DONE — **Permanent System User token** installed (expires_at:0 / never), scopes whatsapp_business_messaging + whatsapp_business_management. In `~/.openclaw/wa_cloud.env`. Acharya survives indefinitely.
2. **App secret was shared in chat** (`e444...`) — regenerate in App settings → Basic when convenient (runtime uses the long-lived token, not the secret).
3. Production number — **BLOCKED until business verification completes (in progress as of 2026-06-26).**
   RESUME when verified: Meta app → WhatsApp → Step 2 Production setup → add number **+919135255107**
   (⚠ this REMOVES it from the regular WhatsApp app, permanent) → display name "TrigunAI Gurukul" →
   verify OTP (SMS/call) → register + set a 2-step PIN → copy the NEW Phone Number ID.
   Then (me, ~2 min): set `PHONE_NUMBER_ID=<new>` in `~/.openclaw/wa_cloud.env`; `POST /<new-WABA>/subscribed_apps`;
   confirm `messages` field still subscribed; `systemctl --user restart wa-bridge`; test inbound.
   After that: real Indian number, no allowed-list, no 5-cap, normal inbound — sandbox quirks gone.
   Meanwhile keep using the TEST number (+1 555-662-2646, Phone Number ID 1205009339362440, max 5 OTP-verified recipients).
4. Build the `gurukul-tutor` teaching layer (persona + Learner Model + concept bank + SRS cron via `openclaw cron`).
