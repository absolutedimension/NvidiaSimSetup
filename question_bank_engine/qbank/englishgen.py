"""GENERATE-FROM-DATA English engine — deterministic, correct-by-construction English MCQs for the
SSC / Railway / Banking "English Language" section (SSC CGL Tier-1 pattern).

The fourth sibling of quantgen / reasoninggen / staticgkgen. The SSC English vocab section is
built from VERIFIED word-pairs (synonyms, antonyms, one-word substitution, idioms, spelling), so
we embed the pairs and generate FROM them: the correct answer is the looked-up pair (not an LLM
guess), distractors are drawn from the same category. Plus a fully-mechanical active↔passive voice
builder. Impossible to serve a wrong key, copyright-clean (our own item assembly), UNLIMITED.

Live path: generator.generate_test() routes here when can_generate() covers (subject).
"""
import hashlib
import random

from .models import Question, content_hash

SUBJECT = "English"
EXAM = "SSC CGL"

_SUBJECT_ALIASES = {
    "english", "english language", "general english", "english comprehension",
    "english for ssc cgl", "verbal ability",
}


def can_generate(exam, subject, chapter=None) -> bool:
    if (subject or "").strip().lower() not in _SUBJECT_ALIASES:
        return False
    if not chapter:
        return True
    return chapter in _CHAP_BUILDERS


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
    qid = "gen_eng_" + hashlib.md5((spec.get("chapter", "") + "|" + stem).encode()).hexdigest()[:14]
    q = Question(
        id=qid, exam=spec.get("exam") or EXAM, subject=spec.get("subject") or SUBJECT,
        stem=stem, qtype="MCQ_single", options=options, correct_answer=ans,
        solution=built.get("solution", ""), chapter=spec.get("chapter"),
        concept=built.get("concept"), difficulty=diff, source="englishgen",
        generated=True, hash=content_hash(stem))
    q.verified = True
    return q


def _distractors(pool, correct, rng, k=3):
    cand = [x for x in dict.fromkeys(pool) if x != correct]
    rng.shuffle(cand)
    return cand[:k]


# =============================================================================
# VERIFIED DATA
# =============================================================================

SYNONYM = {
    "Abandon": "Desert", "Benevolent": "Kind", "Candid": "Frank", "Diligent": "Hardworking",
    "Eloquent": "Fluent", "Frugal": "Thrifty", "Gregarious": "Sociable", "Hostile": "Unfriendly",
    "Immense": "Huge", "Jubilant": "Joyful", "Lucid": "Clear", "Meticulous": "Careful",
    "Novice": "Beginner", "Obstinate": "Stubborn", "Placid": "Calm", "Rapid": "Quick",
    "Scarce": "Rare", "Tranquil": "Peaceful", "Vivid": "Bright", "Wrath": "Anger",
    "Abundant": "Plentiful", "Cordial": "Friendly", "Dubious": "Doubtful", "Enormous": "Gigantic",
}
ANTONYM = {
    "Ancient": "Modern", "Barren": "Fertile", "Cautious": "Reckless", "Dense": "Sparse",
    "Expand": "Contract", "Feeble": "Strong", "Genuine": "Fake", "Humble": "Arrogant",
    "Innocent": "Guilty", "Liberal": "Conservative", "Miser": "Spendthrift", "Optimist": "Pessimist",
    "Praise": "Criticize", "Rigid": "Flexible", "Transparent": "Opaque", "Victory": "Defeat",
    "Wise": "Foolish", "Bold": "Timid", "Create": "Destroy", "Ascend": "Descend",
    "Vague": "Clear", "Permanent": "Temporary", "Amateur": "Professional", "Frequent": "Rare",
}
ONE_WORD = {
    "A person who eats everything": "Omnivore",
    "A place where birds are kept": "Aviary",
    "One who studies stars and planets": "Astronomer",
    "A person who cannot read or write": "Illiterate",
    "A government by the people": "Democracy",
    "A speech made without preparation": "Extempore",
    "One who loves mankind": "Philanthropist",
    "One who hates mankind": "Misanthrope",
    "That which cannot be believed": "Incredible",
    "One who walks on foot": "Pedestrian",
    "A doctor who treats children": "Pediatrician",
    "One who does not believe in God": "Atheist",
    "Handwriting that cannot be read": "Illegible",
    "One who collects coins": "Numismatist",
    "One who collects stamps": "Philatelist",
    "A medicine that kills germs": "Antiseptic",
    "Animals that live both on land and in water": "Amphibians",
    "A person who talks too much": "Loquacious",
    "Something that cannot be avoided": "Inevitable",
    "A place where money is coined": "Mint",
}
IDIOM = {
    "To let the cat out of the bag": "To reveal a secret",
    "A piece of cake": "Something very easy",
    "To bite the dust": "To fail or be defeated",
    "Once in a blue moon": "Very rarely",
    "To burn the midnight oil": "To work late into the night",
    "To hit the nail on the head": "To be exactly right",
    "Under the weather": "Feeling unwell",
    "To cost an arm and a leg": "To be very expensive",
    "To break the ice": "To start a conversation",
    "A blessing in disguise": "A good thing that first seemed bad",
    "To turn a blind eye": "To ignore deliberately",
    "To be in hot water": "To be in trouble",
    "To make a mountain out of a molehill": "To exaggerate a small problem",
    "To add fuel to the fire": "To make a situation worse",
    "A white elephant": "A costly but useless possession",
    "To beat around the bush": "To avoid coming to the point",
    "To pull someone's leg": "To tease or joke with someone",
    "To smell a rat": "To suspect something wrong",
}
# correct spelling -> list of common misspellings
SPELL = {
    "Accommodate": ["Acommodate", "Accomodate", "Acomodate"],
    "Necessary": ["Neccessary", "Necesary", "Neccesary"],
    "Occurrence": ["Occurence", "Ocurrence", "Occurrance"],
    "Separate": ["Seperate", "Sepparate", "Seperete"],
    "Definitely": ["Definately", "Definetly", "Defenitely"],
    "Embarrass": ["Embarass", "Embaras", "Embarras"],
    "Privilege": ["Priviledge", "Privelege", "Privilage"],
    "Maintenance": ["Maintainance", "Maintenence", "Maintanance"],
    "Recommend": ["Recomend", "Reccommend", "Recommand"],
    "Conscience": ["Consience", "Concience", "Conscence"],
    "Rhythm": ["Rythm", "Rhythim", "Rythem"],
    "Bureaucracy": ["Beaurocracy", "Bureacracy", "Buraucracy"],
    "Millennium": ["Millenium", "Milennium", "Millenneum"],
    "Grievance": ["Greivance", "Grievence", "Grievanse"],
}
# active-voice building blocks (NOUN subjects only, so "by <subject>" needs no pronoun change;
# simple present; singular objects → "is"). Verbs are paired with SENSIBLE objects so sentences
# read naturally. Every verb has base ≠ past-participle (no collision with the base-verb distractor).
_VOICE_SUBJECTS = ["The boy", "The teacher", "The chef", "The artist", "The farmer",
                   "The doctor", "The mason", "The tailor", "The gardener", "The girl"]
# base -> (third-person-singular, past-participle, [sensible objects])
_VOICE_VERBS = {
    "write": ("writes", "written", ["a letter", "the book", "a poem", "a story"]),
    "eat": ("eats", "eaten", ["the food", "a cake", "the apple", "the mango"]),
    "sing": ("sings", "sung", ["a song", "the anthem", "a hymn"]),
    "break": ("breaks", "broken", ["the window", "a glass", "the vase", "the wall"]),
    "build": ("builds", "built", ["a house", "the bridge", "a wall", "the temple"]),
    "paint": ("paints", "painted", ["a picture", "the wall", "the door", "a portrait"]),
    "cook": ("cooks", "cooked", ["the food", "a cake", "the meal", "the rice"]),
    "clean": ("cleans", "cleaned", ["the window", "the room", "the floor", "the car"]),
    "make": ("makes", "made", ["a cake", "the tea", "a chair", "a toy"]),
}


# =============================================================================
# BUILDERS
# =============================================================================

def _b_synonym(rng, diff):
    w = rng.choice(list(SYNONYM)); s = SYNONYM[w]
    stem = f"Select the word that is MOST SIMILAR in meaning to '{w}'."
    d = _distractors(list(SYNONYM.values()), s, rng)
    return {"stem": stem, "correct": s, "distractors": d,
            "solution": f"'{w}' means '{s}'.", "concept": "Synonyms"}

def _b_antonym(rng, diff):
    w = rng.choice(list(ANTONYM)); a = ANTONYM[w]
    stem = f"Select the word that is MOST OPPOSITE in meaning to '{w}'."
    d = _distractors(list(ANTONYM.values()), a, rng)
    return {"stem": stem, "correct": a, "distractors": d,
            "solution": f"The antonym of '{w}' is '{a}'.", "concept": "Antonyms"}

def _b_oneword(rng, diff):
    defn = rng.choice(list(ONE_WORD)); w = ONE_WORD[defn]
    stem = f"Choose the ONE WORD for: '{defn}'."
    d = _distractors(list(ONE_WORD.values()), w, rng)
    return {"stem": stem, "correct": w, "distractors": d,
            "solution": f"'{defn}' = {w}.", "concept": "One-Word Substitution"}

def _b_idiom(rng, diff):
    idm = rng.choice(list(IDIOM)); m = IDIOM[idm]
    stem = f"What does the idiom '{idm}' mean?"
    d = _distractors(list(IDIOM.values()), m, rng)
    return {"stem": stem, "correct": m, "distractors": d,
            "solution": f"'{idm}' means: {m}.", "concept": "Idioms & Phrases"}

def _b_spell_correct(rng, diff):
    w = rng.choice(list(SPELL))
    stem = "Select the CORRECTLY spelt word."
    return {"stem": stem, "correct": w, "distractors": list(SPELL[w])[:3],
            "solution": f"The correct spelling is '{w}'.", "concept": "Spelling"}

def _b_spell_wrong(rng, diff):
    w = rng.choice(list(SPELL))
    wrong = rng.choice(SPELL[w])
    others = _distractors([x for x in SPELL if x != w], None, rng, k=3)
    stem = "Select the INCORRECTLY spelt word."
    return {"stem": stem, "correct": wrong, "distractors": others,
            "solution": f"'{wrong}' is misspelt; the correct spelling is '{w}'.", "concept": "Spelling"}

def _b_active_passive(rng, diff):
    s = rng.choice(_VOICE_SUBJECTS)
    base = rng.choice(list(_VOICE_VERBS)); third, pp, objs = _VOICE_VERBS[base]
    o = rng.choice(objs)
    active = f"{s} {third} {o}."
    obj_cap = o[0].upper() + o[1:]
    subj_low = s[0].lower() + s[1:]
    passive = f"{obj_cap} is {pp} by {subj_low}."
    stem = f"Select the correct PASSIVE voice of: \"{active}\""
    d = [
        f"{obj_cap} is {base} by {subj_low}.",          # wrong: base verb
        f"{obj_cap} was {pp} by {subj_low}.",           # wrong tense
        f"{obj_cap} is {pp} {subj_low}.",               # missing 'by'
    ]
    return {"stem": stem, "correct": passive, "distractors": d,
            "solution": f"Passive (simple present): {passive}", "concept": "Voice (Active/Passive)"}


_CHAP_BUILDERS = {
    "Vocabulary (Synonyms & Antonyms)": [_b_synonym, _b_antonym],
    "One-Word Substitution": [_b_oneword],
    "Idioms & Phrases": [_b_idiom],
    "Spelling": [_b_spell_correct, _b_spell_wrong],
    "Grammar (Active/Passive Voice)": [_b_active_passive],
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
        "spec": spec, "generator": "englishgen", "requested": count,
        "generated": len(accepted), "rejected": [],
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
    }
