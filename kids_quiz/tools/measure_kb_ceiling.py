#!/usr/bin/env python3
"""measure_kb_ceiling.py — how many DISTINCT questions can each KB actually produce?

The landing page claims a number ("over N different questions per subject"). This is the script
that number must come from. It asks every KB for `--target` distinct items; the generator dedups
by (type, payload) signature and gives up after a stall streak, so "delivered == target" means the
real ceiling is at or above the target, and anything less is the true ceiling.

    python3 kids_quiz/tools/measure_kb_ceiling.py            # 100k target (the shipped claim)
    python3 kids_quiz/tools/measure_kb_ceiling.py --target 250000

If any KB comes back SHORT, lower MIN_QUESTIONS_PER_SUBJECT in lms/app/kids_worksheet.py to the
smallest number every KB still delivers — never leave the claim above the measured floor.
"""
import argparse
import glob
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kb_engine as KB          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=100_000)
    ap.add_argument("--kb", default="", help="measure just one KB (e.g. evs_class3)")
    a = ap.parse_args()

    names = ([a.kb] if a.kb else
             [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(os.path.dirname(HERE), "kb", "*.json")))])
    short = []
    print(f"{'KB':26} {'distinct':>10} {'target':>10} {'sec':>6}  verdict")
    for name in names:
        kb = KB.load_kb(name)
        t = time.time()
        got = len(KB.generate(kb, a.target, seed=11))
        dt = time.time() - t
        ok = got >= a.target
        if not ok:
            short.append((name, got))
        print(f"{name:26} {got:>10,} {a.target:>10,} {dt:>6.1f}  {'ok' if ok else 'SHORT — this is the ceiling'}")

    print()
    if short:
        floor = min(g for _, g in short)
        print(f"FLOOR = {floor:,} — set MIN_QUESTIONS_PER_SUBJECT to this (or lower) and fix the copy.")
        return 1
    print(f"Every KB delivered {a.target:,} distinct questions. Claiming up to {a.target:,} per subject is honest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
