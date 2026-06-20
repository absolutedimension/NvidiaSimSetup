# TrigunAI LMS — Learning Design & Gamification

> How we teach (Brilliant-style) and how we make it *feel* like a game. This is the design bible
> for every lesson and every reward. Pairs with `PROJECT_PLAN.md` (architecture).

---

## 1. The core teaching principle (non-negotiable)

> **The medium IS the teaching method. Make the learner DO the work — predict, manipulate, solve —
> BEFORE showing any explanation.**

This is Brilliant's founding rejection of passive video. We keep our flipped model (video before
the live session), but the *lesson itself* is never a video — it's an interactive sequence that
forces active production first, explanation second. Active learning is ~6× more effective than
watching; it's also why learners *finish*.

**The loop, every single time:** `try → struggle → feedback → understand` — never
`watch → understand → try`.

---

## 2. Anatomy of one lesson (the template every lesson follows)

A lesson = **one concept**, ~6–9 steps, 5–12 minutes.

| # | Step | Rule |
|---|------|------|
| 1 | **Micro-intro** | 2–4 sentences + one visual. Just enough framing. Never a lecture. |
| 2 | **Immediate challenge** | Learner acts right away using the just-shown idea (predict / tap / drag). |
| 3 | **Instant, specific feedback** | Wrong → the thing reacts + a Socratic hint that nudges *reasoning*, never the answer. Right → reveal + advance. |
| 4 | **Scaffolded ramp** | Each next step builds on the proven one; difficulty climbs gently. |
| 5 | **Scaffold removal** | The last practice step strips hints — unaided mastery. |
| 6 | **Make it yours** | Apply the concept to the student's *own* agent use-case (ties to the workbook). |
| 7 | **Mastery summary** | Checkmarks + the one-line takeaway + reward burst. |

**Why? / Skip explanation:** after a correct answer, the learner chooses depth. Fast learners skip;
strugglers get the deep dive. Respect their time — it's a retention and satisfaction lever.

---

## 3. The interactive primitives (our lesson "component library")

Every lesson is assembled from these step types. Building them once lets us author lessons 2–9
as pure content. (All are implemented in the Lesson 1 engine.)

| `kind` | What it does | Used for |
|---|---|---|
| `intro` | text + visual + Continue | framing |
| `mcq` | predict-before-explain multiple choice, Why?/Skip | concept checks |
| `reveal` | tap cards to expose ideas; gated Continue | introduce a small set (e.g. the 4 parts) |
| `classify` | tap item → tap bucket; **live constraint checklist** turns green | mapping things to categories |
| `order` | tap chips into a sequence; validate order | processes / loops |
| `slider`/`toggle` | manipulate a parameter, see the system change | contrast, cause→effect |
| `reflect` | free-text input(s); always-accept, encouraging | "make it yours" → workbook |
| `done` | mastery summary + celebration | lesson end |

### Lesson authoring schema (JSON)

```json
{
  "slug": "what-is-an-agent",
  "module": 1,
  "title": "What is an agent?",
  "max_gems": 100,
  "steps": [
    { "kind": "intro", "art": "🤖 → 🔁", "prompt": "...", "sub": "...", "cta": "Start" },
    { "kind": "mcq", "prompt": "...", "options": ["...","..."], "correct": 1,
      "why": "...", "hints": ["socratic hint 1","socratic hint 2"] },
    { "kind": "classify", "prompt": "...", "buckets": ["Goal","Brain","Tools","Loop/stop"],
      "items": [{ "t": "...", "b": 0 }], "constraints": ["All placed","All correct"],
      "hints": ["...","..."] },
    { "kind": "order", "prompt": "...", "chips": ["Act","Think","Observe"],
      "correct": [1,0,2], "constraints": ["Loop order correct"], "hints": ["..."] },
    { "kind": "reflect", "prompt": "...", "fields": [{ "k":"goal","label":"...","ph":"..." }] },
    { "kind": "done" }
  ]
}
```

> **Migration note:** Lesson 1 currently hard-codes `STEPS` inside `index.html`. The engine refactor
> (post-Friday) loads this JSON from the API so non-engineers can author lessons. Same data shape.

---

## 4. The Socratic tutor ("Koji") — ask, then guide

Koji never hands over the answer. On a wrong attempt it opens and asks a guiding question.
Observed escalation (built into each step's `hints` array):

```
1. Diagnose:      "Walk me through how you got there — what made you pick that?"
2. Decompose:     break the goal into the smallest failing sub-check
3. One question:  lead with a single targeted question
4. Withhold:      hints escalate slowly; the answer is the last resort
5. Track state:   knows which constraint/step is failing right now
6. Adapt pace:    speed up when mastered, slow down on a gap
```

**Now:** rule-based, driven by each step's `hints` (works offline, ships Friday).
**Next:** wire to the LiteLLM proxy (Azure GPT-4o-mini) for true conversational tutoring — the
prompt gets the problem, the constraints, the learner's current widget state, and the strict
"never give the answer" system prompt. ~30 lines, drop-in.

---

## 5. Gamification — the psychology, then the rules

We're not bolting on points for decoration. Three forces do the work:

1. **Progress made visible** — a journey map, a filling bar, levels. The brain rewards perceived
   forward motion. (Endowed-progress effect.)
2. **Variable, immediate celebration** — coins on correct, confetti on complete, **balloon-burst**
   on milestones. Dopamine loves the *unexpected* small win. Keep bursts crisp, never annoying.
3. **Streaks = loss aversion** — a daily streak the student doesn't want to break is the single
   strongest driver of the "40 minutes a day" habit the cohort PDF asks for.

### Reward map (canonical — also in PROJECT_PLAN §6)

| Event | Points | Celebration |
|---|---|---|
| Step correct (first try) | +10 | coin pop + tick |
| Lesson complete | +25 | confetti |
| Perfect lesson | +15 | extra confetti |
| Daily workbook task | +10 | coin pop |
| "Bring to Friday" item | +30 | confetti |
| Streak day | +5 × multiplier | streak flame +1 |
| Streak milestone 3/7/14/30 | +20/50/120/300 | **balloon burst** + badge |
| Week complete | +100 | full-screen balloon burst + level-up check |
| Module watched | +15 | coin pop |
| Demo Day capstone | +500 | finale burst |

### Levels (the "marks" the student collects)

```
total = SUM(points_ledger.points)
level = floor( sqrt(total / 50) )          # 50→L1, 200→L2, 450→L3, 800→L4 …
to_next = 50 * (level+1)^2 - total
```

Show as **"Builder Level N"** with a bar to the next level. Levels are cosmetic status — they never
gate content (content unlocks by EMI/week, not by points).

### Balloon-burst animation (spec)

- Trigger: streak milestone, week complete, badge earned.
- Visual: 12–20 balloons rise from the bottom, then **pop** in sequence with a confetti spray;
  a center badge/level card scales in. ~1.8s, auto-dismiss, `prefers-reduced-motion` respected.
- Implementation: pure CSS/Canvas, no library, no blocking. Reusable `celebrate(type, payload)`.

---

## 6. Streak rules

- A "streak day" = any points-earning activity that day (lesson step, workbook tick, video).
- `current` increments once/day; resets to 1 if a calendar day was missed.
- `longest` tracks the best run. Milestones at 3, 7, 14, 30 days fire balloon-burst + badge.
- (Optional later) one "freeze" per week so a single missed day doesn't nuke a long streak —
  matches the PDF's Sunday "rest/buffer" day.

---

## 7. How a student's week actually flows (ties learning + game + PDF)

```
Sat  Watch module video        → +15, streak day
     Open Lesson N (Brilliant)  → +10/step, +25 complete, confetti
Sun  Rest / buffer (freeze ok)
Mon  Workbook: guided build     → +10
Tue  Workbook: extend it        → +10
Wed  Workbook: make it yours     → +10  (reflect step feeds this)
Thu  Workbook: test & post       → +10
     "Bring to Friday" item      → +30, confetti
Fri  LIVE session (in person)    → week complete → +100, BALLOON BURST, level-up check
```

The dashboard makes this rhythm visible and rewarding, so the student walks into Friday with
something built — exactly what the cohort promises.

---

## 8. Quality bar for every lesson (checklist)

- [ ] One concept only.
- [ ] Learner acts before any explanation appears.
- [ ] Every wrong answer has a Socratic hint that does NOT give the answer.
- [ ] Difficulty ramps; the last step has no scaffolding.
- [ ] A "make it yours" step connects to the student's real agent.
- [ ] Ends in a mastery summary + a celebration.
- [ ] Works on a phone (the student may do it on the couch).
- [ ] `prefers-reduced-motion` respected.

---

*Owner: TrigunAI. Created 2026-06-19. This is the bible — every new lesson is reviewed against §8.*
