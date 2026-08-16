# Handoff → Hermes (CEO agent): ingest Rohan's Saathi data + run the same goal/learning engine for the CEO

> **Read this in a Hermes session.** Two jobs:
> 1. **Pull Rohan's Saathi (training companion) data into Hermes** so Deepak monitors his BD executive
>    from his CEO Telegram agent — goal, daily plan, learning progress, activity, red flags.
> 2. **Give Deepak the SAME engine for himself** — Hermes becomes the CEO's own companion: holds his
>    goals, runs a daily plan/reflect loop, drives his learning, and traces reality — mirroring Saathi
>    at CEO altitude.
>
> This doc explains the model, the data, the integration, and the CEO-companion spec.

---

## 0. The two systems in one line

- **Saathi** = the employee daily companion (LIVE on the Gurukul VM, on WhatsApp). Runs Rohan's day:
  plan → learn → close, holds his goal, teaches sales, traces reality. Friend tone.
- **Hermes** = Deepak's CEO chief-of-staff (OpenClaw agent, Telegram `@dk_ceo_tetris_bot`, Azure VM
  `azureuser@104.211.75.64`, key `~/.ssh/hermes_key`). Already the CEO's front door.

**Goal:** Hermes reads Saathi's data (so Deepak mentors Rohan from Telegram) **and** runs the same
goal/learning/companion loop for Deepak himself.

---

## 1. How Rohan's learning + goal actually works (the model to understand)

Full design: `employee_training/` in the NvidiaSimSetup repo — `FIELD_SALES_CURRICULUM.md` (what he
learns), `TEACHING_STRATEGY.md` (how), `FEEDBACK_SYSTEM.md` (loops + mentor), `DAILY_COMPANION.md`
(Saathi persona), `SAATHI_PERSONA.md` (the live system prompt). In brief:

- **Goal (Goal OS):** Day 1, Saathi helps Rohan articulate + **lock a 30-day goal** (e.g. "first paying
  institute in Patna"). It holds that goal and bends every day toward it.
- **Daily loop:** morning plan (pulls his plan out via questions, locks it) · a ~20-min **learning
  session** (question-led: diagnose → teach the gap/theory → explain-back → apply → confidence check →
  mastered/loop → spaced review) · evening close (traces plan vs reality, captures the field-report).
- **Feedback = the engine.** Every learning turn yields: mastered / shaky / **confident-wrong** (sure +
  wrong = a blind spot = the top mentor signal). This is what should reach Deepak.
- **Curriculum:** 5 modules (Product · Vision/Mission · Field Playbook · Objections · Fundamentals).
- **Tone:** warm friend, never orders. Holidays/Sundays off (`holidays_2026.json`).

---

## 2. Where Rohan's data lives (Gurukul VM `20.219.2.53`)

Saathi is deployed in the WhatsApp bridge `~/wa_bridge.mjs` (function `askSaathi`, isolated to the
`EMPLOYEES` allow-list). It writes to Rohan's profile:

- **Profile JSON:** `~/.openclaw/students/917667177063.json`
  - `saathi_history` — array of `{role:"user"|"assistant", content}` (the full companion conversation)
  - `saathi_last` — ISO timestamp of last interaction (activity signal)
  - `saathi: true`
  - `goal`, `goal_confirmed`, `goal_deadline` — **structured goal (extraction is a pending enhancement;**
    **until wired, the goal is in the Day-1 messages inside `saathi_history`)**
  - `concepts` / `misconceptions` / `srs` — mastery map (**Saathi-side mastery capture is a pending**
    **enhancement; interim, learning progress is inferable from `saathi_history`**)
- **Event log:** `~/.openclaw/gurukul/events.jsonl` — append-only; Saathi turns are `{"type":"saathi_turn",
  "student":"917667177063","student_msg":...,"tutor_msg":...}` (grep this for a fast activity feed).

> **Honest current state:** Saathi stores the **conversation + last-active** reliably today. Structured
> `goal`/`mastery` extraction is the next enhancement on the Gurukul side. So Hermes should start by
> **LLM-summarising `saathi_history`** into a digest (works now), and switch to the structured fields
> once they're populated.

---

## 3. Integration — how Hermes reads it (recommended: a read-only endpoint)

Two ways; **(A) is preferred** (no cross-VM SSH keys):

### (A) Read-only HTTP endpoint on the Gurukul bridge  ← recommended
Add to `~/wa_bridge.mjs` (Caddy `handle /saathi/*` → bridge :8788), protected by a shared key:

```
GET https://gurukul.trigunai.com/saathi/state?key=<SAATHI_READ_KEY>&num=917667177063
→ 200 {
    "employee": "Rohan",
    "number": "917667177063",
    "last_active": "2026-08-06T14:40:00Z",
    "turns": 12,
    "goal": "<structured once extracted, else null>",
    "goal_confirmed": false,
    "recent": [ {"role":"user","content":"…"}, {"role":"assistant","content":"…"}, … last 10 ]
  }
```

Hermes polls this (cron every few hours, and on-demand) and formats a Telegram digest. **This endpoint
is on the Gurukul side — coordinate with the Gurukul/maintain-trigunai-system owner to add it (or ask
Claude in a Gurukul session; ~20 lines + a Caddy `handle` block + a key in `wa_cloud.env`).**

### (B) SSH read (fallback, if you don't want a new endpoint)
From the Hermes box, `ssh -i <gurukul_key> dk_trigun@20.219.2.53 'cat ~/.openclaw/students/917667177063.json'`
(needs Rohan's Gurukul key authorised for the Hermes box — less clean; prefer A).

### (C) Optional real-time push (later)
For instant alerts (e.g. a **confident-wrong on a customer-critical concept**), the bridge can POST a
one-line event to a Hermes ingest URL. Add only after the pull digests are working.

---

## 4. What Hermes surfaces to Deepak on Telegram

Hermes turns the raw data into the **Mentor Cockpit, delivered as chat** (mirrors
`FEEDBACK_SYSTEM.md`'s cockpit, no web page needed):

- **On-demand:** Deepak types *"how's Rohan"* → Hermes pulls `/saathi/state`, LLM-summarises into:
  goal · today's plan · what he learned · activity (last-active, #turns) · any red flag (confident-wrong /
  cold pilot) · **the one mentor action** for Deepak.
- **Daily digest (morning):** a short Telegram card — *"Rohan · goal: … · yesterday: 2 visits, learned
  X · 🔴 shaky on pricing · Your move: 2-min voice note."*
- **Alerts (if push wired):** same-day ping on a customer-critical confident-wrong or a cold pilot.

Keep the **mentor-action framing** from the design: convert tracking → ONE specific thing for Deepak to
do; Red Box (confident-and-wrong) first.

---

## 5. The CEO's OWN companion (build this into Hermes) — same engine, CEO altitude

Deepak wants for himself what Saathi does for Rohan: **hold my goals, run my daily plan/reflect, drive my
learning, trace reality.** Hermes already is his Telegram chief-of-staff — extend it with the Saathi engine
at CEO altitude:

- **Goal store (Hermes box):** Deepak's company + personal goals (e.g. "first cleared payment", a fundraise
  milestone, a learning goal). Locked, held, pointed at daily. Mirrors Goal OS.
- **Daily loop (mirror `trigunai-daily-discipline`):** morning — Hermes asks Deepak's plan against his
  **5 blocks** (Marketing / Robotics / Course / FlowArt / Tech-scan) + the gate-first rule; evening —
  reflect on what actually shipped (output > hours), log it, set tomorrow's lead domino.
- **Learning track (CEO-level):** a daily learning nudge — strategy, a tech-scan item, a founder skill —
  taught question-led with the same mastery check (explain-back + apply). Deepak learns daily too.
- **Reality-check (reuse `founder-reality-check`):** periodically, Hermes commits Deepak to an answer +
  confidence, then grades vs ground truth (repo/live/DB/pulse) → surfaces his **Red Box** (confident-wrong
  about his own company). Deepak is the first dogfood of the "Reality Check" product.
- **Tone for the CEO:** honest operator, not a cheerleader — this is the `trigunai-ceo` hat. (Rohan gets
  a gentle friend; Deepak asked to be pushed hard on follow-through — keep that difference.)

So Hermes ends up running **two companions**: a *window* into Rohan's (read-only, for mentoring) and a
*full* one for Deepak (his goals + learning + daily loop). Same model, two altitudes.

Reuse existing skills as the content/engine: `trigunai-daily-discipline` (the 5-block day + routine log),
`founder-reality-check` (calibration), `trigunai-ceo` (the honest operating hat), `trigunai-campaign-tracker`
(the pulse numbers that are ground truth).

---

## 6. Build checklist (for the Hermes session)

1. **Decide the read path** — recommend (A): request the Gurukul `/saathi/state` endpoint + a shared
   `SAATHI_READ_KEY`. (Coordinate with a Gurukul session to add it; spec in §3.)
2. **Hermes: a `saathi` skill/tool** — fetch `/saathi/state`, LLM-summarise → the digest in §4.
3. **Telegram commands** — `how's rohan` (on-demand) + a daily-digest cron (holiday-aware — reuse
   `employee_training/holidays_2026.json`; Sunday + festivals = no push).
4. **CEO companion (§5)** — goal store + daily plan/reflect loop + learning nudge + reality-check, wired
   into Hermes's Telegram flow, using the existing CEO skills as the engine.
5. **Security (§7).**

---

## 7. Security / privacy

- **Rohan's number + chat are personal data.** Keep `SAATHI_READ_KEY` server-side (Hermes env + Gurukul
  env); never log full conversations to shared channels; the Telegram digests should be *summaries*, not
  raw dumps. Don't commit the number or key to git (it's git-ignored in `employee_training/employees.json`).
- **Read-only** from Hermes — Hermes never writes to Rohan's profile; Saathi (Gurukul) owns that.
- HTTPS only (Caddy) for the endpoint; the shared key gates it.

---

## 8. Pointers

- Saathi (live): Gurukul VM `20.219.2.53`, `~/wa_bridge.mjs::askSaathi`, persona `SAATHI_PERSONA.md`.
- Hermes: Azure VM `azureuser@104.211.75.64` (`~/.ssh/hermes_key`), Telegram `@dk_ceo_tetris_bot`.
- Design docs: `employee_training/{FIELD_SALES_CURRICULUM,TEACHING_STRATEGY,FEEDBACK_SYSTEM,DAILY_COMPANION,SAATHI_PERSONA,COMPANY_CALENDAR}.md`.
- Memories: `[[project-hermes-agent]]`, `[[project-employee-training-os]]`, `[[project-gurukul-vm]]`,
  `[[feedback-daily-discipline]]`, `[[project-founder-reality-check]]`.
