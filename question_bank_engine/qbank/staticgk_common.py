"""Static GK (General Knowledge) taxonomy — the SHARED SSC / Railway / Banking / BPSC "Static
Portion — GK" chapters. GENERATION-first: qbank.staticgkgen draws each chapter deterministically
from verified fact tables (correct-by-construction). Chapter names MUST match
staticgkgen._CHAP_BUILDERS keys."""

STATIC_GK_COMMON = {
    "Indian States & Capitals": {
        "keywords": ["capital", "state", "capital of"],
        "concepts": {"State Capitals": ["capital of", "state capital"]},
    },
    "World Capitals & Currencies": {
        "keywords": ["capital of", "currency", "country"],
        "concepts": {"World Capitals": ["capital of"], "World Currencies": ["currency of"]},
    },
    "Rivers & National Parks": {
        "keywords": ["river", "origin", "national park", "tiger reserve", "wildlife"],
        "concepts": {"Rivers of India": ["river", "originate"], "National Parks": ["national park"]},
    },
    "Art, Culture & Books": {
        "keywords": ["dance", "book", "author", "award", "folk", "classical"],
        "concepts": {"Dances of India": ["dance"], "Books & Authors": ["author", "book"],
                     "Awards & Honours": ["award"]},
    },
    "Indian Polity (Constitution)": {
        "keywords": ["article", "constitution", "fundamental", "amendment"],
        "concepts": {"Constitution Articles": ["article", "constitution"]},
    },
    "Static Science GK": {
        "keywords": ["instrument", "measure", "vitamin", "deficiency", "players", "sport"],
        "concepts": {"Scientific Instruments": ["instrument", "measure"],
                     "Vitamins & Diseases": ["vitamin", "deficiency"], "Sports GK": ["players", "team"]},
    },
    "Organisations, Days & Firsts": {
        "keywords": ["headquarters", "day", "observed", "first", "largest", "longest", "highest"],
        "concepts": {"Headquarters": ["headquarters"], "Important Days": ["observed", "day"],
                     "Superlatives (India)": ["largest", "longest", "highest"],
                     "First in India": ["first"]},
    },
}
