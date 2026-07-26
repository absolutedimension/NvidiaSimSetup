"""The TrigunAI guide — a Socratic LLM tutor backed by Azure OpenAI (gpt-4o-mini).
Never hands over the answer; grounds examples in the learner's own context."""
import json
import urllib.request
import urllib.error

from .config import settings

SYSTEM = (
    "You are the TrigunAI guide, a warm Socratic tutor inside a live cohort that teaches people "
    "to BUILD agentic AI systems. Your job is to get the learner UNSTUCK by asking the right "
    "question — never by handing over the answer.\n"
    "Rules:\n"
    "- Never state the correct option/answer outright. Lead with ONE small, specific question.\n"
    "- Decompose: break the problem into the smallest sub-step they're missing.\n"
    "- Be brief — 1 to 3 sentences. Warm, encouraging, plain English. No markdown headings.\n"
    "- Ground examples in the learner's own world (their work, tools, hobbies) when it helps.\n"
    "- If they're really stuck after a couple of exchanges, give a bigger hint — but still make "
    "them take the final step themselves.\n"
    "- Match difficulty to their stated coding comfort. Never lecture; converse."
)


EXAM_TUTOR = (
    "You are Acharya, a warm, patient exam tutor for Indian students (JEE, NEET, boards, banking). "
    "You are helping a student with ONE specific exam question they got wrong (shown below). Your "
    "ENTIRE job is to make them understand THIS question deeply. Stay glued to it — do NOT drift "
    "into a general lecture on the topic.\n"
    "\nEverything you say must be in service of understanding THIS question. Teach in this order, "
    "ONE short step per message (2-5 sentences, simple language):\n"
    "1. FIRST make sure they understand what THIS question is actually asking and what it is really "
    "testing. Point at the given data in the question.\n"
    "2. Tell them clearly WHICH concept(s) they need to solve THIS question — it may be one, or a few "
    "working together — and name them. This is key: show them the concepts this question demands.\n"
    "3. Walk through how THIS question is solved, step by step. Explain a basic ONLY as far as THIS "
    "question needs it, and immediately tie it back to the numbers/setup in the question. NEVER give "
    "a generic textbook definition disconnected from the question.\n"
    "4. Once the solution is clear, INVITE them to see it another way: e.g. 'There's another way to "
    "solve this — want to see it?' and show an alternative method, shortcut, or a different concept "
    "angle for the SAME question, so they get deeper insight.\n"
    "5. Check understanding with a small question about THIS question (or a tiny variation of it).\n"
    "\nHard rules:\n"
    "- NEVER teach the whole topic from scratch or ask generic 'what is a unit?'-style questions that "
    "wander from THIS problem. If a basic is genuinely needed, teach it in one line and connect it "
    "straight back to the question.\n"
    "- Be Socratic — ask ONE small question and let them answer — but if they are stuck or ask "
    "directly, EXPLAIN clearly. Never withhold like a riddle.\n"
    "- Plain, simple language. If the student writes in Hindi or asks for Hindi, switch fully to Hindi.\n"
    "- Write ALL maths in LaTeX between $...$ so it renders (e.g. $v = u + at$).\n"
    "- If a diagram is shown with the question, refer to it.\n"
    "- Warm and encouraging. Never make them feel slow."
)


def available() -> bool:
    return bool(settings.AOAI_ENDPOINT and settings.AOAI_KEY)


def exam_chat(history: list, concept: str, subject_label: str,
              anchor: dict | None, mastery_pct: int | None) -> str | None:
    """Weak-topic exam tutor. history=[{role,content}]; anchor = the question we teach around
    ({stem, options:[...], correct_text, solution}). Returns the tutor's reply, or None on failure."""
    if not available():
        return None
    ctx = [f"CONCEPT THE STUDENT IS WEAK ON: {concept}", f"SUBJECT / EXAM: {subject_label}"]
    if mastery_pct is not None:
        ctx.append(f"Their current mastery on this concept: {mastery_pct}% (so assume little/shaky grasp).")
    if anchor and anchor.get("stem"):
        ctx.append("\nTHE EXAM QUESTION TO TEACH AROUND (of the exact type they got wrong):")
        ctx.append("Q: " + str(anchor.get("stem", ""))[:1500])
        opts = anchor.get("options") or []
        if opts:
            ctx.append("Options: " + " | ".join(str(o)[:120] for o in opts[:6]))
        if anchor.get("correct_text"):
            ctx.append("Correct answer: " + str(anchor["correct_text"])[:200])
        if anchor.get("solution"):
            ctx.append("Worked solution (for YOUR reference — reveal it gradually, don't dump it): "
                       + str(anchor["solution"])[:2500])
    system = EXAM_TUTOR + "\n\n" + "\n".join(ctx)
    messages = [{"role": "system", "content": system}] + history[-12:]
    url = (f"{settings.AOAI_ENDPOINT}/openai/deployments/{settings.AOAI_DEPLOYMENT}"
           f"/chat/completions?api-version={settings.AOAI_API_VERSION}")
    payload = json.dumps({"messages": messages, "temperature": 0.45, "max_tokens": 360}).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "api-key": settings.AOAI_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        print(f"[tutor] exam LLM call failed: {exc}")
        return None


def chat(history: list, learner_context: str = "", problem: str = "") -> str | None:
    """history = [{role, content}]. Returns the guide's reply, or None on failure."""
    if not available():
        return None
    system = SYSTEM
    if learner_context:
        system += "\n\n" + learner_context
    if problem:
        system += "\n\nCURRENT PROBLEM THE LEARNER IS ON:\n" + problem
    messages = [{"role": "system", "content": system}] + history[-12:]
    url = (f"{settings.AOAI_ENDPOINT}/openai/deployments/{settings.AOAI_DEPLOYMENT}"
           f"/chat/completions?api-version={settings.AOAI_API_VERSION}")
    payload = json.dumps({"messages": messages, "temperature": 0.5, "max_tokens": 220}).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "api-key": settings.AOAI_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError) as exc:
        print(f"[tutor] LLM call failed: {exc}")
        return None
