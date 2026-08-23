"""The ASKING STYLES the commission actually uses, over the fact tables we already own.

Measured, not assumed. Classifying 552 official General Studies questions from the extracted BSSC
papers by the SHAPE of their asking gives:

    sentence-completion   36.1%      ("Full form of ATM is", "Surti, Murrah ... are breeds of")
    direct-wh             16.7%      ("Who appoints the Finance Commission ?")
    embedded-which        14.3%      ("Zika Virus attacks which part of human body ?")
    word-problem          13.8%
    which-of-following     9.2%
    negative-select        5.1%      ("Find the odd one among the following")
    match-list             2.5%
    fill-in-blank          1.3%
    statement-list         0.2%

and the paper we were shipping ran match-list at 44% and statement-list at 30% — 74% of the
section in two styles that together are 2.7% of the real exam, and ZERO of the commission's
largest style. To a reader that is one question asked fifty times, which is exactly what the
institute's owner said when he read it.

How it happened is written down in build_onestep_paper.generate_static_gk: direct recall was
judged "difficulty-1" and suppressed in favour of statement and match forms, because those are how
BPSC and UPSC raise difficulty. They are. BSSC Inter Level is not that exam, and the reasoning
confused two separate dials —

    STYLE      is how the question is asked. It should match the exam being practised for.
    DIFFICULTY is how hard the work is. It comes from which FACT is chosen and how close the
               distractors sit, and it is available in every style.

So this module renders the SAME verified (key, value) tables in the commission's own styles, and
gets its difficulty from the distractors rather than from the form. Nothing new is asserted: the
answer is always the table's own value, and every option is another value from the same table.

The safety rule from staticgk_forms carries over unchanged and matters MORE here, because two of
these styles run the table BACKWARDS. A reverse question ("which state has Chandigarh as its
capital?") is only sound when the value belongs to exactly one key — Chandigarh is the capital of
both Punjab and Haryana, and four states share a classical dance. `_reversible` is that gate, and
a table that fails it simply never produces a reverse question.
"""
import re

from . import staticgk_hi as HI

# Per table: how to ASK for the value, in each of the commission's styles.
#   wh    - direct question ending in '?'
#   comp  - an INCOMPLETE SENTENCE the options finish. No question mark. The commission's most
#           common style by a wide margin, and the one we generated none of.
#   blank - the same fact with the answer blanked out mid-sentence
#   rev   - runs the table backwards: the value is given and the KEY is the answer. Gated.
# {k} is the table's key, {v} its value.
ASK = {
    "STATE_CAPITAL": {
        "wh": ("What is the capital of {k}?", "{k} की राजधानी क्या है?"),
        "comp": ("The capital of {k} is", "{k} की राजधानी है —"),
        "blank": ("______ is the capital of {k}.", "______ {k} की राजधानी है।"),
        "rev": ("{v} is the capital of which state?", "{v} किस राज्य की राजधानी है?"),
    },
    "DANCE_STATE": {
        "wh": ("Where does the dance form {k} come from?", "{k} नृत्य कहाँ का है?"),
        "comp": ("{k} is a dance form of", "{k} नृत्य है —"),
        "blank": ("{k} is a dance form of ______.", "{k} ______ का नृत्य है।"),
    },
    "RIVER_ORIGIN": {
        "wh": ("Where does the river {k} originate?", "{k} नदी का उद्गम स्थल कहाँ है?"),
        "comp": ("The river {k} originates at", "{k} नदी का उद्गम स्थल है —"),
        "blank": ("The river {k} originates at ______.", "{k} नदी का उद्गम स्थल ______ है।"),
        "rev": ("Which river originates at {v}?", "{v} से कौन-सी नदी निकलती है?"),
    },
    "ARTICLE_SUBJECT": {
        "wh": ("What does Article {k} of the Constitution deal with?",
               "संविधान का अनुच्छेद {k} किससे संबंधित है?"),
        "comp": ("Article {k} of the Constitution deals with",
                 "संविधान का अनुच्छेद {k} संबंधित है —"),
        "blank": ("Article {k} of the Constitution deals with ______.",
                  "संविधान का अनुच्छेद {k} ______ से संबंधित है।"),
        "rev": ("Which Article of the Constitution deals with {v}?",
                "संविधान का कौन-सा अनुच्छेद {v} से संबंधित है?"),
    },
    "PANCHAYAT_ARTICLE": {
        "wh": ("What does Article {k} of the Constitution deal with?",
               "संविधान का अनुच्छेद {k} किससे संबंधित है?"),
        "comp": ("Article {k} of the Constitution deals with",
                 "संविधान का अनुच्छेद {k} संबंधित है —"),
        "blank": ("Article {k} of the Constitution deals with ______.",
                  "संविधान का अनुच्छेद {k} ______ से संबंधित है।"),
        "rev": ("Which Article of the Constitution deals with {v}?",
                "संविधान का कौन-सा अनुच्छेद {v} से संबंधित है?"),
    },
    "AMENDMENT_DID": {
        "comp": ("The {k} Constitutional Amendment", "{k} संविधान संशोधन ने —"),
        "rev": ("Which Constitutional Amendment {v}?", "किस संविधान संशोधन ने {v}?"),
    },
    "BIHAR_SITE_DISTRICT": {
        "wh": ("In which district of Bihar is {k} located?",
               "{k} बिहार के किस जिले में स्थित है?"),
        "comp": ("{k} is located in the Bihar district of", "{k} बिहार के जिस जिले में है, वह है —"),
        "blank": ("{k} is located in the ______ district of Bihar.",
                  "{k} बिहार के ______ जिले में स्थित है।"),
    },
    "BIHAR_GI_PRODUCT": {
        "wh": ("The GI-tagged product {k} belongs to which district of Bihar?",
               "जीआई-टैग उत्पाद {k} बिहार के किस जिले का है?"),
        "comp": ("The GI-tagged product {k} belongs to the Bihar district of",
                 "जीआई-टैग उत्पाद {k} बिहार के जिस जिले का है, वह है —"),
        "rev": ("Which GI-tagged product of Bihar belongs to {v} district?",
                "बिहार का कौन-सा जीआई-टैग उत्पाद {v} जिले का है?"),
    },
    "BIHAR_FREEDOM_ROLE": {
        "comp": ("In Bihar's national movement, {k} was",
                 "बिहार के राष्ट्रीय आंदोलन में {k} थे —"),
        # ⚠️ "कौन थे" is masculine. Every person in BIHAR_FREEDOM_ROLE today is male, so it is
        # correct; adding a woman to that table REQUIRES revisiting this line, exactly like
        # HI.sits() and possessive() elsewhere in this repo.
        "rev": ("Who was {v}?", "{v} कौन थे?"),
    },
    "BIHAR_FOLK_REGION": {
        "wh": ("{k} is a folk art form of which region of Bihar?",
               "{k} बिहार के किस क्षेत्र की लोक कला है?"),
        "comp": ("{k} is a folk art form of the Bihar region of",
                 "{k} बिहार के जिस क्षेत्र की लोक कला है, वह है —"),
    },
    # History. Their values are YEARS, which is why they matter for difficulty: `_near` compares
    # numbers, so "Which movement took place in 1930?" can be offered against 1929/1931/1932 and
    # reach difficulty 3. Every other history-shaped table (leader, target) has text values with no
    # closeness metric and tops out at 2 — the same wall capitals and dances hit.
    "MOVEMENT_YEAR": {
        "wh": ("In which year did the {k} take place?", "{k} किस वर्ष हुआ था?"),
        "comp": ("The {k} took place in the year", "{k} जिस वर्ष हुआ, वह है —"),
        # "EVENT", not "movement". MOVEMENT_YEAR holds the Battle of Plassey (1757) and the
        # Battle of Buxar (1764) alongside the satyagrahas, so "which MOVEMENT took place in 1757"
        # printed a factual error — a battle is not a movement. The templates were added without
        # reading the table's contents, which is what the review gates exist to catch.
        "rev": ("Which event took place in {v}?", "{v} में कौन-सी घटना हुई थी?"),
    },
    "FOUNDED_YEAR": {
        "wh": ("In which year was the {k} founded?", "{k} की स्थापना किस वर्ष हुई थी?"),
        "comp": ("The {k} was founded in the year", "{k} की स्थापना जिस वर्ष हुई, वह है —"),
    },
    "MOVEMENT_LEADER": {
        "wh": ("Who led the {k}?", "{k} का नेतृत्व किसने किया था?"),
        "comp": ("The {k} was led by", "{k} का नेतृत्व किया —"),
        "rev": ("Which movement was led by {v}?", "{v} ने किस आंदोलन का नेतृत्व किया था?"),
    },
    "MOVEMENT_AGAINST": {
        "wh": ("The {k} was directed against what?", "{k} किसके विरुद्ध था?"),
        "comp": ("The {k} was directed against", "{k} जिसके विरुद्ध था, वह है —"),
    },
    "BIHAR_FREEDOM": {
        "wh": ("In Bihar's freedom movement, what was {k}?",
               "बिहार के स्वतंत्रता आंदोलन में, {k} क्या था?"),
        "comp": ("In Bihar's freedom movement, {k} was",
                 "बिहार के स्वतंत्रता आंदोलन में, {k} था —"),
    },
    # आर्थिक परिदृश्य / पंचवर्षीय योजना.
    # "rev" is offered on both: plan periods and event years are distinct within their tables, so
    # running them backwards has exactly one answer — `_rev_ok` checks that per row anyway.
    "PLAN_PERIOD": {
        "wh": ("The {k} covered which period?", "{k} की अवधि क्या थी?"),
        "comp": ("The {k} ran from", "{k} चली —"),
        "blank": ("The {k} ran from ______.", "{k} ______ तक चली।"),
        "rev": ("Which Five-Year Plan ran from {v}?", "{v} तक कौन-सी पंचवर्षीय योजना चली?"),
    },
    "ECON_EVENT_YEAR": {
        "wh": ("In which year did the {k} take place?", "{k} किस वर्ष से संबंधित है?"),
        "comp": ("The {k} took place in", "{k} संबंधित है —"),
        "blank": ("The {k} took place in ______.", "{k} ______ से संबंधित है।"),
        "rev": ("Which of these took place in {v}?", "इनमें से क्या {v} में हुआ?"),
    },
    # भारतीय कृषि तथा प्राकृतिक संसाधन.
    "REVOLUTION_PRODUCT": {
        "wh": ("The {k} is associated with which product?", "{k} का संबंध किस उत्पाद से है?"),
        "comp": ("The {k} is associated with", "{k} का संबंध है —"),
        "blank": ("The {k} is associated with ______.", "{k} का संबंध ______ से है।"),
        "rev": ("Which revolution is associated with {v}?", "{v} से कौन-सी क्रांति संबंधित है?"),
    },
    "AGRI_INSTITUTE_CITY": {
        "wh": ("Where is the {k} located?", "{k} कहाँ स्थित है?"),
        "comp": ("The {k} is located at", "{k} स्थित है —"),
        "blank": ("The {k} is located at ______.", "{k} ______ में स्थित है।"),
        "rev": ("Which agricultural research institute is located at {v}?",
                "{v} में कौन-सा कृषि अनुसंधान संस्थान स्थित है?"),
    },
    # खेल-खिलाड़ी. NO "rev" on TROPHY_SPORT: several trophies share a sport, so "which trophy is
    # associated with cricket?" has more than one right answer among our own rows. `_rev_ok`
    # would catch it row by row, but the style is wrong for this table in principle, not by
    # accident, so it is simply not offered.
    "TROPHY_SPORT": {
        "wh": ("The {k} is associated with which sport?", "{k} का संबंध किस खेल से है?"),
        "comp": ("The {k} is associated with the sport of", "{k} का संबंध है —"),
        "blank": ("The {k} is associated with the sport of ______.", "{k} का संबंध ______ से है।"),
    },
    "STADIUM_CITY": {
        "wh": ("In which city is {k} located?", "{k} किस शहर में स्थित है?"),
        "comp": ("{k} is located in", "{k} स्थित है —"),
        "blank": ("{k} is located in ______.", "{k} ______ में स्थित है।"),
        "rev": ("Which stadium is located in {v}?", "{v} में कौन-सा स्टेडियम स्थित है?"),
    },
    "ELEMENT_SYMBOL": {
        "wh": ("What is the chemical symbol of {k}?", "{k} का रासायनिक प्रतीक क्या है?"),
        "comp": ("The chemical symbol of {k} is", "{k} का रासायनिक प्रतीक है —"),
        "rev": ("{v} is the chemical symbol of which element?",
                "{v} किस तत्व का रासायनिक प्रतीक है?"),
    },
    "ELEMENT_ATOMIC_NUMBER": {
        "wh": ("What is the atomic number of {k}?", "{k} का परमाणु क्रमांक क्या है?"),
        "comp": ("The atomic number of {k} is", "{k} का परमाणु क्रमांक है —"),
        "rev": ("Which element has the atomic number {v}?",
                "किस तत्व का परमाणु क्रमांक {v} है?"),
    },
    "COMPOUND_FORMULA": {
        "wh": ("What is the chemical formula of {k}?", "{k} का रासायनिक सूत्र क्या है?"),
        "comp": ("The chemical formula of {k} is", "{k} का रासायनिक सूत्र है —"),
        "rev": ("{v} is the chemical formula of which compound?",
                "{v} किस यौगिक का रासायनिक सूत्र है?"),
    },
}

STYLE_CONCEPT = {
    "comp": "Sentence Completion",
    "wh": "Direct Question",
    "blank": "Fill in the Blank",
    "rev": "Reverse Lookup",
    "odd": "Odd One Out (GK)",
}


def _hi(x):
    """Hindi if we have it, otherwise the token — numbers and symbols print the same either way."""
    return HI.hi(str(x)) or str(x)


def _alias(a, b):
    ha, hb = HI.hi(str(a)), HI.hi(str(b))
    return a == b or (ha is not None and ha == hb)


def _reversible(table, v):
    """True when exactly one key owns this value, so running the table backwards has ONE answer.

    Chandigarh is the capital of Punjab AND Haryana; several states share a classical dance. A
    reverse question over such a value has two correct answers and only one of them on the page.
    This is the same hazard staticgk_forms._false_value guards, and it bites harder here because
    the reverse direction is the ANSWER rather than a distractor.
    """
    return sum(1 for vv in table.values() if _alias(vv, v)) == 1


def _neutral(x):
    """Tokens that print identically in both scripts: article numbers, element symbols, formulae.

    NOT "any alphanumeric word". Written that way first, and it let "Karma" and "Nautanki" through
    a Hindi stem untranslated — "Karma नृत्य है —" on the page, Latin stranded inside Devanagari,
    which is a structural check this repo already runs and would have failed.
    """
    x = str(x)
    return bool(re.match(r"^\d+[A-Za-z]?$", x)          # 21A  368
                or re.match(r"^[A-Z][a-z]?$", x)        # Cu  H
                or re.match(r"^[A-Z0-9()]{1,12}$", x))  # H2SO4  CO(NH2)2


def _printable(x):
    return HI.hi(str(x)) is not None or _neutral(x)


def _bilingual(table):
    """Keys whose key AND value can both be printed in Hindi."""
    return [k for k, v in table.items() if _printable(k) and _printable(v)]


def _near(a, b):
    """How confusable two options are — smaller is closer. Numbers by distance, text by shared
    words. This is the ONLY difficulty dial these styles have, and it is a real one: 'Article 14'
    against 15, 16, 17 is a different question from 'Article 14' against 148, 324 and 50."""
    sa, sb = str(a), str(b)
    ma = re.match(r"^(\d+)([A-Z]*)$", sa)
    mb = re.match(r"^(\d+)([A-Z]*)$", sb)
    if ma and mb:
        # The SUFFIX has to count. Comparing the numeric prefix alone made every Panchayat article
        # (243B, 243C, 243D ... 243W) sit at distance 0 from every other, so `_tight` saw no spread
        # and refused to call ANY of them hard — a false negative on the most confusable option set
        # in the whole bank. Scaled so the article number still dominates: 243B/243C = 1,
        # 243B/243W = 21, 14/315 = 3010.
        n = abs(int(ma.group(1)) - int(mb.group(1))) * 10
        sfx = lambda g: ord(g[0]) if g else 0
        return n + abs(sfx(ma.group(2)) - sfx(mb.group(2)))
    wa = {w for w in re.findall(r"[a-z]{4,}", sa.lower())}
    wb = {w for w in re.findall(r"[a-z]{4,}", sb.lower())}
    if wa & wb:
        return 100 - 10 * len(wa & wb)
    # No shared words — which for PROPER NOUNS is almost always, and that is why capitals, rivers
    # and dances could never reach difficulty 3: every distractor scored an identical 100, `_tight`
    # saw no spread, and the question was called easy no matter which options it offered.
    #
    # For a proper noun, confusability IS lexical similarity. A candidate who half-remembers the
    # answer confuses Amaravati with Amarkantak, Itanagar with Imphal, Kathak with Kathakali — and
    # is untroubled by Panaji. Character similarity measures exactly that, and it is the same
    # principle as the numeric branch above: how easily could this be mistaken for the answer.
    import difflib
    ratio = difflib.SequenceMatcher(None, sa.lower(), sb.lower()).ratio()
    return 100 - int(60 * ratio)


def _options(pool, answer, rng, n=3, diff=2):
    """n distractors from the SAME table — same kind, never an alias of the answer, each printable
    in Hindi, and CHOSEN by how close they sit to the answer.

    Drawing from every value in the table pulled in ones whose key had been excluded for having no
    Hindi, so the option itself came out in English. And drawing at random made every question in
    these styles difficulty-1 by construction, which is precisely the objection that got the whole
    style suppressed in the first place. The style is not what makes a recall question easy — the
    distance between its options is.
    """
    cand = [v for v in dict.fromkeys(pool) if not _alias(v, answer) and _printable(v)]
    rng.shuffle(cand)
    if diff >= 3:
        cand.sort(key=lambda v: _near(v, answer))          # hardest: the confusable ones
    elif diff <= 1:
        cand.sort(key=lambda v: -_near(v, answer))         # easiest: obviously unrelated
    return cand[:n]


def _tight(chosen, answer, pool):
    """Did we actually manage to pick CONFUSABLE distractors for this answer?

    Two conditions, and the second is the one that matters. The chosen options must sit in the
    closest quartile of what was available — AND `_near` must discriminate between the candidates
    at all. Without that second test every capital-city question scores "tight", because all the
    distances are identical (no capital shares a word with another) and the closest quartile of a
    flat list is the whole list.

    This is the difference between a difficulty that is measured and one that is asserted.
    """
    dists = sorted(_near(v, answer) for v in pool)
    if len(dists) < 4 or dists[-1] == dists[0]:
        return False                       # the metric cannot tell these options apart
    # A real quantile. `len(dists)//4 - 1` collapses to index 0 on any pool below eight, so the
    # test became "closer than the single closest candidate" — unsatisfiable. Large tables were
    # unaffected (88 candidates -> index 21 either way) which is exactly why it survived: Articles
    # scored 89 of 89 hard while the 8-row Panchayat table scored 0, with distractors 243E/243D/243C
    # sitting 2, 3 and 4 away from 243G. The data was as confusable as it gets; the check could not
    # see it.
    q1 = dists[max(0, (len(dists) - 1) // 4)]
    mean = sum(_near(v, answer) for v in chosen) / max(1, len(chosen))
    return mean <= q1


def difficulty_of(style, chosen, answer, pool):
    """What this question actually demands — 1 easy, 2 medium, 3 hard.

    NOT the band the paper happened to be filling when it drew the question. That is how "The
    capital of Rajasthan is —", offered against Imphal, Hyderabad and Patna, came to print a
    कठिन / Hard badge: `_gs_row` stamped the loop variable. The owner is being asked to calibrate
    our difficulty against his judgement, so a decorative badge does not merely look wrong, it
    corrupts the one feedback loop that has ever worked here.

    Only two things genuinely vary in a lookup question, and both are checkable:
      · running the table BACKWARDS is more work than reading it forwards
      · options that sit close together force the candidate to actually know the fact
    A plain forward lookup with unrelated options is difficulty 1, and should say so.
    """
    d = 1
    if style == "rev":
        d += 1
    if _tight(chosen, answer, pool):
        d += 1
    return min(d, 3)


def build(tables, name, style, rng, diff=2):
    """One question over `tables[name]` in the given asking `style`, or None.

    Returns the same dict shape staticgk_forms' builders return, so the paper can consume it
    without a second code path: stem / stem_hi / correct / distractors / hi_opts / solution /
    solution_hi / concept / src.
    """
    table = tables.get(name)
    tmpl = (ASK.get(name) or {}).get(style)
    if not table or not tmpl:
        return None
    keys = _bilingual(table)
    if len(keys) < 4:
        return None
    en_t, hi_t = tmpl

    if style == "rev":
        # answer is the KEY, so the VALUE must identify it uniquely
        cand = [k for k in keys if _reversible(table, table[k])]
        if len(cand) < 4:
            return None
        k = rng.choice(cand)
        answer, pool = k, [kk for kk in keys]
        stem, stem_hi = en_t.format(k=k, v=table[k]), hi_t.format(k=_hi(k), v=_hi(table[k]))
        sol = f"{table[k]} belongs to {k}."
        sol_hi = f"{_hi(table[k])} — {_hi(k)}।"
    else:
        k = rng.choice(keys)
        answer, pool = table[k], list(table.values())
        stem, stem_hi = en_t.format(k=k, v=table[k]), hi_t.format(k=_hi(k), v=_hi(table[k]))
        sol = f"The answer for {k} is {answer}."
        sol_hi = f"{_hi(k)} का उत्तर {_hi(answer)} है।"

    d = _options(pool, answer, rng, diff=diff)
    if len(d) < 3:
        return None
    # The difficulty this question actually has, not the band that asked for it.
    cands = [v for v in dict.fromkeys(pool) if not _alias(v, answer) and _printable(v)]
    honest = difficulty_of(style, d, answer, cands)
    opts = [answer] + d
    return {"stem": stem, "stem_hi": stem_hi, "correct": str(answer),
            "distractors": [str(x) for x in d],
            "hi_opts": {str(o): _hi(o) for o in opts},
            "solution": sol, "solution_hi": sol_hi,
            # WHICH FACT this question is about, independent of how it is asked. Two styles over
            # the same row are two renderings of one question — a paper printed "The river Godavari
            # originates at" and "Where does the river Godavari originate?" four questions apart,
            # and gen_sig allowed both because their concepts differ. The caller dedups on this.
            "concept": STYLE_CONCEPT[style], "src": [name], "fact": f"{name}|{k}",
            "difficulty": honest}


def build_odd(tables, name, rng, diff=3):
    """'Find the odd one' — three options share a key, the fourth does not.

    5.1% of the real paper is a negative selection and we generated none of it. Built the safe way
    round: pick a key, take THREE values that genuinely belong to it... which a key->value table
    cannot give. So it runs the other way: three items that share the same VALUE, plus one that
    does not — "which of these is NOT a dance of Kerala".
    """
    table = tables.get(name)
    if not table:
        return None
    ask = (ASK.get(name) or {})
    if not ask:
        return None
    keys = _bilingual(table)
    groups = {}
    for k in keys:
        groups.setdefault(str(table[k]), []).append(k)
    big = [(v, ks) for v, ks in groups.items() if len(ks) >= 3]
    if not big:
        return None
    v, ks = rng.choice(big)
    same = rng.sample(ks, 3)
    others = [k for k in keys if not _alias(str(table[k]), v)]
    if not others:
        return None
    odd = rng.choice(others)
    label = {"DANCE_STATE": ("a dance form of", "का नृत्य"),
             "STATE_CAPITAL": ("a capital of", "की राजधानी"),
             "RIVER_ORIGIN": ("a river originating at", "से निकलने वाली नदी")}.get(name)
    if not label:
        return None
    stem = f"Which one of the following is NOT {label[0]} {v}?"
    stem_hi = f"निम्नलिखित में से कौन-सा {_hi(v)} {label[1]} नहीं है?"
    return {"stem": stem, "stem_hi": stem_hi, "correct": str(odd),
            "distractors": [str(x) for x in same],
            "hi_opts": {str(o): _hi(o) for o in same + [odd]},
            "solution": f"{odd} does not belong to {v}; the other three do.",
            "solution_hi": f"{_hi(odd)} {_hi(v)} {label[1]} नहीं है; शेष तीनों हैं।",
            "concept": STYLE_CONCEPT["odd"], "src": [name], "fact": f"{name}|odd|{v}",
            "difficulty": 2}


def build_neg_statement(tables, rng, diff=3):
    """'Which one of the following statements is NOT correct?' — three true, one false.

    The commission spends 5.1% of its paper on a negative selection, and `build_odd` can only be
    built where three keys share a VALUE — which across our tables is Kerala's dances and nothing
    else. That capped the bucket at one question a paper however the weights were set. This form
    works over any key->value table, which is what makes the share reachable.

    Safety is inherited unchanged: the false statement pairs a key with a different value from the
    SAME table via `_false_value`, so it is false by our own data rather than by assertion, and the
    three true ones are the table's own rows.
    """
    from . import staticgk_forms as SF
    names = [n for n in SF.STATEMENTS if n in tables and len(_bilingual(tables[n])) >= 4]
    if not names:
        return None
    name = rng.choice(names)
    table, tmpl = tables[name], SF.STATEMENTS[name]
    keys = rng.sample(_bilingual(table), 4)
    bad = rng.randrange(4)
    en_s, hi_s = [], []
    for i, k in enumerate(keys):
        v = table[k] if i != bad else SF._false_value(table, k, rng)
        if v is None or not _printable(v):
            return None
        e, h = SF._statement(table, k, v, tmpl)
        en_s.append(e)
        hi_s.append(h)
    if len(set(en_s)) != 4:
        return None
    return {"stem": "Which one of the following statements is NOT correct?",
            "stem_hi": "निम्नलिखित में से कौन-सा कथन सही नहीं है?",
            "correct": en_s[bad],
            "distractors": [e for i, e in enumerate(en_s) if i != bad],
            "hi_opts": dict(zip(en_s, hi_s)),
            "solution": f"'{en_s[bad]}' is false; the correct value for {keys[bad]} is "
                        f"{table[keys[bad]]}.",
            "solution_hi": f"'{hi_s[bad]}' गलत है; {_hi(keys[bad])} का सही मान "
                           f"{_hi(table[keys[bad]])} है।",
            "concept": "Incorrect Statement", "src": [name],
            "fact": f"{name}|neg|{keys[bad]}", "difficulty": 3}
