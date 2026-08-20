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
    "Radha": "राधा", "Neha": "नेहा",
}

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
    """Hindi ordinal as printed in exam papers: 1st -> पहले, otherwise 10वें."""
    return {1: "पहले", 2: "दूसरे", 3: "तीसरे"}.get(n, f"{n}वें")


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
