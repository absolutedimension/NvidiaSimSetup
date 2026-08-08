#!/usr/bin/env python3
"""
arrangement_rl.py — AMP/GAIL prototype for DJ-style ARRANGEMENT via RL.

The idea (see ARRANGEMENT_RL_DESIGN.md):
  - An arrangement = a grid over time of which sonic ELEMENTS are active
    (sub / kick+bass / bassline / drone / stab / hats).
  - A POLICY composes that grid step by step (state -> which elements are on next).
  - A DISCRIMINATOR learns "real DJ arrangement vs policy-generated". Its score
    IS the reward (adversarial imitation, exactly like AMP for the dance pipeline).
  - We do NOT hand-code the DJ's rules. The policy should REDISCOVER them
    (entry order, breakdown behaviour, active fractions) purely by fooling D.

Data: "real" grids are sampled from the learned grammar.json (a synthetic teacher
distribution). The scale-up version swaps this for the real per-track grids on EC2
and a torch discriminator. This file is pure-numpy so it runs anywhere in seconds.

Usage:
  python3 arrangement_rl.py --grammar ../burmeister_grammar.json --iters 400
  python3 arrangement_rl.py --grammar ../goa-gil/grammar.json    --iters 400
"""
import argparse, json, os, numpy as np

ELEMENTS = ["sub", "kick+bass", "bassline", "drone", "stab", "hats"]
NE = len(ELEMENTS)
LV = " ▁▂▃▄▅▆▇█"


# ----------------------------------------------------------------------------- #
#  TEACHER: sample a plausible "real" arrangement grid from the learned grammar
# ----------------------------------------------------------------------------- #
class Teacher:
    """Turns the aggregated grammar.json back into per-track element grids.

    This is the 'expert' the discriminator is trained to recognise. It encodes
    only the STATISTICS the grammar measured (entry order, active fraction,
    breakdown signature, energy arc) — the individual grids vary by seed."""

    def __init__(self, grammar, T):
        self.T = T
        self.dj = grammar.get("dj", "?")
        self.track_s = grammar["track_minutes"]["median"] * 60.0
        self.active = grammar["element_active_fraction"]            # per-element on-rate
        self.entry_s = grammar["element_mean_entry_s"]             # first appearance (s)
        self.arc = np.array(grammar["energy_arc_24"], float)        # 24-pt energy curve
        self.bpr = grammar["breakdowns_per_hour"]["median"]
        self.bd_dur_s = grammar["breakdown_dur_s"]["median"]
        self.bd_ret = grammar["breakdown_retains"]                 # what survives a breakdown
        self.intro_amb = grammar.get("intro_ambient_fraction", 0.3)
        # entry step per element (fraction of track -> step index)
        self.entry_step = {e: int(np.clip(self.entry_s[e] / self.track_s, 0, 0.95) * T)
                           for e in ELEMENTS}
        # energy arc resampled to T
        self.energy = np.interp(np.linspace(0, 23, T), np.arange(24), self.arc)
        self.sec_per_step = self.track_s / T

    def sample(self, rng):
        T = self.T
        g = np.zeros((T, NE), np.float32)
        # breakdown steps
        hours = self.track_s / 3600.0
        n_bd = max(0, int(round(self.bpr * hours)))
        bd_len = max(1, int(round(self.bd_dur_s / self.sec_per_step)))
        bd_steps = set()
        for _ in range(n_bd):
            c = rng.integers(int(T * 0.35), int(T * 0.9))
            for k in range(bd_len):
                if c + k < T:
                    bd_steps.add(c + k)
        ambient_intro = rng.random() < self.intro_amb
        for t in range(T):
            energy = self.energy[t]
            in_bd = t in bd_steps
            for ei, e in enumerate(ELEMENTS):
                if t < self.entry_step[e]:
                    on = 0.0                                       # not introduced yet
                elif ambient_intro and t < max(1, int(T * 0.05)) and e in ("kick+bass", "hats", "stab"):
                    on = 0.0                                       # ambient no-kick intro
                elif in_bd:
                    on = 1.0 if rng.random() < self.bd_ret.get(e, 0.0) else 0.0
                else:
                    p = self.active[e]
                    # energy gates the "lever" elements (hats/stab) more than the bed
                    if e in ("hats", "stab"):
                        p *= 0.4 + 0.9 * energy
                    on = 1.0 if rng.random() < min(1.0, p) else 0.0
                g[t, ei] = on
        return g


class RealTeacher:
    """Expert distribution built from the REAL per-track grids on EC2
    (dj_engine/<dj>/analysis/*.json). Each track is a list of variable-duration
    sections with continuous element energies; we resample to T uniform steps and
    threshold at 0.35 (same cutoff dj_arrangement_analysis.py uses for 'element on').
    Same .sample(rng) interface as Teacher, so the RL loop is unchanged."""

    THR = 0.35

    def __init__(self, real_dir, T):
        import glob
        self.T = T
        self.dj = os.path.basename(os.path.dirname(real_dir.rstrip("/"))) or "real"
        files = sorted(glob.glob(os.path.join(real_dir, "*.json")))
        self.grids, durs = [], []
        for f in files:
            d = json.load(open(f))
            bands = d["bands"]
            secs = d["sections"]
            if not secs:
                continue
            dur = d["duration_s"]
            durs.append(dur)
            g = np.zeros((T, NE), np.float32)
            for t in range(T):
                tc = (t + 0.5) / T * dur                     # center time of step
                sec = next((s for s in secs if s["start_s"] <= tc < s["end_s"]), secs[-1])
                ev = sec["elements"]
                for ei, e in enumerate(ELEMENTS):
                    # bands order matches ELEMENTS, but index by name to be safe
                    val = ev.get(e, ev.get(bands[ei], 0.0))
                    g[t, ei] = 1.0 if val > self.THR else 0.0
            self.grids.append(g)
        self.track_s = float(np.median(durs)) if durs else T * 30.0
        if not self.grids:
            raise SystemExit(f"no grids loaded from {real_dir}")
        print(f"[RealTeacher] loaded {len(self.grids)} real tracks from {real_dir}")

    def sample(self, rng):
        return self.grids[rng.integers(len(self.grids))]


# ----------------------------------------------------------------------------- #
#  Tiny 1-hidden-layer MLP with manual backprop (no torch available on the Mac)
# ----------------------------------------------------------------------------- #
def he(rng, a, b):
    return (rng.standard_normal((a, b)) * np.sqrt(2.0 / a)).astype(np.float32)


class Discriminator:
    """window of recent element-masks -> P(real). Trained with BCE."""
    def __init__(self, din, hid, rng, lr=0.05):
        self.W1, self.b1 = he(rng, din, hid), np.zeros(hid, np.float32)
        self.W2, self.b2 = he(rng, hid, 1), np.zeros(1, np.float32)
        self.lr = lr

    def forward(self, X):
        self.X = X
        self.z1 = X @ self.W1 + self.b1
        self.h = np.maximum(self.z1, 0)
        self.z2 = self.h @ self.W2 + self.b2
        self.p = 1.0 / (1.0 + np.exp(-self.z2))
        return self.p.ravel()

    def train(self, X, y):
        p = self.forward(X).reshape(-1, 1)
        y = y.reshape(-1, 1)
        n = len(y)
        dz2 = (p - y) / n
        dW2 = self.h.T @ dz2
        db2 = dz2.sum(0)
        dh = dz2 @ self.W2.T
        dz1 = dh * (self.z1 > 0)
        dW1 = self.X.T @ dz1
        db1 = dz1.sum(0)
        for P, dP in ((self.W1, dW1), (self.b1, db1), (self.W2, dW2), (self.b2, db2)):
            P -= self.lr * dP
        eps = 1e-7
        return float(-np.mean(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps)))

    def reward(self, X):
        """GAIL reward: high when D is fooled into thinking the grid is real."""
        p = np.clip(self.forward(X), 1e-6, 1 - 1e-6)
        return -np.log(1.0 - p)


class Policy:
    """state -> 6 independent Bernoulli 'element on' probabilities. REINFORCE."""
    def __init__(self, din, hid, rng, lr=0.05):
        self.W1, self.b1 = he(rng, din, hid), np.zeros(hid, np.float32)
        self.W2, self.b2 = he(rng, hid, NE), np.zeros(NE, np.float32)
        self.lr = lr
        self.rng = rng

    def forward(self, X):
        z1 = X @ self.W1 + self.b1
        h = np.maximum(z1, 0)
        z2 = h @ self.W2 + self.b2
        p = 1.0 / (1.0 + np.exp(-z2))
        return p, (X, z1, h, z2)

    def act(self, x):
        p, _ = self.forward(x[None])
        p = p[0]
        a = (self.rng.random(NE) < p).astype(np.float32)
        return a, p

    def update(self, X, A, ADV):
        """X:(n,din) states, A:(n,NE) actions taken, ADV:(n,) advantages."""
        p, (X, z1, h, z2) = self.forward(X)
        # d(logprob)/d z2 = (a - p);  ascend ADV*logprob  ->  loss grad = -ADV*(a-p)
        dz2 = -(A - p) * ADV[:, None] / len(X)
        # entropy bonus keeps exploration alive
        ent_g = 0.01 * (np.log(np.clip(p, 1e-6, 1) / np.clip(1 - p, 1e-6, 1)))
        dz2 = dz2 - ent_g * (p * (1 - p)) / len(X)
        dW2 = h.T @ dz2
        db2 = dz2.sum(0)
        dh = dz2 @ self.W2.T
        dz1 = dh * (z1 > 0)
        dW1 = X.T @ dz1
        db1 = dz1.sum(0)
        for P, dP in ((self.W1, dW1), (self.b1, db1), (self.W2, dW2), (self.b2, db2)):
            P -= self.lr * dP


# ----------------------------------------------------------------------------- #
#  Environment: policy composes a T-step arrangement; D scores a sliding window
# ----------------------------------------------------------------------------- #
WIN = 10  # discriminator sees a LONG window (needs temporal context to judge the arc)

def pos_feat(t, T):
    f = t / (T - 1)
    return np.array([f, np.sin(2 * np.pi * f), np.cos(2 * np.pi * f)], np.float32)

def policy_state(prev_mask, t, T, recent_e=0.0):
    # recent_e (running energy) lets the policy SHAPE dynamics — build up, drop, recover.
    return np.concatenate([prev_mask, pos_feat(t, T), [recent_e]]).astype(np.float32)  # 6+3+1 = 10

KI, BI, DI = ELEMENTS.index("kick+bass"), ELEMENTS.index("bassline"), ELEMENTS.index("drone")
def bd_flag(masks):
    """breakdown PATTERN: kick+bass OUT, bassline & drone IN (the DJ's signature)."""
    return ((masks[..., KI] < 0.5) & (masks[..., BI] > 0.5) & (masks[..., DI] > 0.5)).astype(np.float32)

def disc_window(grid, t):
    """last WIN masks + the ENERGY trajectory + the BREAKDOWN-pattern trajectory + position.
    The breakdown channel lets D see where the DJ breaks down, so it rewards real breakdowns."""
    T = len(grid)
    w = np.zeros((WIN, NE), np.float32)
    for k in range(WIN):
        idx = t - (WIN - 1) + k
        if 0 <= idx < T:
            w[k] = grid[idx]
    energy = w.mean(axis=1)                                          # (WIN,) energy
    bd = bd_flag(w)                                                  # (WIN,) breakdown pattern
    return np.concatenate([w.ravel(), energy, bd, [t / (T - 1)]]).astype(np.float32)  # WIN*NE+2*WIN+1


def rollout(policy, T):
    grid = np.zeros((T, NE), np.float32)
    states, actions = [], []
    prev = np.zeros(NE, np.float32)
    recent = 0.0
    for t in range(T):
        s = policy_state(prev, t, T, recent)
        a, _ = policy.act(s)
        grid[t] = a
        states.append(s); actions.append(a)
        prev = a
        recent = 0.6 * recent + 0.4 * float(a.mean())               # running energy (for the arc)
    return grid, np.array(states), np.array(actions)


# ----------------------------------------------------------------------------- #
#  Metrics — does the policy reproduce the DJ's grammar without being told it?
# ----------------------------------------------------------------------------- #
def grid_stats(grids):
    G = np.stack(grids)                       # (N,T,NE)
    active = G.mean(axis=(0, 1))              # per-element active fraction
    # mean first-on step per element
    entry = []
    for ei in range(NE):
        firsts = []
        for g in G:
            on = np.where(g[:, ei] > 0.5)[0]
            if len(on): firsts.append(on[0])
        entry.append(np.mean(firsts) if firsts else G.shape[1])
    # breakdown signature rate: kick off while bassline+drone on
    ki, bi, di = ELEMENTS.index("kick+bass"), ELEMENTS.index("bassline"), ELEMENTS.index("drone")
    bd = ((G[:, :, ki] < 0.5) & (G[:, :, bi] > 0.5) & (G[:, :, di] > 0.5)).mean()
    return active, np.array(entry), bd


def print_grid(grid, title):
    print(f"\n{title}")
    T = len(grid)
    hdr = "".join(str(int(i * 10 / T)) if i % max(1, T // 10) == 0 else " " for i in range(T))
    print(f"{'':>10s} |{hdr}")
    for ei, e in enumerate(ELEMENTS):
        row = "".join("█" if grid[t, ei] > 0.5 else "·" for t in range(T))
        print(f"{e:>10s} |{row}")


def stat_table(name, active, entry, bd, T):
    order = [ELEMENTS[i] for i in np.argsort(entry)]
    print(f"  [{name}] active-frac: " +
          " ".join(f"{e[:4]}={active[i]:.2f}" for i, e in enumerate(ELEMENTS)))
    print(f"  [{name}] entry order (first->last): {' -> '.join(order)}")
    print(f"  [{name}] breakdown-signature rate: {bd:.3f}")


# ----------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", help="grammar.json (synthetic teacher)")
    ap.add_argument("--real-dir", help="dir of real per-track analysis JSONs (real teacher)")
    ap.add_argument("--T", type=int, default=48, help="arrangement steps (a track)")
    ap.add_argument("--iters", type=int, default=400)
    ap.add_argument("--batch", type=int, default=32, help="tracks per iter")
    ap.add_argument("--hid", type=int, default=64)
    ap.add_argument("--gamma", type=float, default=0.96)
    ap.add_argument("--arc-weight", type=float, default=6.0,
                    help="reward weight for matching the DJ's energy arc (0 = pure GAIL, flat)")
    ap.add_argument("--bd-weight", type=float, default=0.0,
                    help="reward weight for producing the DJ's breakdown PATTERN at its rate (0 = off)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--emit-grid", default=None,
                    help="after training, save the policy's composed arrangement (probs T x 6) for the audio renderer")
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    if a.real_dir:
        teacher = RealTeacher(a.real_dir, a.T)
        src = f"REAL grids ({a.real_dir})"
    elif a.grammar:
        teacher = Teacher(json.load(open(a.grammar)), a.T)
        src = f"synthetic teacher ({a.grammar})"
    else:
        raise SystemExit("pass --real-dir or --grammar")
    disc = Discriminator(WIN * NE + 2 * WIN + 1, a.hid, rng)
    policy = Policy(NE + 4, a.hid, rng)

    # the DJ's real per-step ENERGY arc + BREAKDOWN rate — the reward targets
    _samp = [teacher.sample(rng) for _ in range(300)]
    dj_energy = np.mean(_samp, axis=0).mean(axis=1)                        # (T,)
    dj_bd_rate = float(np.mean([bd_flag(g).mean() for g in _samp]))        # scalar breakdown rate

    print(f"=== Arrangement-RL (AMP/GAIL + arc reward) — DJ: {teacher.dj} ===")
    print(f"source={src}")
    print(f"track={a.T} steps (~{teacher.track_s/60:.0f} min real) · "
          f"batch={a.batch} · iters={a.iters} · WIN={WIN} · arc_weight={a.arc_weight} · bd_weight={a.bd_weight}")
    print(f"DJ energy arc: " + "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v * 8))] for v in dj_energy) +
          f"   (DJ breakdown rate={dj_bd_rate:.3f})")

    # --- teacher reference stats ---
    real0 = [teacher.sample(rng) for _ in range(200)]
    ta, te, tbd = grid_stats(real0)
    print("\n--- TEACHER (target grammar, from grammar.json) ---")
    stat_table("teacher", ta, te, tbd, a.T)
    print_grid(real0[0], "teacher sample arrangement:")

    # --- policy BEFORE training ---
    pre = [rollout(policy, a.T)[0] for _ in range(200)]
    pa, pe, pbd = grid_stats(pre)
    print("\n--- POLICY @ init (random) ---")
    stat_table("init", pa, pe, pbd, a.T)

    # --- GAIL / AMP training loop ---
    baseline = 0.0
    for it in range(a.iters):
        # 1) rollouts
        grids, S, A = [], [], []
        rewards_win = []
        for _ in range(a.batch):
            g, s, act = rollout(policy, a.T)
            grids.append(g); S.append(s); A.append(act)
        # 2) discriminator update: real=1, policy=0  (window samples)
        real = [teacher.sample(rng) for _ in range(a.batch)]
        Xr = np.array([disc_window(g, t) for g in real for t in range(a.T)])
        Xf = np.array([disc_window(g, t) for g in grids for t in range(a.T)])
        Xd = np.vstack([Xr, Xf])
        yd = np.concatenate([np.ones(len(Xr)), np.zeros(len(Xf))])
        for _ in range(3):
            perm = rng.permutation(len(Xd))
            dloss = disc.train(Xd[perm], yd[perm])
        # 3) rewards from D + discounted return-to-go
        all_states, all_acts, all_adv = [], [], []
        ep_returns = []
        for g, s, act in zip(grids, S, A):
            gail = np.array([disc.reward(disc_window(g, t)[None])[0] for t in range(a.T)])
            e = g.mean(axis=1)                                   # policy energy per step
            arc = -a.arc_weight * (e - dj_energy) ** 2           # match the DJ's rise-and-fall
            r = gail + arc
            if a.bd_weight > 0:                                  # learn the DJ's breakdown PATTERN
                pol_bd = float(bd_flag(g).mean())
                # reward breakdowns up to the DJ's rate; penalize over-breaking
                bd_r = a.bd_weight * (min(pol_bd, dj_bd_rate) - 2.0 * max(0.0, pol_bd - dj_bd_rate))
                r = r + bd_r
            ret = np.zeros(a.T)
            acc = 0.0
            for t in reversed(range(a.T)):
                acc = r[t] + a.gamma * acc
                ret[t] = acc
            ep_returns.append(ret.mean())
            all_states.append(s); all_acts.append(act); all_adv.append(ret)
        Sflat = np.vstack(all_states)
        Aflat = np.vstack(all_acts)
        ADV = np.concatenate(all_adv)
        baseline = 0.9 * baseline + 0.1 * ADV.mean()
        ADVn = (ADV - baseline)
        ADVn = ADVn / (ADV.std() + 1e-6)
        policy.update(Sflat, Aflat, ADVn)

        if it % max(1, a.iters // 10) == 0 or it == a.iters - 1:
            meanD_real = disc.forward(Xr).mean()
            meanD_fake = disc.forward(Xf).mean()
            print(f"  it {it:4d} | Dloss {dloss:.3f} | D(real) {meanD_real:.2f} "
                  f"D(fake) {meanD_fake:.2f} | ep_ret {np.mean(ep_returns):.2f}")

    # --- policy AFTER training ---
    post = [rollout(policy, a.T)[0] for _ in range(200)]
    qa, qe, qbd = grid_stats(post)
    print("\n--- POLICY @ trained ---")
    stat_table("trained", qa, qe, qbd, a.T)
    print_grid(post[0], "trained-policy sample arrangement:")

    # --- scorecard: how close did the policy get to the DJ's grammar? ---
    print("\n=== DID THE POLICY REDISCOVER THE GRAMMAR? ===")
    af_err0 = np.abs(pa - ta).mean(); af_err1 = np.abs(qa - ta).mean()
    print(f"active-fraction L1 error   : init {af_err0:.3f}  ->  trained {af_err1:.3f}")
    to = [ELEMENTS[i] for i in np.argsort(te)]
    qo = [ELEMENTS[i] for i in np.argsort(qe)]
    print(f"teacher entry order        : {' -> '.join(to)}")
    print(f"trained-policy entry order : {' -> '.join(qo)}")
    print(f"breakdown-signature (teacher {tbd:.3f}) : init {pbd:.3f} -> trained {qbd:.3f}")
    # --- energy ARC: did the policy learn the DJ's rise-and-fall? ---
    pol_e0 = np.stack(pre).mean(axis=0).mean(axis=1)
    pol_e1 = np.stack(post).mean(axis=0).mean(axis=1)
    def corr(x, y): return float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 1e-6 and np.std(y) > 1e-6 else 0.0
    print(f"energy-arc corr vs DJ       : init {corr(pol_e0, dj_energy):+.2f}  ->  trained {corr(pol_e1, dj_energy):+.2f}")
    print("DJ  energy arc :", "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v * 8))] for v in dj_energy))
    print("pol energy arc :", "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v * 8))] for v in pol_e1))

    if a.emit_grid:
        # the policy's EXPECTED arrangement = mean over many stochastic rollouts.
        # A single deterministic rollout saturates to "all on" (densities are >0.5);
        # averaging stochastic rollouts recovers the temporal profile — the intro is
        # sparse, hats/stab fill in late (the learned entry timing) — as smooth
        # per-step occupancy in [0,1], which the renderer uses as gain automation.
        NR = 128
        acc = np.zeros((a.T, NE), np.float32)
        for _ in range(NR):
            g, _, _ = rollout(policy, a.T)
            acc += g
        occ = acc / NR
        json.dump({"dj": teacher.dj, "T": a.T, "elements": ELEMENTS,
                   "probs": occ.tolist()}, open(a.emit_grid, "w"))
        print(f"\nemitted arrangement grid ({NR} rollouts avg) -> {a.emit_grid}")
        print("\ncomposed arrangement (occupancy, darker=more present):")
        print(f"{'':>10s} |{''.join(str(int(i*10/a.T)) if i%max(1,a.T//10)==0 else ' ' for i in range(a.T))}")
        for ei, e in enumerate(ELEMENTS):
            print(f"{e:>10s} |{''.join(LV[min(8,int(occ[t,ei]*8))] for t in range(a.T))}")

    if a.out:
        json.dump({"dj": teacher.dj, "T": a.T,
                   "teacher": {"active": ta.tolist(), "entry": te.tolist(), "bd": float(tbd)},
                   "trained": {"active": qa.tolist(), "entry": qe.tolist(), "bd": float(qbd)},
                   "elements": ELEMENTS}, open(a.out, "w"), indent=2)
        print(f"\nsaved -> {a.out}")


if __name__ == "__main__":
    main()
