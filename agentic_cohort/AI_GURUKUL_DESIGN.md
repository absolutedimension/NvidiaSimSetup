# The AI Gurukul — an agentic system that teaches each student with their own context

> **One line:** Bloom's 2-sigma (a personal tutor beats classroom teaching by 2 standard deviations)
> made affordable — an agent with per-student memory is that tutor, at near-zero marginal cost.
> Built for the *Building Agentic Systems* cohort (9 modules, weekly live hour, lms.trigunai.com).
> Runs on the existing OpenClaw VM over Telegram + WhatsApp.
>
> **The meta-move:** the system teaching them agents IS an agentic system running the exact
> `perceive → decide → act → observe` loop they build in Session 1. By Module 7 we open the hood
> and show them their own tutor's orchestrator + memory + tools. The course self-demonstrates.

---

## 1. The learning science (highest-effect, async-friendly principles only)

| Principle (the science) | The mechanic that implements it |
|---|---|
| **Curiosity = information gap** (Loewenstein; dopamine = prediction error, Schultz) | Open every concept with a GAP + a prediction prompt, never an answer first. |
| **Retrieval practice + spacing** (Roediger/Karpicke; Ebbinghaus) — *the biggest lever* | Spaced active-recall pings at 1d→3d→7d→16d over TG/WA. Recall, don't re-read. |
| **Desirable difficulty** (Bjork) | Let them hit the wall before scaffolding. Struggle is the encoding. |
| **Formative feedback** (Hattie, top effect size) | Specific, immediate feedback on their real committed code. |
| **Project-based / generation effect** (Papert) | Everything routes through their BYOA use-case. No abstract drills. |
| **Self-Determination Theory** (Deci & Ryan) | Autonomy (their project) · competence (streak + small wins) · relatedness (cohort presence). |

---

## 2. Architecture

**Spine (everything hangs off these two):**
- **Learner Model** — per-student context: goal, level, concept mastery, misconceptions, SRS queue,
  streak, last win, blockers. Stored in **OpenClaw's own memory** (same pattern the course teaches).
- **Orchestrator** — perceive student state → decide which agent acts → act via TG/WA/LMS → observe →
  update model. *This is the agent loop they are learning.*

**The 9 teaching agents (OpenClaw skills), build-ordered:**

| # | Agent | Job | Channel | Phase |
|---|---|---|---|---|
| 1 | Diagnostic | Build initial learner model (goal, level, BYOA) | onboarding | later |
| 2 | **Curiosity Hook** | Gap + prediction before each concept | TG/WA | **MVP** |
| 3 | Socratic Tutor | Just-in-time, ZPD, asks > tells, tied to project | TG/WA + LMS | v2 |
| 4 | Build Coach | Worked-example → faded scaffolding on their code | TG/WA | v2 |
| 5 | **Retrieval Engine** | Spaced active-recall pings (forgetting-curve clock) | TG/WA cron | **MVP** |
| 6 | Reviewer | Formative feedback on commits/answers | LMS hook | v2 |
| 7 | Reflection | Weekly metacognition → updates model | TG/WA | v2 |
| 8 | Motivation/Streak | Goal-gradient nudges, cohort relatedness, wins | TG/WA | v2 |
| 9 | Live-Class Bridge | Surface blockers before the live hour; recap after | LMS digest | v2 |

---

## 3. The weekly flywheel

```
   WEEKLY LIVE HOUR ──► agents own the week ──► back to a higher-value live hour
   (you, build live)                                        ▲
        │                                                   │
        ▼                                                   │
 [Hook next concept] → [Tutor on demand] → [Coach on code] │
        │                                                   │
        ▼                                                   │
 [Retrieval 1d/3d/7d] → [Reviewer on commit] → [Reflect Fri]│
        │                                                   │
        ▼                                                   │
 [Bridge surfaces each student's blockers] ────────────────┘
```

---

## 4. The Learner Model (per-student object — the most important thing in the system)

Stored as one OpenClaw memory record per student. Every agent reads it before acting, writes after.

```json
{
  "student_id": "tg:12345 | wa:+9198...", "name": "...", "channel": "whatsapp",
  "byoa_goal": "an agent that tidies my inbox each morning",
  "level": "writes Python, new to APIs",
  "concepts": { "agent_loop": "solid", "tool_use": "shaky", "memory": "not_seen" },
  "misconceptions": ["thinks the model runs the tool itself"],
  "srs_queue": [ { "concept": "agent_loop", "interval_days": 3, "due": "2026-06-29", "streak": 2 } ],
  "engagement": "high", "streak_days": 4, "last_win": "first tool call fired",
  "current_module": 2
}
```

**Mastery states:** `not_seen → shaky → solid` (promote on a correct unaided recall, demote on a miss).
**SRS rule:** correct recall → `interval_days *= 2.5` (1→3→7→16…); miss → reset to 1 day, mark `shaky`.

---

## 5. The Concept Bank (the spine of retrieval + hooks — mapped to the 9 modules)

Each concept has a **hook** (gap/prediction, sent before teaching) and a **recall** (active-recall
question, sent on the SRS schedule). Grade the recall leniently against the `answer` gist.

| key | module | hook (open the gap) | recall (active recall) | answer gist |
|---|---|---|---|---|
| `agent_loop` | 2 | "A chatbot and an agent get the same question. One stops, one keeps going. What's the extra thing the agent does?" | "No looking — name the 4 steps of the agent loop, in order." | perceive → decide → act → observe, then loop |
| `agent_vs_chatbot` | 2 | "Why can't ChatGPT book your flight even though it 'knows how'?" | "In one sentence: what makes an agent different from a chatbot?" | it ACTS via tools + observes results + loops |
| `tool_is_fn` | 3 | "The model 'calls' a tool. But the model can't run code. So who actually runs it?" | "When a model uses a tool, whose code executes the function?" | YOUR code runs it; model only requests the call |
| `tool_schema` | 3 | "Two identical tools, one gets called and one is ignored. What's the difference the model sees?" | "What part of a tool makes the model decide WHEN to use it?" | the `description` in the schema |
| `tool_boundary` | 3 | "Your agent worked 9 times then crashed. Bet it crashed in the same place every agent does. Where?" | "Where do agents most often fail, and how do you design for it?" | the tool boundary; wrap calls, return a clean error string |
| `context_window` | 4 | "Your agent forgets what it did 20 steps ago. Is it broken, or working as designed?" | "Why does an agent 'forget'? What's the limit called?" | finite context window; old turns fall out |
| `memory_types` | 4 | "What should an agent remember forever, and what should it forget after this task?" | "Short-term vs long-term memory in an agent — what goes in each?" | short = this task's turns; long = facts/prefs persisted |
| `planning` | 5 | "Give an agent a big goal with no plan and it flails. What does a good agent do FIRST?" | "What does multi-step planning let an agent do that a single call can't?" | decompose goal → sub-steps → execute → re-plan |
| `stopping` | 5 | "An agent that never knows when it's done will loop forever or burn your budget. How do you stop it?" | "Two ways to stop an agent loop safely?" | a done-condition + a max_turns cap |
| `orchestration` | 7 | "One agent doing everything gets confused. Companies use many. Who's in charge of the many?" | "What does an orchestrator do in a multi-agent system?" | routes work to specialist agents, manages handoffs |
| `guardrails` | 8 | "Your agent works in the demo and does something dumb in production. What did the demo not have?" | "Name two production guardrails an agent needs." | input validation, retries, cost caps, output checks |
| `cost` | 8 | "Two agents solve the same task. One costs ₹1, one costs ₹100. Same model. What changed?" | "What drives an agent's cost, and one way to cut it?" | tokens × turns; trim context / cheaper model / fewer loops |

*(Extend as modules drip. The hook teaches the meta-lesson too — `orchestration` + `memory_types`
are exactly what the Gurukul itself uses, so you can reveal the hood when those land.)*

---

## 6. How the MVP runs on OpenClaw (Retrieval Engine + Curiosity Hook)

**Trigger (reactive):** student messages the bot → orchestrator reads their Learner Model →
if they're starting a new concept, send the **hook**; if they answer a recall, **grade → update SRS
+ mastery**.

**Trigger (proactive — the spaced pings):** a scheduler tick (cron on the VM) scans all Learner
Models for `srs_queue` items where `due <= today`, picks the most-due concept per student, and sends
that concept's **recall** question over their channel. On reply, grade, then reschedule.

```
cron daily ──► for each student:
                 due = [c for c in srs_queue if c.due <= today]
                 if due: send recall(most_due.concept) via channel
student reply ─► grade vs answer-gist:
                 correct → mastery↑, interval *= 2.5, reschedule, streak++
                 miss    → mastery = shaky, interval = 1d, send the micro-explanation + hook
```

**The one technical dependency to confirm on the VM:** OpenClaw must support **proactive/scheduled
outbound sends** (not just replying when messaged). If it's reply-only today, the Retrieval Engine
needs a small scheduler that pushes via the Telegram/WhatsApp send API. Verify before building §6.

---

## 7. Build order (don't build all 9)

1. **MVP (this week):** Learner Model + Retrieval Engine + Curiosity Hook → one OpenClaw skill
   `gurukul-tutor` + the concept bank above + a daily scheduler. Covers the gap between weekly classes
   — exactly when forgetting happens.
2. **v2:** Live-Class Bridge (makes your human hour 10× sharper) + Reviewer (feedback on commits).
3. **v3:** Socratic Tutor + Build Coach (full in-pocket tutor) + Reflection + Motivation.

---

*Design owner: Deepak. Grounded in Bloom 1984, Roediger/Karpicke, Loewenstein, Bjork, Hattie, Deci & Ryan.
Built 2026-06-26 as the Building Agentic Systems cohort's teaching engine.*
