#!/usr/bin/env python3
"""Audit the bank for INCOMPLETE questions (reference a figure they lack) and backfill needs_figure.

Uses the qtype-aware detector in qbank.models. A question is INCOMPLETE (would be served half)
when it is figure-dependent AND carries no figure (no figure_url, no figure_svg). Setting
needs_figure=1 on these makes the serving gate (needs_figure=0 OR has-figure) exclude them.

    python3 audit_backfill_figures.py            # report only
    python3 audit_backfill_figures.py --apply     # set needs_figure=1 on incomplete ones
"""
import argparse, json, os, sqlite3, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qbank import config, models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    c = sqlite3.connect(config.DB_PATH); c.execute("PRAGMA busy_timeout=30000")
    rows = c.execute("""SELECT id, stem, options, qtype, figure_url, figure_svg,
        COALESCE(needs_figure,0), COALESCE(generated,0) FROM questions WHERE verified=1""").fetchall()

    reasons = Counter(); inc_gen = 0; silent = 0; to_flag = []
    for qid, stem, opts, qtype, furl, fsvg, needs, gen in rows:
        has_fig = bool((furl or "").strip()) or bool((fsvg or "").strip())
        if has_fig:
            continue
        try:
            options = json.loads(opts or "[]")
        except Exception:
            options = []
        if not models.is_figure_dependent(stem, options, qtype or "MCQ_single"):
            continue
        # classify reason (for reporting)
        if models.references_figure(stem or ""):
            reasons["figure/table reference in text"] += 1
        else:
            reasons["MCQ options carry no content"] += 1
        if gen:
            inc_gen += 1
        if not needs:
            silent += 1
            to_flag.append(qid)

    total_inc = sum(reasons.values())
    print(f"verified questions: {len(rows)}")
    print(f"\nINCOMPLETE (figure-dependent, no figure): {total_inc}")
    for r, n in reasons.most_common():
        print(f"   {r:34s} {n}")
    print(f"\n  in the GENERATED servable pool : {inc_gen}   (active student-facing risk)")
    print(f"  currently needs_figure=0 (SILENT): {silent}   (flag missed — would backfill)")

    if args.apply and to_flag:
        for i in range(0, len(to_flag), 500):
            batch = to_flag[i:i+500]
            c.execute("UPDATE questions SET needs_figure=1 WHERE id IN (%s)" %
                      ",".join("?" * len(batch)), batch)
        c.commit()
        print(f"\n[APPLIED] set needs_figure=1 on {len(to_flag)} previously-silent incomplete questions.")
        print("          the serving gate now excludes them (needs_figure=0 OR has-figure).")
    elif to_flag:
        print(f"\n(dry-run) would set needs_figure=1 on {len(to_flag)} questions. Re-run with --apply.")


if __name__ == "__main__":
    main()
