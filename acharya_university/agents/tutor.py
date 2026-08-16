"""TUTOR (the 'T' in ALTER) — 1:1 Socratic teacher, grounded in ONE unit.

Carries the old Acharya's teaching soul (open a gap not an answer, retrieve don't
re-explain, catch the confident-wrong) but is now scoped to a unit of an AI-generated
curriculum instead of a single exam question.

Also exposes grade_recall() — the deterministic-ish mastery check. Per the standing
rule, the *model* proposes; a concept only becomes `solid` (1.0) when a recall answer
passes here (code owns the promotion).
"""
from llm import chat, extract_json

TUTOR_SYSTEM = (
    "You are Acharya, a warm, sharp 1:1 tutor inside a self-taught university. You are teaching ONE "
    "unit of the learner's personal curriculum (given below). Your job is to make them TRULY understand "
    "and be able to DO the unit's objectives.\n"
    "Method:\n"
    "- Lead with ONE small, specific question that opens the exact gap in their understanding — don't "
    "lecture, don't dump the answer.\n"
    "- Make them retrieve and reason; give a bigger hint only if they're stuck after a couple of turns, "
    "but still make them take the final step.\n"
    "- Keep each turn to 2-5 sentences, plain language, warm. No markdown headings.\n"
    "- Stay inside THIS unit's objectives and concepts. If they drift, gently bring them back.\n"
    "- Catch confident-wrong answers — probe, don't rubber-stamp.\n"
    "- Ground examples in the learner's own world when it helps.\n"
    "- Write any maths in LaTeX between $...$.\n"
    "- When they clearly nail a concept, tell them plainly and move to the next objective."
)

RECALL_SYSTEM = (
    "You are a strict but fair grader. Given a recall QUESTION, the reference ANSWER, and the learner's "
    "ATTEMPT, decide if they genuinely got it right (ideas matter, not exact wording). "
    "Return STRICT JSON only: {\"correct\": bool, \"feedback\": \"one short encouraging sentence\"}."
)


def _unit_context(curriculum: dict, unit: dict) -> str:
    lines = [f"COURSE: {curriculum.get('title','')}",
             f"UNIT: {unit.get('title','')} — {unit.get('summary','')}",
             "OBJECTIVES:"]
    lines += [f"  - {o}" for o in unit.get("objectives", [])]
    if unit.get("concepts"):
        lines.append("KEY CONCEPTS (name — answer, for YOUR reference; reveal gradually):")
        for c in unit["concepts"]:
            lines.append(f"  - {c.get('name','')}: {c.get('answer','')}")
    if unit.get("sources"):
        lines.append("SOURCES ON THE SHELF (cite when relevant):")
        for s in unit["sources"]:
            lines.append(f"  - {s.get('title','')} ({s.get('url','')})")
    return "\n".join(lines)


def step(curriculum: dict, unit: dict, history: list) -> str | None:
    """One tutoring turn. history=[{role,content}] (client resends recent turns)."""
    system = TUTOR_SYSTEM + "\n\n" + _unit_context(curriculum, unit)
    messages = [{"role": "system", "content": system}] + history[-12:]
    return chat(messages, temperature=0.45, max_tokens=380)


def grade_recall(question: str, answer: str, attempt: str) -> dict:
    """Grade a recall attempt. Returns {correct: bool, feedback: str}."""
    msgs = [{"role": "system", "content": RECALL_SYSTEM},
            {"role": "user",
             "content": f"QUESTION: {question}\nREFERENCE ANSWER: {answer}\nLEARNER ATTEMPT: {attempt}"}]
    data = extract_json(chat(msgs, temperature=0.0, max_tokens=120, json_mode=True)) or {}
    return {"correct": bool(data.get("correct")),
            "feedback": str(data.get("feedback", "")).strip() or "Keep going."}
