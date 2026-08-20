#!/usr/bin/env python3
"""Regenerate REASONING_GEN.json across the difficulty range.

The pool the paper draws Part III from was generated before reasoninggen understood `diff`, so
every row in it is one fixed difficulty. That is why the build report has read "PART-III SHORT: 15
at difficulty 3" even after five builders learned to vary — the generator could produce hard
reasoning, and the pool it was being asked to draw from could not.

Each row is stamped with the difficulty it was BUILT at, which is what the paper's mix reads. Rows
are deduplicated by gen_sig, so a builder that ignores `diff` contributes once rather than four
identical times — eight of thirteen still do, and this makes that visible in the output rather than
silently quadrupling the easy end of the pool.

Usage:  python3 regen_reasoning_pool.py [--out drop/bssc/REASONING_GEN.json] [--per 60]
"""
import argparse
import io
import json
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "teacher_gtm"))
from qbank import reasoninggen as R          # noqa: E402
from paper_common import numbers_agree, analogy_ambiguous, odd_one_out_ambiguous  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "drop", "bssc", "REASONING_GEN.json"))
    ap.add_argument("--per", type=int, default=60, help="seeds per builder per difficulty")
    a = ap.parse_args()

    rows, seen, by_diff, gated = [], set(), Counter(), Counter()
    for chap, fns in R._CHAP_BUILDERS.items():
        for fn in fns:
            for diff in (1, 2, 3, 4):
                for seed in range(a.per):
                    try:
                        q = R._make_question(fn(random.Random(seed), diff),
                                             random.Random(seed),
                                             {"chapter": chap, "dmax": diff})
                    except Exception:
                        continue
                    row = {"stem": q.stem, "stem_hi": q.stem_hi,
                           "options": q.options, "options_hi": q.options_hi,
                           "correct_answer": q.correct_answer,
                           "solution": q.solution, "solution_hi": q.solution_hi,
                           "concept": q.concept, "chapter": chap,
                           "difficulty": diff, "generated": True,
                           "exam": "BSSC", "source": "reasoninggen"}
                    # the same gates the paper applies, so the pool never carries a question the
                    # builder would refuse at draw time
                    if not numbers_agree(row):
                        gated["Hindi dropped part of the question"] += 1
                        continue
                    if analogy_ambiguous(row) or odd_one_out_ambiguous(row):
                        gated["two defensible answers both on offer"] += 1
                        continue
                    sig = R._make_question.__module__ and (
                        str(row["concept"]) + "|" +
                        ",".join(re.findall(r"\d+", row["stem"])) + "|" +
                        "~".join(sorted(o["text"] for o in row["options"])))
                    if sig in seen:
                        continue
                    seen.add(sig)
                    rows.append(row)
                    by_diff[diff] += 1

    json.dump(rows, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} distinct reasoning questions -> {os.path.basename(a.out)}")
    for d in sorted(by_diff):
        print(f"  difficulty {d}: {by_diff[d]:5d}")
    for why, n in gated.most_common():
        print(f"  gated out: {n:4d}  {why}")


if __name__ == "__main__":
    main()
