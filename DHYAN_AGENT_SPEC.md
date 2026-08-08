# Dhyan — the Focus & Deep-Understanding agent for Acharya (evidence-based spec)

> **ध्यान (dhyāna) = focused, deep attention.** A plug-in agent for Acharya that makes a student's
> study time go *deep* instead of shallow, catches the illusion of understanding, and structures the
> focus loop — on WhatsApp, in Hindi/English, using Acharya's existing per-student learner model.
>
> **Evidence status (honest):** grounded in a deep-research pass over primary sources (Dunlosky 2013,
> VanLehn 2011, Cepeda 2006, Agarwal 2021, Angrist/Nature, MCII/WOOP meta, etc.). The adversarial
> 3-vote verification stage was cut off by a session limit, so the specific *numbers* below are
> sourced-but-not-yet-adversarially-verified — most are well-established findings I corroborate from
> known literature; re-run the verify pass before quoting exact effect sizes externally.

---

## 0. THE single most important finding (this decides the whole design)

**VanLehn (2011) meta-analysis:** human tutoring ≈ **d 0.79** over no tutoring; **step-based ITS ≈ d
0.76** (nearly as good as a human tutor); **answer-based CAI ≈ d 0.31** (just checking final
answers). The gap between 0.76 and 0.31 is the entire ballgame.

→ **Acharya must engage step-by-step — ask at each step of reasoning, not just check the final
answer.** This is *exactly* the "won't let you fake-understand" wedge, and it's the difference
between a real tutor and a glorified answer-key. Every Dhyan behavior below is a way to force
step-level engagement.

Second-biggest: **feedback is not optional.** Agarwal 2021 (50 classroom experiments, n=5374):
retrieval practice *without* feedback → mostly small effects; *with* immediate feedback → small-to-
large. A quiz that doesn't explain the answer is half-wasted.

---

## 1. The evidence, per problem (what's proven · what's myth · effect size)

### Problem 2 — Shallow processing → **deep processing** (STRONGEST for AI; build first)
- **Dunlosky et al. 2013 (PSPI monograph):** of 10 study techniques, only **practice testing** and
  **distributed practice** rate *high utility*. **Rereading, highlighting, summarizing = low utility**
  — and rereading/highlighting are what students actually do most. Rereading is beaten head-to-head by
  elaborative interrogation, self-explanation, and practice testing.
- **Testing effect / generation:** retrieving (generating) an answer beats re-studying; **free recall
  > multiple-choice recognition** for retention. → Acharya's questions should demand recall/explanation,
  not just "pick A/B/C/D".
- **Spacing (Cepeda 2006, 254 studies, 14k+ people):** spaced ≈ 47% vs massed ≈ 37% recall. (Acharya's
  SRS queue already does this — Dhyan extends it from *facts* to *understanding*.)

### Problem 3 — Illusion of understanding → **metacognitive calibration** (build first)
- **Dunning-Kruger in study:** low performers systematically *overestimate* what they know. Critically,
  **score-only feedback does NOT fix it** — students saw their practice-test scores and right/wrong
  answers and *still* stayed overconfident (PMC8442020).
- Practice testing can even *worsen* calibration at the extremes if it's just scores.
- **What fixes it:** explicit instruction on how to *use* feedback, richer *explanatory* feedback,
  metacognitive training, and **reaching miscalibrated students early** (before the first big test).
- → The gold data for Acharya: **where the student *feels* confident but *isn't*** — the confidence-
  vs-correctness gap. This is the single most valuable signal to surface to student *and* teacher.

### Problem 4 — No deep-work structure → **session structuring** (build first, but softly)
- **Mixed evidence, important nuance.** One RCT (MDPI 2025): *imposing* rigid Pomodoro → faster fatigue
  and faster motivation decline than letting students self-regulate breaks, with **no productivity
  difference**. Another review (3 RCTs, n=87): structured intervals → ~20% lower fatigue + better
  distractibility. AI-enhanced Pomodoro apps → +10–18% engagement.
- **Verdict:** session structuring helps *self-rated focus & fatigue* — **NOT proven for retention** —
  and **forcing a rigid timer can backfire.** → Acharya should *offer* structure and let the student
  set the rhythm, never nag a fixed 25-min block.

### Problem 1 — Attention / distraction (build LATER; weakest for a chat agent + myth-heavy)
- **Myth alert:** the famous "your phone drains your brain just by being present" (Ward 2017) **failed a
  pre-registered replication** — phone location produced no effect on working memory/attention. Don't
  build features on "put your phone in another room."
- **What's real:** *active* media-multitasking correlates with worse achievement (meta-analysis) — the
  harm is *using* the phone mid-study, not its mere presence. → The honest lever is **single-tasking**,
  not phone-banishment.
- A WhatsApp agent literally *lives on the distracting device* — so Acharya can't police attention; it
  can only make the on-phone time productive and coach single-tasking. (This is why #1 is Phase 2.)

### Problem 5 — Motivation / self-regulation (build LATER; modest effects, backfire risk)
- **Implementation intentions (Gollwitzer & Sheeran): d ≈ 0.65** — "*If it's 7pm, then I will do 20
  min of organic chemistry*" plans genuinely work. **WOOP/MCII meta: g ≈ 0.336** (21 studies, 15,907).
- **Procrastination treatments overall: only g ≈ 0.34 (small)** — light-touch coaching = modest. **Do
  not overpromise "we'll fix procrastination."**
- **Nudges → intrinsic motivation (β ≈ 0.211)** when well-designed. But **SDT warning:** extrinsic
  rewards/streaks can *crowd out* intrinsic motivation if overdone.
- **Gaming-the-system (Baker):** students who exploit hints instead of thinking **learn less** — a
  direct caution against Acharya giving answers too easily.

### Cross-cutting myths to NOT build on
- **Learning styles** (visual/auditory tailoring) — **no scientific basis** (Pashler et al. 2009). Never
  build style-matching.
- **Focus audio (binaural/isochronic):** a meta (22 studies) found binaural beats **g ≈ 0.45** on
  cognition/anxiety — *not* pure myth, but modest and heterogeneous, and mostly about relaxation, not
  learning. → We can offer our focus bed as *"may help you settle in"* — **never** *"proven to boost
  learning."* (Honest claim protects the brand.)

### The delivery evidence (why WhatsApp can work in India)
- **Angrist et al. (Nature Human Behaviour):** weekly **SMS + phone-call** tutoring in a low-resource
  setting → **0.16–0.29 SD** learning gains at **$2–14/student**. Phone-based light-touch tutoring
  *works* — direct validation for Acharya's channel.
- **Chatbot nudges** raised the likelihood of a B-or-higher by ~8 percentage points (Fordham).

---

## 2. The phased architecture

**Phase 1 (build now): 2 + 3 + 4** — deep processing, calibration, soft session structure. These are
where a conversational agent is strongest and where Acharya's learner model already gives us the hooks.
**Phase 2 (later): 1 + 5** — attention coaching, motivation/habit — weaker for a chat agent, modest
effect sizes, real backfire risks; add once Phase 1 shows retention gains.

### PHASE 1 — the three behaviors to build

**① Deep-Processing Probe (problem 2)** — *"explain it, don't just nod."*
- **Trigger:** student finishes a topic / says "samajh gaya" / after any Acharya explanation.
- **Behavior (step-based, per VanLehn):** don't accept "got it." Run a short ladder — *explain it back
  in your own words* (Feynman) → *predict/apply to a NEW case* → *why does that work?* (one "why"
  deeper). Free-recall, not multiple-choice. **Always give explanatory feedback**, not just right/wrong.
- **Guardrail:** if the student is stuck, scaffold with a *hint that requires a step*, never the full
  answer (anti-gaming).

**② Calibration Check (problem 3)** — *"you think you know — let's see."*
- **Trigger:** before a topic is marked `solid`; before a scheduled test; on the SRS due-item.
- **Behavior:** ask the recall question **+ a confidence rating** ("kitna confident ho — 1 se 5?").
  Compute the **confidence-vs-correct gap.** Overconfident+wrong = the priority intervention. Give
  *explanatory* feedback (score-only doesn't work) and a one-line metacognitive nudge ("aapko laga aata
  hai, par yahaan gap hai — isliye recall practice zaroori hai").
- **Output to teacher (extends the teacher):** the pre-class brief already exists — add a
  **"confidently wrong" list** (the highest-value teacher signal there is). Reach miscalibrated students
  *early*, before the test.

**③ Deep-Work Session (problem 4)** — *offered, not imposed.*
- **Trigger:** student says "padhne baithe" / "focus session" / a scheduled study window.
- **Behavior:** help them set an intention ("aaj kaunsa ek topic, kitne minute?"), start a **student-
  chosen** block (not a forced 25 min), one mid-check, and **end with a recall, not a timer bell** — the
  session is proven by what they can retrieve, not by time elapsed. Optional focus-audio ("settle in"
  framing only).
- **Guardrail:** no rigid nagging; let them self-regulate the rhythm (forcing it backfires).

### PHASE 2 — add after Phase 1 proves out

**④ Single-Tasking / Attention coach (problem 1):** coach *single-tasking* (not phone-banishment —
that's a myth). Gentle "ek kaam pe raho" check-ins during a session; notice each student's actual
focus windows from their data and suggest study times that fit. Low-frequency (avoid notification
blindness).

**⑤ Intention & Habit coach (problem 5):** implementation intentions ("**if 7pm → then 20 min
Physics**", d≈0.65) + WOOP (wish/outcome/obstacle/plan). Streaks **only** tied to the *behavior*
(showed up + did a deep-recall), framed as progress not prize — watch the SDT crowding-out risk.
Honest scope: light-touch, modest effect — never sold as a procrastination cure.

---

## 3. Failure modes to design against (from the research)
- **Answer-farming / gaming the hint** → students learn *less*. Hints must cost a step of thinking.
- **Nagging fatigue & notification blindness** → keep proactive pings rare and high-value; never a fixed
  drumbeat. (Angrist worked at *weekly* cadence, not hourly.)
- **Extrinsic crowding-out (SDT)** → don't over-gamify; tie any streak to the learning behavior, not points.
- **Rigid timers backfire** → offer structure, let the student self-regulate.
- **Score-only feedback doesn't fix overconfidence** → always explanatory feedback + metacognitive framing.
- **Overclaiming** → "deeper understanding & better recall," never "fixes focus" / "guarantees marks" /
  "focus music proven to boost learning." Overclaim burns teacher trust fastest.

## 4. Measurable outcomes (so we know it works)
- **Calibration gap** (confidence-vs-correct) shrinks over weeks — the headline metric.
- **`shaky → solid` promotions** per week (from the learner model) rise vs baseline.
- **Free-recall accuracy on spaced items** (retention) rises — the one that actually predicts exam scores.
- **Session completion with an end-recall** (not just time logged).
- **Teacher-facing:** # of "confidently wrong" students caught *before* a test.
- Guard against vanity metrics (messages sent, streak length) — they don't equal learning.

## 5. Indian coaching / exam-prep context
- **WhatsApp-first, low-friction** is validated (Angrist: SMS+call tutoring works cheaply at scale).
- **Hindi/English** — run the probes in the student's language; keep tech/exam terms as-is.
- **Parental involvement** is a real lever here — a *weekly* (not daily) parent note ("your child is
  practising, here's one strength + one gap") fits the market and the teacher's brand. Low-frequency.
- **Exam-prep is high-stakes + high-anxiety** — calibration ("you're confidently wrong on X") must be
  framed kindly, as help before the test, not judgment.

## 6. Validation plan (before we fully build it)
This is a strong hypothesis — validate demand + effect before the full build:
1. **Field demand:** does Rohan hear *"students can't focus / don't understand deeply / think they know
   but fail the test"* **3+ times** in Patna? (Add focus/depth questions to his research guide.)
2. **Existing data:** does Acharya's **learning-loop instrumentation** (wrong-attempts, hint-reliance,
   the confidence gap) confirm the illusion-of-understanding pattern in real users?
3. **Cheapest test:** ship **behavior ① (Deep-Processing Probe)** alone to one pilot batch, measure the
   calibration gap + free-recall over 3–4 weeks vs a non-Dhyan batch. If retention moves, build the rest.

## 7. Sources (primary, from the research pass — re-verify numbers before external quoting)
- Dunlosky et al. 2013, *Psychological Science in the Public Interest* — technique utility ranking
- VanLehn 2011 — human vs ITS vs CAI meta (step-based d≈0.76) · Cepeda et al. 2006 — spacing meta
- Agarwal et al. 2021, *Educational Psychology Review* — 50 classroom retrieval experiments
- PMC8442020 — practice-test feedback & Dunning-Kruger calibration
- Ruiz Pardo & Minda (Acta Psychologica) — "brain drain" replication failure
- Pashler et al. 2009 — learning-styles myth · binaural-beats meta (PubMed 30073406, g≈0.45)
- MDPI Behav. Sci. 2025 & BMC Med Educ 2025 — Pomodoro RCT evidence (mixed)
- MCII/WOOP meta (PMC8149892, g≈0.336); Gollwitzer & Sheeran implementation intentions (d≈0.65)
- procrastination-treatment meta (g≈0.34); Baker — gaming-the-system & learning
- Angrist et al., *Nature Human Behaviour* — SMS+phone tutoring 0.16–0.29 SD; Fordham — chatbot nudges

*Created 2026-07-17. Owner: Deepak. Feeds ACHARYA_FEATURES.md §C roadmap. Companion: AI_GURUKUL_DESIGN.md
(the learning-science engine Acharya already runs on). Re-run the deep-research verify pass to confirm
effect sizes before any external/marketing use.*
