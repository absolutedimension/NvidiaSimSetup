# WhatsApp / Meta Cloud API — Config & Production Migration

> The official Meta WhatsApp Cloud API setup powering the bridge. Secrets live in
> `~/.openclaw/wa_cloud.env` — never print them.

## Current config (TEST number)
| Item | Value |
|---|---|
| Mode | Meta WhatsApp **Cloud API** (official, server-to-server) |
| Test number | `+1 555-662-2646` |
| Phone Number ID | `1205009339362440` |
| WABA ID | `1060787129847082` |
| Meta App ID | `1047742064872397` |
| Webhook URL | `https://gurukul.trigunai.com/webhook` (Caddy TLS → bridge :8788) |
| Token | permanent System User token (never expires) — in `wa_cloud.env` |
| Env file | `~/.openclaw/wa_cloud.env`: META_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN, GRAPH_VERSION, ADMIN_NUMBERS |

## How the webhook is wired (already done)
- App-level subscription (callback URL + verify token + `messages` field):
  `POST /<APP_ID>/subscriptions` with `object=whatsapp_business_account`, `fields=messages`, app access token.
- WABA → app: `POST /<WABA_ID>/subscribed_apps` (with the token).
- Verify it's intact: `GET /<APP_ID>/subscriptions` (has `messages`) and `GET /<WABA_ID>/subscribed_apps`.

## Message templates (one-time, in Meta → WhatsApp Manager → Templates)
Proactive / out-of-window messages need approved **utility** templates with a `{{1}}` body variable:
- `gurukul_recall` — daily SRS ping. Body e.g.: `🪔 Quick recall, no peeking: {{1}}  Reply with your answer.`
- `gurukul_announce` — broadcasts. Body e.g.: `🪔 TrigunAI Gurukul: {{1}}`
Until approved, SRS pings + broadcasts to out-of-window students fail; free-form to active students works.

## ⬆️ PRODUCTION NUMBER MIGRATION (+919135255107) — pending business verification
**Blocked until Meta business verification completes** (in progress). When verified:

**On Meta (Deepak):**
1. WhatsApp → **Step 2. Production setup** → Add phone number → **+91 91352 55107**.
   ⚠️ This **removes that number from the regular WhatsApp app, permanently** — it becomes a Cloud-API number.
2. Display name: `TrigunAI Gurukul` (students see this) → may go through review.
3. Verify via OTP (SMS / voice to that number) → **Register** → set a 2-step PIN (save it).
4. Copy the **NEW Phone Number ID** for +919135255107.

**On the box (Sutradhaar, ~2 min):**
1. `cp ~/.openclaw/wa_cloud.env ~/.openclaw/wa_cloud.env.bak`
2. Set `PHONE_NUMBER_ID=<new id>` in `~/.openclaw/wa_cloud.env`. (Token usually stays — it's account-level;
   if the new number is under a new WABA, also confirm the token has access to it.)
3. Subscribe the new WABA: `POST /<new-WABA>/subscribed_apps` (token). Confirm `messages` field still subscribed.
4. `systemctl --user restart wa-bridge` → `curl -s localhost:8788/health`.
5. Test: message the production number from any phone → expect Acharya's welcome.

**After migration:** real Indian number, **no allowed-list, no 5-recipient cap, normal inbound from anyone
who opts in.** All the test-number friction disappears. Students just message your TrigunAI number.

## Routing recap
- `ADMIN_NUMBERS` (in wa_cloud.env, currently `918454964893`) → Sutradhaar (admin).
- Everyone else → Acharya (student tutor). Keep Deepak's number in ADMIN_NUMBERS; add student-test numbers
  only as students (not admin).
