---
name: content-marketing-bot
description: >
  Master OPERATIONS map for every autonomous system running on the TrigunAI OpenClaw box
  (hearmenow, Azure 20.120.226.5). Covers three engines + shared infra: (1) the DAILY CONTENT
  ENGINE (15-day plan → reels/music/carousels → auto-post IG/FB/YouTube + deliver LinkedIn/Stories),
  (2) the TEACHER OUTREACH chief-of-staff (teacher_gtm sprint: morning brief, Azure-Maps lead
  sourcing, call logging, pilot builds), (3) the AI VOICE-CALL AGENT "Maya" — LIVE, real outbound
  calls with an Indian caller-ID, three channels (Plivo + Twilio + WhatsApp) and Azure gpt-realtime
  speech-to-speech; runs on the GURUKUL VM (see §6), plus the render farm (EC2 auto start/stop + T4 fallback).
  Use to OPERATE / MAINTAIN / DEBUG / EXTEND any of these: pause-resume an engine, edit a plan,
  change a schedule, check what posted/called, source leads, log calls, place a call, change the call
  script, pull a call transcript/recording, rotate keys/tokens, start/stop the farm, add a content type or skill.
  On the box it self-maintains via Codex (trigun-coding). Triggers: "content-marketing-bot", "maintain the engine",
  "the daily engine", "the teacher agent", "the voice agent", "Maya", "call this number/lead", "change the call script",
  "call transcript", "pause posting", "why didnt it post/call", "edit the plan", "change the schedule", "check the log",
  "add a skill", "rotate the token".
metadata: { "openclaw": { "emoji": "🛠️", "requires": { "bins": ["ssh"] } } }
---

# content-marketing-bot — Master Ops for the OpenClaw Autonomous Systems

The single operations map for everything the box runs on its own. **Read before changing any of it.**
On the box paths are local; from Claude/Mac, connect with:
`ssh -i ~/Downloads/hearmenow-agentic-system_key.pem hearmenow-agentic-system@20.120.226.5`
(⚠️ SSH **user = `hearmenow-agentic-system`**, NOT azureuser. This box is in a SEPARATE Azure subscription from
the Maya/LMS one — can't be az-managed from the 7db80eaf login.) Maya voice box (§6) is a DIFFERENT VM:
`ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53`.

## 0. The three engines + infra (what fires when)
| Engine | Cron (UTC → IST) | Does |
|---|---|---|
| **Teacher outreach** (`teacher-daily`) | `teacher-morning` 03:30→9am · `teacher-evening` 15:00→8:30pm | morning brief + Azure-Maps leads + Priyanshu list → Telegram; evening log-check + interview reminder |
| **Content engine** (`studio-daily`) | `daily-content-engine` 05:30→11am | today's reel/carousel/music → auto-post IG/FB/YT + deliver LinkedIn/Stories; starts+stops EC2 |
| **Voice-call agent "Maya"** (LIVE, on **Gurukul** VM) | manual (place a call on demand; call-list runner not built yet) | real outbound AI calls to teachers/leads from an Indian caller-ID, sub-second gpt-realtime; auto-transcribed + recorded. **Full ops in §6.** |

## 1. Where everything lives (on the box)
| Thing | Path |
|---|---|
| **Content plan** (15 days) | `~/.openclaw/content_plan.json` |
| **Teacher kit** | `~/teacher_gtm/` (`15DAY_PLAN.md`, `DAY{N}_BRIEF.md`, `progress.py`, `progress.json`, `03_CONVERSATION_LOG.md`, `02_CONVERSATION_SCRIPT.md`) |
| **Skills** | `~/.openclaw/workspace/skills/` — `studio-daily`, `studio-reel/social/track/flowart/tableread/script/video/faceless/music/youtube`, `teacher-daily`, `trigun-coding`, this skill |
| **Voice agent "Maya"** | ⚠️ **on the GURUKUL VM, not this box** → `dk_trigun@20.219.2.53:~/voicebot_wa/` (see §6). Old brain-only proto still here: `~/voicebot/voicebot_reply.py` |
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

**Voice agent (Maya)** — now LIVE with real telephony on the **Gurukul VM**. Full operations (place a call, change the script, pull transcripts, all 3 channels) are in **§6** below.

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

---

## 6. Voice-calling agent "Maya" — LIVE (3 channels)

Real AI phone agent that cold-calls Indian teachers in warm Hindi/Hinglish to qualify interest in TrigunAI's AI suite (Acharya WhatsApp tutor + dashboard) and hand off to the team for a 14-day free trial. **User-confirmed working, sub-second, natural.**

### 6.0 Where it runs (IMPORTANT)
Maya lives on the **GURUKUL VM**, NOT the OpenClaw box:
`ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53` → dir `~/voicebot_wa/`.
Fronted by **Caddy** on `gurukul.trigunai.com` (TLS). Caddy routes coexist with live Acharya (never break `/webhook` → Acharya:8788).

### 6.1 The three channels
| Channel | Bot file | systemd | Port | Caddy route | Brain | Status |
|---|---|---|---|---|---|---|
| **Plivo + gpt-realtime** ⭐ (PRODUCTION) | `maya_rt_bridge.py` | `maya-realtime` | 7863 | `/realtime*` | Azure **gpt-realtime** S2S (South India) | ✅ best — Indian caller-ID, sub-second, µ-law E2E |
| **Plivo + cascade** (fallback) | `maya_plivo.py` | `maya-plivo` | 7862 | `/plivo*` | Azure STT + gpt-4o-mini + TTS | ✅ works, ~1s lag |
| **Twilio + cascade** | `maya_twilio.py` | `maya-twilio` | 7861 | `/twilio*` | STT + gpt-4o-mini + TTS | ✅ works (US caller-ID +19786669305) |
| **WhatsApp calling** | `wa_voice_bot.py` + `whatsapp_router.py` | `maya`(7860) + `wa-router`(8799) | 7860/8799 | `/webhook*`→router | SmallWebRTC + Azure | ⏳ built; **gated by Meta** (needs messaging tier ≥2000 + $10 balance) |

Repo source of truth for all of the above: `azure_migration/openclaw-studio/`.

### 6.2 Telephony + Azure creds (on Gurukul, chmod 600)
- **Plivo** (`~/voicebot_wa/plivo.env`): `PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`. Account "Deepak Kumar", India region. **Indian number = `912264230921` (+91 22 6423 0921, Mumbai)** — voice, compliance accepted (Reg Cert + GST). ~$0.0075/min + ~$3.12/mo.
- **Twilio** (creds in `~/voicebot_wa/wa_voice.env`): from `+19786669305` (US, Full account).
- **Azure** (`~/voicebot_wa/wa_voice.env`): `AZURE_OPENAI_ENDPOINT=https://maya-india-aoai.openai.azure.com` + `AZURE_OPENAI_API_KEY` (resource `maya-india-aoai`, rg `llm-moedel`, **South India**, sub `7db80eaf-...`, tenant `be2ca4fb-...` needs MFA). Deployments: `gpt-4o-mini` (50K TPM) + `gpt-realtime` (v2025-08-28). `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION=centralindia`. Paid by **Microsoft-for-Startups credits** ($20k, exp Jun 2028).
- **Telegram delivery** (`~/voicebot_wa/wa_voice.env`): `TELEGRAM_CHAT_ID=8478318652` set; **`TELEGRAM_BOT_TOKEN` still missing** → paste the bot token to activate auto-push of transcripts.

### 6.3 Place a call (production realtime channel)
```bash
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 '
  set -a; source ~/voicebot_wa/plivo.env; set +a
  B="https://api.plivo.com/v1/Account/$PLIVO_AUTH_ID"
  curl -s -u "$PLIVO_AUTH_ID:$PLIVO_AUTH_TOKEN" -X POST "$B/Call/" -H "Content-Type: application/json" -d "{
    \"from\":\"912264230921\", \"to\":\"91XXXXXXXXXX\",
    \"answer_url\":\"https://gurukul.trigunai.com/realtime-answer\", \"answer_method\":\"POST\"}"'
```
`to` = `91` + 10-digit number. Outcome/CDR: `GET $B/Call/{request_uuid}/` → `bill_duration`, `hangup_cause_name` (Busy Line / No Answer / Normal).

### 6.4 Change the call script / voice
Edit `INSTRUCTIONS` (and `CLOSERS` if you change the closing lines) in **`maya_rt_bridge.py`**, then:
```bash
scp -i ~/.ssh/gurukul_key azure_migration/openclaw-studio/maya_rt_bridge.py dk_trigun@20.219.2.53:~/voicebot_wa/
ssh -i ~/.ssh/gurukul_key dk_trigun@20.219.2.53 'sudo systemctl restart maya-realtime'
```
Current script = polite warm screener: greet ONCE (hard rule, no re-greet) → qualify teacher/wants-to-earn-by-teaching → frame "plug AI into teaching, reach more students with less effort" + complete AI suite + 14-day free trial → details (Acharya bot / dashboard / WhatsApp channel) only if asked → NO price → close "team will contact for free-trial registration". Voice = `coral` (`MAYA_VOICE`). Half-duplex (caller audio ignored while Maya speaks). Auto-hangup when a CLOSER phrase is detected.

### 6.5 Transcripts + recordings
- **Transcript** per call: `~/voicebot_wa/transcripts/<call_id>.txt` (USER + MAYA lines; user side via `gpt-4o-transcribe`).
- **Recording** (mp3): auto-started each call → Plivo console → **Logs / Recordings** (or `GET $B/Recording/`).
- Pull latest: `ssh ... 'cat $(ls -t ~/voicebot_wa/transcripts/*.txt | head -1)'`.

### 6.6 Latency architecture (why it's fast — don't regress)
Cascade (STT→LLM→TTS) floors at ~1s even in-region. The win = **gpt-realtime speech-to-speech** in **South India** with **`g711_ulaw` in+out** (Plivo's native µ-law, zero resampling) via a **direct Plivo↔Azure WS bridge** (Pipecat 1.4 can't drive it — Pipecat sends GA `session.type`; the resource's realtime endpoint only speaks the OLD protocol on `api-version=2025-04-01-preview`). Everything India-region (Plivo Mumbai edge + Gurukul Central India + realtime South India). Don't move the LLM/realtime out of India or add resampling.

### 6.7 Debug a silent/failed call
`systemctl is-active maya-realtime` → `sudo journalctl -u maya-realtime -n 40` (look for `session.type` errors = endpoint/version drift, or WS not accepted) → Caddy up + `/realtime-answer` returns XML → Plivo CDR `hangup_cause_name` (Busy/No Answer = not our bug) → transcript file written? Restore `/tmp` assets only matters for the drone pipeline, not Maya.

### 6.8 Compliance / safety
Cold voice calls to Indian mobiles need **DLT registration + DND scrubbing + 9am–9pm + AI disclosure + opt-out** before scale. Fine for a small pilot to known/interested numbers; register DLT before volume. Honesty guardrail: candidates are candidates until Deepak confirms; never fake call outcomes.

### 6.9a Daily calling scheduler (approve-then-call, on Gurukul)
Autonomous daily teacher-calling with human approval. Lead list: `~/leads/all_leads.csv` (1,803 phone-verified
coaching/tuition leads from `lead_extractor.py` via Google Places API; key in `~/places.env`).
- **`batch_planner.py`** (cron **05:15 UTC = 10:45 IST**): picks 25 fresh leads (round-robin by city, skips chains +
  already-called), writes `~/leads/pending/<date>.csv`, Telegrams Deepak the list + one-tap Approve/Skip links.
- **`maya_scheduler.py`** (systemd **`maya-scheduler`** :7864, Caddy **`/maya-*`**): `/maya-approve?key=&date=` launches
  `call_runner.py` on that batch; `/maya-skip` cancels. Secret `MAYA_APPROVE_KEY` in wa_voice.env.
- **`call_runner.py`**: sequential dialer (realtime is capacity-1) → each lead via `/realtime-answer` with caller
  context (name/city/segment as query params → Maya sounds informed); **office-hours guard 11am–5pm IST** (waits if
  approved early, defers if after 5pm); logs to `~/leads/call_results.csv` (status + interested via closer-phrase
  detection); Telegrams a batch summary. Manual: `python3 call_runner.py --city Patna --segment NEET/JEE --limit 25 [--dry-run] [--ignore-hours]`.
- Config: `MAYA_DAILY=25` in wa_voice.env. Chain-exclusion list in call_runner.py + batch_planner.py (Aakash/PW/Vedantu/etc).
- Add more leads: `source ~/places.env; python3 ~/lead_extractor.py --out ~/leads/all_leads.csv` (edit SEGMENTS/CITIES in the script).

### 6.9 Open items
1. **Telegram bot token** → set `TELEGRAM_BOT_TOKEN` to auto-deliver transcripts. 2. **WhatsApp calling** awaits Meta account (tier ≥2000 + $10). 3. **T4** (`ubuntu-new-gpu`, Malaysia, `20.17.162.96`, key `~/Downloads/dk-gpu-nvidia_key.pem`) — tested for self-host STT, NOT used; **stop it** (`az vm deallocate -g ubuntu-new-gp_group -n ubuntu-new-gpu`) to save cost. 4. **Call-list runner** (morning leads → approve → dial list → log) not built yet.
