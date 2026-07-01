# WhatsApp message templates (one-time Meta setup)

Proactive (business-initiated) messages — the daily SRS recall pings and broadcasts sent outside a
student's 24h reply window — **require Meta-approved templates**. Create these two once. Utility
templates are usually approved in minutes.

**Where:** Meta → WhatsApp Manager → **Manage templates** → **Create template**
(or business.facebook.com → WhatsApp Manager → Templates). Category = **Utility**, Language = English (US).

### 1. `gurukul_recall`  (drives the daily SRS ping)
- Name: `gurukul_recall`
- Category: **Utility**
- Body:
  ```
  🪔 Quick recall, no peeking: {{1}}

  Reply with your answer — Acharya
  ```
- Add a sample for `{{1}}`: `Name the 4 steps of the agent loop, in order.`
- Submit. Once **Approved**, the SRS cron uses it automatically (`{{1}}` = the recall question).

### 2. `gurukul_announce`  (drives broadcasts)
- Name: `gurukul_announce`
- Category: **Utility**
- Body:
  ```
  🪔 TrigunAI Gurukul

  {{1}}
  ```
- Sample for `{{1}}`: `Live class tonight at 5pm. Bring your agent.py.`
- Use via: `node broadcast.mjs --template gurukul_announce --param "your message"`

## Notes
- Until a template is approved, proactive sends fail with a `(#132001)`-type error naming the template
  — the cron logs this and tells you to create it.
- Students **within** their 24h window (messaged you recently) can also get plain text — `broadcast.mjs`
  without `--template` uses free-form for those.
- On the **test number** you can only use templates you create on its WABA; on your production number,
  same templates carry over.
