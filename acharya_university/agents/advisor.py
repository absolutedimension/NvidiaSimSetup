"""ADVISOR (the 'A' in ALTER) — the agent that GENERATES the curriculum.

Two moves, straight from the "university in a box" idea:
  1. interview()  — ask up to 5 sharp questions, ONE at a time, to nail
     destination / baseline / sequencing / cut-list / milestones.
  2. build()      — turn the goal + answers into a full, sequenced curriculum object
     (units, objectives, concepts, milestones). This is the AI-generated 'subject'.
"""
import json

from llm import chat, extract_json
from store import new_id, _now

INTERVIEW_SYSTEM = (
    "You are the ADVISOR — an elite academic advisor building a PERSONAL curriculum for ONE learner "
    "who wants to teach themselves a topic from scratch using AI. You run a short intake interview.\n"
    "Your goal across the whole interview is to pin down FIVE things: (1) DESTINATION — what they want "
    "to be able to DO when done; (2) BASELINE — what they already know; (3) reason/motivation; "
    "(4) time budget / pace; (5) any specific sub-area to focus or ignore.\n"
    "Rules:\n"
    "- Ask ONE question at a time. Keep it to 1-2 warm sentences. Plain language.\n"
    "- Build on what they just said; never repeat a question.\n"
    "- Ask at most 5 questions total. When you have enough to design a great curriculum, STOP asking.\n"
    "Return STRICT JSON only: {\"done\": bool, \"question\": string}. "
    "When done=true, question is a one-line encouraging summary of what you'll build."
)

BUILD_SYSTEM = (
    "You are the ADVISOR. Using the learner's goal and interview answers, DESIGN a complete personal "
    "curriculum — their custom degree in this subject. Sequence it so each unit builds on the last.\n"
    "Return STRICT JSON only, matching EXACTLY this shape:\n"
    "{\n"
    '  "title": "short course title",\n'
    '  "destination": "what the learner can DO after finishing (1-2 sentences)",\n'
    '  "baseline": "where they are starting from (1 sentence)",\n'
    '  "why": "a motivating one-line reason this matters to them",\n'
    '  "cut_list": ["3-6 things to deliberately IGNORE for now"],\n'
    '  "units": [\n'
    "    {\n"
    '      "title": "unit title",\n'
    '      "summary": "1-2 sentence overview of the unit",\n'
    '      "objectives": ["3-5 concrete things they will be able to do"],\n'
    '      "concepts": [ {"key":"snake_case_id","name":"human name","recall":"a no-peeking recall question","answer":"the crisp answer"} ],\n'
    '      "milestone": {"prompt":"a small deliverable that PROVES mastery of this unit","rubric":["2-4 things a good answer must show"]}\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "Design guidance:\n"
    "- 5 to 8 units. Each unit 3-6 concepts. Order units from foundation to application.\n"
    "- Concepts must be specific and testable, not vague headings.\n"
    "- Milestones must be DOABLE by the learner (explain-back, a small build, a worked example, a short write-up) "
    "— never 'take an exam'.\n"
    "- Match depth to their baseline. Honour their focus/ignore preferences.\n"
    "- Work for ANY subject: finance, design theory, a language, a school subject, a craft, a science."
)


def interview(goal: str, history: list) -> dict:
    """history = [{role,content}] of the intake so far. Returns {done, question}."""
    msgs = [{"role": "system", "content": INTERVIEW_SYSTEM},
            {"role": "user", "content": f"The learner wants to learn: {goal}"}] + history[-10:]
    raw = chat(msgs, temperature=0.5, max_tokens=200, json_mode=True)
    data = extract_json(raw) or {}
    return {"done": bool(data.get("done")),
            "question": str(data.get("question", "")).strip()
            or "What do you want to be able to DO once you've learned this?"}


def build(user_id: str, goal: str, interview_history: list) -> dict | None:
    """Generate the full curriculum object. Returns a saved-shape dict (not yet persisted)."""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in interview_history)
    msgs = [{"role": "system", "content": BUILD_SYSTEM},
            {"role": "user",
             "content": f"GOAL: {goal}\n\nINTERVIEW:\n{convo or '(no interview — infer sensible defaults)'}"}]
    raw = chat(msgs, temperature=0.55, max_tokens=2600, json_mode=True)
    data = extract_json(raw)
    if not data or not data.get("units"):
        return None
    curriculum_id = new_id("cur")
    units = []
    for i, u in enumerate(data.get("units", [])):
        concepts = []
        for c in (u.get("concepts") or []):
            concepts.append({
                "key": str(c.get("key") or f"c{i}_{len(concepts)}"),
                "name": str(c.get("name", "")),
                "recall": str(c.get("recall", "")),
                "answer": str(c.get("answer", "")),
                "mastery": 0.0,
            })
        units.append({
            "unit_id": f"u{i+1}",
            "title": str(u.get("title", f"Unit {i+1}")),
            "summary": str(u.get("summary", "")),
            "objectives": [str(o) for o in (u.get("objectives") or [])],
            "concepts": concepts,
            "sources": [],  # Librarian fills in Phase 3
            "milestone": {
                "prompt": str((u.get("milestone") or {}).get("prompt", "")),
                "rubric": [str(r) for r in ((u.get("milestone") or {}).get("rubric") or [])],
            },
            "mastery": 0.0,
            "status": "active" if i == 0 else "locked",
        })
    return {
        "curriculum_id": curriculum_id,
        "user_id": user_id,
        "title": str(data.get("title", goal))[:120],
        "goal": goal,
        "destination": str(data.get("destination", "")),
        "baseline": str(data.get("baseline", "")),
        "why": str(data.get("why", "")),
        "cut_list": [str(x) for x in (data.get("cut_list") or [])],
        "status": "active",
        "created_at": _now(),
        "units": units,
    }
