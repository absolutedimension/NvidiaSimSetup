# The Feedback System — Employee Training OS

> **Deepak's philosophy (the design axiom):** *the best learning system is the one with the fastest,
> highest-quality feedback.* So we don't bolt "feedback" on at the end — the whole training **is** a
> stack of feedback loops, fastest at the core, and every loop must end in a **specific action**, not
> a number on a screen. The mentor (Deepak) is wired in as the highest-signal loop, and the system's
> job is to tell him the **one thing to do** — not make him analyse data.

---

## 1. The principle: nested loops, fast core → slow shell

**Learning speed = feedback speed × feedback quality.** We run five loops at once, each a different
timescale. The tighter the loop, the more it's automated; the wider the loop, the more it's *you*.

| Loop | Cadence | What it measures | Who closes it | Output = ACTION |
|---|---|---|---|---|
| **L0 · Answer** | seconds | Each recall/apply answer: right? confident-but-wrong? explanation quality? | **Acharya** (instant) | Immediate correction + *why* |
| **L1 · Concept** | daily | Mastered? Decaying? | **Acharya** (SRS reschedules) | Re-teach / space it / advance |
| **L2 · Field-transfer** | per visit | Did he *do in the field* what he learned? What happened? | **Rohan self-report + Acharya check** | Match classroom ↔ reality; flag the gap |
| **L3 · Mentor** | weekly + triggered | Aggregate mastery + field adherence + red flags | **Deepak** (you) | One targeted coaching act |
| **L4 · Curriculum** | monthly | Which concepts don't transfer to real visits? | **System → Deepak** | Fix the bank (the OS learns) |

**Why this matters:** most "training" only has L0/L1 (quiz scores) and never closes L2 (did it change
behaviour?) or L4 (did the training itself work?). Those two are where a salesperson actually improves —
and they're exactly what your field logs + the tutor let us close.

---

## 2. Feedback is TWO-WAY (not the system lecturing Rohan)

- **System → Rohan:** instant answer correction · daily nudge · weekly summary · "you're confident-wrong here."
- **Rohan → System:** after each concept, a one-tap **"Got it / Still fuzzy"**; he can flag *"confused about X."*
- **Rohan → Field → System:** after each visit he reports *did I use it? what happened?* (2 taps + a line).
- **Field → Curriculum:** outcomes tell us which concepts are unclear or missing → L4.
- **Everyone → Mentor:** anything red surfaces to you, fast.

A trainee who can *give* feedback (rate clarity, flag confusion) learns faster than one who only receives it.

---

## 3. The mentor connection — "as mentor, what should I do?"

This is the heart of your ask. The system **converts all tracking into a prioritised mentor action list**,
so your job is to *act*, not to interpret. Three rules govern what reaches you:

**Rule 1 — Red Box first (from the `founder-reality-check` idea).**
The top mentor priority is always **confident-AND-wrong** — where Rohan was *sure* and got it *wrong*.
That's a blind spot, and blind spots don't fix themselves. The cockpit shows these in a red box, first.

**Rule 2 — Field-gap flags.**
If his last *N* logged visits skipped a **taught behaviour** (no discovery question, no follow-up, no
demo-link sent), that's a coaching moment — surfaced with the evidence.

**Rule 3 — One action, fully specified.**
Never "Rohan needs help with objections." Always: *"Send Rohan a 2-min voice note on the pricing
objection — he rated himself 9/10 sure and got it wrong twice. Script: …"* You just do it.

### Triggers that ping you SAME-DAY (via the Telegram group)
- Confident-wrong on a **customer-critical** concept (pricing · "why us" · an honesty rule).
- A field outcome that **contradicts training** (quoted cash, over-promised a guarantee, skipped discovery).
- A **pilot going cold** (no follow-up logged in X days).
- Rohan flags **"I'm confused about X."**
- A **milestone** (module mastered / certified-to-solo) — positive feedback is feedback too.

### The mentor's playbook — what to DO per signal
| Signal | Your move |
|---|---|
| **Confident-wrong** (customer-critical) | Correct it *personally* — voice note or a 5-min Maya role-play. Human correction sticks for false confidence; don't leave it to Acharya alone. |
| **Field-behaviour gap** | Give a **one-visit micro-goal**: "next visit, only nail discovery — nothing else." |
| **Cold pilot** | Co-plan the follow-up with him (what to send, when). |
| **Repeated struggle across trainees** | The *curriculum* is unclear → escalate to L4, fix the concept. |
| **A win** | Reinforce it out loud. Momentum is a feedback signal. |

**Your loop has feedback too:** every coaching act is logged, and next week the system checks *did the
red box close?* If your voice note didn't fix the pricing blind spot, it re-surfaces. Mentoring gets measured.

---

## 4. The UI — where it's required

Two surfaces. Everything else stays on WhatsApp (no UI needed).

### A) The Mentor Cockpit (web) — *your* one screen
Reuses the existing teacher-SWOT dashboard pattern (`teacher_gtm/assessment_demo/dashboard.html` + the
live `/report` SWOT), repurposed for staff → served as **`/mentor`** on the Gurukul VM. Per trainee:
1. **Status line** — week, % curriculum mastered, certified-to-solo?
2. **🔴 THE RED BOX** — confident-wrong concepts, top and unmissable.
3. **Knowledge heatmap** — concept × mastery (green/amber/red) + decay markers.
4. **Field-transfer panel** — taught behaviours vs field-observed (from his logs) = adherence %.
5. **Role-play scores** (Maya).
6. **→ THIS WEEK'S MENTOR ACTIONS** — the 1–3 specific things for you, prioritised. **This is the hero of the page.**
7. **Trainee switcher** — Rohan today; the next hire tomorrow (pluggable).

### B) The daily Mentor Pulse (Telegram) — *no UI, one line*
Every morning in the group:
> *"Rohan · Day 6 · Module 1 done (4/6 mastered) · 🔴 confident-wrong on pricing. Your move: 2-min voice note on pricing (script attached)."*
One glance, one action. The cockpit is for when you want the full picture; the pulse is for daily flow.

### C) Rohan's own view (light, optional)
Mostly WhatsApp. Optionally a simple progress card (reuse the student `/report`) so he sees his own
mastery + streak — **self-feedback motivates**, and it lets him self-correct before you even step in.

---

## 5. Metrics that matter (feedback on the feedback system itself)

Per your axiom, we optimise for loop *speed*, not activity:
- **Feedback latency** — time from a gap appearing → a correction landing. Drive this DOWN; it's the whole philosophy.
- **Field-transfer rate** — % of taught behaviours actually observed in visits (L2 health).
- **Red-box close time** — confident-wrong → corrected → re-verified.
- **Business correlation** — does higher mastery track with better visit outcomes (discovery done, pilots live)? If not, fix the curriculum (L4).

---

## 6. Data sources (so this is buildable, not a fantasy)

| Loop | Data comes from | Already exists? |
|---|---|---|
| L0/L1 knowledge | Acharya mastery + SRS on the Gurukul VM | ✅ (the tutor tracks it) |
| L2 field | Rohan's field log / `08_PAIN_POINT_LOG` / visit reports | ✅ (he already logs) |
| Role-play | Maya calls + `trigunai-sales-rehearsal` scores | ✅ skill exists |
| Cockpit UI | reuse `assessment_demo/dashboard.html` → `/mentor` | ⚙️ adapt existing |
| Mentor pulse | Telegram group (Maya already posts there) + WhatsApp | ✅ channel exists |

**The one honest gap:** L2 (field-transfer) needs a light structured **post-visit report** from Rohan
(2 taps: *"used discovery? y/n · demo-link sent? y/n"* + one line + outcome) so the system can compare
*learned* vs *done*. That's the single new input to design — everything else is wiring existing streams.

---

## 7. Build order (when we build)

1. **Post-visit micro-report** (the L2 input) — 4 quick fields Rohan sends after each visit (WhatsApp or his "start my day" flow).
2. **Mentor Cockpit `/mentor`** — adapt the SWOT dashboard: red box + heatmap + field-transfer + **mentor actions**.
3. **Daily Mentor Pulse** — the 1-line Telegram push with the day's single action.
4. **Trigger rules** — the same-day pings (confident-wrong on critical concept, cash quoted, cold pilot).
5. **Close the mentor loop** — log coaching acts, re-check the red box next week.

See [[project-employee-training-os]] · curriculum in `FIELD_SALES_CURRICULUM.md` · tutor infra
[[project-gurukul-vm]] · role-play [[project-sales-rehearsal-coach]] · the mentor-cockpit UI reuses the
Acharya assessment SWOT dashboard.
