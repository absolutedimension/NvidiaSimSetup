# Teacher GTM — PMF Test Spec (LOCKED)

> Written 2026-07-02. This is the falsifiable test. Do not edit the parameters mid-test —
> if a parameter must change, that IS a result: log why, then start Test v2.

## The one-sentence hypothesis

**Exam-prep tuition teachers with an existing student base will pay ₹4,999/month for
Acharya as their own branded WhatsApp AI tutor, because it helps them retain and expand
paying students.**

## Locked parameters

| Parameter | Value | Do NOT change mid-test |
|---|---|---|
| Segment | Tuition/coaching teachers, **exam-prep subjects** (Class 9–12 maths/science/bio, NEET, government exams). 10–200 students. India, Hindi/English. | No "AI course" pitch — organic demand asked for exam prep |
| Offer | Acharya under the **teacher's name/brand**: daily practice + doubt-solving + spaced revision on WhatsApp, progress visible to the teacher | See 01_OFFER_ONE_PAGER.md |
| Price | **₹4,999/month flat** (up to 50 active students; beyond that, talk to us) | One price. Do not negotiate per teacher — the price is part of the test |
| Pilot | **14 days free, max 10 students**, then ₹4,999/mo via Razorpay. Pilot start requires the teacher to onboard ≥5 real students in week 1 | A pilot with 0 students is not a pilot |
| Weekly quota | **10 real teacher conversations/week** (voice/video/in-person — not messages sent) | This is the input metric. Everything else follows from it |
| Timebox | **3 weeks: Thu 3 Jul → Wed 23 Jul 2026** | |

## Success / kill criteria (pre-committed — written before the test, per PMF discipline)

| Signal by 23 Jul | Verdict | Next move |
|---|---|---|
| ≥1 teacher **paid** ₹4,999 (cleared, Razorpay/UTR) | ✅ PMF signal | Test v2: raise quota, add 2nd teacher cohort, tighten onboarding |
| ≥2 pilots live with real students, 0 paid yet | 🟡 Offer lands, conversion untested | Extend 1 week ONLY to run the pilot→pay close; do not restart discovery |
| ≥20 conversations held, **0 pilots** | 🔴 Offer or price wrong | Iterate the OFFER (not the segment) using logged objections; Test v2 |
| <20 conversations held | ⚫ Test invalid — input quota missed | The problem is founder time allocation, not the market. Diagnose the week, not the strategy |
| ≥3 pilots, students don't use it (<30% weekly active) | 🔴 Product gap | Fix the top usage blocker before any more sales conversations |

**Anti-drift rule:** switching segment (teachers → something else) is allowed ONLY after a
🔴 verdict at the end of the timebox, with the objection log as evidence. A slow week is
not a verdict.

## What counts / what does not count

- **Counts as a conversation:** ≥10 min live with a real teacher about their tuition
  business and this offer. Logged in 03_CONVERSATION_LOG.md same day.
- **Does NOT count:** WhatsApp forwards, pamphlet sends, "interested, will call back",
  self-tests, family courtesy chats.
- **Counts as paid:** money cleared in the Trigunaï Razorpay/current account. Screenshot/UTR.
- **Does NOT count:** "will pay next week", a signed nothing, a ₹5 test sub.

## Weekly rhythm

- **Mon:** review 05_WEEKLY_SCORECARD.md, book the week's 10 conversations.
- **Daily:** conversations logged same day; objections verbatim.
- **Wed 23 Jul:** verdict against the table above. No silent extensions.

## Unit economics guardrail (verify once, week 1)

Rough per-student monthly cost = Azure gpt-4o-mini tokens (pennies) + WABA conversation
charges (user-initiated service conversations are free within the 24h window; business-
initiated template messages are billed — check the current Meta India rate card) +
infra share. **Task: compute actual cost/active-student from Kritansh's usage data and
write it here: ₹___/student/month.** ₹4,999 for 50 students needs cost < ~₹40/student to
keep >60% margin. If cost is higher, the cap (50) or price moves in Test v2 — not now.
