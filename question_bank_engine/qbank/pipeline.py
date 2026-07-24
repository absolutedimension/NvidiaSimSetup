"""Orchestrator — wires the agents together and returns a run report.

    collector -> extractor -> (keymatch) -> cleaner -> validator -> store
"""
from . import cleaner, collector, extractor, keymatch, validator
from .llm import LLM
from .storage import Store


def ingest_open_dataset(dataset="daman1209arora/jeebench", subject="phy",
                        limit=40, exam="JEE Advanced", subject_name="Physics",
                        llm_validate=False,
                        store: Store | None = None, llm: LLM | None = None) -> dict:
    """Ingest a structured open dataset (jeebench-style: inline options + `gold`).
    By default validation is RULE-BASED (llm_validate=False) — the dataset already
    carries gold answers, and the LLM well-formedness check spuriously rejects valid
    integer/numeric questions (no options) + hard multi-part ones. Pass llm_validate=True
    to also run the LLM check (slower, stricter)."""
    store = store or Store()
    llm = llm if llm is not None else LLM()

    # 1. collect
    rows = collector.fetch_open_dataset(dataset, subject=subject, limit=limit)
    # 2. extract
    questions = [extractor.from_dataset_row(r, exam=exam, subject=subject_name) for r in rows]
    # 3. keymatch — dataset rows already carry answers (extractor set them); no-op here.
    # 4. clean + dedup (against what's already banked, and within batch)
    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    # 5. validate
    validator.validate(questions, llm=(llm if llm_validate else None))
    # 6. store
    for q in questions:
        store.upsert(q)

    return _report(questions, llm)


def ingest_grafite(dataset="ruh-ai/grafite-jee-mains-qna-no-img", subject="physics",
                   exam="JEE Main", subject_name="Physics", limit=None,
                   default_difficulty=2, llm_validate=False,
                   store: Store | None = None, llm: LLM | None = None) -> dict:
    """Ingest the grafite JEE-Main bank — pre-tagged (chapter/topic) + pre-solved
    (answer + worked solution) TEXT questions, no vision needed. Uses the HF `datasets`
    library (full ~11k-row load, filtered to `subject`). By default validation is
    RULE-BASED only (llm_validate=False) so it doesn't fire thousands of LLM calls;
    the answers come from the dataset, and a separate flag-pass can audit keys later."""
    from datasets import load_dataset
    store = store or Store()
    llm = llm if llm is not None else LLM()

    ds = load_dataset(dataset, split="train")
    rows = [r for r in ds if str(r.get("subject", "")).lower() == subject.lower()]
    if limit:
        rows = rows[:limit]
    questions = []
    for r in rows:
        q = extractor.from_grafite_row(r, exam=exam, subject=subject_name,
                                       default_difficulty=default_difficulty)
        if q:
            questions.append(q)
    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    validator.validate(questions, llm=(llm if llm_validate else None))
    for q in questions:
        store.upsert(q)

    rep = _report(questions, llm)
    rep["source_rows"] = len(rows)
    return rep


def ingest_datavorous(dataset="datavorous/entrance-exam-dataset", want_exam="NEET",
                      subjects=None, limit=None, default_difficulty=2, llm_validate=False,
                      figures_only=False,
                      store: Store | None = None, llm: LLM | None = None) -> dict:
    """Ingest the datavorous entrance-exam bank — pre-tagged (subject/chapter/exam),
    pre-keyed (li.correct, cross-checked vs correct_option) and pre-solved (answer),
    all in HTML. No LLM needed. `want_exam` picks the exam by tag; `subjects` (a set of
    canonical subject names) optionally narrows further. Rule-based validation by
    default — the keys are already cross-checked in the extractor.

    `figures_only=True` ingests ONLY rows carrying an <img> diagram — used to ADD the
    diagram questions of an exam whose text bank already exists from another source
    (e.g. JEE Main from grafite), without re-importing/duplicating its text questions.
    figure recovery (recover_datavorous_figures.py) then attaches the actual images."""
    from datasets import load_dataset
    store = store or Store()
    llm = llm if llm is not None else LLM()

    ds = load_dataset(dataset, split="train")
    questions, seen_bad_exam, seen_bad_subj, seen_no_fig = [], 0, 0, 0
    for r in ds:
        if want_exam not in (r.get("tags") or ""):
            seen_bad_exam += 1
            continue
        if figures_only and not extractor._HTML_IMG.search(
                (r.get("question") or "") + " " + (r.get("options") or "")):
            seen_no_fig += 1
            continue
        q = extractor.from_datavorous_row(r, want_exam=want_exam,
                                          default_difficulty=default_difficulty)
        if not q:
            continue
        if subjects and q.subject not in subjects:
            seen_bad_subj += 1
            continue
        if figures_only:
            # datavorous chapter names only partly match an exam that already has a
            # taxonomy from another source (JEE), so clear the chapter → these land as
            # UNTAGGED and `run.py tag` LLM-classifies them into the existing taxonomy.
            q.chapter = None
        questions.append(q)
        if limit and len(questions) >= limit:
            break

    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    validator.validate(questions, llm=(llm if llm_validate else None))
    for q in questions:
        store.upsert(q)

    rep = _report(questions, llm)
    rep["skipped_wrong_subject"] = seen_bad_subj
    return rep


def ingest_neet_bio(dataset="sweatSmile/neet-biology-qa", exam="NEET", subject_name="Biology",
                    limit=None, default_difficulty=2, llm_validate=False,
                    store: Store | None = None, llm: LLM | None = None) -> dict:
    """Ingest a plain-text NEET Biology bank (sweatSmile schema: question / choices[] /
    answer). Rule-based validation by default — same reasoning as ingest_grafite: the
    rows carry keys, and these are RAG exemplars rather than a graded set. Chapter tags
    and worked solutions are added downstream by `retag` + `enrich-solutions`."""
    store = store or Store()
    llm = llm if llm is not None else LLM()

    rows = collector.fetch_open_dataset(dataset, subject=None,
                                        limit=limit or 10 ** 6, split="train")
    questions = []
    for r in rows:
        q = extractor.from_neet_bio_row(r, exam=exam, subject=subject_name,
                                        default_difficulty=default_difficulty)
        if q:
            questions.append(q)
    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    validator.validate(questions, llm=(llm if llm_validate else None))
    for q in questions:
        store.upsert(q)

    rep = _report(questions, llm)
    rep["source_rows"] = len(rows)
    return rep


def ingest_pdf(pdf_path, key_path=None, exam="JEE Advanced", subject="Physics",
               year=None, store: Store | None = None, llm: LLM | None = None) -> dict:
    """Production PDF path. Requires the vision LLM (QBANK_LLM on/auto + reachable)."""
    store = store or Store()
    llm = llm if llm is not None else LLM()

    questions = extractor.from_pdf(pdf_path, llm, exam=exam, subject=subject, year=year)
    if key_path:
        try:
            import fitz
            key_text = "\n".join(p.get_text() for p in fitz.open(key_path))
            keymatch.attach(questions, keymatch.parse_key_text(key_text))
        except Exception:
            pass
    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    validator.validate(questions, llm=llm)
    for q in questions:
        store.upsert(q)
    return _report(questions, llm)


def ingest_image_dataset(dataset="Reja1/jee-neet-benchmark", exam_prefix="JEE",
                         subject="Physics", limit=None, exam="JEE Advanced",
                         store: Store | None = None, llm: LLM | None = None) -> dict:
    """Ingest an image-based dataset (questions as PNGs, answers in metadata) via the
    vision LLM. Answers come from metadata, so no keymatch step. Semantic LLM validation
    is skipped (these are real past-paper questions); rule + novelty checks still run."""
    store = store or Store()
    llm = llm if llm is not None else LLM()
    if not llm.ok:
        return {"error": f"vision LLM required (QBANK_LLM proxy): {llm.last_error}", "questions": []}

    rows = collector.fetch_image_dataset(dataset, exam_prefix=exam_prefix, subject=subject, limit=limit)
    questions, failed = [], 0
    for i, row in enumerate(rows, 1):
        try:
            q = extractor.from_image_row(row, llm, exam=exam, subject=subject)
        except Exception:
            q = None
        if q:
            questions.append(q)
        else:
            failed += 1
        if i % 10 == 0:
            print(f"  extracted {i}/{len(rows)} ({failed} unreadable)")

    cleaner.clean(questions)
    cleaner.flag_duplicates(questions, existing_hashes=store.existing_hashes())
    validator.validate(questions, llm=None)   # rule-only; content is real past-paper
    for q in questions:
        store.upsert(q)
    rep = _report(questions, llm)
    rep["source_rows"] = len(rows)
    rep["unreadable"] = failed
    return rep


def enrich_solutions(chapter=None, limit=None, exam=None, subject=None,
                     store: Store | None = None, llm: LLM | None = None) -> dict:
    """Write + validate worked solutions for real questions missing one. Skips
    needs_figure questions (can't solve reliably from text alone)."""
    from . import solver
    store = store or Store()
    llm = llm if llm is not None else LLM()
    if not llm.ok:
        return {"error": f"LLM required: {llm.last_error}"}
    all_missing = store.iter_real(chapter=chapter, missing_solution=True, limit=limit,
                                  exam=exam, subject=subject)
    qs = [q for q in all_missing if not q.needs_figure]
    skipped = len(all_missing) - len(qs)
    agree = review = failed = 0
    for i, q in enumerate(qs, 1):
        res = solver.solve(q, llm)
        if not res or not res["solution"]:
            failed += 1
            continue
        if solver.answers_match(q, res["final_answer"]):
            store.set_solution(q.id, res["solution"])        # independent solve = official → trust
            agree += 1
        else:
            # independent solve disagreed with the key: write a solution TOWARD the official
            # answer (never show the contradicting one) and flag for human review.
            expl = solver.explain(q, llm) or res["solution"]
            store.set_solution(q.id, expl, "solution_needs_review")
            review += 1
        if i % 10 == 0:
            print(f"  solved {i}/{len(qs)} (verified {agree}, needs-review {review})")
    return {"targeted": len(qs), "verified": agree, "needs_review": review,
            "failed": failed, "skipped_needs_figure": skipped}


def reverify_solutions(chapter=None, k=5, limit=None, exam=None, subject=None,
                       store: Store | None = None, llm: LLM | None = None) -> dict:
    """Self-consistency re-check of `needs_review` questions: solve k times, majority-vote.
    If the majority agrees with the official answer, promote to a VERIFIED solution
    (clear the flag). Otherwise it stays flagged for human review."""
    from . import solver
    store = store or Store()
    llm = llm if llm is not None else LLM()
    if not llm.ok:
        return {"error": f"LLM required: {llm.last_error}"}
    qs = [q for q in store.iter_real(chapter=chapter, limit=limit, exam=exam, subject=subject)
          if "solution_needs_review" in (q.validation_issues or []) and not q.needs_figure]
    promoted = still = failed = 0
    for i, q in enumerate(qs, 1):
        res = solver.solve_consistent(q, llm, k=k)
        if not res:
            failed += 1
            continue
        official = solver.canon(q, q.correct_answer)
        if res["majority"] == official and res["votes"] >= (res["k"] // 2 + 1):
            # majority self-consistent solve now matches the official key -> trust it
            issues = [x for x in q.validation_issues if x != "solution_needs_review"]
            store.con.execute("UPDATE questions SET solution=?, validation_issues=? WHERE id=?",
                              (res["solution"] or q.solution,
                               __import__("json").dumps(issues), q.id))
            store.con.commit()
            promoted += 1
        else:
            still += 1
        if i % 10 == 0:
            print(f"  reverified {i}/{len(qs)} (promoted {promoted}, still-review {still})")
    return {"reviewed": len(qs), "promoted_to_verified": promoted,
            "still_needs_review": still, "failed": failed}


def retag(chapter=None, limit=None, exam=None, subject=None,
          store: Store | None = None, llm: LLM | None = None) -> dict:
    """Re-tag real questions with the LLM (accurate concept + calibrated difficulty),
    overwriting keyword tags. Scope with exam/subject — unscoped means the WHOLE bank."""
    from . import tagger
    store = store or Store()
    llm = llm if llm is not None else LLM()
    if not llm.ok:
        return {"error": f"LLM required: {llm.last_error}"}
    qs = store.iter_real(chapter=chapter, limit=limit, exam=exam, subject=subject)
    conf = {}
    for i, q in enumerate(qs, 1):
        t = tagger.tag_question(q, llm=llm)
        store.update_tags(q.id, t["chapter"], t["concept"], t["difficulty"], t["bloom"])
        conf[t["confidence"]] = conf.get(t["confidence"], 0) + 1
        if i % 20 == 0:
            print(f"  retagged {i}/{len(qs)}")
    return {"retagged": len(qs), "confidence": conf}


def mark_needs_figure(store: Store | None = None) -> dict:
    """Flag every question whose text refers to a diagram/graph/circuit. Cheap, no LLM."""
    from .models import references_figure
    store = store or Store()
    rows = store.rows_id_stem()
    flagged = 0
    for qid, stem, furl in rows:
        need = references_figure(stem) or bool(furl)
        store.set_needs_figure(qid, need)
        flagged += int(need)
    return {"scanned": len(rows), "needs_figure": flagged}


def backfill_image_figures(dataset="Reja1/jee-neet-benchmark", exam_prefix="JEE",
                           subject="Physics", exam="JEE Advanced",
                           store: Store | None = None) -> dict:
    """Re-download the original PNG for already-ingested image questions and attach it
    as their figure. No LLM — pure image fetch. Idempotent."""
    import os
    import urllib.request
    from . import config
    from .models import references_figure
    store = store or Store()
    os.makedirs(config.FIG_DIR, exist_ok=True)
    id_stem = {r[0]: r[1] for r in store.rows_id_stem()}
    rows = collector.fetch_image_dataset(dataset, exam_prefix=exam_prefix, subject=subject)
    prefix = extractor.image_id_prefix(exam, subject)
    saved, missing = 0, 0
    for row in rows:
        qid = f"{prefix}_{row['exam_year']}_{row['question_id']}"
        if qid not in id_stem:
            missing += 1
            continue
        try:
            img = urllib.request.urlopen(row["image_url"], timeout=45).read()
            with open(os.path.join(config.FIG_DIR, f"{qid}.png"), "wb") as f:
                f.write(img)
            url = f"{config.PUBLIC_BASE}/figures/{qid}.png"
            store.update_figure(qid, url, references_figure(id_stem[qid]))
            saved += 1
        except Exception:
            pass
    return {"dataset_rows": len(rows), "figures_saved": saved, "not_in_bank": missing}


def batch_generate(exam="JEE Advanced", subject="Physics", per_cell=15,
                   difficulties=("2-3", "3-4"), qtypes=("MCQ_single",),
                   chapters=None, k_exemplars=3, store: Store | None = None,
                   llm: LLM | None = None, on_progress=None) -> dict:
    """PRE-FILL the shared question pool across a subject's taxonomy so the frontend can
    serve questions INSTANTLY (no LLM in the hot path). For each
    (chapter × difficulty-band × qtype) cell it tops up to `per_cell` verified questions,
    SKIPPING cells already at target — so the fill is resumable and idempotent. The
    generated Qs persist automatically (generator.generate_test upserts them with
    generated=1, verified=1); `pool_questions` then serves them. Run it in the background
    per subject; re-run any time to top up drained cells.

    This is the batch engine behind the 'shared pool + live top-up for power users' model:
    everyone reads the pool; live /generate only fires when an active student drains a cell.
    """
    from . import generator, syllabus
    store = store or Store()
    llm = llm if llm is not None else LLM()
    if not llm.ok:
        return {"error": f"LLM required for generation: {llm.last_error}"}

    tax = syllabus.get_taxonomy(exam, subject)
    chapter_list = chapters or list(tax.keys())
    have = store.pool_stats(exam, subject)          # (chapter, difficulty, qtype) -> count
    made = cells = skipped = failed = 0

    for ch in chapter_list:
        for band in difficulties:
            lo, hi = int(band.split("-")[0]), int(band.split("-")[-1])
            for qt in qtypes:
                cells += 1
                existing = sum(v for (c, d, t), v in have.items()
                               if c == ch and t == qt and d is not None and lo <= d <= hi)
                need = per_cell - existing
                if need <= 0:
                    skipped += 1
                    if on_progress:
                        on_progress(ch, band, qt, 0, 0, existing)
                    continue
                spec = {"exam": exam, "subject": subject, "chapter": ch, "concept": None,
                        "qtype": qt, "dmin": lo, "dmax": hi, "require_figure": False}
                try:
                    rep = generator.generate_test(store, spec, llm=llm, count=need,
                                                  k_exemplars=k_exemplars)
                except Exception:
                    failed += 1
                    continue
                g = rep.get("generated", 0)
                made += g
                if on_progress:
                    on_progress(ch, band, qt, g, need, existing + g)

    return {"exam": exam, "subject": subject, "per_cell_target": per_cell,
            "cells": cells, "cells_skipped_full": skipped, "cells_failed": failed,
            "questions_generated": made,
            "pool_total_now": sum(store.pool_stats(exam, subject).values())}


def _report(questions, llm) -> dict:
    dupes = [q for q in questions if q.duplicate_of]
    unique = [q for q in questions if not q.duplicate_of]
    verified = [q for q in unique if q.verified]
    rejected = [q for q in unique if not q.verified]
    reasons = {}
    for q in rejected:
        for i in q.validation_issues:
            reasons[i] = reasons.get(i, 0) + 1
    return {
        "processed": len(questions),
        "duplicates_flagged": len(dupes),
        "unique": len(unique),
        "verified_clean": len(verified),
        "rejected": len(rejected),
        "rejection_reasons": dict(sorted(reasons.items(), key=lambda x: -x[1])),
        "llm_used": bool(llm and llm.ok),
        "llm_note": None if (llm and llm.ok) else f"rule-based only ({getattr(llm,'last_error',None)})",
    }
