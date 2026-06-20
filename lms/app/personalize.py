"""Progressive learner profiling — gather context gradually (never a big form),
then weave it into examples and the tutor. See PERSONALIZATION.md for the design."""
from sqlalchemy.orm import Session

from .models import LearnerFact, now

# Curated, casual, ONE-AT-A-TIME prompts. Order = priority. Shown a few at a time on the
# dashboard, each optional and skippable. Answering one awards a few gems.
MICRO_QUESTIONS = [
    {"key": "name", "q": "What should we call you?", "ph": "your first name"},
    {"key": "work", "q": "What kind of work or study fills most of your day?",
     "ph": "e.g. I run a Shopify store / final-year CS student / I do sales"},
    {"key": "why", "q": "What made you join this cohort — what do you want your agent to do?",
     "ph": "e.g. automate my daily lead follow-ups"},
    {"key": "interest", "q": "One hobby or interest you love (we'll borrow it for examples):",
     "ph": "e.g. cricket, cooking, gaming, music"},
    {"key": "tools", "q": "Which apps do you live in every day?",
     "ph": "e.g. Gmail, Google Sheets, WhatsApp, Notion"},
    {"key": "experience", "q": "How comfortable are you with coding right now?",
     "ph": "none yet / a little / fairly comfortable"},
    {"key": "routine", "q": "When do you usually get your focused study time?",
     "ph": "e.g. early mornings, after 9pm, weekends"},
]
QKEY = {m["key"]: m for m in MICRO_QUESTIONS}


def get_facts(db: Session, student_id: int) -> dict:
    return {
        f.key: f.value
        for f in db.query(LearnerFact).filter_by(student_id=student_id).all()
    }


def capture_fact(db: Session, student_id: int, key: str, value: str, source: str = "prompt") -> bool:
    value = (value or "").strip()
    key = (key or "").strip()
    if not value or not key:
        return False
    # prompt-sourced facts must be a known micro-question; lesson/inferred facts (goal, stop…) are free-form
    if key not in QKEY and source not in ("lesson", "inferred"):
        return False
    f = db.query(LearnerFact).filter_by(student_id=student_id, key=key).first()
    if f:
        f.value, f.source, f.updated_at = value, source, now()
    else:
        db.add(LearnerFact(student_id=student_id, key=key, value=value, source=source))
    db.commit()
    return True


def next_questions(facts: dict, n: int = 1) -> list:
    """The next unanswered micro-questions, in priority order."""
    return [m for m in MICRO_QUESTIONS if m["key"] not in facts][:n]


def build_learner_context(facts: dict) -> str:
    """A compact natural-language brief injected into the tutor / example prompts.
    Returns '' when we know nothing yet."""
    if not facts:
        return ""
    bits = []
    if facts.get("name"):
        bits.append(f"The learner's name is {facts['name']}.")
    if facts.get("work"):
        bits.append(f"They work/study in: {facts['work']}.")
    if facts.get("why"):
        bits.append(f"They joined to: {facts['why']}.")
    if facts.get("interest"):
        bits.append(f"A hobby they love: {facts['interest']}.")
    if facts.get("tools"):
        bits.append(f"Apps they use daily: {facts['tools']}.")
    if facts.get("experience"):
        bits.append(f"Coding comfort: {facts['experience']}.")
    return (
        "PERSONALIZATION CONTEXT — use this to ground examples and analogies in THIS "
        "learner's world. Prefer examples from their work, tools, and interests over generic "
        "ones. Match difficulty to their coding comfort. Never recite these facts back at "
        "them; just let examples quietly reflect them.\n" + " ".join(bits)
    )


def greeting(facts: dict) -> str:
    name = facts.get("name")
    hi = f"Welcome back, {name}" if name else "Welcome back"
    if facts.get("work"):
        return f"{hi} — let's build agents for {facts['work'].rstrip('.')}."
    return f"{hi} 👋"
