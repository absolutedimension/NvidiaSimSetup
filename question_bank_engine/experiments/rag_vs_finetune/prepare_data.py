#!/usr/bin/env python3
"""Prepare the RAG-vs-fine-tune experiment data from the live bank.

Outputs (into ./artifacts/):
  ft_train.jsonl   instruction -> question(JSON) pairs for LoRA SFT (all verified real Qs)
  specs.json       the balanced set of generation specs BOTH arms author against
  bank_stems.json  every real stem (novelty reference corpus, shared by both arms)

The fair-comparison design: both arms are handed the SAME specs and author NEW
questions; both pass through the SAME validator + novelty gate. We are testing
"given this bank, which METHOD authors better novel JEE questions" — not recall.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)  # so Store() finds data/qbank.sqlite

from qbank.storage import Store  # noqa: E402

ART = os.path.join(HERE, "artifacts")
os.makedirs(ART, exist_ok=True)

# chapters with enough real questions to be a fair exemplar pool AND believable specs
MIN_PER_CHAPTER = 5
# how many novel questions each arm authors per (chapter, difficulty band, type) spec
COUNT_PER_SPEC = 4


def _instruction(q: dict) -> str:
    kind = {
        "MCQ_single": "a single-correct MCQ with exactly 4 options",
        "MCQ_multi": "a multiple-correct MCQ with 4 options (one or more correct)",
        "integer": "an integer-answer question",
        "numeric": "a numeric-answer question",
    }.get(q["qtype"], "a single-correct MCQ with 4 options")
    return (
        f"Write one original {q['exam']} {q['subject']} question.\n"
        f"Chapter: {q.get('chapter')}\n"
        f"Concept: {q.get('concept') or 'any within the chapter'}\n"
        f"Difficulty: {q.get('difficulty')} on a 1-5 scale\n"
        f"Format: {kind}\n"
        'Return JSON: {"stem","options":[{"label","text"}],"correct_answer","solution"}. '
        "Use LaTeX for math."
    )


def _completion(q: dict) -> str:
    return json.dumps({
        "stem": q["stem"],
        "options": q.get("options", []),
        "correct_answer": q.get("correct_answer", ""),
        "solution": q.get("solution", "") or "",
    }, ensure_ascii=False)


def main():
    store = Store()
    rows = store.retrieve(subject="Physics", limit=100000, include_generated=False)
    rows = [r for r in rows if r.get("verified")]
    print(f"loaded {len(rows)} verified real questions")

    # --- ft_train.jsonl (chat-format SFT pairs) ---
    n_ft = 0
    with open(os.path.join(ART, "ft_train.jsonl"), "w") as f:
        for q in rows:
            rec = {"messages": [
                {"role": "system", "content":
                    "You are an expert author of original Indian competitive-exam physics "
                    "questions. You never copy or paraphrase existing questions."},
                {"role": "user", "content": _instruction(q)},
                {"role": "assistant", "content": _completion(q)},
            ]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_ft += 1
    print(f"wrote ft_train.jsonl: {n_ft} pairs")

    # --- specs.json (balanced generation targets) ---
    from collections import Counter
    by_ch = Counter(r.get("chapter") for r in rows)
    chapters = [c for c, n in by_ch.items()
                if c and c != "Unclassified" and n >= MIN_PER_CHAPTER]
    specs = []
    for ch in sorted(chapters):
        ch_rows = [r for r in rows if r.get("chapter") == ch]
        diffs = [r.get("difficulty") or 3 for r in ch_rows]
        lo, hi = min(diffs), max(diffs)
        mid_lo = max(2, (lo + hi) // 2)
        mid_hi = min(5, mid_lo + 1)
        specs.append({
            "exam": "JEE Advanced", "subject": "Physics", "chapter": ch,
            "qtype": "MCQ_single", "dmin": mid_lo, "dmax": mid_hi,
            "num_options": 4, "count": COUNT_PER_SPEC,
        })
    with open(os.path.join(ART, "specs.json"), "w") as f:
        json.dump(specs, f, indent=2, ensure_ascii=False)
    print(f"wrote specs.json: {len(specs)} specs x {COUNT_PER_SPEC} = "
          f"{len(specs) * COUNT_PER_SPEC} target questions per arm")

    # --- shared novelty reference corpus ---
    with open(os.path.join(ART, "bank_stems.json"), "w") as f:
        json.dump([r["stem"] for r in rows], f, ensure_ascii=False)
    print(f"wrote bank_stems.json: {len(rows)} stems")


if __name__ == "__main__":
    main()
