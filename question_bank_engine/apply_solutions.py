#!/usr/bin/env python3
"""Apply Claude-authored solutions to the bank.

Input JSON: [{"id":..., "answer":"<my derived answer>", "solution":"<worked solution>"}]
For each: compare my answer to the official key.
  match    -> store solution, mark verified (remove needs_review, add 'solved_by_claude')
  mismatch -> store solution, flag 'answer_disputed_claude' (my answer != official → review)
"""
import json
import re
import sqlite3
import sys

DB = "data/qbank.sqlite"


def _nums(s):
    return [float(x) for x in re.findall(r"-?\d+\.?\d*", str(s or ""))]


def agrees(qtype, mine, official):
    if qtype in ("MCQ_single", "MCQ_multi"):
        a = "".join(sorted(set(re.findall(r"[A-D]", (mine or "").upper()))))
        b = "".join(sorted(set(re.findall(r"[A-D]", (official or "").upper()))))
        return bool(b) and a == b
    m, o = _nums(mine), _nums(official)
    if not m or not o:
        return False
    val = m[0]
    if len(o) >= 2:                       # official is a tolerance range [lo, hi]
        lo, hi = min(o), max(o)
        return lo - 1e-9 <= val <= hi + 1e-9
    tol = max(0.05, abs(o[0]) * 0.02)     # single value: 2% or 0.05 tolerance
    return abs(val - o[0]) <= tol


def main(path):
    data = json.load(open(path))
    c = sqlite3.connect(DB)
    match = dispute = 0
    for item in data:
        row = c.execute("SELECT qtype, correct_answer, validation_issues FROM questions WHERE id=?",
                        (item["id"],)).fetchone()
        if not row:
            continue
        qtype, official, vi = row
        issues = [x for x in json.loads(vi or "[]") if x not in ("needs_review", "solution_needs_review")]
        agree = agrees(qtype, item.get("answer"), official)
        issues.append("solved_by_claude" if agree else "answer_disputed_claude")
        c.execute("UPDATE questions SET solution=?, validation_issues=? WHERE id=?",
                  (item.get("solution", ""), json.dumps(issues, ensure_ascii=False), item["id"]))
        match += int(agree)
        dispute += int(not agree)
    c.commit()
    print(json.dumps({"applied": len(data), "agree_official": match, "disputed": dispute}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
