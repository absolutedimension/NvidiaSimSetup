"""Solution agent — writes a worked solution AND validates it against the official
answer. The model solves INDEPENDENTLY (not told the answer), then we compare its
derived answer to the banked answer:
  agree    -> store the solution (it explains the correct answer)
  disagree -> store it but flag 'solution_mismatch' (bad extraction / hard question / mis-key)

That mismatch flag is a free quality gate — it surfaces questions not safe to grade on."""
import re

from .models import repair_latex

_ANSWER_FORMAT = (
    "final_answer format: MCQ_single -> one letter (e.g. B); MCQ_multi -> letters (e.g. AC); "
    "integer -> the integer; numeric -> the decimal."
)

_SYS = (
    "You are an expert JEE physics solver. Solve the question INDEPENDENTLY and rigorously "
    "from first principles. Return JSON "
    '{"solution":"step-by-step worked solution using LaTeX $...$","final_answer":"..."}. '
    + _ANSWER_FORMAT +
    " Base final_answer ONLY on your own derivation."
)

# Factual-RECALL domains (maritime/GP-Rating, static GK, regulations, trade knowledge).
# The derivation prompt above is actively harmful here: there is nothing to derive, and
# demanding "first principles" + LaTeX pushes the model to invent a rationale for a
# guess. This variant asks for domain recall and — critically — licenses "UNSURE", so a
# question the model does not actually know fails the audit instead of being confabulated
# into a confident wrong vote.
_SYS_RECALL = (
    "You are a subject-matter expert in merchant-navy / maritime operations, marine "
    "engineering, workshop practice and shipboard safety, answering a multiple-choice "
    "question from an entrance exam. Answer INDEPENDENTLY from your own domain knowledge. "
    'Return JSON {"solution":"brief factual justification, plain text, no LaTeX",'
    '"final_answer":"..."}. '
    + _ANSWER_FORMAT +
    ' If you genuinely do not know, set final_answer to "UNSURE" rather than guessing — '
    "an honest UNSURE is more useful than a confident guess."
)

# A question is COMPUTATIONAL when the work is arithmetic/algebra rather than recall.
# Used by style="auto" to pick the right solver prompt per question.
_NUMERIC_OPT = re.compile(r"^\s*[-+]?[\d.,]+\s*(%|km|m|cm|mm|kg|g|s|min|hr|hours?|rs\.?|"
                          r"litres?|liters?|years?|days?|:\s*\d+)?\s*$", re.I)


def pick_style(q) -> str:
    """'derive' when the answer must be computed, else 'recall'.

    Heuristic, not a classifier: if most options are bare numbers/quantities the question
    is almost certainly arithmetic; otherwise it is prose recall."""
    texts = [str(o.get("text") or "") for o in (q.options or [])]
    if not texts:
        return "derive"          # integer/numeric types are computational by definition
    numeric = sum(1 for t in texts if _NUMERIC_OPT.match(t.strip()))
    return "derive" if numeric >= max(2, len(texts) - 1) else "recall"


def _system_for(q, style: str) -> str:
    if style == "auto":
        style = pick_style(q)
    return _SYS_RECALL if style == "recall" else _SYS


def solve(q, llm, temperature: float = 0.1, style: str = "derive"):
    """style: 'derive' (default, unchanged JEE behaviour) | 'recall' | 'auto' (per-question)."""
    opts = "\n".join(f"({o.get('label')}) {o.get('text')}" for o in q.options)
    user = f"TYPE: {q.qtype}\nQUESTION: {q.stem}\n" + (f"OPTIONS:\n{opts}" if opts else "")
    res = llm.chat_json(_system_for(q, style), user, temperature=temperature)
    if not res:
        return None
    return {"solution": repair_latex(res.get("solution", "")),
            "final_answer": str(res.get("final_answer", "")).strip()}


def canon(q, ans: str) -> str:
    """Canonical form of an answer, for voting/comparison."""
    if q.qtype in ("MCQ_single", "MCQ_multi"):
        return "".join(sorted(set(re.findall(r"[A-D]", (ans or "").upper()))))
    n = _num(ans)
    if n is None:
        return ""
    return str(round(n)) if q.qtype == "integer" else f"{n:.4g}"


def solve_consistent(q, llm, k: int = 5, style: str = "derive"):
    """Self-consistency: solve k times (sampled), majority-vote the answer. Returns the
    majority answer, its vote count, and a solution from a run that produced it.

    An explicit "UNSURE" (recall style) is counted as a NON-vote: it lowers the effective
    k, so a question the model mostly doesn't know cannot reach a majority and will fail
    an audit. That is the intended behaviour — silence should not be evidence."""
    from collections import Counter
    votes, sol_by_ans, unsure = [], {}, 0
    for _ in range(k):
        res = solve(q, llm, temperature=0.7, style=style)
        if not res or not res["final_answer"]:
            continue
        if res["final_answer"].strip().upper() == "UNSURE":
            unsure += 1
            continue
        cv = canon(q, res["final_answer"])
        if not cv:
            continue
        votes.append(cv)
        sol_by_ans.setdefault(cv, res["solution"])
    if not votes:
        return None
    maj, cnt = Counter(votes).most_common(1)[0]
    # `k` stays the EFFECTIVE vote count (existing callers compare against it). `k_requested`
    # and `unsure` are additive: an audit must judge against the requested k, otherwise a
    # single vote among four UNSUREs looks like a 1-of-1 unanimous majority.
    return {"majority": maj, "votes": cnt, "k": len(votes), "k_requested": k,
            "unsure": unsure, "solution": sol_by_ans.get(maj)}


_EXPLAIN_SYS = (
    "You are an expert JEE physics teacher. You are given a question and its OFFICIAL "
    "correct answer. Write a correct, rigorous step-by-step worked solution (LaTeX $...$) "
    'that arrives at that official answer. Return JSON {"solution":"..."}.'
)


def explain(q, llm):
    """Produce a solution that reaches the KNOWN official answer (used when the
    independent solve disagreed — content students see, flagged for review)."""
    opts = "\n".join(f"({o.get('label')}) {o.get('text')}" for o in q.options)
    user = f"QUESTION: {q.stem}\n{opts}\nOFFICIAL ANSWER: {q.correct_answer}"
    res = llm.chat_json(_EXPLAIN_SYS, user)
    return repair_latex(res.get("solution", "")) if res else None


def _num(x):
    m = re.search(r"-?\d+\.?\d*", str(x or ""))
    return float(m.group()) if m else None


def answers_match(q, derived: str) -> bool:
    if q.qtype in ("MCQ_single", "MCQ_multi"):
        a = set(re.findall(r"[A-D]", (derived or "").upper()))
        b = set(re.findall(r"[A-D]", (q.correct_answer or "").upper()))
        return bool(b) and a == b
    da, ob = _num(derived), _num(q.correct_answer)
    if da is None or ob is None:
        return False
    if q.qtype == "integer":
        return round(da) == round(ob)
    return abs(da - ob) <= max(0.01, abs(ob) * 0.02)   # 2% tolerance for numeric
