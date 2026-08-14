"""Validator agent — the quality gate. A question is verified only if it passes
BOTH the deterministic rule checks and (when the LLM is available) the semantic
check. This is the text analogue of the drone VLM-critic pattern (CLAUDE.md 17.9):
never trust the source — prove each question is well-formed and answerable."""
import re

_LLM_SYS = (
    "You are a strict exam-question reviewer for Indian competitive exams (JEE/NEET/boards). "
    "Given ONE question (stem, options, stated correct answer), judge whether it is a clean, "
    "self-contained, answerable question with exactly the right number of correct options. "
    "Do NOT solve it fully; judge well-formedness and whether the stated answer is plausible. "
    'Return JSON {"well_formed":bool,"answer_plausible":bool,"issues":[string]}.'
)


def rule_check(q) -> list[str]:
    issues = []
    if len(q.stem) < 15:
        issues.append("stem_too_short")
    if q.qtype in ("MCQ_single", "MCQ_multi"):
        if len(q.options) < 2:
            issues.append("insufficient_options")
        labels = {o.get("label") for o in q.options}
        if any(not o.get("text") for o in q.options):
            issues.append("empty_option")
        ans = set(re.findall(r"[A-E]", (q.correct_answer or "").upper()))  # A-E: BPSC 5-option papers
        if not ans:
            issues.append("no_answer_key")
        elif not ans.issubset(labels):
            issues.append("answer_not_in_options")
        if q.qtype == "MCQ_single" and len(ans) > 1:
            issues.append("multiple_answers_for_single")
    else:  # integer / numeric
        if not (q.correct_answer or "").strip():
            issues.append("no_answer_key")
    return issues


def llm_check(q, llm) -> list[str]:
    if not llm.ok:
        return []
    payload = (f"TYPE: {q.qtype}\nSTEM: {q.stem}\n"
               f"OPTIONS: {q.options}\nSTATED_ANSWER: {q.correct_answer}")
    res = llm.chat_json(_LLM_SYS, payload)
    if not res:
        return []
    issues = list(res.get("issues", []))
    if res.get("well_formed") is False:
        issues.append("llm_not_well_formed")
    if res.get("answer_plausible") is False:
        issues.append("llm_answer_implausible")
    return issues


def validate(questions, llm=None):
    for q in questions:
        if q.duplicate_of:            # skip dupes; they aren't banked as unique
            continue
        issues = rule_check(q)
        if not issues and llm is not None:   # only spend LLM on rule-clean questions
            issues += llm_check(q, llm)
        q.validation_issues = issues
        q.verified = len(issues) == 0
    return questions
