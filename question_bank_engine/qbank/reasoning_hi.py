"""Hindi layer for the compute-the-answer reasoning engine (qbank.reasoninggen).

Bihar govt papers (BSSC / BPSC / TRE) print every question in BOTH Hindi and English, so a
Hindi-medium student reads the same paper an English-medium student does. This module supplies
the Hindi half.

WHY THIS IS NOT TRANSLATION — and why that matters:
    reasoninggen builds each question from a template and COMPUTES its answer in Python. The
    Hindi version is the SAME computation rendered with a Hindi template, so the answer is
    derived, never translated. A machine translation can silently mangle a number, an option or
    a negation; a template cannot. For a product whose whole claim is "the answer key is right",
    this distinction is the entire ballgame.

Option handling: most reasoning options are numbers, letters or codes and are identical in both
languages, so a builder only supplies `hi_opts` (an English-text -> Hindi-text map) for the two
builders whose options are WORDS — directions and kinship terms. `_make_question` maps options
through it AFTER shuffling, so Hindi options always sit in the same order as the English ones.
"""

# ---- vocabularies -----------------------------------------------------------

NAME = {
    "Ram": "राम", "Amit": "अमित", "Vikas": "विकास", "Rohan": "रोहन",
    "Arun": "अरुण", "Sunil": "सुनील",
    "Sita": "सीता", "Priya": "प्रिया", "Anjali": "अंजलि", "Meena": "मीना",
    "Radha": "राधा", "Neha": "नेहा", "Rahul": "राहुल", "Sneha": "स्नेहा",
}


def missing_names(used):
    """Names a builder can pick that have no Hindi. name() falls back to the ENGLISH spelling,
    so a gap here prints Latin letters inside a Devanagari sentence — 'तथा Rahul बाईं ओर से' —
    which is the same class of defect as the scanned 'बAREफुट' Rohan caught by eye. Silent, and
    only visible if you read the Hindi. Builders should assert on this rather than trust it."""
    return [n for n in used if n not in NAME]

DIR = {"North": "उत्तर", "South": "दक्षिण", "East": "पूर्व", "West": "पश्चिम"}
TURN = {"left": "बाएँ", "right": "दाएँ"}

# Kinship. Hindi has no single neutral word for "uncle"/"aunt" — the paternal/maternal terms
# differ (चाचा/मामा, बुआ/मौसी). Bihar papers commonly print the generic "चाचा"/"मौसी" style, so
# we use the widely-accepted neutral renderings and keep them CONSISTENT between stem, options
# and solution. Consistency matters more than dialect precision: a student must be able to match
# the word in the question to the word in the options.
REL = {
    "father": "पिता", "mother": "माता", "son": "पुत्र", "daughter": "पुत्री",
    "brother": "भाई", "sister": "बहन",
    "grandfather": "दादा", "grandmother": "दादी",
    "grandson": "पोता", "granddaughter": "पोती",
    "uncle": "चाचा", "aunt": "बुआ", "nephew": "भतीजा", "niece": "भतीजी",
    "cousin": "चचेरा भाई/बहन",
}


def name(x):
    return NAME.get(x, x)


def rel(x):
    return REL.get(str(x).strip().lower(), x)


def ordinal(n: int) -> str:
    """Hindi ordinal as printed in exam papers: always the DIGIT, e.g. 3वें, 10वें.

    The word forms (पहले, दूसरे, तीसरे) read more naturally, but they cost the paper real
    questions: paper_common.numbers_agree() compares the digits in the two languages to catch a
    Hindi template that dropped part of the question, and a word-form ordinal looks to it exactly
    like a missing number. Every ranking question whose position happened to be 1, 2 or 3 was
    being silently discarded. Bihar's own Hindi papers print "3वें स्थान पर", so the digit form
    is both authentic and checkable.
    """
    return f"{n}वें"


def rel_opts(english_options) -> dict:
    """English kinship option -> Hindi, for `hi_opts`."""
    return {str(o): rel(str(o)) for o in english_options}


def dir_opts(english_options) -> dict:
    return {str(o): DIR.get(str(o), str(o)) for o in english_options}


# Hindi possessive agrees with the GENDER of the relation word, not the person:
#   "विकास के पिता"  (masc.)   but   "विकास की माता"  (fem.)
# Getting this wrong is the first thing a Hindi reader notices, so it is table-driven, not guessed.
_FEM_RELS = {"माता", "बहन", "दादी", "पोती", "बुआ", "भतीजी", "पुत्री"}


def possessive(person_hi: str, relation_en: str) -> str:
    """'विकास की माता' / 'विकास के पिता' — person + correctly-agreeing particle + relation."""
    r = rel(relation_en)
    return f"{person_hi} {'की' if r in _FEM_RELS else 'के'} {r}"


# Hindi conjugates the PARTICIPLE for the subject's gender — राधा बैठी है, not राधा बैठा है. A
# seating question names people in every clue, so a masculine default puts the error on the page
# five or six times in one question. Exactly the same failure as possessive()'s का/की above, and
# table-driven for the same reason: it is not guessable from the spelling.
_FEMININE = {"Sita", "Priya", "Anjali", "Meena", "Radha", "Neha", "Sneha"}


def is_female(name_en) -> bool:
    return str(name_en).strip() in _FEMININE


def sits(name_en) -> str:
    """'बैठी है' / 'बैठा है' — agreeing with the PERSON named, not with the sentence."""
    return "बैठी है" if is_female(name_en) else "बैठा है"
