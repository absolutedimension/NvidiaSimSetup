"""Evaluate the RL-trained tutor vs. baselines on a held-out set of students.

Metric that matters: retained learning gain on the held-out quiz (the real signal),
plus immediate gain, misconceptions repaired, and answer-dump rate.  Uses a FIXED
set of eval seeds disjoint from training so we measure generalization to unseen
students (the student2student analogue of sim-to-real).

Run:  python3 evaluate.py            # trains then evaluates everyone
      python3 evaluate.py --load policy.npy
"""
from __future__ import annotations
import sys, numpy as np
from student_env import StudentEnv, decode_action
from tutors import BASELINES, LinearPolicy
from train import train


def run_episode(env, tutor, seed):
    obs = env.reset(seed=seed)
    done = False; info = {}; dumps = 0; n = 0
    while not done:
        a, _, _ = tutor.act(obs, greedy=True)
        if decode_action(a)[0] == "explain":
            dumps += 1
        n += 1
        obs, r, done, info = env.step(a)
    info["dump_rate"] = dumps / max(n, 1)
    return info


def eval_tutor(make_tutor, eval_seeds, max_turns=40):
    env = StudentEnv(max_turns=max_turns)
    gi, gr, mc, dr = [], [], [], []
    for s in eval_seeds:
        tutor = make_tutor()
        info = run_episode(env, tutor, seed=s)
        gi.append(info.get("immediate_gain", 0.0))
        gr.append(info.get("retained_gain", 0.0))
        mc.append(info.get("misc_remaining", 0))
        dr.append(info.get("dump_rate", 0.0))
    return dict(immediate=np.mean(gi), retained=np.mean(gr),
                misc=np.mean(mc), dump=np.mean(dr))


def main():
    eval_seeds = list(range(50_000, 50_300))   # held-out, disjoint from training
    if "--load" in sys.argv:
        w = np.load(sys.argv[sys.argv.index("--load") + 1])
        policy = LinearPolicy(); policy.w = w
    else:
        print("=== training RL tutor ===")
        policy, _ = train(iters=600, batch=32)
        print()

    rows = {}
    for name, cls in BASELINES.items():
        rows[name] = eval_tutor(lambda c=cls: c(), eval_seeds)

    def make_rl():
        p = LinearPolicy(); p.w = policy.w; return p
    rows["RL_tutor"] = eval_tutor(make_rl, eval_seeds)

    print(f"\n=== Held-out eval ({len(eval_seeds)} unseen students) ===")
    print(f"{'tutor':<14}{'retained_gain':>14}{'immediate':>12}{'misc_left':>12}{'dump_rate':>11}")
    for n, r in rows.items():
        star = "  <<<" if n == "RL_tutor" else ""
        print(f"{n:<14}{r['retained']:>14.4f}{r['immediate']:>12.4f}{r['misc']:>12.2f}{r['dump']:>11.2f}{star}")

    best_base = max(v["retained"] for k, v in rows.items() if k != "RL_tutor")
    rl = rows["RL_tutor"]["retained"]
    print(f"\nRL vs best baseline (retained gain): {rl:.4f} vs {best_base:.4f}  "
          f"({'+' if rl>=best_base else ''}{100*(rl-best_base)/abs(best_base):.1f}%)")


if __name__ == "__main__":
    main()
