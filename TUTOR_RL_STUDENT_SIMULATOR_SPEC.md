# Student Simulator — the RL Environment for a Trainable AI Tutor

> **Purpose.** Spec the *environment* a tutor policy is trained against. The tutor is the agent;
> the simulated student is the world. This is a sim-to-real RL problem — the same discipline TrigunAI
> already runs for the drone (Isaac Sim → real). The simulator's fidelity is the ceiling on everything.
>
> **One rule above all:** real students are the **eval**, never the **training set**. They are the
> "eye outside the optimizer" — the same role the VLM critic plays in the drone pipeline (`CLAUDE.md §17.9`).
>
> Status: design v0 (2026-06-29). Owner: TrigunAI. Companion to the Acharya tutor (`[[project-gurukul-vm]]`)
> and the LMS lessons (`[[project-lms-lessons]]`).

---

## 0. The map (drone analogy — read this first)

| Drone RL (we already do this) | Tutor RL (this spec) |
|---|---|
| Isaac Sim physics | **Student simulator** (this doc) |
| PPO/AMP policy | **Tutor policy** (the agent) |
| sensor obs (partial) | dialogue + responses (partial — true mastery is hidden) |
| motor command | tutoring move (ask / hint / explain / practice / review) |
| reward = reached goal | reward = **learning gain** on held-out quiz |
| domain randomization → sim2real | randomize persona/misconceptions → student2student |
| VLM critic outside optimizer | **real-cohort eval** outside optimizer |

If you can build a faithful student environment, the rest is machinery you already own (skrl / rl_games / A10G).

---

## 1. Two-layer student (the key design choice)

A real student utterance is messy NL; a *reward* needs clean numbers. So split the student into two layers — exactly how Isaac separates **physics state** from **rendered pixels**:

```
┌─────────────────────────────────────────────────────────┐
│  LAYER A — LATENT DYNAMICS (numbers, cheap, drives reward)│
│  per-skill mastery vector, misconceptions, affect,        │
│  learning rate, forgetting rate.  Updated by a learning-  │
│  science transition rule on every tutor move.             │
└───────────────▲───────────────────────┬──────────────────┘
                │ conditions             │ updates
┌───────────────┴───────────────────────▼──────────────────┐
│  LAYER B — SURFACE (LLM, realistic, what the tutor sees)  │
│  Generates the student's actual words, errors, questions, │
│  "I don't get it", guesses — conditioned on Layer A.      │
└──────────────────────────────────────────────────────────┘
```

- **Layer A** is the source of truth for reward and for whether learning happened. Deterministic-ish, fast, fully introspectable.
- **Layer B** makes the dialogue realistic so the tutor faces real linguistic ambiguity (partial observability). The tutor **never** sees Layer A — it must *infer* mastery from Layer B (implicit knowledge tracing).

This separation is what makes the reward computable AND the dialogue realistic. Don't collapse them.

---

## 2. Latent state schema (Layer A)

A single simulated student instance:

```json
{
  "student_id": "sim_000142",
  "course_id": "agentic-systems",
  "skills": {                         // K concepts in the course's knowledge graph
    "what-is-an-agent":      {"mastery": 0.20, "last_seen_step": 0, "reps": 0},
    "tool-calling":          {"mastery": 0.05, "last_seen_step": 0, "reps": 0},
    "memory-and-context":    {"mastery": 0.00, "last_seen_step": 0, "reps": 0}
    // ... one entry per skill node
  },
  "misconceptions": ["agent-eq-chatbot", "tools-are-magic"],   // active subset of the bank (§3)
  "affect": {"confidence": 0.4, "frustration": 0.1, "engagement": 0.7, "fatigue": 0.0},
  "traits": {                         // persona — fixed for the episode, sampled at reset
    "learning_rate": 0.18,            // α: how fast mastery rises on good practice
    "forgetting_rate": 0.06,          // λ: Ebbinghaus decay per step of disuse
    "transfer": 0.3,                  // spillover of mastery to neighbor skills in the graph
    "help_seeking": 0.5,              // P(asks for help when stuck) vs. silent/guesses
    "guess_rate": 0.2,                // P(guesses) on low mastery
    "verbosity": 0.4,                 // surface-layer style
    "grit": 0.6,                      // tolerance before disengaging under frustration
    "prior_knowledge": 0.25           // global offset to starting mastery
  },
  "step": 0
}
```

`mastery ∈ [0,1]` is BKT-style "P(knows skill)". The **knowledge graph** (skills + prerequisite edges) comes from the existing LMS course journey (`seed.py`) — reuse it, don't reinvent.

---

## 3. Misconception bank (the part that MUST be grounded in real data)

The simulator can only contain mistakes you put in it. Invented misconceptions → a tutor for problems nobody has. Source these from (a) learning-science literature per subject, then (b) **calibrate against real Acharya logs** once the flywheel runs.

```json
{
  "id": "agent-eq-chatbot",
  "skill": "what-is-an-agent",
  "description": "Believes an 'agent' is just a chatbot with a personality.",
  "wrong_model": "If it talks back, it's an agent. Tools/loops/goals don't matter.",
  "trigger_signs": ["calls any LLM call an agent", "ignores the action loop"],
  "repair_difficulty": 0.6,          // how hard to dislodge (0 easy … 1 sticky)
  "repaired_by": ["contrastive-example", "force-define-loop", "counterexample-failure"],
  "reinforced_by": ["telling-the-answer-without-recall", "vague-praise"]
}
```

Key property: a misconception is **repaired** by good moves and **reinforced** by bad ones (e.g. giving the answer without a recall attempt). This is what lets RL discover *Socratic* behavior instead of *answer-dumping* — the reward structure has to make answer-dumping backfire.

---

## 4. Action space (the tutor's moves)

A tutoring move = a **discrete move type** + **NL content** (Layer B reads the content; Layer A reacts to the type + difficulty + target skill).

| Move type | Params | Intended pedagogy |
|---|---|---|
| `diagnose` | target skill | probe mastery (reduce tutor's uncertainty) |
| `ask_recall` | skill, difficulty | retrieval practice (the testing effect) |
| `worked_example` | skill, fade_level∈{full,partial,solo} | scaffolding → fading |
| `hint` | skill, level∈{1,2,3} | minimal nudge before telling |
| `explain` | skill, depth | direct instruction (use sparingly) |
| `practice` | skill, difficulty | apply at the edge of ability (desirable difficulty) |
| `review` | old skill | spaced repetition pull-back |
| `encourage` | — | affect repair |
| `assess` | (terminal) | trigger the held-out mastery quiz |

A learned policy chooses *which move, which skill, what difficulty, when to review, when to stop*. That sequencing decision is the thing RL adds over a fixed script.

---

## 5. Transition model (how the student updates each step)

On tutor move `a` against student state `s`:

1. **Layer B generates the student response** (LLM, conditioned on the latent state + persona + dialogue history). Produces words, an answer (correct/incorrect/partial), maybe a question or a give-up.
2. **Layer A updates** with a learning-science rule:
   - **On a genuine recall/practice attempt** on skill `k`:
     `mastery_k += α · desirable_difficulty(d, mastery_k) · spacing_bonus(steps_since_last_k)`
     — gain is *largest* when the item is at the edge of ability and well-spaced (encodes retrieval practice + spacing + desirable difficulty).
   - **Telling the answer with no recall attempt:** tiny/zero mastery gain, and any active misconception on `k` gets `reinforced` (penalized downstream).
   - **Misconception repair:** if move ∈ `repaired_by`, draw repair with P ∝ `(1 - repair_difficulty)`; on success remove it and unlock real mastery growth.
   - **Forgetting (every step):** `mastery_k *= exp(-λ · steps_since_last_seen_k)` (Ebbinghaus). Spacing is *valuable precisely because* this decay exists.
   - **Transfer:** a fraction `transfer` of gain spills to graph-neighbor skills.
   - **Affect update:** repeated too-hard → frustration↑, engagement↓; too-easy → engagement↓ (boredom); success at right difficulty → confidence↑. If `frustration > grit` → student **disengages** (episode quality collapses — a real failure mode the tutor must avoid).
3. **Advance `step`**, append to dialogue history (the observation).

Start every parameter from literature priors; **calibrate α, λ, repair_difficulty against real cohort data** as it accumulates. Wrong dynamics = confident sim, weak reality.

---

## 6. Reward (where it lives or dies)

Compute reward from **Layer A**, not from the student saying "thanks."

**Terminal — the real signal:**
```
learning_gain = mean(mastery_post) − mean(mastery_pre)        # over the session's target skills
```
measured by a **held-out mastery quiz** whose items are **disjoint from everything taught** → kills teaching-to-the-test (the tutor's version of reward-hacking).

**Retention (anti-cramming):** re-quiz after simulating elapsed time (apply forgetting), reward the *retained* gain. A tutor that only inflates immediate scores loses here — this is the analogue of your "reward went up but the flight got worse" guard.

**Process shaping (small, dense, keeps RL stable):**
```
+ misconceptions_repaired
+ socratic_ratio            (recall/hint moves before any 'explain')
+ efficiency                (gain per turn)
+ engagement_kept_healthy
− answer_dumping            (explain/answer with no prior recall attempt)
− cognitive_overload        (too many new ideas/turn)
− caused_disengagement      (frustration > grit)
```

Total: `R = w_gain·learning_gain + w_ret·retained_gain + Σ w_i·process_i`. Keep `w_gain` dominant; process terms only shape, never override real learning.

---

## 7. Environment contract (gym-like — plugs into your stack)

```python
class StudentEnv:
    def reset(self) -> Obs:
        # sample a NEW student from the population distribution (§8) — domain randomization
        # returns initial observation (course intro + empty dialogue); latent state hidden
    def step(self, action: TutorMove) -> tuple[Obs, float, bool, dict]:
        # 1. Layer B: student responds   2. Layer A: update mastery/affect/misconceptions
        # 3. compute shaped reward        4. done if assess called / max_turns / disengaged
        # obs = full dialogue history + last student response (NOT latent state)
        # info = {latent_state, mastery_vector, ...}  # for logging/eval ONLY, never fed to policy
```

- **Observation** = dialogue history + latest student utterance (+ optional running tutor-estimated mastery). Partial — true mastery is hidden, exactly like drone sensors vs. full physics state.
- **Episode** = one tutoring session (or a multi-session arc with between-session forgetting for the retention reward).
- Batch thousands of envs on the A10G the way you batch 256–4096 drone envs (watch the same RAM/throughput limits from `CLAUDE.md §19.8`).

---

## 8. Domain randomization (your sim-to-real lever, reused verbatim)

At every `reset`, sample the student from a *distribution*, not a fixed persona:
- `traits` (α, λ, grit, help_seeking, prior_knowledge…) from calibrated ranges,
- a random **subset of misconceptions** weighted by real prevalence,
- random starting mastery profile (true beginner ↔ partial knowledge ↔ has-misconceptions).

This is identical to randomizing mass/friction in robotics so the policy transfers. A tutor trained against *one* student overfits to it; trained against a *diverse population* it generalizes to real humans. Coverage of the population = your generalization.

---

## 9. Anti-reward-hacking guardrails (all four are mandatory)

1. **Freeze the student sim during tutor training.** Do **not** co-train tutor + student — they collude (GAN/self-play collapse). Improve the sim in separate, deliberate passes.
2. **Held-out quiz items** disjoint from taught items (no teaching-to-the-test).
3. **Retention re-quiz** after simulated forgetting (no cramming exploit).
4. **Real-cohort eval is the only ground truth.** If sim-reward rises but real-cohort learning gain doesn't → the *simulator* is lying. Fix the simulator, not the tutor. (This is the VLM-critic principle.)

---

## 10. Build order (don't skip — each stage de-risks the next)

| Stage | Deliverable | Why |
|---|---|---|
| **0** | Knowledge graph + misconception bank for **one** course (reuse LMS `seed.py` journey) | Can't simulate what you can't enumerate |
| **1** | Layer A transition model + held-out quiz, **no LLM yet** — drive it with scripted "tutor moves" and unit-test that good pedagogy → higher gain than answer-dumping | Validates the *physics* before adding the renderer |
| **2** | Layer B (LLM student) on top, conditioned on Layer A | Realistic dialogue / partial observability |
| **3** | **Synthetic SFT first** — expert-teacher LLM tutors the sim → fine-tune Acharya to imitate. *Stable, no RL, ~70% of the gain* | Cheapest big win; cold-start for RL |
| **4** | RL for the **sequencing decision only**, against the frozen population | The part SFT can't capture |
| **5** | Calibrate sim params on real Acharya logs; gate every model on the real-cohort held-out eval | Close the sim-to-real loop |

**Highest-leverage first artifact after this spec:** Stage 0+1 for the `agentic-systems` course — the misconception bank + the numeric transition model, validated by the "good pedagogy beats answer-dumping" unit test. That's the equivalent of getting the drone env-config right before any training run.

---

## 11. Honest ceiling

- The student simulator is **~80% of the work**; the RL is the last 20%.
- Synthetic SFT (Stage 3) beats jumping straight to RL and is far more stable.
- Published adaptive-sequencing gains are *real but bounded* (a fraction of Bloom's 2-sigma); **most** of the 2-sigma comes from the *tutoring mode itself* (Socratic + mastery + immediate feedback) — i.e. the prompt, which is free and deployable today.
- This program is a genuine **moat for TrigunAI specifically**: almost no edu-AI team is a sim-to-real RL shop with a GPU pipeline *and* a live cohort to validate against. You have all three.

---

*Next concrete step on request: generate the Stage-0 knowledge graph + misconception bank for `agentic-systems` from the existing LMS course journey, and the Stage-1 numeric transition model with the "good-pedagogy-beats-answer-dumping" unit test.*
