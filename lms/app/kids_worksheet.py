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
import kb_engine as KBE            # noqa: E402  (knowledge subjects: KB + templates, live)
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
        # servable = computed (Maths) · a verified KB · or a pre-pooled bank. KBs are per
        # subject+class and board-independent, so this also covers boards we never pooled a
        # bank file for (e.g. Bihar Board outside Class 3).
        if subject != "Mathematics" and not (has_kb(subject, cls) or _has_bank(board, cls, subject)):
            continue
        chs = [c[0] for c in WE.chapters_of(cell) if c[0]]
        if chs:
            out[subject] = chs
    return out


# ---------- what we ACTUALLY have (drives the landing page — no hand-typed marketing numbers) ----------
BOARDS = ["CBSE", "ICSE", "Bihar Board"]
SUBJECTS = ["Mathematics", "EVS", "English", "GK", "Hindi"]
_COVERAGE = None


# Measured floor, not a marketing number: kids_quiz/tools/measure_kb_ceiling.py asks every KB for
# 100,000 DISTINCT questions and all 20 deliver without exhausting, so the real ceiling is higher.
# Re-run that script if the KBs change, and only ever quote a number it has actually produced.
MIN_QUESTIONS_PER_SUBJECT = 100_000


def coverage():
    """A factual map of what the app can actually serve, computed ONCE at first use.

    {"classes": {1: {"subjects": [...], "boards": {...}, "chapters": n}, ...},
     "cells": <servable knowledge subject×class×board cells>,
     "min_per_subject": <measured distinct-question floor>, "boards": [...]}

    Note what this deliberately does NOT report any more: a pooled question TOTAL. Knowledge is
    generated live from the KBs now, so counting the frozen bank files would understate the
    product by orders of magnitude — and Maths never had a pool to count in the first place."""
    global _COVERAGE
    if _COVERAGE is not None:
        return _COVERAGE
    classes, cells = {}, 0
    for cls in range(1, 6):
        boards, chapters = {}, 0
        for board in BOARDS:
            subs = picker(board, cls)
            if not subs:
                continue
            boards[board] = sorted(subs.keys(), key=SUBJECTS.index)
            chapters += sum(len(v) for v in subs.values())
            cells += sum(1 for s in subs if s != "Mathematics")
        union = sorted({s for v in boards.values() for s in v}, key=SUBJECTS.index)
        classes[cls] = {"subjects": union, "boards": boards, "chapters": chapters}
    _COVERAGE = {"classes": classes, "cells": cells,
                 "min_per_subject": MIN_QUESTIONS_PER_SUBJECT,
                 "boards": [b for b in BOARDS if any(b in c["boards"] for c in classes.values())]}
    return _COVERAGE




# ---------- official chapter → KB themes ----------
# The picker offers REAL syllabus chapters (the curriculum cells are transcribed from the official
# books, each with its source URL). The KBs tag facts THEMATICALLY, because one KB serves every
# board. This map, built by kids_quiz/tools/build_chapter_map.py, is the bridge. Where a chapter
# has no credible themes the map says so with an empty list, and serve() reports scope="mixed"
# instead of pretending the sheet is chapter-specific.
_CHMAP_DIR = os.path.join(_ENG, "chapter_map")
_CHMAP_CACHE = {}


def _chapter_map(board, cls, subject):
    key = (str(board), int(cls or 0), str(subject))
    if key in _CHMAP_CACHE:
        return _CHMAP_CACHE[key]
    slug = f"{board}".lower().replace(" ", "") + f"_class{cls}_" + f"{subject}".lower().replace(" ", "")
    path = os.path.join(_CHMAP_DIR, slug + ".json")
    data = {}
    if os.path.exists(path):
        try:
            import json
            data = json.load(open(path, encoding="utf-8")).get("map", {})
        except Exception as exc:
            print(f"[kids] chapter map {slug} unreadable: {str(exc)[:80]}")
    _CHMAP_CACHE[key] = data
    return data


def chapter_entry(board, cls, subject, chapter):
    """This official chapter's mapping entry ({} when unmapped). Matched on the chapter NAME,
    which is what the picker sends. Carries `themes` and a `confidence` earned by the strength
    of the vocabulary evidence — weak evidence must not produce a confident claim."""
    if not chapter:
        return {}
    want = str(chapter).strip().lower()
    for entry in _chapter_map(board, cls, subject).values():
        if str(entry.get("name", "")).strip().lower() == want:
            return entry
    return {}


def themes_for_chapter(board, cls, subject, chapter):
    return chapter_entry(board, cls, subject, chapter).get("themes") or []


# ---------- knowledge generation (LIVE) ----------
# Knowledge subjects used to be served from a frozen 1,000-item bank file, and serve() then drew
# from the ~40 nearest-difficulty items — so a child repeated 57% of questions inside 10 sessions
# while the product promised "never repeats". The KB engine can emit >100k distinct questions per
# cell in ~0.2ms with no network, so we generate at request time instead. The banks stay as a
# fallback for any cell that has no KB.
_SUBJECT_KB = {"evs": "evs", "english": "english", "gk": "gk", "hindi": "hindi"}
_KB_CACHE = {}


def _kb_for(subject, cls):
    """The verified knowledge base for a subject+class, or None. Cached — a KB is a static file
    and re-reading/re-validating it on every request would be wasted work."""
    key = (str(subject).strip().lower(), int(cls or 0))
    if key in _KB_CACHE:
        return _KB_CACHE[key]
    stem = _SUBJECT_KB.get(key[0])
    kb = None
    if stem and 1 <= key[1] <= 5:
        try:
            kb = KBE.load_kb(f"{stem}_class{key[1]}")
        except Exception as exc:
            print(f"[kids] KB {stem}_class{key[1]} unavailable: {str(exc)[:100]}")
    _KB_CACHE[key] = kb
    return kb


def has_kb(subject, cls) -> bool:
    return _kb_for(subject, cls) is not None


def _kb_subset(kb, themes):
    """A KB containing ONLY the entries a chapter's themes cover.

    Generating from the subset beats generating everything and filtering: every question is
    on-theme by construction, and a small theme (say Water — one category and a few facts) still
    fills a sheet instead of being drowned out by the weighted mix across all themes."""
    want = {t.strip().lower() for t in themes}
    sub = {k: v for k, v in kb.items() if k not in ("categories", "groupings", "relations", "facts")}
    for sec in ("categories", "groupings", "relations", "facts"):
        sub[sec] = [e for e in (kb.get(sec) or [])
                    if str(e.get("chapter", "")).strip().lower() in want]
    return sub


def _kb_items(board, subject, cls, chapter, want, n_sheet=8):
    """A FRESH candidate pool, drawn anew on every call (unseeded → different every request),
    narrowed to the chapter as far as the KB honestly allows.

    Returns (items, scope, on_theme). Scope is:
      "chapter" — the whole sheet comes from this chapter's themes
      "partial" — every on-theme question we have, topped up with general practice
      "mixed"   — nothing mapped (or nothing usable), so it's general practice for the subject

    A single theme is often thin — "Water" in Class-3 EVS is one category plus five facts, which
    cannot fill eight questions. Rather than silently serving a general sheet (what used to
    happen) or refusing, we give the child every on-theme question that exists and say what the
    sheet actually is."""
    kb = _kb_for(subject, cls)
    if not kb:
        return [], "mixed", 0
    entry = chapter_entry(board, cls, subject, chapter)
    themes = entry.get("themes") or []
    # A weak lexical match ("Here comes a Letter" → Animals) still yields usable practice, but it
    # has not earned the right to be called this chapter's sheet — cap it at "partial".
    can_claim_chapter = entry.get("confidence") == "high"
    themed = []
    if themes:
        sub = _kb_subset(kb, themes)
        try:
            themed = KBE.generate(sub, max(want // 2, n_sheet * 6), seed=random.randrange(1 << 30))
        except Exception as exc:
            print(f"[kids] themed generate failed ({subject} {cls} {chapter}): {str(exc)[:80]}")
            themed = []
    if len(themed) >= n_sheet * 2 and can_claim_chapter:
        return themed, "chapter", len(themed)
    try:
        general = KBE.generate(kb, want, seed=random.randrange(1 << 30))
    except Exception as exc:
        print(f"[kids] KB generate failed for {subject} class {cls}: {str(exc)[:100]}")
        return (themed, ("chapter" if can_claim_chapter else "partial"), len(themed)) if themed else ([], "mixed", 0)
    if themed:
        # on-theme first so difficulty targeting still prefers them, then general to fill
        seen = {KBE._sig(it) for it in themed}
        return themed + [g for g in general if KBE._sig(g) not in seen], "partial", len(themed)
    return general, "mixed", 0


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
    pool, chapter_scope, on_theme = [], ("chapter" if chapter else "all"), 0
    try:
        if is_math:
            # WE.generate defaults to seed=7 and serve() never passed one, so the "computed,
            # therefore unlimited" subject returned the SAME dozen questions on every request,
            # for every child, forever — 5 distinct across 48 questions when measured. The
            # generator was never the problem; nobody was turning the handle.
            pool = WE.generate(board, cls, subject, chapter, n=max(n * 4, 40),
                               seed=random.randrange(1 << 30))
        else:
            # LIVE from the verified KB — a fresh candidate set every request, so the same child
            # practising the same topic keeps getting new questions. Ask for many more than the
            # sheet needs so difficulty targeting still has choices after the band cut.
            pool, chapter_scope, on_theme = _kb_items(board, subject, cls, chapter, max(n * 20, 160), n)
            if not pool:                      # no KB for this cell → the pre-pooled bank
                pool = _bank_items(board, cls, subject, chapter)
            if not pool:
                pool = WE.generate(board, cls, subject, chapter, n=max(n * 4, 40),
                                   seed=random.randrange(1 << 30))
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
    def _near(cands, k):
        """k items sampled from the candidates nearest the target difficulty."""
        c = sorted(cands, key=lambda it: abs(it.get("difficulty", 0.0) - target_b))
        band = c[:max(k * 5, 40)]
        return random.sample(band, k) if len(band) > k else band[:k]

    if chapter_scope == "partial" and on_theme:
        # _kb_items puts the on-theme items at the head. They must SURVIVE selection — the UI
        # tells the child how many questions came from their chapter, so difficulty targeting
        # is not allowed to quietly drop them.
        head, rest = pool[:on_theme], pool[on_theme:]
        take = min(len(head), n)
        items = _near(head, take) + _near(rest, n - take)
        on_theme = take                          # report what's in the SHEET, not the pool
    else:
        items = _near(pool, n)
        if chapter_scope == "chapter":
            on_theme = len(items)
    random.shuffle(items)                         # and don't present them difficulty-ordered
    return {"skill": skill, "board": board, "class": cls, "subject": subject, "chapter": chapter or "all",
            "items": items, "target_b": round(target_b, 2), "chapter_scope": chapter_scope, "on_theme": on_theme,
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
