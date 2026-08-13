#!/usr/bin/env python3
"""import_current_affairs.py — MANUAL-ENTRY pipeline for Current Affairs (and any hand-typed MCQs).

Current Affairs is time-sensitive → it CANNOT be generated (unlike Reasoning/Quant/GK/English).
So it comes from a human filling a CSV template; this script loads that CSV into the live question
bank as REAL, dated, verified questions (generated=0, verified=1) that serve directly to students.

CSV columns (header row required; see TEMPLATE_current_affairs.csv):
    question, option_a, option_b, option_c, option_d, correct, exam, subject, topic, month
      correct = A|B|C|D
      exam    = "Current Affairs" (shared) OR a specific exam string ("SSC CGL", "BPSC", …)
      subject = "Current Affairs" (keep constant)
      topic   = Sports | Economy | Polity | International | Awards | Science & Tech | … (→ chapter+concept)
      month   = YYYY-MM  (e.g. 2026-08 — used for freshness/aging; newest months are the ones to serve)

Run ON the live bank box (Gurukul), from ~/question_bank_engine:
    .venv/bin/python current_affairs/import_current_affairs.py --csv current_affairs/aug2026.csv        # dry-run
    .venv/bin/python current_affairs/import_current_affairs.py --csv current_affairs/aug2026.csv --apply
Then: sudo systemctl restart qbank-api.  (Back up data/qbank.sqlite first — the script reminds you.)

Idempotent: re-importing the same CSV upserts by content-hash (no duplicates). Reusable for ANY
manual MCQ entry (deepening GK/English, adding a new topic) — just set exam/subject accordingly.
"""
import argparse
import csv
import os
import sys

# import qbank package (run from ~/question_bank_engine so `qbank` is importable)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qbank.models import Question, content_hash  # noqa: E402
from qbank.storage import Store  # noqa: E402

REQUIRED = ["question", "option_a", "option_b", "option_c", "option_d", "correct"]


def _row_to_question(row, idx):
    """Validate + build a Question from one CSV row. Returns (Question|None, error|None)."""
    q = (row.get("question") or "").strip()
    if len(q) < 10:
        return None, f"row {idx}: question too short/empty"
    opts_txt = [(l, (row.get("option_" + l.lower()) or "").strip()) for l in "ABCD"]
    if any(not t for _, t in opts_txt):
        return None, f"row {idx}: all four options A-D are required"
    correct = (row.get("correct") or "").strip().upper()
    if correct not in ("A", "B", "C", "D"):
        return None, f"row {idx}: 'correct' must be A/B/C/D (got {correct!r})"
    exam = (row.get("exam") or "Current Affairs").strip()
    subject = (row.get("subject") or "Current Affairs").strip()
    topic = (row.get("topic") or "General").strip()
    month = (row.get("month") or "").strip()
    # chapter carries the month so newest CA can be preferred; concept = topic
    chapter = month or topic
    options = [{"label": l, "text": t} for l, t in opts_txt]
    stem = q
    qid = "ca_" + content_hash(stem)[:16]
    obj = Question(
        id=qid, exam=exam, subject=subject, stem=stem, qtype="MCQ_single",
        options=options, correct_answer=correct,
        solution=(row.get("solution") or "").strip(),
        chapter=chapter, concept=topic, difficulty=2,
        source="manual_ca", generated=False, hash=content_hash(stem))
    obj.verified = True
    return obj, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--apply", action="store_true", help="actually write to the DB (default = dry-run)")
    ap.add_argument("--db", default=None, help="override DB path (default = qbank default store)")
    args = ap.parse_args()

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"CSV is missing required columns: {missing}\nHeaders found: {reader.fieldnames}")
        rows = list(reader)

    good, errors, seen = [], [], set()
    for i, row in enumerate(rows, 2):  # row 1 = header
        if not any((v or "").strip() for v in row.values()):
            continue  # skip blank lines
        q, err = _row_to_question(row, i)
        if err:
            errors.append(err)
            continue
        if q.hash in seen:
            errors.append(f"row {i}: duplicate of an earlier row (skipped)")
            continue
        seen.add(q.hash)
        good.append(q)

    print(f"parsed {len(rows)} data rows → {len(good)} valid questions, {len(errors)} skipped")
    for e in errors[:20]:
        print("  ⚠", e)
    # preview
    for q in good[:3]:
        ct = [o["text"] for o in q.options if o["label"] == q.correct_answer][0]
        print(f"  • [{q.exam}/{q.concept}/{q.chapter}] {q.stem[:70]} → {q.correct_answer}) {ct}")

    if not args.apply:
        print("\nDRY-RUN. Re-run with --apply to write these to the bank "
              "(back up data/qbank.sqlite first), then restart qbank-api.")
        return
    if not good:
        sys.exit("nothing valid to import.")

    store = Store(args.db) if args.db else Store()
    n = 0
    for q in good:
        store.upsert(q)
        n += 1
    print(f"\n✅ imported {n} Current-Affairs questions (generated=0, verified=1). "
          f"Now: sudo systemctl restart qbank-api")


if __name__ == "__main__":
    main()
