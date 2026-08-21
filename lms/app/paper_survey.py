"""The paper-setting questionnaire — one definition, used by the form, the storage and the alert.

WHY THIS FILE EXISTS AT ALL. Three rounds of feedback from One Step's owner have each been six
words long ("ye basic ka bhi basic hai", "GS me question ek type ke"), and each time we guessed what
he meant and rebuilt. Our own difficulty tag has disagreed with him twice. He is himself a teacher
who sets papers, so the fastest way to a paper he will use is to ask him to specify one — in the
terms a generator can actually be set to.

Every question maps to a knob that already exists:

    q1..q4  what "difficult" MEANS, asked separately for GS / Maths / Reasoning, because it is not
            one thing and our single 1-4 band has been flattening three different meanings.
            MULTI-SELECT: if he says a maths question is hard because of BOTH the step count and
            close options, that is two dials to turn, and a single-pick form would have hidden one
    q5      how many of 100 students should get a hard question right  ->  a p-value TARGET, the
            first number that would put his judgement and our difficulty tag in the same unit
    q6, q7  --difficulty-mix
    q8      question ORDER, which the builder does not do at all today
    q9      how different two papers in a series must be (set disjointness)
    q10     the per-topic cap (ours is 4)
    q11     distractor policy (ours: every wrong option is a NAMED mistake)
    q12-q14 what he checks first, which section decides the paper, hours it costs him today

EVERY question carries an "Other" with a free-text box. He may simply not think in our categories,
and a fixed option list would then record a wrong answer rather than no answer — which is worse,
because we would act on it.
"""

QUESTIONS = [
    ("q1", "When you call a question DIFFICULT, which of these do you mean?", [
        "The student simply does not know the fact",
        "The student knows it but must think through steps",
        "The options are close, so a careless student gets it wrong",
        "It takes too long to finish in the time given"]),
    ("q2", "In GENERAL STUDIES, what makes a question hard?", [
        "A less-known / rarer fact",
        "Several statements to judge in one question (3–4)",
        "All four options look correct",
        "Two different topics combined in one question"]),
    ("q3", "In MATHS, what makes a question hard?", [
        "More steps in the solution",
        "Awkward numbers — fractions, decimals, large values",
        "Options very close to each other",
        "Two chapters combined in one question"]),
    ("q4", "In REASONING, what makes a question hard?", [
        "More conditions to hold in the head at once",
        "A longer chain — more links to follow",
        "Asked in reverse (given the answer, find the start)",
        "A question type the student has not seen before"]),
    ("q5", "Out of 100 students, how many SHOULD get a hard question right?", [
        "Fewer than 20", "20–40", "40–60", "More than 60"]),
    ("q6", "In a 150-question paper, how many should be genuinely hard?", [
        "About 20", "About 40", "About 70", "More than 100"]),
    ("q7", "What average score should a well-prepared student get on your paper?", [
        "Below 40%", "40–55%", "55–70%", "Above 70%"]),
    ("q8", "Where should the hard questions sit?", [
        "Spread evenly through the paper", "Kept at the end of each section",
        "Grouped in one hard section", "Easy first, then steadily harder"]),
    ("q9", "If you make 4 papers for 4 batches, they should be —", [
        "Completely different questions", "Same pattern, only numbers/names changed",
        "About half common, half new", "The same paper is fine"]),
    ("q10", "At most how many questions from ONE topic in a 50-question section?", [
        "2", "3–4", "5–6", "No limit"]),
    ("q11", "How do you write the WRONG options?", [
        "The mistakes students actually make", "Numbers close to the correct answer",
        "Taken from the book", "Anything that looks different"]),
    ("q12", "What is the FIRST thing you check in a finished paper?", [
        "That no answer in the key is wrong", "That nothing is outside the syllabus",
        "That the level is right", "That it can be finished in the time"]),
    ("q13", "Which section decides whether the whole paper is good?", [
        "General Studies", "Maths & Science", "Reasoning", "All equally"]),
    ("q14", "How long does it take you to make one full paper today?", [
        "Under an hour", "2–3 hours", "Half a day", "More than a day"]),
]

_BY_ID = {q: (text, opts) for q, text, opts in QUESTIONS}


def parse(form) -> dict:
    """Starlette form -> {q_id: {choices: [...], labels: [...], text: str}}.

    Questions are MULTI-SELECT. A paper-setter rarely means one thing by "hard" — a question can be
    hard because it has more steps AND because the options sit close together, and forcing a single
    pick would record half of what he thinks. Unanswered questions are simply absent.

    "Other" is a real answer, not a fallback: its typed text is stored and shown as given, and it
    can be ticked ALONGSIDE the listed options rather than instead of them.
    """
    out = {}
    for qid, _text, opts in QUESTIONS:
        picked = [c.strip() for c in form.getlist(qid) if str(c).strip()]
        typed = (form.get(qid + "_other") or "").strip()[:400]
        if typed and "other" not in picked:
            picked.append("other")          # typing IS the answer; never lose it to an unticked box
        if not picked:
            continue
        labels = []
        for c in picked:
            if c == "other":
                labels.append(typed or "(other — not specified)")
            elif c in "abcd" and "abcd".index(c) < len(opts):
                labels.append(opts["abcd".index(c)])
            else:
                labels.append(c)
        out[qid] = {"choices": picked, "labels": labels, "text": typed}
    return out


def summarise(answers: dict, limit: int = 900) -> str:
    """One line per answered question, for the WhatsApp alert and the container log.

    This is the belt to the database's braces. If the DB write ever fails, or the row is lost, the
    answers still exist in two other places — the founder's WhatsApp and the container log. The
    instruction was that a submission must not be lost, and one store is not that.
    """
    bits = []
    for qid, _text, _opts in QUESTIONS:
        a = answers.get(qid)
        if not a:
            continue
        parts = []
        for c, lab in zip(a["choices"], a["labels"]):
            parts.append(("OTHER: " + lab) if c == "other" else lab)
        bits.append(f"{qid}=" + " + ".join(parts))
    line = " | ".join(bits)
    return line[:limit]
