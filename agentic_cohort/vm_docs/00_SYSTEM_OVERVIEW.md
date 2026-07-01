# TrigunAI Gurukul — System Overview & Architecture

> **For the admin (Sutradhaar) and future sessions.** This is the master reference for the live
> WhatsApp AI-tutoring system on this box. Read `cat ~/.openclaw/docs/*.md` for the full set.
> Docs index: 00 overview (this) · 01 operations · 02 troubleshooting · 03 whatsapp/meta.

## What this system is
An AI tutor cohort over WhatsApp for TrigunAI's **Building Agentic Systems** course. Two AI personas
on one WhatsApp number, routed by **who** messages:
- 🪔 **Acharya** — the student tutor. Strict, sequential, mastery-gated teaching of the 9-module
  curriculum, one student at a time, anchored to each student's own project (BYOA).
- 🛠️ **Sutradhaar** — the admin/ops agent (this is you). Only Deepak's number reaches it. Can run
  shell commands, edit skills/configs, restart services, code (via codex), and upgrade the system.

Everything runs on this one box. The LLM brains are Azure OpenAI (gpt-5.5 / gpt-5.3-codex / gpt-4o-mini)
reached via OpenClaw's `microsoft-foundry` provider — no GPU here, just orchestration + I/O.

## The end-to-end flow
```
 Student's WhatsApp
   │  Meta WhatsApp Cloud API (official, server-to-server — never logs out)
   ▼
 https://gurukul.trigunai.com/webhook   (Caddy TLS, port 443)
   ▼
 wa_bridge.mjs  (Node, systemd `wa-bridge`, 127.0.0.1:8788)
   │  • if sender ∈ ADMIN_NUMBERS  → openclaw agent --agent admin   (Sutradhaar; no profile)
   │  • else                       → load Learner Profile → inject → openclaw agent  (Acharya)
   ▼
 OpenClaw gateway (systemd `openclaw-gateway`) → Azure gpt-5.5  (+ skills)
   ▼
 reply text → Meta Graph API → student's WhatsApp
   │
   └─ (students only) background: gpt-4o-mini extracts + saves Learner Profile, grades recall answers

 PROACTIVE:
   wa-srs.timer (daily 03:30 UTC) → srs_cron.mjs → due recall ping per student (needs gurukul_recall template)
   broadcast.mjs → message the whole roster at once
```

## The teaching model (Acharya)
- **Opens** with one line: *"why do you want to learn AI agents?"* (first contact only).
- **Strict sequence** — concepts taught only in the fixed order (see `~/.openclaw/gurukul/concepts.json`
  `order`). Student can't skip or pick topics.
- **Mastery gate** — explain from basics → ask a check question → advance ONLY if understood; re-explain
  simpler if not.
- **Off-sequence question** → "we'll get there, first the foundation" → back to current step + check.
- **Module complete** → congratulate + share the LMS scored assessment link (`https://lms.trigunai.com/lesson/<slug>`).
- **Spaced repetition** — mastered concepts get recall pings on a 1→3→7→16→30-day schedule.
Full design: `~/.openclaw/docs/` + the `gurukul-tutor` skill.

## Per-student memory (Learner Profile)
One JSON per student at `~/.openclaw/students/<wa_id>.json`: byoa_goal, level, concept mastery
(not_seen/shaky/solid), misconceptions, srs queue, streak, last_win, greeted flag. The bridge injects
it into every turn and updates it after each reply. The **roster** = these files.

## Key identifiers (this deployment)
- VM: `20.219.2.53` (Azure, Central India, RG `trigunai-gurukul-rg`). SSH user `dk_trigun`.
- WhatsApp: **TEST number** `+1 555-662-2646`, Phone Number ID `1205009339362440`, WABA `1060787129847082`,
  Meta App `1047742064872397`. Webhook `https://gurukul.trigunai.com/webhook`.
  (Production number `+919135255107` pending business verification — see 03_whatsapp.)
- Admin number (→ Sutradhaar): `918454964893` (in `ADMIN_NUMBERS`, `~/.openclaw/wa_cloud.env`).
- Azure OpenAI: resource `trigunai-lms-aoai`, provider `microsoft-foundry`. Default model gpt-5.5.

## Secrets — never print these
`~/.openclaw/wa_cloud.env` (Meta token + Phone Number ID + verify token + admin numbers) and OpenClaw
auth profiles. Tokens/keys must never appear in chat or logs.
