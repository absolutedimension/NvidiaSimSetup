"""Acharya University agents — the Advisor (generates the course) + the Tutor.

Staged, async-friendly generation so a course "need not be instant":
  1. advisor_interview()  — ≤5 chip-guided intake questions, one at a time.
  2. advisor_outline()    — FAST: title/destination/why + unit stubs (title+summary+objectives).
  3. advisor_unit_detail()— per-unit: concepts (recall/answer) + milestone. Runs one unit at a time
     in a background job, so units flip building→active progressively.
  4. tutor_step() / grade_recall() — teach a unit + mastery (code owns the `solid` promotion).

Reuses the same Azure OpenAI (gpt-4o-mini) setup as app/tutor.py.
"""
import json
import urllib.error
import urllib.request

from .config import settings


def available() -> bool:
    return bool(settings.AOAI_ENDPOINT and settings.AOAI_KEY)


def _chat(messages: list, temperature: float = 0.5, max_tokens: int = 900,
          json_mode: bool = False) -> str | None:
    if not available():
        print("[university] AOAI not configured")
        return None
    url = (f"{settings.AOAI_ENDPOINT}/openai/deployments/{settings.AOAI_DEPLOYMENT}"
           f"/chat/completions?api-version={settings.AOAI_API_VERSION}")
    payload = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "api-key": settings.AOAI_KEY})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        print(f"[university] LLM call failed: {exc}")
        return None


def _json(text: str | None) -> dict | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    s, e = text.find("{"), text.rfind("}")
    if 0 <= s < e:
        try:
            return json.loads(text[s:e + 1])
        except (ValueError, TypeError):
            return None
    return None


# ---- ADVISOR --------------------------------------------------------------
INTERVIEW_SYSTEM = (
    "You are the ADVISOR — an elite academic advisor designing a PERSONAL course for ONE learner who "
    "wants to teach themselves a topic using AI. Run a SHORT intake interview to pin down: DESTINATION "
    "(what they want to be able to DO), BASELINE (what they already know), motivation, and pace/time.\n"
    "Rules: ask ONE question at a time, 1-2 warm sentences, plain language; build on their last answer; "
    "never repeat; ask at most 4 questions total, then stop.\n"
    "Return STRICT JSON only: {\"done\": bool, \"question\": string}. When done=true, question is a "
    "one-line encouraging summary of what you'll build."
)

OUTLINE_SYSTEM = (
    "You are the ADVISOR. From the learner's goal + interview, design the OUTLINE of their personal "
    "course — the skeleton only (units are detailed later). Sequence units foundation → application.\n"
    "Return STRICT JSON only:\n"
    "{\n"
    '  "title": "short course title",\n'
    '  "destination": "what they can DO after finishing (1-2 sentences)",\n'
    '  "baseline": "where they start (1 sentence)",\n'
    '  "why": "a motivating one-line reason this matters to them",\n'
    '  "cut_list": ["3-6 things to deliberately IGNORE for now"],\n'
    '  "units": [ {"title":"unit title","summary":"1-2 sentence overview","objectives":["3-5 concrete can-do items"]} ]\n'
    "}\n"
    "5 to 8 units. Works for ANY subject (finance, design, a language, a craft, a science, school topics)."
)

UNIT_SYSTEM = (
    "You are the ADVISOR detailing ONE unit of a learner's course. Given the course title and this unit "
    "(title/summary/objectives), produce its testable concepts and a proof-of-mastery milestone.\n"
    "Return STRICT JSON only:\n"
    "{\n"
    '  "concepts": [ {"key":"snake_case_id","name":"human name","recall":"a no-peeking recall question","answer":"the crisp correct answer"} ],\n'
    '  "milestone": {"prompt":"a small DOABLE deliverable that proves mastery (explain-back, a tiny build, a worked example, a short write-up)","rubric":["2-4 things a good answer must show"]}\n'
    "}\n"
    "3 to 6 specific, testable concepts (not vague headings). The milestone must NOT be 'take an exam'."
)


def advisor_interview(goal: str, history: list) -> dict:
    msgs = [{"role": "system", "content": INTERVIEW_SYSTEM},
            {"role": "user", "content": f"The learner wants to learn: {goal}"}] + history[-10:]
    d = _json(_chat(msgs, 0.5, 200, json_mode=True)) or {}
    return {"done": bool(d.get("done")),
            "question": str(d.get("question", "")).strip()
            or "What do you want to be able to DO once you've learned this?"}


def advisor_outline(goal: str, interview: list) -> dict | None:
    convo = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in interview)
    msgs = [{"role": "system", "content": OUTLINE_SYSTEM},
            {"role": "user",
             "content": f"GOAL: {goal}\n\nINTERVIEW:\n{convo or '(none — infer sensible defaults)'}"}]
    d = _json(_chat(msgs, 0.55, 1500, json_mode=True))
    if not d or not d.get("units"):
        return None
    return d


def advisor_unit_detail(course_title: str, unit: dict) -> dict | None:
    ctx = (f"COURSE: {course_title}\nUNIT: {unit.get('title','')}\n"
           f"SUMMARY: {unit.get('summary','')}\nOBJECTIVES:\n"
           + "\n".join(f"- {o}" for o in unit.get("objectives", [])))
    d = _json(_chat([{"role": "system", "content": UNIT_SYSTEM},
                     {"role": "user", "content": ctx}], 0.55, 1200, json_mode=True))
    if not d:
        return None
    concepts = []
    for i, c in enumerate(d.get("concepts") or []):
        concepts.append({"key": str(c.get("key") or f"c{i}"), "name": str(c.get("name", "")),
                         "recall": str(c.get("recall", "")), "answer": str(c.get("answer", "")),
                         "mastery": 0.0})
    ms = d.get("milestone") or {}
    return {"concepts": concepts,
            "milestone": {"prompt": str(ms.get("prompt", "")),
                          "rubric": [str(r) for r in (ms.get("rubric") or [])]}}


# ---- TUTOR ----------------------------------------------------------------
TUTOR_SYSTEM = (
    "You are Acharya, a warm, sharp 1:1 tutor in a self-taught university, teaching ONE unit of the "
    "learner's course. Make them TRULY understand and be able to DO the unit's objectives.\n"
    "- Lead with ONE small, specific question that opens the exact gap — don't lecture, don't dump the answer.\n"
    "- Make them retrieve/reason; give a bigger hint only if stuck after a couple of turns, but they take the final step.\n"
    "- 2-5 sentences per turn, plain, warm. No markdown headings. Stay inside THIS unit.\n"
    "- Catch confident-wrong answers. Ground examples in the learner's world. Maths in LaTeX $...$.\n"
    "- When they clearly nail a concept, say so plainly and move to the next objective."
)

RECALL_SYSTEM = (
    "You are a strict but fair grader. Given a recall QUESTION, reference ANSWER, and the learner's "
    "ATTEMPT, decide if they genuinely got it right (ideas, not wording). "
    "Return STRICT JSON only: {\"correct\": bool, \"feedback\": \"one short encouraging sentence\"}."
)


def _unit_context(course_title: str, unit: dict) -> str:
    lines = [f"COURSE: {course_title}", f"UNIT: {unit.get('title','')} — {unit.get('summary','')}",
             "OBJECTIVES:"] + [f"  - {o}" for o in unit.get("objectives", [])]
    if unit.get("concepts"):
        lines.append("KEY CONCEPTS (name — answer, for YOUR reference; reveal gradually):")
        lines += [f"  - {c.get('name','')}: {c.get('answer','')}" for c in unit["concepts"]]
    return "\n".join(lines)


def tutor_step(course_title: str, unit: dict, history: list) -> str | None:
    system = TUTOR_SYSTEM + "\n\n" + _unit_context(course_title, unit)
    return _chat([{"role": "system", "content": system}] + history[-12:], 0.45, 380)


def grade_recall(question: str, answer: str, attempt: str) -> dict:
    d = _json(_chat([{"role": "system", "content": RECALL_SYSTEM},
                     {"role": "user",
                      "content": f"QUESTION: {question}\nREFERENCE ANSWER: {answer}\nLEARNER ATTEMPT: {attempt}"}],
                    0.0, 120, json_mode=True)) or {}
    return {"correct": bool(d.get("correct")),
            "feedback": str(d.get("feedback", "")).strip() or "Keep going."}
