#!/usr/bin/env python3
"""One-off repair: relabel numerically-labelled MCQ options to A/B/C/D and re-validate.

Why this exists: the Reja1 NEET papers print options as (1)(2)(3)(4) and give the key
as an option INDEX, while JEE Advanced papers use (A)(B)(C)(D). The bank standardises
on letters, so the first NEET image ingest had every question rejected with
`no_answer_key` even though the extraction itself was perfect. `extractor.letterize_options`
now fixes this at ingest time; this script applies the same normalisation to rows that
were already extracted, so ~2h of vision calls don't have to be repeated.

Idempotent — rows whose labels are already letters are skipped.

    python3 repair_numeric_options.py [--exam NEET] [--apply]
"""
import argparse
import json

from qbank import validator
from qbank.extractor import letterize_options
from qbank.storage import Store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exam", default="NEET")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    store = Store()
    rows = store.con.execute(
        "SELECT id, qtype, options, correct_answer, stem FROM questions "
        "WHERE exam=? AND verified=0", (args.exam,)).fetchall()

    changed = now_valid = still_bad = 0
    reasons = {}
    for qid, qtype, opts_json, answer, stem in rows:
        if qtype not in ("MCQ_single", "MCQ_multi"):
            continue
        opts = json.loads(opts_json or "[]")
        new_opts, new_answer = letterize_options(opts, answer or "")
        if new_answer == (answer or "") and new_opts == json.loads(opts_json or "[]"):
            continue                       # already lettered / nothing to do
        changed += 1

        # re-run the same rule gate the ingest uses
        class _Q:                          # rule_check only touches these fields
            pass
        q = _Q()
        q.qtype, q.options, q.correct_answer = qtype, new_opts, new_answer
        q.stem, q.needs_figure = stem or "", False
        issues = validator.rule_check(q)
        if issues:
            still_bad += 1
            for i in issues:
                reasons[i] = reasons.get(i, 0) + 1
        else:
            now_valid += 1

        if args.apply:
            store.con.execute(
                "UPDATE questions SET options=?, correct_answer=?, verified=?, "
                "validation_issues=? WHERE id=?",
                (json.dumps(new_opts, ensure_ascii=False), new_answer,
                 0 if issues else 1, json.dumps(issues, ensure_ascii=False), qid))
    if args.apply:
        store.con.commit()

    print(json.dumps({"exam": args.exam, "unverified_scanned": len(rows),
                      "relabelled": changed, "now_verified": now_valid,
                      "still_rejected": still_bad, "remaining_reasons": reasons,
                      "applied": bool(args.apply)}, indent=2))


if __name__ == "__main__":
    main()
