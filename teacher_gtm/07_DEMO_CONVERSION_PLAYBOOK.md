# 25-Lead Demo & Conversion Playbook — Maya-accepted cohort of 2026-07-12

> **What this is:** the operating plan to take the **25 Maya-accepted institutes** (see
> `leads/MAYA_ACCEPTED_25_2026-07-12.csv`) from "said yes to a demo on a robo-call" to
> **enrolled Acharya customers** — and to mine every conversation for pain points that agentic
> systems can solve beyond Acharya.
>
> **Team:** Maya (AI, top of funnel — keeps dialing) → **the field rep** (human voice — scheduling,
> discovery, follow-up) → **Deepak** (demo + tech + provisioning).
> **Feeds:** `MILESTONE_50_IN_50.md` (the north star) · `08_PAIN_POINT_LOG.md` (the research
> output) · `USER_RESEARCH_EDU.md` (knowledge base).

---

## 1. Honest read of what "25 accepted" means

A Maya-call "yes to demo" is **interest, not intent**. Expect the standard B2B decay:
of 25 accepted → ~15 will pick up the field rep's call → ~10 will sit through a demo →
~4–6 will start a free pilot → **2–4 will enroll/pay**. That's a great outcome for
one cohort — 2–4 enrolled against a 50-in-50 target — but only if the follow-up
happens **within 72 hours** of the Maya call. Accepted leads decay by roughly half
per week of silence. **Speed is the whole strategy.**

Two leads are warmer than the rest — work them first, they can produce enrolled #1 this week:
- **#2 Catalyzers (Kota):** concept bank already exists (`agentic_cohort/gurukul_pipeline/courses/catalyzers-kota.json`), was in `template_sent` since 07-08. One good call could go straight to pilot.
- **#1 MCM (Patna):** was on the original Day-0 Patna list, now double-confirmed via Maya.

---

## 2. The funnel (stages + owner per stage)

```
maya_accepted (25)                          ← Maya (done)
   ↓ the field rep calls within 72h
demo_scheduled                              ← the field rep (books a 20-min slot + sends demo video)
   ↓
demo_done                                   ← Deepak demos live; the field rep on the call taking pain notes
   ↓
pilot_confirmed (14-day free, 10 students)  ← close ON the demo call
   ↓ WhatsApp onboarding bot takes over (existing pipeline, OPERATIONS.md)
template_sent → started → web_upload_pending → provisioning
   ↓ acharya-technology-transfer
LIVE (counts toward 50-in-50)               ← Deepak provisions; the field rep confirms students active
   ↓ day-14 close
PAID (₹4,999/mo cleared)
```

The **only new machinery** this playbook adds is the human layer at the top (the field rep + the
demo). Everything from `template_sent` down already exists and was E2E-validated 07-08.

---

## 3. Wave plan (don't call 25 at once)

| Wave | Who | When | Why first |
|---|---|---|---|
| **W1 (4)** | Catalyzers, MCM, Base Point, Delta Success Point | **Day 1–2 (Mon 07-13/Tue)** | Warmest + Patna cluster; Catalyzers can be enrolled #1 |
| **W2 (11)** | Kota #2s, Delhi ×2, Prayagraj #4, Lucknow ×2, Hyderabad #6, Bengaluru #9, Jaipur ×2, Pune #18 | Day 2–5 | Strong NEET/JEE fit, single-subject teachers prioritized |
| **W3 (10)** | The rest (incl. PACE — verify decision-maker; APEX branch 2 merged into #4) | Day 4–8 | Chains/ambiguous-fit — need decision-maker verification first |

The field rep's capacity: ~8–10 scheduling calls/day → all 25 touched inside 4 working days.
**Rule: no lead goes >72h from Maya-accept without a human touch.** For W3 leads that
can't be called by day 3, the field rep sends the post-call WhatsApp (they opted in on the Maya
call) with the demo video link to hold warmth.

### Demo slots (Deepak's calendar)
Block **two demo windows daily: 12:00–13:30 and 18:00–19:30 IST** (teachers are free
midday and post-class evening). 20 min per demo + 10 min buffer = up to 6 demos/day
capacity. The field rep books only into these windows.

---

## 4. The demo itself (20 minutes, fixed structure)

**Format:** WhatsApp video call or Google Meet to the teacher's phone. The field rep joins,
introduces, takes notes. Deepak drives.

| Min | Segment | What happens |
|---|---|---|
| 0–2 | Warm-up | The field rep intros; Deepak: "before I show anything, 3 questions about your classes" |
| 2–7 | **Discovery = pain-point touchpoint** | The 6 questions from `08_PAIN_POINT_LOG.md` §2. The field rep writes verbatim answers. This is the research goldmine — never skip it, even for an eager buyer |
| 7–15 | **Live demo, anchored to their pain** | Deepak messages the real Acharya number with a doubt **from their subject** on screen-share → step-by-step answer → daily practice → the weekly teacher report ("this is what YOU see"). Show the brand: "it introduces itself as *your* tutor" |
| 15–18 | Offer + close | ₹4,999 flat / 14-day free pilot with 10 students / "not a replacement for you." Close: "give me 10 students, we start today — the onboarding takes one WhatsApp message from you" |
| 18–20 | Next step ON the call | If yes → send onboarding template from the bot while still on the call (start the state machine live). If maybe → book a specific follow-up date. Never end on "I'll think" without a date |

**Post-demo, same hour (the field rep):** WhatsApp recap + demo video link + one-pager.
**Post-demo, same day (both):** pain rows → `08_PAIN_POINT_LOG.md`; stage update in the CSV;
conversation row in `03_CONVERSATION_LOG.md`; `progress.py log` the day's counts.

### No-show protocol
1 no-show → the field rep reschedules same day, sends demo video ("2-min dekh lijiye, phir baat karte hain").
2 no-shows → the video IS the demo; move to a light WhatsApp nurture. Don't chase past two.

---

## 5. Beyond Acharya — the agentic-solution decision tree

The discovery block will surface pains Acharya doesn't solve. **Rule: sell Acharya first**
(it's built, it's ₹4,999, it's provisioned in hours). A custom agentic build is offered ONLY
when (a) the teacher doesn't bite on Acharya AND (b) their pain maps to something we can
ship in <1 week from existing infra. Log everything else as research, not commitments.

| Pain heard | Agentic solution | Build effort (existing infra) | Price posture |
|---|---|---|---|
| Doubts at night / practice / retention | **Acharya (core)** | 0 — provision only | ₹4,999/mo |
| "Fees collection is a headache — chasing parents" | WhatsApp fee-reminder agent (polite escalating sequences + UPI link + paid-status tracking) | ~2–3 days (WABA bridge + bot state machine exist) | ₹1,999/mo add-on |
| "Parents keep calling for updates / complaints" | Weekly parent progress digest on WhatsApp (auto, per student, teacher-branded) | ~2 days (extension of the weekly teacher report) | Bundle with Acharya |
| "Admissions season — can't follow up all inquiries" | **Maya-for-them**: AI voice agent calling THEIR admission leads + WhatsApp follow-up | ~3–4 days (Maya/Plivo stack exists — literally our own tool, white-labeled) | ₹3,999/mo seasonal |
| "Making test papers / DPPs eats my Sundays" | Test-paper + DPP generator from their syllabus (concept bank → paper PDF) | ~3 days (concept-bank machinery exists) | ₹1,499/mo add-on |
| "Attendance + batch scheduling is chaos" | WhatsApp attendance agent (student check-in, absent-parent alert) | ~3–4 days | Log as research first — validate ≥3 asks |
| Anything else (marketing videos, website, etc.) | We literally have the video pipeline — but **do not sell it now**; log it | — | Research only |

**Anti-distraction guardrail (CEO OS):** a custom build gets committed to a customer only
with money attached (paid pilot or LOI), max ONE custom build in flight at a time, and never
at the cost of an Acharya pilot. The 50-in-50 number counts Acharya enrollments; side quests
don't move the board.

---

## 6. The demo video (the force multiplier)

One **~3-minute Hinglish demo video** made on our own pipeline, used at 4 points in the
funnel: (1) the field rep sends it when booking the demo — pre-warms; (2) no-show fallback;
(3) post-demo recap; (4) the teacher forwards it to their partner/spouse — the hidden
decision-maker we never meet. Script: `DEMO_VIDEO_SCRIPT.md`. Owner: Deepak (screen
captures) + production-video-trigunai (assembly).

---

## 7. Targets & scoreboard for this cohort (review Fri 07-17 and Fri 07-24)

| Metric | By Fri 07-17 | By Fri 07-24 |
|---|---|---|
| Human touch (field-rep call attempted) | 25/25 | — |
| Real conversations held | ≥12 | ≥15 |
| Demos done | ≥6 | ≥10 |
| Pilots started | ≥3 | ≥5 |
| **Enrolled (live w/ students)** | **≥1** | **≥3** |
| Pain rows in 08_PAIN_POINT_LOG | ≥12 | ≥20 |

Log daily via `progress.py log` (conversations = the field rep's + Deepak's ≥10-min real ones) and
update the `MILESTONE_50_IN_50.md` board each evening. If by 07-17 fewer than 6 demos have
happened, the bottleneck is scheduling, not product — diagnose the field rep's pickup rate before
touching the pitch.

---

*Created 2026-07-12 (Day 7/50). Owner: Deepak.*
