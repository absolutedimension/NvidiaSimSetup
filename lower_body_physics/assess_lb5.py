#!/usr/bin/env python3
"""Assess LB5 training results by reading TensorBoard event files.

Usage (inside isaaclab container):
    ./isaaclab.sh -p /workspace/isaaclab/assess_lb5.py

Reads the LB5 (3000-iter) and optionally LB4 (500-iter) runs and prints
a comparative summary for the LB5 subjective gate decision.
"""

import os
import json

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

LB5_DIR = "/workspace/isaaclab/logs/skrl/humanoid_amp_lower_body/2026-05-24_15-41-42_amp_torch"
# LB4 may have been moved; try both locations
LB4_CANDIDATES = [
    "/workspace/isaaclab/logs/skrl/humanoid_amp_lower_body/2026-05-24_15-33-46_amp_torch",
    "/home/ubuntu/lb4_500iter_v2_final",
]


def read_run(run_dir: str) -> dict:
    """Read key scalar metrics from a TensorBoard run directory."""
    ea = EventAccumulator(run_dir)
    ea.Reload()
    tags = ea.Tags().get("scalars", [])

    result = {}
    for tag in sorted(tags):
        events = ea.Scalars(tag)
        if not events:
            continue
        values = [e.value for e in events]
        result[tag] = {
            "first": events[0].value,
            "last": events[-1].value,
            "min": min(values),
            "max": max(values),
            "n_points": len(events),
            "first_step": events[0].step,
            "last_step": events[-1].step,
            "wall_time_min": (events[-1].wall_time - events[0].wall_time) / 60.0,
        }

    return result


def print_summary(name: str, metrics: dict):
    """Print a formatted summary of a training run."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    steps = 0
    wall_min = 0
    for tag, m in metrics.items():
        steps = max(steps, m["last_step"])
        wall_min = max(wall_min, m["wall_time_min"])

    iters = steps // 16  # rollouts=16
    print(f"  Steps: {steps}  |  Iterations: {iters}  |  Wall time: {wall_min:.1f} min")
    print()

    key_metrics = [
        ("Reward / Total reward (mean)", "Mean Total Reward", "{:.2f}"),
        ("Reward / Total reward (max)", "Max Total Reward", "{:.2f}"),
        ("Reward / Instantaneous reward (mean)", "Mean Inst. Reward", "{:.4f}"),
        ("Episode / Total timesteps (mean)", "Mean Episode Length", "{:.1f}"),
        ("Episode / Total timesteps (max)", "Max Episode Length", "{:.0f}"),
        ("Loss / Discriminator loss", "Discriminator Loss", "{:.4f}"),
        ("Loss / Value loss", "Value Loss", "{:.4f}"),
        ("Loss / Policy loss", "Policy Loss", "{:.4f}"),
    ]

    print(f"  {'Metric':<30s} {'Start':>10s} {'End':>10s} {'Best':>10s}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10}")

    for tag, label, fmt in key_metrics:
        if tag not in metrics:
            continue
        m = metrics[tag]
        start = fmt.format(m["first"])
        end = fmt.format(m["last"])
        # "Best" depends on metric type
        if "loss" in tag.lower() or "Loss" in tag:
            best = fmt.format(m["min"])
        else:
            best = fmt.format(m["max"])
        print(f"  {label:<30s} {start:>10s} {end:>10s} {best:>10s}")

    # Derived: mean episode duration in seconds (at 60 Hz control)
    ep_tag = "Episode / Total timesteps (mean)"
    if ep_tag in metrics:
        ep_mean_end = metrics[ep_tag]["last"]
        ep_max_end = metrics["Episode / Total timesteps (max)"]["last"]
        print(f"\n  Mean upright duration: {ep_mean_end/60:.1f}s")
        print(f"  Max upright duration:  {ep_max_end/60:.1f}s (episode limit = 10.0s)")
        if ep_max_end >= 595:
            print(f"  >> Some envs reach full 10s episode! <<")


def compare(lb4: dict, lb5: dict):
    """Print a side-by-side comparison."""
    print(f"\n{'='*60}")
    print(f"  LB4 vs LB5 Comparison")
    print(f"{'='*60}")

    comparisons = [
        ("Reward / Total reward (mean)", "Mean Reward", "last"),
        ("Reward / Total reward (max)", "Max Reward", "last"),
        ("Episode / Total timesteps (mean)", "Mean Ep. Len", "last"),
        ("Episode / Total timesteps (max)", "Max Ep. Len", "last"),
        ("Loss / Discriminator loss", "Disc. Loss", "last"),
    ]

    print(f"  {'Metric':<25s} {'LB4':>10s} {'LB5':>10s} {'Change':>10s}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")

    for tag, label, which in comparisons:
        if tag not in lb4 or tag not in lb5:
            continue
        v4 = lb4[tag][which]
        v5 = lb5[tag][which]
        delta = v5 - v4
        pct = 100 * delta / abs(v4) if v4 != 0 else 0
        print(f"  {label:<25s} {v4:>10.2f} {v5:>10.2f} {delta:>+8.2f} ({pct:+.0f}%)")

    # Gate recommendation
    ep_mean = lb5.get("Episode / Total timesteps (mean)", {}).get("last", 0)
    ep_max = lb5.get("Episode / Total timesteps (max)", {}).get("last", 0)
    reward_mean = lb5.get("Reward / Total reward (mean)", {}).get("last", 0)

    print(f"\n  --- Gate Assessment ---")
    if ep_mean > 150:
        print(f"  [PASS] Mean episode {ep_mean:.0f} > 150 (>{ep_mean/60:.1f}s upright)")
    else:
        print(f"  [MARGINAL] Mean episode {ep_mean:.0f} <= 150 ({ep_mean/60:.1f}s upright)")

    if ep_max >= 595:
        print(f"  [PASS] Some envs reach full 10s episode")
    else:
        print(f"  [MARGINAL] Max episode {ep_max:.0f} < 595 (doesn't reach full episode)")

    if reward_mean > 20:
        print(f"  [PASS] Mean reward {reward_mean:.1f} > 20")
    else:
        print(f"  [MARGINAL] Mean reward {reward_mean:.1f} <= 20")

    disc_loss = lb5.get("Loss / Discriminator loss", {}).get("last", 999)
    if disc_loss < 1.5:
        print(f"  [PASS] Discriminator converged ({disc_loss:.3f} < 1.5)")
    else:
        print(f"  [MARGINAL] Discriminator still high ({disc_loss:.3f} >= 1.5)")


def main():
    # Read LB5
    if not os.path.isdir(LB5_DIR):
        print(f"ERROR: LB5 directory not found: {LB5_DIR}")
        return

    lb5 = read_run(LB5_DIR)
    print_summary("LB5 — 3000-iter Full AMP Training", lb5)

    # Try to read LB4 for comparison
    lb4 = None
    for lb4_dir in LB4_CANDIDATES:
        if os.path.isdir(lb4_dir):
            try:
                lb4 = read_run(lb4_dir)
                print_summary("LB4 — 500-iter Balance-Only Training", lb4)
                break
            except Exception as e:
                print(f"  (Could not read LB4 from {lb4_dir}: {e})")

    if lb4:
        compare(lb4, lb5)
    else:
        print("\n  (LB4 data not found — skipping comparison)")

    # Output JSON for programmatic consumption
    output = {
        "lb5": {tag: {"first": m["first"], "last": m["last"], "best_min": m["min"], "best_max": m["max"]}
                for tag, m in lb5.items()},
    }
    if lb4:
        output["lb4"] = {tag: {"first": m["first"], "last": m["last"]}
                         for tag, m in lb4.items()}

    json_path = "/tmp/lb5_assessment.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  JSON saved to {json_path}")


if __name__ == "__main__":
    main()
