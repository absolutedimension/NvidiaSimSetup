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

# ── Per-goal blueprints for the shared test series (used by tools/build_mock_papers.py) ──
# Keyed by examgen.GOALS id. `mix` = how many slots each subject-slug gets (multi-subject papers).
# OBJECTIVE exams only: CBSE boards/commerce are subjective, so we do NOT fake a board mock — those
# goals fall through to the honest "coming soon" empty state on /exam-prep/papers.
_MCQ = {"name": "Single correct — one option", "type": "MCQ_single", "partial": 0}
BLUEPRINTS = {
    "jee-advanced": {          # the original hard Physics paper (multi-type)
        "label": "JEE Advanced Physics", "code": "JEEADV-PHY", "minutes": 60, "difficulty": "4",
        "mix": {"jee-physics": 17}, "sections": BLUEPRINT["sections"],
    },
    "neet": {                  # single-correct, +4/-1, Bio-heavy
        "label": "NEET", "code": "NEET", "minutes": 25, "difficulty": "3",
        "mix": {"neet-biology": 8, "neet-physics": 4, "neet-chemistry": 4},
        "sections": [{**_MCQ, "n": 16, "marks": 4, "neg": -1}],
    },
    "jee-main": {              # single-correct MCQ + numerical, +4/-1
        "label": "JEE Main", "code": "JEEMAIN", "minutes": 30, "difficulty": "3",
        "mix": {"jeemain-physics": 5, "jeemain-chemistry": 5, "jeemain-maths": 5},
        "sections": [{**_MCQ, "n": 12, "marks": 4, "neg": -1},
                     {"name": "Numerical value", "type": "numeric", "n": 3, "marks": 4, "neg": 0, "partial": 0}],
    },
    "banking": {               # quant aptitude, +1/-0.25
        "label": "Banking — Quantitative Aptitude", "code": "BANK-QUANT", "minutes": 20, "difficulty": "2",
        "mix": {"banking-quant": 15},
        "sections": [{**_MCQ, "n": 15, "marks": 1, "neg": -0.25}],
    },
    "upsc": {                  # Prelims GS + CSAT, +2/-0.66
        "label": "UPSC Civil Services (Prelims)", "code": "UPSC", "minutes": 20, "difficulty": "3",
        "mix": {"upsc-gs": 10, "upsc-csat": 5},
        "sections": [{**_MCQ, "n": 15, "marks": 2, "neg": -0.66}],
    },
    # ── CBSE boards: real NCERT-sourced OBJECTIVE (MCQ) questions from /pool. 1 mark each, NO
    # negative marking (board style). These are objective practice papers, not the full subjective
    # board paper — built via tools/build_pool_papers.py (real questions), not the LLM generator.
    "cbse-10": {
        "label": "CBSE Class 10 Science", "code": "CBSE10", "minutes": 20, "kind": "mcq",
        "mix": {"cbse10-science": 15},
        "sections": [{**_MCQ, "n": 15, "marks": 1, "neg": 0}],
    },
    "cbse-12": {
        "label": "CBSE Class 12 (PCB)", "code": "CBSE12", "minutes": 25, "kind": "mcq",
        "mix": {"cbse12-physics": 5, "cbse12-chemistry": 5, "cbse12-biology": 5},
        "sections": [{**_MCQ, "n": 15, "marks": 1, "neg": 0}],
    },
    "cbse-12-commerce": {
        "label": "CBSE Class 12 Commerce", "code": "CBSE12-COM", "minutes": 20, "kind": "mcq",
        "mix": {"cbse12-accountancy": 8, "cbse12-economics": 7},
        "sections": [{**_MCQ, "n": 15, "marks": 1, "neg": 0}],
    },
}

# A goal's paper kind: "full" = real objective exam format (JEE/NEET/Banking/UPSC), "mcq" =
# objective MCQ practice only (CBSE boards — the bank has no subjective board questions yet).
def paper_kind(goal_id: str) -> str:
    return BLUEPRINTS.get(goal_id, {}).get("kind", "full")


def plan_paper_multi(goal_id: str, chapters_by_subject: dict, seed: int) -> list[dict]:
    """Plan all slots for one paper of `goal_id`, distributing across the goal's subjects per its
    `mix`, weighted by banked exemplars. `chapters_by_subject` = {subject_slug: [chapter dicts]}."""
    bp = BLUEPRINTS[goal_id]
    rng = random.Random(seed)
    # flat list of (section) templates, one entry per question slot
    slot_secs = [sec for sec in bp["sections"] for _ in range(sec["n"])]
    # assign a subject to each slot per the mix, then shuffle so subjects interleave
    subj_slots = []
    for subj, n in bp["mix"].items():
        subj_slots += [subj] * n
    rng.shuffle(subj_slots)
    slots, used = [], {}
    for sec, subj in zip(slot_secs, subj_slots):
        # concepts are optional — some subjects (e.g. NEET Physics/Chemistry) bank exemplars but
        # ship no per-chapter concept list; examgen generates fine from just the chapter.
        pool = [c for c in (chapters_by_subject.get(subj) or [])
                if (c.get("exemplars_banked") or 0) > 0] or list(chapters_by_subject.get(subj) or [])
        if not pool:
            continue
        weights = [max(1, c.get("exemplars_banked", 1)) for c in pool]
        choices = [c for c in pool if used.get((subj, c["chapter"]), 0) < 3] or pool
        w = [weights[pool.index(c)] for c in choices]
        ch = rng.choices(choices, weights=w, k=1)[0]
        used[(subj, ch["chapter"])] = used.get((subj, ch["chapter"]), 0) + 1
        cons = ch.get("concepts") or []
        slots.append({"section": sec["name"], "type": sec["type"],
                      "marks": sec["marks"], "neg": sec["neg"], "partial": sec.get("partial", 0),
                      "subject": subj, "chapter": ch["chapter"],
                      "concept": (rng.choice(cons) if cons else ""),
                      "figure": False})
    return slots
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
