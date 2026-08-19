"""kids_worksheet.py — the serving brain for the kids WORKSHEET + ADAPTIVE ASSESSMENT flow.

Ties together: the curriculum-driven generator (kidsengine/worksheet_engine), the common
assessment core (difficulty + misconception distractors + hints), and the adaptive engine
(BKT mastery + Elo + 85% controller), backed by the KidsSkillState table.

Public API (main.py routes call these):
  picker(board, cls)                         → subjects + chapters available for the picker
  serve(db, student, board, cls, subject, chapter, n)  → an adaptive worksheet (items near target_b)
  complete(db, student, skill, results)      → update mastery/ability, log misconceptions, return progress
Keeps existing intact — it ALSO updates ConceptStat so the current report/weakest-concept keeps working.
"""
import os, sys, random

_ENG = os.path.join(os.path.dirname(__file__), "kidsengine")
if _ENG not in sys.path:
    sys.path.insert(0, _ENG)
import worksheet_engine as WE      # noqa: E402
import assessment_core as AC       # noqa: E402
import adaptive_engine as AE       # noqa: E402

from .models import KidsSkillState, ConceptStat  # noqa: E402


def skill_key(board, cls, subject, chapter):
    return f"{board}/{cls}/{subject}/{chapter or 'all'}"


_BANK = os.path.join(_ENG, "content", "bank")


def _bank_path(board, cls, subject):
    slug = f"{board}".lower().replace(" ", "") + f"_class{cls}_" + f"{subject}".lower().replace(" ", "")
    return os.path.join(_BANK, slug + ".json")


def _has_bank(board, cls, subject) -> bool:
    """Is there a pooled bank behind this cell? (drives what the picker offers)"""
    return os.path.exists(_bank_path(board, cls, subject))


def _bank_items(board, cls, subject, chapter):
    """Pre-pooled worksheet items for a cell (offline fallback when live generation is empty —
    e.g. a knowledge subject whose LLM endpoint is unreachable). Enriched like live items."""
    path = _bank_path(board, cls, subject)
    if not os.path.exists(path):
        return []
    try:
        import json
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return []
    items = data.get("items", []) if isinstance(data, dict) else (data or [])
    if chapter:
        low = chapter.lower()
        hit = [it for it in items if low in str(it.get("chapter", "")).lower()]
        items = hit or items
    out = []
    for it in items:
        try:
            out.append(AC.enrich(it) if "difficulty" not in it else it)
        except Exception:
            out.append(it)
    return out


# ---------- curriculum picker ----------
def picker(board, cls):
    """Return the subjects (with chapters) available for a board+class from the taxonomy.

    A subject is only OFFERED if we can actually serve it: Maths is computed (always available),
    every knowledge subject needs its pooled bank. The taxonomy has cells we have no bank for yet
    (Bihar Board knowledge outside Class 3) — showing those chips just walks a child into an empty
    "pack being prepared" sheet, so they're filtered out here."""
    out = {}
    # names MUST match the curriculum file slugs (…_gk.json → "GK", not "General Knowledge")
    for subject in ["Mathematics", "EVS", "English", "GK", "Hindi"]:
        cell = WE.load_cell(board, cls, subject)
        if not cell:
            continue
        if subject != "Mathematics" and not _has_bank(board, cls, subject):
            continue
        chs = [c[0] for c in WE.chapters_of(cell) if c[0]]
        if chs:
            out[subject] = chs
    return out


# ---------- what we ACTUALLY have (drives the landing page — no hand-typed marketing numbers) ----------
BOARDS = ["CBSE", "ICSE", "Bihar Board"]
SUBJECTS = ["Mathematics", "EVS", "English", "GK", "Hindi"]
_COVERAGE = None


def coverage():
    """A factual map of the shipped content, read off the banks + curriculum ONCE at first use.

    {"classes": {1: {"subjects": [...], "boards": {"CBSE": [...], ...}, "chapters": n}, ...},
     "questions": <pooled knowledge questions>, "boards": [...]}
    Maths is COMPUTED (its bank file is a 12-item stub), so it counts as a subject but contributes
    no pooled total — the landing must never present those stubs as a question count."""
    global _COVERAGE
    if _COVERAGE is not None:
        return _COVERAGE
    import json
    classes, pooled = {}, 0
    for cls in range(1, 6):
        boards, chapters = {}, 0
        for board in BOARDS:
            subs = picker(board, cls)
            if not subs:
                continue
            boards[board] = sorted(subs.keys(), key=SUBJECTS.index)
            chapters += sum(len(v) for v in subs.values())
            for s in subs:
                if s == "Mathematics":
                    continue                      # computed, not pooled
                try:
                    d = json.load(open(_bank_path(board, cls, s), encoding="utf-8"))
                    pooled += len(d if isinstance(d, list) else d.get("items", []))
                except Exception:
                    pass
        union = sorted({s for v in boards.values() for s in v}, key=SUBJECTS.index)
        classes[cls] = {"subjects": union, "boards": boards, "chapters": chapters}
    _COVERAGE = {"classes": classes, "questions": pooled,
                 "boards": [b for b in BOARDS if any(b in c["boards"] for c in classes.values())]}
    return _COVERAGE


# ---------- adaptive state ----------
def _load_state(db, student_id, skill):
    row = db.query(KidsSkillState).filter_by(student_id=student_id, skill=skill).first()
    if row:
        s = AE.new_state(skill, theta=row.theta)
        s.update({"p_mastery": row.p_mastery, "ema": row.ema, "target_b": row.target_b,
                  "n": row.n, "n_correct": row.n_correct, "misconceptions": dict(row.misconceptions or {})})
        return row, s
    return None, AE.new_state(skill)


def _save_state(db, student_id, skill, s, row):
    if row is None:
        row = KidsSkillState(student_id=student_id, skill=skill)
        db.add(row)
    row.p_mastery, row.theta, row.ema, row.target_b = s["p_mastery"], s["theta"], s["ema"], s["target_b"]
    row.n, row.n_correct, row.misconceptions = s["n"], s["n_correct"], s["misconceptions"]
    db.commit()


# ---------- serve an adaptive worksheet ----------
def serve(db, student, board, cls, subject, chapter, n=8):
    skill = skill_key(board, cls, subject, chapter)
    sid = getattr(student, "id", 0) or 0
    _, state = _load_state(db, sid, skill) if sid else (None, AE.new_state(skill))
    target_b = AE.next_target_b(state)

    # Build a spanning pool, then pick n around target_b.
    #  • Maths = COMPUTED live (instant, varied, no endpoint) → generate.
    #  • Knowledge (EVS/English/GK/Hindi) = prefer the reliable PRE-POOLED bank (no LLM dependency
    #    at request time); only hit the LLM generator if we have no pack for this cell.
    is_math = str(subject).lower().replace(" ", "") in ("mathematics", "maths", "math")
    pool = []
    try:
        if is_math:
            pool = WE.generate(board, cls, subject, chapter, n=max(n * 2, 12))
        else:
            pool = _bank_items(board, cls, subject, chapter)
            if not pool:
                pool = WE.generate(board, cls, subject, chapter, n=max(n * 2, 12))
    except Exception:
        pool = _bank_items(board, cls, subject, chapter)
    pool = [it for it in (pool or []) if it]
    if not pool:
        pool = _bank_items(board, cls, subject, chapter)
    if not pool:
        # Nothing we can serve yet — tell the UI so it can show a friendly "pack being prepared".
        return {"skill": skill, "board": board, "class": cls, "subject": subject,
                "chapter": chapter or "all", "items": [], "reason": "pack_pending",
                "target_b": target_b, "mastery": state["p_mastery"]}
    # Draw n items RANDOMLY from a band of candidates near the target difficulty — NOT the strict
    # n-closest (that returned the same sheet every time). With a big pool this gives real variety
    # (a fresh sheet each visit) while still targeting the right difficulty.
    pool.sort(key=lambda it: abs(it.get("difficulty", 0.0) - target_b))
    band = pool[:max(n * 5, 40)]                 # the ~40+ nearest-difficulty candidates
    items = random.sample(band, n) if len(band) > n else band[:n]
    random.shuffle(items)                         # and don't present them difficulty-ordered
    return {"skill": skill, "board": board, "class": cls, "subject": subject, "chapter": chapter or "all",
            "items": items, "target_b": round(target_b, 2),
            "mastery": round(state["p_mastery"], 3), "attempts": state["n"]}


# ---------- record results, update mastery ----------
def complete(db, student, skill, results, subject=""):
    """results = [{correct, difficulty, misconception_id?, guess?, concept?}]. Updates KidsSkillState
    (BKT+Elo) AND ConceptStat (so the existing report keeps working)."""
    sid = getattr(student, "id", 0) or 0
    if not sid:
        return {"ok": False}
    row, s = _load_state(db, sid, skill)
    subj = (subject or skill)[:40]
    cs_cache = {}   # concept -> ConceptStat pending this call (rows aren't visible to query until flush)
    for r in results or []:
        if not isinstance(r, dict):
            continue
        b = float(r.get("difficulty", 0.0) or 0.0)
        correct = bool(r.get("correct"))
        guess = float(r.get("guess", 0.05) or 0.05)   # worksheets = free response (low guess)
        AE.update(s, b, correct, guess=guess, misconception_id=r.get("misconception_id"))
        # keep the existing per-concept report alive
        concept = str(r.get("concept") or skill)[:120]
        cs = cs_cache.get(concept)
        if cs is None:
            cs = db.query(ConceptStat).filter_by(student_id=sid, subject=subj, concept=concept).first()
            if not cs:
                cs = ConceptStat(student_id=sid, subject=subj, concept=concept, seen=0, correct=0.0)
                db.add(cs)
            cs_cache[concept] = cs
        cs.seen = (cs.seen or 0) + 1
        cs.correct = (cs.correct or 0.0) + (1.0 if correct else 0.0)
    _save_state(db, sid, skill, s, row)
    return {"ok": True, "mastery": round(s["p_mastery"], 3), "mastered": AE.is_mastered(s),
            "attempts": s["n"], "accuracy": round(s["n_correct"] / max(1, s["n"]), 2),
            "misconceptions": label_misconceptions(s["misconceptions"])}


def label_misconceptions(mis_dict, k=3):
    """Top-k stored misconceptions as readable [{id, name, why, n}] (most-frequent first)."""
    top = sorted((mis_dict or {}).items(), key=lambda kv: -kv[1])[:k]
    return [{**AC.mis_label(mid), "n": int(n or 0)} for mid, n in top]


def student_misconceptions(db, student, k=4):
    """Aggregate misconceptions across ALL of a student's skills → top-k readable [{id,name,why,n}].
    Powers the 'common slips' card in the kids report (the same slip recurring across worksheets)."""
    from collections import Counter
    sid = getattr(student, "id", 0) or 0
    cnt = Counter()
    if sid:
        for ks in db.query(KidsSkillState).filter_by(student_id=sid).all():
            for mid, n in (ks.misconceptions or {}).items():
                cnt[mid] += int(n or 0)
    return [{**AC.mis_label(mid), "n": n} for mid, n in cnt.most_common(k)]
