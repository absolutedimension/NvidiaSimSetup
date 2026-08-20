#!/usr/bin/env python3
"""Repair the Hindi of already-generated blood-relation questions.

English has one word where Hindi has two. A "niece" is भतीजी through a brother and भांजी through a
sister; an "uncle" is चाचा on the father's side and मामा on the mother's. reasoninggen mapped the
English relation to a single Hindi word, so 4 of its 20 kin routes printed the wrong Hindi answer
beside a perfectly correct English one.

Nothing we had could see it. The numbers agree across languages, the option counts agree, the
script is clean Devanagari, and the English is right — so every cross-language check passes. It
surfaced only when a model was asked to solve the HINDI version blind and answered that Neha, the
daughter of Meena's sister, is her भांजी and not the भतीजी the paper offered.

reasoninggen.py is fixed for everything generated from now on. This patches the questions already
drawn into a frozen paper, which cannot be regenerated without changing the paper.

Idempotent: rerunning it finds nothing to do.
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from qbank.reasoninggen import _KIN_HI, _KIN  # noqa: E402

# "Neha is the daughter of Anjali, and Anjali is the sister of Meena. How is Neha related to Meena?"
STEM = re.compile(r"is the (\w+) of \w+, and \w+ is the (\w+) of ", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.path.join(HERE, "drop", "bssc", "REASONING_GEN.json"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rows = json.load(io.open(a.file, encoding="utf-8"))
    fixed = checked = 0
    for q in rows:
        if (q.get("concept") or "") != "Blood Relations":
            continue
        m = STEM.search(q.get("stem") or "")
        if not m:
            continue
        route = (m.group(1).lower(), m.group(2).lower())
        want = _KIN_HI.get(route)
        if not want:
            continue
        checked += 1
        if _KIN.get(route, "").capitalize() != str(q.get("correct_answer_text") or
                                                   _correct_text(q)).capitalize():
            pass                                    # English answer text is informational only
        opts_hi = q.get("options_hi") or []
        opts = q.get("options") or []
        idx = next((i for i, o in enumerate(opts)
                    if o.get("label") == q.get("correct_answer")), None)
        if idx is None or idx >= len(opts_hi):
            continue
        cur = str(opts_hi[idx].get("text", "")).strip()
        if cur == want:
            continue
        others = {str(o.get("text", "")).strip() for i, o in enumerate(opts_hi) if i != idx}
        if want in others:
            print(f"  ! {q['stem'][:60]} — '{want}' is already a distractor; skipping "
                  f"rather than creating two identical options")
            continue
        print(f"  ✓ {q['stem'][:64]}\n      Hindi answer {cur!r} -> {want!r}  (route {route})")
        opts_hi[idx]["text"] = want
        if q.get("solution_hi"):
            q["solution_hi"] = q["solution_hi"].replace(cur, want)
        fixed += 1

    if fixed and not a.dry_run:
        json.dump(rows, io.open(a.file, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  {checked} blood-relation questions on a route where Hindi distinguishes; "
          f"{fixed} corrected")
    if a.dry_run:
        print("  (dry run — nothing written)")


def _correct_text(q):
    return next((o.get("text") for o in q.get("options") or []
                 if o.get("label") == q.get("correct_answer")), "")


if __name__ == "__main__":
    main()
