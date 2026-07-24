"""Solution agent — writes a worked solution AND validates it against the official
answer. The model solves INDEPENDENTLY (not told the answer), then we compare its
derived answer to the banked answer:
  agree    -> store the solution (it explains the correct answer)
  disagree -> store it but flag 'solution_mismatch' (bad extraction / hard question / mis-key)

That mismatch flag is a free quality gate — it surfaces questions not safe to grade on."""
import re

from .models import repair_latex

_SYS = (
    "You are an expert JEE physics solver. Solve the question INDEPENDENTLY and rigorously "
    "from first principles. Return JSON "
    '{"solution":"step-by-step worked solution using LaTeX $...$","final_answer":"..."}. '
    "final_answer format: MCQ_single -> one letter (e.g. B); MCQ_multi -> letters (e.g. AC); "
    "integer -> the integer; numeric -> the decimal. Base final_answer ONLY on your own derivation."
)


def solve(q, llm, temperature: float = 0.1):
    opts = "\n".join(f"({o.get('label')}) {o.get('text')}" for o in q.options)
    user = f"TYPE: {q.qtype}\nQUESTION: {q.stem}\n" + (f"OPTIONS:\n{opts}" if opts else "")
    res = llm.chat_json(_SYS, user, temperature=temperature)
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


def solve_consistent(q, llm, k: int = 5):
    """Self-consistency: solve k times (sampled), majority-vote the answer. Returns the
    majority answer, its vote count, and a solution from a run that produced it."""
    from collections import Counter
    votes, sol_by_ans = [], {}
    for _ in range(k):
        res = solve(q, llm, temperature=0.7)
        if not res or not res["final_answer"]:
            continue
        cv = canon(q, res["final_answer"])
        if not cv:
            continue
        votes.append(cv)
        sol_by_ans.setdefault(cv, res["solution"])
    if not votes:
        return None
    maj, cnt = Counter(votes).most_common(1)[0]
    return {"majority": maj, "votes": cnt, "k": len(votes), "solution": sol_by_ans.get(maj)}


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
