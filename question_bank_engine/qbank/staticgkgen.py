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
    """Factory: 'What is the <fact> of <key>?' correct=value, distractors=other values."""
    def build(rng, diff):
        k = rng.choice(list(table))
        v = table[k]
        stem = q_tmpl.format(k=k)
        d = _distractors(list(table.values()), v, rng)
        return {"stem": stem, "correct": f"{v}{unit}",
                "distractors": [f"{x}{unit}" for x in d],
                "solution": stem + f" {v}{unit}.", "concept": concept}
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
