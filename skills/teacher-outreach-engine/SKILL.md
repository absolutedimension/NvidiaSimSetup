---
name: teacher-outreach-engine
description: >
  Deepak's DAILY teacher-outreach engine for the TrigunAI B2B2C PMF test — sourcing independent
  Indian exam-prep tuition teachers and converting them to paid Acharya (AI WhatsApp tutor,
  ₹4,999/mo under the teacher's brand). Run it every day to: pull fresh teacher leads from the
  right sources, hold real teacher conversations off the discovery script, log every call, and
  update a live progress dashboard that shows what's done and how much is left in the 3-week
  test (conversations held, pilots booked, teachers PAID, days remaining, pace vs target). It
  reads and writes the teacher_gtm/ kit (00_TEST_SPEC, 01_OFFER, 02_SCRIPT, 03_CONVERSATION_LOG,
  04_PILOT_ONBOARDING, 05_WEEKLY_SCORECARD, 06_SOURCING_CHANNELS) and maintains progress.json +
  PROGRESS.md via progress.py. USE WHEN Deepak wants to run/plan/log the teacher outreach, find
  teachers to approach, check test progress, or close a pilot. Triggers on: "teacher outreach",
  "run teacher outreach", "find teachers", "who do I call today", "teacher leads", "log my
  calls", "teacher progress", "how's the teacher test going", "how many teachers left", "pilot",
  "onboard a teacher", "close the teacher", "teacher gtm", "daily teachers", "sourcing teachers",
  "/teachers". Companion to trigunai-ceo (owns the PMF strategy + gate), maintain-trigunai-system
  (owns the live Acharya/LMS stack the pilots run on), and add-trigunai-course (stands up a new
  exam-prep concept bank per subject). This skill OWNS the daily teacher-outreach loop + its
  progress log.
---

# Teacher Outreach Engine — the daily loop that finds the first paying customer

> **Job:** every day, move the teacher B2B2C PMF test forward by a measurable amount, and
> record it. Pull leads → hold real conversations → log them → update the dashboard →
> know exactly how far along the test is. Repeat until a teacher PAYS or the window closes
> with a written verdict.
>
> **The kit this skill drives** (all in `teacher_gtm/`):
> `00_TEST_SPEC.md` (the locked test + kill criteria) · `01_OFFER_ONE_PAGER.md` (the pitch) ·
> `02_CONVERSATION_SCRIPT.md` (discovery + qualify) · `03_CONVERSATION_LOG.md` (verbatim ledger) ·
> `04_PILOT_ONBOARDING.md` (yes → first student in 48h) · `05_WEEKLY_SCORECARD.md` (Monday numbers) ·
> `06_SOURCING_CHANNELS.md` (where the teachers are) · `progress.py` → `progress.json` + `PROGRESS.md`.
>
> Strategy owner: **trigunai-ceo** (the PMF gate). This skill is the *operating arm*.

---

## 0. THE GOLDEN RULE (read every run)

> **The only scoreboard is: conversations held → pilots live → a teacher PAYS.**
> Numbers dialed, pamphlets sent, group posts — inputs, not outcomes. A day is "done" when
> a *logged conversation* or a *cleared rupee* moved the dashboard, not when hours passed.
> (CEO OS anti-pattern #21: reach is not traction.)

**Two hard rules from the research (never break):**
1. **No cold WhatsApp to scraped numbers** — it violates WhatsApp's Business Policy and risks
   the live Acharya WABA number. **CALL the listed business number**, pitch live, capture the
   WhatsApp opt-in on the call.
2. **No fake student leads on UrbanPro/TeacherOn** to reach a teacher — it burns their money
   and poisons the first impression. Those platforms are for finding *names*, not first contact.

---

## 1. FIRST RUN EVER — initialize (skip if progress.json exists)

If `teacher_gtm/progress.json` doesn't exist, `progress.py` seeds defaults on first write
(window 2026-07-03 → 2026-07-23; targets 30 conversations / 3 pilots / 2 live / 1 paid).
If the test dates or targets have changed, edit them once via the JSON, then never hand-edit
again — use the CLI. Confirm the window with Deepak if it looks stale.

---

## 2. THE DAILY LOOP (run this each day)

Do these in order. Keep it to one screen of action — this is a doing skill, not a planning one.

### Step A — Show where we are (always first)
```bash
cd teacher_gtm && python3 progress.py show
```
Read the dashboard aloud to Deepak in 3 lines: **day X of 21, N conversations held (pace),
P pilots, £ paid, D days left.** Name the pace honestly (ON TRACK / BEHIND / TARGET HIT).
If interviews aren't done (0–2 of 3), that's the top item — say so.

### Step B — Non-payer interviews first (until 3/3 done)
The 3 cohort non-payers (Aditya / Kritansh / Gauri) are the highest-value data in the company
and gate nothing else well until captured. Each is a 15-min call, one question: *"You came,
you didn't pay — what was the real reason?"* Log verbatim:
```bash
python3 progress.py interview --who aditya --note "verbatim reason here"
```
Their answers sharpen the teacher offer (the ChatGPT objection especially).

### Step C — Pull today's leads (the sourcing move)
Target ~6 fresh leads/day → ~30/week → ~10 conversations/week (⅓ answer & talk).
Use `06_SOURCING_CHANNELS.md` Tier 1, in this order of yield:
1. **Google Maps** — search "NEET coaching / tuition centre / SSC coaching + [locality]";
   pick small ones (low review count = 10–200 students); grab name + phone.
2. **Justdial / Sulekha** — per-city exam categories; visible phone numbers.
3. **Small YouTube educators** (1k–50k subs, Hindi exam channels) — email in About page.
4. **FB owner groups** (ALL India Coaching/tuition Classes Association; Classplus-Lite
   community) — 1 value-post/day, then DM engaged members.
Paste the ~6 leads into `03_CONVERSATION_LOG.md` as "queued" rows (name, subject, phone, source).
> The skill CAN help build the list: use WebSearch / Chrome MCP to surface Google-Maps /
> Justdial listings for a locality Deepak names, and hand back name+phone+subject rows. It must
> NOT auto-dial or auto-message — Deepak makes the human calls.

### Step D — Hold the conversations (Deepak, live)
Use `02_CONVERSATION_SCRIPT.md`: 10 min discovery first (their tuition business, their pain),
qualify (3-of-4 checklist), then pitch `01_OFFER_ONE_PAGER.md` anchored to their words, close
on the 14-day free pilot, book onboarding **on the call**. Capture WhatsApp opt-in live.

### Step E — Log the day (same day, non-negotiable)
For each real conversation, add a row to `03_CONVERSATION_LOG.md` with the **verbatim objection**
(that text is the test's real output). Then update the dashboard counts:
```bash
python3 progress.py log --date $(date +%F) \
  --queued 6 --conversations 2 --qualified 1 \
  --pilots-booked 0 --paid 0 --revenue 0 \
  --note "2 NEET centres Patna; both said 'students have ChatGPT'"
```
Fields are the DAY's counts, not cumulative. `progress.py` re-renders `PROGRESS.md` every run.

### Step F — Close the loop verbally
Restate the new dashboard line and the ONE thing tomorrow needs. If a pilot booked → point
Deepak at `04_PILOT_ONBOARDING.md` (yes → first student message in 48h). If a rupee cleared →
celebrate, then Test v2.

---

## 3. WHEN A TEACHER SAYS YES (pilot onboarding)

Drive `04_PILOT_ONBOARDING.md`: configure Acharya for their subject (use **add-trigunai-course**
if the exam-prep concept bank doesn't exist yet — budget 2–4h first time, reusable after), set
their brand name in Acharya's intro, send the student-invite template, chase ≥5 students onboarded
by day 2, send the weekly progress report (the thing they pay for), close on day 14 with the
Razorpay ₹4,999/mo link. Log `--pilots-live 1` when ≥5 students are actually messaging; log
`--paid 1 --revenue 4999` ONLY when money clears (Razorpay/bank confirmation — verify, don't assume).
Anything touching the live Acharya bridge/LMS → load **maintain-trigunai-system** first (don't
disrupt live students).

---

## 4. WEEKLY (every Monday) + VERDICT (Wed 23 Jul)

- **Monday:** open `05_WEEKLY_SCORECARD.md`, fill last week's column from the dashboard, answer
  the 5 Monday questions in writing (esp. "if I missed 10 conversations, what ate the hours?" —
  if the honest answer is *building/rendering*, that's the audit pattern repeating; name it).
  Set this week's objection-driven tweak to the OFFER (never the segment mid-test).
- **Wed 23 Jul (or when the window closes):** run `progress.py show`, then judge against the
  `00_TEST_SPEC.md` verdict table (✅ ≥1 paid → scale · 🟡 pilots-no-pay → 1-week close extension ·
  🔴 20 convos/0 pilots → iterate OFFER · ⚫ <20 convos → founder-time problem, not market).
  Write the verdict into `05_WEEKLY_SCORECARD.md` and update memory `project-pmf-audit-202607`.
  **No silent extension. No silent segment-switch — a switch needs a 🔴 verdict + the objection log.**

---

## 5. HONESTY GUARDRAILS (this skill enforces)

- **Paid = cleared money only.** Not "will pay", not a booked pilot, not a ₹5 test sub.
- **A conversation = ≥10 min live with a real qualified teacher, logged same day.** Forwards,
  "interested will call back", and self-tests do not count.
- **Report the real number even when it's zero.** A blank dashboard after a "busy" day means the
  day produced no outcomes — say that plainly; don't let activity masquerade as progress.
- **Cross-session evidence:** the work scanner can't see phone calls. `progress.json` +
  `03_CONVERSATION_LOG.md` ARE the record — if it isn't logged, it didn't happen.

---

## 6. QUICK REFERENCE

| I want to… | Do |
|---|---|
| See status / how much left | `python3 progress.py show` |
| Log today's calls | `python3 progress.py log --conversations N --qualified N --note "…"` |
| Log a non-payer interview | `python3 progress.py interview --who aditya --note "…"` |
| Find teachers to call | `06_SOURCING_CHANNELS.md` Tier 1 + WebSearch/Chrome for a locality |
| Run a discovery call | `02_CONVERSATION_SCRIPT.md` |
| Pitch | `01_OFFER_ONE_PAGER.md` |
| Onboard a yes | `04_PILOT_ONBOARDING.md` |
| Weekly review / verdict | `05_WEEKLY_SCORECARD.md` + `00_TEST_SPEC.md` |
