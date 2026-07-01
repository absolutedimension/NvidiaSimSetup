# tutor_rl — an RL-trained AI tutor, end to end

A runnable implementation of the plan in
[`../TUTOR_RL_STUDENT_SIMULATOR_SPEC.md`](../TUTOR_RL_STUDENT_SIMULATOR_SPEC.md):
a **student simulator** (the RL environment) + a **tutor policy trained by RL** to
sequence teaching moves for maximum *retained learning gain* — grounded in the real
`agentic-systems` course (the 10 LMS lessons).

> Thesis: a teaching system gets more powerful when the **sequencing** is *learned*
> against a faithful student model — not hand-scripted. This package demonstrates
> that an RL tutor beats random/answer-dumping/fixed-order baselines on unseen
> simulated students, and ships the path to push the discovered policy into the
> live Acharya tutor via synthetic SFT.

## Why this maps to TrigunAI's edge
It's a **sim-to-real RL** problem — the same discipline as the drone pipeline
(`../CLAUDE.md §17`). The student simulator is the "physics"; domain randomization
over student personas is the sim-to-real lever; **real students are the eval, never
the training set** (the VLM-critic principle).

## Files
| File | Role |
|---|---|
| `knowledge.py` | Stage 0 — skill graph + prereqs + **misconception bank** for `agentic-systems` |
| `student_env.py` | Stage 1 — the **student simulator** (Layer A latent dynamics). Gym-like `reset()/step()` |
| `tutors.py` | Baselines (random / answer-dump / fixed-order / Socratic heuristic) + the learnable `LinearPolicy` |
| `test_physics.py` | **Validation gate** — proves good pedagogy beats answer-dumping *before* any training |
| `train.py` | Stage 4 — REINFORCE trainer (pure numpy, no GPU). Saves `policy.npy` |
| `evaluate.py` | Held-out eval: RL tutor vs all baselines on unseen students |
| `llm_student.py` | Layer B — realistic LLM student surface via the EC2 LiteLLM proxy |
| `gen_sft_data.py` | Stage 3 — distill the RL sequencing into an SFT corpus for Acharya |

## Run it
```bash
cd tutor_rl
python3 test_physics.py        # 1. validate the simulator's physics (must PASS)
python3 train.py               # 2. train the RL tutor -> policy.npy
python3 evaluate.py            # 3. RL tutor vs baselines on held-out students
python3 evaluate.py --load policy.npy   # eval a saved policy without retraining
```
Only dependency: `numpy`. Everything above runs on a laptop.

### Layer B + SFT corpus (needs the LiteLLM proxy)
```bash
# tunnel the EC2 proxy to localhost (IP from AWS console; see ../CLAUDE.md §2)
ssh -i ~/.ssh/trigunai_key.pem -L 4000:localhost:4000 ubuntu@$EC2_IP
python3 llm_student.py                 # see a latent student talk
python3 gen_sft_data.py --episodes 20  # -> sft_corpus.jsonl  (dialogue -> ideal move)
```

## What the model is
- **State (hidden):** per-skill mastery, active misconceptions, affect, learning/forgetting traits.
- **Observation (tutor sees):** BKT-style belief from observed responses + staleness + affect — *not* the latent state (partial observability).
- **Action:** `(move, skill)` over `{ask_recall, worked_example, hint, explain, practice, review, assess}`.
- **Reward:** dense mastery gain + misconception repair − answer-dumping, plus a
  **terminal retained-learning-gain** on a held-out quiz (disjoint from teaching →
  no teaching-to-the-test; consolidation makes spacing/review matter for retention).

## Results (first end-to-end run, 300 held-out unseen students)

| tutor | retained gain | immediate | misc left | answer-dump |
|---|---|---|---|---|
| random | 0.074 | 0.112 | 1.87 | 25% |
| answer_dump | −0.016 | 0.000 | 2.70 | 91% |
| fixed_order | 0.024 | 0.056 | 1.64 | 0% |
| **heuristic** (hand-built Socratic) | **0.128** | 0.161 | 1.68 | 0% |
| **RL_tutor** | 0.107 | 0.144 | **1.02** (best) | 0% |

Honest read: the RL policy learned real pedagogy from scratch — **zero answer-dumping**
and, after valuing misconception repair in the reward, it **repairs more misconceptions
than any other tutor** (misc-left 2.70→1.02). It is **competitive** with but does **not
beat** the strong hand-built heuristic on retained gain (−16%) — expected for a tiny
*linear* policy vs. a heuristic that hard-codes prereq ordering + spaced review.
A reward-shaping lesson showed up exactly as the spec predicted: v1 maximized the
dominant reward term and *neglected* repair (misc-left 2.70); raising the repair reward
fixed it. To surpass the heuristic: (a) MLP+PPO policy on the A10G, (b) calibrate the
sim on real Acharya logs. **Not tuned further on purpose** — chasing a win on an
uncalibrated simulator proves nothing.

## Honest limits (read before trusting a number)
- The simulator's parameters are **literature priors, not yet calibrated** to real
  Acharya logs. The *ordering* of tutors is meaningful; absolute gains are not real
  learning gains until Stage 5 calibration.
- The policy is a small linear model — enough to show learned sequencing wins;
  swap in an MLP/PPO (torch on the A10G) for the production version.
- **Most** of the famous Bloom 2-sigma comes from the tutoring *mode* (Socratic +
  mastery + immediate feedback) — i.e. the Acharya prompt — which is free today.
  The learned sequencer is the *additional* margin on top.

## Stage 5 — calibration flywheel (real Acharya data)
Closes the sim-to-real loop. **Read-only + privacy-safe**: an aggregator runs on the
Gurukul VM and emits ONLY de-identified statistics (concept-state counts, misconception
frequencies, SRS Leitner-box distribution) — no names, no transcripts leave the box.

```bash
bash calibration/refresh.sh    # pull aggregate from VM + recalibrate -> calibrated_priors.json
```
- `calibration/aggregate_profiles.mjs` — runs on the VM, reads `~/.openclaw/students/*.json`, prints de-identified aggregate.
- `calibrate.py` — fits priors **with data-sufficiency gates** (refuses a prior it can't support); writes `calibrated_priors.json`.
- `student_env.py` auto-loads `calibrated_priors.json` if present (concept difficulty, SRS-box→forgetting), else literature priors.

**First run (2026-06-29, honest):** 7 students with data → **33 real misconception phrases
captured** (Big-O + music-course — richer & different from the hand-authored agentic priors,
proving the premise). Concept-difficulty + retention still thin.

**Capture-density investigation (the real diagnosis):** the bridge's capture mechanism is
actually *well-built* — code owns mastery/SRS, the model only proposes "shaky" marks, "solid"
is granted only by deterministic recall grading, and it already appends an event stream to
`~/.openclaw/gurukul/events.jsonl`. Two genuine gaps, neither a code bug:
1. **Event logging just went live** (bridge restarted 2026-06-29 13:26 UTC with the `logEvent`
   code) — `events.jsonl` fills from the next student exchange. The aggregator now consumes it
   (recall verdicts → real per-concept difficulty), preferring it over snapshots.
2. **SRS boxes never advance (all 0, even the streak-60 student)** — the daily recall→grade→box
   loop never completes, almost certainly because the `gurukul_recall` Meta template isn't
   approved. No template → no recall ping → no graded recall → no durable "solid" → no retention
   signal. **This is the one operational unblock** (Meta console), and it improves the live
   product (students actually get spaced recall), not just calibration.

So capture density is mostly fixed by today's restart; the retention signal is gated on the
SRS template approval + cohort growth.

## Build order (where this sits)
0 ✅ knowledge graph + misconception bank → 1 ✅ numeric env + validation gate →
2 (LLM surface, `llm_student.py`) → 3 (synthetic SFT, `gen_sft_data.py`) →
4 ✅ RL sequencing → 5 ✅ calibration flywheel (read-only, privacy-safe; data still thin).
