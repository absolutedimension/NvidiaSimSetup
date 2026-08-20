#!/usr/bin/env python3
"""Classify extracted BSSC questions, then derive the exam's real blueprint by counting.

Two passes, deliberately separate:

  TAG  — an LLM assigns each question a section / type / topic / difficulty from a FIXED taxonomy.
         Classification against a closed list is what small models are reliable at; nothing here
         is generation, so a wrong tag costs a mis-sorted question, never a wrong answer.

  MINE — pure arithmetic over the tags. The "pattern" of an exam is a distribution, and a
         distribution is a GROUP BY, not machine learning. Calling this ML would be dressing up
         counting; the place ML genuinely belongs is item difficulty from real student responses,
         which needs sittings we do not have yet.

The output blueprint is measured from real papers, which is the point: today's generated paper had
11 blood-relation questions in 50 because nothing declared what the real proportion is.
"""
import argparse
import glob
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SECTIONS = ["General Studies", "General Science", "Mathematics", "Reasoning", "Hindi", "English"]

TYPES = [
    # reasoning shapes we can also GENERATE — tagging these tells us what to build next
    "ranking", "coding_decoding", "blood_relation", "direction_sense", "series",
    "analogy", "odd_one_out", "calendar", "clock", "inequality", "dice",
    "seating_arrangement", "syllogism", "figure_series", "matrix_puzzle",
    # quant
    "arithmetic", "percentage_profit_loss", "time_work_speed", "ratio_average",
    "mensuration", "algebra", "number_system", "data_interpretation",
    # knowledge
    "factual_recall", "match_the_pairs", "assertion_reason", "statement_based", "current_affairs",
]

# The first taxonomy was GK-only, so 46% of a real paper fell into "Other" — half these papers are
# Hindi/English language and arithmetic, which had no bucket. A catch-all that big makes the mix
# meaningless, so language and maths topics are now first-class.
TOPICS = [
    # Bihar
    "Bihar GK", "Bihar History", "Bihar Geography", "Bihar Polity/Schemes",
    # national GK
    "Indian History", "Indian Polity", "Indian Geography", "Economy",
    "Physics", "Chemistry", "Biology", "Environment",
    "Current Affairs - National", "Current Affairs - International", "Sports",
    "Art & Culture", "Static GK", "Science & Technology",
    # Hindi language (व्याकरण) — ~30% of several BSSC papers
    "Hindi Grammar", "Hindi Vocabulary", "Hindi Idioms/Proverbs", "Hindi Comprehension",
    # English language
    "English Grammar", "English Vocabulary", "English Comprehension",
    # maths / quantitative — ~25-30% of every paper
    "Arithmetic", "Percentage/Profit-Loss", "Time-Work-Speed", "Ratio/Average",
    "Mensuration", "Algebra", "Number System", "Data Interpretation",
    # reasoning
    "Logical Reasoning", "Series/Analogy", "Coding-Decoding", "Blood Relation/Direction",
    "Other",
]

TAG_SYS = (
    "You classify one question from a Bihar (BSSC) government exam paper. Choose ONLY from the "
    "given lists — never invent a value.\n"
    f"section: {SECTIONS}\n"
    f"type: {TYPES}\n"
    f"topic: {TOPICS}\n"
    "difficulty: 1 (very easy) to 5 (very hard), judged for a Class-12-level candidate.\n"
    "bihar_specific: true ONLY if the question is about Bihar itself (its history, geography, "
    "schemes, districts, rivers, personalities). A question that merely lists Patna as one wrong "
    "option is NOT Bihar-specific.\n"
    'Return JSON: {"section":"...","type":"...","topic":"...","difficulty":int,"bihar_specific":bool}'
)


def tag_file(llm, path, force=False):
    qs = json.load(io.open(path, encoding="utf-8"))
    changed = 0
    for i, q in enumerate(qs):
        if q.get("tag") and not force:
            continue
        stem = (q.get("stem") or q.get("stem_hi") or "")[:600]
        opts = " | ".join(o.get("text", "")[:40] for o in (q.get("options") or [])[:5])
        try:
            t = llm.chat_json(TAG_SYS, f"Question: {stem}\nOptions: {opts}")
        except Exception:
            t = None
        if not t:
            continue
        q["tag"] = {
            "section": t.get("section") if t.get("section") in SECTIONS else "General Studies",
            "type": t.get("type") if t.get("type") in TYPES else "factual_recall",
            "topic": t.get("topic") if t.get("topic") in TOPICS else "Other",
            "difficulty": min(5, max(1, int(t.get("difficulty") or 3))),
            "bihar_specific": bool(t.get("bihar_specific")),
        }
        changed += 1
        if changed % 25 == 0:
            print(f"    tagged {changed}…", flush=True)
    json.dump(qs, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(qs), changed



# For Mathematics / Reasoning / language questions, "type" and "topic" are the SAME concept — the
# first taxonomy listed them on both axes, so the model put the real answer in `type` and fell back
# to "Other" for `topic`. That is a taxonomy bug, not a tagging failure: the information is already
# in the record. Rather than re-run the LLM over 497 questions, derive the effective topic from
# (section, type) and only fall back to "Other" when we genuinely know nothing.
_TYPE_TO_TOPIC = {
    "arithmetic": "Arithmetic", "algebra": "Algebra", "number_system": "Number System",
    "mensuration": "Mensuration", "data_interpretation": "Data Interpretation",
    "time_work_speed": "Time-Work-Speed", "ratio_average": "Ratio/Average",
    "percentage_profit_loss": "Percentage/Profit-Loss",
    "ranking": "Logical Reasoning", "coding_decoding": "Coding-Decoding",
    "blood_relation": "Blood Relation/Direction", "direction_sense": "Blood Relation/Direction",
    "series": "Series/Analogy", "analogy": "Series/Analogy", "odd_one_out": "Logical Reasoning",
    "calendar": "Logical Reasoning", "clock": "Logical Reasoning", "inequality": "Logical Reasoning",
    "dice": "Logical Reasoning", "seating_arrangement": "Logical Reasoning",
    "syllogism": "Logical Reasoning", "figure_series": "Logical Reasoning",
    "matrix_puzzle": "Logical Reasoning",
}
# last resort: the section itself is a truthful, if coarse, topic
_SECTION_TO_TOPIC = {
    "Mathematics": "Arithmetic", "Reasoning": "Logical Reasoning",
    "Hindi": "Hindi Comprehension", "English": "English Comprehension",
    "General Science": "Science & Technology",
}


def effective_topic(tag):
    """The topic we can actually stand behind for this question."""
    t = tag.get("topic")
    if t and t != "Other":
        return t
    return _TYPE_TO_TOPIC.get(tag.get("type")) or _SECTION_TO_TOPIC.get(tag.get("section")) or "Other"


def _blueprint(qs, label):
    from collections import Counter as C
    def dist(items):
        c = C(items); tot = sum(c.values()) or 1
        return {k: round(v / tot, 3) for k, v in c.most_common()}
    return {
        "exam": label,
        "questions": len(qs),
        "section_mix": dist([q["tag"]["section"] for q in qs]),
        "topic_mix": dist([effective_topic(q["tag"]) for q in qs]),
        "type_mix": dist([q["tag"]["type"] for q in qs]),
        "difficulty_mix": dist([str(q["tag"]["difficulty"]) for q in qs]),
        "avg_difficulty": round(sum(q["tag"]["difficulty"] for q in qs) / max(len(qs), 1), 2),
        "bihar_share": round(sum(1 for q in qs if q["tag"]["bihar_specific"]) / max(len(qs), 1), 3),
        "unclassified_share": round(sum(1 for q in qs if effective_topic(q["tag"]) == "Other") / max(len(qs), 1), 3),
    }


def mine(paths):
    """One blueprint PER EXAM. Averaging across exam types produced 'Reasoning 3.8%' from five
    papers with genuinely different structures — an artifact, not a fact about any real exam."""
    per, allq = [], []
    for p in paths:
        qs = [q for q in json.load(io.open(p, encoding="utf-8")) if q.get("tag")]
        if not qs:
            continue
        label = qs[0].get("paper_label") or os.path.basename(p).replace("_KEYED.json", "")
        per.append(_blueprint(qs, label))
        allq += qs
    if not per:
        print("no tagged questions yet"); return None
    return {
        "note": ("One blueprint per exam. The pooled view is reference only — these papers are "
                 "different exams with different structures and must not be averaged."),
        "per_exam": per,
        "pooled_reference_only": _blueprint(allq, "ALL PAPERS POOLED (do not use as a blueprint)"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/bssc_in"))
    ap.add_argument("--mine-only", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.dir, "*_KEYED.json")))
    print(f"{len(paths)} keyed papers")
    if not a.mine_only:
        from qbank.llm import LLM
        llm = LLM()
        if not llm.ok:
            sys.exit("LLM not reachable")
        for p in paths:
            n, c = tag_file(llm, p)
            print(f"  {os.path.basename(p):34s} {n:4d} q, tagged {c}", flush=True)
    bp = mine(paths)
    if bp:
        dst = a.out or os.path.join(a.dir, "BSSC_BLUEPRINT.json")
        json.dump(bp, io.open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nblueprint -> {dst}")
        print(json.dumps({k: v for k, v in bp.items() if k != "per_section"},
                         ensure_ascii=False, indent=1)[:1400])


if __name__ == "__main__":
    main()
