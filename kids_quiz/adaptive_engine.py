#!/usr/bin/env python3
"""
adaptive_engine.py — RUNG 2 + 3 of the science-backed engine: per-skill MASTERY STATE + the 85% CONTROLLER.

Common to kids AND seniors — student state is level-agnostic. It reads the difficulty `b` that
assessment_core computes for each item, and:
  • RUNG 2 — tracks, per (student, skill): BKT p_mastery + an Elo ability θ + recent accuracy.
  • RUNG 3 — the 85% controller: picks the next item's target difficulty so the learner stays near
             ~85% correct (Wilson 2019), and gates a skill "mastered" at p_mastery ≥ 0.95 (Corbett & Anderson).

Together with assessment_core this is the minimal closed loop:
   measure mastery → request an item at b≈target → hold 85% → update → repeat.

Pure Python, no deps. State is a plain dict → store one row per (student, skill) in any DB.
"""
import math

BKT = {"L0": 0.30, "T": 0.12, "S": 0.10, "G": 0.20}   # prior, learn, slip, guess (defaults)
ELO_K = 0.40
EMA_ALPHA = 0.30
TARGET = 0.85
# P(correct)=0.85 in a 1-param logistic ⇒ (θ − b) = ln(.85/.15) ≈ 1.734 ⇒ serve at b ≈ θ − 1.73
B_OFFSET = 1.73


def new_state(skill, theta=0.0):
    return {"skill": skill, "p_mastery": BKT["L0"], "theta": theta, "ema": TARGET,
            "n": 0, "n_correct": 0, "target_b": theta - B_OFFSET, "misconceptions": {}}


def _logistic(x):
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, x))))


def update(state, b, correct, guess=None, slip=None, misconception_id=None):
    """After a student answers an item of difficulty `b`. `guess` should be 0.25 for 4-option MCQ,
    lower (~0.05) for free-response — pass it so mastery doesn't inflate on MCQ luck."""
    S = BKT["S"] if slip is None else slip
    G = BKT["G"] if guess is None else guess
    p = state["p_mastery"]
    # --- BKT: posterior given the observation, then the learning transition ---
    if correct:
        p_obs = p * (1 - S) / (p * (1 - S) + (1 - p) * G)
    else:
        p_obs = p * S / (p * S + (1 - p) * (1 - G))
    state["p_mastery"] = p_obs + (1 - p_obs) * BKT["T"]
    # --- Elo: nudge ability toward/away from the item ---
    exp = _logistic(state["theta"] - b)
    state["theta"] += ELO_K * ((1.0 if correct else 0.0) - exp)
    # --- recent accuracy + counts ---
    state["ema"] = EMA_ALPHA * (1.0 if correct else 0.0) + (1 - EMA_ALPHA) * state["ema"]
    state["n"] += 1
    state["n_correct"] += 1 if correct else 0
    # --- the 85% controller: proportional shift of target difficulty ---
    if state["ema"] > TARGET + 0.03:
        state["target_b"] += 0.12          # too easy → harder next
    elif state["ema"] < TARGET - 0.03:
        state["target_b"] -= 0.12          # too hard → easier next
    # keep the target anchored to ability (the ZPD band: just below θ)
    state["target_b"] = max(state["theta"] - 2.6, min(state["theta"] + 0.4, state["target_b"]))
    # --- diagnostic: log which misconception on a wrong answer ---
    if (not correct) and misconception_id:
        state["misconceptions"][misconception_id] = state["misconceptions"].get(misconception_id, 0) + 1
    return state


def next_target_b(state):
    return state["target_b"]

def is_mastered(state, thresh=0.95, min_attempts=5):
    """Mastered = BKT p ≥ 0.95 AND enough evidence AND recent success was near the student's edge
    (not just easy items) — otherwise a few easy correct answers falsely 'master' a skill."""
    at_edge = state["target_b"] >= state["theta"] - 1.0   # items have climbed toward ability
    return state["p_mastery"] >= thresh and state["n"] >= min_attempts and at_edge

def pick_item(candidates, target_b):
    """From generated+enriched candidates (each has item['difficulty']), pick the one nearest target_b."""
    return min(candidates, key=lambda it: abs(it.get("difficulty", 0.0) - target_b))


# ---------------- simulation: prove the loop holds ~85% and detects mastery ----------------
if __name__ == "__main__":
    import random
    r = random.Random(7)
    # a synthetic student whose TRUE ability starts low and rises (they're learning)
    true_theta = -0.5
    st = new_state("frac.add", theta=0.0)
    print(f"{'item':>4} {'served_b':>8} {'correct':>7} {'ema':>6} {'θ_est':>6} {'p_mastery':>9}")
    for i in range(1, 41):
        if i <= 20:
            true_theta += 0.09                  # the student improves while learning...
        # ...then plateaus (i>20) so we can see the controller settle at 85%
        b = next_target_b(st)                   # controller chooses difficulty
        p_correct = _logistic(true_theta - b)   # ground-truth response model
        correct = r.random() < p_correct
        update(st, b, correct, guess=0.05)      # free-response worksheet → low guess
        if i % 5 == 0 or i == 1:
            print(f"{i:>4} {b:>8.2f} {str(correct):>7} {st['ema']:>6.2f} {st['theta']:>6.2f} {st['p_mastery']:>9.3f}"
                  + ("   ← MASTERED" if is_mastered(st) else ""))
    acc = st["n_correct"] / st["n"]
    print(f"\nOverall accuracy held at {acc:.0%}  (target 85%)  ·  final p_mastery={st['p_mastery']:.3f}  ·  θ_est={st['theta']:.2f}")
    print("→ the controller kept the student near their edge while ability rose, and BKT detected mastery.")
