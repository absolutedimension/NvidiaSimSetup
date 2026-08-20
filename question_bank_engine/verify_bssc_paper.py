#!/usr/bin/env python3
"""Per-paper sanity check for an extracted BSSC paper, plus a page rendered for the eye.

The skill's gotcha #12 exists because a duplicate-language bug was invisible in the JSON and
obvious the moment a page was rendered and looked at. So this prints the machine checks AND drops
a PNG of a source page next to the questions extracted from it, for a human (or a vision-capable
agent) to compare line by line.

Machine checks:
  - numbering continuous, no gaps, no duplicates
  - every question has options, and 4 of them
  - English servable count (stem + options present)
  - keyed count, and whether the key letter is one of the printed labels
  - Hindi capture rate and whether it is quarantined or promoted

Usage:
    python3 verify_bssc_paper.py ~/bssc_in/GK1_KEYED.json [--pdf ~/bssc_in/GK1.PDF] [--page 10]
"""
import argparse
import io
import json
import os
from collections import Counter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyed")
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--page", type=int, default=None, help="source PDF page to render (1-based)")
    ap.add_argument("--dpi", type=int, default=130)
    a = ap.parse_args()

    qs = json.load(io.open(a.keyed, encoding="utf-8"))
    name = os.path.basename(a.keyed)
    nums = [q.get("number") for q in qs if isinstance(q.get("number"), int)]
    dupes = [n for n, c in Counter(nums).items() if c > 1]
    gaps = [n for n in range(min(nums), max(nums) + 1) if n not in set(nums)] if nums else []
    servable = [q for q in qs if q.get("stem") and q.get("options")]
    keyed = [q for q in qs if q.get("correct_answer")]
    bad_key = [q["number"] for q in keyed
               if q.get("options") and q["correct_answer"] not in [o["label"] for o in q["options"]]]
    optcount = Counter(len(q.get("options") or []) for q in qs)
    hi_q = sum(1 for q in qs if q.get("stem_hi_unverified"))
    hi_p = sum(1 for q in qs if q.get("stem_hi"))
    empty_stem = [q["number"] for q in qs if not q.get("stem")]

    ok = lambda b: "OK  " if b else "FAIL"
    print(f"=== {name} — {len(qs)} questions ===")
    print(f" {ok(not gaps)} numbering {min(nums) if nums else '-'}..{max(nums) if nums else '-'}"
          f"   gaps: {gaps or 'none'}")
    print(f" {ok(not dupes)} duplicates: {dupes or 'none'}")
    print(f" {ok(len(servable)==len(qs))} English servable: {len(servable)}/{len(qs)}"
          f"   (missing stem: {empty_stem[:12] or 'none'})")
    print(f" {ok(len(keyed)==len(qs))} officially keyed : {len(keyed)}/{len(qs)}")
    print(f" {ok(not bad_key)} key letter matches a printed option: "
          f"{'yes' if not bad_key else 'NO for ' + str(bad_key[:12])}")
    print(f"      option counts: {dict(sorted(optcount.items()))}")
    print(f"      Hindi: {hi_p} promoted, {hi_q} quarantined (unverified)")

    if a.pdf and a.page:
        import pymupdf
        d = pymupdf.open(os.path.expanduser(a.pdf))
        out = os.path.splitext(a.keyed)[0] + f"_verify_p{a.page}.png"
        d[a.page - 1].get_pixmap(dpi=a.dpi).save(out)
        print(f"\n rendered source page {a.page} -> {out}")
        onpage = [q for q in qs if q.get("page") == a.page or q.get("page_hi") == a.page]
        print(f" {len(onpage)} extracted questions reference that page:")
        for q in sorted(onpage, key=lambda x: x["number"])[:10]:
            print(f"   Q{q['number']:>3} [{q.get('correct_answer') or '?'}] {q.get('stem','')[:88]}")
            for o in (q.get("options") or [])[:4]:
                print(f"        ({o['label']}) {o['text'][:70]}")


if __name__ == "__main__":
    main()
