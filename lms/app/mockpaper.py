"""Full JEE-Advanced-style mock papers (the shared test series).

The blueprint below is DERIVED FROM THE REAL PAPERS in our own bank (JEE Advanced Physics,
2024/2025/2026 — 31 questions per year across both papers):

    year   total  MCQ_single  integer  MCQ_multi  numeric
    2026    31        11         9         9         2
    2025    31        10        12         7         2
    2024    31        11        13         5         2
    difficulty: 76 of 93 at level 4, 15 at level 3 (almost nothing easier)

One paper's Physics section is half a year's questions (~17 in 60 minutes), so the real mix
scaled to 17 gives the section table below. Marking is the standard JEE Advanced scheme
(confirmed by Deepak 2026-07-23) — it is NOT in the bank, so it lives here as one constant.

Papers are PRE-GENERATED once and shared by every student (a real test series), which is why
generation cost is one-time rather than per-signup, and why a student never waits.
"""
import random

BLUEPRINT = {
    "exam": "JEE Advanced",
    "subject": "Physics",
    "minutes": 60,
    "sections": [
        {"name": "Section 1 — One correct option",   "type": "MCQ_single", "n": 6,
         "marks": 3, "neg": -1, "partial": 0,
         "rule": "+3 for the correct option, −1 for a wrong one, 0 if unattempted."},
        {"name": "Section 2 — One or more correct",  "type": "MCQ_multi",  "n": 4,
         "marks": 4, "neg": -2, "partial": 1,
         "rule": "+4 if all correct options (and only those) are chosen; +1 for each correct "
                 "option when partially right; −2 if any wrong option is chosen; 0 if unattempted."},
        {"name": "Section 3 — Integer value",        "type": "integer",    "n": 6,
         "marks": 4, "neg": 0, "partial": 0,
         "rule": "+4 for the correct integer, 0 otherwise (no negative marking)."},
        {"name": "Section 4 — Numerical value",      "type": "numeric",    "n": 1,
         "marks": 4, "neg": 0, "partial": 0,
         "rule": "+4 for the correct value (2 decimal places), 0 otherwise (no negative marking)."},
    ],
}

TOTAL_Q = sum(s["n"] for s in BLUEPRINT["sections"])            # 17
MAX_MARKS = sum(s["n"] * s["marks"] for s in BLUEPRINT["sections"])  # 62
SERIES_SIZE = 15          # papers pre-generated and shared with everyone
DIFFICULTY = "4"          # the real papers cluster hard; a few 3s come through anyway

# Real JEE papers are full of figures. Forcing a diagram costs ~90-150s per question — far too slow
# for a live request, but free here because papers are generated OFFLINE, once. We target ~5 of 17
# and only ask chapters where a diagram is natural (a circuit, a ray path, a free-body sketch).
FIGURE_TARGET = 5
FIGURE_CHAPTERS = {
    "Ray Optics", "Wave Optics", "Electrostatics", "Current Electricity",
    "Electromagnetic Induction & AC", "Magnetism & Moving Charges",
    "Rotational Motion", "Laws of Motion", "Properties of Matter & Fluids", "Kinematics",
}


def plan_paper(chapters: list[dict], seed: int) -> list[dict]:
    """Decide (section, qtype, chapter, concept) for all 17 slots of one paper.

    Chapters are picked WEIGHTED BY BANKED EXEMPLARS (a chapter the real papers lean on gets more
    slots), and no chapter dominates a single paper. `seed` makes each paper in the series
    reproducibly different."""
    rng = random.Random(seed)
    pool = [c for c in chapters if (c.get("exemplars_banked") or 0) > 0 and c.get("concepts")]
    if not pool:
        return []
    weights = [max(1, c.get("exemplars_banked", 1)) for c in pool]
    slots, used = [], {}
    for sec in BLUEPRINT["sections"]:
        for _ in range(sec["n"]):
            # cap any chapter at ~3 questions per paper so it stays a spread, like the real thing
            choices = [c for c in pool if used.get(c["chapter"], 0) < 3] or pool
            w = [weights[pool.index(c)] for c in choices]
            ch = rng.choices(choices, weights=w, k=1)[0]
            used[ch["chapter"]] = used.get(ch["chapter"], 0) + 1
            slots.append({"section": sec["name"], "type": sec["type"],
                          "marks": sec["marks"], "neg": sec["neg"], "partial": sec["partial"],
                          "chapter": ch["chapter"], "concept": rng.choice(ch["concepts"]),
                          "figure": False})
    # ask for diagrams on ~FIGURE_TARGET slots, only where a figure is natural for that chapter
    figurable = [s for s in slots if s["chapter"] in FIGURE_CHAPTERS]
    for s in rng.sample(figurable, min(FIGURE_TARGET, len(figurable))):
        s["figure"] = True
    return slots


def score_attempt(paper_questions: list[dict], answers: dict) -> dict:
    """Score a sitting against the JEE Advanced scheme. `answers` is {question_no: response}:
    single -> "B" · multi -> ["A","C"] · integer/numeric -> "9" / "3.14"."""
    total = 0.0
    correct = wrong = skipped = 0
    per_q = []
    for q in paper_questions:
        no = str(q.get("n"))
        given = answers.get(no)
        marks, neg, partial = q.get("marks", 4), q.get("neg", 0), q.get("partial", 0)
        key = q.get("correct")
        got = 0.0
        state = "skipped"
        empty = given is None or given == "" or given == []
        if empty:
            skipped += 1
        elif q.get("qtype") == "MCQ_multi":
            chosen = set(x.upper() for x in (given if isinstance(given, list) else [given]))
            keyset = set(x.upper() for x in (key if isinstance(key, list) else list(str(key))))
            if chosen == keyset:
                got, state = marks, "correct"; correct += 1
            elif chosen - keyset:                     # any wrong option chosen
                got, state = neg, "wrong"; wrong += 1
            elif chosen:                              # all chosen are right, but incomplete
                got, state = partial * len(chosen), "partial"; correct += 1
            else:
                skipped += 1
        elif q.get("qtype") in ("integer", "numeric"):
            try:
                ok = abs(float(str(given).strip()) - float(str(key).strip())) < (
                    0.005 if q.get("qtype") == "numeric" else 1e-9)
            except Exception:
                ok = str(given).strip() == str(key).strip()
            if ok:
                got, state = marks, "correct"; correct += 1
            else:
                got, state = neg, "wrong"; wrong += 1
        else:                                          # MCQ_single
            if str(given).strip().upper() == str(key).strip().upper():
                got, state = marks, "correct"; correct += 1
            else:
                got, state = neg, "wrong"; wrong += 1
        total += got
        per_q.append({"n": q.get("n"), "state": state, "got": got, "correct": key, "given": given})
    return {"score": round(total, 2), "correct": correct, "wrong": wrong,
            "skipped": skipped, "per_q": per_q}
