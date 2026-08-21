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


def _complete_mcq(q) -> bool:
    """An MCQ carrying >=2 non-empty options and a key that points into them is a
    COMPLETE question no matter how terse the stem is."""
    if q.qtype not in ("MCQ_single", "MCQ_multi") or len(q.options) < 2:
        return False
    if any(not str(o.get("text") or "").strip() for o in q.options):
        return False
    labels = {o.get("label") for o in q.options}
    ans = set(re.findall(r"[A-E]", (q.correct_answer or "").upper()))
    return bool(ans) and ans.issubset(labels)


def rule_check(q) -> list[str]:
    issues = []
    # `stem_too_short` exists to catch TRUNCATED extractions, not terse questions. A flat
    # 15-char floor is right for JEE/NEET problem statements but wrong for recall banks:
    # it threw away 16 perfectly good maritime questions ("IMO stands for", "Scupper is",
    # "A \"BOLT\" has") that carried four real options and a valid key. So shortness is only
    # a defect when the question is ALSO incomplete — or when it is so short (<8 chars) that
    # it cannot be a question at all.
    if len(q.stem) < 15 and (len(q.stem) < 8 or not _complete_mcq(q)):
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
