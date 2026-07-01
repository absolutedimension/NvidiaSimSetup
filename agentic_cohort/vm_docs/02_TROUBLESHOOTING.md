# Troubleshooting & Gotchas — TrigunAI Gurukul

> Hard-won rules. When something "doesn't work," check here first.

## WhatsApp delivery rules (the #1 source of confusion)
**Free-form text only delivers inside a 24-hour window that the STUDENT opened by messaging first.**
- Outside that window, Meta returns 200 ("sent") but WhatsApp **silently drops delivery**.
- Only an **approved template** (`gurukul_recall`, `gurukul_announce`, `hello_world`) crosses a closed window.
- Diagnose "sent but not arriving": `journalctl --user -u wa-bridge | grep "inbound <- <num>"`. If 0 inbounds,
  their window is CLOSED → have them message the bot first ("hi"), or send a template — not free-form.
- This is true on the production number too — NOT a sandbox quirk.

## Onboarding a student (the correct pattern)
Students must **message the bot first** ("hi" / "JOIN"). That one message: opens their 24h window AND
auto-triggers Acharya's welcome (the bridge sets a `greeted` flag and injects a FIRST-CONTACT instruction).
Do NOT push a free-form welcome to someone who hasn't messaged — it won't deliver.

## TEST number limitations (current: +1 555-662-2646)
- Max **5 recipients**, each added manually in Meta dashboard (API Setup → To → Manage list) with an OTP.
- Inbound can be flaky/confusing for non-primary numbers; it's an unfamiliar US number.
- These ALL disappear on the **production number** (+919135255107, pending verification — see 03_whatsapp).
- Do not waste time fighting sandbox inbound for real students — wait for production.

## Why we are NOT on WhatsApp Web (history — do not revert)
The OpenClaw native WhatsApp plugin uses **WhatsApp Web** (QR link). It logged out repeatedly (3× in 90 min)
— inherent fragility of the unofficial linked-device path, made worse by gateway restarts. We pivoted to the
**official Meta Cloud API + a custom bridge** (`wa_bridge.mjs`), which is server-to-server and never logs out.
The old `whatsapp` channel is disabled. Do not re-enable it for production.

## Bridge replies the fallback ("one sec — I hit a snag")
The `openclaw agent` call returned nothing. Check:
- `journalctl --user -u wa-bridge` for an "openclaw error".
- Model health: `openclaw infer model run --model microsoft-foundry/gpt-5.5 --prompt ping` (expect a reply).
- The reply is parsed from `result.payloads[].text` of `openclaw agent --json` — if OpenClaw changes that
  shape, update the parser in `wa_bridge.mjs` (askAcharya/askAdmin).

## GPT-5 models reject the request (schema/tool payload error)
GPT-5-series Azure deployments need the **Responses API**. In `concepts`/provider config, the model entry
must have `"api": "azure-openai-responses"` (gpt-5.3-codex AND gpt-5.5 when used by the agent with tools).
Set via `openclaw config patch` under `models.providers."microsoft-foundry".models[]`.

## Memory index fails ("No API key for provider openai")
OpenClaw semantic memory wants an embeddings model; the Azure resource has none deployed. Not needed for
core teaching (per-student context comes from the Learner Profile + session). Add a text-embedding
deployment later if semantic recall is wanted.

## SRS ping fails: "(#132001) Template name does not exist"
The `gurukul_recall` template isn't created/approved yet in Meta. Create it (utility, body `{{1}}`) in
WhatsApp Manager → Templates. Until then, proactive pings to out-of-window students can't deliver.
Free-form replies to active students work fine.

## WhatsApp session / token
- Token is a **permanent System User token** (never expires) in `~/.openclaw/wa_cloud.env`. If sends start
  failing with auth errors, regenerate it (Business Settings → System Users) and update `META_TOKEN`.
- The webhook callback + `messages` field subscription live at the Meta App level (App `1047742064872397`).
  If inbound stops entirely, re-check: `GET /<app>/subscriptions` has `messages`, and `GET /<WABA>/subscribed_apps`
  lists this app.

## Gateway / bridge won't start
`systemctl --user status wa-bridge openclaw-gateway` → read the error. Common: node path (service sets
`PATH=%h/.npm-global/bin`), or a syntax error in a just-edited file (restore the `.bak`).
