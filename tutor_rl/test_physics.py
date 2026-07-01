"""Stage 1 validation — the 'physics' must reward good pedagogy over answer-dumping
BEFORE we add an LLM or train anything.  If this fails, the simulator is wrong and
no amount of RL will help.  (Same discipline as validating the drone env-config
before any training run.)

Run:  python3 test_physics.py
"""
from __future__ import annotations
import numpy as np
from student_env import StudentEnv
from tutors import AnswerDumpTutor, GreedyHeuristicTutor, FixedOrderTutor


def run(tutor_cls, seed, max_turns=40):
    env = StudentEnv(max_turns=max_turns, seed=seed)
    obs = env.reset(seed=seed)
    tutor = tutor_cls()
    total = 0.0; info = {}
    done = False
    while not done:
        a, _, _ = tutor.act(obs)
        obs, r, done, info = env.step(a)
        total += r
    return total, info


def main():
    N = 200
    results = {}
    for name, cls in [("answer_dump", AnswerDumpTutor),
                      ("fixed_order", FixedOrderTutor),
                      ("heuristic", GreedyHeuristicTutor)]:
        gains, rets, miscs, rewards = [], [], [], []
        for s in range(N):
            tot, info = run(cls, seed=1000 + s)
            gains.append(info.get("immediate_gain", 0.0))
            rets.append(info.get("retained_gain", 0.0))
            miscs.append(info.get("misc_remaining", 0))
            rewards.append(tot)
        results[name] = dict(
            gain=np.mean(gains), retained=np.mean(rets),
            misc=np.mean(miscs), reward=np.mean(rewards))

    print(f"{'tutor':<14}{'learn_gain':>12}{'retained':>12}{'misc_left':>12}{'reward':>12}")
    for n, r in results.items():
        print(f"{n:<14}{r['gain']:>12.4f}{r['retained']:>12.4f}{r['misc']:>12.2f}{r['reward']:>12.3f}")

    # ---- assertions: the physics must be pedagogically sane ----
    assert results["heuristic"]["gain"] > results["answer_dump"]["gain"], \
        "FAIL: answer-dumping should NOT beat good pedagogy on learning gain"
    assert results["heuristic"]["retained"] > results["answer_dump"]["retained"], \
        "FAIL: answer-dumping should NOT beat good pedagogy on retention"
    assert results["heuristic"]["misc"] < results["answer_dump"]["misc"], \
        "FAIL: good pedagogy should repair MORE misconceptions than answer-dumping"
    print("\nPASS — the simulator rewards good pedagogy over answer-dumping.")


if __name__ == "__main__":
    main()
