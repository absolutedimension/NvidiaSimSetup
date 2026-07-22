"""Dynamic assessment generation — turn any exam/topic into a validated, adaptive test.

Pipeline (all in-LMS, code owns the score):
  1. GENERATE candidate questions with Azure gpt-4o-mini (JSON output), bilingual EN+हिं.
  2. VALIDATE each: structural checks + a KEY-WITHHELD independent-solver pass (a second LLM
     call that must re-derive the same answer). Only items that survive are ever served.
  3. CACHE validated items in the AssessmentItem bank so repeat/other students are instant.
  4. ASSEMBLE a pack in the exact shape the assess.html engine consumes (window.__PACK).

v1 generates MCQ + True/False only (both deterministically gradable). Numeric (with sympy
recompute) and match come later. Free-text is never generated (it can't be honestly graded).
"""
import json
import re
import urllib.request
import urllib.error

from .config import settings

GEN_MODEL_NOTE = "azure/gpt-4o-mini"


def available() -> bool:
    return bool(settings.AOAI_ENDPOINT and settings.AOAI_KEY)


def _azure_json(system: str, user: str, *, max_tokens: int = 1600, temperature: float = 0.4) -> dict | None:
    """One Azure chat call constrained to a JSON object. Returns the parsed dict or None."""
    if not available():
        return None
    url = (f"{settings.AOAI_ENDPOINT}/openai/deployments/{settings.AOAI_DEPLOYMENT}"
           f"/chat/completions?api-version={settings.AOAI_API_VERSION}")
    payload = json.dumps({
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature, "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
                                headers={"Content-Type": "application/json", "api-key": settings.AOAI_KEY})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        print(f"[assess_gen] Azure call failed: {exc}")
        return None


# ---------------------------------------------------------------- generation
_GEN_SYSTEM = (
    "You are an expert question-writer for Indian competitive and school/board exams (JEE, NEET, "
    "CBSE/State boards, and similar). You write ACCURATE, curriculum-appropriate practice questions "
    "with unambiguous single correct answers. You output STRICT JSON only — no prose, no markdown."
)


def _gen_user(exam_title: str, n: int) -> str:
    return (
        f"Write {n} exam-practice questions for: \"{exam_title}\".\n"
        "Requirements:\n"
        "- Mix of two types: \"mcq\" (exactly 4 options, exactly ONE correct) and \"truefalse\".\n"
        "- Cover a VARIETY of distinct sub-topics from this exam. Real syllabus content, factual, unambiguous.\n"
        "- For EVERY text field give BOTH English (en) and Hindi (hi).\n"
        "- 'topic' = the concept being tested, 2-4 words.\n"
        "- 'explain' = one short line why the answer is correct.\n"
        "- For mcq: 'correct' is the 0-based index of the correct option. Options must be distinct, non-empty, "
        "and NOT 'all/none of the above'. Do not make the correct option always the longest.\n"
        "- For truefalse: 'answer' is a boolean.\n"
        "Return JSON EXACTLY like:\n"
        "{\"questions\":[\n"
        "  {\"type\":\"mcq\",\"topic\":{\"en\":\"...\",\"hi\":\"...\"},\"correct\":1,"
        "\"en\":{\"q\":\"...\",\"opts\":[\"..\",\"..\",\"..\",\"..\"],\"explain\":\"...\"},"
        "\"hi\":{\"q\":\"...\",\"opts\":[\"..\",\"..\",\"..\",\"..\"],\"explain\":\"...\"}},\n"
        "  {\"type\":\"truefalse\",\"topic\":{\"en\":\"...\",\"hi\":\"...\"},\"answer\":true,"
        "\"en\":{\"q\":\"...\",\"explain\":\"...\"},\"hi\":{\"q\":\"...\",\"explain\":\"...\"}}\n"
        "]}"
    )


def _struct_ok(q: dict) -> bool:
    """Structural validity — cheap checks before spending an LLM verify call."""
    try:
        t = q.get("type")
        for lang in ("en", "hi"):
            v = q.get(lang) or {}
            if not str(v.get("q", "")).strip():
                return False
        tp = q.get("topic") or {}
        if not str(tp.get("en", "")).strip() or not str(tp.get("hi", "")).strip():
            return False
        if t == "mcq":
            if not isinstance(q.get("correct"), int) or not (0 <= q["correct"] <= 3):
                return False
            for lang in ("en", "hi"):
                opts = (q.get(lang) or {}).get("opts")
                if not isinstance(opts, list) or len(opts) != 4:
                    return False
                cleaned = [str(o).strip() for o in opts]
                if any(not o for o in cleaned) or len(set(cleaned)) != 4:
                    return False
                if any(re.search(r"\b(all|none) of the above\b", o, re.I) for o in cleaned):
                    return False
            return True
        if t == "truefalse":
            return isinstance(q.get("answer"), bool)
        return False
    except Exception:
        return False


def generate_candidates(exam_title: str, n: int = 8) -> list[dict]:
    """Ask the LLM for n candidate questions; keep the structurally-valid ones."""
    out = _azure_json(_GEN_SYSTEM, _gen_user(exam_title, n), max_tokens=2200)
    if not out:
        return []
    qs = out.get("questions") if isinstance(out, dict) else None
    if not isinstance(qs, list):
        return []
    return [q for q in qs if isinstance(q, dict) and q.get("type") in ("mcq", "truefalse") and _struct_ok(q)]


# ---------------------------------------------------------------- verification
_VERIFY_SYSTEM = (
    "You are a meticulous exam solver. You will be given practice questions WITHOUT their answer keys. "
    "Solve each independently and correctly. Output STRICT JSON only."
)


def _verify_user(cands: list[dict]) -> str:
    items = []
    for i, q in enumerate(cands):
        e = q.get("en", {})
        if q["type"] == "mcq":
            items.append({"i": i, "type": "mcq", "q": e.get("q", ""), "opts": e.get("opts", [])})
        else:
            items.append({"i": i, "type": "truefalse", "q": e.get("q", "")})
    return (
        "Solve each question. Return JSON {\"answers\":[{\"i\":<index>,\"a\":<answer>}]} where for an "
        "mcq \"a\" is the 0-based index of the correct option, and for a truefalse \"a\" is true/false. "
        "Answer ONLY from your own knowledge; if a question is ambiguous or you are unsure, set \"a\":\"unsure\".\n"
        + json.dumps({"questions": items}, ensure_ascii=False)
    )


def verify_candidates(cands: list[dict]) -> list[dict]:
    """Key-withheld independent solve. Keep only candidates whose stated key the solver reproduces."""
    if not cands:
        return []
    out = _azure_json(_VERIFY_SYSTEM, _verify_user(cands), max_tokens=900, temperature=0.0)
    if not out:
        return []   # can't verify -> ship nothing (honesty over coverage)
    ans = {a.get("i"): a.get("a") for a in (out.get("answers") or []) if isinstance(a, dict)}
    kept = []
    for i, q in enumerate(cands):
        got = ans.get(i)
        if q["type"] == "mcq":
            if isinstance(got, int) and got == q.get("correct"):
                kept.append(q)
        else:  # truefalse
            if isinstance(got, bool) and got == q.get("answer"):
                kept.append(q)
    return kept


def generate_validated(exam_title: str, want: int = 5) -> list[dict]:
    """End-to-end: generate -> structural filter -> independent-solver verify. Returns validated questions."""
    cands = generate_candidates(exam_title, n=max(want + 3, 8))
    if not cands:
        return []
    validated = verify_candidates(cands)
    return validated[:want]


# ---------------------------------------------------------------- assembly
def _intro(title: str, n: int, lang: str) -> str:
    if lang == "hi":
        return f"नमस्ते 🙏 <b>{title}</b> का क्विक adaptive टेस्ट — {n} सवाल। बस tap करें।"
    return f"Namaste 🙏 A quick <b>{title}</b> adaptive test — {n} questions. Just tap to answer."


def question_to_engine(q: dict) -> dict:
    """Map a validated candidate/DB item into the exact shape assess.html expects."""
    tp = q.get("topic") or {"en": "Concept", "hi": "अवधारणा"}
    e, h = q.get("en", {}), q.get("hi", {})
    base = {"type": q["type"],
            "en": {"tag": tp.get("en", ""), "q": e.get("q", ""), "explain": e.get("explain", "")},
            "hi": {"tag": tp.get("hi", ""), "q": h.get("q", ""), "explain": h.get("explain", "")},
            "_topic": tp}
    if q["type"] == "mcq":
        base["correct"] = int(q.get("correct", 0))
        base["en"]["opts"] = q["en"].get("opts", [])
        base["hi"]["opts"] = q["hi"].get("opts", [])
    else:
        base["answer"] = bool(q.get("answer"))
    return base


def build_pack(exam_title: str, questions: list[dict], topic_line: dict | None = None) -> dict:
    """Assemble a full pack (title, topic, intro, topicMap, questions) for window.__PACK."""
    eng = [question_to_engine(q) for q in questions]
    topic_map = [q.pop("_topic") for q in eng]
    tline = topic_line or {"en": "Adaptive practice test", "hi": "Adaptive अभ्यास टेस्ट"}
    n = len(eng)
    return {
        "title": exam_title,
        "topic": tline,
        "intro": {"en": _intro(exam_title, n, "en"), "hi": _intro(exam_title, n, "hi")},
        "topicMap": topic_map,
        "questions": eng,
    }
