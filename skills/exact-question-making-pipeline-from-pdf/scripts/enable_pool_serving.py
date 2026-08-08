#!/usr/bin/env python3
"""
enable_pool_serving.py — Make a REAL (generated=0) question bank serve from the frontend hot
path (/pool), which by default only serves generated=1 rows.

Patches ~/question_bank_engine/qbank/storage.py in two places (idempotent), mirroring the
UPSC fix. Pass the exam-name PREFIX your rows use (e.g. "CBSE Class 12", "UPSC").

What it changes in pool_questions() + pool_stats():
  1. Bypass the `generated=1` gate for your exam prefix  -> real PYQs serve.
  2. (pool_questions only) skip the chapter filter for your exam prefix IF your rows are
     chapter-NULL, so topic-named requests from the frontend still return rows instead of
     falling through to slow LLM /generate. Omit --skip-chapter once you tag rows by chapter.

ALWAYS restart the API after:  sudo systemctl restart qbank-api

Usage:
  cd ~/question_bank_engine
  cp qbank/storage.py qbank/storage.py.bak_serving
  python3 <thisdir>/enable_pool_serving.py --prefix "CBSE Class 12" --skip-chapter
  python3 -m py_compile qbank/storage.py && sudo systemctl restart qbank-api
"""
import argparse, os, re, sys

STORAGE = os.path.expanduser("~/question_bank_engine/qbank/storage.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True, help='exam-name prefix, e.g. "CBSE Class 12" or "UPSC"')
    ap.add_argument("--skip-chapter", action="store_true", help="also skip chapter filter (chapter-NULL banks)")
    args = ap.parse_args()
    p = args.prefix.replace('"', '\\"')

    s = open(STORAGE).read()
    orig = s

    # 1) generated=1 bypass — REBUILD the whole condition from its existing prefixes so it works
    #    on both the bare form  ( if exam and str(exam).startswith("CBSE Class"): )
    #    and the parenthesised form ( if exam and (str(exam).startswith("A") or ...startswith("B")): ).
    def add_prefix(match):
        indent = match.group(1)
        prefixes = re.findall(r'startswith\("([^"]*)"\)', match.group(0))
        if p not in prefixes:
            prefixes.append(p)
        inner = " or ".join(f'str(exam).startswith("{pref}")' for pref in prefixes)
        return f"{indent}if exam and ({inner}):"

    s = re.sub(r'([ \t]*)if exam and \(?str\(exam\)\.startswith\([^\n]*\):', add_prefix, s)

    # 2) chapter-skip inside pool_questions (only if requested and not already present)
    if args.skip_chapter and "skip_chapter =" not in s:
        anchor = ('        for col, val in (("exam", exam), ("subject", subject), '
                  '("chapter", chapter), ("qtype", qtype)):\n'
                  '            if val:\n'
                  '                where.append(f"{col}=?")\n'
                  '                args.append(val)')
        repl = ('        # real chapter-NULL banks: honour subject but ignore chapter filter\n'
                f'        skip_chapter = bool(exam and str(exam).startswith("{p}"))\n'
                '        for col, val in (("exam", exam), ("subject", subject), '
                '("chapter", chapter), ("qtype", qtype)):\n'
                '            if col == "chapter" and skip_chapter:\n'
                '                continue\n'
                '            if val:\n'
                '                where.append(f"{col}=?")\n'
                '                args.append(val)')
        if anchor in s:
            s = s.replace(anchor, repl, 1)
        else:
            print("!! could not find the chapter-filter loop verbatim — apply the chapter-skip by hand.")

    if s == orig:
        print("no change (already patched?) — verify with: grep -n startswith qbank/storage.py")
    else:
        open(STORAGE, "w").write(s)
        print("patched storage.py — now: py_compile + restart qbank-api")
    print('verify:  grep -n \'startswith(\' qbank/storage.py')


if __name__ == "__main__":
    main()
