# DAY 1 — Thu 3 Jul 2026 — THE TASK

> One job today: **hold 3 real teacher conversations and book Pilot #1.** WABA is verified
> working, so any "yes" can go live in 48h. Warm inbound leads first, cold queue after.
> Log every call SAME DAY. Scoreboard = conversations → pilot booked. Not dials.

---

## 08:30–09:00 · Open
- [ ] `cd teacher_gtm && python3 progress.py show`
- [ ] Send ONE WhatsApp test message to a non-admin number — confirm it lands (30 sec; WABA is verified, this is just a sanity ping).
- [ ] Kritansh check: is he active this week? If idle 2+ days, one warm nudge tonight.

## 09:00–10:30 · Warm inbound — CALL THESE FIRST (they raised their hand)
> These 2 are the cleanest external teacher leads in the system. Everything else today is cold.

| Priority | Who | Number | Why | Goal |
|---|---|---|---|---|
| 🔥 1 | **Priyanshu Jain** — Class 11/12 **Biology** teacher (typed TEACHER on the web form Jul 1) | **7070658506** | Real inbound teacher, exact ICP, NEET-adjacent subject | **Book Pilot #1** on the call |
| 🔥 2 | **NEET-prep requester** (web form, Jul 1) | **9472272634** | Organic NEET-prep demand | Qualify: is this a teacher or a student? If teacher → pitch. If student → ask who their teacher is (referral) |

- [ ] Call Priyanshu Jain → run `02_CONVERSATION_SCRIPT.md` → if yes, book onboarding on the call, capture WhatsApp opt-in live.
- [ ] Call the NEET number → qualify first (teacher vs student), then pitch or pivot to referral.
- [ ] **Skip / verify these — likely tests, don't waste a slot:** "Ravi Class 10 Maths" `911234500099` (test-looking number), "Govt Railway Exam" `trigun.music.prod@gmail.com` (Deepak's own music account). Confirm dead, then ignore.

## 10:30–13:00 · Cold call block 1 — Patna queue Q1–Q5 (numbers ready)
- [ ] Q1 NEET Boring Rd · 09054312381
- [ ] Q2 NEET Kankarbagh · 08401942759
- [ ] Q3 NEET Karmali Chowk · 08050800261
- [ ] Q4 NEET Nayatola · 08904899640
- [ ] Q5 MCM Institute (IIT-JEE) · 7992250244
- **Target: 2 conversations from this block.**

## 13:00–14:00 · Lunch + LOG (while fresh)
- [ ] Add each real conversation as a row in `03_CONVERSATION_LOG.md` — **verbatim objection** is the point.

## 14:00–16:00 · Cold call block 2
- [ ] The field rep works Q6–Q10 in parallel — verify the numbers on Justdial first (2 min each), then dial.
- [ ] You: follow up any "call me later" from the morning. Hard stop 16:00 (teachers start evening batches).

## 16:00–17:00 · Close the loop
- [ ] `python3 progress.py log --date 2026-07-03 --queued 6 --conversations N --qualified N --pilots-booked N --paid 0 --revenue 0 --note "..."`
- [ ] Log the field rep's conversations too.

## 17:00–19:00 · Pilot block (ONLY if Pilot #1 booked)
- [ ] Load `maintain-trigunai-system` first. Stand up the Biology/NEET concept bank (`add-trigunai-course`) — scp only, no bridge restart. Set the teacher's brand name in Acharya's intro.

## 19:00–19:15 · Social (15 min cap)
- [ ] ONE post to IG/FB from existing stock → CTA "type TEACHER" (`wa.me/919135255107?text=TEACHER`). No new production.

## 20:00–20:30 · Interview (highest-value data)
- [ ] **Aditya** `8126060070`: "You came to Session 0, you didn't pay — what was the real reason?" → `python3 progress.py interview --who aditya --note "verbatim"`

---

## ✅ Day 1 is DONE when:
- WABA ping confirmed · **≥3 conversations logged** · **≥1 pilot booked** (goal) · Aditya interview captured · dashboard updated.

## ❌ Day 1 is a ZERO day if:
- 8 hours passed and the log shows 0 conversations. Building the concept bank without a booked pilot does NOT count.
