# Live Intro Class — Agentic AI Systems · Run-of-Show + Close

> **Tomorrow, Fri 19 June, 5:00 PM IST · Google Meet · ~60 min.**
> Attendees: Gauri (gaurimittal448) + Kritansh (kritanshsinghal) — both enrolled in Build Agentic AI Systems.
> **This is your first conversion event.** Goal in priority order: (1) deliver real value, (2) discover who
> they are & why they're here, (3) make a clear soft offer for the ₹35k live cohort. Value earns the ask.

---

## Pre-flight (do at 4:45 PM)

- [ ] Sent the 1-hour reminder to both (kills no-shows).
- [ ] Google Meet open, link works, mic + screen-share tested.
- [ ] Demo ready in a terminal: `intro_agent_demo.py` with the API key set (see "Live demo" below). **Run it once at 4:45 so it's warm and you've seen today's output.**
- [ ] One slide/notes tab with the anatomy (Brain · Loop · Tools · Memory) and the 9-module list.
- [ ] Admin dashboard open in a tab — to log who showed + their answers right after.
- [ ] Water, calm, camera on. You built an app live on the Meta Quest store — own that.

---

## Run-of-show (≈55 min)

**0–3 min · Welcome + frame.**
"Thanks for jumping on. Quick plan: I'll show you what an AI agent really is — we'll build a tiny one
live in a few minutes — then I'll walk you through what you'll build across the course, and leave time
for your questions. Stop me anytime." (Ask each their name + what they're studying/doing — warm start.)

**3–8 min · The hook (Module 1 idea).**
"Everyone's used a chatbot — you ask, it answers, it stops. An agent doesn't stop at the answer. You give
it a *goal*, and it goes and does the work. A chatbot tells you how to send the email; an agent sends it.
Let me show you the difference, live."

**8–20 min · LIVE DEMO (the centerpiece).** Share screen, run the agent (see "Live demo" below). Narrate:
- "Watch — I give it a goal: summarize my overdue invoices. It's not answering yet…"
- "See that? It *decided* to call a tool — get_invoices — I didn't tell it to. My code runs the tool, hands back the data…"
- "…now it looks at the result, picks the overdue unpaid ones, and writes the summary. Goal met, it stops."
- "That loop — think, act, observe — in about 50 lines, is the whole idea. Everything else in the course is making this bigger and more reliable."

**20–30 min · The anatomy.** Brain (the LLM decides) · Loop (think-act-observe) · Tools (its hands) ·
Memory (what it carries). Tie each back to what they just saw in the demo.

**30–40 min · What you'll build (the arc).** "Across the course you build one real thing — the *Ops Agent* —
that automates a real workflow end to end: reads an inbox/docs, drafts replies, updates a sheet, reports
daily, runs on a schedule. 9 modules, from this tiny loop to a deployed agent doing a real job. You don't
watch me build it — you build it, with me, live." (Show the 9-module list briefly.)

**40–48 min · Discovery (let them talk — this is gold).** Weave in the questions below. Listen more than talk.

**48–55 min · Soft close.** (Script below.) Make the offer, explain how it works, name the price + installments,
and make the ask. Then **shut up and let them respond.**

**55–60 min · Next step + wrap.** Whatever they say, define the next concrete step (send details + link;
or "watch the module videos and I'll follow up Monday"). Thank them. End warm.

---

## Live demo — cheat sheet

```bash
cd <where intro_agent_demo.py is>
pip install openai            # once
export OPENAI_API_KEY=sk-...  # your OpenAI key
#  OR the TrigunAI proxy (already tested working):
#    export OPENAI_API_KEY=sk-trigunai-master-key-2026
#    export OPENAI_BASE_URL=http://localhost:4000/v1   (needs the proxy reachable)
python3 intro_agent_demo.py
```
**Expected output (tested):** it calls `get_invoices()`, finds Acme ₹/$45k + Dynamo 27k overdue = 72k,
ignores the paid + not-yet-due ones, writes a summary + next step.
**Fallback if the API hiccups live:** you ran it at 4:45, so screen-share that saved output and walk
through it as a recording — never debug live in front of prospects. The point lands either way.

---

## Discovery questions (ask naturally, not as a quiz)

- "What made you sign up — what do you want to be able to build or automate?"
- "Are you studying / working right now? (year + branch if student.)" → tells you if this is a project/internship need.
- "How'd you find us — YouTube, a post, a friend?" → **which channel produced a real lead. Note it.**
- "Have you tried building anything with AI before?"
- "If you had an agent doing one boring task for you every day, what would it be?" → their real motivation = your close.

---

## The soft-close script (say it plainly, then stop talking)

> "So that's the shape of it. What you saw today is module one. The full thing is a live cohort — we meet
> weekly for about three months, you build the Ops Agent step by step with me, you get GPU access and your
> code reviewed, and you finish with a real agent running on a schedule plus a completion certificate for the
> work. It's ₹35,000, and you can pay in installments. I'm keeping the first cohort small so everyone gets
> real attention. If that's something you want in on, I'll send you the details and how to confirm your seat —
> want me to do that?"

- If **yes / interested:** "Great — I'll send it right after this." → send within the hour (below).
- If **hesitant / price:** "Totally fair. The free module videos are yours to watch — go through them, and
  I'll check in. What's the part you'd want to be sure about?" (Listen — that objection is your real data.)
- **Don't discount on the call.** Note the objection; we decide pricing from the pattern, not in the moment.

---

## Follow-up message (send within 1 hour, while warm)

> Hi [name] — great having you on today. As promised, here's how the Build Agentic AI Systems live cohort works:
> • ~3 months, weekly live build sessions with me
> • You build & deploy the Ops Agent — a real working agent — as your project
> • GPU access + code review + completion certificate
> • ₹35,000 — installments available ([2–3 split])
> First cohort is small (limited seats). To confirm your seat: [company account no. + UPI/payment link].
> Any question, just reply — this reaches me directly. — Deepak

**Then log it:** in the admin dashboard, record who attended, their answers (esp. the channel + their goal),
and their commitment level. A "yes" you didn't write down is a "no" in three days.

---

## Honesty guardrails (hold the line even while selling)

- Certificate = "completion certificate for real work," NOT industry-recognized / AICTE / placement-guaranteed.
- Don't promise outcomes you can't ensure. The value is real (you ship a working agent) — let that carry it.
- Lead with the live product you shipped (Quest store) as credibility; don't inflate it.
- It's fine if nobody pays tomorrow. The session's job is value + the ask + learning the objection.
  A captured "interested + here's why" beats a forced "yes."
