#!/usr/bin/env python3
"""Replace machine-read answer keys with the ones transcribed by eye from the commission's pages.

WHY THIS EXISTS. Vision cannot read these answer keys reliably. Measured against a key I
transcribed by hand from GK1.PDF page 29, reading the page whole put 39 of 100 letters WRONG.
Cropping the grid into tiles cut the wrong answers to 9 but then skipped 19 rows, and a 3-vote
majority over tiles still left 10 wrong and 25 missing. None of that is good enough for a claim
like "the commission's own answer key", which is not a claim you can walk back once an institute
has handed the paper to students.

The cause is the same one that garbles the Devanagari: the vision API downscales the image, and
the keys for Advertisement 0111 (GK, Maths, Hindi) are HANDWRITTEN, so an 'A' and a 'B' end up a
few pixels apart. The typeset keys read perfectly — a 50-answer check of the live One Step paper's
key (Field Assistant 03/25) matched 50/50 — so only the handwritten ones ever needed a human, but
all of them are transcribed here so the whole set has one provenance.

This script overwrites `correct_answer` from VERIFIED_KEYS.json and records the provenance on each
question, so nothing downstream has to guess where an answer came from.
"""
import argparse
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KEYS = os.path.join(HERE, "drop", "bssc", "VERIFIED_KEYS.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/bssc_in"))
    ap.add_argument("--keys", default=DEFAULT_KEYS)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    keys = json.load(io.open(a.keys, encoding="utf-8"))
    keys = {k: v for k, v in keys.items() if not k.startswith("_")}
    print(f"{len(keys)} verified keys loaded from {a.keys}\n")

    total_q = total_keyed = total_changed = 0
    for stem, spec in sorted(keys.items()):
        path = os.path.join(a.dir, stem + "_KEYED.json")
        if not os.path.exists(path):
            print(f"  {stem:28s} SKIP — {os.path.basename(path)} not found yet")
            continue
        qs = json.load(io.open(path, encoding="utf-8"))
        key = {int(k): v for k, v in spec["key"].items()}
        keyed = changed = mislabelled = 0
        for q in qs:
            n = q.get("number")
            ans = key.get(n) if isinstance(n, int) else None
            if not ans:
                continue
            labels = [o.get("label") for o in q.get("options") or []]
            if labels and ans not in labels:
                # the option the key points at was not captured (usually a 4th option lost at a
                # band edge). Storing the letter anyway would point at nothing — record and skip.
                mislabelled += 1
                q["key_letter_unmatched"] = ans
                continue
            if q.get("correct_answer") != ans:
                changed += 1
            q["correct_answer"] = ans
            q["answer_source"] = ("official key, transcribed by hand (handwritten original)"
                                  if spec.get("handwritten")
                                  else "official key, transcribed by hand (typeset original)")
            q["exam_advertisement"] = spec.get("exam")
            keyed += 1
        if not a.dry_run:
            json.dump(qs, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        flag = "handwritten" if spec.get("handwritten") else "typeset"
        print(f"  {stem:28s} {len(qs):4d} q | keyed {keyed:4d} | corrected {changed:4d} "
              f"| unmatched option {mislabelled:3d} | {flag}")
        total_q += len(qs); total_keyed += keyed; total_changed += changed

    print(f"\n  TOTAL {total_q} questions, {total_keyed} carrying a verified official answer, "
          f"{total_changed} letters corrected against the machine read")
    if a.dry_run:
        print("  (dry run — nothing written)")


if __name__ == "__main__":
    main()
