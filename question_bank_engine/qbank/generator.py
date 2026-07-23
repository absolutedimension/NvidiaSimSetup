"""Generator agent — the RAG exam-generation loop.

  retrieve tagged exemplars  ->  author a NEW question in that mold (LLM)
     ->  validate (well-formed + answer-correct)  ->  novelty-check vs the bank
     ->  store (generated=True) + assemble into a test

The novelty gate is what keeps the product copyright-clean: a generated question
that is too similar to any exemplar / banked past-paper question is REJECTED and
regenerated. We learn the pattern; we never resell the paper."""
import re

import re
import xml.etree.ElementTree as ET

from . import cleaner, validator
from .models import Question, content_hash, normalize_for_hash, references_figure, repair_latex


def _sanitize_svg(svg: str | None) -> str | None:
    """Make an LLM-produced SVG safe to inline in the frontend: strip scripts, event
    handlers, external links, and foreignObject. Defense-in-depth (frontend should also
    sanitize)."""
    if not svg:
        return None
    s = svg.strip()
    low = s.lower()
    if "<svg" not in low:
        return None
    start = low.find("<svg")
    end = low.rfind("</svg>")
    s = s[start:end + 6] if end != -1 else s[start:]
    s = re.sub(r"<script.*?</script>", "", s, flags=re.I | re.S)
    s = re.sub(r"<foreignObject.*?</foreignObject>", "", s, flags=re.I | re.S)
    s = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", "", s, flags=re.I)   # onclick=…
    s = re.sub(r"\s(?:xlink:href|href)\s*=\s*(\"[^\"]*\"|'[^']*')", "", s, flags=re.I)
    return s.strip()


def _valid_svg(s: str | None) -> bool:
    if not s or not (40 <= len(s) <= 20000):
        return False
    try:
        ET.fromstring(s)                      # must be well-formed XML
    except Exception:
        return False
    return bool(re.search(r"<(path|line|circle|rect|polygon|polyline|ellipse|text|g)\b", s, re.I))

NOVELTY_MAX_SIM = 0.82   # generated stem must be < this cosine vs any real question


# --- retrieval ---------------------------------------------------------------

def retrieve_exemplars(store, spec: dict, k: int = 3) -> list[dict]:
    """Pull real, tagged questions to use as style/difficulty references. Falls back
    progressively so small chapters still generate: exact (type+difficulty) →
    chapter+difficulty → chapter only. If the question's own exam has nothing for that
    chapter, retry the whole ladder against its companion exam (NEET → JEE Main, see
    syllabus.EXEMPLAR_FALLBACK) rather than returning nothing."""
    from . import syllabus

    def _ladder(exam, subject):
        base = dict(exam=exam, subject=subject, chapter=spec.get("chapter"),
                    include_generated=False)
        for filt in (dict(base, qtype=spec.get("qtype"), dmin=spec.get("dmin"), dmax=spec.get("dmax")),
                     dict(base, dmin=spec.get("dmin"), dmax=spec.get("dmax")),
                     dict(base)):
            ex = store.retrieve(limit=k, **filt)
            if ex:
                return ex
        return []

    ex = _ladder(spec.get("exam"), spec.get("subject"))
    if ex:
        return ex
    fb = syllabus.exemplar_fallback(spec.get("exam"), spec.get("subject"))
    return _ladder(*fb) if fb else []


# --- prompt construction (this IS the RAG) -----------------------------------

def _exemplar_block(exemplars: list[dict]) -> str:
    out = []
    for i, e in enumerate(exemplars, 1):
        opts = "  ".join(f"({o['label']}) {o['text']}" for o in e.get("options", []))
        out.append(f"--- EXEMPLAR {i} (difficulty {e.get('difficulty')}) ---\n"
                   f"{e['stem']}\n{opts}\nAnswer: {e['correct_answer']}")
    return "\n\n".join(out)


def build_prompt(spec: dict, exemplars: list[dict]) -> tuple[str, str]:
    n_opts = spec.get("num_options", 4)
    qtype = spec.get("qtype", "MCQ_single")
    kind = {"MCQ_single": f"a single-correct MCQ with exactly {n_opts} options",
            "MCQ_multi": f"a multiple-correct MCQ with {n_opts} options (1+ correct)",
            "integer": "an integer-answer question (answer is a non-negative integer)",
            "numeric": "a numeric-answer question (answer is a decimal)"}.get(qtype, "an MCQ")
    ans_fmt = {
        "MCQ_single": 'EXACTLY ONE option is correct; "correct_answer" is a SINGLE letter, e.g. "B".',
        "MCQ_multi": 'one or more options are correct; "correct_answer" is the correct letters concatenated, e.g. "AC".',
        "integer": 'no options; "correct_answer" is a non-negative integer as a string, e.g. "7".',
        "numeric": 'no options; "correct_answer" is a decimal as a string, e.g. "3.14".',
    }.get(qtype, 'EXACTLY ONE option is correct; "correct_answer" is a single letter.')
    system = (
        "You are an expert author of Indian competitive-exam physics questions. "
        "You write ORIGINAL questions — never copies or paraphrases of existing ones. "
        f'Return JSON: {{"stem":"...","options":[{{"label":"A","text":"..."}}],'
        '"correct_answer":"...","solution":"...","svg":"..."}. Use LaTeX for all math. '
        'The "svg" field is OPTIONAL: include it ONLY if the question cannot be understood '
        "without a diagram (ray-optics setup, electrical circuit, geometry, free-body "
        "diagram, a graph). When you include it, give a SELF-CONTAINED SVG string starting "
        'with <svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg"> using only simple '
        "shapes (line, rect, circle, polygon, path, text) with explicit stroke/fill colors "
        "and clear text labels. NO <script>, NO external images or links, NO CSS classes, "
        "under 3000 characters. If no diagram is needed, omit svg or set it to null. "
        "NEVER put the answer in the diagram."
    )
    user = (
        f"Write ONE brand-new question for:\n"
        f"  Exam: {spec.get('exam')}\n  Subject: {spec.get('subject')}\n"
        f"  Chapter: {spec.get('chapter')}\n  Concept: {spec.get('concept') or 'any within the chapter'}\n"
        f"  Difficulty: {spec.get('dmin')}-{spec.get('dmax')} on a 1-5 scale\n"
        f"  Format: {kind}\n"
        f"  ANSWER FORMAT: {ans_fmt}\n\n"
        "Match the STYLE, rigor, and difficulty of these real exemplars, but invent a "
        "DIFFERENT scenario with DIFFERENT numbers. It must NOT be a reworded exemplar. "
        "The exemplars are ONLY style/difficulty references — follow the Format and Answer "
        "Format above even if an exemplar uses a different format. "
        + ("You MUST design a question that depends on a diagram and include a valid svg. "
           if spec.get("require_figure")
           else "If the physics genuinely needs a diagram to be answerable, include the svg. ")
        + "\n\n"
        f"{_exemplar_block(exemplars)}\n\n"
        "Follow the Answer Format exactly and make the solution prove the answer."
    )
    return system, user


# --- generation --------------------------------------------------------------

def _to_question(data: dict, spec: dict, idx: int) -> Question:
    data = {**data,
            "stem": repair_latex(data.get("stem") or ""),
            "solution": repair_latex(data.get("solution") or ""),
            "options": [{**o, "text": repair_latex(o.get("text", ""))}
                        for o in data.get("options", [])]}
    stem = (data.get("stem") or "").strip()
    svg = _sanitize_svg(data.get("svg"))
    if svg and not _valid_svg(svg):
        svg = None
    needs_fig = bool(svg) or references_figure(stem) or bool(spec.get("require_figure"))
    return Question(
        id=f"gen_{spec.get('subject','').lower()}_{content_hash(stem)}_{idx}",
        exam=spec.get("exam", ""), subject=spec.get("subject", ""),
        stem=stem, qtype=spec.get("qtype", "MCQ_single"),
        options=data.get("options", []), correct_answer=str(data.get("correct_answer", "")).strip(),
        solution=data.get("solution", ""),
        chapter=spec.get("chapter"), concept=spec.get("concept"),
        difficulty=spec.get("dmax") or spec.get("dmin"),
        needs_figure=needs_fig, figure_svg=svg,
        source="generated", generated=True, hash=content_hash(stem),
    )


def _mock_question(spec: dict, idx: int) -> Question:
    """OFFLINE plumbing only — NOT physically meaningful. Requires QBANK_LLM=on for real output."""
    v = 10 + idx * 3
    stem = (f"[MOCK] A demonstration {spec.get('chapter')} problem #{idx}: a system has "
            f"a characteristic value of {v} SI units. Which option follows from the governing law?")
    opts = [{"label": L, "text": f"result equals {v * m}"} for L, m in zip("ABCD", (2, 1, 3, 4))]
    q = _to_question({"stem": stem, "options": opts, "correct_answer": "A",
                      "solution": f"By the governing relation, result = 2*{v}."}, spec, idx)
    return q


def novelty(gen_q: Question, references: list[str]) -> float:
    """Max cosine similarity of the generated stem vs any reference (real) question."""
    refs = [normalize_for_hash(r) for r in references if r]
    text = normalize_for_hash(gen_q.stem)
    if not refs or not text:
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        X = TfidfVectorizer(min_df=1).fit_transform([text] + refs)
        return float(cosine_similarity(X[0:1], X[1:]).ravel().max())
    except Exception:
        # jaccard fallback
        a = set(text.split())
        return max((len(a & set(r.split())) / max(1, len(a | set(r.split()))) for r in refs), default=0.0)


def generate_one(spec, exemplars, llm, idx, mock=False):
    if mock:
        return _mock_question(spec, idx), None
    system, user = build_prompt(spec, exemplars)
    data = llm.chat_json(system, user)
    if not data:
        return None, "llm_no_output"
    return _to_question(data, spec, idx), None


def generate_test(store, spec: dict, llm=None, count: int = 5, k_exemplars: int = 3,
                  max_retries: int = 2, mock: bool = False) -> dict:
    exemplars = retrieve_exemplars(store, spec, k=k_exemplars)
    if not exemplars and not mock:
        return {"error": f"no exemplars for spec {spec} — tag/ingest that chapter first",
                "questions": []}

    # reference corpus for novelty: the exemplars + a wider slice of the same chapter
    ref_pool = [e["stem"] for e in exemplars]
    ref_pool += [r["stem"] for r in store.retrieve(
        subject=spec.get("subject"), chapter=spec.get("chapter"), limit=50, include_generated=False)]

    accepted, rejected = [], []
    for i in range(count):
        for attempt in range(max_retries + 1):
            q, err = generate_one(spec, exemplars, llm, idx=i, mock=mock)
            if q is None:
                rejected.append({"slot": i, "reason": err})
                break
            issues = validator.rule_check(q)
            if q.needs_figure and not q.figure_svg:
                issues.append("figure_required_but_missing")
            if not issues and llm is not None and getattr(llm, "ok", False):
                issues += validator.llm_check(q, llm)
            sim = novelty(q, ref_pool + [a.stem for a in accepted])
            if sim >= NOVELTY_MAX_SIM:
                issues.append(f"too_similar_to_bank({sim:.2f})")
            if issues:
                if attempt == max_retries:
                    rejected.append({"slot": i, "reason": issues})
                continue
            q.verified = True
            store.upsert(q)
            accepted.append(q)
            ref_pool.append(q.stem)
            break

    return {
        "spec": spec,
        "exemplars_used": [e["id"] for e in exemplars],
        "requested": count,
        "generated": len(accepted),
        "rejected": rejected,
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
        "mock": mock,
        "llm_used": bool(llm and getattr(llm, "ok", False)),
    }
