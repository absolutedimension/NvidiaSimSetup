---
name: trigunai-daily-discipline
description: >
  Deepak's DAILY routine + discipline engine. Run it at the start of each day to lock the 5
  work blocks, route each to the skill that owns it, and at the end of the day to log what was
  actually produced (building a visible streak). The 5 blocks (11 hrs): (1) 2h Marketing for the
  learning courses — reels/videos posted to public platforms; (2) 2h Robotics AI — training the
  drone policy; (3) 4h Learning the courses in depth + writing course scripts + flow design;
  (4) 2h Flow Art Dance — push the VR app to Live + make YouTube channel content; (5) 1h scanning
  new tech in the market. Discipline rule = OUTPUT over hours (a block is done when it ships a
  logged artifact, not when time passes) and GATE-FIRST (Marketing + Course are revenue; if the
  day collapses, those two survive). Logs to daily_routine/ROUTINE_LOG.md (cross-session evidence).
  USE WHEN Deepak wants to start/plan/run/close his day or check discipline. Triggers on: "my
  routine", "daily routine", "start my day", "run my day", "plan my day", "what should I work on
  today", "my blocks", "daily blocks", "time blocks", "focus blocks", "discipline", "log my day",
  "end of day", "close the day", "did I do my blocks", "my streak", "/daily", "today's plan",
  "morning kickoff". Companion to content-daily-engine (it owns Block 1's marketing pipeline),
  trigunai-training (Block 2), trigunai-content-strategy + video-script-writer (Block 3),
  trigunai-vr + trigunai-youtube (Block 4). This skill OWNS the daily rhythm + the routine log.
---

# TrigunAI Daily Discipline — the day engine

> **Job:** turn the *intention* of a disciplined day into a *logged, repeatable* one. Each
> morning: lock the 5 blocks and what each must ship. Each evening: log what actually shipped.
> Repeat. Gradual, compounding, evidence-backed — not vibes.
>
> **The two laws (read every day):**
> 1. **OUTPUT > HOURS.** A block is "done" only when it produces a *named artifact in the log*
>    (a posted reel, a checkpoint, a written script scene, a shipped build step, a tech note).
>    "I spent 2 hours" is not done. Time is the budget; the artifact is the proof.
> 2. **GATE-FIRST.** The company's gate is still **first cleared payment (0 paid today).** Blocks
>    1 (Marketing) + 3 (Course) directly feed that gate — they are non-negotiable. Blocks 2, 4,
>    5 are upside/IP/input. If a day collapses, **protect 1 + 3, drop the rest** without guilt.
>
> **The lens (why the laws exist — see `SYSTEMS_THINKING_PLAYBOOK.md`):** getting paid is a
> **COMPLEX** system (cause→effect only clear in hindsight, no feature "solves" it), so it yields
> only to *real-world experiments with humans*. Building is a **COMPLICATED** system — your
> superpower, and instant-reward, which is exactly why you drift to it. The gate-first law is the
> guardrail against spending a complex problem's time on a complicated problem's dopamine.
>
> Log: `daily_routine/ROUTINE_LOG.md` (this skill writes it). Plan: `daily_routine/PLAN.md`
> (today's concrete tasks). Resolver: `scripts/today.py`. Owner: Deepak. Cadence: daily.

---

## 0. HOW YOUR SYSTEM WORKS — the 30-second reminder (shown every day)

**Three layers, three hats — don't mix them:**
- **Direction** = `trigunai-ceo` — truth, the gate, strategy, grants, pitch. Open it **Mondays + for
  real decisions**, NOT to make things.
- **Rhythm** = THIS skill (`trigunai-daily-discipline`) — your **daily front door**. It sets today's
  tasks, picks the model, and holds you accountable.
- **Execution** = the specialist skills — they make the thing. One session each, named `D#·…`.

**The map — open the skill that OWNS the work (not CEO):**
reel/post → `content-daily-engine` · course script → `video-script-writer-trigunai` ·
web/app → `trigunai-dev` · drone pipeline → `trigunai-drone-pipeline` · general sim → `trigunai-training` · VR / Flow-Art → `trigunai-vr` ·
music → `production-music-trigunai` · YouTube → `trigunai-youtube` · strategy/gate → `trigunai-ceo`.
*(Full operating model: `HOW_I_RUN_TRIGUNAI.md`.)*

**Sessions don't share memory — FILES do.** Read the plan/log at start, write the log at end.
Today's tasks live in `daily_routine/PLAN.md`; what you shipped goes in `daily_routine/ROUTINE_LOG.md`.

**Use the cheapest model that does the job (spend tokens intelligently):**

| Model | Cost | Use for |
|---|---|---|
| **Haiku** | cheapest | mechanical — uploads, running scripts, file ops, quick web lookups, the tech-scan summary |
| **Sonnet** | mid | the broad middle — most coding, writing scripts/content, content production, VR/Unity work |
| **Opus** | priciest | hard reasoning only — CEO/strategy, curriculum & flow design, tricky debugging, RL reward design |

> **Rule:** start at the cheapest model that could plausibly do it; escalate only when it struggles.
> Don't run Opus for an upload; don't run Haiku for strategy. Each `PLAN.md` task carries an
> `@model:` tag and the morning brief prints it per block — **set that model when you open the session.**

---

## A. ACCOUNTABILITY PROTOCOL — run this BEFORE planning today (non-negotiable)

> **Deepak's standing instruction (2026-06-22, on record):** *"I lack following a routine on a
> regular basis — you have to be hard on me to complete my task daily."* This section is the
> authorization to do exactly that. Be blunt about the gap. Never soft-pedal a missed day, never
> cheerlead a half-day as if it were full. **Attack the gap, not the person** — the goal is to get
> the streak moving, not to make him feel bad. But do not let him paper over a miss.

**Every time this skill runs, do the audit FIRST — before you talk about today:**

1. **Run the audit:**
   ```bash
   python3 ~/.claude/skills/trigunai-daily-discipline/scripts/today.py --audit 7
   ```
   It lists the last 7 days and flags: **MISSING** (no row), **EMPTY** (row stamped, 0 blocks
   done), and **partial** days, plus the streak and gate-days.

2. **Confront every gap out loud.** For each MISSING/EMPTY/partial day, name it and ask Deepak to
   account for it in one line: a real reason or an honest *"I skipped."* No silent roll-forward.
   Write his reason into that day's row. A pattern (same block skipped 3 days running, or two
   EMPTY days) gets named as a pattern, not treated as three unrelated misses.

3. **Verify, don't trust the ticks — this is the teeth.** A `[x]` is a *claim*; demand the
   *evidence*. Cross-check against ground truth:
   - **Block 1 (Marketing):** is there an actual **public link** + a row in
     `marketing_pipeline/CONTENT_LOG.md`? No link ⇒ it's `[ ]`, not done.
   - **Blocks 2/3/4:** is there a **file, path, commit, or upload**? Run
     `git -C <repo> log --oneline --since=yesterday` and check the work-scanner
     (`project_hub/WORK_LOG.md`) / `daily_routine/`. A claim with no artifact = **DISPUTED** —
     say so and downgrade it to `[ ]`.
   - **Cross-session truth:** Deepak works across Claude surfaces + his phone; the local scanner
     misses email/no-file work. If a block is plausibly done off-repo (e.g. a post, an outreach
     email), check `in:sent` before disputing — but still require the link in the log.
   - **Never count a sent invoice / "welcomed student" as a paid student** (CEO gate: a cleared
     UTR only). Marketing output is measured in **intro-class registrations**, not likes.

4. **Close yesterday before opening today.** If yesterday's row is unfilled, you fill it (with
   Deepak) FIRST. He doesn't get to plan a shiny new day on top of an unaccounted one.

5. **State the verdict in one hard line**, e.g.: *"Streak: 0. Yesterday was EMPTY — you stamped
   it and shipped nothing. Gate-days this week: 1/7. That's not a routine yet, it's a list. Today
   we fix it: Block 1 + Block 3, minimum, before anything fun."*

**Escalation rules (apply them, don't just hold them):**
- **Streak broken (a MISSING/EMPTY day):** it resets to 0 and he must acknowledge it in writing in
  the log. No quiet restart.
- **2 gate-days missed in a row** (Block 1 or 3 skipped two days running): stop the block-planning
  and have the real conversation — *"what is actually blocking you?"* — because the routine is
  failing at its only job (moving revenue). Route to `trigunai-ceo` System 7 if it's bandwidth/energy.
- **3 consecutive full misses:** escalate hard — this isn't a scheduling problem, it's a commitment
  problem; name it plainly and ask what needs to change (scope, hours, the routine itself).

---

## B. THE SYSTEMS CHECK — classify before you build (DART, 30 seconds)

> Run this once each morning, right after the audit, **before** you let the plan default to
> building. Its only job: catch the days when you're about to spend complex-system time
> (getting paid) on complicated-system work (shipping a feature), because that feels productive
> and is the #1 way the gate stays at 0. Full rationale: `SYSTEMS_THINKING_PLAYBOOK.md`.

Ask the four DART questions about **today's most important goal** (usually: move the gate):

- **D — Deconstruct.** Is the goal made of *stable* parts (a bug, a deploy, a render) or *shifting*
  ones (a human deciding to pay)? Shifting ⇒ it's not a keyboard problem.
- **A — Analyze (the key one).** Is cause→effect **obvious** (Clear → checklist), **expert-solvable**
  (Complicated → build/analyze), **hindsight-only** (Complex → run a cheap experiment, don't build),
  or **broken** (Chaotic → stabilize first)? *Paid, PMF, "which channel works" = Complex, always.*
- **R — Recognize.** Have I seen this pattern? If today's plan is "build another feature and revenue
  will follow," that's the **build-trap** (PMF audit closed 0/3, the ₹499 silent pivot). Name it.
- **T — Test.** For any Complex goal, the day's move is the **smallest real-world test** — one Patna
  visit, one "will you pay ₹X" ask, one WhatsApp cohort blast — **not** a 2-week build.

**The verdict, in one line:** *"Today's gate work is a COMPLEX problem → my Block 1/3 action is an
experiment with a real human, not a feature."* If you can't say that, the plan is mis-typed — fix it
before stamping the row. **One real-world revenue action ships every day**, to keep the slow sales
feedback loop competitive with building's instant hit (§the delay problem).

---

## 0. THE 5 BLOCKS (11 hours)

| # | Block | Hrs | Owns the work (load this skill) | Engine | DONE = (the logged artifact) |
|---|---|---|---|---|---|
| **1** | **Marketing** — reels/videos posted to public platforms for the courses | 2h | `content-daily-engine` → `content-marketing-emotion-connect` → render → `trigunai-marketing` | A · **Revenue** | ≥1 asset **posted publicly** today, driving to the intro-class CTA + logged with the link |
| **2** | **Robotics AI** — training the drone policy | 2h | `trigunai-drone-pipeline` (full pipeline: train → export → render → VLM eval → GLB) or `trigunai-training` (general sim work) | B · IP/fundraise | One concrete advance: a train run launched, a checkpoint, a trajectory export, or a VLM eval — with the path/number logged |
| **3** | **Course mastery + scripting + flow design** — learn the material in depth, turn it into script + flow | 4h | `trigunai-content-strategy` + `video-script-writer-trigunai` | A · **Revenue (the product itself)** | A captured artifact: a module outline, a script scene, or a flow/lesson design — **written down**, not just "studied" |
| **4** | **Flow Art Dance** — push the VR app to Live + make YouTube channel content | 2h | `trigunai-vr` + `production-video-trigunai` / `production-music-trigunai` + `trigunai-youtube` | Movement II | A build step toward Live OR a piece of channel content shipped — logged |
| **5** | **Tech scan** — what's new in the market/tech | 1h | `WebSearch` / `deep-research` | Input | **3 items + 1 "so-what for TrigunAI" line** captured in the log. Browsing with no note ≠ done |

> **Why these and not others:** this is the routine Deepak chose (recorded 2026-06-22). The OS
> doesn't second-guess the *set* — it enforces that the set produces *output* and stays
> *gate-honest*. Block 3 is the biggest because the live cohort **is** the product and the profit
> engine; Block 1 fills the room for it. Blocks 2 + 4 compound IP and Movement II but do not move
> the revenue gate — never let them quietly displace 1 + 3 (CEO OS anti-patterns #18/#19/#20).

---

## 1. THE MORNING RUN (start of day)

0. **Do §A first — the audit + confront yesterday.** Never skip to planning today over an
   unaccounted yesterday. **Then run §B — the 30-second systems check (DART)** so today's gate
   work is typed as an *experiment*, not a build, before you plan the blocks.
1. **Resolve today.** Run the day resolver — it prints the 5 blocks, today's gate reminders, your
   current **streak**, and the last-7-day adherence per block:
   ```bash
   python3 ~/.claude/skills/trigunai-daily-discipline/scripts/today.py
   ```
   (Run from the repo root so it finds `daily_routine/ROUTINE_LOG.md`. Pass a date to plan ahead.)
2. **Stamp today's row.** Append today's skeleton to the log so the day has a home to fill:
   ```bash
   python3 ~/.claude/skills/trigunai-daily-discipline/scripts/today.py --new
   ```
3. **Read today's tasks from the plan.** The resolver prints, per block, the top unchecked item in
   `daily_routine/PLAN.md` as **TODAY:** plus the **[model: …]** to run it on. That *is* your task
   list — you don't have to invent it each morning; you maintain `PLAN.md` and the brief surfaces it.
   Confirm/adjust the top item per block, then set its target small enough to finish in the hours.
   (Edit `PLAN.md` whenever priorities shift — reorder so the right thing is on top.)
4. **Honor today's special slot** (the resolver flags it):
   - **Fri** → Block 1 *is* the **free-intro-class INVITE** (LinkedIn + email). This fills Saturday.
   - **Sat** → Block 1 *is* **running the free live intro class** — the conversion event. Book 1:1s after.
   These two are the weekly gate-movers (per `content-daily-engine`). Protect them over anything.

---

## 2. RUNNING A BLOCK

For each block, **load the owning skill and do the work there** — this skill is the conductor, not
the orchestra. The owning skill knows the pipeline; this skill only guarantees the block ships an
artifact and gets logged.

- **Block 1 (Marketing):** invoke `content-daily-engine` (it resolves the day's content slot,
  runs it through the emotion OS, renders, distributes, and logs to `CONTENT_LOG.md`). Block 1 is
  "done" when something is **publicly posted** with the intro-class CTA. *Reach is not the score —
  registrations are.*
- **Block 2 (Drone):** invoke `trigunai-drone-pipeline` for the full chain (Isaac Lab PPO →
  trajectory export → OVRTX render → VLM quality gate → animated GLB delivery) or
  `trigunai-training` for general sim/rendering work. Start the EC2 box only when actually
  training (~$1/hr — stop it after). Log the checkpoint path / reward / eval verdict.
- **Block 3 (Course):** invoke `trigunai-content-strategy` to pick what to deepen, then
  `video-script-writer-trigunai` to convert the learning into a script/flow artifact. The trap
  here is infinite study — **end every Block-3 session with a written file**, even a rough one.
- **Block 4 (Flow Art / VR):** invoke `trigunai-vr` for the app-to-Live work, or the production
  skills + `trigunai-youtube` for channel content. Pick ONE of the two sub-goals per day (Live
  push *or* content) — don't split 2 hours across both and finish neither.
- **Block 5 (Tech scan):** `WebSearch` / `deep-research`. End with **3 items + the one line that
  matters: "so what does this change for TrigunAI?"** That line is the deliverable.

---

## 3. THE EVENING CLOSE (end of day)

Fill in today's row in `daily_routine/ROUTINE_LOG.md` honestly. For each block: `[x]` + the
artifact (link/path/filename), or `[ ]` + one word why it didn't ship. Then one **Reflection**
line and tomorrow's **lead domino**.

**Honesty rules (CEO OS carries into the log):**
- A block with no artifact is **`[ ]` even if you spent the hours.** The streak is built on output.
- Marketing "done" needs a **public link**. A drafted-but-unposted reel is `[ ]`.
- Don't log a payment/student as won until it's real (a cleared UTR, not a sent invoice).

Template the resolver writes:
```
## 2026-06-22 Mon  (gate: 0 paid)
- [ ] 1 Marketing (2h)   — target: …            → artifact:
- [ ] 2 Robotics  (2h)   — target: …            → artifact:
- [ ] 3 Course    (4h)   — target: …            → artifact:
- [ ] 4 FlowArt/VR(2h)   — target: …            → artifact:
- [ ] 5 TechScan  (1h)   — target: …            → artifact:
Reflection:
Tomorrow's lead domino:
```

---

## 4. THE SCOREBOARD (what the streak means)

The resolver reports two numbers — keep them honest, they're different things:

- **Streak** = consecutive days you *showed up and logged* (any block done). This is the
  discipline habit. Protect it; missing a day resets it to 0.
- **Gate-days** = days where **both** Block 1 (Marketing) **and** Block 3 (Course) shipped. This
  is the number that actually moves the business. A long streak with few gate-days means the
  routine is busy but drifting off revenue — the OS will say so.

> **The weekly check (Sunday or Monday):** "How many gate-days this week? Did the marketing
> blocks produce intro-class registrations? Did the course blocks add to the *shippable* cohort?"
> If gate-days < 4/7, next week rebalance toward Blocks 1 + 3 — even if it means a 7-block day
> becomes a 3-block day. **Fewer blocks done well beats five blocks half-done.** (System 7.)

> **The monthly platform check (get off the moving train — `SYSTEMS_THINKING_PLAYBOOK.md §4`):**
> from inside the system you can't tell if you're moving. Use **data + time** to stand on the
> platform. Once a month ask the single honest question: **"vs 30 days ago, did *paid* move?"**
> (Read it from `/admin/api/pulse` via `trigunai-campaign-tracker` — paid, not signups, not reach.)
> If paid didn't move despite versions shipped, the train hasn't moved: **change the experiment,
> not the product.** A month of green streaks with paid still at 0 is the build-trap wearing a
> disguise — the OS names it.

---

## 5. WHEN A DAY BREAKS (the realistic-day rule)

11 hours is the *full* shape, not the *minimum*. A real day with a meeting, a render that hangs,
a low-energy afternoon, or the Vintage call will not fit all five. That's fine. The fallback:

- **Minimum viable day = Block 1 + Block 3** (the two revenue blocks). Ship one public marketing
  asset + write one course/script artifact. If only that happens, the streak holds and the gate moves.
- **Collapsed day** = ship the smallest gate-touching thing (one Short reposted, one script
  paragraph) and log it honestly with why. A logged small day beats a silent skipped one.
- **Never trade sleep for the streak.** Burnout ends the company faster than a broken streak does.

---

## 6. INTEGRATION MAP

```
trigunai-daily-discipline  (this — the day's conductor + the routine log)
   │
   ├─ Block 1 → content-daily-engine ──→ content-marketing-emotion-connect ──→ production-video / faceless-explainer ──→ trigunai-marketing   (logs CONTENT_LOG.md)
   ├─ Block 2 → trigunai-training       (EC2 / Isaac / OVRTX / drone policy)
   ├─ Block 3 → trigunai-content-strategy + video-script-writer-trigunai   (course → script → flow)
   ├─ Block 4 → trigunai-vr  +  production-video/music  +  trigunai-youtube   (VR-to-Live + channel content)
   └─ Block 5 → WebSearch / deep-research   (3 items + so-what)
```

The CEO OS (`trigunai-ceo`) sits above all of this: it owns the gate and the weekly review. This
skill is how the gate gets served *daily*. At any session start, the CEO work-scanner + the
`ROUTINE_LOG.md` together are the ground-truth of what Deepak actually did.

---

*Built 2026-06-22 from Deepak's chosen routine. Two laws: output > hours, gate-first.
Owner: Deepak. Log: daily_routine/ROUTINE_LOG.md.*
