# Learning Progress Model (v1) — "the O(n) of a learning goal"

> A rigorous, computable, **daily** measure of *real* learning progress — one that rewards
> **holding depth across all aspects** and exposes **surface-gazing**, instead of the vanity number
> (time spent / topics touched) that every other tracker shows. Pressure-tested 2026-07-19.
> Runs on data **Acharya already generates** (the concept bank + mastery gate + SRS). Owner: Deepak.
> Serves the `ACHARYA_BRAND_SOUL.md` thesis ("the knowledge is in the holding") in math.

---

## 0. The problem it solves

Two lies every learning dashboard tells:
1. **Time = progress.** It isn't. 90 minutes of grazing ≈ 0 learning. (Deepak's own law: *output > hours.*)
2. **Average mastery = progress.** It isn't. Deeply learn the easy 80%, skip the hard 20%, and your
   *average* still reads 80% — the surface-gazer's dashboard looks identical to the disciplined learner's.

This model fixes both: it measures **depth held evenly across every aspect**, and it treats **time as the
cost, never the score.**

---

## 1. The object: a goal is a set of aspects

A learning goal `G` decomposes into aspects `a₁…aₙ` (Acharya already has this — the **concept bank**;
e.g. Building Agentic Systems = 18 concepts). Each aspect gets a mastery score:

```
mᵢ = depthᵢ × retentionᵢ          mᵢ ∈ [0,1]
```

**depthᵢ** — how deeply held (straight from Acharya's `concepts` field + mastery gate):

| Acharya state | depthᵢ | meaning |
|---|---|---|
| `not_seen` | 0.0 | not reached |
| `shaky` | 0.5 | attempted, wobbly |
| `solid` (explained in own words) | 0.85 | held |
| `solid` + **transferred to a fresh case** | 1.0 | truly held (the gate's gold standard) |

**retentionᵢ** — did it survive? From SRS: `ρ = e^(−Δt/S)`, stability `S` grows with each spaced recall,
resets on a miss. (Acharya's SRS already tracks the recall schedule per concept.)

**wᵢ** — aspect weight (importance). v1: equal weights, OR exam-blueprint weights for exam goals.
*(Deferred: prerequisite-centrality weighting — see §7.)*

---

## 2. Aggregation — the pressure-tested core

The whole family of "how to combine the mᵢ" is one operator, the **power mean**, with a strictness knob `p`:

```
P(p) = ( Σ wᵢ·mᵢᵖ / Σ wᵢ )^(1/p)
```

- `p = 1` → arithmetic mean → **rewards gazing** (the vanity number). Rejected.
- `p → 0` → geometric mean → **FAILS**: one untouched aspect (mᵢ=0) zeroes the whole score, so a student
  who deeply knows 17/18 scores the same (0) as a total beginner. Useless for a sequential journey. Rejected.
- **`p ≈ 0.5`** → penalizes unevenness (anti-gazing) **without** the zero-catastrophe (for p>0 a zero term
  just drags proportionally, never annihilates). **← v1 CHOICE.**
- `p → −∞` → min / weakest-link → too brutal for a headline number (fine as a *diagnostic*, see §4).

**Why p ≈ 0.5 — the worked proof (equal weights):**

| Scenario | Arithmetic (p=1) | **P_real (p=0.5)** | verdict |
|---|---|---|---|
| 17 deep (m=1), 1 untouched (m=0) | 0.944 | **0.892** | mild honest penalty, NOT zero |
| Gazer: 9 deep (m=1), 9 shallow (m=0.1) | 0.550 | **0.433** | spread-out shallowness punished harder |
| Disciplined: all 18 evenly at 0.7 | 0.700 | **0.699** | even depth → no penalty |

Even depth rewarded, gazing punished, graceful at zeros. `p` stays **tunable** — raise toward 1 if too
harsh in practice, lower toward 0 to punish gaps harder. Start at **0.5**.

**Headline number the student sees:** `P_real = P(0.5)` over the **whole goal** (a smooth 0→1 progress meter).

---

## 3. The Surface-Gazing Index (behavior signal)

```
GazingIndex = P_avg − P_real     (computed over the REACHED set only, not the whole goal)
```

By the AM–GM inequality family, this gap ≈ **variance of depth across aspects** — i.e. *how uneven your
holding is.* High gap = "you're deep in some, shallow in others = gazing." **Reached-set only** — otherwise
not-yet-covered concepts masquerade as gazing when they're just "not started." This is the number that
says: *"you look 80% done; you're really 60% done; here's the aspect you keep dodging."*

---

## 4. The daily layer — what you actually asked for

Log **time-per-aspect** `tᵢ` per day. Time is the **denominator, never the score.**

- **Real gain vs decay (shown separately — don't net them into one scary number):**
  `gain_today` = Σ positive Δmᵢ (new depth + retention recovered by recall);
  `decay_today` = Σ negative Δmᵢ (retention bleeding on neglected aspects).
- **Learning efficiency:** `η = ΔP_real / Σ tᵢ` — real mastery gained per minute today.
  - Gazer: big Σtᵢ, tiny ΔP_real → **η ≈ 0** → *"you gave 90 min and barely moved — you were grazing."*
  - Holder: time converts → high η. *(Retention-recovery counts into ΔP_real so pure-review/consolidation
    days aren't under-rewarded.)*
- **Today's forced hold (operationalizes "hold every aspect"):** surface the most-neglected reached aspect
  = `argminᵢ mᵢ` (tie-break by lowest `tᵢ`) and make them hold *that one*. This is Acharya's SRS ping,
  generalized from "most-overdue concept" → "the aspect of your goal you keep avoiding."

---

## 5. Scalar to motivate, VECTOR to decide

Never let one number be both compass and scoreboard (Goodhart). So:

- **Student sees ONE headline:** `P_real` (+ streak). Motivation.
- **Acharya teaches off the VECTOR:** `(coverage, depth_of_covered, GazingIndex, retention_health, η_today,
  weakest_aspect)`. The vector picks what to teach/force next; the scalar never makes a pedagogical decision.

---

## 6. Worked example — Kritansh (live data, 2026-07-19)

His profile: 5 `solid` (agent_loop, agent_vs_chatbot, tool_is_fn, tool_schema, evaluation),
13 `shaky`, of 18 concepts. depth: solid→0.9, shaky→0.5; retention≈1.0 (recently active).

```
P_avg (p=1)      = (5·0.9 + 13·0.5)/18                 = 0.61
P_real (p=0.5)   = ((5·√0.9 + 13·√0.5)/18)²            = 0.60
GazingIndex      = 0.61 − 0.60                          = 0.01  → he is NOT gazing
```

Honest read: Kritansh is **~60% along, evenly** — not a surface-gazer (his gap is ~0), just genuinely
mid-climb with lots still `shaky`. The model correctly refuses to inflate him to "5/18 solid = done with the
easy stuff." **Data caveat:** several `shaky` concepts are in *future* modules (he's at M3) — likely a
default init, not real attempts. v1 should score over the **reached set** (concepts ≤ current position);
default-shaky-unreached must not be counted as "attempted." *(This is the depth-signal-integrity risk in §8.)*

---

## 7. Deliberately NOT in v1 (don't build ahead)

- **Prerequisite-DAG / poison-propagation** (a weak foundation discounting its dependents). The true
  structure *is* a DAG — but Acharya's **strict sequence already enforces it** (can't reach a concept until
  prereqs are solid), so a flat power-mean is a defensible approximation. Add the graph only if we teach
  non-linear goals and real data shows the flat model misleading.
- **Learned/auto-tuned `p` or weights.** Start p=0.5, equal (or exam-blueprint) weights. Tune from data.
- **Per-second attention tracking.** Coarse per-aspect daily time is enough for η.

---

## 8. Honest caveats (the model lives or dies here)

1. **The whole model is downstream of the depth signal.** If `depthᵢ` is "passed a quiz," it's garbage-in
   and the elegant aggregation is lipstick. It only works because Acharya gates `solid` on **explain +
   transfer to a fresh case + calibration**. Guard that measurement like it's the product — for this, it is.
2. **Retention decay makes ΔP_real go negative on studied days.** Honest (you forget), but show *gain* and
   *decay* as separate channels, never a single number that punishes a student who showed up.
3. **Goodhart.** The power-mean (p<1) is hard to game (must raise *every* aspect), but any target invites
   gaming at the measurement layer — keep the transfer/fresh-case requirement adversarial.
4. **It's a hypothesis until validated.** Ship it, then check: does P_real predict real outcomes (exam
   marks, a working project) better than time-spent or P_avg? If not, the operator or the depth signal is wrong.

---

## 9. MVP build (on top of what exists)

1. Add per-day `time_by_aspect` + `depth_history` to the learner profile (or the `LearningEvent` table from
   the learning-loop instrumentation — see [[project-learning-loop]]).
2. One pure function: `P_real(concepts, srs, p=0.5)` → headline + the diagnostic vector. ~30 lines.
3. Surface `P_real` + weakest-aspect on the read-only dashboard (:8790) and (later) to the student.
4. Wire the "today's forced hold" into the existing SRS ping selection.

*Ships on data Acharya already has. The new work is the aggregation + the daily time log, not a new sensor.*
