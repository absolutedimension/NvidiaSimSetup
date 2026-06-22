# How I Run TrigunAI — the operating model

> For Deepak. One company, many skills, many sessions. This is how they fit together so you
> run the business instead of drowning in it. Written 2026-06-22.

---

## The one idea that fixes everything

**Sessions don't share memory. FILES do.** Every Claude session starts blank — it knows nothing
about your other sessions. So the way a multi-session, multi-skill company stays coherent is:
**each session reads the shared files when it starts, and writes them when it ends.** The files
are the company's brain; the sessions are just hands that pick it up.

You already half-knew this — that's why you name your sessions. The upgrade: stop relying on the
*name* to carry the context, and start relying on the *files*.

The shared brain:

| File | What it holds | Who writes it | Who reads it |
|---|---|---|---|
| `project_hub/CEO_BRIEFING.md` | The narrative truth — where the company actually is | CEO sessions | every CEO session, at start |
| `daily_routine/ROUTINE_LOG.md` | What you did each day (the 5 blocks) | daily-discipline | morning/evening check + you |
| `marketing_pipeline/CONTENT_LOG.md` | What marketing actually shipped (links) | content-daily-engine | evening check, CEO |
| `project_hub/WORK_LOG.md` | Auto-scanned ground truth (commits, sessions) | `ceo_work_scan.py` | CEO at session start |
| `memory/` | Durable cross-session facts + your preferences | any session | every session (auto-loaded) |

**Rule:** end every session by updating its log. Start every CEO/daily session by reading them.

---

## The three layers (which hat for which work)

```
DIRECTION   →  trigunai-ceo            (truth, gate, strategy, grants, pitch, weekly review)
   │            "what matters, what's real, did anyone pay"
   ▼
RHYTHM      →  trigunai-daily-discipline   (the 5 blocks, the streak, the daily dispatch)
   │            "what am I doing today, did I ship it"
   ▼
EXECUTION   →  the specialist skills    (make the reel, write the script, train the drone…)
                "do the actual work"
```

- **You don't open CEO to make a reel.** You open CEO when you need a *decision* or a *truth check*:
  am I on track, what do I tell an investor, is this strategy doc honest, what's the week's one move.
- **You don't open CEO to plan your day either.** That's `trigunai-daily-discipline` — your single
  entry point each morning. It dispatches each block to the right execution skill.
- **Execution skills do the work.** One session each, named by the work.

---

## The map — "when I want X, open this skill"

| I want to… | Open this skill (the doer) | It chains to |
|---|---|---|
| Make a reel / short / post / thumbnail / hook | **content-daily-engine** | emotion-connect → production-video / faceless-explainer → trigunai-marketing |
| Decide the *feeling* of a piece before making it | **content-marketing-emotion-connect** | (then a render skill) |
| Render a narrated video / module / episode | **production-video-trigunai** | — |
| Make a faceless b-roll explainer | **faceless-explainer-trigunai** | — |
| Write a course/module video script | **video-script-writer-trigunai** | production-video |
| Decide what episode/content to make next | **trigunai-content-strategy** | video-script-writer |
| Make music / focus audio / a song | **production-music-trigunai** | — |
| Upload / publish / set thumbnails on YouTube | **trigunai-youtube** | — |
| Build/fix a landing page, web app, API, service | **trigunai-dev** | — |
| Build/ship the VR app (Gurulok / Flow Art) | **trigunai-vr** | — |
| Train the drone policy / Isaac / render on EC2 | **trigunai-training** | — |
| Distribute content across channels (email/TG/Discord) | **trigunai-marketing** | — |
| Run a locked, day-by-day plan autonomously | **trigunai-executor** | — |
| Check status / brief me / cross-agent handoff | **trigunai-project-hub** | — |
| Strategy, gate, grants, pitch, "are we on track", honest status | **trigunai-ceo** | — |
| Plan/run/close my day, check my discipline | **trigunai-daily-discipline** | dispatches to all of the above |

> If you're ever unsure which skill: just describe the task in plain words at the start of a session
> — the right skill auto-triggers from its description. You rarely need to name it yourself.

---

## Session naming — tie it to your 5 blocks

Name each work session by the block + the task, so the name tells you *which block it serves* (this
also makes your day legible to the evening accountability check):

```
D1·MKT   — Wed nudge reel for the 3 invoices
D2·DRONE — 500-iter retrain + VLM eval
D3·COURSE— Agentic Module 3 script
D4·VR    — Flow Art app: push build to Live
D5·SCAN  — what's new in world-models this week
CEO      — Monday review / Vintage call prep
```

`CEO` and `DAILY` get their own prefixes because they're the steering layer, not a block.

---

## The cadence that ties it together

- **Each morning:** open `trigunai-daily-discipline` ("start my day"). It stamps the day, shows your
  blocks + streak, and you fire off one execution session per block. (The 7am email does this for you.)
- **During the day:** one execution session per block. Name it `D#·…`. End it by logging the artifact.
- **Each evening:** the 9pm check reads your logs + git and tells you the truth. Fill your row honestly.
- **Each Monday:** ONE `CEO` session — the weekly review. Read WORK_LOG + inbox + briefing, decide the
  week's ONE move, update CEO_BRIEFING.md.
- **Ad-hoc:** open `CEO` only for a real decision or truth-check — not for execution.

---

## Five efficiency rules

1. **One conductor, not six.** Your single daily entry point is `trigunai-daily-discipline`. Everything
   fans out from there. Don't start your day by opening six skills and guessing.
2. **Right hat for the work.** Don't CEO a reel. Don't execute in a strategy session. Mixing them is
   why work feels slow and steering feels absent.
3. **The files are your memory — not your head, not the session name.** Update the log when you finish.
   A session whose work never touched a file is invisible to tomorrow (and to the work-scanner).
4. **Batch by block, not by ping.** Do your 2h of marketing in one focused session, not seven scattered
   reel-sessions. Context-switching across skills all day is the solo-founder tax.
5. **Gate-first, always.** With ~20 skills it's easy to feel productive while the gate (first paid
   rupee) doesn't move. Marketing + Course are the only two blocks that touch revenue. The others
   compound IP and reach — real, but secondary until someone pays.

---

*The system is big so that YOU can be small on any given task — pick the block, open the skill, ship
the artifact, log it. The CEO layer keeps the whole thing pointed at the one thing that matters: a
cleared payment.*
