#!/usr/bin/env python3
"""Adversarial test battery for a built paper (or a set of them).

Checks the things that have actually gone wrong on this line, plus the ones that would be
embarrassing in front of an institute. Structural checks are cheap; the two that carry real
weight are:

  - NUMBER AGREEMENT between the Hindi and English halves of a bilingual question. If the English
    says "9 km" and the Hindi says "12 किमी", one of them is a mistranslation and a student
    working in Hindi gets a different answer. This is the automatable half of the failure that
    printed a "climate change" stem over four 1919 dates.

  - INDEPENDENT RE-SOLVING of the generated reasoning. Those answers are computed by
    `reasoninggen`; re-deriving them here from the question text alone, with solvers written
    without reference to that code, is a genuine check rather than a restatement.

Usage:  python3 test_papers.py Set1.html Set2.html
"""
import html
import io
import pathlib
import re
import sys
from collections import Counter

DEV = re.compile(r"[ऀ-ॿ]")
MIXED = re.compile(r"[ऀ-ॿ][A-Za-z]{2,}[ऀ-ॿ]")
NUM = re.compile(r"\d+")


def strip(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def parse(path):
    """-> (questions, answer_key). Each question: number, hi/en stem, hi/en options."""
    raw = io.open(path, encoding="utf-8").read()
    body = raw.split('<div class="meta">', 1)[1]
    blocks = re.findall(r'<div class="q">(.*?)(?=<div class="q">|<div class="keyhead")', body, re.S)
    qs = []
    for b in blocks:
        num = re.search(r'<span class="n">(\d+)\.', b)
        hi = re.search(r'<div class="hi">(.*?)</div>', b, re.S)
        en = re.search(r'<div class="en">(.*?)</div>', b, re.S)
        opt_groups = re.findall(r'<div class="ops">(.*?)</div>\s*(?=<div|$)', b, re.S)
        opts = [[(m.group(1), strip(m.group(2)))
                 for m in re.finditer(r'<b>\((\w)\)</b>(.*?)</span>', g, re.S)] for g in opt_groups]
        qs.append({"n": int(num.group(1)) if num else None,
                   "hi": strip(hi.group(1)) if hi else "",
                   "en": strip(en.group(1)) if en else "",
                   "opts": opts, "raw": b, "text": strip(b)})
    key = {int(m.group(1)): m.group(2)
           for m in re.finditer(r'class="k">(\d+)\. <b>([A-E])</b>', raw)}
    gen = {int(m.group(1)) for m in re.finditer(r'class="k">(\d+)\. <b>[A-E]</b><i>\*</i>', raw)}
    return qs, key, gen


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail and not ok else ''}")
    return ok


def structural(tag, qs, key, gen):
    print(f"\n=== {tag}: structure ===")
    ok = True
    nums = [q["n"] for q in qs]
    ok &= check("150 questions", len(qs) == 150, f"got {len(qs)}")
    ok &= check("numbering 1..150, no gaps or dupes", sorted(nums) == list(range(1, 151)))
    ok &= check("answer key has 150 entries", len(key) == 150, f"got {len(key)}")
    ok &= check("every question has a key entry", all(n in key for n in nums))
    bad_opts = [q["n"] for q in qs for g in q["opts"] if len(g) != 4]
    ok &= check("every rendered option block has 4 options", not bad_opts, str(bad_opts[:8]))
    keyless = [q["n"] for q in qs
               if q["opts"] and key.get(q["n"]) not in [lb for lb, _ in q["opts"][0]]]
    ok &= check("key letter exists among the printed options", not keyless, str(keyless[:8]))
    ok &= check("no raw LaTeX on the page",
                not any("\\frac" in q["text"] or "\\sqrt" in q["text"] for q in qs))
    mixed = [q["n"] for q in qs if MIXED.search(q["text"])]
    ok &= check("no Latin stranded inside Devanagari", not mixed, str(mixed[:8]))
    empty = [q["n"] for q in qs if not q["opts"]]
    ok &= check("no question printed without options", not empty, str(empty[:8]))
    # A question that DEFINES its own notation must still carry that notation after rendering.
    # mathify strips `$` as a LaTeX delimiter, so a coded-inequality question using it printed
    # "'A  B' means 'A is smaller than B'" — the symbol silently deleted from both the legend and
    # the statements, leaving the question unanswerable. Nothing above could see that: the stem was
    # present, the options were four, the key letter existed. Check the legend itself.
    legend_bad = []
    for q in qs:
        if "the symbols are used as" not in q["text"]:
            continue
        syms = re.findall(r"'A (\S+) B' means", q["text"])
        if len(syms) != 5 or len(set(syms)) != 5:
            legend_bad.append(q["n"])
    ok &= check("every symbol legend defines 5 distinct symbols", not legend_bad,
                str(legend_bad[:8]))
    print(f"        generated (asterisked): {len(gen)} of 150")
    return ok


def bilingual(tag, qs):
    """Numbers must agree between the two languages of the same question."""
    print(f"\n=== {tag}: Hindi vs English agreement ===")
    both = [q for q in qs if q["hi"] and q["en"]]
    mismatch = []
    for q in both:
        hn, en = Counter(NUM.findall(q["hi"])), Counter(NUM.findall(q["en"]))
        # ignore the leading question number that only the first-printed language carries
        for c in (hn, en):
            c.pop(str(q["n"]), None)
        if hn != en:
            mismatch.append((q["n"], sorted(hn - en), sorted(en - hn)))
    ok = check(f"numbers agree across languages ({len(both)} bilingual questions)",
               not mismatch, f"{len(mismatch)} differ")
    for n, honly, eonly in mismatch[:10]:
        print(f"        Q{n}: only in Hindi {honly} · only in English {eonly}")
    # option COUNT agreement where both languages printed options
    twolang = [q for q in qs if len(q["opts"]) == 2]
    bad = [q["n"] for q in twolang if len(q["opts"][0]) != len(q["opts"][1])]
    ok &= check("option counts agree across languages", not bad, str(bad[:8]))
    # ...and option CONTENT. Counts matching is not enough: one question printed English options
    # 29 / 9 beside Hindi −42 / −14, so the keyed letter was right in one language and wrong in
    # the other.
    numbad = []
    for q in twolang:
        if len(q["opts"][0]) != len(q["opts"][1]):
            continue
        for (_, h), (_, e) in zip(q["opts"][0], q["opts"][1]):
            if Counter(NUM.findall(h)) != Counter(NUM.findall(e)):
                numbad.append(q["n"])
                break
    ok &= check("option NUMBERS agree across languages", not numbad, str(numbad[:8]))
    return ok


def uniqueness(sets):
    print("\n=== uniqueness ===")
    ok = True

    def sig(q):
        """Whole stem plus the option set. A 90-char prefix false-positived on Assertion-Reason
        questions, which all open with the same rubric — it flagged two genuinely different
        questions as one."""
        t = (q["en"] or "") + "|" + (q["hi"] or "") + "|"
        t += "~".join(sorted(txt for g in q["opts"] for _, txt in g))
        t = re.sub(r"^\d+\.\s*", "", t).lower()
        return re.sub(r"[^a-z0-9ऀ-ॿ|~]+", "", t)

    for tag, qs, *_ in sets:
        dupes = [k for k, c in Counter(sig(q) for q in qs).items() if c > 1]
        ok &= check(f"{tag}: no repeat WITHIN the paper", not dupes, f"{len(dupes)} repeated")
        for d in dupes[:3]:
            print("        ", d[:70])
    # same COMPUTATION under different wording — text signatures cannot see this
    for tag, qs, key, _g in sets:
        seen, dup = {}, []
        for q in qs:
            body = q["en"] or q["hi"] or ""
            # A statement-based or match-the-pairs question is ENUMERATED, not computed. Its
            # "1. 2. 3." are list markers, so two entirely different statement questions sharing
            # an answer looked like one computation. The numeric signature is for arithmetic.
            if re.search(r"Consider the following statements|Match the following", body):
                continue
            nums = tuple(sorted(NUM.findall(body)))
            ans = dict(q["opts"][-1]).get(key.get(q["n"]), "") if q["opts"] else ""
            if len(nums) < 2:
                continue
            sg = (nums, re.sub(r"\s+", "", ans))
            if sg in seen:
                dup.append((seen[sg], q["n"]))
            seen[sg] = q["n"]
        ok &= check(f"{tag}: no two questions are the same COMPUTATION", not dup, str(dup[:5]))
    if len(sets) > 1:
        (t1, q1, *_), (t2, q2, *_) = sets[0], sets[1]
        shared = {sig(q) for q in q1} & {sig(q) for q in q2}
        ok &= check(f"{t1} vs {t2}: no shared question", not shared, f"{len(shared)} shared")
        for s in list(shared)[:5]:
            print("        ", s[:70])
    return ok


def main():
    paths = sys.argv[1:]
    sets, all_ok = [], True
    for p in paths:
        qs, key, gen = parse(p)
        tag = re.sub(r".*InterLevel_|\.html", "", p) or p
        sets.append((tag, qs, key, gen))
    for tag, qs, key, gen in sets:
        all_ok &= structural(tag, qs, key, gen)
        all_ok &= bilingual(tag, qs)
        all_ok &= resolve(tag, qs, key, gen)
    all_ok &= uniqueness(sets)
    print("\n" + ("ALL CHECKS PASSED" if all_ok
                  else "*** SOME CHECKS FAILED — see above ***"))
    return 0 if all_ok else 1




# ── independent solvers ─────────────────────────────────────────────────────────────────────────
# Written from the QUESTION TEXT only. They deliberately do not import or consult reasoninggen —
# the point is to re-derive the answer by a second route and see whether the printed key agrees.
import math

DIRS = ["North", "East", "South", "West"]
HI_DIR = {"उत्तर": "North", "पूर्व": "East", "दक्षिण": "South", "पश्चिम": "West"}


def _turn(facing, way):
    i = DIRS.index(facing)
    return DIRS[(i + 1) % 4] if way == "right" else DIRS[(i - 1) % 4]


def solve_direction_facing(en):
    m = re.search(r"facing\s+(North|South|East|West)", en, re.I)
    if not m:
        return None
    cur = m.group(1).capitalize()
    for w in re.findall(r"takes?\s+a\s+(right|left)", en, re.I):
        cur = _turn(cur, w.lower())
    return cur


def solve_direction_distance(en):
    legs = re.findall(r"(\d+)\s*km", en, re.I)
    if len(legs) != 2 or not re.search(r"how far", en, re.I):
        return None
    a, b = int(legs[0]), int(legs[1])
    d = math.hypot(a, b)
    return f"{int(d)} km" if d == int(d) else None


def solve_ranking(en):
    m = re.search(r"row of (\d+).*?(\d+)(?:st|nd|rd|th) from the (left|right)", en, re.I | re.S)
    if not m:
        return None
    n, k = int(m.group(1)), int(m.group(2))
    if not re.search(r"position from the (right|left) end", en, re.I):
        return None
    return str(n - k + 1)


def solve_letter_shift(en):
    m = re.search(r"'([A-Z]+)'\s*is written as\s*'([A-Z]+)'.*?'([A-Z]+)'", en, re.S)
    if not m:
        return None
    src, dst, tgt = m.groups()
    if len(src) != len(dst):
        return None
    shifts = {(ord(b) - ord(a)) % 26 for a, b in zip(src, dst)}
    if len(shifts) != 1:
        return None
    s = shifts.pop()
    return "".join(chr((ord(c) - 65 + s) % 26 + 65) for c in tgt)


def solve_number_coding(en):
    m = re.search(r"coded by\s*(twice)?\s*its position.*?'([A-Z]+)'", en, re.I | re.S)
    if not m:
        return None
    mult = 2 if m.group(1) else 1
    return " ".join(str((ord(c) - 64) * mult) for c in m.group(2))


def solve_odd_one_out(en):
    nums = [int(x) for x in re.findall(r"\b(\d+)\b", en)]
    nums = [n for n in nums if n > 4]
    if len(nums) != 4 or not re.search(r"odd one out|alike", en, re.I):
        return None
    for test in (lambda n: int(math.isqrt(n)) ** 2 == n,
                 lambda n: n > 1 and all(n % d for d in range(2, int(math.isqrt(n)) + 1)),
                 lambda n: round(n ** (1 / 3)) ** 3 == n):
        flags = [test(n) for n in nums]
        if flags.count(True) == 3:
            return str(nums[flags.index(False)])
        if flags.count(False) == 3:
            return str(nums[flags.index(True)])
    return None


SOLVERS = [("direction-facing", solve_direction_facing), ("direction-distance", solve_direction_distance),
           ("ranking", solve_ranking), ("letter-shift", solve_letter_shift),
           ("number-coding", solve_number_coding), ("odd-one-out", solve_odd_one_out)]


def resolve(tag, qs, key, gen):
    print(f"\n=== {tag}: independent re-solve of generated reasoning ===")
    checked = agree = 0
    bad, ambiguous = [], []
    for q in qs:
        if q["n"] not in gen or not q["opts"]:
            continue
        en = q["en"] or ""
        # The new General Studies pair forms put the CONTENT in the options and leave the stem a
        # single question line, so a solver handed the stem alone can see nothing to check. Stash
        # the English options against the stem before dispatching.
        _LAST_OPTIONS[en] = [t for _, t in q["opts"][-1]]
        for name, fn in SOLVERS:
            try:
                want = fn(en)
            except Exception:
                want = None
            if not want:
                continue
            # The keyed letter must be checked against EVERY language block: Hindi prints first,
            # so opts[0] is Hindi and an English computation would "disagree" with दक्षिण purely
            # because of language. Translate the direction words and accept a match in either.
            letter = key.get(q["n"])
            keyed = [dict(g).get(letter, "") for g in q["opts"]]
            checked += 1
            norm = lambda t: re.sub(r"\s+", "", str(t)).lower().rstrip(".")
            cands = set()
            _ = norm
            for k in keyed:
                cands.add(norm(k))
                cands.add(norm(HI_DIR.get(k.strip(), k)))
            wants = want if isinstance(want, set) else {want}
            # A solver may only be able to RULE AN OPTION OUT rather than name the answer — the
            # error-spot form can prove the shown value is wrong without knowing which named
            # mistake produced it. "__NOT__x" asserts the key must not be x, which still fails
            # loudly on a paper that keys "there is no mistake" beside a wrong value.
            neg = {w[len("__NOT__"):] for w in wants if str(w).startswith("__NOT__")}
            if neg:
                norm0 = lambda t: re.sub(r"\s+", "", str(t)).lower().rstrip(".")
                letter0 = key.get(q["n"])
                keyed0 = [dict(g).get(letter0, "") for g in q["opts"]]
                # NOT `checked += 1` — this question was already counted a few lines above, and
                # counting it twice printed "re-solved 156 of 150", a coverage figure that cannot
                # be true and would have quietly hidden six genuinely unread questions the day
                # some other solver went silent.
                if any(norm0(k0) == norm0(n0) for k0 in keyed0 for n0 in neg):
                    bad.append((q["n"], name, ["NOT " + n0 for n0 in neg],
                                " / ".join(filter(None, keyed0)), en[:70]))
                else:
                    agree += 1
                break
            if len(wants) > 1:
                # Ambiguity only HURTS if two defensible answers are both on offer. If the options
                # contain just one of them, the option set disambiguates and the question is sound.
                printed_all = {norm(t) for g in q["opts"] for _, t in g}
                on_offer = sorted(w for w in wants if norm(w) in printed_all)
                if len(on_offer) > 1:
                    ambiguous.append((q["n"], name, on_offer))
            if any(norm(w) in cands for w in wants):
                agree += 1
            else:
                bad.append((q["n"], name, sorted(wants), " / ".join(filter(None, keyed)), en[:70]))
            break
    ok = check(f"printed key matches an independent solve ({checked} solvable questions)", not bad,
               f"{len(bad)} disagree")
    ok &= check("no generated question has two defensible answers among its options", not ambiguous,
                f"{len(ambiguous)} ambiguous")
    for n, name, want, got, stem in bad[:10]:
        print(f"        Q{n} [{name}] computed {want!r} but key says {got!r} — {stem}")
    if checked:
        print(f"        coverage: re-solved {checked} of {len(gen)} generated questions")
    if ambiguous:
        print(f"        AMBIGUOUS: {len(ambiguous)} question(s) have TWO defensible answers both "
              f"present in the options:")
        for n, name, ws in ambiguous[:8]:
            print(f"          Q{n} [{name}] both {' and '.join(ws)} are on offer")
    return ok




# ── second wave of independent solvers ──────────────────────────────────────────────────────────
# Same discipline as the first: derived from the printed question only, with no reference to
# reasoninggen. If these agree with the printed key, that is two independent derivations agreeing.

def _letters(s):
    return [c for c in s if c.isalpha()]


def solve_letter_series(en):
    """'H, I, J, K, ?' and 'A3, C5, E7, ?' — constant letter step, constant number step."""
    m = re.search(r"series[^:?]*[:?]\s*(.+?)\s*\?", en, re.I | re.S)
    if not m:
        return None
    terms = [t.strip() for t in re.split(r"[,\s]+", m.group(1)) if t.strip()]
    terms = [t for t in terms if re.fullmatch(r"[A-Za-z]+\d*", t)]
    if len(terms) < 3:
        return None
    heads = [t.rstrip("0123456789") for t in terms]
    tails = [t[len(h):] for t, h in zip(terms, heads)]
    if not all(len(h) == len(heads[0]) for h in heads):
        return None
    # every letter position must advance by the same constant
    steps = []
    for i in range(len(heads[0])):
        d = {(ord(heads[j + 1][i]) - ord(heads[j][i])) % 26 for j in range(len(heads) - 1)}
        if len(d) != 1:
            return None
        steps.append(d.pop())
    nxt = "".join(chr((ord(heads[-1][i]) - 65 + steps[i]) % 26 + 65) for i in range(len(heads[0])))
    if all(t for t in tails):
        nums = [int(t) for t in tails]
        dn = {nums[i + 1] - nums[i] for i in range(len(nums) - 1)}
        if len(dn) != 1:
            return None
        nxt += str(nums[-1] + dn.pop())
    return nxt


def _relation(a, b):
    """The single arithmetic relation taking a to b, if there is an obvious one."""
    rels = []
    if a:
        if b % a == 0:
            rels.append(("mul", b // a))
        if abs(a) > 0 and b * a > 0 and a ** 2 == b:
            rels.append(("sq", 0))
        if a ** 3 == b:
            rels.append(("cube", 0))
        # relations _b_number_analogy gained when it learned difficulty
        if a * a + a == b:
            rels.append(("sq_plus", 0))
        if a * a - a == b:
            rels.append(("sq_minus", 0))
        if 2 * a + 1 == b:
            rels.append(("double_plus", 0))
    rels.append(("add", b - a))
    return rels


def solve_number_analogy(en):
    """'11 : 22 :: 9 : ?' — every relation the first pair supports, applied to the second.

    Returns a SET, because some pairs are genuinely ambiguous: 2 : 8 is both x4 and 2 cubed, so
    "3 : ?" is defensibly 12 or 27. A verifier must not pick one and call the other wrong. The
    check passes if the printed key is among the candidates, and a question with more than one
    candidate is reported separately — an exam question that admits two answers is a defect in
    its own right, whichever one the key names.
    """
    m = re.search(r"(\d+)\s*:\s*(\d+)\s*::\s*(\d+)\s*:\s*\?", en)
    if not m:
        return None
    a, b, c = (int(x) for x in m.groups())
    out = set()
    for kind, k in _relation(a, b):
        if kind == "mul":
            out.add(str(c * k))
        elif kind == "sq":
            out.add(str(c * c))
        elif kind == "cube":
            out.add(str(c ** 3))
        elif kind == "add":
            out.add(str(c + k))
        if kind == "sq_plus":
            out.add(str(c * c + c))
        if kind == "sq_minus":
            out.add(str(c * c - c))
        if kind == "double_plus":
            out.add(str(2 * c + 1))

    return out or None


def solve_letter_analogy(en):
    """'FG : IJ :: AB : ?' — same per-position shift applied to the third term."""
    m = re.search(r"([A-Z]+)\s*:\s*([A-Z]+)\s*::\s*([A-Z]+)\s*:\s*\?", en)
    if not m:
        return None
    a, b, c = m.groups()
    if not (len(a) == len(b) == len(c)):
        return None
    shifts = [(ord(y) - ord(x)) % 26 for x, y in zip(a, b)]
    return "".join(chr((ord(ch) - 65 + s) % 26 + 65) for ch, s in zip(c, shifts))


def solve_ranking_total(en):
    """'8th from the left and 10th from the right — how many in the row?' -> 8 + 10 - 1."""
    if not re.search(r"how many (students|persons|people|boys|girls)", en, re.I):
        return None
    m = re.search(r"(\d+)(?:st|nd|rd|th)\s+from the left.*?(\d+)(?:st|nd|rd|th)\s+from the right",
                  en, re.I | re.S)
    if not m:
        return None
    return str(int(m.group(1)) + int(m.group(2)) - 1)


# X --r1--> Y --r2--> Z. Siblings share parents, which is what makes the two directions differ:
# a PARENT of one sibling is a parent of the other, but a CHILD of one is a niece/nephew of the
# other. Keyed by (r1 kind, r2 kind) -> relation of X to Z, then gendered by X.
_PARENT, _CHILD, _SIB = "parent", "child", "sib"
_KIND = {"father": (_PARENT, "m"), "mother": (_PARENT, "f"),
         "son": (_CHILD, "m"), "daughter": (_CHILD, "f"),
         "brother": (_SIB, "m"), "sister": (_SIB, "f")}
_COMPOSE = {
    (_PARENT, _SIB): {"m": "father", "f": "mother"},
    (_CHILD, _SIB): {"m": "nephew", "f": "niece"},
    (_SIB, _PARENT): {"m": "uncle", "f": "aunt"},
    (_SIB, _CHILD): {"m": "son", "f": "daughter"},
    (_PARENT, _PARENT): {"m": "grandfather", "f": "grandmother"},
    (_CHILD, _CHILD): {"m": "grandson", "f": "granddaughter"},
    (_CHILD, _PARENT): {"m": "brother", "f": "sister"},
    (_SIB, _SIB): {"m": "brother", "f": "sister"},
}


def solve_blood_relation(en):
    """'X is the daughter of Y, and Y is the sister of Z. How is X related to Z?'"""
    m = re.search(r"\b(\w+)\s+is\s+the\s+(\w+)\s+of\s+(\w+)[,\s]+and\s+\3\s+is\s+the\s+(\w+)\s+of\s+(\w+)",
                  en, re.I)
    if not m:
        return None
    _x, r1, _y, r2, _z = m.groups()
    k1, k2 = _KIND.get(r1.lower()), _KIND.get(r2.lower())
    if not (k1 and k2):
        return None
    rule = _COMPOSE.get((k1[0], k2[0]))
    return rule[k1[1]] if rule else None


SOLVERS += [("letter-series", solve_letter_series), ("number-analogy", solve_number_analogy),
            ("letter-analogy", solve_letter_analogy), ("ranking-total", solve_ranking_total),
            ("blood-relation", solve_blood_relation)]


# ── independent QUANT solvers ───────────────────────────────────────────────────────────────────
# Written from the QUESTION TEXT only, exactly like the reasoning solvers above: they never import
# quantgen. A generated maths question that reaches a paper was previously re-solved only while the
# GENERATORS were being built — coverage on a built paper sat at 44 of 54, so the ten maths
# questions rode on a check that lived outside the paper pipeline. These close that.
#
# Each returns the answer formatted the way the paper prints it, so it can be compared with the
# keyed option directly.
from fractions import Fraction as _F


def _n(x):
    """quantgen's number formatting: whole numbers bare, otherwise two decimals."""
    x = float(x)
    return str(int(x)) if x.is_integer() else str(round(x, 2))


def _rs(x):
    x = float(x)
    return f"Rs. {int(x):,}" if x.is_integer() else f"Rs. {round(x, 2):,}"


def _int(s):
    return int(str(s).replace(",", ""))


def _f(s):
    return _F(str(s).replace(",", ""))


def solve_simple_interest(en):
    m = re.search(r"simple interest on Rs\. ([\d,]+) at (\d+)% per annum for (\d+) years", en)
    if m:
        p, r, t = _int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _rs(p * r * t / 100)
    m = re.search(r"amount is received on Rs\. ([\d,]+) at (\d+)% per annum simple interest "
                  r"after (\d+) years", en)
    if m:
        p, r, t = _int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _rs(p + p * r * t / 100)
    m = re.search(r"sum of Rs\. ([\d,]+) earns Rs\. ([\d,]+) as simple interest in (\d+) years", en)
    if m:
        p, si, t = _int(m.group(1)), _int(m.group(2)), int(m.group(3))
        return _n(_F(si * 100, p * t)) + "%"
    m = re.search(r"sum of Rs\. ([\d,]+) is lent partly at (\d+)% and the rest at (\d+)% per annum "
                  r"simple interest\. If the total interest for one year is Rs\. ([\d,]+)", en)
    if m:
        tot, r1, r2, I = (_int(m.group(i)) for i in (1, 2, 3, 4))
        return _rs(_F(I * 100 - tot * r2, r1 - r2))
    return None


def solve_compound_interest(en):
    m = re.search(r"compound interest on Rs\. ([\d,]+) at (\d+)% per annum for (\d+) years?"
                  r" \(compounded annually\)", en)
    if m:
        p, r = _int(m.group(1)), int(m.group(2))
        return _rs(float(_F(p) * (1 + _F(r, 100)) ** int(m.group(3)) - p))
    m = re.search(r"compound interest and the simple interest on a sum of Rs\. ([\d,]+) at "
                  r"(\d+)% per annum for 2 years", en)
    if m:
        p, r = _int(m.group(1)), int(m.group(2))
        return _rs(float(_F(p) * _F(r, 100) ** 2))
    m = re.search(r"compound interest on Rs\. ([\d,]+) at (\d+)% per annum for 1 year, "
                  r"compounded half-yearly", en)
    if m:
        p, r = _int(m.group(1)), int(m.group(2))
        return _rs(float(_F(p) * (1 + _F(r, 200)) ** 2 - p))
    m = re.search(r"amounts to Rs\. ([\d,.]+) in 2 years at (\d+)% per annum compound interest", en)
    if m:
        amt, r = _f(m.group(1)), int(m.group(2))
        return _rs(float(amt / (1 + _F(r, 100)) ** 2))
    return None


def solve_profit_loss(en):
    m = re.search(r"bought for Rs\. ([\d,]+) and sold at a (profit|loss) of (\d+)%", en)
    if m:
        cp, g, p = _int(m.group(1)), (1 if m.group(2) == "profit" else -1), int(m.group(3))
        return _rs(cp * (100 + g * p) / 100)
    m = re.search(r"By selling an article for Rs\. ([\d,]+), a shopkeeper gains (\d+)%", en)
    if m:
        sp, p = _int(m.group(1)), int(m.group(2))
        return _rs(_F(sp * 100, 100 + p))
    m = re.search(r"marks an article (\d+)% above its cost price of Rs\. ([\d,]+) and then allows "
                  r"a discount of (\d+)%", en)
    if m:
        mu, cp, d = int(m.group(1)), _int(m.group(2)), int(m.group(3))
        mp = cp * (100 + mu) // 100
        sp = mp * (100 - d) // 100
        return _n(_F((sp - cp) * 100, cp)) + "%"
    m = re.search(r"two successive discounts of (\d+)% and (\d+)%", en)
    if m:
        d1, d2 = int(m.group(1)), int(m.group(2))
        return _n(100 - _F((100 - d1) * (100 - d2), 100)) + "%"
    return None


def solve_time_work(en):
    m = re.search(r"A can complete a work in (\d+) days and B can complete it in (\d+) days\. "
                  r"Working together", en)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _n(_F(a * b, a + b)) + " days"
    m = re.search(r"A can do a piece of work in (\d+) days and B in (\d+) days\. A works alone "
                  r"for (\d+) days", en)
    if m:
        a, b, w = (int(m.group(i)) for i in (1, 2, 3))
        return _n((1 - _F(w, a)) * b) + " days"
    m = re.search(r"A, B and C can do a piece of work in (\d+), (\d+) and (\d+) days", en)
    if m:
        a, b, c = (int(m.group(i)) for i in (1, 2, 3))
        return _n(_F(1, _F(1, a) + _F(1, b) + _F(1, c))) + " days"
    m = re.search(r"A and B together can complete a work in ([\d.]+) days\. A alone can do it in "
                  r"(\d+) days", en)
    if m:
        tog, a = _f(m.group(1)), int(m.group(2))
        return _n(_F(1, _F(1, tog) - _F(1, a))) + " days"
    return None


def solve_pipes(en):
    m = re.search(r"Two pipes can fill a tank in (\d+) hours and (\d+) hours", en)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _n(_F(a * b, a + b)) + " hours"
    m = re.search(r"A pipe fills a tank in (\d+) hours while an outlet pipe empties it in "
                  r"(\d+) hours", en)
    if m:
        i, o = int(m.group(1)), int(m.group(2))
        return _n(_F(1, _F(1, i) - _F(1, o))) + " hours"
    m = re.search(r"Two pipes fill a tank in (\d+) hours and (\d+) hours, while a waste pipe "
                  r"empties it in (\d+) hours", en)
    if m:
        a, b, c = (int(m.group(i)) for i in (1, 2, 3))
        return _n(_F(1, _F(1, a) + _F(1, b) - _F(1, c))) + " hours"
    m = re.search(r"fill a tank in (\d+) hours, but because of a leak it takes ([\d.]+) hours", en)
    if m:
        f, wl = int(m.group(1)), _f(m.group(2))
        return _n(_F(1, _F(1, f) - _F(1, wl))) + " hours"
    return None


def solve_averages(en):
    m = re.search(r"Find the average of the numbers ([\d, ]+)\.", en)
    if m:
        nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
        return _n(_F(sum(nums), len(nums)))
    m = re.search(r"average age of (\d+) students is (\d+) years\. When a new student replaces "
                  r"one aged (\d+) years, the average increases by (\d+)", en)
    if m:
        n2, _oa, om, ch = (int(m.group(i)) for i in (1, 2, 3, 4))
        return _n(om + n2 * ch)
    m = re.search(r"average weight of (\d+) boys is (\d+) kg and that of (\d+) girls is (\d+) kg",
                  en)
    if m:
        n1, a1, n2, a2 = (int(m.group(i)) for i in (1, 2, 3, 4))
        return _n(_F(n1 * a1 + n2 * a2, n1 + n2))
    m = re.search(r"average of (\d+) numbers was found to be (\d+)\..*?read as (\d+) instead of "
                  r"(\d+)", en, re.S)
    if m:
        n, wa, mis, act = (int(m.group(i)) for i in (1, 2, 3, 4))
        return _n(_F(n * wa - mis + act, n))
    return None


def solve_ages(en):
    m = re.search(r"ages of A and B are in the ratio (\d+) : (\d+)\. If A is (\d+) years old, "
                  r"what is B's present age", en)
    if m:
        a, b, ageA = (int(m.group(i)) for i in (1, 2, 3))
        return _n(_F(ageA * b, a)) if ageA % a == 0 else None
    m = re.search(r"ages of A and B are in the ratio (\d+) : (\d+)\. If A's present age is (\d+) "
                  r"years, what will be B's age after (\d+) years", en)
    if m:
        a, b, ageA, yrs = (int(m.group(i)) for i in (1, 2, 3, 4))
        return _n(_F(ageA * b, a) + yrs) if ageA % a == 0 else None
    m = re.search(r"(\d+) years ago the ages of A and B were in the ratio (\d+) : (\d+)\. If A is "
                  r"now (\d+) years old, what will B's age be (\d+) years", en)
    if m:
        n, a, b, nowA, m2 = (int(m.group(i)) for i in (1, 2, 3, 4, 5))
        past = nowA - n
        return _n((past // a) * b + n + m2) if past % a == 0 else None
    m = re.search(r"(\d+) years ago the ages of A and B were in the ratio (\d+) : (\d+)\. (\d+) "
                  r"years from now the ratio of their ages will be (\d+) : (\d+)", en)
    if m:
        n1, a, b, n2, p, q = (int(m.group(i)) for i in (1, 2, 3, 4, 5, 6))
        for A in range(n1 + 1, 500):
            if (b * (A - n1)) % a:
                continue
            B = (b * (A - n1)) // a + n1
            if q * (A + n2) == p * (B + n2):
                return _n(A)
    return None


def solve_ratio(en):
    m = re.search(r"amount of Rs\. ([\d,]+) is divided among three people in the ratio (\d+) : "
                  r"(\d+) : (\d+)\. Find the share of the (first|second|third)", en)
    if m:
        tot = _int(m.group(1))
        parts = [int(m.group(i)) for i in (2, 3, 4)]
        who = ["first", "second", "third"].index(m.group(5))
        return _rs(_F(tot * parts[who], sum(parts)))
    m = re.search(r"share an amount in the ratio (\d+) : (\d+)\. If the first receives Rs\. "
                  r"([\d,]+) more than the second", en)
    if m:
        hi_, lo, gap = int(m.group(1)), int(m.group(2)), _int(m.group(3))
        return _rs(_F(gap * (hi_ + lo), hi_ - lo))
    m = re.search(r"A : B = (\d+) : (\d+) and B : C = (\d+) : (\d+), and Rs\. ([\d,]+) is divided",
                  en)
    if m:
        a, b, b2, c2, tot = (int(m.group(i)) for i in (1, 2, 3, 4)), None, None, None, None
        a, b, b2, c2 = (int(m.group(i)) for i in (1, 2, 3, 4))
        tot = _int(m.group(5))
        A, B, C = a * b2, b * b2, b * c2
        g = math.gcd(math.gcd(A, B), C)
        A, B, C = A // g, B // g, C // g
        return _rs(_F(tot * C, A + B + C))
    m = re.search(r"Two numbers are in the ratio (\d+) : (\d+)\. If (\d+) is added to each, the "
                  r"ratio becomes (\d+) : (\d+)", en)
    if m:
        x, y, add, p, q = (int(m.group(i)) for i in (1, 2, 3, 4, 5))
        for k in range(1, 800):
            if q * (x * k + add) == p * (y * k + add):
                return _n(x * k)
    return None


def solve_boats(en):
    m = re.search(r"boat in still water is (\d+) km/hr and the speed of the stream is (\d+) km/hr\."
                  r" How far can the boat travel (downstream|upstream) in (\d+) hours", en)
    if m:
        b, s, dirn, t = int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))
        return f"{(b + s if dirn == 'downstream' else b - s) * t} km"
    m = re.search(r"boat covers (\d+) km/hr downstream and (\d+) km/hr upstream", en)
    if m:
        d, u = int(m.group(1)), int(m.group(2))
        return _n(_F(d + u, 2)) + " km/hr"
    m = re.search(r"boat covers (\d+) km downstream in (\d+) hours and the same distance upstream "
                  r"in ([\d.]+) hours", en)
    if m:
        dist, td, tu = int(m.group(1)), int(m.group(2)), _f(m.group(3))
        return _n((_F(dist, td) - _F(dist, tu)) / 2) + " km/hr"
    m = re.search(r"still water is (\d+) km/hr rows to a place and comes back\. The stream flows "
                  r"at (\d+) km/hr and the whole trip takes ([\d.]+) hours", en)
    if m:
        b, s, tot = int(m.group(1)), int(m.group(2)), _f(m.group(3))
        return _n(tot / (_F(1, b + s) + _F(1, b - s))) + " km"
    return None


def solve_bodmas(en):
    m = re.search(r"value of\s+(.*?)\s*\?", en)
    if not m or "%" not in m.group(1):
        return None
    e = m.group(1)
    if not re.fullmatch(r"[\d\s()x^%+\-/of.]*", e.replace("of", "of")):
        return None
    # On the PAGE the exponent is a <sup> tag, and stripping the tags leaves "(12) 2" with no
    # caret at all — so the caret form never matched anything the paper actually prints, and
    # twelve simplification questions per paper went unread while the harness reported coverage.
    e = re.sub(r"\((\d+)\)\s*\^?\s*2\b", r"(\1**2)", e)
    e = re.sub(r"(\d+)% of (\d+)", r"(_F(\1,100)*\2)", e)
    e = e.replace("x", "*")
    try:
        return _n(eval(e, {"_F": _F, "__builtins__": {}}))
    except Exception:
        return None


SOLVERS += [("simple-interest", solve_simple_interest),
            ("compound-interest", solve_compound_interest),
            ("profit-loss", solve_profit_loss),
            ("time-and-work", solve_time_work),
            ("pipes-cisterns", solve_pipes),
            ("averages", solve_averages),
            ("ages", solve_ages),
            ("ratio", solve_ratio),
            ("boats-streams", solve_boats),
            ("bodmas", solve_bodmas)]


# ── statement-based and match-the-pairs GS ──────────────────────────────────────────────────────
# These re-derive the answer by looking every printed statement back up in the fact TABLES. That
# is independent of the builder in the way that matters: the builder composes a subset, and this
# checks the composition against the data. Importing the facts is not importing the logic.
_GK_TABLES = None


def _gk_tables():
    global _GK_TABLES
    if _GK_TABLES is None:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                               / "question_bank_engine"))
        from qbank import staticgkgen as _G
        from qbank import polity_tables as _P
        from qbank import science_tables as _S
        # The solver must know EVERY table the forms draw from, or it reports "None correct" on a
        # correctly-matched pair — which reads as a wrong key rather than a blind checker.
        _GK_TABLES = {"cap": _G.STATE_CAPITAL, "dance": _G.DANCE_STATE, "river": _G.RIVER_ORIGIN,
                      "article": _P.ARTICLE_SUBJECT, "amendment": _P.AMENDMENT_DID,
                      # Chemistry joins Part II once CHEM_REVIEWED is set. Without it here the
                      # statement solvers return "None correct" on a correctly-keyed chemistry
                      # question, which reads as a wrong key rather than a blind checker.
                      "elem_sym": _S.ELEMENT_SYMBOL, "elem_no": _S.ELEMENT_ATOMIC_NUMBER,
                      "formula": _S.COMPOUND_FORMULA}
    return _GK_TABLES


def _stmt_true(line):
    t = _gk_tables()
    m = re.match(r"(.+?) is the capital of (.+?)\.$", line)
    if m:
        return t["cap"].get(m.group(2)) == m.group(1)
    m = re.match(r"(.+?) is a dance form of (.+?)\.$", line)
    if m:
        return t["dance"].get(m.group(1)) == m.group(2)
    m = re.match(r"The river (.+?) originates at (.+?)\.$", line)
    if m:
        return t["river"].get(m.group(1)) == m.group(2)
    m = re.match(r"Article (.+?) of the Constitution deals with (.+?)\.$", line)
    if m:
        return t["article"].get(m.group(1).strip()) == m.group(2).strip()
    m = re.match(r"The (.+?) Amendment (.+?)\.$", line)
    if m:
        return t["amendment"].get(m.group(1).strip()) == m.group(2).strip()
    m = re.match(r"The chemical symbol of (.+?) is (.+?)\.$", line)
    if m:
        return t["elem_sym"].get(m.group(1).strip()) == m.group(2).strip()
    m = re.match(r"The atomic number of (.+?) is (.+?)\.$", line)
    if m:
        return t["elem_no"].get(m.group(1).strip()) == m.group(2).strip()
    m = re.match(r"The chemical formula of (.+?) is (.+?)\.$", line)
    if m:
        return t["formula"].get(m.group(1).strip()) == m.group(2).strip()
    return None


_SUBSET_NAME = {(True, True, True): "1, 2 and 3", (True, True, False): "1 and 2 only",
                (True, False, True): "1 and 3 only", (False, True, True): "2 and 3 only",
                (True, False, False): "1 only", (False, True, False): "2 only",
                (False, False, True): "3 only", (False, False, False): "None of these"}


def solve_multi_statement(en):
    if "Consider the following statements" not in en:
        return None
    lines = re.findall(r"(?:^|\s)([123])\.\s*(.+?)(?=\s+[123]\.|\s*Which of the statements)",
                       en)
    if len(lines) != 3:
        return None
    truth = tuple(_stmt_true(t.strip()) for _, t in lines)
    return None if None in truth else _SUBSET_NAME[truth]


def solve_match_pairs(en):
    if "Match the following pairs" not in en:
        return None
    t = _gk_tables()
    flat = {}
    for d in t.values():
        flat.update(d)
    rows = re.findall(r"([A-D])\.\s*(.+?)\s+—\s+(.+?)(?=\s+[A-D]\.|\s*Which of the pairs)", en)
    if len(rows) != 4:
        return None
    good = [lab for lab, k, v in rows if flat.get(k.strip()) == v.strip()]
    return ", ".join(good) if good else "None"


SOLVERS += [("gs-multi-statement", solve_multi_statement),
            ("gs-match-pairs", solve_match_pairs)]


# ── independent GENERAL SCIENCE solvers ─────────────────────────────────────────────────────────
# Physics formulas applied to the printed stem. Like the quant solvers, these never import
# sciencegen: the point is to reach the answer by a second route and see whether the printed key
# agrees. Written after the paper's coverage regressed 69/69 -> 64/69 when science questions were
# first wired in and nothing here could read them.

def _sci(x, unit):
    x = float(x)
    return (str(int(x)) if x.is_integer() else str(round(x, 2))) + unit


def solve_science(en):
    m = re.search(r"covers (\d+) m in (\d+) seconds", en)
    if m:
        return _sci(_F(int(m.group(1)), int(m.group(2))), " m/s")
    m = re.search(r"Convert a speed of (\d+) km/h", en)
    if m:
        return _sci(_F(int(m.group(1)) * 5, 18), " m/s")
    m = re.search(r"first half of a journey at (\d+) km/h and the second half at (\d+) km/h", en)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _sci(_F(2 * a * b, a + b), " km/h")
    m = re.search(r"velocity of (\d+) m/s accelerates uniformly at (\d+) m/s. for (\d+) seconds",
                  en)
    if m:
        u, a, t = (int(m.group(i)) for i in (1, 2, 3))
        return _sci(u * t + _F(a * t * t, 2), " m")
    m = re.search(r"current of (\d+) A flows through a resistance of (\d+) ohm", en)
    if m:
        return _sci(int(m.group(1)) * int(m.group(2)), " V")
    m = re.search(r"difference of (\d+) V drives a current of (\d+) A", en)
    if m:
        return _sci(_F(int(m.group(1)), int(m.group(2))), " ohm")
    m = re.search(r"draws (\d+) A at (\d+) V", en)
    if m:
        return _sci(int(m.group(1)) * int(m.group(2)), " W")
    m = re.search(r"resistances of (\d+) ohm and (\d+) ohm .*?SERIES across a (\d+) V", en, re.S)
    if m:
        r1, r2, v = (int(m.group(i)) for i in (1, 2, 3))
        return _sci(_F(v, r1 + r2), " A")
    m = re.search(r"force of (\d+) N moves a body (\d+) m in (\d+) seconds", en)
    if m:
        f_, ss, t = (int(m.group(i)) for i in (1, 2, 3))
        return _sci(_F(f_ * ss, t), " W")
    m = re.search(r"force of (\d+) N moves a body through (\d+) m", en)
    if m:
        return _sci(int(m.group(1)) * int(m.group(2)), " J")
    m = re.search(r"mass (\d+) kg moving with a velocity of (\d+) m/s", en)
    if m:
        mm, v = int(m.group(1)), int(m.group(2))
        return _sci(_F(mm * v * v, 2), " J")
    m = re.search(r"mass (\d+) kg is raised to a height of (\d+) m", en)
    if m:
        return _sci(int(m.group(1)) * 10 * int(m.group(2)), " J")
    return None


SOLVERS += [("general-science", solve_science)]


# ── reasoning forms added when reasoninggen learned difficulty ──────────────────────────────────
# The pre-difficulty solvers answered the question they EXPECTED rather than the one printed: the
# two-position ranking solver ran on the difficulty-4 INTERCHANGE form, and the blood-relation
# solver computed the forward relation on the difficulty-4 REVERSED form. Six questions "failed"
# that were correctly keyed. These handle the new forms, and they are registered BEFORE nothing —
# the dispatch takes the first solver that returns a value, so each of these refuses anything that
# is not its own form.

def solve_ranking_interchange(en):
    m = re.search(r"row of (\d+) students, (\w+) is (\d+)(?:st|nd|rd|th) from the left end\. "
                  r"(\w+) is (\d+)(?:st|nd|rd|th) from the left end\. If .*?interchange", en,
                  re.S)
    if not m or "from the RIGHT end" not in en:
        return None
    total, second = int(m.group(1)), int(m.group(5))
    return str(total - second + 1)          # the first person takes the second's seat


def solve_ranking_between(en):
    m = re.search(r"row of (\d+) students, \w+ is (\d+)(?:st|nd|rd|th) from the left end and "
                  r"\w+ is (\d+)(?:st|nd|rd|th) from the right end\. How many students are "
                  r"sitting between", en, re.S)
    if not m:
        return None
    total, left, right = (int(m.group(i)) for i in (1, 2, 3))
    return str((total - right + 1) - left - 1)


_INVERSE = {"grandfather": "grandson", "grandmother": "granddaughter",
            "grandson": "grandfather", "granddaughter": "grandmother",
            "uncle": "nephew", "aunt": "niece", "nephew": "uncle", "niece": "aunt",
            "father": "son", "mother": "daughter", "brother": "brother", "sister": "sister",
            "son": "father", "daughter": "mother"}
_KIN2 = {("father", "father"): "grandfather", ("father", "mother"): "grandfather",
         ("mother", "father"): "grandmother", ("mother", "mother"): "grandmother",
         ("son", "son"): "grandson", ("son", "daughter"): "grandson",
         ("daughter", "son"): "granddaughter", ("daughter", "daughter"): "granddaughter",
         ("brother", "father"): "uncle", ("brother", "mother"): "uncle",
         ("sister", "father"): "aunt", ("sister", "mother"): "aunt",
         ("father", "brother"): "father", ("father", "sister"): "father",
         ("mother", "brother"): "mother", ("mother", "sister"): "mother",
         ("son", "brother"): "nephew", ("son", "sister"): "nephew",
         ("daughter", "brother"): "niece", ("daughter", "sister"): "niece"}


def solve_blood_relation_chain(en):
    """Compose the stated links, and invert when the question asks the other way round."""
    links = re.findall(r"(\w+) is the (\w+) of (\w+)", en)
    ask = re.search(r"How is (\w+) related to (\w+)\?", en)
    if len(links) < 2 or not ask:
        return None
    who, to = ask.groups()
    rel = {(a, b): r for a, r, b in links}
    chain = [links[0][0]] + [l[2] for l in links]
    cur = rel.get((chain[0], chain[1]))
    for i in range(1, len(chain) - 1):
        cur = _KIN2.get((cur, rel.get((chain[i], chain[i + 1]))))
        if cur is None:
            return None
    if who == chain[0] and to == chain[-1]:
        return cur.capitalize()
    if who == chain[-1] and to == chain[0]:
        inv = _INVERSE.get(cur)
        return inv.capitalize() if inv else None
    return None


SOLVERS = ([("ranking-interchange", solve_ranking_interchange),
            ("ranking-between", solve_ranking_between),
            ("blood-relation-chain", solve_blood_relation_chain)] + SOLVERS)


# ── series and coding variants ──────────────────────────────────────────────────────────────────
# The last twelve generated forms without an independent route. Written from the printed series or
# code alone; both wrap the alphabet mod 26, which is where the first version of each of these got
# it wrong — "L, Q, V, A, ?" is a constant +5 that crosses Z, and a solver that subtracts raw
# ordinals sees the gaps as 5, 5, -21 and gives up.

def solve_series_any(en):
    if "letter series" not in en:
        return None
    ls = re.findall(r"\b([A-Z])\b", en.split("\n")[-1])
    if len(ls) != 4:
        return None
    A = ord("A")
    p = [ord(c) - A for c in ls]
    g = [(p[i + 1] - p[i]) % 26 for i in range(3)]
    if len(set(g)) == 1:                                   # constant step
        return chr((p[3] + g[0]) % 26 + A)
    if g[0] == g[2]:                                       # alternating: next gap is g[1]
        return chr((p[3] + g[1]) % 26 + A)
    if (g[1] - g[0]) == (g[2] - g[1]):                     # step grows by a constant
        return chr((p[3] + g[2] + (g[1] - g[0])) % 26 + A)
    return chr((p[2] + (p[2] - p[0]) % 26) % 26 + A)       # interleaved: continue the odd series


def solve_coding_any(en):
    m = re.search(r"'([A-Z]+)' is written as '([A-Z]+)'.*?'([A-Z]+)'", en, re.S)
    if not m:
        return None
    A = ord("A")
    w1, c1, w2 = m.groups()
    if len(w1) != len(c1):
        return None
    sh = [(ord(b) - ord(a)) % 26 for a, b in zip(w1, c1)]
    if len(set(sh)) == 1:                                              # one shift throughout
        return "".join(chr((ord(c) - A + sh[0]) % 26 + A) for c in w2)
    if sh == [(i + 1) % 26 for i in range(len(w1))]:                   # positional 1,2,3,...
        return "".join(chr((ord(c) - A + i + 1) % 26 + A) for i, c in enumerate(w2))
    rs = [(ord(b) - ord(a)) % 26 for a, b in zip(w1[::-1], c1)]        # reversed, then shifted
    if len(set(rs)) == 1:
        return "".join(chr((ord(c) - A + rs[0]) % 26 + A) for c in w2[::-1])
    odd, even = sh[0::2], sh[1::2]                                     # alternating shifts
    if len(set(odd)) == 1 and len(set(even)) == 1:
        return "".join(chr((ord(c) - A + (odd[0] if i % 2 == 0 else even[0])) % 26 + A)
                       for i, c in enumerate(w2))
    return None


SOLVERS = ([("series-any", solve_series_any),
            ("coding-any", solve_coding_any)] + SOLVERS)


# ── the last two generated forms ────────────────────────────────────────────────────────────────

_DIRV = {"North": (0, 1), "South": (0, -1), "East": (1, 0), "West": (-1, 0)}
_RIGHT_OF = {"North": "East", "East": "South", "South": "West", "West": "North"}


def solve_direction_walk(en):
    """Walk the whole path on a grid — four legs, distance or direction.

    Handles the leg written as "turns right and walks 12 km" with no direction stated: from North
    a right turn is East, and a solver that only reads explicit compass words silently drops that
    leg and reports a wrong distance with no sign anything went missing.
    """
    if " km towards " not in en:
        return None
    x = y = 0
    facing = None
    for m in re.finditer(r"(\d+) km(?:\s+towards\s+(North|South|East|West))?",
                         en.split("?")[0]):
        d = int(m.group(1))
        dirn = m.group(2) or (_RIGHT_OF.get(facing) if facing else None)
        if dirn is None:
            return None
        facing = dirn
        dx, dy = _DIRV[dirn]
        x += dx * d
        y += dy * d
    if "which direction" in en.lower():
        ns = "North" if y > 0 else "South" if y < 0 else ""
        ew = "East" if x > 0 else "West" if x < 0 else ""
        return f"{ns}-{ew}" if ns and ew else (ns or ew or None)
    dist = math.hypot(x, y)
    return f"{int(dist)} km" if dist == int(dist) else None


def solve_number_coding(en):
    """A=1 style letter-to-number coding, including the 'one more' and 'twice' variants."""
    m = re.search(r"each letter is coded by (.+?), how is '([A-Z]+)' coded", en)
    if not m:
        return None
    rule, word = m.group(1), m.group(2)
    if "BACKWARDS from Z" in rule or "counted BACKWARDS" in rule:
        f = lambda n: 27 - n          # Z=1 ... A=26
    elif "one more than" in rule:
        f = lambda n: n + 1
    elif "twice" in rule:
        f = lambda n: n * 2
    elif "its position in the alphabet" in rule:
        f = lambda n: n
    else:
        return None
    return " ".join(str(f(ord(c) - 64)) for c in word)


SOLVERS = ([("direction-walk", solve_direction_walk),
            ("number-coding-rule", solve_number_coding)] + SOLVERS)


# ── static GK recall, and the two-statement form ────────────────────────────────────────────────
# The all-generated draw reached forms the paper had not used before and sixteen arrived with no
# independent route. Both are table lookups.
#
# The first attempt looked up "What is the capital of X?" in STATE_CAPITAL alone — but staticgkgen
# uses that SAME template for COUNTRY_CAPITAL, so every country question was answered from the
# wrong table and 27 correct questions were reported as failures. A checker that returns confident
# wrong answers is worse than one that returns none: it fails good questions and could pass bad
# ones. A template is therefore resolved against EVERY table that renders with it.

_PAIR_NAME = {(True, True): "Both 1 and 2", (True, False): "1 only",
              (False, True): "2 only", (False, False): "Neither 1 nor 2"}
_GK_ALL = None


def _gk_merged():
    global _GK_ALL
    if _GK_ALL is None:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                               / "question_bank_engine"))
        from qbank import staticgkgen as _G

        def merge(*names):
            out = {}
            for n in names:
                out.update(getattr(_G, n, {}) or {})
            return out

        _GK_ALL = {"capital": merge("STATE_CAPITAL", "COUNTRY_CAPITAL"),
                   "dance": merge("DANCE_STATE"),
                   "river": merge("RIVER_ORIGIN"),
                   "instate": merge("PARK_STATE", "LAKE_STATE2", "SANCTUARY_STATE",
                                    "TEMPLE_STATE")}
    return _GK_ALL


def solve_static_gk(en):
    t = _gk_merged()
    for pat, key in ((r"What is the capital of (.+?)\?", "capital"),
                     (r"The classical/folk dance '(.+?)' belongs to which state\?", "dance"),
                     (r"Where does the river (.+?) originate\?", "river"),
                     (r"In which state is (.+?) located\?", "instate")):
        m = re.match(pat, en)
        if m:
            return t[key].get(m.group(1).strip())
    return None


def solve_two_statement(en):
    if "Consider the following statements" not in en:
        return None
    # A three-statement question matches this regex too — it just never sees statement 3, and the
    # length guard cannot tell, because the pattern can only ever find two. Without this it read
    # 3-statement questions as 2-statement ones and reported 22 correct questions as failures.
    if re.search(r"(?:^|\s)3\.\s", en):
        return None                      # the three-statement solver owns that case
    lines = re.findall(r"(?:^|\s)([12])\.\s*(.+?)(?=\s+[12]\.|\s*Which of the statements)", en)
    if len(lines) != 2:
        return None
    truth = tuple(_stmt_true(t.strip()) for _, t in lines)
    return None if None in truth else _PAIR_NAME[truth]


SOLVERS = ([("static-gk", solve_static_gk),
            ("gs-two-statement", solve_two_statement)] + SOLVERS)


# ── खंड (ग): syllogism, seating, coded inequality, calendar, dice ───────────────────────────────
# Five new question families, five new independent routes. Each of these deliberately uses a
# DIFFERENT algorithm from the builder that produced the question, not merely a second copy of the
# same one — a re-implementation of the same idea agrees with itself even when the idea is wrong:
#
#   syllogism     builder reasons about the maximal/minimal model; this ENUMERATES every model
#   seating       builder derives clues from an arrangement; this searches every arrangement
#   inequality    builder composes relations symbolically; this assigns NUMBERS and tests them
#   calendar      builder counts odd days by hand; this uses `datetime`
#   dice          builder deduces by elimination; this tries all 15 pairings of six faces
#
# Where a question could admit more than one answer, these return a SET, so resolve()'s ambiguity
# check sees it. A seating puzzle with two valid arrangements and a dice puzzle with two valid
# pairings are both defects that no structural check can see.

_FOLLOW_OPTS = {(True, False): "Only conclusion I follows",
                (False, True): "Only conclusion II follows",
                (True, True): "Both I and II follow",
                (False, False): "Neither I nor II follows"}

_SYL_SENT = re.compile(r"\b(All|No|Some) ([A-Za-z]+) are (not )?([A-Za-z]+)\.")


def _syl_parse(text):
    """-> [(kind, term_index, term_index)] plus the term registry, in order of appearance."""
    terms, out = [], []
    for kind, x, neg, y in _SYL_SENT.findall(text):
        for t in (x, y):
            if t not in terms:
                terms.append(t)
        k = {"All": "all", "No": "no", "Some": "some_not" if neg else "some"}[kind]
        out.append((k, terms.index(x), terms.index(y)))
    return out, terms


def _syl_holds(model, st):
    kind, x, y = st
    if kind == "all":
        return not any((c >> x & 1) and not (c >> y & 1) for c in model)
    if kind == "no":
        return not any((c >> x & 1) and (c >> y & 1) for c in model)
    if kind == "some":
        return any((c >> x & 1) and (c >> y & 1) for c in model)
    return any((c >> x & 1) and not (c >> y & 1) for c in model)


def solve_syllogism(en):
    """Enumerate EVERY arrangement of the terms; a conclusion follows iff it survives all of them.

    2^(2^k - 1) models — 128 for three terms, 32768 for four. Brute force is affordable here
    because a paper carries a handful of these, and it is the point: the builder reaches its answer
    by an argument about which model is decisive, and an argument can be wrong in a way that
    enumeration cannot.
    """
    m = re.search(r"Statements: (.+?) Conclusions: I\. (.+?) II\. (.+?) Which of the conclusions",
                  en)
    if not m:
        return None
    sts, terms = _syl_parse(m.group(1))
    if not sts:
        return None
    concls = []
    for part in (m.group(2), m.group(3)):
        got = _SYL_SENT.findall(part)
        if len(got) != 1:
            return None
        kind, x, neg, y = got[0]
        if x not in terms or y not in terms:
            return None
        concls.append(({"All": "all", "No": "no",
                        "Some": "some_not" if neg else "some"}[kind],
                       terms.index(x), terms.index(y)))
    k = len(terms)
    if k > 4:
        return None
    cells = list(range(1, 1 << k))
    truth, found = [True, True], False
    for mask in range(1, 1 << len(cells)):
        model = [cells[i] for i in range(len(cells)) if mask >> i & 1]
        if any(not any(c >> t & 1 for c in model) for t in range(k)):
            continue                                    # a term with no members
        if not all(_syl_holds(model, s) for s in sts):
            continue
        found = True
        for i, c in enumerate(concls):
            if not _syl_holds(model, c):
                truth[i] = False
        if not any(truth):
            break                                       # both already refuted
    if not found:
        return None                                     # premises cannot hold together
    return _FOLLOW_OPTS[(truth[0], truth[1])]


# Circular seating: "facing the centre" is the printed convention, so the left hand points
# clockwise and the right hand anticlockwise. Both the builder and this solver apply that same
# stated convention — what is being cross-checked is the ARRANGEMENT, which is where the work is.
def _seat_parse(en):
    m = re.match(r"(.+?) (?:are|is) sitting (in a row|around a circular table facing the centre)\.",
                 en)
    if not m:
        return None
    names = [x.strip() for x in re.split(r",| and ", m.group(1)) if x.strip()]
    circular = m.group(2).startswith("around")
    rest = en[m.end():]
    clues = []
    for p, side in re.findall(r"(\w+) sits at the extreme (left|right) end\.", rest):
        clues.append(("end", p, side))
    for p, k, side in re.findall(r"(\w+) sits (\d+)(?:st|nd|rd|th) from the (left|right) end\.",
                                rest):
        clues.append(("from_end", p, int(k), side))
    for p, side, q in re.findall(r"(\w+) sits immediately to the (left|right) of (\w+)\.", rest):
        clues.append(("next_to", p, q, side))
    for m2 in re.finditer(r"There are exactly (\d+) persons between (\w+) and (\w+)\.", rest):
        clues.append(("between", m2.group(2), m2.group(3), int(m2.group(1))))
    for p, word, side, q in re.findall(r"(\w+) sits (second|third) to the (left|right) of (\w+)\.",
                                       rest):
        clues.append(("nth_of", p, {"second": 2, "third": 3}[word], side, q))
    return names, circular, clues, rest


def _seat_ok(clue, pos, n, circular):
    kind = clue[0]
    if kind == "end":
        _, p, side = clue
        return pos[p] == (0 if side == "left" else n - 1)
    if kind == "from_end":
        _, p, k, side = clue
        return pos[p] == (k - 1 if side == "left" else n - k)
    if kind == "next_to":
        _, p, q, side = clue
        # The two tables do NOT share a convention, and treating them as though they did is what
        # this solver got wrong first time round: in a ROW, "immediately to the right" is the next
        # seat rightwards (+1); around a circle with everyone FACING THE CENTRE, a person's right
        # hand points anticlockwise, so the same words mean the PREVIOUS seat (-1). One sign, 115
        # questions reported as wrongly keyed when the key was right.
        step = (1 if side == "left" else -1) if circular else (-1 if side == "left" else 1)
        return pos[p] == (pos[q] + step) % n if circular else pos[p] == pos[q] + step
    if kind == "between":
        _, p, q, m = clue
        return abs(pos[p] - pos[q]) == m + 1
    _, p, k, side, q = clue
    return pos[p] == (pos[q] + (k if side == "left" else -k)) % n


def solve_seating(en):
    """Search every arrangement of the named people and answer from the ones that fit.

    Returns a SET, so a clue set that leaves two arrangements standing is reported as ambiguous
    rather than silently agreeing with whichever one the builder happened to start from.
    """
    import itertools
    got = _seat_parse(en)
    if not got:
        return None
    names, circular, clues, rest = got
    n = len(names)
    if not clues or n > 8:
        return None
    ask_end = re.search(r"Who is sitting at the extreme (left|right) end\?", rest)
    ask_from = re.search(r"Who is sitting (third|second) from the (left|right) end\?", rest)
    ask_rel = re.search(r"Who sits (second|third) to the (left|right) of (\w+)\?", rest)
    if not (ask_end or ask_from or ask_rel):
        return None
    out = set()
    for perm in itertools.permutations(names):
        pos = {p: i for i, p in enumerate(perm)}
        if not all(_seat_ok(c, pos, n, circular) for c in clues):
            continue
        if ask_end:
            out.add(perm[0] if ask_end.group(1) == "left" else perm[-1])
        elif ask_from:
            k = {"second": 2, "third": 3}[ask_from.group(1)]
            out.add(perm[k - 1] if ask_from.group(2) == "left" else perm[n - k])
        else:
            k = {"second": 2, "third": 3}[ask_rel.group(1)]
            i = pos[ask_rel.group(3)]
            out.add(perm[(i + (k if ask_rel.group(2) == "left" else -k)) % n])
    return out or None


def solve_coded_inequality(en):
    """Assign actual NUMBERS to the letters and see which conclusion survives every assignment.

    The builder reaches its answer by composing relation symbols ('>' after '>=' is '>'); this
    never composes anything. It gives each letter a value from 1..n, keeps the assignments that
    satisfy the statements, and asks whether a conclusion holds in all of them. Any weak ordering
    of n letters is representable in that range, so the search is complete — and it shares no
    reasoning with the code that wrote the question.
    """
    import itertools
    if "Conclusions:" not in en or "means" not in en:
        return None
    legend = {}
    for sym, phrase in re.findall(r"'A (\S+) B' means 'A (is [a-z ]+?) B'", en):
        legend[sym] = {"is greater than": "gt", "is smaller than": "lt", "is equal to": "eq",
                       "is either greater than or equal to": "ge",
                       "is either smaller than or equal to": "le"}.get(phrase.strip())
    if len(legend) < 3 or None in legend.values():
        return None
    m = re.search(r"Statements: (.+?)\. Conclusions: I\. (\S+ \S+ \S+) II\. (\S+ \S+ \S+) ", en)
    if not m:
        return None
    def link(s):
        p = s.strip().split()
        return (p[0], legend.get(p[1]), p[2]) if len(p) == 3 else None
    sts = [link(x) for x in m.group(1).split(",")]
    cs = [link(m.group(2)), link(m.group(3))]
    if any(x is None or x[1] is None for x in sts + cs):
        return None
    letters = []
    for a, _, b in sts + cs:
        for t in (a, b):
            if t not in letters:
                letters.append(t)
    n = len(letters)
    if n > 7:
        return None
    test = {"gt": lambda u, v: u > v, "lt": lambda u, v: u < v, "eq": lambda u, v: u == v,
            "ge": lambda u, v: u >= v, "le": lambda u, v: u <= v}
    truth, found = [True, True], False
    for vals in itertools.product(range(1, n + 1), repeat=n):
        v = dict(zip(letters, vals))
        if not all(test[r](v[a], v[b]) for a, r, b in sts):
            continue
        found = True
        for i, (a, r, b) in enumerate(cs):
            if not test[r](v[a], v[b]):
                truth[i] = False
        if not any(truth):
            break
    if not found:
        return None
    return _FOLLOW_OPTS[(truth[0], truth[1])]


_MONTH_N = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}
_WD = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _date(txt):
    m = re.match(r"(\d{1,2}) ([A-Z][a-z]+) (\d{4})", txt.strip())
    if not m or m.group(2) not in _MONTH_N:
        return None
    import datetime
    try:
        return datetime.date(int(m.group(3)), _MONTH_N[m.group(2)], int(m.group(1)))
    except ValueError:
        return None


def solve_calendar(en):
    """`datetime` against a builder that counts odd days by hand — two different routes to a day."""
    import datetime
    m = re.match(r"Today is (\w+day)\. What day of the week will it be after (\d+) days\?", en)
    if m:
        return _WEEK[(_WEEK.index(m.group(1)) + int(m.group(2))) % 7]
    m = re.match(r"What was/will be the day of the week on (.+?)\?", en)
    if m:
        d = _date(m.group(1))
        return _WD[d.weekday()] if d else None
    m = re.match(r"(.+?) was a (\w+day)\. What day of the week will (.+?) be\?", en)
    if m:
        d0, d1 = _date(m.group(1)), _date(m.group(3))
        if not (d0 and d1) or _WD[d0.weekday()] != m.group(2):
            return None                       # the stated day is wrong — say nothing, fail loudly
        return _WD[d1.weekday()]
    m = re.match(r"Which of the following years will have exactly the same calendar as the year "
                 r"(\d{4})\?", en)
    if m:
        y = int(m.group(1))
        leap = lambda t: t % 4 == 0 and (t % 100 != 0 or t % 400 == 0)
        for t in range(y + 1, y + 100):
            if (datetime.date(t, 1, 1).weekday() == datetime.date(y, 1, 1).weekday()
                    and leap(t) == leap(y)):
                return str(t)
    return None


def solve_dice(en):
    """Try all 15 ways to pair six faces and keep the pairings the statements allow.

    The builder deduces the missing pair by elimination; this never eliminates anything. If more
    than one pairing survives, the answer comes back as a set and the question is reported
    ambiguous — which is the failure elimination cannot see, because elimination assumes the
    pairing it started from.
    """
    if "faces numbered 1 to 6" not in en:
        return None
    opp_facts = [(int(a), int(b)) for a, b in
                 re.findall(r"(\d) is opposite (\d)", en)]
    # Match the NUMBER LIST itself rather than stopping at the first punctuation. A lazy
    # "up to the next comma" read captured only the first face of "1, 2, 5 and 6", so every
    # adjacency question failed its constraint, no pairing survived, and the solver went quiet on
    # three of the four difficulty bands while reporting nothing wrong.
    adj_of = [(int(m.group(1)), [int(x) for x in re.findall(r"\d+", m.group(2))])
              for m in re.finditer(r"faces adjacent to (\d) are "
                                   r"((?:\d+(?:,\s*|\s+and\s+)?)+)", en)]
    ask_one = re.search(r"Which number is on the face opposite to (\d)\?", en)
    ask_sum = re.search(r"SUM of the numbers on the faces opposite to (\d) and (\d)\?", en)
    if not (ask_one or ask_sum) or not (opp_facts or adj_of):
        return None

    def pairings(rest):
        if not rest:
            yield []
            return
        a = rest[0]
        for i in range(1, len(rest)):
            for tail in pairings(rest[1:i] + rest[i + 1:]):
                yield [(a, rest[i])] + tail

    out = set()
    for pr in pairings([1, 2, 3, 4, 5, 6]):
        opp = {}
        for a, b in pr:
            opp[a], opp[b] = b, a
        if any(opp[a] != b for a, b in opp_facts):
            continue
        if any(sorted(x for x in range(1, 7) if x != f and x != opp[f]) != sorted(lst)
               for f, lst in adj_of):
            continue
        out.add(str(opp[int(ask_one.group(1))]) if ask_one else
                str(opp[int(ask_sum.group(1))] + opp[int(ask_sum.group(2))]))
    return out or None


def solve_alnum_series(en):
    """'H5, L7, P8, T10, ?' — a letter component and a number component moving independently.

    solve_letter_series handles this form only when BOTH steps are constant, so the alternating and
    growing number patterns (difficulties 2 and 3 of _b_alnum_series) went unread — four questions
    a paper that the harness reported as coverage rather than as failures. The letter step is
    always constant here, taken mod 26 so a series running BACKWARDS through A is still seen as
    constant; the number step may be constant, alternating, or growing by a fixed amount.
    """
    m = re.search(r"series\?\s*(.+?)\s*\?", en, re.I | re.S)
    if not m:
        return None
    terms = [t for t in re.split(r"[,\s]+", m.group(1)) if re.fullmatch(r"[A-Z]+\d+", t)]
    if len(terms) < 4:
        return None
    heads = [t.rstrip("0123456789") for t in terms]
    nums = [int(t[len(h):]) for t, h in zip(terms, heads)]
    if len({len(h) for h in heads}) != 1:
        return None
    steps = []
    for i in range(len(heads[0])):
        g = {(ord(heads[j + 1][i]) - ord(heads[j][i])) % 26 for j in range(len(heads) - 1)}
        if len(g) != 1:
            return None
        steps.append(g.pop())
    nxt = "".join(chr((ord(heads[-1][i]) - 65 + steps[i]) % 26 + 65)
                  for i in range(len(heads[0])))
    g = [nums[i + 1] - nums[i] for i in range(len(nums) - 1)]
    if len(set(g)) == 1:                                    # constant
        step = g[0]
    elif len(g) >= 3 and g[0] == g[2]:                      # alternating: the next gap is g[1]
        step = g[1]
    elif len(g) >= 3 and (g[1] - g[0]) == (g[2] - g[1]):    # gap grows by a constant
        step = g[-1] + (g[1] - g[0])
    else:
        return None
    return f"{nxt}{nums[-1] + step}"


# ── the four new General Studies styles ─────────────────────────────────────────────────────────
# Same route as the statement solvers above: every claim is looked back up in the fact TABLES, so
# what is checked is the builder's COMPOSITION against the data. Importing the facts is not
# importing the logic — the builder decides which pairs to show and which to falsify, and that is
# exactly what these re-derive.

_PAIR_LINE = re.compile(r"(.+?)\s+—\s+(.+)")


def _pair_true(text):
    """Is 'Kathak — Uttar Pradesh' a real pair? None when the key is not in exactly one table.

    Refusing an ambiguous key rather than taking the first table that has it is the lesson from
    solve_static_gk: looking a capital up in STATE_CAPITAL when the question came from
    COUNTRY_CAPITAL answered 27 correct questions wrongly and reported them as key errors. A
    checker that returns confident wrong answers is worse than one that returns none.
    """
    m = _PAIR_LINE.match(text.strip())
    if not m:
        return None
    k, v = m.group(1).strip(), m.group(2).strip().rstrip(".")
    k = re.sub(r"^Article\s+", "", k)
    found = [t[k] for t in _gk_tables().values() if k in t]
    if not found:
        return None                       # key in no table — refuse rather than guess
    # A key can legitimately live in SEVERAL tables: "Argon" maps to Ar in ELEMENT_SYMBOL and to
    # 18 in ELEMENT_ATOMIC_NUMBER, and BOTH "Argon — Ar" and "Argon — 18" are correctly matched.
    # Requiring exactly one table made the solver refuse every chemistry pair question. OR-ing
    # across the tables is sound here in a way the old COUNTRY_CAPITAL bug was not: that one
    # picked ONE possibly-wrong table and answered confidently, whereas this asks whether the
    # printed pairing appears anywhere, which is exactly what the question means.
    return any(f == v for f in found)


def _solve_pair_pick(en, q_text, want_true):
    """Shared by the correctly/NOT-correctly matched forms. Returns a SET, so a question with two
    true pairs (or two false ones) is reported as ambiguous rather than quietly agreeing."""
    if q_text not in en:
        return None
    opts = _LAST_OPTIONS.get(en)
    if not opts:
        return None
    verdicts = [(o, _pair_true(o)) for o in opts]
    if any(v is None for _, v in verdicts):
        return None
    hits = {o for o, v in verdicts if v is want_true}
    return hits or None


def solve_correct_pair(en):
    return _solve_pair_pick(en, "Which of the following pairs is correctly matched?", True)


def solve_wrong_pair(en):
    return _solve_pair_pick(en, "Which of the following pairs is NOT correctly matched?", False)


def solve_which_statement(en):
    if "Which one of the following statements is correct?" not in en:
        return None
    opts = _LAST_OPTIONS.get(en)
    if not opts:
        return None
    verdicts = [(o, _stmt_true(o.strip().rstrip(".") + ".")) for o in opts]
    if any(v is None for _, v in verdicts):
        return None
    hits = {o for o, v in verdicts if v}
    return hits or None


_COUNT_NAME = {0: "None of them", 1: "Only one", 2: "Only two", 3: "All three"}


def solve_count_statements(en):
    if "How many of the above statements are correct?" not in en:
        return None
    lines = re.findall(r"(?:^|\s)([123])\.\s*(.+?)(?=\s+[123]\.|\s*How many of the above)", en)
    if len(lines) != 3:
        return None
    truth = [_stmt_true(t.strip()) for _, t in lines]
    if None in truth:
        return None
    return _COUNT_NAME[sum(truth)]


# Three of these solvers need the printed OPTIONS, not just the stem, because that is where the
# content lives in the new pair forms. resolve() hands solvers the stem alone, so the options are
# stashed here as each question is read. Keyed on the stem, which is unique within a paper.
_LAST_OPTIONS = {}


# ── symbol substitution and word formation ──────────────────────────────────────────────────────

_OPFN = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
         "×": lambda a, b: a * b, "÷": lambda a, b: a / b}


def _sub_eval(expr, mapping):
    """Substitute, then let PYTHON apply the precedence.

    The builder walks the operators by hand, doing × and ÷ in a first pass. This hands the whole
    thing to Python's own parser instead, so the two only agree if that hand-written walk is
    correct — which is the entire reason for not sharing an evaluator.
    """
    toks = expr.strip().split()
    if len(toks) < 3 or len(toks) % 2 == 0:
        return None
    py = toks[0]
    for i in range(1, len(toks), 2):
        op = mapping.get(toks[i])
        if op is None or not re.fullmatch(r"\d+", toks[i + 1]):
            return None
        py += {"+": "+", "-": "-", "×": "*", "÷": "/"}[op] + f"_F({toks[i + 1]})"
    try:
        return eval(f"_F({py})", {"_F": _F, "__builtins__": {}})
    except Exception:
        return None


def solve_symbol_substitution(en):
    """Returns the value, or — for the 'which equation is correct' form — the set of true ones."""
    legend = dict(re.findall(r"'(\S)' stands for '(\S)'", en))
    if len(legend) != 4:
        return None
    if "which of the following equations is correct" in en:
        opts = _LAST_OPTIONS.get(en)
        if not opts:
            return None
        good = set()
        for o in opts:
            if "=" not in o:
                return None
            lhs, rhs = o.rsplit("=", 1)
            v = _sub_eval(lhs, legend)
            if v is None or not re.fullmatch(r"-?\d+", rhs.strip()):
                return None
            if v == int(rhs.strip()):
                good.add(o)
        return good or None
    m = re.search(r"what is the value of (.+?)\?", en)
    if not m:
        return None
    v = _sub_eval(m.group(1), legend)
    if v is None or v.denominator != 1:
        return None
    return str(v.numerator)


def solve_word_formation(en):
    """Re-derive which option is (not) formable straight from the PRINTED word and options.

    This shares its rule with the builder — letter containment is what "can be formed" means, so
    there is no second definition to reach for. What it independently checks is the COMPOSITION:
    that the word printed on the page is the word the answer was computed against, and that the
    option keyed is the one the printed letters actually single out. That is the step where a
    generator goes wrong, and it returns a SET so an option list with two valid answers is
    reported as ambiguous rather than quietly matched.
    """
    m = re.search(r"select the word which (cannot|can) be formed using the letters of the given "
                  r"word\s*:\s*([A-Z]+)", en)
    if not m:
        return None
    want_can, source = m.group(1) == "can", m.group(2)
    opts = _LAST_OPTIONS.get(en)
    if not opts or not all(re.fullmatch(r"[A-Z]+", o.strip()) for o in opts):
        return None
    src = Counter(source)
    hits = {o for o in opts
            if (all(src[c] >= n for c, n in Counter(o.strip()).items())) is want_can}
    return hits or None


# ── number grid / matrix ────────────────────────────────────────────────────────────────────────
# This one INFERS the rule instead of being told it: it knows nothing about which rule the builder
# used, searches a family, and returns every answer the surviving rules give. That makes it both
# the independent check AND the ambiguity detector — if two simple rules explain the shown columns
# and disagree about the missing one, the set comes back with two members and resolve() reports the
# question as having two defensible answers.
#
# The family here is deliberately WIDER than the builder's. A grid the builder thought unambiguous
# because it only compared its own ten rules can still be read another way by a candidate, and a
# checker that only knows what the generator knows cannot catch that.

_GRID_FAMILY = [
    lambda a, b, c: a + b + c,           lambda a, b, c: a * b + c,
    lambda a, b, c: a * b - c,           lambda a, b, c: b * c - a,
    lambda a, b, c: b * c + a,           lambda a, b, c: a * c - b,
    lambda a, b, c: a * c + b,           lambda a, b, c: a * a + b * b + c * c,
    lambda a, b, c: (a + b) * c,         lambda a, b, c: (a + c) * b,
    lambda a, b, c: (b + c) * a,         lambda a, b, c: a * b * c,
    lambda a, b, c: a + b - c,           lambda a, b, c: a - b + c,
    lambda a, b, c: (a + b + c) * 2,     lambda a, b, c: a * a + b * c,
    lambda a, b, c: (a - b) * c,         lambda a, b, c: (a + b) * c - a,
    lambda a, b, c: a * b + b * c,       lambda a, b, c: (a + b) * (b + c),
]


def _grid_parse(en):
    rows = re.findall(r"Row \d+: ([\d,\s?]+?)(?=\s*Row \d+:|\s*In each column)", en)
    if len(rows) < 3:
        return None
    grid = [[t.strip() for t in r.split(",")] for r in rows]
    if len({len(r) for r in grid}) != 1:
        return None
    return grid


def solve_number_grid(en):
    """Returns the SET of answers every rule consistent with the shown columns produces."""
    if "number arrangement" not in en:
        return None
    grid = _grid_parse(en)
    if not grid:
        return None
    ncol = len(grid[0])
    cols = [[grid[r][c] for r in range(len(grid))] for c in range(ncol)]
    miss = [c for c in cols if "?" in c]
    full = [c for c in cols if "?" not in c]
    if len(miss) != 1 or len(full) < 2:
        return None
    try:
        full = [[int(x) for x in c] for c in full]
        target = [int(x) for x in miss[0] if x != "?"]
    except ValueError:
        return None
    out = set()
    if len(grid) == 4:                                   # three inputs feeding a result row
        for fn in _GRID_FAMILY:
            try:
                if all(fn(*c[:3]) == c[3] for c in full):
                    out.add(str(fn(*target[:3])))
            except Exception:
                continue
    elif len(grid) == 3:                                 # each row built from the ones above
        v1, v2 = target[0], target[1]
        for name, f in (("prod", lambda c: c[0] * c[1]),
                        ("arith", lambda c: 2 * c[1] - c[0]),
                        ("geom", lambda c: (c[1] * c[1] // c[0])
                         if c[0] and c[1] * c[1] % c[0] == 0 else None)):
            if all(f(c) == c[2] for c in full):
                v = f([v1, v2, None])
                if v:
                    out.add(str(v))
    return out or None


# ── the error-spotting FORM ─────────────────────────────────────────────────────────────────────
# An error-spot item embeds the ORIGINAL question inside its stem, which is what makes it checkable
# at all: the ordinary solvers can be pointed at that embedded question and asked for the real
# answer, independently of anything the form did.
#
# What this verifies: that the number shown to the student is genuinely NOT the answer (or, on the
# quarter of items that show the correct value, genuinely IS it) and that the key agrees with which
# of those two situations holds. That is the half that could go wrong silently — a form that showed
# the correct answer while keying a mistake would be unanswerable, and no structural check sees it.
#
# What it does NOT verify: which of the three named mistakes produces the shown number. Doing that
# would mean reimplementing every buggy procedure, i.e. restating the builder. That half rests on
# item_forms.can_error_spot refusing any item whose named mistakes do not land on DISTINCT numbers,
# so the shown number can only have come from one of them. Weaker than the direct forms — stated
# here rather than left for someone to assume otherwise.

_NO_MISTAKE = "There is no mistake — the answer is correct"


def solve_error_spot(en):
    m = re.match(r"A student was asked the following question\. (.+?) "
                 r"The student answered: (.+?)\. "
                 r"Which of the following describes what the student did\?$", en)
    if not m:
        return None
    inner, shown = m.group(1).strip(), m.group(2).strip()
    norm = lambda t: re.sub(r"\s+", "", str(t)).lower().rstrip(".")
    # Word formation is the one embedded question whose ordinary solver needs the ORIGINAL four
    # options, and an error-spot item deliberately does not print them — its options are the four
    # reasons. The claim is still checkable directly: does the shown word actually fit inside the
    # source word's letters, and does that match the direction the question asked for?
    wf = re.search(r"select the word which (cannot|can) be formed using the letters of the given "
                   r"word\s*:\s*([A-Z]+)", inner)
    if wf and re.fullmatch(r"[A-Z]+", shown):
        src = Counter(wf.group(2))
        fits = all(src[c] >= n for c, n in Counter(shown).items())
        return _NO_MISTAKE if fits == (wf.group(1) == "can") else {"__NOT__" + _NO_MISTAKE}
    # Same situation for the symbol-substitution "which equation is correct" form: the four
    # candidate equations are not reprinted, so solve_symbol_substitution has nothing to read. But
    # the value shown to the student IS an equation, so it can be checked on its own — substitute
    # and evaluate its left side, compare with its right.
    legend = dict(re.findall(r"'(\S)' stands for '(\S)'", inner))
    if (len(legend) == 4 and "which of the following equations is correct" in inner
            and "=" in shown):
        lhs, rhs = shown.rsplit("=", 1)
        v = _sub_eval(lhs, legend)
        if v is None or not re.fullmatch(r"-?\d+", rhs.strip()):
            return None
        return _NO_MISTAKE if v == int(rhs.strip()) else {"__NOT__" + _NO_MISTAKE}
    real = None
    for name, fn in SOLVERS:
        if name == "error-spot":
            continue
        try:
            got = fn(inner)
        except Exception:
            got = None
        if got:
            real = got if isinstance(got, set) else {got}
            break
    if not real:
        return None                       # cannot re-solve the embedded question — say nothing
    shown_is_right = any(norm(r) == norm(shown) for r in real)
    # We can only name the answer when the shown value IS correct; otherwise all we can say is
    # that the key must NOT be the no-mistake option, which resolve() checks by comparison.
    return _NO_MISTAKE if shown_is_right else {"__NOT__" + _NO_MISTAKE}


def solve_number_series(en):
    """Infer a numeric series' rule from the printed terms and continue it.

    Returns a SET of every continuation a simple rule supports, so a series two different patterns
    explain differently comes back ambiguous rather than quietly matched. Written from the numbers
    alone — it never consults quantgen.
    """
    m = re.search(r"place of the question mark \(\?\) in the following series\?\s*(.+)", en)
    if not m:
        return None
    t = [int(x) for x in re.findall(r"-?\d+", m.group(1).split("?")[0])]
    if len(t) < 3:
        return None
    out = set()
    d1 = [t[i + 1] - t[i] for i in range(len(t) - 1)]
    if len(set(d1)) == 1:
        out.add(str(t[-1] + d1[0]))                                    # arithmetic
    if all(x for x in t[:-1]) and len({_F(t[i + 1], t[i]) for i in range(len(t) - 1)}) == 1:
        out.add(str(int(t[-1] * _F(t[1], t[0]))))                       # geometric
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]
    if len(d2) >= 2 and len(set(d2)) == 1:
        out.add(str(t[-1] + d1[-1] + d2[0]))                           # 2nd difference constant
    if len(d1) >= 2 and all(d1[i] for i in range(len(d1) - 1)) and \
            len({_F(d1[i + 1], d1[i]) for i in range(len(d1) - 1)}) == 1:
        out.add(str(int(t[-1] + d1[-1] * _F(d1[1], d1[0]))))            # the GAPS multiply
    for k in (2, 3, 4, 5):                                             # t*k + c
        cs = {t[i + 1] - k * t[i] for i in range(len(t) - 1)}
        if len(cs) == 1:
            out.add(str(k * t[-1] + cs.pop()))
    for k in (2, 3, 4):                                                # t*k - i, gaps by index
        if all(t[i + 1] == k * t[i] - (i + 1) for i in range(len(t) - 1)):
            out.add(str(k * t[-1] - len(t)))
    if all(d1[i] == (i + 1) ** 2 for i in range(len(d1))):             # gaps are squares
        out.add(str(t[-1] + len(t) ** 2))
    if all(d1[i] == (i + 1) ** 3 for i in range(len(d1))):
        out.add(str(t[-1] + len(t) ** 3))
    return out or None


def solve_percentage(en):
    """The three percentage templates, computed with exact fractions."""
    m = re.match(r"What is (\d+)% of (\d+)\?$", en)
    if m:
        return _n(_F(int(m.group(1)) * int(m.group(2)), 100))
    m = re.match(r"(\d+) is what percent of (\d+)\?$", en)
    if m:
        return _n(_F(int(m.group(1)) * 100, int(m.group(2)))) + "%"
    m = re.match(r"The value (\d+) is first increased by (\d+)% and then the result is "
                 r"decreased by (\d+)%\. What is the final value\?$", en)
    if m:
        v, up, dn = (int(x) for x in m.groups())
        return _n(_F(v) * _F(100 + up, 100) * _F(100 - dn, 100))
    return None


SOLVERS = ([("number-series", solve_number_series),
            ("percentage", solve_percentage),
            ("error-spot", solve_error_spot),
            ("number-grid", solve_number_grid),
            ("symbol-substitution", solve_symbol_substitution),
            ("word-formation", solve_word_formation),
            ("gs-correct-pair", solve_correct_pair),
            ("gs-wrong-pair", solve_wrong_pair),
            ("gs-which-statement", solve_which_statement),
            ("gs-count-statements", solve_count_statements),
            ("alphanumeric-series", solve_alnum_series),
            ("syllogism", solve_syllogism),
            ("seating-arrangement", solve_seating),
            ("coded-inequality", solve_coded_inequality),
            ("calendar", solve_calendar),
            ("dice", solve_dice)] + SOLVERS)


if __name__ == "__main__":
    sys.exit(main())
