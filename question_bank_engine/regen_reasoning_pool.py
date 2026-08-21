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
# The paper's OWN identity function, not a copy of it. This file used to inline its own version of
# gen_sig; the two then drifted, and a pool deduplicated by one rule was drawn from by another.
from build_onestep_paper import gen_sig      # noqa: E402
from qbank.item_forms import FORMS           # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "drop", "bssc", "REASONING_GEN.json"))
    ap.add_argument("--per", type=int, default=60, help="seeds per builder per difficulty")
    a = ap.parse_args()

    rows, seen, by_diff, by_form, gated = [], set(), Counter(), Counter(), Counter()
    for chap, fns in R._CHAP_BUILDERS.items():
        for fn in fns:
            for diff in (1, 2, 3, 4):
                for seed in range(a.per):
                    try:
                        built = fn(random.Random(seed), diff)
                    except Exception:
                        continue
                    if not built:
                        continue
                    # Emit the DIRECT form, then re-ask the same solved item through every form in
                    # item_forms. A form never recomputes an answer — it re-uses the one the
                    # builder produced along with its named mistakes — so variety grows without
                    # growing the surface on which an arithmetic error could appear.
                    variants = [(built, "direct")]
                    for fname, form in FORMS.items():
                        try:
                            alt = form(built, random.Random(seed * 7919 + diff))
                        except Exception:
                            alt = None
                        if alt:
                            variants.append((alt, fname))
                    for b_v, fname in variants:
                        _emit(b_v, fname, chap, diff, seed, rows, seen, by_diff, by_form, gated)

    json.dump(rows, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} distinct reasoning questions -> {os.path.basename(a.out)}")
    for d in sorted(by_diff):
        print(f"  difficulty {d}: {by_diff[d]:5d}")
    for f, n in by_form.most_common():
        print(f"  form {f:12s}: {n:5d}")
    for why, n in gated.most_common():
        print(f"  gated out: {n:4d}  {why}")


def _emit(built, fname, chap, diff, seed, rows, seen, by_diff, by_form, gated):
    """One built item -> one pool row, after the same gates the paper applies at draw time."""
    try:
        q = R._make_question(built, random.Random(seed), {"chapter": chap, "dmax": diff})
    except Exception:
        return
    row = {"stem": q.stem, "stem_hi": q.stem_hi,
           "options": q.options, "options_hi": q.options_hi,
           "correct_answer": q.correct_answer,
           "solution": q.solution, "solution_hi": q.solution_hi,
           "concept": q.concept, "chapter": chap, "form": fname,
           "difficulty": diff, "generated": True,
           "exam": "BSSC", "source": "reasoninggen"}
    # the same gates the paper applies, so the pool never carries a question the builder would
    # refuse at draw time
    if not numbers_agree(row):
        gated["Hindi dropped part of the question"] += 1
        return
    if analogy_ambiguous(row) or odd_one_out_ambiguous(row):
        gated["two defensible answers both on offer"] += 1
        return
    sig = gen_sig(row)
    if sig in seen:
        return
    seen.add(sig)
    rows.append(row)
    by_diff[diff] += 1
    by_form[fname] += 1


if __name__ == "__main__":
    main()
