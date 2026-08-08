#!/usr/bin/env python3
"""
clean_option_blocks.py — Strip the duplicated (a)-(d) option block that vision models leave
INSIDE the stem. Without this the UI renders the options twice (once in the question text,
once as the clickable A/B/C/D buttons) and the question looks broken.

Handles BOTH formats seen in real papers:
  * multi-line options:  "...?\n(a) foo\n(b) bar\n(c) baz\n(d) qux"
  * single-line options: "...? (a) foo (b) bar (c) baz (d) qux"
Also strips a leading question number ("1. ", "23. ") that the extractor sometimes keeps.
The numbered STATEMENT lists (1./2./3. or I./II./III.) inside the stem are PRESERVED.

Idempotent + safe: never leaves a stem shorter than 15 chars; backs up nothing itself
(YOU back up the DB first — see the skill). Reports anything it could not fully clean.

Run ON the serving VM:
  cd ~/question_bank_engine
  cp data/qbank.sqlite data/qbank.sqlite.bak_clean
  PYTHONPATH=$PWD python3 clean_option_blocks.py --exam-like "CBSE Class 12 Physics"
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.expanduser("~/question_bank_engine"))
from qbank import storage  # noqa: E402

MARKER = re.compile(r"\(\s*[abcd]\s*\)", re.I)
BLOCK_MULTILINE = re.compile(r"\n\s*\(a\).*?\n\s*\(b\).*?\n\s*\(c\).*?\n\s*\(d\).*$", re.S | re.I)
BLOCK_INLINE = re.compile(r"\(a\)\s.*?\(b\)\s.*?\(c\)\s.*?\(d\)\s.*$", re.S | re.I)
LEADNUM = re.compile(r"^\s*\d+\.\s+")


def clean_one(stem):
    if not stem or not MARKER.search(stem):
        return stem
    new = stem
    m = BLOCK_MULTILINE.search(new) or BLOCK_INLINE.search(new)
    if m:
        new = new[:m.start()].rstrip()
    new = LEADNUM.sub("", new).strip()
    return new if len(new) >= 15 else stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam-like", required=True, help="SQL LIKE pattern, e.g. 'CBSE Class 12 Physics' or 'UPSC%'")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    like = args.exam_like if "%" in args.exam_like else f"%{args.exam_like}%"
    s = storage.Store(); con = s.con
    rows = list(con.execute("SELECT id, stem FROM questions WHERE exam LIKE ?", (like,)))
    changed = still = 0
    for qid, stem in rows:
        new = clean_one(stem)
        if new != stem:
            if not args.dry_run:
                con.execute("UPDATE questions SET stem=? WHERE id=?", (new, qid))
            changed += 1
            if MARKER.search(new):
                still += 1
    if not args.dry_run:
        con.commit()
    remaining = [r[0] for r in con.execute("SELECT id, stem FROM questions WHERE exam LIKE ?", (like,))
                 if r[1] and MARKER.search(clean_one(r[1]))]
    print(f"rows matched: {len(rows)} | cleaned: {changed}{' (dry-run)' if args.dry_run else ''}")
    print(f"still contain option markers after clean: {len(remaining)} {remaining[:15]}")
    if remaining:
        print("  ^ inspect these by hand — likely a non-(a-d) option style or markers used in the question itself")


if __name__ == "__main__":
    main()
