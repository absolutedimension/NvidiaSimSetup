---
name: acharya-whatsapp-announce
description: >-
  Send a WhatsApp message through the Acharya (Meta Cloud API) channel — to ONE specific student,
  a few numbers, a whole COURSE cohort, or ALL students — using an APPROVED Meta template so it
  DELIVERS EVEN IF the student's 24-hour WhatsApp window is closed. Handles the #1 gotcha: free-form
  text only reaches people who messaged Acharya in the last 24h; outside that window Meta rejects it
  ("Re-engagement message"), so this skill sends via the approved `gurukul_announce` template (with a
  {{1}} body variable) which always gets through. USE WHEN Deepak wants to: "message a student",
  "send an announcement", "tell my students X", "WhatsApp all students / the agentic cohort",
  "broadcast on Acharya", "remind students", "why isn't my Acharya message delivering", "message
  Kritansh/Aditya/<name>", "send to <number>". Runs on the Gurukul VM. Companion to
  maintain-trigunai-system (owns the Acharya/LMS stack) and acharya-technology-transfer (per-teacher
  onboarding). This skill OWNS outbound student WhatsApp messaging + its 24h-window/template handling.
---

# acharya-whatsapp-announce — outbound student WhatsApp (Acharya channel)

Send announcements or 1:1 messages to Acharya students over WhatsApp, reliably, without tripping the
24-hour-window failure.

## The core gotcha (why messages fail)
WhatsApp only lets a business send **free-form text within 24h of the student's last inbound message**.
Outside that window Meta rejects free-form with **"FAILED: Re-engagement message"** (this is exactly
why a plain send to Kritansh/Aditya failed on 2026-07-05). The fix: send an **approved template**,
which crosses the closed window. This skill defaults to the template path.

## The tool
`~/wa_send.py` on the Gurukul VM (`dk_trigun@20.219.2.53`). Connect:
`ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53`

```bash
# one student (personalised "Namaste <name>! ..." + template, crosses closed window):
python3 ~/wa_send.py --to 916396844362 --msg "your message here"

# several specific numbers:
python3 ~/wa_send.py --to 916396844362 --to 918126060070 --msg "..."

# a whole course cohort:
python3 ~/wa_send.py --course agentic --msg "New lesson is live — open Acharya to try it!"

# ALL real students — ALWAYS --dry-run first to review the recipient list:
python3 ~/wa_send.py --all --msg "Classes resume Monday 9am." --dry-run
python3 ~/wa_send.py --all --msg "Classes resume Monday 9am."

# free-form (ONLY delivers if their 24h window is open — e.g. they just replied):
python3 ~/wa_send.py --to 916396844362 --msg "quick note" --mode freeform
```

Flags: `--to` (repeatable) · `--all` · `--course <slug>` · `--msg "..."` (required) ·
`--template <name>` (default `gurukul_announce`) · `--mode template|freeform` (default template) ·
`--no-name` (skip the "Namaste <name>! " prefix) · `--dry-run`.

Recipients for `--all`/`--course` come from `~/.openclaw/students/*.json`; synthetic test numbers and
`web_*` (web-login, no WhatsApp) accounts are auto-excluded. Every send is logged to
`~/leads/wa_announce_log.csv`. Number format = country code + number, no `+` (e.g. `916396844362`).

## Approved templates (each has one `{{1}}` body variable → your `--msg` goes there)
| Template | Category | Use for | Student sees |
|---|---|---|---|
| `gurukul_announce` (default) | MARKETING | student announcements, reminders, requests | 🪔 TrigunAI Gurukul / **{{1}}** / Reply here to continue with Acharya. |
| `gurukul_recall` | MARKETING | spaced-recall quiz nudge | 🪔 Quick recall, no peeking: **{{1}}** / Reply with your answer — Acharya |
| `admin_alert` | UTILITY | genuine non-promotional notices ONLY | 🔔 TrigunAI admin alert / **{{1}}** / …automated notification… |

To add/change template wording you must submit a new template in Meta WhatsApp Manager and wait for
APPROVED status; check current ones:
`curl -s "https://graph.facebook.com/$GRAPH_VERSION/$WHATSAPP_BUSINESS_ACCOUNT_ID/message_templates?fields=name,status,category&access_token=$META_TOKEN"` (env in `~/.openclaw/wa_cloud.env`).

## Guardrails (do NOT skip)
- **Always `--dry-run` before `--all`** and read the recipient list back to Deepak before firing.
- **Never send promotional content via `admin_alert`** (UTILITY) — that violates Meta policy and risks the
  number's quality rating. Promos/announcements → `gurukul_announce` (MARKETING).
- Marketing templates respect **opt-outs and per-user marketing limits**, so delivery is high but not 100%.
- Keep `{{1}}` to one line's worth of content (the tool strips newlines — Meta rejects them in params).
- Once a student **replies**, their 24h window reopens and normal Acharya free-form chat resumes.
- Confirm the message wording with Deepak before broadcasting to more than a couple of people.

## How it fits
- Bridge that receives student replies + runs Acharya: `~/wa_bridge.mjs` (see [[project-gurukul-vm]]).
- Channel policy: WhatsApp = Meta Cloud API (this skill). Voice = Plivo only (see maya calling).
- Related: **maintain-trigunai-system** (Acharya/LMS stack), **acharya-technology-transfer** (onboard a
  teacher's cohort), **user-research-education-trigunai** (mines student replies for pains).
