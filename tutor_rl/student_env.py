"""Stage 1 — the Student Simulator (Layer A: latent numeric dynamics).

This IS the RL environment.  The tutor is the agent; this is the world.
Mirrors a gym env: reset() samples a new student (domain randomization),
step(action) applies a tutoring move and returns (obs, reward, done, info).

The tutor NEVER sees the true mastery — only an observation built from observed
responses (partial observability, like drone sensors vs. full physics state).
The reward is computed from the LATENT state (learning gain on a held-out quiz +
retention), exactly as specced in TUTOR_RL_STUDENT_SIMULATOR_SPEC.md.
"""
from __future__ import annotations
import os, json
import numpy as np

from knowledge import (
    K, SKILLS, PREREQ_IDX, NEIGHBOR_IDX, MISCONCEPTIONS, MISC_BY_SKILL,
    MISC_PREVALENCE, SKILL_IDX,
)

# Stage-5 flywheel: load real-data priors if calibrate.py has produced them.
# Falls back silently to literature priors when a field is absent / too thin.
def _load_calibrated():
    p = os.path.join(os.path.dirname(__file__), "calibrated_priors.json")
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p)).get("fields", {})
    except Exception:
        return {}

CALIB = _load_calibrated()

# Tutoring move types (the action vocabulary).  `assess` is terminal.
MOVES = ["ask_recall", "worked_example", "hint", "explain", "practice", "review", "assess"]
MOVE_IDX = {m: i for i, m in enumerate(MOVES)}
N_NONTERMINAL = 6  # everything except assess
# Flat action space: (move, skill) for the 6 non-terminal moves + a single assess.
N_ACTIONS = N_NONTERMINAL * K + 1
ASSESS_ACTION = N_ACTIONS - 1


def decode_action(a: int):
    if a == ASSESS_ACTION:
        return "assess", -1
    return MOVES[a // K], a % K


def encode_action(move: str, skill: int) -> int:
    if move == "assess":
        return ASSESS_ACTION
    return MOVE_IDX[move] * K + skill


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class StudentEnv:
    def __init__(self, max_turns=40, retention_steps=30, seed=0,
                 w_gain=10.0, w_retain=6.0):
        self.max_turns = max_turns
        self.retention_steps = retention_steps
        self.w_gain = w_gain
        self.w_retain = w_retain
        self.rng = np.random.default_rng(seed)
        self.target = np.arange(K)  # course mastery = all skills

    # ---- domain randomization: sample a NEW student each reset ----
    def reset(self, seed: int | None = None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        rng = self.rng
        prior = rng.uniform(0.05, 0.35)                       # global prior knowledge
        # starting mastery decays along the prereq chain (later skills lower)
        depth = np.array([len(PREREQ_IDX[i]) for i in range(K)], float)
        self.mastery = np.clip(prior - 0.04 * np.arange(K) + rng.normal(0, 0.05, K), 0.0, 0.9)
        # calibrated per-concept difficulty (real data) -> lower starting mastery on harder concepts
        cdiff = CALIB.get("concept_difficulty", {})
        if cdiff:
            for i, s in enumerate(SKILLS):
                if s in cdiff:
                    self.mastery[i] = float(np.clip(self.mastery[i] * (1.0 - 0.5 * cdiff[s]), 0.0, 0.9))
        # calibrated retention: a higher mean SRS box => slower real forgetting
        lam_hi = 0.045
        mean_box = CALIB.get("srs_mean_box")
        if isinstance(mean_box, (int, float)) and mean_box > 0:
            lam_hi = max(0.020, 0.045 / (1.0 + 0.3 * mean_box))
        self.traits = dict(
            alpha=rng.uniform(0.10, 0.28),       # learning rate
            lam=rng.uniform(0.010, lam_hi),      # forgetting per step (calibrated upper bound)
            transfer=rng.uniform(0.10, 0.40),    # spillover to neighbours
            grit=rng.uniform(0.45, 0.85),        # frustration tolerance
            help_seeking=rng.uniform(0.2, 0.8),
            guess=rng.uniform(0.10, 0.25),
            slip=rng.uniform(0.05, 0.15),
        )
        # active misconceptions sampled by real prevalence
        self.misc = set()
        for m in MISCONCEPTIONS:
            if rng.random() < MISC_PREVALENCE[m["id"]]:
                self.misc.add(m["id"])
        self.affect = dict(confidence=0.5, frustration=0.0, engagement=0.7)
        self.last_seen = np.full(K, -1, int)
        self.reps = np.zeros(K, int)
        self.turn = 0
        self.disengaged = False
        self._cur_skill = 0
        self._misc_hardening = {}
        self.pretest = self._quiz(self.mastery)
        # tutor-side belief (a simple BKT estimate built from observed responses)
        self._belief = self.mastery * 0.0 + 0.15
        self._obs_correct = np.zeros(K); self._obs_total = np.zeros(K)
        return self._obs()

    # ---- helpers on the LATENT state ----
    def _misc_penalty(self, skill: int) -> float:
        """How much an active misconception drags down P(correct) on a skill."""
        for m in MISC_BY_SKILL.get(skill, []):
            if m["id"] in self.misc:
                return 0.25
        return 0.0

    def _p_correct(self, skill: int, difficulty: float) -> float:
        t = self.traits
        base = _sigmoid(5.0 * (self.mastery[skill] - difficulty))
        base = t["guess"] + (1 - t["guess"] - t["slip"]) * base
        return float(np.clip(base - self._misc_penalty(skill), 0.02, 0.98))

    def _quiz(self, mastery: np.ndarray) -> float:
        """Held-out mastery quiz: expected score on fresh items at fixed difficulty,
        disjoint from teaching (so the tutor can't teach-to-the-test)."""
        diff = 0.5
        ps = []
        for k in self.target:
            p = _sigmoid(5.0 * (mastery[k] - diff))
            p -= self._misc_penalty(k) * 0.5  # misconceptions still bite on the quiz
            ps.append(np.clip(p, 0.02, 0.98))
        return float(np.mean(ps))

    def _difficulty_for(self, skill: int, move: str) -> float:
        """Auto-pick item difficulty near the edge of ability (desirable difficulty)."""
        m = self.mastery[skill]
        if move == "worked_example":
            return max(0.0, m - 0.15)
        if move == "hint":
            return m + 0.10
        if move == "practice":
            return m + 0.15
        return m + 0.05  # ask_recall / review

    # ---- transition ----
    def step(self, action: int):
        assert not self.disengaged, "episode over"
        move, skill = decode_action(action)
        self.turn += 1
        info = {"move": move, "skill": skill}

        if move == "assess":
            return self._finish(info)

        t = self.traits
        self._cur_skill = skill
        diff = self._difficulty_for(skill, move)
        attempt = move in ("ask_recall", "practice", "review", "hint")
        correct = False
        reward = 0.0
        gain = 0.0

        # spacing: bigger durable gain if the skill hasn't been seen for a while
        gap = self.turn - self.last_seen[skill] if self.last_seen[skill] >= 0 else self.turn
        spacing = 1.0 + 0.5 * np.tanh(gap / 8.0)
        # desirable difficulty: gain peaks when item ~ at the edge of ability
        ddiff = np.exp(-((diff - self.mastery[skill]) / 0.30) ** 2)
        prereq_ok = self._prereq_factor(skill)

        if attempt:
            p = self._p_correct(skill, diff)
            correct = self.rng.random() < p
            if move == "hint":  # a hint assists the attempt
                p = min(0.98, p + 0.15)
                correct = self.rng.random() < p
            base = t["alpha"] * (1 - self.mastery[skill]) * ddiff * spacing * prereq_ok
            gain = base * (1.0 if correct else 0.4)  # successful retrieval is more durable
            self._update_affect(diff, success=correct)
            # observed response feeds the tutor's belief
            self._obs_total[skill] += 1
            self._obs_correct[skill] += 1 if correct else 0
        elif move == "worked_example":
            gain = t["alpha"] * (1 - self.mastery[skill]) * 0.7 * prereq_ok
            self._update_affect(diff, success=True, mild=True)
        elif move == "explain":
            # telling without recall: tiny gain, and it REINFORCES misconceptions
            gain = t["alpha"] * (1 - self.mastery[skill]) * 0.25 * prereq_ok
            self._reinforce_misconception(skill)
            self._update_affect(diff, success=True, mild=True)
            reward -= 0.15  # process penalty: answer-dumping

        self.mastery[skill] = float(np.clip(self.mastery[skill] + gain, 0.0, 1.0))
        repaired = self._maybe_repair(move, skill)
        self._transfer(skill, gain)
        self._forget()
        self.last_seen[skill] = self.turn
        self.reps[skill] += 1

        # dense shaping reward
        reward += 4.0 * gain
        if repaired:
            reward += 2.0   # repairing a misconception unlocks downstream mastery — value it
        if self.affect["frustration"] > t["grit"]:
            self.disengaged = True
            reward -= 2.0
            info["disengaged"] = True

        done = self.disengaged or self.turn >= self.max_turns
        if done and not self.disengaged:
            obs, term_r, _, fin = self._finish(info)
            return obs, reward + term_r, True, fin
        return self._obs(), reward, done, info

    def _finish(self, info):
        """Terminal: retained learning gain on the held-out quiz."""
        retained = self.mastery.copy()
        for _ in range(self.retention_steps):
            retained = self._decay(retained)
        post = self._quiz(self.mastery)
        post_ret = self._quiz(retained)
        gain = post - self.pretest
        ret_gain = post_ret - self.pretest
        reward = self.w_gain * gain + self.w_retain * ret_gain
        info.update(immediate_gain=gain, retained_gain=ret_gain,
                    pretest=self.pretest, posttest=post,
                    misc_remaining=len(self.misc))
        self.disengaged = True
        return self._obs(), reward, True, info

    # ---- dynamics sub-rules ----
    def _prereq_factor(self, skill):
        ps = PREREQ_IDX[skill]
        if not ps:
            return 1.0
        return float(0.3 + 0.7 * np.mean([self.mastery[p] for p in ps]))

    def _transfer(self, skill, gain):
        for n in NEIGHBOR_IDX[skill]:
            self.mastery[n] = float(np.clip(self.mastery[n] + self.traits["transfer"] * gain * 0.3, 0, 1))

    def _decay(self, mastery):
        # consolidation: a well-practiced skill (more reps) forgets slower.
        # This is what makes spacing + review valuable for RETENTION, so a tutor
        # that only crams loses the retained-gain reward.
        eff = self.traits["lam"] / (1.0 + 0.6 * self.reps)
        return mastery * np.exp(-eff)

    def _forget(self):
        self.mastery = self._decay(self.mastery)

    def _update_affect(self, diff, success, mild=False):
        m = self.mastery[self._cur_skill]
        if not mild:
            if diff - m > 0.35:        # too hard
                self.affect["frustration"] += 0.18
                self.affect["engagement"] -= 0.08
            elif m - diff > 0.35:      # too easy / boring
                self.affect["engagement"] -= 0.06
            elif success:
                self.affect["confidence"] = min(1, self.affect["confidence"] + 0.05)
                self.affect["engagement"] = min(1, self.affect["engagement"] + 0.03)
        else:
            self.affect["engagement"] = max(0, self.affect["engagement"] - 0.01)
        self.affect["frustration"] = max(0.0, self.affect["frustration"] - 0.02)  # natural cool-down
        self._clip_affect()

    def _clip_affect(self):
        for k in self.affect:
            self.affect[k] = float(np.clip(self.affect[k], 0.0, 1.0))

    def _maybe_repair(self, move, skill):
        for m in list(MISC_BY_SKILL.get(skill, [])):
            if m["id"] in self.misc and move in m["repaired_by"]:
                hard = self._misc_hardening.get(m["id"], 0.0)
                if self.rng.random() < max(0.05, (1 - m["repair_difficulty"] - hard) * 0.6):
                    self.misc.discard(m["id"])
                    return True
        return False

    def _reinforce_misconception(self, skill):
        # answer-dumping (explain) on a skill with an active misconception makes
        # that misconception harder to shift later — so RL learns telling backfires.
        for m in MISC_BY_SKILL.get(skill, []):
            if m["id"] in self.misc and "explain" in m["reinforced_by"]:
                self._misc_hardening[m["id"]] = min(0.4, self._misc_hardening.get(m["id"], 0.0) + 0.08)

    # ---- observation (what the tutor sees; NOT the latent state) ----
    def _obs(self):
        # BKT-style belief from observed responses, blended with a prior
        with np.errstate(invalid="ignore", divide="ignore"):
            emp = np.where(self._obs_total > 0, self._obs_correct / np.maximum(self._obs_total, 1), 0.15)
        belief = np.clip(emp, 0.02, 0.98)
        steps_since = np.where(self.last_seen >= 0, (self.turn - self.last_seen), self.turn) / max(self.max_turns, 1)
        reps = self.reps / 10.0
        glob = np.array([self.turn / self.max_turns, self.affect["frustration"],
                         self.affect["engagement"], self.affect["confidence"],
                         float(belief.mean())])
        self._belief = belief
        return dict(belief=belief, steps_since=steps_since, reps=reps, glob=glob)

    # convenience for hand-written tutors
    def prereqs_met(self):
        b = self._belief
        out = np.zeros(K)
        for k in range(K):
            ps = PREREQ_IDX[k]
            out[k] = 1.0 if not ps else float(np.mean([b[p] for p in ps]) > 0.55)
        return out
