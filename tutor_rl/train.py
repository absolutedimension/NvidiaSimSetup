"""Stage 4 — train the tutor sequencing policy with REINFORCE (pure numpy).

The policy is a linear-softmax over per-action features (tutors.LinearPolicy).
Reward = dense shaping + terminal retained learning gain from the student env.
A moving-average baseline reduces variance.  No torch / no GPU needed.

Run:  python3 train.py            # trains, prints learning curve, saves policy.npy
"""
from __future__ import annotations
import numpy as np
from student_env import StudentEnv, N_ACTIONS
from tutors import LinearPolicy


def rollout(env, policy, seed):
    obs = env.reset(seed=seed)
    feats, acts, rews = [], [], []
    done = False; info = {}
    while not done:
        a, p, F = policy.act(obs)
        feats.append(F); acts.append(a)
        obs, r, done, info = env.step(a)
        rews.append(r)
    return feats, acts, rews, info


def discounted(rews, gamma=0.99):
    out = np.zeros(len(rews)); run = 0.0
    for t in reversed(range(len(rews))):
        run = rews[t] + gamma * run
        out[t] = run
    return out


def train(iters=400, batch=32, lr=0.02, gamma=0.99, seed=0, max_turns=40):
    rng = np.random.default_rng(seed)
    policy = LinearPolicy(seed=seed)
    env = StudentEnv(max_turns=max_turns, seed=seed)
    baseline = 0.0
    curve = []
    for it in range(iters):
        grad = np.zeros_like(policy.w)
        batch_ret = []
        for b in range(batch):
            s = int(rng.integers(1, 10_000_000))
            feats, acts, rews, info = rollout(env, policy, seed=s)
            G = discounted(rews, gamma)
            ep_ret = sum(rews)
            batch_ret.append(ep_ret)
            for F, a, Gt in zip(feats, acts, G):
                # softmax grad of log pi(a|s) = f_a - E_pi[f]
                logits = F @ policy.w
                p = np.exp(logits - logits.max()); p /= p.sum()
                expected = p @ F
                dlogp = F[a] - expected
                grad += dlogp * (Gt - baseline)
        grad /= batch
        policy.w += lr * grad
        mean_ret = float(np.mean(batch_ret))
        baseline = 0.9 * baseline + 0.1 * mean_ret
        curve.append(mean_ret)
        if it % 20 == 0 or it == iters - 1:
            print(f"iter {it:4d}  mean_return {mean_ret:8.3f}  |w| {np.linalg.norm(policy.w):6.3f}")
    np.save("policy.npy", policy.w)
    print("saved policy.npy")
    return policy, curve


if __name__ == "__main__":
    train()
