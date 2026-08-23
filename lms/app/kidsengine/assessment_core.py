#!/usr/bin/env python3
"""
assessment_core.py — RUNG 1 of the science-backed engine (see ASSESSMENT_STYLE_SYSTEM.md +
the Science-of-Assessment map). Enriches any generated item with the three things every learning-
science pillar needs:

  1. DIFFICULTY  — a predicted difficulty `b` computed from RADICALS (number size, carrying, operation,
                   representation, DOK). Item models: radicals set difficulty, incidentals are cosmetic
                   (Gierl & Lai). This lets the 85% controller request `b ≈ θ` and get it.
  2. DISTRACTORS — misconception-tagged wrong options, each computed by executing a NAMED buggy
                   procedure on the item's own numbers (Force Concept Inventory style). A wrong answer
                   becomes a DIAGNOSIS, not just "incorrect". Universal: makes MCQ senior courses diagnostic.
  3. FEEDBACK    — a tiered hint ladder (strategy → step → worked → answer-last) + per-distractor "why"
                   (Hattie process-level feedback; answer revealed last).

Pure Python, no deps. `enrich(item)` mutates the item in place and returns it.
"""
import re

# ---------------- carry / borrow detection (radicals) ----------------
def _needs_carry(a, b):
    sa, sb = str(a)[::-1], str(b)[::-1]; c = 0
    for i in range(max(len(sa), len(sb))):
        d = (int(sa[i]) if i < len(sa) else 0) + (int(sb[i]) if i < len(sb) else 0) + c
        if d >= 10: return True
        c = 0
    return False

def _needs_borrow(a, b):
    sa, sb = str(a)[::-1], str(b)[::-1]; borrow = 0
    for i in range(len(sa)):
        top = int(sa[i]) - borrow; bot = int(sb[i]) if i < len(sb) else 0
        if top < bot: return True
        borrow = 0
    return False

# Knowledge subjects come from the KB+template engine; maths comes from the computed engine.
# They need different difficulty treatment, so name the split once.
_KNOWLEDGE_SUBJECTS = {"evs", "english", "gk", "hindi"}


def _grade_adj(item, rad):
    """Class 3 is the anchor: the same question shape is easier at Class 1, harder at Class 5.
    Only applied to knowledge items — maths difficulty already scales through its number sizes."""
    cls = item.get("class") or item.get("cls")
    if isinstance(cls, int) and 1 <= cls <= 5:
        rad["grade"] = cls
        return (cls - 3) * 0.35
    return 0.0


# ---------------- 1. DIFFICULTY MODEL (radicals → b) ----------------
def difficulty(item):
    """Return (b, radicals). b is a difficulty logit-ish score; radicals is the {feature: value} that drove it."""
    t = item.get("type"); p = item.get("payload", {}); rad = {}; b = 0.0
    rep = (item.get("style") or {}).get("representation", "abstract")
    dok = (item.get("style") or {}).get("dok", 1)

    if t == "arith":
        a, bb, op = p.get("a", 0), p.get("b", 0), p.get("op", "+")
        digits = len(str(max(a, bb))); rad["digits"] = digits; b += (digits - 1) * 0.5
        rad["op"] = op; b += {"+": 0.0, "-": 0.2, "×": 0.6, "÷": 0.8}.get(op, 0)
        if op == "+" and _needs_carry(a, bb): rad["carry"] = True; b += 0.4
        if op == "-" and _needs_borrow(a, bb): rad["borrow"] = True; b += 0.5
    elif t == "count_write":
        n = p.get("n", 0); rad["count"] = n; b += (n / 12.0) * 0.6 - 0.6  # counting is easy
    elif t == "compare_symbol":
        digits = len(str(max(p.get("a", 0), p.get("b", 0)))); rad["digits"] = digits; b += (digits - 1) * 0.4 - 0.2
    elif t == "fill_sequence":
        step = p.get("step", 1); rad["step"] = step; b += 0.2 + (0.3 if step not in (1, 2, 10) else 0)
    elif t == "neighbour_number":
        digits = len(str(p.get("n", 0))); rad["digits"] = digits; b += (digits - 1) * 0.4 - 0.3
    elif t == "count_money":
        rad["coins"] = len(p.get("coins", [])); b += 0.2 + rad["coins"] * 0.15
    elif t in ("true_false",):
        b += 0.3  # error-spot / recognition
        # A knowledge true/false still has to be READ and judged, and a Class-5 statement is a
        # harder read than a Class-1 one. (Maths items are NOT grade-scaled here — their digit
        # count already encodes grade, so scaling again would double-count.)
        if str(item.get("subject", "")).lower() in _KNOWLEDGE_SUBJECTS:
            words = len(str(p.get("statement", "")).split())
            rad["words"] = words
            b += min(0.30, max(0, words - 6) * 0.03)     # longer statement = more to hold
            b += _grade_adj(item, rad)
    # ---- KNOWLEDGE items (KB+template engine: EVS / English / GK / Hindi) ----------------
    # Without these branches every knowledge question scored 0.0 (only true_false scored at all),
    # so all 42 pooled banks held just TWO difficulty values and the adaptive controller had
    # nothing to sort on. Difficulty here comes from three real signals:
    #   1. TASK TYPE   — recognising < recalling < producing a multi-part answer
    #   2. STRUCTURE   — more options / pairs / bins = more to hold in mind, less guessable
    #   3. GRADE       — the same shape of question is harder when the facts are Class-5 facts
    elif t in ("odd_one_out", "match_following", "cloze", "sort_groups", "match", "sort"):
        opts = p.get("options") or []
        pairs = p.get("pairs") or []
        bank = p.get("bank") or []
        gitems = p.get("items") or []
        bins = p.get("bins") or []
        if t == "odd_one_out":
            # find-the-misfit: scan every option and hold one category in mind
            b += 0.35
            rad["options"] = len(opts)
            b += max(0, len(opts) - 3) * 0.12          # 4 options is harder than 3
        elif t == "cloze":
            # recall, but a word bank turns it into a choice — chance = 1/len(bank)
            b += 0.55
            rad["bank"] = len(bank)
            b += -0.10 if len(bank) >= 4 else (0.10 if len(bank) <= 2 else 0.0)
            if not bank:
                rad["free_recall"] = True; b += 0.45   # no bank = genuine production
        elif t in ("match_following", "match"):
            # k simultaneous relations — load grows with k, and the last pair is free
            k = len(pairs); rad["pairs"] = k
            b += 0.70 + max(0, k - 4) * 0.25
        else:                                          # sort_groups
            ni, nb = len(gitems), len(bins)
            rad["sort_items"], rad["bins"] = ni, nb
            b += 0.80 + max(0, ni - 4) * 0.15 + max(0, nb - 2) * 0.30
        b += _grade_adj(item, rad)
    # representation (CPA) + cognitive depth (DOK) dials
    rad["representation"] = rep; b += {"pictorial": -0.3, "abstract": 0.0, "object": 0.0, "story": 0.4, "words": 0.3}.get(rep, 0)
    rad["dok"] = dok; b += (dok - 1) * 0.3
    return round(b, 2), rad

def difficulty_band(b):
    """Map a difficulty logit to a 1-4 band (compatible with the qbank bands)."""
    return 1 if b < 0.3 else 2 if b < 1.0 else 3 if b < 1.8 else 4

# ---------------- 2. MISCONCEPTION LIBRARY → diagnostic distractors ----------------
def _add_no_carry(a, b):
    sa, sb = str(a)[::-1], str(b)[::-1]; res = ""
    for i in range(max(len(sa), len(sb))):
        d = (int(sa[i]) if i < len(sa) else 0) + (int(sb[i]) if i < len(sb) else 0)
        res = str(d % 10) + res
    return int(res or 0)

def _sub_smaller_from_larger(a, b):
    sa, sb = str(a)[::-1], str(b)[::-1]; res = ""
    for i in range(len(sa)):
        da = int(sa[i]); db = int(sb[i]) if i < len(sb) else 0
        res = str(abs(da - db)) + res
    return int(res or 0)

# concept → [ {id, name, fn(a,b)->wrong, why} ]  — each fn runs the BUGGY procedure
MISCONCEPTIONS = {
    "add": [
        {"id": "add_no_carry", "name": "forgot to carry", "fn": _add_no_carry, "why": "You added each column but forgot to carry the 1."},
        {"id": "add_place_slip", "name": "place-value slip", "fn": lambda a, b: a + b - 10, "why": "Check your tens column — the place value slipped by 10."},
    ],
    "sub": [
        {"id": "sub_smaller_from_larger", "name": "always took smaller from larger", "fn": _sub_smaller_from_larger, "why": "In each column you took the smaller digit from the larger — you must borrow instead."},
        {"id": "sub_added", "name": "added instead", "fn": lambda a, b: a + b, "why": "This is a take-away — you added instead of subtracting."},
    ],
    "mul": [
        {"id": "mul_added", "name": "added instead of multiplied", "fn": lambda a, b: a + b, "why": "'Times' means multiply, not add."},
        {"id": "mul_one_group_short", "name": "one group too few", "fn": lambda a, b: a * b - b, "why": "You used one group too few — count all the groups."},
    ],
    "div": [
        {"id": "div_multiplied", "name": "multiplied instead", "fn": lambda a, b: a * b, "why": "Sharing means divide, not multiply."},
        {"id": "div_off_by_one", "name": "off by one", "fn": lambda a, b: (a // b) + 1 if b else 0, "why": "Count the groups again — you're one over."},
    ],
}
_OP2CONCEPT = {"+": "add", "-": "sub", "×": "mul", "÷": "div"}

def distractors(item, want=3):
    """For a numeric-answer item, compute misconception-tagged distractors. Returns [] if not applicable."""
    if item.get("type") != "arith":
        return []
    op = item["payload"].get("op"); concept = _OP2CONCEPT.get(op)
    right = item.get("answer"); a, b = item["payload"].get("a"), item["payload"].get("b")
    if concept is None or not isinstance(right, int):
        return []
    out, seen = [], {right}
    for m in MISCONCEPTIONS.get(concept, []):
        try:
            w = int(m["fn"](a, b))
        except Exception:
            continue
        if w <= 0 or w in seen:
            continue
        seen.add(w); out.append({"value": w, "misconception_id": m["id"], "misconception": m["name"], "why": m["why"]})
        if len(out) >= want:
            break
    # pad with a plausible near-miss if we lack diagnostic ones
    for delta in (1, -1, 10, -10):
        if len(out) >= want:
            break
        w = right + delta
        if w > 0 and w not in seen:
            seen.add(w); out.append({"value": w, "misconception_id": "near_miss", "misconception": "computation slip", "why": "A small arithmetic slip."})
    return out

def to_mcq(item):
    """Turn a numeric item into an MCQ form WITH diagnostic distractors (for the senior/MCQ courses)."""
    ds = distractors(item)
    if not ds:
        return None
    opts = [{"value": item["answer"], "correct": True}] + [{"value": d["value"], "correct": False, "misconception_id": d["misconception_id"], "why": d["why"]} for d in ds]
    return {"stem": item.get("instruction"), "options": opts, "answer_value": item["answer"]}

# ---------------- 3. PROCESS FEEDBACK — tiered hint ladder ----------------
_STRAT = {
    "+": "What does the question ask you to put together? Add the numbers.",
    "-": "This is a take-away — start from the bigger number and subtract.",
    "×": "Equal groups added up — multiply the two numbers.",
    "÷": "Share equally into groups — divide.",
}
def hints(item):
    t = item.get("type"); p = item.get("payload", {})
    if t == "arith":
        op = p.get("op", "+")
        return [
            {"level": "strategy", "text": _STRAT.get(op, "Read the question and pick the operation.")},
            {"level": "step", "text": "Line the numbers up by place value, then work one column at a time (right to left)."},
            {"level": "worked", "text": f"Work it column by column, carrying/borrowing where needed."},
        ]
    if t == "count_write":
        return [{"level": "strategy", "text": "Touch each object as you count so you don't miss one."}]
    if t == "compare_symbol":
        return [{"level": "strategy", "text": "Compare the biggest place value first. The open mouth points to the bigger number."}]
    if t == "fill_sequence":
        return [{"level": "strategy", "text": f"Find how much the numbers jump each time, then add that jump."}]
    if t == "neighbour_number":
        return [{"level": "strategy", "text": "Just after = add 1. Just before = take 1."}]
    return [{"level": "strategy", "text": "Read it slowly and think about what it's really asking."}]

# ---------------- enrich() — attach all three to an item ----------------
def enrich(item):
    b, rad = difficulty(item)
    item["difficulty"] = b
    item["band"] = difficulty_band(b)   # 1-4, overrides the coarse age band with a computed one
    item["radicals"] = rad
    ds = distractors(item)
    if ds:
        item["distractors"] = ds        # misconception-tagged — diagnosis on wrong answers
    item["hints"] = hints(item)         # tiered process feedback (answer-last)
    return item


if __name__ == "__main__":
    # demo
    import json
    demo = [
        {"type": "arith", "instruction": "Add it!  47 + 38 = ?", "payload": {"op": "+", "a": 47, "b": 38}, "answer": 85, "style": {"representation": "abstract", "dok": 1}},
        {"type": "arith", "instruction": "Multiply!  6 × 7 = ?", "payload": {"op": "×", "a": 6, "b": 7}, "answer": 42, "style": {"representation": "abstract", "dok": 1}},
        {"type": "arith", "instruction": "Riya has 234, gets 158 more...", "payload": {"op": "+", "a": 234, "b": 158}, "answer": 392, "style": {"representation": "story", "dok": 2}},
    ]
    for it in demo:
        enrich(it)
        print(f"\n{it['instruction']}")
        print(f"  difficulty b={it['difficulty']} (band {it['band']})  radicals={it['radicals']}")
        for d in it.get("distractors", []):
            print(f"  distractor {d['value']:>5}  ← {d['misconception']}  ({d['misconception_id']})")
        print(f"  hints: {[h['level'] for h in it['hints']]}")
