#!/usr/bin/env python3
"""Blind LLM-judge for generated physics questions.

Scores each question 1-5 on four axes with a STRONG model (default gpt-4o), which
must be a different / stronger model than either arm's generator so the judge isn't
grading its own work. Order is not revealed to the judge (one question at a time,
arm label stripped). Novelty is computed numerically (TF-IDF), not judged.

Usage:
  python3 judge.py artifacts/out_rag.json  artifacts/scored_rag.json
  python3 judge.py artifacts/out_ft.json   artifacts/scored_ft.json
Then:
  python3 judge.py --report artifacts/scored_rag.json artifacts/scored_ft.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)

from qbank.llm import LLM  # noqa: E402

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o")

RUBRIC_SYSTEM = (
    "You are a senior JEE Advanced physics examiner grading the QUALITY of a single "
    "candidate exam question (not answering it for a student). Be strict and calibrated "
    "to real JEE Advanced standards. First SOLVE the question yourself, then grade.\n"
    "Return JSON with integer 1-5 scores and short reasons:\n"
    "{\n"
    '  "physics_correct": 1-5,   // is the physics sound AND is the marked correct_answer'
    " actually correct? 1=wrong/unsolvable, 5=rigorous and the key is right\n"
    '  "jee_authentic": 1-5,     // does it read like a real JEE Advanced item (framing,'
    " rigor, phrasing)? 1=textbook-trivial/AI-generic, 5=indistinguishable from a real paper\n"
    '  "difficulty_match": 1-5,  // does realized difficulty match the requested band?\n'
    '  "distractor_quality": 1-5,// are wrong options plausible traps from real'
    " misconceptions (not obviously silly / not duplicated)? 5=excellent traps\n"
    '  "solver_answer": "<the option letter(s)/value YOU derived>",\n'
    '  "key_agrees": true/false, // does your derived answer match the given correct_answer?\n'
    '  "reason": "<=40 words"\n'
    "}"
)


def _fmt(q: dict) -> str:
    opts = "\n".join(f"({o['label']}) {o['text']}" for o in q.get("options", []))
    return (
        f"Requested: {q.get('exam')} {q.get('subject')} | chapter={q.get('chapter')} "
        f"| difficulty band requested={q.get('difficulty')} | type={q.get('qtype')}\n\n"
        f"STEM:\n{q.get('stem')}\n\nOPTIONS:\n{opts}\n\n"
        f"GIVEN correct_answer: {q.get('correct_answer')}\n"
        f"GIVEN solution: {q.get('solution') or '(none provided)'}"
    )


def score_file(inp: str, outp: str):
    data = json.load(open(inp))
    qs = data["questions"] if isinstance(data, dict) else data
    llm = LLM()
    if not llm.ok:
        sys.exit(f"LLM proxy not reachable: {llm.last_error}. Set QBANK_LLM=on + proxy env.")
    scored = []
    for i, q in enumerate(qs, 1):
        r = llm.chat_json(RUBRIC_SYSTEM, _fmt(q), model=JUDGE_MODEL, temperature=0.0)
        if not r:
            r = {"physics_correct": 0, "jee_authentic": 0, "difficulty_match": 0,
                 "distractor_quality": 0, "key_agrees": False, "reason": "judge_no_output"}
        r["_qid"] = q.get("id")
        r["_novelty"] = q.get("_novelty")  # populated by the generators
        scored.append({"question": q, "scores": r})
        print(f"  [{i}/{len(qs)}] phys={r.get('physics_correct')} "
              f"auth={r.get('jee_authentic')} key_agrees={r.get('key_agrees')}")
    json.dump(scored, open(outp, "w"), indent=2, ensure_ascii=False)
    print(f"wrote {outp} ({len(scored)} scored)")


AXES = ["physics_correct", "jee_authentic", "difficulty_match", "distractor_quality"]


def _agg(path: str) -> dict:
    scored = json.load(open(path))
    n = len(scored) or 1
    out = {"n": len(scored)}
    for ax in AXES:
        vals = [s["scores"].get(ax, 0) or 0 for s in scored]
        out[ax] = round(sum(vals) / n, 2)
    out["overall"] = round(sum(out[ax] for ax in AXES) / len(AXES), 2)
    out["key_correct_rate"] = round(
        sum(1 for s in scored if s["scores"].get("key_agrees")) / n, 3)
    nov = [s["scores"].get("_novelty") for s in scored if s["scores"].get("_novelty") is not None]
    out["mean_novelty_sim"] = round(sum(nov) / len(nov), 3) if nov else None
    return out


def report(paths: list[str]):
    print(f"\n{'ARM':<28}{'n':>4}{'phys':>7}{'auth':>7}{'diff':>7}{'distr':>7}"
          f"{'OVER':>7}{'key%':>7}{'novel':>7}")
    print("-" * 84)
    for p in paths:
        a = _agg(p)
        name = os.path.basename(p).replace("scored_", "").replace(".json", "")
        print(f"{name:<28}{a['n']:>4}{a['physics_correct']:>7}{a['jee_authentic']:>7}"
              f"{a['difficulty_match']:>7}{a['distractor_quality']:>7}{a['overall']:>7}"
              f"{a['key_correct_rate']*100:>6.0f}%{str(a['mean_novelty_sim']):>7}")
    print("\nHigher is better on all axes. key% = fraction where an independent solve "
          "agreed with the marked answer (the correctness gate). novel = mean max TF-IDF "
          "similarity to the real bank (LOWER = more original).")


if __name__ == "__main__":
    if sys.argv[1] == "--report":
        report(sys.argv[2:])
    else:
        score_file(sys.argv[1], sys.argv[2])
