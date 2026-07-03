---
name: content-marketing-bot
description: >
  Master OPERATIONS map for every autonomous system running on the TrigunAI OpenClaw box
  (hearmenow, Azure 20.120.226.5). Covers three engines + shared infra: (1) the DAILY CONTENT
  ENGINE (15-day plan → reels/music/carousels → auto-post IG/FB/YouTube + deliver LinkedIn/Stories),
  (2) the TEACHER OUTREACH chief-of-staff (teacher_gtm sprint: morning brief, Azure-Maps lead
  sourcing, call logging, pilot builds), (3) the AI VOICE-CALL AGENT (Twilio + Azure Speech +
  gpt-5.5 outbound calls — in progress), plus the render farm (EC2 auto start/stop + T4 fallback).
  Use to OPERATE / MAINTAIN / DEBUG / EXTEND any of these: pause-resume an engine, edit a plan,
  change a schedule, check what posted/called, source leads, log calls, rotate keys/tokens,
  start/stop the farm, add a content type or skill. On the box it self-maintains via Codex
  (trigun-coding). Triggers: "content-marketing-bot", "maintain the engine", "the daily engine",
  "the teacher agent", "the voice agent", "pause posting", "why didnt it post/call", "edit the plan",
  "change the schedule", "check the log", "add a skill", "rotate the token".
metadata: { "openclaw": { "emoji": "🛠️", "requires": { "bins": ["ssh"] } } }
---

# content-marketing-bot — Master Ops for the OpenClaw Autonomous Systems

The single operations map for everything the box runs on its own. **Read before changing any of it.**
On the box paths are local; from Claude/Mac, prefix with `ssh -i ~/.ssh/... hearmenow-agentic-system@20.120.226.5`.

## 0. The three engines + infra (what fires when)
| Engine | Cron (UTC → IST) | Does |
|---|---|---|
| **Teacher outreach** (`teacher-daily`) | `teacher-morning` 03:30→9am · `teacher-evening` 15:00→8:30pm | morning brief + Azure-Maps leads + Priyanshu list → Telegram; evening log-check + interview reminder |
| **Content engine** (`studio-daily`) | `daily-content-engine` 05:30→11am | today's reel/carousel/music → auto-post IG/FB/YT + deliver LinkedIn/Stories; starts+stops EC2 |
| **Voice-call agent** (in progress) | (manual until Twilio wired) | outbound AI calls to leads — brain+voice proven; telephony pending |

## 1. Where everything lives (on the box)
| Thing | Path |
|---|---|
| **Content plan** (15 days) | `~/.openclaw/content_plan.json` |
| **Teacher kit** | `~/teacher_gtm/` (`15DAY_PLAN.md`, `DAY{N}_BRIEF.md`, `progress.py`, `progress.json`, `03_CONVERSATION_LOG.md`, `02_CONVERSATION_SCRIPT.md`) |
| **Skills** | `~/.openclaw/workspace/skills/` — `studio-daily`, `studio-reel/social/track/flowart/tableread/script/video/faceless/music/youtube`, `teacher-daily`, `trigun-coding`, this skill |
| **Voice agent** | `~/voicebot/voicebot_reply.py` (gpt-5.5 "Maya" + Azure TTS) |
| **Farm resolver / scripts** | `~/.openclaw/farm.sh` (EC2→T4) · `farm_start.sh` · `farm_stop.sh` |
| **Cron store** | `~/.openclaw/cron/jobs.json` (manage via `openclaw cron ...`) |
| **Env / secrets (all chmod 600)** | `~/.aws/credentials` (EC2 start/stop, avinash key) · `~/.openclaw/maps.env` (Azure Maps) · `~/.openclaw/speech.env` (Azure Speech) · `~/.codex/azure.env` (Azure OpenAI) · `~/marketing_pipeline/ig_publish/.env` on **EC2** (Meta IG/FB token, ⚠️ expires ~2026-08-31) |
| **Lead sourcing** | `~/.openclaw/maps_leads.sh "q" lat lon r n` + `maps_parse.py` (Azure Maps POI) · `web_search.sh` (DDG, currently blocked) |
| **Logs** | content: `~/.openclaw/content_log.md` · teacher: `~/teacher_gtm/progress.json` + `03_CONVERSATION_LOG.md` · cron: `openclaw cron runs` |
| **Kill switches** | `~/.openclaw/PAUSE_DAILY` (content) · `~/.openclaw/PAUSE_TEACHER` (teacher) |
| **Render farm** | EC2 A10G (EIP `34.192.145.204`, `i-047ebf759f2386e71`, us-east-1) primary · T4 (`20.17.162.80`) fallback |
| **Azure resources** | OpenAI `trigunai-lms-aoai` (gpt-5.5/gpt-5.3-codex) · Maps `trigunai-maps` · Speech `trigunai-speech` (centralindia) |
| **Local source of truth** | repo `azure_migration/openclaw-studio/` (+ `skills/` for Claude-side copies) |

## 2. Common maintenance

**Pause / resume an engine**
```bash
touch ~/.openclaw/PAUSE_DAILY    # content off      | rm to resume
touch ~/.openclaw/PAUSE_TEACHER  # teacher off      | rm to resume
```

**Edit a plan** — content: `~/.openclaw/content_plan.json` (validate with `python3 -c "import json;json.load(open('...'))"`). Teacher: `~/teacher_gtm/15DAY_PLAN.md` / `DAY{N}_BRIEF.md`. On the box use **trigun-coding** (Codex) for safe edits.

**Schedules / cron**
```bash
openclaw cron list ; openclaw cron runs        # jobs + history
openclaw cron edit <id> --cron "30 3 * * *"    # change time (UTC)
openclaw cron disable <id> / enable <id> / run <id>   # run once = debug
```
Jobs: `daily-content-engine`, `teacher-morning`, `teacher-evening`.

**Source leads (teacher)**
```bash
~/.openclaw/maps_leads.sh "NEET JEE coaching institute" 25.5941 85.1376 12000 10   # Patna
```

**Log a teacher call** (when Deepak reports): append verbatim to `~/teacher_gtm/03_CONVERSATION_LOG.md` + `cd ~/teacher_gtm && python3 progress.py log --date <d> --conversations N --qualified N --pilots-booked N --note "..."` (+ `interview --who <x>`).

**Farm start/stop**
```bash
bash ~/.openclaw/farm_start.sh   # start EC2 + wait SSH   |   farm_stop.sh = stop (save cost)
```

**Check what posted / called** — `tail ~/.openclaw/content_log.md` · on EC2 `cat ~/marketing_pipeline/ig_publish/posted_state.json` · `python3 ~/teacher_gtm/progress.py show`.

**Rotate creds** — Meta IG/FB token (re-mint in Gurukul app → update EC2 `ig_publish/.env`) · keys for Maps/Speech via `az cognitiveservices/maps account keys list` → update the `.env` on box · Twilio (when wired) in the voice-agent config.

**Voice agent (test the brain+voice, no telephony)**
```bash
source ~/.codex/azure.env; source ~/.openclaw/speech.env
python3 ~/voicebot/voicebot_reply.py --user "haan main biology padhata hoon" --history /tmp/h.json --out /tmp/r.mp3
```
Telephony = Twilio (SID/token/number, pending) → Media Streams WS → this brain. India cold calls need DLT + geo-permissions + DND.

## 3. Self-maintenance via Codex
Box has `trigun-coding` (Codex gpt-5.3-codex). For any code/config change, describe it to trigun-coding, let Codex edit + validate, then `pm2 restart openclaw-gateway` if a skill changed. Always keep plans valid JSON, keep the kill-switch checks, and **mirror edits back to the repo** `azure_migration/openclaw-studio/`.

## 4. Debug a silent run
`openclaw cron runs` (fired? error?) → `pm2 logs openclaw-gateway --lines 60 --nostream | grep -i error` (rate-limit? skill error?) → farm reachable (`farm_start.sh`) → posting token / `posted_state.json` → kill switch present? → for teacher: `progress.py show`.

## 5. Safety rules (do NOT break)
- **Honesty guardrail** everywhere: no fabricated testimonials, metrics, verified numbers, or conversations. Real-asset days (content) + call outcomes (teacher) come from Deepak — request, don't fake.
- **Scoreboards:** content = posts shipped; teacher = conversations→pilots→₹4,999 (8 hrs + 0 logged calls = ZERO day, say so).
- **Never double-post** (studio-social state files idempotent). **Same-day log** teacher calls.
- **Compliance:** IG/FB token valid; voice cold-calls need DLT/DND/9-9/disclosure/opt-out.
- **Stop EC2 when done** (~$1/hr). **Test before enabling** (`cron run`). **Keep kill switches working.**
- **Parked for the teacher sprint till 23 Jul:** don't let engines wander into FlowArt/music/new courses during teacher hours.
