"""Tutor policies — the AGENT side.

Baselines (hand-written) + a learnable linear-softmax policy trained by REINFORCE.
All policies act on the env OBSERVATION only (never the latent state).

The learnable policy scores each candidate action a=(move,skill) with w·f(obs,a)
and samples from a softmax.  Per-action features make the sequencing problem
learnable with a tiny linear model — no torch needed, runs anywhere.
"""
from __future__ import annotations
import numpy as np

from knowledge import K, PREREQ_IDX
from student_env import MOVES, N_NONTERMINAL, N_ACTIONS, ASSESS_ACTION, decode_action

# ---- per-action feature builder (shared by the learnable policy) ----
N_MOVE_FLAGS = len(MOVES)           # one-hot of move type
N_FEAT = 8 + N_MOVE_FLAGS + 4       # see _features


def _features(obs, a: int) -> np.ndarray:
    move, skill = decode_action(a)
    b = obs["belief"]; ss = obs["steps_since"]; reps = obs["reps"]; g = obs["glob"]
    f = np.zeros(N_FEAT)
    if a == ASSESS_ACTION:
        bm = float(b.mean())
        f[0] = bm                      # mean belief (assess when high)
        f[1] = g[0]                    # turn fraction
        f[2] = 1.0
    else:
        prereq = PREREQ_IDX[skill]
        pmet = 1.0 if not prereq else float(np.mean([b[p] for p in prereq]))
        f[0] = b[skill]                # current belief on the skill
        f[1] = 1.0 - b[skill]          # room to grow
        f[2] = pmet                    # prereqs met?
        f[3] = ss[skill]               # staleness (drives review)
        f[4] = reps[skill]             # how much practiced
        f[5] = g[1]                    # frustration
        f[6] = g[2]                    # engagement
        f[7] = g[0]                    # turn fraction
    # move one-hot
    f[8 + MOVES.index(move)] = 1.0
    # interactions that encode pedagogy priors the policy can keep or flip
    if a != ASSESS_ACTION:
        f[8 + N_MOVE_FLAGS + 0] = (move == "ask_recall") * b[skill]
        f[8 + N_MOVE_FLAGS + 1] = (move == "worked_example") * (1 - b[skill])
        f[8 + N_MOVE_FLAGS + 2] = (move == "review") * ss[skill]
        f[8 + N_MOVE_FLAGS + 3] = (move == "practice") * b[skill]
    return f


def _action_matrix(obs) -> np.ndarray:
    return np.stack([_features(obs, a) for a in range(N_ACTIONS)])


def _softmax(x):
    x = x - x.max()
    e = np.exp(x)
    return e / e.sum()


class LinearPolicy:
    def __init__(self, seed=0):
        self.w = np.zeros(N_FEAT)
        self.rng = np.random.default_rng(seed)

    def probs(self, obs):
        F = _action_matrix(obs)              # (A, N_FEAT)
        return _softmax(F @ self.w), F

    def act(self, obs, greedy=False):
        p, F = self.probs(obs)
        a = int(p.argmax()) if greedy else int(self.rng.choice(N_ACTIONS, p=p))
        return a, p, F


# ---------------- hand-written baselines ----------------
class RandomTutor:
    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)
    def act(self, obs, greedy=False):
        return int(self.rng.integers(N_ACTIONS)), None, None


class AnswerDumpTutor:
    """The anti-pattern: explain every skill in order, then assess. Should LOSE."""
    def __init__(self, **_):
        self.i = 0
    def act(self, obs, greedy=False):
        from student_env import encode_action
        if self.i >= K:
            return ASSESS_ACTION, None, None
        a = encode_action("explain", self.i); self.i += 1
        return a, None, None


class FixedOrderTutor:
    """Teach skills in curriculum order with worked_example -> recall, then assess."""
    def __init__(self, **_):
        self.i = 0; self.phase = 0
    def act(self, obs, greedy=False):
        from student_env import encode_action
        if self.i >= K:
            return ASSESS_ACTION, None, None
        move = ["worked_example", "ask_recall"][self.phase]
        a = encode_action(move, self.i)
        self.phase += 1
        if self.phase > 1:
            self.phase = 0; self.i += 1
        return a, None, None


class GreedyHeuristicTutor:
    """Strong hand-built Socratic baseline: teach-then-check (worked_example to
    introduce, then ask_recall/practice so the belief actually updates), advance
    along the prereq chain, review the stalest mastered skill occasionally, and
    assess when mean belief is high.  Uses reps (not just belief) to advance so it
    never gets stuck re-teaching the same skill."""
    def __init__(self, **_):
        self.t = 0
    def act(self, obs, greedy=False):
        from student_env import encode_action
        self.t += 1
        b = obs["belief"]; ss = obs["steps_since"]; reps = obs["reps"]; g = obs["glob"]
        if g[0] > 0.5 and b.mean() > 0.6:
            return ASSESS_ACTION, None, None
        # prereq-met mask (a skill is teachable once its prereqs look learned)
        met = np.ones(K, bool)
        for k in range(K):
            ps = PREREQ_IDX[k]
            if ps and np.mean([b[p] for p in ps]) < 0.5:
                met[k] = False
        cand = np.where(met)[0]
        if len(cand) == 0:
            cand = np.arange(K)
        # spaced review pull-back every 5th move
        if self.t % 5 == 0:
            mastered = np.where(b > 0.6)[0]
            if len(mastered):
                k = int(mastered[np.argmax(ss[mastered])])
                return encode_action("review", k), None, None
        # target = least-practiced-then-least-believed teachable skill
        k = int(cand[np.lexsort((b[cand], reps[cand]))[0]])
        if reps[k] < 0.05:                       # never introduced -> teach first
            move = "worked_example"
        elif b[k] < 0.6:                          # introduced -> retrieval practice
            move = "ask_recall"
        else:                                     # solid -> push difficulty
            move = "practice"
        return encode_action(move, k), None, None


BASELINES = {
    "random": RandomTutor,
    "answer_dump": AnswerDumpTutor,
    "fixed_order": FixedOrderTutor,
    "heuristic": GreedyHeuristicTutor,
}
