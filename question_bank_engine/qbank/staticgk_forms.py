"""Harder GS question FORMS built from the verified fact tables.

The fact cannot be made harder; the FORM can. "Who led the Bardoli Satyagraha?" is recall. The same
fact asked as "consider the following statements — which are correct?" is analysis, and that is how
BPSC and UPSC raise difficulty without needing more obscure facts.

What makes this safe is that nothing new is asserted. A statement is TRUE when it is a (key, value)
pair straight out of a table. A statement is FALSE when it pairs a key with a DIFFERENT value from
the SAME table — which is false *by our own data*, not by a model's opinion. Every statement on the
page is therefore as verified as the table it came from.

Two hazards, both measured before writing this rather than assumed:

  1. A "false" pairing is only false if the key has exactly one correct value. Dicts give us that
     for free in the forward direction, but the reverse direction does not hold: Chandigarh is the
     capital of BOTH Punjab and Haryana, and four states have several classical dances. So these
     forms only ever run key -> value.

  2. Two spellings of one thing would make a "false" statement accidentally true. Our own maps
     contain Kaveri/Cauvery and Allahabad/Prayagraj. `_alias` catches those by their Hindi, which
     is the one place both spellings collapse to a single string.

NOT built here: Assertion-Reason. Its four options turn on whether R *explains* A, and a lookup
table encodes no explanation at all — only that a key maps to a value. Every A-R pair derivable
from this data would be either circular ("Ghoomar is performed in Rajasthan BECAUSE Ghoomar is a
dance of Rajasthan") or two unrelated facts, which makes the "correct explanation" option
unanswerable rather than hard. A sound A-R needs a source sentence that states the causal link —
a PIB or NCERT paragraph — not a dictionary.
"""
import random
import re

from . import staticgk_hi as HI

# table -> (english statement template, hindi statement template)
STATEMENTS = {
    # Constitution first — these are what Advt 02/23(A) actually names (भारत का संविधान एवं राज्य
    # व्यवस्था, पंचायती राज), and they are the reason a statement question can be hard rather than
    # a capital dressed up in a harder form.
    "ARTICLE_SUBJECT": ("Article {k} of the Constitution deals with {v}.",
                        "संविधान का अनुच्छेद {k} {v} से संबंधित है।"),
    "AMENDMENT_DID": ("The {k} Amendment {v}.", "{k} संविधान संशोधन ने {v}।"),
    "STATE_CAPITAL": ("{v} is the capital of {k}.", "{v} {k} की राजधानी है।"),
    "DANCE_STATE": ("{k} is a dance form of {v}.", "{k} {v} का नृत्य है।"),
    "RIVER_ORIGIN": ("The river {k} originates at {v}.", "{k} नदी का उद्गम {v} में है।"),
    # भारत का इतिहास + स्वतंत्रता आन्दोलन — the two biggest holes in the Inter Level blueprint.
    # Supplied by history_tables, and only when its REVIEWED flag is True; see gs_tables().
    "MOVEMENT_YEAR": ("The {k} took place in {v}.", "{k} {v} में हुआ था।"),
    "FOUNDED_YEAR": ("The {k} was founded in {v}.", "{k} की स्थापना {v} में हुई थी।"),
    "MOVEMENT_LEADER": ("The {k} was led by {v}.", "{k} का नेतृत्व {v} ने किया था।"),
    "MOVEMENT_AGAINST": ("The {k} was directed against {v}.",
                         "{k} {v} के विरुद्ध था।"),
    # A DASH, not a copula. "{k} {v} थे।" needs the verb to agree with the value's gender and
    # number — "कुंवर सिंह थे" is right but "चम्पारण थे" is wrong for a district, and the table
    # holds both people and places. The dash form is what a real paper prints for this shape
    # anyway, and it sidesteps an agreement the template cannot know.
    "BIHAR_FREEDOM": ("In the national movement, {k} — {v}.",
                      "राष्ट्रीय आंदोलन में, {k} — {v}।"),
    # बिहार — the advertisement names Bihar as its own emphasis and the delivered paper had THREE
    # Bihar questions in 150. Gated behind bihar_tables.REVIEWED; see gs_tables().
    "BIHAR_SITE_DISTRICT": ("{k} is located in the district of {v}.",
                            "{k} {v} जिले में स्थित है।"),
    "BIHAR_GI_PRODUCT": ("The GI-tagged product {k} belongs to {v} district.",
                         "जीआई-टैग उत्पाद {k} {v} जिले का है।"),
    # A DASH again: the value is a noun phrase about a person, and a copula would have to agree
    # with a gender the template cannot know. Same reasoning as BIHAR_FREEDOM above.
    "BIHAR_FREEDOM_ROLE": ("In Bihar's national movement, {k} — {v}.",
                           "बिहार के राष्ट्रीय आंदोलन में, {k} — {v}।"),
    "BIHAR_FOLK_REGION": ("{k} is a folk art form of the {v} region.",
                          "{k} {v} क्षेत्र की लोक कला है।"),
    # रसायन शास्त्र + जीव विज्ञान for Part II. Chemistry is machine-verified against PubChem;
    # biology waits on a human. See science_tables and gs_tables()/science_fact_tables().
    "ELEMENT_SYMBOL": ("The chemical symbol of {k} is {v}.", "{k} का रासायनिक प्रतीक {v} है।"),
    "ELEMENT_ATOMIC_NUMBER": ("The atomic number of {k} is {v}.", "{k} का परमाणु क्रमांक {v} है।"),
    "COMPOUND_FORMULA": ("The chemical formula of {k} is {v}.", "{k} का रासायनिक सूत्र {v} है।"),
    "VITAMIN_DEFICIENCY": ("A deficiency of {k} causes {v}.", "{k} की कमी से {v} होता है।"),
    "VITAMIN_CHEMICAL_NAME": ("The chemical name of {k} is {v}.", "{k} का रासायनिक नाम {v} है।"),
    "HORMONE_GLAND": ("{k} is secreted by {v}.", "{k} {v} से स्रावित होता है।"),
    "DISEASE_PATHOGEN": ("{k} is caused by {v}.", "{k} {v} से होता है।"),
}


def _alias(a, b):
    """True when two spellings name the same thing — Kaveri/Cauvery, Allahabad/Prayagraj."""
    ha, hb = HI.hi(a), HI.hi(b)
    return a == b or (ha is not None and ha == hb)


def _hi_or_self(x):
    """Hindi if we wrote one, otherwise the token itself — for numbers, which are the same
    in both scripts and which the commission prints in Arabic digits either way."""
    return HI.hi(x) or str(x)


def _statement(table, k, v, tmpl):
    return tmpl[0].format(k=k, v=v), tmpl[1].format(k=_hi_or_self(k), v=_hi_or_self(v))


def _bilingual_keys(table):
    """Keys whose key AND value are both usable in Hindi.

    An article number ("21A") is language-neutral — it prints identically in both halves and needs
    no entry in the map. Requiring one would have excluded the entire Constitution table while
    reporting nothing, which is the quiet-failure shape this codebase keeps producing.
    """
    def ok(x):
        x = str(x)
        return HI.hi(x) is not None or bool(re.match(r"^\d+[A-Za-z]?$", x))
    return [k for k, v in table.items() if ok(k) and ok(v)]


def _false_value(table, k, rng, need_hindi=True):
    """A value from the same table that is genuinely NOT this key's — alias-guarded.

    A value SHARED by two keys can never be used as a false one: the 73rd and 74th Amendments were
    both enacted in 1992, so "the 74th Amendment was enacted in 1992" is true however the swap was
    made. The key-side function property is not enough; the value side has to be checked too, and
    that only showed up when a real table (amendment -> year) had a genuine collision in it.
    """
    true_v = table[k]
    owners = {}
    for kk, vv in table.items():
        owners.setdefault(vv, set()).add(kk)
    pool = [v for v in set(table.values())
            if not _alias(v, true_v) and len(owners[v]) == 1
            and (HI.hi(v) if need_hindi else True)]
    return rng.choice(pool) if pool else None


_SUBSETS = {(True, True, True): "1, 2 and 3", (True, True, False): "1 and 2 only",
            (True, False, True): "1 and 3 only", (False, True, True): "2 and 3 only",
            (True, False, False): "1 only", (False, True, False): "2 only",
            (False, False, True): "3 only", (False, False, False): "None of these"}
_SUBSETS_HI = {"1, 2 and 3": "1, 2 और 3", "1 and 2 only": "केवल 1 और 2",
               "1 and 3 only": "केवल 1 और 3", "2 and 3 only": "केवल 2 और 3",
               "1 only": "केवल 1", "2 only": "केवल 2", "3 only": "केवल 3",
               "None of these": "इनमें से कोई नहीं"}


def b_multi_statement(tables):
    """Three statements from the tables, some true, asking which hold. Answer is COMPUTED."""
    def build(rng, diff):
        names = [n for n in STATEMENTS if n in tables and _bilingual_keys(tables[n])]
        rng.shuffle(names)
        picks, truth, used = [], [], []
        for name in (names * 3)[:3]:
            used.append(name)
            table, tmpl = tables[name], STATEMENTS[name]
            k = rng.choice(_bilingual_keys(table))
            # harder papers state MORE true things, so the wrong options stay tempting
            make_true = rng.random() < (0.5 if diff <= 2 else 0.65)
            v = table[k] if make_true else _false_value(table, k, rng)
            if v is None:
                v, make_true = table[k], True
            picks.append(_statement(table, k, v, tmpl))
            truth.append(make_true)
        if not any(truth):                      # "None of these" as the key reads like a trick
            picks[0] = _statement(tables[names[0]], _bilingual_keys(tables[names[0]])[0],
                                  tables[names[0]][_bilingual_keys(tables[names[0]])[0]],
                                  STATEMENTS[names[0]])
            truth[0] = True
        correct = _SUBSETS[tuple(truth)]
        body = "\n".join(f"{i + 1}. {en}" for i, (en, _) in enumerate(picks))
        body_hi = "\n".join(f"{i + 1}. {h}" for i, (_, h) in enumerate(picks))
        stem = ("Consider the following statements:\n" + body +
                "\nWhich of the statements given above is/are correct?")
        stem_hi = ("निम्नलिखित कथनों पर विचार कीजिए:\n" + body_hi +
                   "\nउपर्युक्त कथनों में से कौन-सा/से सही है/हैं ?")
        wrong = [x for x in _SUBSETS.values() if x != correct and x != "None of these"]
        rng.shuffle(wrong)
        d = wrong[:3]
        sol = ("Statement-wise: " +
               "; ".join(f"{i + 1} is {'correct' if t else 'incorrect'}"
                         for i, t in enumerate(truth)) + f". So {correct}.")
        sol_hi = ("कथनानुसार: " +
                  "; ".join(f"{i + 1} {'सही' if t else 'गलत'} है"
                            for i, t in enumerate(truth)) + f"। अतः {_SUBSETS_HI[correct]}।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "distractors": d,
                "hi_opts": {x: _SUBSETS_HI[x] for x in [correct] + d},
                "solution": sol, "solution_hi": sol_hi, "concept": "Statement-based GS", "src": sorted(set(used))}
    return build


def b_match_pairs(tables):
    """Match List-I with List-II. Four pairs, one of which is deliberately mismatched."""
    def build(rng, diff):
        names = [n for n in STATEMENTS if n in tables and len(_bilingual_keys(tables[n])) >= 4]
        name = rng.choice(names)
        used = [name]
        table, (en_t, hi_t) = tables[name], STATEMENTS[name]
        keys = rng.sample(_bilingual_keys(table), 4)
        n_wrong = 1 if diff <= 2 else 2
        wrong_idx = set(rng.sample(range(4), n_wrong))
        # Same rule as _pair_rows: no value may be printed twice in one list, or the repeated text
        # marks the planted row for a reader who knows nothing about the subject. Rendered on a
        # delivered paper as "44th — lowered the voting age from 21 to 18" directly above
        # "61st — lowered the voting age from 21 to 18".
        printed = {table[k] for i, k in enumerate(keys) if i not in wrong_idx}
        shown, truth = [], []
        for i, k in enumerate(keys):
            if i not in wrong_idx:
                v = table[k]
            else:
                v = None
                for _ in range(12):
                    c = _false_value(table, k, rng)
                    if c is None:
                        break
                    if c not in printed:
                        v = c
                        break
                if v is None:
                    v = table[k]          # no distinct false value available — leave the row true
            printed.add(v)
            shown.append((k, v))
            truth.append(v == table[k])
        rows = "\n".join(f"{chr(65 + i)}. {k} — {v}" for i, (k, v) in enumerate(shown))
        # _hi_or_self, not HI.hi: an article number has no Hindi entry and returned None, so the
        # Hindi half printed "A. None — ..." and the cross-language number check caught it. Fixed
        # in _statement when polity was wired in; this second renderer was missed.
        rows_hi = "\n".join(f"{chr(65 + i)}. {_hi_or_self(k)} — {_hi_or_self(v)}"
                            for i, (k, v) in enumerate(shown))
        good = [chr(65 + i) for i, t in enumerate(truth) if t]
        correct = ", ".join(good) if good else "None"
        stem = ("Match the following pairs:\n" + rows +
                "\nWhich of the pairs are correctly matched?")
        stem_hi = ("निम्नलिखित युग्मों का मिलान कीजिए:\n" + rows_hi +
                   "\nकौन-से युग्म सही सुमेलित हैं ?")
        alts = []
        for i in range(4):
            cand = ", ".join(c for c in ("A", "B", "C", "D") if c != chr(65 + i))
            if cand != correct and cand not in alts:
                alts.append(cand)
        d = alts[:3]
        sol = ("; ".join(f"{chr(65 + i)} is {'correct' if t else 'wrong'}"
                         for i, t in enumerate(truth)) + f". Correctly matched: {correct}.")
        sol_hi = ("; ".join(f"{chr(65 + i)} {'सही' if t else 'गलत'}"
                            for i, t in enumerate(truth)) + f"। सही सुमेलित: {correct}।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "distractors": d,
                "solution": sol, "solution_hi": sol_hi, "concept": "Match the Pairs", "src": sorted(set(used))}
    return build

# ── style variation ─────────────────────────────────────────────────────────────────────────────
# One Step's owner read the built paper and said the General Studies questions were good but "only
# two styles". Measured, he was under-counting the problem rather than over-counting it: 35 of the
# 50 GS questions opened with the identical words "Consider the following statements" and 7 more
# with "Match the following pairs", because b_multi_statement and b_two_statement share an opening
# line — so what reads as one style is actually two builders, and the section's whole answer space
# was "1 and 2 only / 1, 2 and 3 / ...", over and over.
#
# The four forms below each change BOTH halves of what a candidate sees: a different opening line
# and a different kind of option. Two put the content in the OPTIONS rather than in the stem, one
# replaces the subset answer space with a count, and one asks for the single true statement out of
# four. Same guarantee as the forms above — every statement is a (key, value) pair from a verified
# table, and every false one pairs a key with a different value from the SAME table, so its
# falsity is a property of our data rather than of anyone's opinion.

# Values long enough to make an unreadable option once a key is glued to the front of them.
# AMENDMENT_DID's values are whole clauses ("added the Tenth Schedule on defection"), which read
# fine as a sentence and badly as one of four "X — Y" pair options.
def _pair_tables(tables):
    return [n for n in STATEMENTS
            if n in tables and len(_bilingual_keys(tables[n])) >= 4
            and max((len(str(tables[n][k])) for k in _bilingual_keys(tables[n])), default=99) <= 34]


def _pair_rows(table, keys, truth, rng, near_miss):
    """(key, value) rows where row i is true iff truth[i]. Returns None if a false one is impossible.

    `near_miss` makes the false values a PERMUTATION of the true values of the very keys on show,
    so the four options are internally consistent and cannot be dismissed by recognising a value
    that does not belong to the topic at all. That is the difference between a candidate checking
    each pair and a candidate scanning for the odd word.
    """
    true_vals = [table[k] for k in keys]
    # Every value some row will actually PRINT. A false value must not be one of these: printing
    # the same text twice in one list points straight at the decoy without any knowledge of the
    # subject. Found by rendering the page — "Garba — Tamil Nadu" sat directly under
    # "Bharatanatyam — Tamil Nadu", and a candidate who knows neither dance can still see that one
    # of those two is the planted one. near_miss made this CERTAIN for the NOT-correctly-matched
    # form, because it draws the false value from the very values the true rows are showing.
    shown = {true_vals[i] for i in range(len(keys)) if truth[i]}
    rows = []
    for i, k in enumerate(keys):
        if truth[i]:
            rows.append((k, table[k]))
            continue
        v = None
        if near_miss:
            cand = [true_vals[j] for j in range(len(keys)) if j != i
                    and not _alias(true_vals[j], table[k])]
            rng.shuffle(cand)
            v = next((c for c in cand if c not in shown and _is_false(table, k, c)), None)
        if v is None:
            for _ in range(12):                     # any other value of the same table will do
                c = _false_value(table, k, rng)
                if c is None:
                    break
                if c not in shown:
                    v = c
                    break
        if v is None:
            return None
        rows.append((k, v))
        shown.add(v)                                # nor may two false rows print the same value
    return rows


def _is_false(table, k, v):
    """v is genuinely NOT k's value — and is owned by exactly one key, so the swap cannot be
    accidentally true the way '74th Amendment, 1992' was."""
    owners = {}
    for kk, vv in table.items():
        owners.setdefault(vv, set()).add(kk)
    return not _alias(v, table[k]) and len(owners.get(v, ())) == 1


def _render_pairs(rows):
    en = [f"{k} — {v}" for k, v in rows]
    hi = [f"{_hi_or_self(k)} — {_hi_or_self(v)}" for k, v in rows]
    return en, hi


def b_correct_pair(tables):
    """'Which of the following pairs is correctly matched?' — the content sits in the OPTIONS.

    Nothing in the stem to read, four pairs to verify, and the answer is a pair rather than a
    subset label. Visually the furthest thing from the numbered-statement form.
    """
    def build(rng, diff):
        names = _pair_tables(tables)
        if not names:
            return None
        _name = rng.choice(names)
        used = [_name]
        table = tables[_name]
        keys = rng.sample(_bilingual_keys(table), 4)
        truth = [False] * 4
        truth[rng.randrange(4)] = True
        rows = _pair_rows(table, keys, truth, rng, near_miss=diff >= 3)
        if not rows:
            return None
        en, hi = _render_pairs(rows)
        i = truth.index(True)
        stem = "Which of the following pairs is correctly matched?"
        stem_hi = "निम्नलिखित युग्मों में से कौन-सा सही सुमेलित है?"
        sol = ("; ".join(f"'{en[j]}' is {'correct' if truth[j] else 'wrong'}"
                         for j in range(4)) + f". So {en[i]}.")
        sol_hi = (f"केवल '{hi[i]}' सही सुमेलित है; शेष तीनों युग्मों में मान किसी अन्य "
                  f"प्रविष्टि का है।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": en[i],
                "distractors": [en[j] for j in range(4) if j != i],
                "hi_opts": dict(zip(en, hi)), "solution": sol, "solution_hi": sol_hi,
                "concept": "Correctly Matched Pair", "src": sorted(set(used))}
    return build


def b_wrong_pair(tables):
    """'Which of the following pairs is NOT correctly matched?' — the mirror reading skill.

    Three true pairs and one false. Finding the single error in a page of correct material is a
    different job from confirming a single correct claim, and both appear in the real papers.
    """
    def build(rng, diff):
        names = _pair_tables(tables)
        if not names:
            return None
        _name = rng.choice(names)
        used = [_name]
        table = tables[_name]
        keys = rng.sample(_bilingual_keys(table), 4)
        truth = [True] * 4
        truth[rng.randrange(4)] = False
        rows = _pair_rows(table, keys, truth, rng, near_miss=diff >= 3)
        if not rows:
            return None
        en, hi = _render_pairs(rows)
        i = truth.index(False)
        stem = "Which of the following pairs is NOT correctly matched?"
        stem_hi = "निम्नलिखित युग्मों में से कौन-सा सही सुमेलित नहीं है?"
        sol = (f"Three of the pairs are correct. '{en[i]}' is not — the correct value for "
               f"{rows[i][0]} is {table[rows[i][0]]}.")
        sol_hi = (f"तीन युग्म सही हैं। '{hi[i]}' सही नहीं है — "
                  f"{_hi_or_self(rows[i][0])} का सही मान {_hi_or_self(table[rows[i][0]])} है।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": en[i],
                "distractors": [en[j] for j in range(4) if j != i],
                "hi_opts": dict(zip(en, hi)), "solution": sol, "solution_hi": sol_hi,
                "concept": "Incorrectly Matched Pair", "src": sorted(set(used))}
    return build


_COUNTS = ["None of them", "Only one", "Only two", "All three"]
_COUNTS_HI = {"None of them": "इनमें से कोई नहीं", "Only one": "केवल एक",
              "Only two": "केवल दो", "All three": "तीनों"}


def b_count_statements(tables):
    """'How many of the above statements are correct?' — the same facts, a COUNT answer space.

    The subset labels ("1 and 3 only") let a candidate work backwards from the options; a count
    does not, because every option is reachable by several different combinations. It is also the
    form the commissions have been moving to.
    """
    def build(rng, diff):
        names = [n for n in STATEMENTS if n in tables and _bilingual_keys(tables[n])]
        rng.shuffle(names)
        picks, truth, used = [], [], []
        for name in (names * 3)[:3]:
            used.append(name)
            table, tmpl = tables[name], STATEMENTS[name]
            k = rng.choice(_bilingual_keys(table))
            make_true = rng.random() < (0.5 if diff <= 2 else 0.6)
            v = table[k] if make_true else _false_value(table, k, rng)
            if v is None:
                v, make_true = table[k], True
            picks.append(_statement(table, k, v, tmpl))
            truth.append(make_true)
        correct = _COUNTS[sum(truth)]
        body = "\n".join(f"{i + 1}. {en}" for i, (en, _) in enumerate(picks))
        body_hi = "\n".join(f"{i + 1}. {h}" for i, (_, h) in enumerate(picks))
        stem = ("Study the following statements:\n" + body +
                "\nHow many of the above statements are correct?")
        stem_hi = ("निम्नलिखित कथनों का अध्ययन कीजिए:\n" + body_hi +
                   "\nउपर्युक्त कथनों में से कितने सही हैं ?")
        d = [x for x in _COUNTS if x != correct]
        sol = ("; ".join(f"{i + 1} is {'correct' if t else 'incorrect'}"
                         for i, t in enumerate(truth)) + f". That is {correct.lower()}.")
        sol_hi = ("; ".join(f"{i + 1} {'सही' if t else 'गलत'} है"
                            for i, t in enumerate(truth)) + f"। अतः {_COUNTS_HI[correct]}।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "distractors": d,
                "hi_opts": dict(_COUNTS_HI), "solution": sol, "solution_hi": sol_hi,
                "concept": "Count the Correct Statements", "src": sorted(set(used))}
    return build


def b_which_statement(tables):
    """'Which one of the following statements is correct?' — four full sentences, one true.

    Like the pair forms the content is in the options, but as prose rather than as a "X — Y" pair,
    so the candidate reads four complete claims instead of matching two columns.
    """
    def build(rng, diff):
        names = [n for n in STATEMENTS if n in tables and len(_bilingual_keys(tables[n])) >= 4]
        if not names:
            return None
        # d1-2 keeps all four claims inside ONE topic, so only the fact is in question; d3+ mixes
        # topics, so the candidate cannot settle into a single domain while reading.
        pool = [rng.choice(names)] * 4 if diff <= 2 else [rng.choice(names) for _ in range(4)]
        used = list(pool)
        which = rng.randrange(4)
        en, hi = [], []
        for i, name in enumerate(pool):
            table, tmpl = tables[name], STATEMENTS[name]
            k = rng.choice(_bilingual_keys(table))
            v = table[k] if i == which else _false_value(table, k, rng)
            if v is None:
                return None
            e, h = _statement(table, k, v, tmpl)
            en.append(e.rstrip("."))
            hi.append(h.rstrip("।"))
        if len({x.lower() for x in en}) != 4:
            return None
        stem = "Which one of the following statements is correct?"
        stem_hi = "निम्नलिखित में से कौन-सा कथन सही है?"
        sol = (f"Only '{en[which]}' matches the verified record; the other three pair a subject "
               f"with a value belonging to a different entry.")
        sol_hi = (f"केवल '{hi[which]}' सही है; शेष तीन कथनों में मान किसी अन्य प्रविष्टि का है।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": en[which],
                "distractors": [en[j] for j in range(4) if j != which],
                "hi_opts": dict(zip(en, hi)), "solution": sol, "solution_hi": sol_hi,
                "concept": "Single Correct Statement", "src": sorted(set(used))}
    return build


_PAIR = {(True, True): "Both 1 and 2", (True, False): "1 only",
         (False, True): "2 only", (False, False): "Neither 1 nor 2"}
_PAIR_HI = {"Both 1 and 2": "1 और 2 दोनों", "1 only": "केवल 1", "2 only": "केवल 2",
            "Neither 1 nor 2": "न तो 1 और न ही 2"}


def b_two_statement(tables):
    """TWO statements rather than three — the missing MEDIUM band in General Studies.

    GS had only two registers: difficulty-1 recall and the difficulty-3 three-statement form, with
    nothing between, so a 15/15/70 mix could not be filled in that section at all. Two statements
    is a genuine middle: the candidate still has to judge each claim rather than recall one, but
    holds half the load and picks from four options instead of eight.

    Same guarantee as the three-statement form — a statement is a (key, value) pair from a verified
    table, and a false one pairs a key with a different value from the SAME table.
    """
    def build(rng, diff):
        names = [n for n in STATEMENTS if n in tables and _bilingual_keys(tables[n])]
        rng.shuffle(names)
        picks, truth, used = [], [], []
        for name in (names * 2)[:2]:
            used.append(name)
            table, tmpl = tables[name], STATEMENTS[name]
            k = rng.choice(_bilingual_keys(table))
            make_true = rng.random() < 0.5
            v = table[k] if make_true else _false_value(table, k, rng)
            if v is None:
                v, make_true = table[k], True
            picks.append(_statement(table, k, v, tmpl))
            truth.append(make_true)
        correct = _PAIR[tuple(truth)]
        body = "\n".join(f"{i + 1}. {en}" for i, (en, _) in enumerate(picks))
        body_hi = "\n".join(f"{i + 1}. {h}" for i, (_, h) in enumerate(picks))
        stem = ("Consider the following statements:\n" + body +
                "\nWhich of the statements given above is/are correct?")
        stem_hi = ("निम्नलिखित कथनों पर विचार कीजिए:\n" + body_hi +
                   "\nउपर्युक्त कथनों में से कौन-सा/से सही है/हैं ?")
        d = [x for x in _PAIR.values() if x != correct]
        sol = ("; ".join(f"{i + 1} is {'correct' if t else 'incorrect'}"
                         for i, t in enumerate(truth)) + f". So {correct}.")
        sol_hi = ("; ".join(f"{i + 1} {'सही' if t else 'गलत'} है"
                            for i, t in enumerate(truth)) + f"। अतः {_PAIR_HI[correct]}।")
        return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "distractors": d,
                "hi_opts": {x: _PAIR_HI[x] for x in [correct] + d},
                "solution": sol, "solution_hi": sol_hi, "concept": "Statement-based GS", "src": sorted(set(used))}
    return build
