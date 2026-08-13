"""Reasoning (General Intelligence) taxonomy — the SHARED SSC / Railway / Banking / BPSC
reasoning pattern.

Like banking_quant, govt-job reasoning has NO usable pre-tagged bank on HF, and its question
types are TEMPLATABLE + COMPUTABLE in Python — so this subject is GENERATION-first:
`qbank.reasoninggen` draws each chapter deterministically (compute-the-answer). The taxonomy
below just names the chapters so `/chapters` can list them and batch-fill can walk the cells.
Chapter names MUST match `reasoninggen._CHAP_BUILDERS` keys. One taxonomy serves every
govt-job exam's reasoning section (SSC CGL/CHSL, RRB, IBPS/SBI, BPSC/Daroga) — tagged by
`exam` at generation time."""

REASONING_COMMON = {
    "Coding-Decoding": {
        "keywords": ["code language", "written as", "coded as", "decode", "cipher",
                     "in a certain code"],
        "concepts": {
            "Letter-Shift Coding": ["written as", "code language", "shift"],
            "Number Coding": ["coded as", "position in the alphabet"],
        },
    },
    "Series": {
        "keywords": ["series", "next term", "letter series", "alphanumeric",
                     "what comes next", "missing term"],
        "concepts": {
            "Letter Series": ["letter series", "next letter"],
            "Alphanumeric Series": ["alphanumeric", "letter and number"],
        },
    },
    "Analogy": {
        "keywords": ["analogy", "is related to", "same way", "::", "as"],
        "concepts": {
            "Number Analogy": ["number analogy", ":: number"],
            "Letter Analogy": ["letter analogy", ":: letter"],
        },
    },
    "Classification (Odd One Out)": {
        "keywords": ["odd one out", "does not belong", "different from", "alike",
                     "odd man out", "which one is different"],
        "concepts": {
            "Odd One Out (Numbers)": ["odd one out", "perfect square", "prime"],
        },
    },
    "Ranking & Ordering": {
        "keywords": ["from the left", "from the right", "rank", "position in a row",
                     "row of", "tallest", "order"],
        "concepts": {
            "Ranking": ["from the left", "from the right", "position"],
        },
    },
    "Direction Sense": {
        "keywords": ["north", "south", "east", "west", "turns right", "turns left",
                     "how far", "which direction", "facing"],
        "concepts": {
            "Direction — Distance": ["how far", "distance from the starting point"],
            "Direction — Facing": ["facing", "which direction is he facing"],
        },
    },
    "Blood Relations": {
        "keywords": ["father of", "mother of", "brother of", "sister of", "son of",
                     "daughter of", "how is", "related to", "pointing to"],
        "concepts": {
            "Blood Relations": ["related to", "father of", "mother of"],
        },
    },
}
