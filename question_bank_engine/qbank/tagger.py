"""Tagging agent — assigns chapter / concept / difficulty / bloom to a question.

This is what makes RETRIEVAL possible ("15 medium Rotational-Motion MCQs").

Two paths, same output contract:
  LLM (preferred) : classify against the syllabus chapter list + calibrated difficulty.
  keyword (fallback): score the question text against the syllabus keyword signatures.

Difficulty is 1..5 (LLM-calibrated when available; heuristic otherwise). Chapter is
always constrained to the taxonomy — never free-text — so retrieval filters stay clean."""
import re

from . import syllabus as syl

_BLOOM = ["Remember", "Understand", "Apply", "Analyze", "Evaluate"]


def _norm(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"\\[a-zA-Z]+", " ", t)       # drop LaTeX command names
    t = re.sub(r"[^a-z0-9'\- ]+", " ", t)     # keep words, apostrophes, hyphens
    return re.sub(r"\s+", " ", t)


def _text_of(q) -> str:
    return _norm(q.stem + " " + " ".join(o.get("text", "") for o in q.options))


# --- keyword fallback --------------------------------------------------------

def keyword_classify(q, taxonomy) -> dict:
    text = _text_of(q)
    best_ch, best_score = None, 0
    for chapter, data in taxonomy.items():
        score = sum(text.count(k) for k in data["keywords"])
        if score > best_score:
            best_ch, best_score = chapter, score
    concept = None
    confidence = "low"
    if best_ch:
        confidence = "medium" if best_score >= 2 else "low"
        best_c, best_cs = None, 0
        for cname, ckw in taxonomy[best_ch]["concepts"].items():
            cs = sum(text.count(k) for k in ckw)
            if cs > best_cs:
                best_c, best_cs = cname, cs
        concept = best_c
    return {"chapter": best_ch, "concept": concept, "confidence": confidence,
            "keyword_hits": best_score}


def estimate_difficulty(q) -> int:
    """Rough proxy from structural signals; LLM overrides when available."""
    s = q.stem
    score = 2
    if len(s) > 400:
        score += 1
    if len(s) > 800:
        score += 1
    if q.qtype in ("integer", "numeric"):
        score += 1
    if q.qtype == "MCQ_multi":
        score += 1
    if len(re.findall(r"\d", s)) > 25:   # many given quantities -> multi-step
        score += 1
    return max(1, min(5, score))


def guess_bloom(q) -> str:
    if q.qtype in ("integer", "numeric"):
        return "Apply"
    if q.qtype == "MCQ_multi":
        return "Analyze"
    return "Understand"


# --- LLM path ----------------------------------------------------------------

def _llm_sys(chapters: list[str]) -> str:
    return (
        "You are a syllabus expert for Indian competitive exams. Classify the question "
        "into EXACTLY ONE chapter from this list (copy the name verbatim):\n- "
        + "\n- ".join(chapters)
        + "\nAlso give the specific concept, a difficulty 1-5 (1=trivial recall, "
        "5=hardest multi-step JEE-Advanced), and a Bloom level "
        "(Remember/Understand/Apply/Analyze/Evaluate). "
        'Return JSON {"chapter":"...","concept":"...","difficulty":int,"bloom":"...","confidence":"high|medium|low"}.'
    )


def llm_classify(q, taxonomy, llm) -> dict | None:
    if not llm.ok:
        return None
    chapters = list(taxonomy.keys())
    payload = (f"EXAM: {q.exam}  SUBJECT: {q.subject}  TYPE: {q.qtype}\n"
               f"QUESTION: {q.stem}\nOPTIONS: {q.options}")
    res = llm.chat_json(_llm_sys(chapters), payload)
    if not res:
        return None
    ch = res.get("chapter")
    if ch not in taxonomy:                      # snap to nearest valid chapter
        ch = next((c for c in taxonomy if c.lower() in (ch or "").lower()), None)
    if not ch:
        return None
    d = res.get("difficulty")
    try:
        d = max(1, min(5, int(d)))
    except (TypeError, ValueError):
        d = estimate_difficulty(q)
    bloom = res.get("bloom") if res.get("bloom") in _BLOOM else guess_bloom(q)
    return {"chapter": ch, "concept": res.get("concept"), "difficulty": d,
            "bloom": bloom, "confidence": res.get("confidence", "medium")}


def tag_question(q, llm=None, taxonomy=None) -> dict:
    taxonomy = taxonomy or syl.get_taxonomy(q.exam, q.subject)
    # No taxonomy for this (exam, subject) → leave it Unclassified instead of asking the LLM to
    # pick from an empty/foreign chapter list. (get_taxonomy used to hand back JEE Physics here,
    # which risked filing e.g. a BPSC polity question under "Kinematics".)
    if not taxonomy:
        return {"chapter": "Unclassified", "concept": None,
                "difficulty": estimate_difficulty(q), "bloom": guess_bloom(q),
                "confidence": "low"}
    tags = llm_classify(q, taxonomy, llm) if llm is not None else None
    if tags is None:                            # fallback
        kw = keyword_classify(q, taxonomy)
        tags = {"chapter": kw["chapter"], "concept": kw["concept"],
                "difficulty": estimate_difficulty(q), "bloom": guess_bloom(q),
                "confidence": kw["confidence"]}
    if not tags["chapter"]:
        tags["chapter"] = "Unclassified"
        tags["confidence"] = "low"
    return tags
