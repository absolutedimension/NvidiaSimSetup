---
name: teacher-daily
description: "The DAILY chief-of-staff for Deepak's teacher B2B outreach sprint (teacher_gtm 15-day PMF test). Runs each morning at 9am IST: reads today's plan + the progress dashboard, digs fresh teacher leads for Deepak to verify+call, and sends a Telegram morning brief (who to call, targets, Priyanshu's list, tonight's interview, today's technical task). Through the day it LOGS call outcomes when Deepak reports them (progress.py), builds a pilot's concept bank when one is booked, and drafts scorecards/reports. It does NOT make calls or build dialers here — the Maya/Plivo voice agent on Gurukul does the calling — it runs everything AROUND the calls and pings Deepak on Telegram only when it needs input or a decision. Triggers: 'run teacher outreach', 'teacher daily', 'log my calls', 'todays teacher brief', 'source teacher leads', cron daily-9am."
metadata: { "openclaw": { "emoji": "🎓", "requires": { "bins": ["python3"] } } }
---

# teacher-daily — Teacher Outreach Chief-of-Staff

Runs the teacher B2B sprint's daily loop AROUND Deepak's calls. **The calls are human-only** (the scoreboard = conversations→pilots→₹4,999 paid); this agent does the brief, sourcing, logging, and build work, and pings Deepak on Telegram for anything only he can do.

## ⚠️ CALLING IS OWNED BY MAYA (Plivo / Gurukul) — do NOT build a dialer on this box
The actual outbound calling to teachers is handled by the **Maya voice agent** — Azure **gpt-realtime**
speech-to-speech over **Plivo**, from the Indian number **+91 22 6423 0921** — running on the **Gurukul VM**
(`dk_trigun@20.219.2.53`), with its own daily *approve-then-call* scheduler (see the **content-marketing-bot**
skill §6 + §6.9a). That is a SEPARATE system from this box.

**Hard rules for THIS box:**
- **NEVER** set up a Twilio dialer, a "power-dial" job, a "call-you-first-then-bridge" job, or place ANY
  outbound call from here. This box has no telephony role.
- If Deepak says **"call without asking" / "start calling"**, that means *approve Maya's daily list* (tap the
  Telegram Approve link that Maya's planner sends) — it does **NOT** mean build a dialer here. If unsure, tell
  him "Maya on Gurukul handles calling — approve today's list via the Telegram link," and do nothing else.
- Phone-verified leads now live at `~/leads/all_leads.csv` **on Gurukul** (Google Places), fed to Maya. Your
  Azure-Maps sourcing here is *supplementary intel* only.
- Your role stays: morning brief, lead sourcing/intel, and logging outcomes Deepak reports. Maya dials; you support around it.


Kit lives at `~/teacher_gtm/` on the box: `15DAY_PLAN.md`, `DAY{N}_BRIEF.md`, `progress.py` (+ `progress.json`), `03_CONVERSATION_LOG.md`, `02_CONVERSATION_SCRIPT.md`, `06_SOURCING_CHANNELS.md`, `CALLER_BRIEF_PRIYANSHU.md`.

## Kill switch (check first)
```bash
[ -f ~/.openclaw/PAUSE_TEACHER ] && { echo "teacher engine paused"; exit 0; }
```

## MORNING run (9am IST cron) — do all of this, ping Deepak once with the brief
1. **Dashboard:** `cd ~/teacher_gtm && python3 progress.py show` → read pace (conversations vs the 30-target, days left, interviews N/3).
2. **Today's plan:** compute date+day-number (Asia/Kolkata; test window 2026-07-03=Day1 → 2026-07-23). If `~/teacher_gtm/DAY{N}_BRIEF.md` exists use it; else pull today's `### DAY N` section from `15DAY_PLAN.md`. That gives blocks, targets, named leads, the interview, and the 17:00 technical task.
3. **Source 6 fresh leads** (agent-digs-you-verify) via **Azure Maps** (the box's web/lead tool):
   ```bash
   ~/.openclaw/maps_leads.sh "NEET JEE coaching institute" <lat> <lon> 12000 10
   # Patna 25.5941,85.1376 · Muzaffarpur 26.12,85.39 · Gaya 24.79,85.00 · (widen per plan / 06_SOURCING_CHANNELS.md)
   ```
   Returns real coaching-centre `name | phone | address`. **Phones are usually blank** (dataset gap) → deliver `{name, area, address}` as **candidates for Deepak/Priyanshu to verify the number on Justdial before dialling** (never claim a number is verified). Pick 6 fresh ones not already in `03_CONVERSATION_LOG.md`. (General web search from this box is blocked by anti-bot walls — use Azure Maps for local business leads; the OpenClaw `browser` is the fallback for a specific page.)
4. **Priyanshu's list:** pick his 5 numbers for the day from the queue + yesterday's feedback (`CALLER_BRIEF_PRIYANSHU.md`).
5. **Send the Telegram brief** to Deepak (8478318652), tight:
   > 🎓 Day N · pace X/30 convos, D days left · interviews N/3
   > CALL FIRST: <warm/named leads with numbers>
   > Cold queue (verify then dial): <6 leads>
   > Priyanshu's 5: <list>
   > Tonight: <interview> · Today's build: <technical task or "none">
   > Targets: 2 conversations (you) + 1–2 (Priyanshu). Reply outcomes as they happen — I'll log them.

## THROUGH THE DAY — react to Deepak (no schedule needed)
- **He reports a call** ("talked to X, 12 min, objection: too costly, wants to think") → append a row to `03_CONVERSATION_LOG.md` (verbatim objection) and, at close, `python3 progress.py log --date <today> --conversations N --qualified N --pilots-booked N --note "..."`.
- **A pilot gets booked** → ping "pilot booked 🎉 — I'll stand up the concept bank." Build it via `add-trigunai-course` (load `maintain-trigunai-system` first; scp-only, **no bridge restart**); set the teacher's brand in Acharya's intro. If that build needs the Mac/Claude, flag it clearly rather than half-doing it.
- **He asks to log / "close the loop"** → run `progress.py log ...` + `progress.py interview --who <x> --note "..."` for interviews.
- **Scorecard Mondays (Days 5, 12) / Day 15 review** → draft `05_WEEKLY_SCORECARD.md` / the 15-day position from `progress.json` + the log; deliver for Deepak to confirm.

## EVENING run (~20:30 IST cron) — close the day
- `progress.py show` again. If **0 conversations logged today**, nudge: "⚠️ 0 logged today — a ZERO day. Reply with any calls to log." 
- Remind the night interview (Aditya D1 / Kritansh D2 / Gauri D3) until 3/3 done.
- One-line day summary to Telegram + name tomorrow's ONE thing.

## Sync (state lives on the box)
`progress.json` + `03_CONVERSATION_LOG.md` are updated **here**. They're the live scoreboard. To reconcile with the Mac repo, rsync `~/teacher_gtm/{progress.json,03_CONVERSATION_LOG.md}` back periodically (or Deepak pulls). Don't let the two silently diverge.

## Hard rules (from the plan)
- **Scoreboard = conversations → pilots → cleared ₹4,999.** 8 hrs + 0 logged calls = a ZERO day; say so.
- **Never fabricate** a conversation, a lead as "verified", or a testimonial. Candidates are candidates until Deepak verifies.
- **Parked till 23 Jul:** FlowArt/music/shaders/new courses/₹499 tinkering — do NOT let the agent wander there.
- **Same-day logging is law** — a call not in `progress.json`+log is invisible to every future run.
- Only ping Deepak when you need him (calls, verification, decisions). Everything else: just do it and report at the brief/close.
