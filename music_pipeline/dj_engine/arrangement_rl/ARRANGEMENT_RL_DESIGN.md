# Arrangement-RL — learning a DJ's arrangement by adversarial imitation (AMP/GAIL)

**Status: v15 LOCKED as reference (2026-07-19).** See `REFERENCE_v15.md` for the frozen artifact +
exact reproduction recipe. Runs locally on the Mac, pure numpy, ~60-90 s/DJ. Proven on Burmeister
(+ Goa Gil grids loaded). This is the RL layer of the two-layer music engine (sound layer =
ACE-Step/synth; arrangement layer = this).

**Reference track:** `REFERENCE_burmeister_v15.mp3` — critic 8.6/10, human-ear approved. Composed by
the RL policy (learned densities/entry-order/energy-arc) + authored `--structure` (breakdowns/drops)
+ clean synthesized low end + kick-locked bass + critic verified.

## The idea

Composing an arrangement is a **sequential decision problem**, so it's an RL problem — the
same shape as the drone policy and the AMP dance policy:

| | Isaac Lab AMP (dance) | Arrangement-RL (this) |
|---|---|---|
| state | character pose + phase | active element mask + position in track |
| action | joint targets | which of the 6 elements are on next |
| reward | discriminator: "real motion vs generated" | discriminator: "real DJ arrangement vs generated" |
| algorithm | PPO + AMP discriminator | REINFORCE + GAIL discriminator |

**No rules are hand-coded.** We never tell the policy "hats enter last" or "drop the kick in a
breakdown." A discriminator learns to tell real DJ grids from the policy's grids, and its score
IS the reward. The policy must *rediscover* the DJ's grammar to fool it.

## Data

- 6 elements (sub / kick+bass / bassline / drone / stab / hats), binary on/off per step, 48 steps/track.
- "Real" grids = sampled from the learned `grammar.json` (entry order, active fraction, energy
  arc, breakdown signature). This is the **synthetic-teacher** idea: the grammar engine is the
  data factory, copyright-clean, unlimited samples.
- Scale-up swaps this for the **real per-track grids on EC2** (`dj_engine/<dj>/analysis/*.json`)
  — nothing else in the design changes.

## What the prototype proved

Starting from a random policy, purely by adversarial imitation:

**1. It matched each DJ's element density (active-fraction L1 error):**
- Burmeister: 0.295 → **0.037**
- Goa Gil: 0.355 → **0.024**

**2. The two DJs produced DIFFERENT policies — matching their real signatures:**
- Burmeister trained: `stab=0.81 hats=0.68` → sparser, hats used as the energy **lever** ✓
- Goa Gil trained: `stab=0.98 hats=0.86` → dense **wall of sound**, stabs almost always on ✓

This is the real measured difference between the two DJs, rediscovered by RL, not templated.

**3. Both nailed the key entry-order signature:** `bassline` first, `hats`/`stab` among the last
in — the "constant bed enters first, energy levers enter late" grammar.

**4. GAIL convergence:** D(real)≈0.52, D(fake)≈0.48 at the end — the discriminator can barely
tell them apart, the equilibrium signature of successful imitation.

## Trained on the REAL grids (2026-07-18, scale-up #1 done)

Pulled all 33 real per-track grids from EC2 (`dj_engine/<dj>/analysis/*.json`, 18 Burmeister +
15 Goa Gil) → `RealTeacher` resamples each to 48 steps, thresholds at 0.35. Same RL loop.
Run: `python3 arrangement_rl.py --real-dir ../burmeister/analysis --iters 400 --seed 1`

| | Burmeister (real) | Goa Gil (real) |
|---|---|---|
| active-frac L1 error | 0.308 → **0.049** | 0.371 → **0.049** |
| entry order (first 2) | `bassline → kick+bass` ✓✓ (exact) | `bassline → kick+bass` ✓✓ (exact) |
| trained density | hats=0.66 stab=0.86 (sparser) | hats=0.94 stab=0.97 (dense wall) |

- The **DJ contrast survives on real data**: Goa Gil's policy is a dense wall (everything ~0.95+),
  Burmeister's keeps hats/stab lower — matching the real signatures.
- On real grids the discriminator keeps a small edge (D(real)≈0.57 vs 0.43) instead of collapsing
  to 0.5 — real tracks have per-track texture the policy hasn't fully captured. Honest and expected;
  more capacity (torch/PPO) closes it.
- **Finding:** real breakdown-signature (0.026 Burmeister / 0.014 Goa Gil) is much LOWER than the
  synthetic reconstruction implied (0.068) — the aggregated grammar over-counted breakdowns. Real
  grids also show bassline dropping out near track ends, texture the aggregate missed. Training on
  real grids is strictly more faithful.

## Grid → audio (2026-07-18, scale-up #3 done)

Closed the loop end-to-end: the trained policy composes an arrangement, which is rendered
to a real track over the DJ's stems.
- `arrangement_rl.py --emit-grid X.json` saves the policy's **expected arrangement** = mean of
  128 stochastic rollouts (a single deterministic rollout saturates to "all on"; averaging
  recovers the temporal profile — sparse intro, hats/stab fill in late).
- `render_from_grid.py` (runs on EC2 audio venv) maps each of the 6 element tracks onto a stem
  (`kick+bass→kick, bassline→bass, drone, stab, hats`; `sub`=synth sat-sine) and uses each grid
  column as that stem's **gain automation** + sidechain duck + density-driven filter-open.
- Output: `burmeister_rl_6min.mp3` — the structure you hear (intro sparseness, constant bed,
  hats staying sparsest) is the RL policy's, not a hand-authored arc.
- Faithful detail: the energy arc came out as a flat plateau — correct for Burmeister (his real
  grammar IS a ~0.75 plateau, not a drop-based track). A drop/breakdown would need reward
  shaping (limitation #1) — the hand-authored `grammar_generate_burmeister_stems.py` still owns
  the explosive drop arc; this path owns the *learned* structure.

Command:
```
python3 arrangement_rl.py --real-dir ../burmeister/analysis --iters 400 --emit-grid g.json
# on EC2:
render_from_grid.py --grid g.json --stems ~/dj_engine/burmeister/stems_fs --minutes 6 --bpm 123 --out t.wav
```

## Audio critic + the calibration lesson (2026-07-18)

`critique_track.py` = the machine half of the two-tier feedback loop (machine = fast/objective
in-the-loop reward; human ear = ground-truth taste). It reuses the same band-grid as
`dj_arrangement_analysis.py`, so the generated track is measured on the DJ's own scale, then
scores grammar-match + entry-order + dynamics + spectral + liveliness → verdict
(ship-it/needs-work/broken), same shape as the drone eval JSON.

**The calibration lesson (drone §17.10, replayed for audio):** the critic first flagged our
track "muddy, 91% bass" against a hardcoded ideal (L0.45). Before brightening the mix, we
measured a REAL Burmeister track: **L0.96/M0.04/H0.01** — hypnotic techno IS bass-dominant, and
our render (L0.90) was already *more* faithful than the "fixed" version. The flag was a false
positive from an uncalibrated target. **Fix = score spectral vs the DJ's real balance, not an
abstract ideal** (same principle as grammar_match). An uncalibrated critic optimizes toward the
wrong thing — always calibrate against ground truth before trusting a machine reward.

**v1 → v4 (fixing the two flagged issues):**
| | v1 | v4 |
|---|---|---|
| verdict | needs-work 6.0 | **ship-it 7.9** |
| spectral | 2.4 (bad target) | **9.7** (vs DJ balance) |
| hats density | 1.0 (never drops) | **0.61** (DJ = 0.62) ✓ |
| density-L1 | 0.175 | **0.113** |

- **Density fix (render-side):** `gate()` turns occupancy→presence so lever elements go truly
  silent in sparse sections (per-band normalization ignores mere volume, so an element must hit
  ~0 to read "off"). Fixed hats/stab. The bed (sub/kick/bass/drone) still reads 1.0 vs the DJ's
  0.82–0.94 — that's a POLICY limitation (flat occupancy, no learned dropouts), belongs to
  reward-shaping #4, NOT the renderer.
- **Muddy fix:** was a miscalibrated critic; corrected the critic + kept a faithful bass-forward mix.

Artifacts: `burmeister_rl_v4.mp3` (ship-it), `critique_track.py`, `*_verdict.json`.

## The two-tier loop closing (2026-07-18) — ear → machine

The human ear caught something the machine missed, and we folded it back into the machine:
- Machine said SHIP-IT 7.9 (v4). **Human ear: "background bass is hazing, not clear."**
- Diagnosed: measured real Burmeister low-band spectral flatness = **0.59**; our track = **0.687**
  (higher = noise-like/smeared = the "haze"). The ear was right; the critic had no metric for it.
- **Fixed the critic:** added a calibrated `clarity` score (low-<200Hz spectral flatness vs the
  DJ's 0.59) — now the machine catches "haze" going forward. This is the whole point of the
  two-tier loop: ear finds the gap → becomes a machine metric.
- **Fixed the render:** clean tonal synth-sub carries <95 Hz, smeared bass stem hp'd to 130 Hz
  (tonal low replaces noise-like low) + deep sidechain on sub/bass. Haze **0.687 → 0.627**
  (near the DJ's 0.59); clarity 6.0 → **8.3/10**. Artifact: `burmeister_rl_v6.mp3`.
- **Honest ceiling:** the residual 0.627 vs 0.59 gap is the **AI-generated + Demucs-separated
  stem smear** the skill documents — mixing tightens it but the real fix is better source stems
  (LoRA fine-tune / cleaner samples).

## #4 — policy LEARNS the arc (2026-07-19)

Reward-shaped the GAIL policy to compose dynamics itself (not the authored `--structure` layer):
- **Longer discriminator window** (WIN 4→10) + the **energy trajectory** over that window as
  input, so D can tell an arc-following track from a flat one.
- **Policy sees recent energy** (running mean) so it can shape build/drop/recover.
- **Energy-arc reward**: `-arc_weight * (policy_energy_t - dj_energy_t)^2`, where `dj_energy` is
  the DJ's measured per-step energy — pins rare dynamics that pure GAIL washes out. `--arc-weight`.

**Result (real Burmeister grids, arc-weight 15):**
- energy-arc correlation vs DJ: **-0.23 → +0.39** (was anti-correlated/flat, now tracks the DJ)
- the policy composed a **mid-track hats-dropout on its own** (a learned breakdown-ish section)
- captured the intro build; active-fraction L1 still 0.049

**The honest finding:** Burmeister's REAL energy arc is a near-flat plateau (`▄▆▆▆…▆▇▇▅`), so the
learned arc is **mild** — faithful imitation of a plateau DJ can't produce dramatic drops, because
he doesn't do them. `burmeister_rl_v14_learned_arc.mp3` = policy-composed dynamics (subtle).

**So the two arc sources are complementary, not competing:**
- **RL-learned arc** = the DJ's *natural* dynamics (mild for Burmeister). Faithful.
- **`--structure`** = *authored* drama beyond what the DJ does (the v13 breakdowns/drops).
- Best track = RL arrangement + `--structure` for the big moments (render the learned grid WITH
  `--structure`).

**Open extensions:** (a) a breakdown-PATTERN reward (kick-out/bass-in), not just energy, to learn
true breakdowns; (b) test the mechanism on Goa Gil (a more dynamic DJ → bigger learned arc);
(c) PPO+torch for a higher-capacity policy.

## Breakdown-pattern reward — the honest result (2026-07-19)

Added a breakdown PATTERN channel to the discriminator (kick-out/bass-in/drone-in flag over the
window) + a breakdown-RATE reward (`--bd-weight`: reward breakdowns up to the DJ's rate, penalize
excess). On real Burmeister:
- energy-arc correlation improved further (**+0.46**)
- the policy matched the breakdown RATE (init 0.138 random → 0.011, near the DJ's 0.023)
- **but no prominent/contiguous breakdown emerged in the composed arrangement.**

**Why (a real RL finding, not a bug):** Burmeister's breakdowns are rare (~2%) and at *varying*
positions (35–90% of the track). So (1) rate-matching yields scattered single-step kick-drops, not
*contiguous* breakdown sections; and (2) because real breakdowns sit at different positions each
track, they **wash out in the averaged arrangement** — for one to show in the mean occupancy the
policy would have to break down at the *same* spot every time, which the data doesn't teach. This is
the classic hard case: learning rare, structured, variably-placed events from limited data.

**Architectural takeaway (this validates the v15 design):** split the labour by what each method is
good at —
- **RL policy** → element densities, entry order, and the (mild) energy arc. Learns these well.
- **Authored `--structure`** → prominent, *placed* breakdowns/drops. Deterministic placement is
  exactly what RL-from-sparse-data can't give you.
- **v15 = RL arrangement + `--structure`** is therefore the right architecture, not a compromise.

**To make RL learn true breakdowns would need:** a contiguity/placement reward (cluster + fix
position), sequence-level modelling (not per-step Bernoulli), or a DJ whose breakdowns are frequent
and consistently placed. Research-grade; the authored layer is the practical answer today.

## Honest limitations (what the scale-up must fix)

1. **Rare events (breakdowns) are under-learned.** Breakdown-signature rate didn't improve
   (Burmeister 0.068 target, policy 0.032). GAIL reward is dominated by the constant bed; rare
   1.3/hr events get washed out. Fix: reward shaping / longer discriminator window / a
   breakdown-aware auxiliary reward, or train on real grids where breakdowns are explicit.
2. **Mid-order elements shuffle** (drone/sub/kick enter within ~30 s of each other in the real
   grammar → hard to separate at 48-step resolution). Higher time resolution fixes it.
3. **Symbolic only.** The policy outputs a grid, not audio. It drives the existing stem arranger
   (`grammar_generate_*_stems.py`) — the grid replaces the hand-authored section plan.
4. **Teacher = grammar stats, not raw grids yet.** Faithful to the aggregate but loses per-track
   texture. Real grids on EC2 are the upgrade.

## Scale-up path (in priority order)

1. **Real grids**: `scp` the EC2 `analysis/*.json` here (or run there) → replace `Teacher.sample`
   with a sampler over real per-track grids. Biggest fidelity win, smallest change.
2. **PPO + torch** on EC2 (A10G): swap REINFORCE→PPO (clipping, GAE) and the numpy MLPs→torch.
   Reuse the Isaac Lab / skrl AMP muscle memory. Handles finer resolution + bigger nets.
3. **Wire grid → audio**: feed the policy's grid into `grammar_generate_burmeister_stems.py` as
   the section plan → render a real track whose *structure* is RL-composed. Close the loop with
   an audio critic (the drone VLM-critic pattern, §17.9) scoring the rendered result.
4. **Reward shaping for rare events** + energy-arc auxiliary reward to fix limitation #1.

## Files

- `arrangement_rl.py` — the prototype (Teacher, Discriminator, Policy, GAIL loop, metrics).
- Run: `python3 arrangement_rl.py --grammar ../burmeister_grammar.json --iters 400 --seed 1`
- Swap `--grammar ../goa-gil/grammar.json` for the other DJ.
