"""English (SSC CGL Tier-1) taxonomy — the SHARED SSC / Railway / Banking English chapters.
GENERATION-first: qbank.englishgen draws each chapter deterministically from verified word-pairs +
a mechanical voice builder. Chapter names MUST match englishgen._CHAP_BUILDERS keys."""

ENGLISH_COMMON = {
    "Vocabulary (Synonyms & Antonyms)": {
        "keywords": ["synonym", "antonym", "similar in meaning", "opposite in meaning"],
        "concepts": {"Synonyms": ["synonym", "similar in meaning"],
                     "Antonyms": ["antonym", "opposite in meaning"]},
    },
    "One-Word Substitution": {
        "keywords": ["one word", "one-word", "substitution", "a person who", "one who"],
        "concepts": {"One-Word Substitution": ["one word", "substitution"]},
    },
    "Idioms & Phrases": {
        "keywords": ["idiom", "phrase", "means", "expression"],
        "concepts": {"Idioms & Phrases": ["idiom", "phrase"]},
    },
    "Spelling": {
        "keywords": ["spelt", "spelling", "correctly spelt", "incorrectly spelt", "misspelt"],
        "concepts": {"Spelling": ["spelt", "spelling"]},
    },
    "Grammar (Active/Passive Voice)": {
        "keywords": ["passive voice", "active voice", "voice", "change into"],
        "concepts": {"Voice (Active/Passive)": ["passive voice", "active voice"]},
    },
}
