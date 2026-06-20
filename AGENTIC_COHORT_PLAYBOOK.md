# Agentic AI Systems — Live Cohort Playbook (Cohort 1)

> The operating manual for delivering "Build Agentic AI Systems" as a 3-month live cohort.
> Course = 9 recorded modules (free) + the live cohort (₹35,000) — the live cohort is the product.
> Cohort 1 students: 3 registered (incl. adityamittal086@gmail.com). **Confirm paid vs free-registered before Session 0.**

---

## Locked decisions (2026-06-18)

| Decision | Choice |
|---|---|
| Live venue | **Zoom / Google Meet** (screen-share + live code; auto-record). VR is the flagship's gimmick, not this course's. |
| Project shape | **Same scaffold, own use-case** — all fork one Ops Agent template, each automates their own real workflow. |
| Cadence | **1× weekly, 90 min**, fixed slot, 13 weeks. Async #help covers the rest. |
| Teaching model | **Flipped** — recorded module is pre-work; live = build / debug / review their real code. Never lecture live. |

---

## The spine: one scaffold, three real agents

Every student forks the same **Ops Agent** starter repo, but each automates a real workflow they personally do:
reads an inbox/docs → extracts tasks → drafts replies → updates a sheet → reports daily.
Outcome per student = a deployed agent doing a real job on a schedule + a portfolio piece + the patterns to build the next one.

---

## 13-week schedule (≈3 months)

| Week | Pre-work (recorded module) | Live session focus (90 min) |
|---|---|---|
| **0** | — | **Kickoff:** orientation · API key working for everyone · each picks their use-case |
| 1 | M1 What an agent actually is | The loop on a whiteboard; map each use-case to goal → actions → stop |
| 2 | M2 Your first tool-calling agent | Live-code the agent loop; everyone gets one tool call working |
| 3 | M3 Tools & integrations | Connect *their* real tool (their inbox / their sheet) |
| 4 | M4 Memory & context | Add memory; RAG basics on their own docs |
| 5 | M5 Planning & multi-step | ReAct + reflection — heaviest module, full week |
| 6 | **Catch-up / integration** | No new module — everyone's agent does a real 5-step job end-to-end |
| 7 | M6 Reliability & guardrails | JSON validation, retries, **cost control** — debug their failures live |
| 8 | M7 Multi-agent systems | Orchestrator + workers; when it helps vs. adds chaos |
| 9 | M8 Deploy your agent | Each agent running on a schedule on a server |
| 10 | M9 Ship a real business agent | Package + hand to a non-technical user; measure time saved |
| 11 | **Capstone build** | Office hours only — polish their own agent |
| 12 | **Demo Day + certificates** | Each demos a working agent; **record it** (proof + funnel + next cohort) |

Weeks 6 & 11 are deliberate slack — the buffer that keeps a solo cohort from collapsing when someone falls behind.

---

## Weekly 90-min live template (reuse every week)

1. **0–10 — Wins & blockers round-robin.** Each student: what they built, where stuck. (This is attendance + accountability.)
2. **10–30 — The hard 20%.** The gotcha the video can't carry. Live, with code.
3. **30–70 — Live build / live debug.** Code this week's pattern, or debug a student's actual agent on screen. *Debugging their real code live is the highest-value thing you do.*
4. **70–85 — Assign the week's build on *their* project** + name next week's pre-work.
5. **85–90 — Cost check** (their API spend) + housekeeping.

---

## The minimum system — 6 off-the-shelf pieces (~half a day to set up)

| # | Piece | Tool | Setup |
|---|---|---|---|
| 1 | Fixed weekly slot | Recurring calendar invite | Pick once (e.g. **Sun 11:00 IST**), 13 invites, never move it |
| 2 | Comms hub | **Discord** server | Channels: `#announcements` `#help` `#show-your-work` `#resources` |
| 3 | Progress tracker | Google Sheet / Notion | Rows = 3 students, cols = M1…M9 + capstone, checkbox each. Shared = peer accountability |
| 4 | Starter kit | GitHub **template repo** + provided API/GPU access | They fork & build, not fight setup. Provided compute = the moat |
| 5 | Recording | Zoom/Meet auto-record → Drive | Each recording = async catch-up + next cohort + funnel clips. Sessions compound |
| 6 | Async office hours | One daily reply window in `#help` + optional mid-week 30-min open call | Bounded — do **not** promise 24/7 |

**Do NOT build:** an LMS, a custom video platform, auto-grading, or Razorpay integration for 3 students (manual UPI/payment-link is right). The product is **you live + the provided compute.**

---

## Starter repo spec (`agentic-ops-agent-starter`)

A GitHub template every student forks Week 0.

```
agentic-ops-agent-starter/
├── README.md              # 5-min setup; "your use-case here" stub
├── .env.example           # ANTHROPIC_API_KEY= / OPENAI_API_KEY=
├── requirements.txt       # anthropic / openai, pydantic, python-dotenv
├── agent/
│   ├── loop.py            # the core agent loop (M2)
│   ├── tools.py           # tool registry — add your tools here (M3)
│   ├── memory.py          # short + long-term memory stub (M4)
│   └── config.py          # model, max steps, cost cap (M6)
├── tools/                 # one file per integration: email, sheets, search, files
├── run.py                 # entrypoint: python run.py "do my task"
└── deploy/                # schedule + logging (M8)
```

Each module fills in one part. By M9 the repo *is* their shipped agent.

---

## Session 0 — Kickoff agenda (30–45 min)

1. **Welcome + the promise:** in 3 months you ship a real agent doing a real job of yours.
2. **How it works:** flipped model — watch the module, come build. Wins/blockers every week.
3. **Everyone gets an API key working live** (Claude or OpenAI). No one leaves without it.
4. **Each student names their use-case** out loud → write it in the progress sheet.
5. **Fork the starter repo**, run `python run.py "hello"`, see the loop tick once.
6. **Logistics:** the weekly slot, Discord, office-hours window, how recordings work.

---

## Certificate & Demo Day (Week 12)

- Each student demos their working agent (5 min) — recorded.
- Issue a **course-completion certificate** (honest framing — not "industry-recognized").
- The Demo Day recording becomes: social proof for Cohort 2, funnel content, and testimonials you'll actually have.

---

## This week's checklist (before Session 0)

- [ ] **Confirm paid vs registered** → send the 3 a payment link, lock them in
- [ ] Pick the weekly slot · send 13 calendar invites
- [ ] Stand up the Discord · post M1 pre-work link in `#announcements`
- [ ] Create the starter template repo + the progress sheet
- [ ] Schedule + run the 30-min Session 0 Kickoff

---

*Owner: Deepak Kumar · Cohort 1 · created 2026-06-18*
