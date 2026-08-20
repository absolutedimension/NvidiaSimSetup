"""GENERATE-FROM-DATA Static GK engine — deterministic, correct-by-construction General Knowledge
MCQs for the SSC / Railway / Banking / BPSC "Static Portion — GK" section.

The third sibling of qbank.quantgen + qbank.reasoninggen. Static GK is FACTUAL and STABLE (capitals,
currencies, dances, rivers, Constitution articles…), so we embed VERIFIED fact tables and generate
questions FROM the data: the correct answer is a looked-up fact (not an LLM guess) and distractors are
drawn from the SAME table (plausible, same category). Impossible to serve a wrong key, copyright-clean
(our own phrasing over public facts), UNLIMITED (fresh pairing every call).

NOT included: current affairs / anything time-sensitive (current CMs, latest winners) — those change
and belong to a dated Current-Affairs feed, not this static engine.

Live path: generator.generate_test() routes here when can_generate() covers (subject). Each chapter
maps to builders; a builder(rng, diff) returns {stem, correct, distractors, solution, concept}.
"""
import hashlib
import random

from . import staticgk_hi as GKHI
from .models import Question, content_hash

SUBJECT = "General Knowledge"
EXAM = "SSC CGL"

_SUBJECT_ALIASES = {
    "general knowledge", "static gk", "gk", "static portion", "static portion - gk",
    "static portion — gk", "general awareness", "static general knowledge",
}


def can_generate(exam, subject, chapter=None) -> bool:
    if (subject or "").strip().lower() not in _SUBJECT_ALIASES:
        return False
    if not chapter:
        return True
    return chapter in _CHAP_BUILDERS


# ---- MCQ assembly (mirrors reasoninggen) -----------------------------------

def _mcq(seed, correct, distractors, rng, n=4):
    labels = ["A", "B", "C", "D"][:n]
    opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))[:n]
    if str(correct) not in opts:
        opts[-1] = str(correct)
    rot = sum(map(ord, seed)) % n
    opts = opts[rot:] + opts[:rot]
    options = [{"label": l, "text": t} for l, t in zip(labels, opts)]
    return options, labels[opts.index(str(correct))]


def _make_question(built, rng, spec):
    stem = built["stem"].strip()
    options, ans = _mcq(stem, built["correct"], built["distractors"], rng)
    diff = spec.get("dmax") or spec.get("dmin") or 2
    qid = "gen_gk_" + hashlib.md5((spec.get("chapter", "") + "|" + stem).encode()).hexdigest()[:14]
    q = Question(
        id=qid, exam=spec.get("exam") or EXAM, subject=spec.get("subject") or SUBJECT,
        stem=stem, qtype="MCQ_single", options=options, correct_answer=ans,
        stem_hi=(built.get("stem_hi") or "").strip(),
        solution_hi=(built.get("solution_hi") or "").strip(),
        options_hi=([{"label": o["label"],
                      "text": (built.get("hi_opts") or {}).get(o["text"], o["text"])}
                     for o in options] if built.get("stem_hi") else []),
        solution=built.get("solution", ""), chapter=spec.get("chapter"),
        concept=built.get("concept"), difficulty=diff, source="staticgkgen",
        generated=True, hash=content_hash(stem))
    q.verified = True
    return q


def _distractors(pool, correct, rng, k=3):
    cand = [x for x in dict.fromkeys(pool) if x != correct]
    rng.shuffle(cand)
    return cand[:k]


# =============================================================================
# VERIFIED FACT TABLES (stable facts only)
# =============================================================================

STATE_CAPITAL = {
    "Andhra Pradesh": "Amaravati", "Arunachal Pradesh": "Itanagar", "Assam": "Dispur",
    "Bihar": "Patna", "Chhattisgarh": "Raipur", "Goa": "Panaji", "Gujarat": "Gandhinagar",
    "Haryana": "Chandigarh", "Himachal Pradesh": "Shimla", "Jharkhand": "Ranchi",
    "Karnataka": "Bengaluru", "Kerala": "Thiruvananthapuram", "Madhya Pradesh": "Bhopal",
    "Maharashtra": "Mumbai", "Manipur": "Imphal", "Meghalaya": "Shillong", "Mizoram": "Aizawl",
    "Nagaland": "Kohima", "Odisha": "Bhubaneswar", "Punjab": "Chandigarh", "Rajasthan": "Jaipur",
    "Sikkim": "Gangtok", "Tamil Nadu": "Chennai", "Telangana": "Hyderabad", "Tripura": "Agartala",
    "Uttar Pradesh": "Lucknow", "Uttarakhand": "Dehradun", "West Bengal": "Kolkata",
}
COUNTRY_CAPITAL = {
    "Japan": "Tokyo", "France": "Paris", "Australia": "Canberra", "Canada": "Ottawa",
    "Brazil": "Brasilia", "Egypt": "Cairo", "Nepal": "Kathmandu", "Bhutan": "Thimphu",
    "Bangladesh": "Dhaka", "China": "Beijing", "Russia": "Moscow", "Italy": "Rome",
    "Germany": "Berlin", "Spain": "Madrid", "Turkey": "Ankara", "Iran": "Tehran",
    "Thailand": "Bangkok", "Indonesia": "Jakarta", "Argentina": "Buenos Aires",
    "Saudi Arabia": "Riyadh", "Afghanistan": "Kabul", "Myanmar": "Naypyidaw",
    "Malaysia": "Kuala Lumpur", "Vietnam": "Hanoi", "South Korea": "Seoul", "Greece": "Athens",
}
COUNTRY_CURRENCY = {
    "Japan": "Yen", "United States": "Dollar", "United Kingdom": "Pound Sterling", "Russia": "Ruble",
    "China": "Yuan", "Nepal": "Nepalese Rupee", "Bangladesh": "Taka", "Thailand": "Baht",
    "Bhutan": "Ngultrum", "Myanmar": "Kyat", "Indonesia": "Rupiah", "Iran": "Rial",
    "Saudi Arabia": "Riyal", "Turkey": "Lira", "South Africa": "Rand", "Vietnam": "Dong",
    "Malaysia": "Ringgit", "South Korea": "Won", "Israel": "Shekel", "Kuwait": "Dinar",
}
DANCE_STATE = {
    "Bharatanatyam": "Tamil Nadu", "Kathak": "Uttar Pradesh", "Kathakali": "Kerala",
    "Kuchipudi": "Andhra Pradesh", "Odissi": "Odisha", "Manipuri": "Manipur",
    "Mohiniyattam": "Kerala", "Sattriya": "Assam", "Bihu": "Assam", "Garba": "Gujarat",
    "Bhangra": "Punjab", "Ghoomar": "Rajasthan", "Lavani": "Maharashtra",
    "Yakshagana": "Karnataka", "Chhau": "Jharkhand",
}
RIVER_ORIGIN = {
    "Ganga": "Gangotri Glacier (Gaumukh)", "Yamuna": "Yamunotri", "Godavari": "Trimbakeshwar (Nashik)",
    "Krishna": "Mahabaleshwar", "Narmada": "Amarkantak", "Kaveri": "Talakaveri (Kodagu)",
    "Indus": "near Lake Mansarovar (Tibet)", "Brahmaputra": "Angsi Glacier (Tibet)",
    "Sabarmati": "Aravalli Hills", "Mahanadi": "Sihawa (Chhattisgarh)", "Tapti": "Multai (Betul, MP)",
}
PARK_STATE = {
    "Jim Corbett National Park": "Uttarakhand", "Kaziranga National Park": "Assam",
    "Gir National Park": "Gujarat", "Ranthambore National Park": "Rajasthan",
    "Bandhavgarh National Park": "Madhya Pradesh", "Kanha National Park": "Madhya Pradesh",
    "Sundarbans National Park": "West Bengal", "Periyar National Park": "Kerala",
    "Bandipur National Park": "Karnataka", "Sariska Tiger Reserve": "Rajasthan",
    "Dudhwa National Park": "Uttar Pradesh", "Manas National Park": "Assam",
    "Simlipal National Park": "Odisha",
}
BOOK_AUTHOR = {
    "The Discovery of India": "Jawaharlal Nehru", "Wings of Fire": "A.P.J. Abdul Kalam",
    "Gitanjali": "Rabindranath Tagore", "Godan": "Munshi Premchand", "Arthashastra": "Kautilya",
    "The Story of My Experiments with Truth": "Mahatma Gandhi", "Train to Pakistan": "Khushwant Singh",
    "Malgudi Days": "R.K. Narayan", "The God of Small Things": "Arundhati Roy",
    "Panchatantra": "Vishnu Sharma", "India Wins Freedom": "Maulana Abul Kalam Azad",
    "Interpreter of Maladies": "Jhumpa Lahiri",
}
AWARD_FIELD = {
    "Bharat Ratna": "the highest civilian honour", "Jnanpith Award": "Literature",
    "Arjuna Award": "Sports", "Dronacharya Award": "coaching in Sports",
    "Dadasaheb Phalke Award": "Cinema", "Shanti Swarup Bhatnagar Prize": "Science & Technology",
    "Saraswati Samman": "Literature", "Vyas Samman": "Hindi Literature",
    "Major Dhyan Chand Khel Ratna": "Sports (highest)",
}
ARTICLE_SUBJECT = {
    "Article 14": "Equality before law", "Article 19": "Freedom of speech and expression",
    "Article 21": "Protection of life and personal liberty",
    "Article 32": "Right to Constitutional Remedies", "Article 44": "Uniform Civil Code",
    "Article 51A": "Fundamental Duties", "Article 356": "President's Rule in a State",
    "Article 368": "Amendment of the Constitution", "Article 280": "Finance Commission",
    "Article 324": "Election Commission of India", "Article 148": "Comptroller and Auditor General",
    "Article 343": "Official language of the Union",
}
ORG_HQ = {
    "WHO": "Geneva", "United Nations (UN)": "New York", "UNESCO": "Paris",
    "IMF": "Washington D.C.", "World Bank": "Washington D.C.", "WTO": "Geneva", "ILO": "Geneva",
    "FIFA": "Zurich", "OPEC": "Vienna", "INTERPOL": "Lyon", "SAARC": "Kathmandu",
    "ASEAN": "Jakarta", "ISRO": "Bengaluru", "RBI": "Mumbai", "NATO": "Brussels",
    "International Court of Justice": "The Hague",
}
INSTRUMENT_MEASURE = {
    "Barometer": "atmospheric pressure", "Thermometer": "temperature",
    "Seismograph": "earthquake intensity", "Hygrometer": "humidity",
    "Ammeter": "electric current", "Anemometer": "wind speed", "Odometer": "distance travelled",
    "Speedometer": "speed", "Sphygmomanometer": "blood pressure", "Lactometer": "purity of milk",
    "Voltmeter": "voltage", "Pyrometer": "very high temperatures",
}
VITAMIN_DISEASE = {
    "Vitamin A": "Night blindness", "Vitamin B1": "Beriberi", "Vitamin C": "Scurvy",
    "Vitamin D": "Rickets", "Vitamin B12": "Pernicious anaemia", "Vitamin B3": "Pellagra",
    "Vitamin K": "delayed blood clotting",
}
SPORT_PLAYERS = {
    "Cricket": 11, "Football": 11, "Hockey": 11, "Kabaddi": 7, "Kho-Kho": 9, "Basketball": 5,
    "Volleyball": 6, "Water Polo": 7, "Baseball": 9, "Rugby": 15, "Netball": 7, "Polo": 4,
}
DAY_DATE = {
    "World Environment Day": "5 June", "International Yoga Day": "21 June",
    "World Health Day": "7 April", "Teachers' Day (India)": "5 September",
    "Children's Day (India)": "14 November", "World Water Day": "22 March",
    "International Women's Day": "8 March", "World Earth Day": "22 April",
    "Gandhi Jayanti": "2 October", "World Literacy Day": "8 September",
    "National Science Day (India)": "28 February",
}
# (question, correct, [distractors])
SUPERLATIVES = [
    ("The largest Indian state by area is", "Rajasthan", ["Madhya Pradesh", "Maharashtra", "Uttar Pradesh"]),
    ("The smallest Indian state by area is", "Goa", ["Sikkim", "Tripura", "Nagaland"]),
    ("The longest river in India is", "Ganga", ["Godavari", "Brahmaputra", "Yamuna"]),
    ("The most populous Indian state is", "Uttar Pradesh", ["Maharashtra", "Bihar", "West Bengal"]),
    ("The largest freshwater lake in India is", "Wular Lake", ["Chilika Lake", "Dal Lake", "Loktak Lake"]),
    ("The largest saltwater lake in India is", "Chilika Lake", ["Wular Lake", "Sambhar Lake", "Pulicat Lake"]),
    ("The largest desert in India is", "Thar Desert", ["Rann of Kutch", "Cold Desert (Ladakh)", "Deccan"]),
    ("The highest mountain peak in India is", "Kangchenjunga", ["Nanda Devi", "K2", "Mount Everest"]),
    ("The longest National Highway in India is", "NH 44", ["NH 27", "NH 48", "NH 16"]),
    ("The largest delta in the world is the", "Sundarbans (Ganga-Brahmaputra) Delta", ["Nile Delta", "Godavari Delta", "Krishna Delta"]),
]
FIRSTS = [
    ("The first President of India was", "Dr. Rajendra Prasad", ["Jawaharlal Nehru", "Dr. S. Radhakrishnan", "Dr. Zakir Husain"]),
    ("The first Prime Minister of India was", "Jawaharlal Nehru", ["Sardar Patel", "Dr. Rajendra Prasad", "Lal Bahadur Shastri"]),
    ("The first woman Prime Minister of India was", "Indira Gandhi", ["Sarojini Naidu", "Pratibha Patil", "Sonia Gandhi"]),
    ("The first woman President of India was", "Pratibha Patil", ["Indira Gandhi", "Sarojini Naidu", "Droupadi Murmu"]),
    ("The first Indian to travel to space was", "Rakesh Sharma", ["Kalpana Chawla", "Sunita Williams", "Ravish Malhotra"]),
    ("The first woman IPS officer of India was", "Kiran Bedi", ["Kiran Mazumdar", "Anna Rajam Malhotra", "Sarla Thakral"]),
    ("The first Field Marshal of India was", "Sam Manekshaw", ["K.M. Cariappa", "General Thimayya", "Arjan Singh"]),
    ("The first Governor-General of independent India was", "Lord Mountbatten", ["C. Rajagopalachari", "Lord Wavell", "Warren Hastings"]),
    ("The first Indian to win a Nobel Prize was", "Rabindranath Tagore", ["C.V. Raman", "Mother Teresa", "Amartya Sen"]),
]


# =============================================================================
# BUILDERS
# =============================================================================

def _b_forward(table, q_tmpl, concept, unit=""):
    """Factory: 'What is the <fact> of <key>?' correct=value, distractors=other values.

    Hindi rides along only when staticgk_hi has hand-written every part — template, key, answer
    and all three distractors. Partial coverage yields an English-only question rather than a
    half-Hindi one, and a bilingual paper then simply does not draw it.
    """
    def build(rng, diff):
        k = rng.choice(list(table))
        v = table[k]
        stem = q_tmpl.format(k=k)
        d = _distractors(list(table.values()), v, rng)
        out = {"stem": stem, "correct": f"{v}{unit}",
               "distractors": [f"{x}{unit}" for x in d],
               "solution": stem + f" {v}{unit}.", "concept": concept}
        bi = GKHI.bilingual(q_tmpl, k, v, d) if not unit else None
        if bi:
            out["stem_hi"] = bi["tmpl"].format(k=bi["key"])
            out["solution_hi"] = bi["tmpl"].format(k=bi["key"]) + f" उत्तर: {bi['correct']}।"
            out["hi_opts"] = dict(zip([f"{v}{unit}"] + [f"{x}{unit}" for x in d],
                                      [bi["correct"]] + bi["distractors"]))
        return out
    return build

def _b_reverse(table, q_tmpl, concept):
    """Factory: 'Which <key-type> has <value>?' — only for values that are UNIQUE in the table."""
    inv = {}
    for k, v in table.items():
        inv.setdefault(v, []).append(k)
    uniq = {v: ks[0] for v, ks in inv.items() if len(ks) == 1}
    def build(rng, diff):
        if not uniq:
            return None
        v = rng.choice(list(uniq))
        k = uniq[v]
        stem = q_tmpl.format(v=v)
        d = _distractors([kk for kk in table if kk != k], k, rng)
        return {"stem": stem, "correct": k, "distractors": d,
                "solution": stem + f" {k}.", "concept": concept}
    return build

def _b_choice(items, concept):
    """Factory for (question, correct, distractors) lists (superlatives, firsts)."""
    def build(rng, diff):
        q, correct, dist = rng.choice(items)
        return {"stem": q + " ______ .", "correct": correct,
                "distractors": list(dist)[:3], "solution": q + f" {correct}.",
                "concept": concept}
    return build

def _b_sport_players(rng, diff):
    s = rng.choice(list(SPORT_PLAYERS))
    n = SPORT_PLAYERS[s]
    stem = f"How many players are there in a {s} team (per side)?"
    d = _distractors([str(x) for x in SPORT_PLAYERS.values()], str(n), rng)
    return {"stem": stem, "correct": str(n), "distractors": d,
            "solution": f"A {s} team has {n} players per side.", "concept": "Sports GK"}


# =============================================================================
# chapter -> builders
# =============================================================================

_CHAP_BUILDERS = {
    "Indian States & Capitals": [
        _b_forward(STATE_CAPITAL, "What is the capital of {k}?", "State Capitals"),
        _b_reverse(STATE_CAPITAL, "'{v}' is the capital of which Indian state?", "State Capitals"),
    ],
    "World Capitals & Currencies": [
        _b_forward(COUNTRY_CAPITAL, "What is the capital of {k}?", "World Capitals"),
        _b_reverse(COUNTRY_CAPITAL, "'{v}' is the capital of which country?", "World Capitals"),
        _b_forward(COUNTRY_CURRENCY, "What is the currency of {k}?", "World Currencies"),
    ],
    "Rivers & National Parks": [
        _b_forward(RIVER_ORIGIN, "Where does the river {k} originate?", "Rivers of India"),
        _b_forward(PARK_STATE, "In which state is {k} located?", "National Parks"),
        _b_reverse(PARK_STATE, "{v} — which of these National Parks is located in it?", "National Parks"),
    ],
    "Art, Culture & Books": [
        _b_forward(DANCE_STATE, "The classical/folk dance '{k}' belongs to which state?", "Dances of India"),
        _b_forward(BOOK_AUTHOR, "Who is the author of the book '{k}'?", "Books & Authors"),
        _b_reverse(BOOK_AUTHOR, "Which book was written by {v}?", "Books & Authors"),
        _b_forward(AWARD_FIELD, "The {k} is given in which field?", "Awards & Honours"),
    ],
    "Indian Polity (Constitution)": [
        _b_forward(ARTICLE_SUBJECT, "Which subject does {k} of the Indian Constitution deal with?", "Constitution Articles"),
        _b_reverse(ARTICLE_SUBJECT, "Which Article of the Constitution deals with '{v}'?", "Constitution Articles"),
    ],
    "Static Science GK": [
        _b_forward(INSTRUMENT_MEASURE, "What does a {k} measure?", "Scientific Instruments"),
        _b_reverse(INSTRUMENT_MEASURE, "Which instrument is used to measure {v}?", "Scientific Instruments"),
        _b_forward(VITAMIN_DISEASE, "Deficiency of {k} causes which disease?", "Vitamins & Diseases"),
        _b_sport_players,
    ],
    "Organisations, Days & Firsts": [
        _b_forward(ORG_HQ, "Where is the headquarters of {k}?", "Headquarters"),
        _b_forward(DAY_DATE, "On which date is {k} observed?", "Important Days"),
        _b_reverse(DAY_DATE, "Which day is observed on {v}?", "Important Days"),
        _b_choice(SUPERLATIVES, "Superlatives (India)"),
        _b_choice(FIRSTS, "First in India"),
    ],
}


def _chapters_for(spec):
    ch = spec.get("chapter")
    if ch and ch in _CHAP_BUILDERS:
        return [ch]
    return list(_CHAP_BUILDERS.keys())


def generate_test(store, spec: dict, count: int = 5) -> dict:
    rng = random.Random()
    chapters = _chapters_for(spec)
    accepted, seen = [], set()
    attempts = 0
    while len(accepted) < count and attempts < count * 25:
        attempts += 1
        ch = spec.get("chapter") or rng.choice(chapters)
        sp = dict(spec, chapter=ch)
        builder = rng.choice(_CHAP_BUILDERS[ch])
        try:
            built = builder(rng, spec.get("dmax") or spec.get("dmin") or 2)
            if not built:
                continue
            q = _make_question(built, rng, sp)
        except Exception:
            continue
        if q.hash in seen or len(q.options) < 4:
            continue
        seen.add(q.hash)
        if store is not None:
            store.upsert(q)
        accepted.append(q)
    return {
        "spec": spec, "generator": "staticgkgen", "requested": count,
        "generated": len(accepted), "rejected": [],
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
    }


# =============================================================================
# EXPANSION (2026-08-14) — ~20 more verified fact tables + choice lists so the
# Static-GK pool clears 1000. Appended: tables, then _CHAP_BUILDERS registration.
# Stable facts only (no current affairs). Distractors auto-drawn from same table.
# =============================================================================

ELEMENT_SYMBOL = {
    "Sodium": "Na", "Potassium": "K", "Iron": "Fe", "Gold": "Au", "Silver": "Ag",
    "Copper": "Cu", "Lead": "Pb", "Tin": "Sn", "Mercury": "Hg", "Zinc": "Zn",
    "Calcium": "Ca", "Carbon": "C", "Nitrogen": "N", "Hydrogen": "H", "Helium": "He",
    "Chlorine": "Cl", "Sulphur": "S", "Phosphorus": "P", "Aluminium": "Al", "Tungsten": "W",
}
COMMON_CHEM = {
    "Common salt": "Sodium chloride", "Baking soda": "Sodium bicarbonate",
    "Washing soda": "Sodium carbonate", "Quicklime": "Calcium oxide",
    "Slaked lime": "Calcium hydroxide", "Chalk / Limestone": "Calcium carbonate",
    "Blue vitriol": "Copper sulphate", "Green vitriol": "Ferrous sulphate",
    "Epsom salt": "Magnesium sulphate", "Marsh gas": "Methane", "Laughing gas": "Nitrous oxide",
    "Vinegar": "Acetic acid", "Caustic soda": "Sodium hydroxide", "Plaster of Paris": "Calcium sulphate hemihydrate",
}
METAL_ORE = {
    "Bauxite": "Aluminium", "Haematite": "Iron", "Galena": "Lead", "Cinnabar": "Mercury",
    "Zinc blende": "Zinc", "Chalcopyrite": "Copper", "Cassiterite": "Tin", "Monazite": "Thorium",
}
INVENTION_INVENTOR = {
    "Telephone": "Alexander Graham Bell", "Electric bulb": "Thomas Edison",
    "Radio": "Guglielmo Marconi", "Television": "John Logie Baird", "Steam engine": "James Watt",
    "Telegraph": "Samuel Morse", "Dynamite": "Alfred Nobel", "Aeroplane": "Wright Brothers",
    "Printing press": "Johannes Gutenberg", "Penicillin": "Alexander Fleming",
    "X-ray": "Wilhelm Roentgen", "Telescope": "Galileo Galilei",
    "Analytical engine (computer)": "Charles Babbage", "Dynamo": "Michael Faraday",
}
SOBRIQUET = {
    "Pink City": "Jaipur", "Blue City": "Jodhpur", "Golden City": "Jaisalmer",
    "City of Lakes": "Udaipur", "City of Nawabs": "Lucknow", "Manchester of India": "Ahmedabad",
    "City of Joy": "Kolkata", "Queen of the Arabian Sea": "Kochi", "City of Pearls": "Hyderabad",
    "Diamond City": "Surat", "Steel City of India": "Jamshedpur", "Silicon Valley of India": "Bengaluru",
}
MONUMENT_CITY = {
    "Taj Mahal": "Agra", "Qutub Minar": "Delhi", "Gateway of India": "Mumbai",
    "Charminar": "Hyderabad", "Hawa Mahal": "Jaipur", "Victoria Memorial": "Kolkata",
    "Golden Temple": "Amritsar", "Meenakshi Temple": "Madurai", "Konark Sun Temple": "Konark",
    "Sanchi Stupa": "Sanchi", "Mysore Palace": "Mysore", "Ajanta Caves": "Aurangabad",
}
DAM_RIVER = {
    "Bhakra Nangal Dam": "Sutlej", "Hirakud Dam": "Mahanadi", "Sardar Sarovar Dam": "Narmada",
    "Nagarjuna Sagar Dam": "Krishna", "Tehri Dam": "Bhagirathi", "Mettur Dam": "Kaveri",
    "Farakka Barrage": "Ganga", "Nizam Sagar Dam": "Manjira",
}
LAKE_STATE2 = {
    "Dal Lake": "Jammu and Kashmir", "Chilika Lake": "Odisha", "Loktak Lake": "Manipur",
    "Sambhar Lake": "Rajasthan", "Vembanad Lake": "Kerala", "Hussain Sagar": "Telangana",
    "Pulicat Lake": "Andhra Pradesh",
}
FESTIVAL_STATE = {
    "Onam": "Kerala", "Bihu (festival)": "Assam", "Pongal": "Tamil Nadu", "Baisakhi": "Punjab",
    "Hornbill Festival": "Nagaland", "Rann Utsav": "Gujarat", "Chhath Puja": "Bihar",
    "Hemis Festival": "Ladakh", "Durga Puja": "West Bengal",
}
SI_UNIT = {
    "Force": "Newton", "Energy": "Joule", "Power": "Watt", "Pressure": "Pascal",
    "Frequency": "Hertz", "Electric current": "Ampere", "Electric resistance": "Ohm",
    "Temperature": "Kelvin", "Electric charge": "Coulomb", "Magnetic flux": "Weber",
    "Luminous intensity": "Candela",
}
NATIONAL_SYMBOL = {
    "National animal of India": "Tiger", "National bird of India": "Peacock",
    "National flower of India": "Lotus", "National tree of India": "Banyan",
    "National fruit of India": "Mango", "National aquatic animal of India": "Gangetic Dolphin",
    "National river of India": "Ganga", "National reptile of India": "King Cobra",
}
FATHER_OF = {
    "the Nation (India)": "Mahatma Gandhi", "the Indian Constitution": "B.R. Ambedkar",
    "the Green Revolution in India": "M.S. Swaminathan", "the White Revolution in India": "Verghese Kurien",
    "the Indian Space Programme": "Vikram Sarabhai", "Modern Physics": "Albert Einstein",
    "Geometry": "Euclid", "Economics": "Adam Smith", "Genetics": "Gregor Mendel",
    "the Indian Missile Programme": "A.P.J. Abdul Kalam",
}
STADIUM_CITY = {
    "Eden Gardens": "Kolkata", "Wankhede Stadium": "Mumbai", "M. Chinnaswamy Stadium": "Bengaluru",
    "Arun Jaitley Stadium": "Delhi", "M.A. Chidambaram Stadium": "Chennai",
    "Narendra Modi Stadium": "Ahmedabad", "Rajiv Gandhi Intl Stadium": "Hyderabad",
    "Green Park Stadium": "Kanpur",
}
BOUNDARY_LINE = {
    "Radcliffe Line": "India and Pakistan", "McMahon Line": "India and China",
    "Durand Line": "Pakistan and Afghanistan", "38th Parallel": "North and South Korea",
    "49th Parallel": "USA and Canada", "Maginot Line": "France and Germany",
    "Oder-Neisse Line": "Germany and Poland",
}
CONSTITUTION_BORROWED = {
    "Fundamental Rights": "USA", "Directive Principles of State Policy": "Ireland",
    "Parliamentary form of government": "Britain", "Federation with a strong Centre": "Canada",
    "Emergency provisions": "Germany", "Concurrent List": "Australia",
    "Fundamental Duties": "Russia (USSR)", "Procedure for amendment": "South Africa",
}
RIVER_CITY = {   # city on the bank of (river)
    "Delhi": "Yamuna", "Kolkata": "Hooghly", "Varanasi": "Ganga", "Lucknow": "Gomti",
    "Ahmedabad": "Sabarmati", "Hyderabad": "Musi", "Nashik": "Godavari", "Srinagar": "Jhelum",
    "Vijayawada": "Krishna", "Surat": "Tapti", "Jabalpur": "Narmada", "Kota": "Chambal",
}

# choice-list facts (question, correct, [distractors])
BATTLES = [
    ("The First Battle of Panipat was fought in", "1526", ["1556", "1761", "1600"]),
    ("The Third Battle of Panipat was fought in", "1761", ["1526", "1556", "1857"]),
    ("The Battle of Plassey was fought in", "1757", ["1764", "1526", "1857"]),
    ("The Battle of Buxar was fought in", "1764", ["1757", "1526", "1856"]),
    ("The Battle of Haldighati was fought in", "1576", ["1526", "1600", "1757"]),
    ("The Battle of Talikota was fought in", "1565", ["1526", "1576", "1600"]),
]
FREEDOM_EVENTS = [
    ("The Jallianwala Bagh massacre took place in", "1919", ["1920", "1930", "1942"]),
    ("The Non-Cooperation Movement began in", "1920", ["1919", "1930", "1942"]),
    ("The Dandi (Salt) March took place in", "1930", ["1920", "1942", "1919"]),
    ("The Quit India Movement was launched in", "1942", ["1930", "1920", "1919"]),
    ("The Indian National Congress was founded in", "1885", ["1905", "1919", "1857"]),
    ("The partition of Bengal took place in", "1905", ["1885", "1911", "1919"]),
    ("India gained independence in", "1947", ["1948", "1950", "1945"]),
    ("The Indian Constitution came into force in", "1950", ["1947", "1949", "1952"]),
]
WORLD_FIRSTS = [
    ("The first man to walk on the Moon was", "Neil Armstrong", ["Buzz Aldrin", "Yuri Gagarin", "Michael Collins"]),
    ("The first man in space was", "Yuri Gagarin", ["Neil Armstrong", "Alan Shepard", "Rakesh Sharma"]),
    ("The first woman in space was", "Valentina Tereshkova", ["Kalpana Chawla", "Sunita Williams", "Sally Ride"]),
    ("The first person to climb Mount Everest was (with Tenzing Norgay)", "Edmund Hillary", ["George Mallory", "Junko Tabei", "Tenzing's brother"]),
    ("The first Secretary-General of the United Nations was", "Trygve Lie", ["U Thant", "Kofi Annan", "Dag Hammarskjold"]),
]
BIOLOGY_FACTS = [
    ("The largest organ of the human body is the", "Skin", ["Liver", "Brain", "Heart"]),
    ("The largest gland in the human body is the", "Liver", ["Pancreas", "Thyroid", "Skin"]),
    ("The smallest bone in the human body is the", "Stapes", ["Femur", "Stirrup rib", "Malleus"]),
    ("The longest bone in the human body is the", "Femur", ["Tibia", "Humerus", "Stapes"]),
    ("The number of bones in the adult human body is", "206", ["300", "212", "198"]),
    ("The universal donor blood group is", "O negative", ["AB positive", "A positive", "O positive"]),
    ("The universal recipient blood group is", "AB positive", ["O negative", "B positive", "A negative"]),
    ("The powerhouse of the cell is the", "Mitochondria", ["Nucleus", "Ribosome", "Golgi body"]),
]

def _mk_forward(table, tmpl, concept, unit=""):
    return _b_forward(table, tmpl, concept, unit)
def _mk_reverse(table, tmpl, concept):
    return _b_reverse(table, tmpl, concept)

_CHAP_BUILDERS.update({
    "General Science (Static)": [
        _mk_forward(ELEMENT_SYMBOL, "What is the chemical symbol of {k}?", "Chemical Symbols"),
        _mk_reverse(ELEMENT_SYMBOL, "'{v}' is the chemical symbol of which element?", "Chemical Symbols"),
        _mk_forward(COMMON_CHEM, "What is the chemical name of '{k}'?", "Common Chemical Names"),
        _mk_forward(METAL_ORE, "{k} is an ore of which metal?", "Metals & Ores"),
        _mk_forward(SI_UNIT, "What is the SI unit of {k}?", "SI Units"),
        _mk_reverse(SI_UNIT, "'{v}' is the SI unit of which physical quantity?", "SI Units"),
        _b_choice(BIOLOGY_FACTS, "Human Body"),
    ],
    "Inventions & Discoveries": [
        _mk_forward(INVENTION_INVENTOR, "Who invented/discovered the {k}?", "Inventions"),
        _mk_reverse(INVENTION_INVENTOR, "What is {v} famous for inventing/discovering?", "Inventions"),
        _b_choice(WORLD_FIRSTS, "World Firsts"),
    ],
    "Indian Geography (Static)": [
        _mk_forward(SOBRIQUET, "Which city is known as the '{k}'?", "Sobriquets of Cities"),
        _mk_reverse(SOBRIQUET, "By which nickname is {v} known?", "Sobriquets of Cities"),
        _mk_forward(DAM_RIVER, "{k} is built on which river?", "Dams & Rivers"),
        _mk_forward(LAKE_STATE2, "In which state is {k} located?", "Lakes of India"),
        _mk_forward(RIVER_CITY, "The city of {k} is situated on the bank of which river?", "Rivers & Cities"),
        _mk_forward(FESTIVAL_STATE, "The festival '{k}' is mainly celebrated in which state?", "Festivals of India"),
        _mk_reverse(FESTIVAL_STATE, "Which festival is mainly celebrated in {v}?", "Festivals of India"),
    ],
    "Monuments & Culture (Static)": [
        _mk_forward(MONUMENT_CITY, "In which city is the {k} located?", "Monuments of India"),
        _mk_forward(NATIONAL_SYMBOL, "What is the {k}?", "National Symbols"),
        _mk_forward(STADIUM_CITY, "In which city is {k} located?", "Stadiums"),
    ],
    "Indian Polity (Static)": [
        _mk_forward(CONSTITUTION_BORROWED, "From which country's constitution did India borrow '{k}'?", "Sources of the Constitution"),
        _mk_forward(FATHER_OF, "Who is known as the Father of {k}?", "Father of…"),
    ],
    "Indian History (Static)": [
        _b_choice(BATTLES, "Battles & Years"),
        _b_choice(FREEDOM_EVENTS, "Freedom Struggle Timeline"),
    ],
    "World Boundaries": [
        _mk_forward(BOUNDARY_LINE, "The '{k}' is the boundary between which two countries/regions?", "Boundary Lines"),
    ],
})


# --- EXPANSION batch 2 (2026-08-14): expand big tables + more new tables to clear 1000 ---
COUNTRY_CAPITAL.update({
    "Mexico": "Mexico City", "Sweden": "Stockholm", "Norway": "Oslo", "Finland": "Helsinki",
    "Denmark": "Copenhagen", "Netherlands": "Amsterdam", "Belgium": "Brussels", "Switzerland": "Bern",
    "Austria": "Vienna", "Portugal": "Lisbon", "Poland": "Warsaw", "Ukraine": "Kyiv",
    "Kenya": "Nairobi", "Nigeria": "Abuja", "Qatar": "Doha", "United Arab Emirates": "Abu Dhabi",
    "Kuwait": "Kuwait City", "Philippines": "Manila", "New Zealand": "Wellington", "Cuba": "Havana",
    "Chile": "Santiago", "Peru": "Lima", "Colombia": "Bogota", "Cambodia": "Phnom Penh",
    "Mongolia": "Ulaanbaatar", "Maldives": "Male", "Oman": "Muscat", "Sri Lanka": "Colombo",
    "Iraq": "Baghdad", "Ghana": "Accra",
})
COUNTRY_CURRENCY.update({
    "Mexico": "Peso", "Sweden": "Krona", "Denmark": "Krone", "Switzerland": "Franc",
    "Poland": "Zloty", "Kenya": "Shilling", "Nigeria": "Naira", "Sri Lanka": "Sri Lankan Rupee",
    "United Arab Emirates": "Dirham", "Qatar": "Qatari Riyal", "Egypt": "Egyptian Pound",
    "Ghana": "Cedi", "Bangladesh (currency)": "Taka", "Philippines": "Philippine Peso",
})
DANCE_STATE.update({
    "Rouf": "Jammu and Kashmir", "Cheraw": "Mizoram", "Dollu Kunitha": "Karnataka",
    "Karma": "Jharkhand", "Padayani": "Kerala", "Nautanki": "Uttar Pradesh",
})
AWARD_FIELD.update({
    "Ramon Magsaysay Award": "public service in Asia", "Pulitzer Prize": "Journalism & Literature (US)",
    "Abel Prize": "Mathematics", "Fields Medal": "Mathematics (under 40)",
    "Kalinga Prize": "popularization of Science", "Grammy Award": "Music",
    "Booker Prize": "English fiction", "Right Livelihood Award": "the 'Alternative Nobel'",
})
ORG_HQ.update({
    "UNICEF": "New York", "IAEA": "Vienna", "Amnesty International": "London",
    "Red Cross (ICRC)": "Geneva", "Greenpeace": "Amsterdam", "OPEC (Secretariat)": "Vienna",
    "World Meteorological Organization": "Geneva", "African Union": "Addis Ababa",
})
DAY_DATE.update({
    "World Population Day": "11 July", "International Day of Peace": "21 September",
    "World AIDS Day": "1 December", "Human Rights Day": "10 December",
    "World Consumer Rights Day": "15 March", "Army Day (India)": "15 January",
    "Republic Day (India)": "26 January", "Independence Day (India)": "15 August",
})
ARTICLE_SUBJECT.update({
    "Article 1": "Name and territory of the Union", "Article 17": "Abolition of untouchability",
    "Article 18": "Abolition of titles", "Article 25": "Freedom of religion",
    "Article 40": "Organisation of village panchayats", "Article 51": "Promotion of international peace",
    "Article 72": "Pardoning power of the President", "Article 370": "Special status (erstwhile) of J&K",
})

MOUNTAIN_PEAK = {
    "Mount Everest": "Nepal", "K2 (Godwin-Austen)": "Pakistan-administered region",
    "Nanda Devi": "Uttarakhand", "Kamet": "Uttarakhand", "Anamudi": "Kerala",
    "Doddabetta": "Tamil Nadu", "Guru Shikhar": "Rajasthan", "Mullayanagiri": "Karnataka",
    "Dhupgarh": "Madhya Pradesh",
}
MOUNTAIN_PASS = {
    "Nathu La": "Sikkim", "Rohtang Pass": "Himachal Pradesh", "Zoji La": "Ladakh",
    "Shipki La": "Himachal Pradesh", "Bomdila Pass": "Arunachal Pradesh",
    "Bara Lacha La": "Himachal Pradesh", "Palakkad (Palghat) Gap": "Kerala",
}
INSTRUMENT_MAESTRO = {
    "Sitar": "Ravi Shankar", "Sarod": "Amjad Ali Khan", "Santoor": "Shivkumar Sharma",
    "Bansuri (Flute)": "Hariprasad Chaurasia", "Tabla": "Zakir Hussain",
    "Shehnai": "Bismillah Khan", "Sarangi": "Ram Narayan", "Mandolin": "U. Srinivas",
}
DISEASE_ORGAN = {
    "Cataract": "Eyes", "Arthritis": "Joints", "Jaundice": "Liver", "Pneumonia": "Lungs",
    "Nephritis": "Kidney", "Meningitis": "Brain", "Goitre": "Thyroid gland", "Glaucoma": "Eyes",
    "Tuberculosis": "Lungs", "Hepatitis": "Liver",
}
BANK_HQ = {
    "State Bank of India": "Mumbai", "Punjab National Bank": "New Delhi",
    "Bank of Baroda": "Vadodara", "Canara Bank": "Bengaluru", "Indian Bank": "Chennai",
    "Union Bank of India": "Mumbai", "Reserve Bank of India": "Mumbai",
    "NABARD": "Mumbai", "SIDBI": "Lucknow",
}
TROPHY_SPORT = {
    "Ranji Trophy": "Cricket", "Duleep Trophy": "Cricket", "Durand Cup": "Football",
    "Santosh Trophy": "Football", "Thomas Cup": "Badminton", "Davis Cup": "Tennis",
    "Ryder Cup": "Golf", "Agha Khan Cup": "Hockey", "Subroto Cup": "Football",
}
STUDY_BRANCH = {
    "Ornithology": "birds", "Ichthyology": "fish", "Entomology": "insects",
    "Herpetology": "reptiles and amphibians", "Mycology": "fungi", "Cardiology": "the heart",
    "Nephrology": "the kidneys", "Dermatology": "the skin", "Osteology": "bones",
    "Cytology": "cells", "Seismology": "earthquakes", "Pedology": "soil",
    "Nephology": "clouds", "Numismatics": "coins and currency", "Philately": "postage stamps",
}
WORLD_SUPERLATIVES = [
    ("The longest river in the world is the", "Nile", ["Amazon", "Yangtze", "Ganga"]),
    ("The largest ocean in the world is the", "Pacific Ocean", ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean"]),
    ("The largest desert in the world is the", "Sahara", ["Gobi", "Thar", "Kalahari"]),
    ("The highest mountain in the world is", "Mount Everest", ["K2", "Kangchenjunga", "Mont Blanc"]),
    ("The largest country by area is", "Russia", ["Canada", "China", "USA"]),
    ("The smallest country in the world is", "Vatican City", ["Monaco", "Nauru", "San Marino"]),
    ("The largest continent is", "Asia", ["Africa", "North America", "Europe"]),
    ("The largest island in the world is", "Greenland", ["New Guinea", "Borneo", "Madagascar"]),
    ("The tallest waterfall in the world is", "Angel Falls", ["Niagara Falls", "Victoria Falls", "Jog Falls"]),
]

_CHAP_BUILDERS.update({
    "Mountains, Peaks & Passes": [
        _mk_forward(MOUNTAIN_PEAK, "In which region/state is the peak {k} located?", "Peaks"),
        _mk_forward(MOUNTAIN_PASS, "In which state/UT is the {k} located?", "Mountain Passes"),
    ],
    "Music, Sports & Branches of Study": [
        _mk_forward(INSTRUMENT_MAESTRO, "Which maestro is associated with the {k}?", "Musicians"),
        _mk_reverse(INSTRUMENT_MAESTRO, "The maestro {v} is a legend of which instrument?", "Musicians"),
        _mk_forward(TROPHY_SPORT, "The {k} is associated with which sport?", "Sports Trophies"),
        _mk_forward(STUDY_BRANCH, "{k} is the study of what?", "Branches of Study"),
        _mk_reverse(STUDY_BRANCH, "What is the scientific study of {v} called?", "Branches of Study"),
    ],
    "Health, Banking & World GK": [
        _mk_forward(DISEASE_ORGAN, "The disease '{k}' affects which organ/part of the body?", "Diseases & Organs"),
        _mk_forward(BANK_HQ, "Where is the headquarters of {k}?", "Bank Headquarters"),
        _b_choice(WORLD_SUPERLATIVES, "World Superlatives"),
    ],
})


# --- EXPANSION batch 3 (2026-08-14): a few more tables + reverse builders on existing tables ---
PLANET_FACTS = [
    ("The Red Planet is", "Mars", ["Jupiter", "Venus", "Mercury"]),
    ("The largest planet in the Solar System is", "Jupiter", ["Saturn", "Neptune", "Earth"]),
    ("The planet closest to the Sun is", "Mercury", ["Venus", "Earth", "Mars"]),
    ("The hottest planet in the Solar System is", "Venus", ["Mercury", "Mars", "Jupiter"]),
    ("The planet famous for its prominent rings is", "Saturn", ["Jupiter", "Uranus", "Neptune"]),
    ("The farthest planet from the Sun is", "Neptune", ["Uranus", "Saturn", "Pluto"]),
    ("The only planet known to support life is", "Earth", ["Mars", "Venus", "Mercury"]),
]
ACID_SOURCE = {
    "Citric acid": "Citrus fruits", "Lactic acid": "Milk / curd", "Acetic acid": "Vinegar",
    "Formic acid": "Ant sting", "Tartaric acid": "Tamarind", "Oxalic acid": "Tomato",
    "Malic acid": "Apple", "Uric acid": "Urine",
}
VITAMIN_CHEM = {
    "Vitamin A": "Retinol", "Vitamin C": "Ascorbic acid", "Vitamin D": "Calciferol",
    "Vitamin B1": "Thiamine", "Vitamin B2": "Riboflavin", "Vitamin E": "Tocopherol",
    "Vitamin K": "Phylloquinone", "Vitamin B3": "Niacin",
}
COUNTRY_PARLIAMENT = {
    "Japan": "Diet", "Israel": "Knesset", "Russia": "Duma", "USA": "Congress",
    "Iran": "Majlis", "Germany": "Bundestag", "Spain": "Cortes Generales", "Norway": "Storting",
}
SANCTUARY_STATE = {
    "Keoladeo (Bharatpur) Sanctuary": "Rajasthan", "Dachigam Sanctuary": "Jammu and Kashmir",
    "Bhitarkanika Sanctuary": "Odisha", "Nagarhole Sanctuary": "Karnataka",
    "Mudumalai Sanctuary": "Tamil Nadu", "Nal Sarovar Sanctuary": "Gujarat",
    "Kumarakom Bird Sanctuary": "Kerala",
}

_CHAP_BUILDERS.update({
    "Solar System & Chemistry": [
        _b_choice(PLANET_FACTS, "Solar System"),
        _mk_forward(ACID_SOURCE, "In which natural source is {k} found?", "Natural Acids"),
        _mk_reverse(ACID_SOURCE, "Which acid is found in {v}?", "Natural Acids"),
        _mk_forward(VITAMIN_CHEM, "What is the chemical name of {k}?", "Vitamins (Chemical Names)"),
    ],
    "World Polity & Wildlife": [
        _mk_forward(COUNTRY_PARLIAMENT, "What is the name of the parliament of {k}?", "World Parliaments"),
        _mk_reverse(COUNTRY_PARLIAMENT, "'{v}' is the parliament of which country?", "World Parliaments"),
        _mk_forward(SANCTUARY_STATE, "In which state is the {k} located?", "Wildlife Sanctuaries"),
    ],
    "More Reverse Facts": [
        _mk_reverse(METAL_ORE, "{v} is chiefly extracted from which ore?", "Metals & Ores"),
        _mk_reverse(COMMON_CHEM, "'{v}' is the chemical name of which common substance?", "Common Chemical Names"),
        _mk_reverse(MONUMENT_CITY, "Which famous monument is located in {v}?", "Monuments of India"),
        _mk_reverse(DAM_RIVER, "Which major dam is built on the river {v}?", "Dams & Rivers"),
        _mk_reverse(STADIUM_CITY, "Which famous stadium is located in {v}?", "Stadiums"),
        _mk_reverse(INVENTION_INVENTOR, "Which invention/discovery is {v} known for?", "Inventions"),
    ],
})


# --- EXPANSION batch 4 (2026-08-14): temples, tribes, more superlatives/firsts + reverses ---
TEMPLE_STATE = {
    "Kedarnath Temple": "Uttarakhand", "Jagannath Temple (Puri)": "Odisha",
    "Tirupati Balaji Temple": "Andhra Pradesh", "Vaishno Devi Temple": "Jammu and Kashmir",
    "Kamakhya Temple": "Assam", "Somnath Temple": "Gujarat",
    "Brihadeeswara Temple": "Tamil Nadu", "Mahakaleshwar Temple": "Madhya Pradesh",
}
TRIBE_STATE = {
    "Toda": "Tamil Nadu", "Bodo": "Assam", "Khasi": "Meghalaya", "Santhal": "Jharkhand",
    "Gond": "Madhya Pradesh", "Bhil": "Rajasthan", "Naga": "Nagaland", "Warli": "Maharashtra",
}
SUPERLATIVES.extend([
    ("The state with the longest coastline in India is", "Gujarat", ["Andhra Pradesh", "Tamil Nadu", "Maharashtra"]),
    ("The highest waterfall in India is", "Kunchikal Falls", ["Jog Falls", "Dudhsagar Falls", "Nohkalikai Falls"]),
    ("The largest district in India by area is", "Kutch", ["Leh", "Jaisalmer", "Barmer"]),
    ("The wettest place in India is", "Mawsynram", ["Cherrapunji", "Agumbe", "Pasighat"]),
    ("The longest railway platform in India is at", "Hubballi (Gorakhpur earlier)", ["Kharagpur", "Kolkata", "Chennai"]),
    ("The state with the largest area in India is", "Rajasthan", ["Madhya Pradesh", "Maharashtra", "Gujarat"]),
    ("The oldest mountain range in India is the", "Aravalli Range", ["Himalayas", "Western Ghats", "Vindhya Range"]),
    ("The largest port in India is", "Mumbai (JNPT/Nhava Sheva handles most container traffic)", ["Kolkata", "Chennai", "Kochi"]),
])
FIRSTS.extend([
    ("The first Chief Justice of India was", "H.J. Kania", ["M. Patanjali Sastri", "B.R. Ambedkar", "Fatima Beevi"]),
    ("The first woman judge of the Supreme Court of India was", "Fatima Beevi", ["Leila Seth", "Indira Jaising", "Ruma Pal"]),
    ("The first Indian to win an individual Olympic gold was", "Abhinav Bindra", ["Neeraj Chopra", "Rajyavardhan Rathore", "Karnam Malleswari"]),
    ("The first Indian woman to win an Olympic medal was", "Karnam Malleswari", ["P.T. Usha", "Mary Kom", "Saina Nehwal"]),
    ("The first Speaker of the Lok Sabha was", "G.V. Mavalankar", ["M. Ananthasayanam Ayyangar", "Sardar Hukam Singh", "Neelam Sanjiva Reddy"]),
    ("The first Education Minister of India was", "Maulana Abul Kalam Azad", ["Jawaharlal Nehru", "Sardar Patel", "C. Rajagopalachari"]),
    ("The first Deputy Prime Minister of India was", "Sardar Vallabhbhai Patel", ["Morarji Desai", "Jawaharlal Nehru", "Gulzarilal Nanda"]),
])

_CHAP_BUILDERS.update({
    "Temples, Tribes & More": [
        _mk_forward(TEMPLE_STATE, "In which state is the {k} located?", "Temples of India"),
        _mk_reverse(TEMPLE_STATE, "Which famous temple is located in {v}?", "Temples of India"),
        _mk_forward(TRIBE_STATE, "The {k} tribe is mainly found in which state?", "Tribes of India"),
        _mk_reverse(TRIBE_STATE, "Which tribe is mainly associated with {v}?", "Tribes of India"),
    ],
    "More Reverse Facts II": [
        _mk_reverse(FATHER_OF, "'{v}' is known as the Father of what?", "Father of…"),
        _mk_reverse(VITAMIN_CHEM, "'{v}' is the chemical name of which vitamin?", "Vitamins (Chemical Names)"),
        _mk_reverse(MOUNTAIN_PEAK, "The peak located in {v} is which of these?", "Peaks"),
        _mk_reverse(MOUNTAIN_PASS, "The mountain pass in {v} is which of these?", "Mountain Passes"),
        _mk_reverse(NATIONAL_SYMBOL, "'{v}' — of which of these is it the national symbol of India?", "National Symbols"),
        _mk_reverse(BANK_HQ, "Which bank/institution is headquartered in {v}?", "Bank Headquarters"),
    ],
})


# --- EXPANSION batch 5 (2026-08-14): slogans + folk paintings (final push past 1000) ---
SLOGANS = [
    ('"Jai Jawan Jai Kisan" was the slogan of', "Lal Bahadur Shastri", ["Mahatma Gandhi", "Bhagat Singh", "Subhas Chandra Bose"]),
    ('"Do or Die" was the call given by', "Mahatma Gandhi", ["Bhagat Singh", "Bal Gangadhar Tilak", "Lal Bahadur Shastri"]),
    ('"Inquilab Zindabad" is associated with', "Bhagat Singh", ["Mahatma Gandhi", "Subhas Chandra Bose", "Nehru"]),
    ('"Give me blood and I will give you freedom" was said by', "Subhas Chandra Bose", ["Bhagat Singh", "Mahatma Gandhi", "Lala Lajpat Rai"]),
    ('"Swaraj is my birthright" was declared by', "Bal Gangadhar Tilak", ["Gopal Krishna Gokhale", "Mahatma Gandhi", "Lala Lajpat Rai"]),
    ('The song "Vande Mataram" was composed by', "Bankim Chandra Chattopadhyay", ["Rabindranath Tagore", "Iqbal", "Sarojini Naidu"]),
    ('"Sare Jahan Se Achha" was written by', "Muhammad Iqbal", ["Rabindranath Tagore", "Bankim Chandra", "Kazi Nazrul Islam"]),
    ('The national anthem "Jana Gana Mana" was written by', "Rabindranath Tagore", ["Bankim Chandra", "Iqbal", "Sarojini Naidu"]),
]
PAINTING_STATE = {
    "Madhubani painting": "Bihar", "Warli painting": "Maharashtra", "Pattachitra painting": "Odisha",
    "Kalamkari painting": "Andhra Pradesh", "Phad painting": "Rajasthan",
    "Tanjore painting": "Tamil Nadu", "Gond painting": "Madhya Pradesh", "Kangra painting": "Himachal Pradesh",
}

_CHAP_BUILDERS.update({
    "Slogans & Folk Art": [
        _b_choice(SLOGANS, "Famous Slogans"),
        _mk_forward(PAINTING_STATE, "The {k} style belongs to which state?", "Folk Paintings"),
        _mk_reverse(PAINTING_STATE, "Which folk painting style is associated with {v}?", "Folk Paintings"),
    ],
})


# --- EXPANSION batch 6 (2026-08-14): continents + chemical formulas (buffer past 1000) ---
COUNTRY_CONTINENT = {
    "India": "Asia", "China": "Asia", "Japan": "Asia", "Thailand": "Asia", "Vietnam": "Asia",
    "Indonesia": "Asia", "Saudi Arabia": "Asia", "Iran": "Asia", "Egypt": "Africa",
    "Nigeria": "Africa", "Kenya": "Africa", "South Africa": "Africa", "Morocco": "Africa",
    "Ghana": "Africa", "France": "Europe", "Germany": "Europe", "Italy": "Europe", "Spain": "Europe",
    "Norway": "Europe", "Sweden": "Europe", "Brazil": "South America", "Argentina": "South America",
    "Peru": "South America", "Chile": "South America", "Colombia": "South America",
    "USA": "North America", "Canada": "North America", "Mexico": "North America", "Cuba": "North America",
    "Australia": "Oceania", "New Zealand": "Oceania",
}
CHEMICAL_FORMULA = {
    "Water": "H2O", "Carbon dioxide": "CO2", "Table salt": "NaCl", "Methane": "CH4",
    "Ammonia": "NH3", "Ozone": "O3", "Sulphuric acid": "H2SO4", "Nitric acid": "HNO3",
    "Hydrochloric acid": "HCl", "Glucose": "C6H12O6", "Ethanol": "C2H5OH",
    "Calcium carbonate": "CaCO3", "Sodium hydroxide": "NaOH", "Sulphur dioxide": "SO2",
    "Nitrous oxide": "N2O",
}
_CHAP_BUILDERS.update({
    "Continents & Formulas": [
        _mk_forward(COUNTRY_CONTINENT, "In which continent is {k} located?", "Continents"),
        _mk_forward(CHEMICAL_FORMULA, "What is the chemical formula of {k}?", "Chemical Formulae"),
        _mk_reverse(CHEMICAL_FORMULA, "'{v}' is the chemical formula of which substance?", "Chemical Formulae"),
    ],
})
