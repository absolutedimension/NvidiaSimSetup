#!/usr/bin/env python3
"""Apply hand-read text corrections from drop/bssc/TEXT_CORRECTIONS.json to the extracted bank.

Companion to `apply_verified_keys.py`, and the same principle: where a human read the commission's
printed page and overrode the machine, the override lives in a file that names the source page and
the reason — not as an untraceable edit inside a 3 MB JSON. Re-run it after any re-extraction.

Idempotent: a correction whose text is already in place is reported as such and not re-applied.
"""
import argparse
import glob
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "drop", "bssc", "TEXT_CORRECTIONS.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "drop", "bssc"))
    ap.add_argument("--corrections", default=DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    spec = json.load(io.open(a.corrections, encoding="utf-8"))
    todo = spec.get("corrections", [])
    print(f"{len(todo)} correction(s) from {os.path.basename(a.corrections)}\n")

    applied = already = missing = 0
    for path in sorted(glob.glob(os.path.join(a.dir, "*_KEYED.json"))):
        rows = json.load(io.open(path, encoding="utf-8"))
        dirty = False
        for c in todo:
            for q in rows:
                if q.get("source_pdf") != c["source_pdf"] or q.get("number") != c["number"]:
                    continue
                fld = c["field"]
                if q.get(fld) == c["now"]:
                    already += 1
                    print(f"  = already correct  {c['source_pdf']} Q{c['number']} .{fld}")
                elif q.get(fld, "").strip() == c["was"].strip():
                    q[fld] = c["now"]
                    dirty = True
                    applied += 1
                    print(f"  ✓ corrected        {c['source_pdf']} Q{c['number']} .{fld}")
                    print(f"      was: {c['was'][:70]}")
                    print(f"      now: {c['now'][:70]}")
                else:
                    missing += 1
                    print(f"  ! text has CHANGED since this correction was written — skipping "
                          f"{c['source_pdf']} Q{c['number']} .{fld}")
                    print(f"      expected: {c['was'][:70]}")
                    print(f"      found   : {str(q.get(fld))[:70]}")
        if dirty and not a.dry_run:
            json.dump(rows, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\n  applied {applied} | already correct {already} | skipped {missing}")
    if a.dry_run:
        print("  (dry run — nothing written)")


if __name__ == "__main__":
    main()
