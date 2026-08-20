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
        names = [n for n in STATEMENTS if _bilingual_keys(tables[n])]
        rng.shuffle(names)
        picks, truth = [], []
        for name in (names * 3)[:3]:
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
                "solution": sol, "solution_hi": sol_hi, "concept": "Statement-based GS"}
    return build


def b_match_pairs(tables):
    """Match List-I with List-II. Four pairs, one of which is deliberately mismatched."""
    def build(rng, diff):
        names = [n for n in STATEMENTS if len(_bilingual_keys(tables[n])) >= 4]
        name = rng.choice(names)
        table, (en_t, hi_t) = tables[name], STATEMENTS[name]
        keys = rng.sample(_bilingual_keys(table), 4)
        n_wrong = 1 if diff <= 2 else 2
        wrong_idx = set(rng.sample(range(4), n_wrong))
        shown, truth = [], []
        for i, k in enumerate(keys):
            v = table[k] if i not in wrong_idx else _false_value(table, k, rng)
            if v is None:
                v, i_ok = table[k], True
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
                "solution": sol, "solution_hi": sol_hi, "concept": "Match the Pairs"}
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
        names = [n for n in STATEMENTS if _bilingual_keys(tables[n])]
        rng.shuffle(names)
        picks, truth = [], []
        for name in (names * 2)[:2]:
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
                "solution": sol, "solution_hi": sol_hi, "concept": "Statement-based GS"}
    return build
