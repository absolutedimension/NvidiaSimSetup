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


def available() -> bool:
    return bool(settings.AOAI_ENDPOINT and settings.AOAI_KEY)


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
