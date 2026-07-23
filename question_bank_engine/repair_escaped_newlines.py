#!/usr/bin/env python3
"""One-off repair: unescape double-escaped newlines in banked solutions.

Some LLM-authored solutions were stored carrying the two characters \\ + n instead of
a real line break, so the frontend renders a literal "\\n\\n" in the middle of a
worked solution. `storage.set_solution` now normalises this at write time; this script
fixes rows written before that.

LaTeX-safe: only unescapes when the n does NOT begin a command word, so \\nu, \\neq,
\\nabla, \\not and \\nonumber survive (see models.unescape_newlines).

Idempotent. Dry-run by default.

    python3 repair_escaped_newlines.py [--apply]
"""
import argparse
import json

from qbank.models import unescape_newlines
from qbank.storage import Store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--exam", default=None, help="limit to one exam")
    args = ap.parse_args()

    store = Store()
    sql = "SELECT id, exam, solution FROM questions WHERE solution IS NOT NULL AND solution != ''"
    params = []
    if args.exam:
        sql += " AND exam=?"
        params.append(args.exam)

    by_exam, changed, sample = {}, 0, None
    for qid, exam, sol in store.con.execute(sql, params).fetchall():
        new = unescape_newlines(sol)
        if new == sol:
            continue
        changed += 1
        by_exam[exam] = by_exam.get(exam, 0) + 1
        if sample is None:
            sample = (qid, sol[:120], new[:120])
        if args.apply:
            store.con.execute("UPDATE questions SET solution=? WHERE id=?", (new, qid))
    if args.apply:
        store.con.commit()

    print(json.dumps({"solutions_fixed": changed, "by_exam": by_exam,
                      "applied": bool(args.apply)}, indent=2))
    if sample:
        print("sample id:", sample[0])
        print("  before:", repr(sample[1]))
        print("  after :", repr(sample[2]))


if __name__ == "__main__":
    main()
