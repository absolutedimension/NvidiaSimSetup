"""General-Studies taxonomies for the real-PYQ govt banks (BPSC TRE / BPSC).

These banks are INGESTED past-paper questions, so unlike the generated pools they arrive with
`chapter = NULL`. That left the picker with nothing to offer (it fell back to "Full Syllabus
(mixed)"), and a student couldn't practise one topic at a time. These taxonomies give each GS
subject a real chapter list; `tag_gs_questions.py` keyword-classifies the banked questions into
them so the picker and the `/pool` chapter filter both work.

Schema matches the rest of syllabus.TAXONOMIES: {chapter: {"keywords": [...], "concepts": {name: [kw]}}}.
Keywords are matched case-insensitively against stem+options, most-specific first.
"""

GS_POLITY = {
    "Constitution & Preamble": {
        "keywords": ["constitution", "preamble", "constituent assembly", "amendment",
                     "schedule of the constitution", "basic structure", "sovereign"],
        "concepts": {"Making of the Constitution": ["constituent assembly", "drafting committee"],
                     "Amendments": ["amendment"]},
    },
    "Fundamental Rights & Duties": {
        "keywords": ["fundamental right", "fundamental dut", "directive principle",
                     "right to equality", "right to freedom", "article 14", "article 19",
                     "article 21", "article 32", "writ", "habeas corpus", "untouchability"],
        "concepts": {"Rights": ["fundamental right", "writ"],
                     "DPSP": ["directive principle"]},
    },
    "Union Executive & Parliament": {
        "keywords": ["president of india", "prime minister", "council of ministers",
                     "lok sabha", "rajya sabha", "parliament", "speaker", "money bill",
                     "ordinance", "vice-president", "impeachment"],
        "concepts": {"Executive": ["president", "prime minister"],
                     "Legislature": ["lok sabha", "rajya sabha", "parliament"]},
    },
    "Judiciary": {
        "keywords": ["supreme court", "high court", "chief justice", "judiciary",
                     "judicial review", "judgement", "judge"],
        "concepts": {"Courts": ["supreme court", "high court"]},
    },
    "State Government & Local Bodies": {
        "keywords": ["governor", "chief minister", "state legislature", "vidhan sabha",
                     "panchayat", "municipal", "local self", "zila parishad"],
        "concepts": {"Panchayati Raj": ["panchayat", "zila parishad"]},
    },
    "Constitutional & Statutory Bodies": {
        "keywords": ["election commission", "comptroller and auditor", "finance commission",
                     "public service commission", "attorney general", "niti aayog",
                     "human rights commission"],
        "concepts": {"Bodies": ["commission"]},
    },
    "Political Theory & Thinkers": {
        "keywords": ["democracy", "liberalism", "socialism", "marx", "plato", "aristotle",
                     "rousseau", "political theory", "sovereignty", "justice", "liberty",
                     "idealism", "utilitarian", "gandhian", "jayaprakash narayan", "ambedkar",
                     "equality", "rights theory", "anarchism", "fascism", "capitalism"],
        "concepts": {"Thinkers": ["marx", "plato", "aristotle", "rousseau", "ambedkar"]},
    },
    "International Relations": {
        "keywords": ["international", "united nations", "league of nations", "morgenthau",
                     "realist", "realism", "foreign policy", "diplomacy", "treaty",
                     "non-aligned", "security council", "cold war", "balance of power",
                     "national interest", "world order", "globalisation", "globalization"],
        "concepts": {"IR Theory": ["realist", "morgenthau", "balance of power"],
                     "Organisations": ["united nations", "security council"]},
    },
    "Comparative Government & Administration": {
        "keywords": ["federal system", "federalism", "unitary", "american", "british system",
                     "parliamentary system", "presidential system", "civil service",
                     "bureaucracy", "public administration", "committee on", "spoils",
                     "political party", "pressure group", "electoral"],
        "concepts": {"Comparative Politics": ["federalism", "presidential system"],
                     "Administration": ["bureaucracy", "civil service"]},
    },
}

GS_HISTORY = {
    "Ancient India": {
        "keywords": ["indus valley", "harappa", "vedic", "maurya", "ashoka", "gupta",
                     "buddha", "buddhism", "jain", "ancient", "stupa", "pataliputra"],
        "concepts": {"Indus Valley": ["harappa", "indus valley"],
                     "Mauryan & Gupta": ["maurya", "ashoka", "gupta"]},
    },
    "Medieval India": {
        "keywords": ["sultanate", "mughal", "akbar", "aurangzeb", "babur", "medieval",
                     "vijayanagara", "maratha", "bhakti", "sufi", "shivaji", "khilji"],
        "concepts": {"Mughals": ["mughal", "akbar", "aurangzeb"],
                     "Delhi Sultanate": ["sultanate", "khilji"]},
    },
    "Modern India & Freedom Struggle": {
        "keywords": ["british", "east india company", "revolt of 1857", "1857", "gandhi",
                     "indian national congress", "swaraj", "quit india", "non-cooperation",
                     "civil disobedience", "independence", "viceroy", "partition", "nehru",
                     "subhas chandra bose", "bhagat singh", "satyagraha"],
        "concepts": {"Freedom Movement": ["gandhi", "swaraj", "quit india", "satyagraha"],
                     "Colonial Rule": ["british", "east india company", "viceroy"]},
    },
    "Bihar in History": {
        "keywords": ["bihar", "champaran", "magadh", "nalanda", "patna", "vaishali"],
        "concepts": {"Bihar Movements": ["champaran"]},
    },
    "World History": {
        "keywords": ["french revolution", "russian revolution", "world war", "industrial revolution",
                     "renaissance", "cold war", "american revolution", "napoleon", "hitler"],
        "concepts": {"Revolutions": ["revolution"]},
    },
    "Art & Culture": {
        "keywords": ["temple", "architecture", "painting", "classical dance", "music",
                     "sculpture", "festival", "literature"],
        "concepts": {"Architecture": ["temple", "architecture"]},
    },
}

GS_GEOGRAPHY = {
    "Physical Geography": {
        "keywords": ["plateau", "mountain range", "volcano", "earthquake", "rock", "tectonic",
                     "landform", "erosion", "atmosphere", "latitude", "longitude", "core"],
        "concepts": {"Landforms": ["plateau", "mountain", "landform"]},
    },
    "Climate & Monsoon": {
        "keywords": ["monsoon", "rainfall", "climate", "cyclone", "temperature", "isotherm",
                     "humidity", "season", "wind"],
        "concepts": {"Monsoon": ["monsoon", "rainfall"]},
    },
    "Rivers & Water Resources": {
        "keywords": ["river", "tributary", "dam", "lake", "canal", "irrigation", "waterfall",
                     "ganga", "kosi", "delta", "basin"],
        "concepts": {"Rivers": ["river", "tributary"], "Dams": ["dam", "canal"]},
    },
    "Indian Geography": {
        "keywords": ["india", "state of", "district", "soil", "crop", "agriculture",
                     "population", "census", "mineral", "port", "railway"],
        "concepts": {"Soils & Crops": ["soil", "crop"]},
    },
    "Bihar Geography": {
        "keywords": ["bihar", "patna", "gangetic plain", "kosi"],
        "concepts": {"Bihar": ["bihar"]},
    },
    "World Geography": {
        "keywords": ["continent", "ocean", "strait", "desert", "country", "world",
                     "equator", "tropic", "hemisphere"],
        "concepts": {"World Physical": ["continent", "ocean"]},
    },
    "Environment & Ecology": {
        "keywords": ["forest", "wildlife", "biodiversity", "ecosystem", "pollution",
                     "national park", "sanctuary", "climate change", "conservation",
                     "greenhouse", "ozone", "tiger reserve"],
        "concepts": {"Conservation": ["national park", "sanctuary", "wildlife"]},
    },
}

GS_ECONOMICS = {
    "Basic Economic Concepts": {
        "keywords": ["demand", "supply", "elasticity", "utility", "market", "cost curve",
                     "production function", "consumer", "monopoly", "equilibrium"],
        "concepts": {"Micro": ["demand", "supply", "elasticity", "utility"]},
    },
    "National Income & Growth": {
        "keywords": ["gdp", "gnp", "national income", "per capita", "domestic product",
                     "growth rate", "nnp"],
        "concepts": {"Income Accounting": ["national income", "gdp", "gnp"]},
    },
    "Money, Banking & Finance": {
        "keywords": ["reserve bank", "rbi", "bank", "money supply", "credit", "repo",
                     "inflation", "currency", "monetary policy", "nbfc", "interest rate"],
        "concepts": {"Banking": ["bank", "rbi", "credit"], "Inflation": ["inflation"]},
    },
    "Public Finance & Budget": {
        "keywords": ["budget", "tax", "gst", "fiscal deficit", "revenue", "expenditure",
                     "finance commission", "subsidy", "disinvestment"],
        "concepts": {"Budget": ["budget", "deficit"], "Taxation": ["tax", "gst"]},
    },
    "Planning & Development": {
        "keywords": ["five year plan", "planning commission", "niti aayog", "poverty",
                     "unemployment", "human development", "yojana", "scheme", "mgnrega"],
        "concepts": {"Planning": ["plan", "niti aayog"], "Poverty": ["poverty", "unemployment"]},
    },
    "Agriculture & Industry": {
        "keywords": ["agriculture", "crop", "farmer", "minimum support price", "msp",
                     "industry", "manufacturing", "msme", "green revolution", "irrigation"],
        "concepts": {"Agriculture": ["agriculture", "crop", "farmer"]},
    },
    "Bihar Economy": {
        "keywords": ["bihar"],
        "concepts": {"Bihar": ["bihar"]},
    },
}

# Combined GS paper (BPSC prelims / TRE "General Studies"): chapters ARE the dimensions.
GS_GENERAL = {
    "Polity & Governance": {
        "keywords": ["constitution", "article", "fundamental right", "parliament", "president",
                     "supreme court", "governor", "panchayat", "election commission", "amendment",
                     "lok sabha", "rajya sabha", "judiciary"],
        "concepts": {"Polity": ["constitution", "parliament"]},
    },
    "History & Culture": {
        "keywords": ["dynasty", "empire", "mughal", "maurya", "gupta", "ashoka", "buddha",
                     "vedic", "harappa", "revolt", "gandhi", "freedom", "independence",
                     "british", "temple", "dance", "sultanate", "1857"],
        "concepts": {"History": ["dynasty", "empire", "freedom"]},
    },
    "Geography & Environment": {
        "keywords": ["river", "mountain", "monsoon", "climate", "soil", "forest", "national park",
                     "ocean", "plateau", "rainfall", "wildlife", "pollution", "biodiversity",
                     "tributary", "desert", "lake"],
        "concepts": {"Geography": ["river", "mountain", "climate"]},
    },
    "Economy": {
        "keywords": ["gdp", "inflation", "budget", "tax", "bank", "rbi", "poverty", "economy",
                     "economic", "five year plan", "niti aayog", "per capita", "agriculture",
                     "unemployment", "gst"],
        "concepts": {"Economy": ["gdp", "inflation", "bank"]},
    },
    "General Science": {
        "keywords": ["atom", "cell", "vitamin", "acid", "chemical", "electron", "energy",
                     "force", "disease", "blood", "photosynthesis", "gas", "metal", "enzyme",
                     "reaction", "lens", "magnet", "bacteria", "hormone", "protein", "synthesis",
                     "ovaries", "organ", "tissue", "digestion", "respiration", "nervous",
                     "gene", "dna", "chromosome", "plant", "reproduction", "friction",
                     "velocity", "current", "light", "sound", "heat", "compound", "element",
                     "molecule", "virus", "vaccine", "kidney", "heart", "brain", "muscle"],
        "concepts": {"Biology": ["cell", "protein", "organ", "blood", "gene"],
                     "Physics": ["force", "friction", "energy", "light", "current"],
                     "Chemistry": ["acid", "chemical", "compound", "element", "reaction"]},
    },
    "Reasoning & Aptitude": {
        "keywords": ["in english alphabet", "denotes", "coded as", "code language", "series",
                     "odd one out", "ratio of", "area of a square", "percentage", "average of",
                     "if a =", "next in the", "which is the smallest", "which is the largest",
                     "arrange the following", "logical order", "find the missing"],
        "concepts": {"Coding & Series": ["coded as", "series", "denotes"],
                     "Quantitative": ["ratio of", "percentage", "average of", "area of"]},
    },
    "Static GK": {
        "keywords": ["capital of", "currency", "award", "book", "author", "headquarters",
                     "first", "largest", "longest", "sport", "dance form", "festival",
                     "national symbol", "instrument", "day is celebrated", "day is observed",
                     "world day", "nickname", "trophy", "prize", "olympic", "stadium"],
        "concepts": {"Static GK": ["capital", "award", "headquarters"],
                     "Days & Awards": ["day is celebrated", "award", "prize"]},
    },
    "Current Affairs": {
        "keywords": ["2023", "2024", "2025", "recently", "appointed", "launched", "summit",
                     "inaugurated", "won the", "scheme launched"],
        "concepts": {"Current Affairs": ["recently", "summit"]},
    },
    "Society & Culture": {
        "keywords": ["culture", "personality", "society", "social", "caste", "tribe",
                     "family", "marriage", "religion", "education policy", "sociolog"],
        "concepts": {"Sociology": ["society", "culture", "caste"]},
    },
}


# Explicit mixed buckets (see tag_gs_questions.FALLBACK) so keyword-unmatched real PYQs stay
# reachable from the picker instead of sitting chapter-less. Listed last in each taxonomy.
GS_POLITY["General Polity (mixed)"] = {"keywords": [], "concepts": {}}
GS_HISTORY["General History (mixed)"] = {"keywords": [], "concepts": {}}
GS_GEOGRAPHY["General Geography (mixed)"] = {"keywords": [], "concepts": {}}
GS_ECONOMICS["General Economics (mixed)"] = {"keywords": [], "concepts": {}}
GS_GENERAL["General Studies (mixed)"] = {"keywords": [], "concepts": {}}
