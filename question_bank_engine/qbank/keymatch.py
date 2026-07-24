"""Keymatch agent — attach official answer keys to extracted questions.

Open-dataset rows already carry the answer (handled in the extractor). This agent
is for the PDF path: the answer key is almost always a SEPARATE PDF, so we parse
'{number -> answer}' from it and join by question number. Never let the model
'guess' the answer — anchor to the official key."""
import re

_KEY_LINE = re.compile(r"\b(\d{1,3})\b[\).:\-\s]+([A-D]{1,4}|\d+(?:\.\d+)?)")


def parse_key_text(text: str) -> dict:
    """Very tolerant parser for 'Q.No  Answer' style key sheets."""
    keymap = {}
    for m in _KEY_LINE.finditer(text):
        num, ans = int(m.group(1)), m.group(2).strip().upper()
        keymap.setdefault(num, ans)
    return keymap


def attach(questions, keymap: dict):
    """Join by the trailing number in each question id (…_<num>)."""
    for q in questions:
        m = re.search(r"_(\d+)$", q.id)
        if not m:
            continue
        ans = keymap.get(int(m.group(1)))
        if ans:
            q.correct_answer = ans
    return questions
