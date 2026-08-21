---
name: sankalp-daily-gate
description: >
  The 60-second GATE that opens and closes Deepak's day, enforcing the one live vow in
  NvidiaSimSetup/SANKALPA.md. Runs BEFORE trigunai-daily-discipline, not instead of it —
  this skill owns the GOAL layer (is today serving the one committed goal?), daily-discipline
  owns the TASK layer (the 5 blocks). Morning: read the vow, name the day's ONE selling action,
  refuse build work until it is named. Night: append ONE line — ON / OFF / अतिचार. It writes
  nothing except that line in SANKALPA.md. USE WHEN Deepak says: "start my day", "open the day",
  "my sankalp", "sankalpa", "record my sankalp", "close the day", "end of day", "log today",
  "am I ON or OFF", "/sankalp", "/gate", "did I hold it", "my streak", "what's my vow".
  Also invoke UNPROMPTED at the top of any session that proposes a new build, repo, product
  line, workstream, or skill — check the सीमा list first. Companion to
  trigunai-daily-discipline (hand off to it once the gate passes) and dk-decision (the only
  legitimate way to exit a vow is a pre-written kill rule firing).
---

# संकल्प — the daily gate

> **Job:** answer one question a day, in writing. *Did today serve the goal I committed to, or a different one?*
>
> **This skill is deliberately tiny.** A morning ritual that takes longer than 60 seconds does not get run. If you are tempted to add a section here, add it to `SANKALPA.md` instead — or better, don't.
>
> **State lives in ONE file:** `NvidiaSimSetup/SANKALPA.md`. No second log. No dashboard. No streak app.

## Why this exists (read once, not daily)

`daily_routine/ROUTINE_LOG.md` has been correctly diagnosing this problem since 22 June and it has not moved the gate. It **describes**; it does not **forbid**. Its 5-block shape always yields an `[x]`, so a pure build day reads as a win — see 2026-08-14, where Block 3 got a large artifact and the gate move was PENDING in the same entry.

This gate exists to make one thing impossible to fake: **build work does not count, no matter whose name is attached to it.**

---

## MORNING — the open (60 seconds)

```bash
python3 skills/sankalp-daily-gate/scripts/gate.py
```

That prints the vow, days remaining, the streak, and the सीमा list. Then, in order:

1. **Is the vow still live?** If past its **काल**, do NOT roll it over. Stop and re-take or drop it in writing (§ Expiry). A silently-extended vow is not a vow.
2. **Name today's ONE selling action.** One line, ≤10 words, a human on the other end. Write it into the log row as `(pending)`.
3. **Do it.** Naming is not doing — the vow says the action must be **done** before build work, not merely written down. A named-but-pending action does not open the day.
4. **Then, and only then**, hand off: invoke `trigunai-daily-discipline` for the 5 blocks.

**Refuse to skip step 2.** If Deepak opens the day with a build request, answer with the vow, not the code. The correct response is one sentence — *"Naming today's selling action first; what is it?"* — not a lecture, and not a refusal to ever do the build.

## The one test — what counts as the selling action

A human, named, who can say no.

| Counts | Does not count |
|---|---|
| Sending Rohan the brief / demo pack | Fixing bugs for the demo |
| Asking an institute for the money | Building what they asked for |
| Putting a paper in front of a real student | Generating 2,000 more questions |
| A call, a visit, a message that lands | Waiting for their reply |

**"Waiting" is never an action** — it is an outcome arriving. It scores neither way.

**Build work with a customer's name on it is still build work.** It may be permitted (आगार 3), but permitted ≠ counted. This is the single most common way the day gets faked, and the reason the last eight weeks looked productive and moved nothing.

---

## NIGHT — the close (2 lines)

Append to the log table in `SANKALPA.md`. Nothing else. Do not journal, do not summarize the day, do not add a Reflection paragraph — `ROUTINE_LOG.md` already owns that, and duplicating it is how this file dies.

- `ON` — the selling action happened, before any build work.
- `OFF` — it didn't. Write OFF plainly. **An OFF that gets argued into an ON destroys the instrument** — the whole value here is a number Deepak cannot argue with.
- `अतिचार` — an आगार fired (client obligation, live-system breakage, illness). **Infraction, not break.** The vow continues. Never convert a slip into a collapse.

Then stop. The close is two lines and a full stop.

## Weekly (Sundays, 30 seconds)

Count. `5/7 ON` is the whole review. If ON < 4 in a week, the problem is a **parameter**, not willpower — walk the seven in `SANKALPA.md` and find the unset one (usually साक्षी or मूल्य). दृढ़ता is an output, never a setting.

## Expiry

On the **काल** date, exactly three outcomes, all written:

- **Held + target hit** → re-take, longer काल, bigger विषय.
- **Held + target missed** → the vow succeeded, the target didn't. **Do not switch lines.** Change the method, keep the goal. This is the reflex being trained out.
- **Broke** → name which parameter was unset. Then take a *smaller* one. अणुव्रत before महाव्रत — the asset is the reliability of the word, not the size of the goal.

## The refusal clause

When any session — including one Deepak starts enthusiastically — proposes work inside the **सीमा** list, say so and cite the vow before doing it. Then ask exactly one question: *is an आगार firing, or are you dropping the vow deliberately, in writing?*

Both answers are acceptable. **Silence is not.** Project 32 has never once announced itself as project 32.
