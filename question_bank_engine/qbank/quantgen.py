"""COMPUTE-THE-ANSWER quant engine — the deterministic generator for Banking-exam
Quantitative Aptitude (IBPS/SBI/RRB shared Prelims pattern).

The banking analog of qbank.figuregen: instead of asking an LLM to author a question and
GUESS its answer (unreliable — the whole point of the verify loop), we PARAMETRICALLY build
an exam-authentic quant question and COMPUTE its answer in plain Python. The question is
exam-shaped because we templated it from real banking patterns; the answer is correct because
Python computed it — so it is impossible to serve a wrong key, it is copyright-clean (our own
numbers), and it is UNLIMITED (fresh numbers every call).

Live path: generator.generate_test() routes here when can_generate() covers the (exam,
subject) — bypassing the LLM/RAG path entirely, so banking works with ZERO ingested data.

Each chapter maps to one or more builders. A builder(rng, diff) returns a dict:
  {stem, correct, distractors, solution, [options], [concept]}
where `correct` and each distractor are already-formatted option strings (same units), and
answers are held EXACT (Fraction / int) internally, only formatted at the end.
"""
import hashlib
import math
import random
from fractions import Fraction

from .models import Question, content_hash

SUBJECT = "Quantitative Aptitude"
EXAM = "Banking Prelims"


def can_generate(exam, subject, chapter=None) -> bool:
    """True when the compute-the-answer engine covers this (subject, chapter). Banking quant
    is entirely generator-served, so every chapter in the taxonomy is coverable."""
    if (subject or "").strip().lower() not in ("quantitative aptitude", "quant"):
        return False
    if not chapter:
        return True
    return chapter in _CHAP_BUILDERS


# ---- formatting helpers -----------------------------------------------------

def _rupees(x) -> str:
    x = int(x) if float(x).is_integer() else round(float(x), 2)
    return f"Rs. {x:,}"

def _num(x) -> str:
    if isinstance(x, Fraction):
        x = float(x)
    return str(int(x)) if float(x).is_integer() else str(round(float(x), 2))

def _pct(x) -> str:
    return f"{_num(x)}%"

def _frac(f: Fraction) -> str:
    f = Fraction(f).limit_denominator(10000)
    return f"{f.numerator}/{f.denominator}"



# ---- Hindi -------------------------------------------------------------------
# NOT translation. The builder COMPUTES the answer, so the Hindi is a second template over the
# same computation and a number physically cannot drift between the two languages the way it can
# in a translated bank. This is the same argument that makes the English side trustworthy.

def _ru_hi(x) -> str:
    x = int(x) if float(x).is_integer() else round(float(x), 2)
    return f"रु. {x:,}"


_UNIT_HI = [("km/hr", "किमी/घंटा"), ("hours", "घंटे"), ("hour", "घंटा"), ("days", "दिन"),
            ("day", "दिन"), ("years", "वर्ष"), ("year", "वर्ष"), ("km", "किमी"), ("kg", "किग्रा"),
            ("Rs. ", "रु. ")]


def hi_text(t):
    """An option string in Hindi. Numerals stay Arabic — that is how the commission prints them
    in its own Hindi papers, and changing them would make the two halves disagree on sight."""
    t = str(t)
    for en, hi in _UNIT_HI:
        t = t.replace(en, hi)
    return t


def hi_options(options):
    return [{"label": o["label"], "text": hi_text(o["text"])} for o in options]


# ---- MCQ assembly -----------------------------------------------------------

def _perturb(values, want, rng):
    """Produce fresh numeric distractors near the existing ones until we have `want` distinct
    option strings (used only to top up when a builder gives too few)."""
    have = list(dict.fromkeys(values))
    nums = []
    for v in have:
        try:
            nums.append(float(str(v).replace("Rs.", "").replace(",", "").replace("%", "").strip()))
        except ValueError:
            nums.append(None)
    base = next((n for n in nums if n is not None), 10.0)
    tmpl = str(have[0])
    def render(n):
        n = int(n) if float(n).is_integer() else round(n, 2)
        if "Rs." in tmpl:
            return _rupees(n)
        if "%" in tmpl:
            return _pct(n)
        return _num(n)
    step = max(1.0, abs(base) * 0.1)
    k = 1
    while len(have) < want and k < 60:
        for cand in (base + k * step, base - k * step):
            s = render(cand)
            if cand > 0 and s not in have:
                have.append(s)
                if len(have) >= want:
                    break
        k += 1
    return have


def mistakes(*pairs):
    """Distractors COMPUTED BY MAKING A MISTAKE, each labelled with the mistake it represents.

    Why this exists. A question is hard mostly because its wrong answers are attractive, and the
    attractive wrong answer is the one you get by doing something plausible and wrong — adding the
    two times instead of adding the rates, taking the discount on the selling price, forgetting to
    subtract the principal. Distractors invented by nudging the right answer ("ans + 5") are not
    attractive to anyone: the question can be solved by elimination without doing the work.

    Measured across our own bank of 1,427 official questions, the option spread FALLS as difficulty
    rises — 1.28 at difficulty 1, 1.00 at 2, 0.80 at 3. Hard questions keep their options close
    together, which is exactly what an error-derived distractor does for free.

    The label is not decoration. Once a student sits the paper, "picked C" stops meaning "got it
    wrong" and starts meaning "applied simple interest to a compound-interest question" — which is
    the difference between a score and a diagnosis.

    Usage:  "mistakes": mistakes(("added the times instead of the rates", _num(a + b) + " days"),
                                 ("took the average of the two times",    _num(avg) + " days"))
    """
    out = []
    for why, value in pairs:
        if value is not None and str(value).strip():
            out.append({"why": why, "text": str(value)})
    return out


def _mcq(seed: str, correct: str, distractors, rng, n: int = 4, fixed=None):
    """Build n options. If `fixed` (a full ordered option list) is given, use it as-is (for
    quadratic relation questions); else assemble correct + distractors, dedup, pad, and rotate
    so the answer isn't always in the same slot."""
    labels = ["A", "B", "C", "D", "E", "F"][:n]
    if fixed:
        opts = list(fixed)[:n]
    else:
        opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))
        if len(opts) < n:
            opts = list(dict.fromkeys(_perturb(opts, n, rng)))
        opts = opts[:n]
        if str(correct) not in opts:            # correct got truncated — force it in
            opts[-1] = str(correct)
        rot = sum(map(ord, seed)) % n
        opts = opts[rot:] + opts[:rot]
    options = [{"label": l, "text": t} for l, t in zip(labels, opts)]
    ans = labels[opts.index(str(correct))]
    return options, ans


def _make_question(built: dict, rng, spec) -> Question:
    stem = built["stem"].strip()
    n_opts = len(built["options"]) if built.get("options") else 4
    # Error-derived distractors win over hand-nudged ones when a builder supplies them.
    mis = built.get("mistakes") or []
    # A "mistake" that lands ON the correct answer is not a distractor — it means this particular
    # set of numbers rewards a wrong method, so a student who adds the two times instead of the
    # rates scores the mark and learns the wrong lesson. Measured at 9 of 920 builder calls. Drop
    # the option (the pad fills the slot) and flag the question so a paper can refuse to use it.
    collided = [m for m in mis if m["text"] == str(built["correct"])]
    mis = [m for m in mis if m["text"] != str(built["correct"])]
    options, ans = _mcq(stem, built["correct"],
                        [m["text"] for m in mis] or built.get("distractors", []),
                        rng, n=n_opts, fixed=built.get("options"))
    diff = spec.get("dmax") or spec.get("dmin") or 2
    qid = "gen_bankq_" + hashlib.md5(
        (spec.get("chapter", "") + "|" + stem).encode()).hexdigest()[:14]
    q = Question(
        id=qid, exam=spec.get("exam") or EXAM, subject=spec.get("subject") or SUBJECT,
        stem=stem, qtype="MCQ_single", options=options, correct_answer=ans,
        solution=built.get("solution", ""),
        chapter=spec.get("chapter"), concept=built.get("concept"), difficulty=diff,
        stem_hi=built.get("stem_hi", ""), solution_hi=built.get("solution_hi", ""),
        options_hi=hi_options(options) if built.get("stem_hi") else [],
        source="quantgen", generated=True, hash=content_hash(stem))
    q.verified = True
    # label -> the mistake that lands on that option, for per-option diagnosis later
    by_text = {m["text"]: m["why"] for m in mis}
    q.distractor_why = {o["label"]: by_text[o["text"]]
                        for o in options if o["text"] in by_text}
    q.rewards_a_wrong_method = [m["why"] for m in collided]
    return q


# ---- number helpers ---------------------------------------------------------

def _mult(rng, lo, hi, base):
    """A multiple of `base` in [lo*base, hi*base] — keeps answers clean/whole."""
    return base * rng.randint(lo, hi)


# =============================================================================
# BUILDERS  — each returns a dict {stem, correct, distractors, solution, concept}
# =============================================================================

# ---- Simplification & Approximation ----------------------------------------

def _b_simplify(rng, diff):
    """BODMAS. Difficulty = how many operations, and whether the order can be got wrong.

    diff 1  two operations, no precedence trap
    diff 2  three operations including a square and a percentage
    diff 3  four operations with a division that must be done before the addition
    diff 4+ a bracket to resolve first, so left-to-right gives a different answer
    """
    r = rng.choice([7, 8, 9, 11, 12, 13, 14, 15])
    sq = r * r
    p_ = rng.choice([10, 15, 20, 25, 40])
    q = _mult(rng, 4, 12, 20)
    part = p_ * q // 100
    m, n = rng.randint(6, 15), rng.randint(3, 9)
    prod = m * n
    if diff <= 1:
        ans = sq + part
        stem = f"What is the value of  ({r})^2 + {p_}% of {q} ?"
        sol = f"({r})^2 = {sq}; {p_}% of {q} = {part}. So {sq} + {part} = {ans}."
        d = mistakes(("doubled r instead of squaring it", _num(2 * r + part)),
                     ("read the percentage as a plain subtraction of the percent", _num(sq + p_)),
                     ("subtracted the percentage instead of adding it", _num(sq - part)))
        return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
                "concept": "Simplification (BODMAS)"}
    if diff == 2:
        ans = sq + part - prod
        stem = f"What is the value of  ({r})^2 + {p_}% of {q} - {m} x {n} ?"
        sol = (f"({r})^2 = {sq}; {p_}% of {q} = {part}; {m} x {n} = {prod}. "
               f"So {sq} + {part} - {prod} = {ans}.")
        d = mistakes(
            ("worked strictly left to right, multiplying the running total by n",
             _num((sq + part - m) * n)),
            ("read the percentage as a subtraction of the percent itself", _num(sq + p_ - prod)),
            ("dropped the minus sign and added the product", _num(sq + part + prod)))
        return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
                "concept": "Simplification (BODMAS)"}
    if diff == 3:
        dvd = m * n * rng.randint(2, 4)
        ans = sq + Fraction(dvd, n) - part
        stem = f"What is the value of  ({r})^2 + {dvd} / {n} - {p_}% of {q} ?"
        sol = (f"({r})^2 = {sq}; {dvd}/{n} = {_num(Fraction(dvd, n))}; {p_}% of {q} = {part}. "
               f"So {sq} + {_num(Fraction(dvd, n))} - {part} = {_num(ans)}.")
        d = mistakes(("added before dividing, i.e. ({} + {})/{}".format(sq, dvd, n),
                      _num(Fraction(sq + dvd, n) - part)),
                     ("added the percentage instead of subtracting it",
                      _num(sq + Fraction(dvd, n) + part)),
                     ("divided by the percentage figure instead of by n",
                      _num(sq + Fraction(dvd, p_) - part)))
        return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
                "concept": "Simplification (BODMAS)"}
    # diff 4+ : a bracket, so left-to-right and correct order disagree
    k = rng.randint(3, 9)
    ans = sq - (prod - k) // 1 + part
    stem = f"What is the value of  ({r})^2 - ({m} x {n} - {k}) + {p_}% of {q} ?"
    sol = (f"Bracket first: {m} x {n} - {k} = {prod - k}. Then ({r})^2 = {sq} and "
           f"{p_}% of {q} = {part}. So {sq} - {prod - k} + {part} = {_num(ans)}.")
    d = mistakes(("ignored the bracket and subtracted only the product",
                  _num(sq - prod + part)),
                 ("subtracted the bracket's contents term by term, flipping the minus on k",
                  _num(sq - prod - k + part)),
                 ("resolved the bracket but then subtracted the percentage",
                  _num(sq - (prod - k) - part)))
    return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
            "concept": "Simplification (BODMAS)"}

def _b_approx(rng, diff):
    a = round(rng.uniform(24.6, 25.4), 2)           # ~25%
    b = round(rng.randint(38, 82) * 10 + rng.uniform(-0.4, 0.4), 2)
    c = round(rng.uniform(14.6, 15.4), 2)
    e = round(rng.uniform(3.6, 4.4), 2)
    val = a / 100 * b + c * e
    ans = round(val)
    stem = (f"What approximate value will come in place of the question mark?\n"
            f"{a}% of {b} + {c} x {e} = ?")
    sol = (f"~25% of ~{round(b)} ≈ {round(0.25*round(b))}; ~{round(c)} x ~{round(e)} "
           f"≈ {round(c)*round(e)}. Sum ≈ {ans}.")
    d = [_num(ans + rng.choice([10, 12, 15])), _num(ans - rng.choice([8, 11, 14])),
         _num(ans + rng.choice([20, 24]))]
    return {"stem": stem, "correct": _num(ans), "distractors": d, "solution": sol,
            "concept": "Approximation"}

# ---- Number Series ----------------------------------------------------------

def _series_seq(rng, diff):
    """Return (list_of_terms, description) for a valid banking-style series of 6 terms."""
    kind = rng.choice(["arith2", "geom", "sqk", "muladd", "diffinc"])
    if kind == "arith2":                            # +d, common difference
        a, d = rng.randint(3, 12), rng.choice([3, 4, 5, 6, 7])
        seq = [a + i * d for i in range(6)]
        desc = f"add {d} each time"
    elif kind == "geom":                            # x r
        a, r = rng.randint(2, 5), rng.choice([2, 3])
        seq = [a * r ** i for i in range(6)]
        desc = f"multiply by {r} each time"
    elif kind == "sqk":                             # n^2 + k
        k = rng.choice([0, 1, 2, -1])
        start = rng.randint(2, 4)
        seq = [(start + i) ** 2 + k for i in range(6)]
        desc = f"consecutive squares {'+' if k>=0 else ''}{k}"
    elif kind == "muladd":                           # x m + c
        a, m, c = rng.randint(2, 5), 2, rng.choice([1, 2, 3])
        seq = [a]
        for _ in range(5):
            seq.append(seq[-1] * m + c)
        desc = f"x {m} then + {c}"
    else:                                            # diffinc: +2,+4,+6,...
        a, step = rng.randint(3, 10), rng.choice([2, 3])
        seq, add = [a], step
        for _ in range(5):
            seq.append(seq[-1] + add)
            add += step
        desc = f"differences increase by {step}"
    return seq, desc

def _b_series_missing(rng, diff):
    seq, desc = _series_seq(rng, diff)
    ans = seq[-1]
    shown = ", ".join(str(x) for x in seq[:-1]) + ", ?"
    stem = (f"What will come in place of the question mark (?) in the following series?\n"
            f"{shown}")
    sol = f"Pattern: {desc}. So the next term is {ans}."
    d = [_num(ans + (seq[-1] - seq[-2])), _num(ans - (seq[-1] - seq[-2])), _num(ans + 2)]
    return {"stem": stem, "correct": _num(ans), "distractors": d, "solution": sol,
            "concept": "Missing-Term Series"}

def _b_series_wrong(rng, diff):
    seq, desc = _series_seq(rng, diff)
    bad_i = rng.randint(1, 4)                        # never corrupt first term
    delta = rng.choice([-3, -2, 2, 3, 4])
    shown_vals = list(seq)
    shown_vals[bad_i] = seq[bad_i] + delta
    correct = str(shown_vals[bad_i])                # the wrong term (the answer they must spot)
    shown = ", ".join(str(x) for x in shown_vals)
    stem = (f"Find the WRONG term in the following number series:\n{shown}")
    sol = (f"The correct pattern is: {desc}. The term should be {seq[bad_i]}, "
           f"but {shown_vals[bad_i]} is given — so {shown_vals[bad_i]} is the wrong term.")
    # distractors = other SHOWN terms (clean integers); the true-pattern value is a good trap
    d = [str(seq[bad_i])] + [str(shown_vals[j]) for j in (bad_i - 1, bad_i + 1, 0, 5)
                             if 0 <= j < 6 and j != bad_i]
    d = [x for x in dict.fromkeys(d) if x != correct][:3]
    return {"stem": stem, "correct": correct, "distractors": d, "solution": sol,
            "concept": "Wrong-Term Series"}

# ---- Quadratic Equations (x vs y) ------------------------------------------

def _quad_from_roots(rng, r1, r2):
    """x^2 - (r1+r2)x + r1 r2 = 0 → coefficients with sign words for the stem."""
    b = -(r1 + r2)
    c = r1 * r2
    def term(coef, var):
        if coef == 0:
            return ""
        sign = "+" if coef > 0 else "-"
        mag = abs(coef)
        magpart = "" if (mag == 1 and var) else str(mag)
        return f" {sign} {magpart}{var}"
    s = f"{'x' if False else ''}"
    body = f"{'x²' if False else 'x^2'}" + term(b, "x") + term(c, "")
    return body.strip()

def _b_quadratic(rng, diff):
    xr = sorted([rng.randint(1, 9), rng.randint(1, 9)])
    yr = sorted([rng.randint(1, 9), rng.randint(1, 9)])
    eqx = _quad_from_roots(rng, xr[0], xr[1]).replace("x^2", "x^2")
    eqy = _quad_from_roots(rng, yr[0], yr[1]).replace("x", "y").replace("y^2", "y^2")
    # relation
    xmin, xmax, ymin, ymax = xr[0], xr[1], yr[0], yr[1]
    if xmin > ymax:
        rel = "x > y"
    elif xmax < ymin:
        rel = "x < y"
    elif xmin >= ymax:
        rel = "x ≥ y"
    elif xmax <= ymin:
        rel = "x ≤ y"
    elif xr == yr:
        rel = "x = y or relation cannot be established"
    else:
        rel = "x = y or relation cannot be established"
    opts = ["x > y", "x < y", "x ≥ y", "x ≤ y", "x = y or relation cannot be established"]
    stem = (f"In each of the following two equations are given. Solve them and find the "
            f"relation between x and y.\nI.  {eqx} = 0\nII. {eqy} = 0")
    sol = (f"Equation I roots: x = {xr[0]}, {xr[1]}. Equation II roots: y = {yr[0]}, {yr[1]}. "
           f"Comparing all values gives: {rel}.")
    return {"stem": stem, "correct": rel, "options": opts, "solution": sol,
            "concept": "x vs y Comparison"}

# ---- Data Interpretation (no figure — table rendered inline as text) --------

def _b_di_table(rng, diff):
    items = rng.sample(["A", "B", "C", "D", "E"], 3)
    # multiples of 20 so every pct in {40,50,60,75,80}% of the count is a whole number
    prod = {it: _mult(rng, 10, 30, 20) for it in items}          # units produced
    sold_pct = {it: rng.choice([40, 50, 60, 75, 80]) for it in items}
    rows = "\n".join(f"  {it:<3} |   {prod[it]:>4}    |   {sold_pct[it]}%"
                     for it in items)
    table = ("Study the table and answer the question.\n"
             "Item | Produced | Sold (%)\n" + rows)
    target = rng.choice(items)
    sold = prod[target] * sold_pct[target] // 100
    stem = (f"{table}\n\nHow many units of item {target} were SOLD?")
    sol = (f"Item {target}: produced = {prod[target]}, sold% = {sold_pct[target]}%. "
           f"Sold = {sold_pct[target]}% of {prod[target]} = {sold}.")
    unsold = prod[target] - sold
    d = [_num(unsold), _num(prod[target]), _num(sold + prod[target] // 10)]
    return {"stem": stem, "correct": _num(sold), "distractors": d, "solution": sol,
            "concept": "Tabular DI"}

def _b_di_caselet(rng, diff):
    a, b = rng.choice([(3, 2), (5, 3), (7, 5), (4, 1)])
    unit = rng.randint(20, 70)
    total = (a + b) * unit                                      # divisible by (a+b) → clean split
    partA = a * unit
    partB = b * unit
    ctx = rng.choice([("a company", "employees", "male", "female"),
                      ("a college", "students", "boys", "girls")])
    place, unit, g1, g2 = ctx
    stem = (f"In {place} there are {total} {unit}. The ratio of {g1} to {g2} is {a} : {b}. "
            f"How many {g2} are there?")
    sol = (f"{g2} = {b}/({a}+{b}) x {total} = {b}/{a+b} x {total} = {partB}.")
    d = [_num(partA), _num(total - partB - 5 if total - partB - 5 > 0 else partB + 5),
         _num(partB + 10)]
    return {"stem": stem, "correct": _num(partB), "distractors": d, "solution": sol,
            "concept": "Caselet DI"}

# ---- Percentage -------------------------------------------------------------

def _b_percentage(rng, diff):
    mode = rng.choice(["of", "isWhat", "netchange"])
    if mode == "of":
        p = rng.choice([12, 15, 18, 24, 35, 45])
        n = _mult(rng, 4, 15, 100)
        ans = p * n // 100
        stem = f"What is {p}% of {n}?"
        sol = f"{p}% of {n} = {p}/100 x {n} = {ans}."
        d = [_num(ans + n // 10), _num(ans - n // 20), _num((p + 10) * n // 100)]  # noqa: E501
        return {"stem": stem, "correct": _num(ans), "distractors": d, "solution": sol,
                "concept": "Percentage of a Number"}
    if mode == "isWhat":
        b = _mult(rng, 4, 12, 50)
        a = b * rng.choice([20, 25, 40, 60, 75]) // 100
        pct = Fraction(a * 100, b)
        stem = f"{a} is what percent of {b}?"
        sol = f"Required % = ({a}/{b}) x 100 = {_num(pct)}%."
        d = [_pct(float(pct) + 5), _pct(float(pct) - 5), _pct(float(pct) * 2)]
        return {"stem": stem, "correct": _pct(pct), "distractors": d, "solution": sol,
                "concept": "Percentage of a Number"}
    n = _mult(rng, 4, 12, 100)
    up, dn = rng.choice([20, 25, 30]), rng.choice([10, 20, 25])
    after_up = Fraction(n * (100 + up), 100)                    # exact
    final = after_up * Fraction(100 - dn, 100)                  # exact (may be a decimal)
    stem = (f"The value {n} is first increased by {up}% and then the result is decreased "
            f"by {dn}%. What is the final value?")
    sol = (f"After +{up}%: {n} x {100+up}/100 = {_num(after_up)}. "
           f"After -{dn}%: x {100-dn}/100 = {_num(final)}.")
    d = [_num(Fraction(n * (100 + up - dn), 100)), _num(n), _num(float(final) + n // 10)]
    return {"stem": stem, "correct": _num(final), "distractors": d, "solution": sol,
            "concept": "Percentage Change"}

# ---- Profit, Loss & Discount ------------------------------------------------

def _b_profit_loss(rng, diff):
    """Profit and loss. Difficulty = how many prices sit between the given and the asked.

    diff 1  CP and % given          -> SP
    diff 2  SP and % given          -> CP. Reversed, and the classic error (taking the percentage
                                       of the SP instead of the CP) is a real option.
    diff 3  MP, discount and profit -> the profit percent actually earned. Two prices to move
                                       through, and the discount is on MP while the profit is on CP.
    diff 4+ two successive discounts, then find the single equivalent discount, or the CP that
            would yield a target profit after them.
    """
    if diff <= 1:
        cp = _mult(rng, 4, 20, 100)
        pct = rng.choice([10, 12, 15, 20, 25])
        gain = rng.choice([1, -1])
        sp = cp * (100 + gain * pct) // 100
        word = "profit" if gain > 0 else "loss"
        word_hi = "लाभ" if gain > 0 else "हानि"
        stem_hi = (f"एक वस्तु {_ru_hi(cp)} में खरीदकर {pct}% {word_hi} पर बेची जाती है। "
                   f"विक्रय मूल्य ज्ञात कीजिए।")
        sol_hi = (f"विक्रय मूल्य = क्रय मूल्य x (100 {'+' if gain > 0 else '-'} {pct})/100 = "
                  f"{cp} x {100 + gain * pct}/100 = {_ru_hi(sp)}।")
        stem = (f"An article is bought for {_rupees(cp)} and sold at a {word} of {pct}%. "
                f"Find the selling price.")
        sol = (f"SP = CP x (100 {'+' if gain > 0 else '-'} {pct})/100 = {cp} x "
               f"{100 + gain * pct}/100 = {_rupees(sp)}.")
        return {"stem": stem, "correct": _rupees(sp), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("applied the percentage the other way — {} instead of {}".format(
                        "loss" if gain > 0 else "profit", word),
                     _rupees(cp * (100 - gain * pct) // 100)),
                    ("treated the percent as rupees", _rupees(cp + gain * pct)),
                    ("gave the profit amount rather than the selling price",
                     _rupees(cp * pct // 100))),
                "concept": "Profit / Loss %"}
    if diff == 2:
        cp = _mult(rng, 4, 20, 100)
        pct = rng.choice([10, 20, 25])
        sp = cp * (100 + pct) // 100
        stem_hi = (f"एक वस्तु को {_ru_hi(sp)} में बेचने पर दुकानदार को {pct}% लाभ होता है। "
                   f"क्रय मूल्य ज्ञात कीजिए।")
        sol_hi = (f"क्रय मूल्य = विक्रय मूल्य x 100/(100 + {pct}) = {sp} x 100/{100 + pct} "
                  f"= {_ru_hi(cp)}।")
        stem = (f"By selling an article for {_rupees(sp)}, a shopkeeper gains {pct}%. "
                f"Find the cost price.")
        sol = f"CP = SP x 100/(100 + {pct}) = {sp} x 100/{100 + pct} = {_rupees(cp)}."
        return {"stem": stem, "correct": _rupees(cp), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("took {}% OF THE SELLING PRICE instead of working back to the cost"
                     .format(pct), _rupees(sp * (100 - pct) // 100)),
                    ("divided by (100 - {}) instead of (100 + {})".format(pct, pct),
                     _rupees(sp * 100 // (100 - pct))),
                    ("subtracted the percent as rupees", _rupees(sp - pct))),
                "concept": "Profit / Loss %"}
    if diff == 3:
        cp = _mult(rng, 4, 20, 100)
        markup = rng.choice([40, 50, 60, 80])
        disc = rng.choice([10, 20, 25])
        mp = cp * (100 + markup) // 100
        sp = mp * (100 - disc) // 100
        gain_pct = Fraction((sp - cp) * 100, cp)
        stem_hi = (f"एक दुकानदार किसी वस्तु का अंकित मूल्य उसके क्रय मूल्य {_ru_hi(cp)} से "
                   f"{markup}% अधिक रखता है और फिर {disc}% की छूट देता है। उसका लाभ प्रतिशत "
                   f"ज्ञात कीजिए।")
        sol_hi = (f"अंकित मूल्य = {cp} x {100 + markup}/100 = {_ru_hi(mp)}; विक्रय मूल्य = "
                  f"{mp} x {100 - disc}/100 = {_ru_hi(sp)}। लाभ% = ({sp} - {cp})/{cp} x 100 = "
                  f"{_num(gain_pct)}%।")
        stem = (f"A shopkeeper marks an article {markup}% above its cost price of {_rupees(cp)} "
                f"and then allows a discount of {disc}%. Find his profit percent.")
        sol = (f"MP = {cp} x {100 + markup}/100 = {_rupees(mp)}; SP = {mp} x {100 - disc}/100 "
               f"= {_rupees(sp)}. Profit% = ({sp} - {cp})/{cp} x 100 = {_num(gain_pct)}%.")
        return {"stem": stem, "correct": _pct(gain_pct), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("subtracted the discount from the mark-up", _pct(markup - disc)),
                    ("took the discount on the COST price instead of the marked price",
                     _pct(Fraction((cp * (100 + markup) // 100 - cp * disc // 100 - cp) * 100,
                                   cp))),
                    ("worked the profit percent on the SELLING price instead of the cost",
                     _pct(Fraction((sp - cp) * 100, sp)))),
                "concept": "Marked Price & Discount"}
    # diff 4+ : two successive discounts -> the single equivalent discount
    d1 = rng.choice([10, 20, 25])
    d2 = rng.choice([x for x in (5, 10, 20) if x != d1])   # "10% and 10%" reads like a typo
    eq = 100 - Fraction((100 - d1) * (100 - d2), 100)
    stem_hi = (f"एक वस्तु {d1}% तथा {d2}% की दो क्रमिक छूटों के बाद बेची जाती है। इन दोनों के "
               f"तुल्य एकल छूट क्या होगी ?")
    sol_hi = (f"शुद्ध गुणक = (100-{d1})/100 x (100-{d2})/100। "
              f"तुल्य छूट = 100 - {_num(100 - eq)} = {_num(eq)}%।")
    stem = (f"An article is sold after two successive discounts of {d1}% and {d2}%. "
            f"What single discount is equivalent to these two?")
    sol = (f"Net factor = (100-{d1})/100 x (100-{d2})/100 = "
           f"{_frac(Fraction((100 - d1) * (100 - d2), 10000))}. "
           f"Equivalent discount = 100 - {_num(100 - eq)} = {_num(eq)}%.")
    return {"stem": stem, "correct": _pct(eq), "solution": sol,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "mistakes": mistakes(
                ("simply ADDED the two discounts", _pct(d1 + d2)),
                ("took the second discount on the original price, not the reduced one",
                 _pct(d1 + d2 - Fraction(d1 * d2, 200))),
                ("averaged the two discounts", _pct(Fraction(d1 + d2, 2)))),
            "concept": "Marked Price & Discount"}

def _b_si(rng, diff):
    """Simple interest, at a difficulty that changes the QUESTION rather than the numbers.

    diff 1  one step, forward        : P, R, T given -> SI
    diff 2  two steps                : P, R, T given -> AMOUNT (interest, then add the principal)
    diff 3  reversed                 : SI, P, T given -> R. Same arithmetic read backwards, which
                                       is where most candidates lose it.
    diff 4+ two unknowns             : a sum split between two rates, total interest given, find
                                       one part. Three steps and a linear equation.
    """
    p = _mult(rng, 4, 20, 500)
    r = rng.choice([4, 5, 6, 8, 10, 12])
    t = rng.randint(2, 5)
    si = p * r * t // 100
    if diff <= 1:
        stem = f"Find the simple interest on {_rupees(p)} at {r}% per annum for {t} years."
        sol = f"SI = P x R x T / 100 = {p} x {r} x {t} / 100 = {_rupees(si)}."
        stem_hi = (f"{_ru_hi(p)} पर {r}% वार्षिक की दर से {t} वर्षों का साधारण ब्याज ज्ञात कीजिए।")
        sol_hi = (f"साधारण ब्याज = मूलधन x दर x समय / 100 = {p} x {r} x {t} / 100 = {_ru_hi(si)}।")
        return {"stem": stem, "correct": _rupees(si), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("gave the AMOUNT (P + SI) instead of the interest", _rupees(p + si)),
                    ("used one year too many", _rupees(p * r * (t + 1) // 100)),
                    ("divided by 10 instead of 100", _rupees(p * r * t // 10))),
                "concept": "Simple Interest"}
    if diff == 2:
        amt = p + si
        stem_hi = (f"{_ru_hi(p)} पर {r}% वार्षिक साधारण ब्याज की दर से {t} वर्षों बाद कुल "
                   f"मिश्रधन कितना प्राप्त होगा ?")
        sol_hi = (f"ब्याज = {p} x {r} x {t}/100 = {_ru_hi(si)}। मिश्रधन = मूलधन + ब्याज = "
                  f"{p} + {si} = {_ru_hi(p + si)}।")
        stem = (f"What amount is received on {_rupees(p)} at {r}% per annum simple interest "
                f"after {t} years?")
        sol = (f"SI = {p} x {r} x {t}/100 = {_rupees(si)}. Amount = P + SI = {p} + {si} "
               f"= {_rupees(amt)}.")
        return {"stem": stem, "correct": _rupees(amt), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("stopped at the interest and never added the principal", _rupees(si)),
                    ("added one year's interest instead of all {} years".format(t),
                     _rupees(p + p * r // 100)),
                    ("compounded instead of using simple interest",
                     _rupees(int(p * (1 + r / 100) ** t)))),
                "concept": "Simple Interest"}
    if diff == 3:
        stem_hi = (f"{_ru_hi(p)} की राशि पर {t} वर्षों में {_ru_hi(si)} साधारण ब्याज मिलता है। "
                   f"वार्षिक ब्याज दर ज्ञात कीजिए।")
        sol_hi = (f"दर = ब्याज x 100 / (मूलधन x समय) = {si} x 100 / ({p} x {t}) = {r}%।")
        stem = (f"A sum of {_rupees(p)} earns {_rupees(si)} as simple interest in {t} years. "
                f"Find the rate of interest per annum.")
        sol = (f"R = SI x 100 / (P x T) = {si} x 100 / ({p} x {t}) = {r}%.")
        return {"stem": stem, "correct": _pct(r), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("forgot the x 100, giving a rate as a fraction", _pct(round(si / (p * t), 2))),
                    ("divided by the principal but not by the time", _pct(round(si * 100 / p, 2))),
                    ("divided by the time but not by the principal",
                     _pct(round(si * 100 / t / 100, 2) or 1))),
                "concept": "Simple Interest"}
    # diff 4+ : one sum, two rates, total interest known -> find one part
    r2 = rng.choice([x for x in (4, 5, 6, 8, 10, 12) if x != r])
    total = _mult(rng, 6, 20, 1000)
    x = _mult(rng, 1, (total // 1000) - 1 or 1, 1000)      # the part lent at r%
    y = total - x
    interest = (x * r + y * r2) // 100                      # for one year
    stem_hi = (f"{_ru_hi(total)} की राशि का कुछ भाग {r}% वार्षिक तथा शेष {r2}% वार्षिक साधारण "
               f"ब्याज पर उधार दिया जाता है। यदि एक वर्ष का कुल ब्याज {_ru_hi(interest)} है, तो "
               f"{r}% पर दिया गया भाग ज्ञात कीजिए।")
    sol_hi = (f"माना {r}% पर दी गई राशि x है। तब x x {r}/100 + ({total} - x) x {r2}/100 = "
              f"{interest}। हल करने पर x = {_ru_hi(x)}।")
    stem = (f"A sum of {_rupees(total)} is lent partly at {r}% and the rest at {r2}% per annum "
            f"simple interest. If the total interest for one year is {_rupees(interest)}, find "
            f"the part lent at {r}%.")
    sol = (f"Let the part at {r}% be x. Then x x {r}/100 + ({total} - x) x {r2}/100 = {interest}. "
           f"Solving, x = {_rupees(x)}.")
    return {"stem": stem, "correct": _rupees(x), "solution": sol,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "mistakes": mistakes(
                ("solved for the OTHER part, lent at {}%".format(r2), _rupees(y)),
                ("split the sum in the ratio of the two rates instead of solving",
                 _rupees(total * r // (r + r2))),
                ("halved the sum", _rupees(total // 2))),
            "concept": "Simple Interest"}

def _b_ci(rng, diff):
    """Compound interest. Difficulty = how far the question sits from applying the formula once.

    diff 1  CI for 2 years
    diff 2  the CI-minus-SI difference for 2 years, which is where P(R/100)^2 gets tested
    diff 3  half-yearly compounding — the rate halves and the periods double, and getting only
            one of the two right is the standard error
    diff 4+ reversed: the amount after 2 years is given, find the sum
    """
    p = _mult(rng, 4, 20, 500)
    r = rng.choice([5, 10, 20])
    if diff <= 1:
        t = 2
        amt = Fraction(p) * (1 + Fraction(r, 100)) ** t
        ci = amt - p
        si = p * r * t // 100
        stem_hi = (f"{_ru_hi(p)} पर {r}% वार्षिक की दर से {t} वर्षों का चक्रवृद्धि ब्याज "
                   f"ज्ञात कीजिए (वार्षिक चक्रवृद्धि)।")
        sol_hi = (f"मिश्रधन = मूलधन(1 + दर/100)^समय = {p}(1 + {r}/100)^2 = {_num(amt)}। "
                  f"चक्रवृद्धि ब्याज = मिश्रधन - मूलधन = {_num(amt)} - {p} = {_num(ci)}।")
        stem = (f"Find the compound interest on {_rupees(p)} at {r}% per annum for {t} years "
                f"(compounded annually).")
        sol = (f"Amount = P(1 + R/100)^T = {p}(1 + {r}/100)^2 = {_num(amt)}. "
               f"CI = Amount - P = {_num(amt)} - {p} = {_num(ci)}.")
        return {"stem": stem, "correct": _rupees(float(ci)), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("used SIMPLE interest", _rupees(si)),
                    ("gave the AMOUNT instead of the interest", _rupees(float(amt))),
                    ("compounded for one year only", _rupees(p * r // 100))),
                "concept": "Compound Interest"}
    if diff == 2:
        diffv = Fraction(p) * Fraction(r, 100) ** 2
        stem_hi = (f"{_ru_hi(p)} की राशि पर {r}% वार्षिक की दर से 2 वर्षों के चक्रवृद्धि ब्याज "
                   f"तथा साधारण ब्याज का अंतर है :")
        sol_hi = (f"2 वर्षों का अंतर = मूलधन x (दर/100)^2 = {p} x ({r}/100)^2 = {_num(diffv)}।")
        stem = (f"The difference between the compound interest and the simple interest on a sum "
                f"of {_rupees(p)} at {r}% per annum for 2 years is:")
        sol = f"Difference (2 years) = P(R/100)^2 = {p} x ({r}/100)^2 = {_num(diffv)}."
        return {"stem": stem, "correct": _rupees(float(diffv)), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("used P x R/100, i.e. one year's simple interest", _rupees(p * r // 100)),
                    ("doubled the difference, as if it were for two years' worth",
                     _rupees(float(diffv) * 2)),
                    ("gave the full compound interest instead of the difference",
                     _rupees(float(Fraction(p) * (1 + Fraction(r, 100)) ** 2 - p)))),
                "concept": "Compound Interest"}
    if diff == 3:
        t = 1
        half_r = Fraction(r, 2)
        amt = Fraction(p) * (1 + half_r / 100) ** 2
        ci = amt - p
        stem_hi = (f"{_ru_hi(p)} पर {r}% वार्षिक की दर से {t} वर्ष का चक्रवृद्धि ब्याज "
                   f"ज्ञात कीजिए, जबकि ब्याज अर्धवार्षिक रूप से संयोजित होता है।")
        sol_hi = (f"अर्धवार्षिक : दर = {r}/2 = {_num(half_r)}% प्रति छमाही, अवधियाँ = 2। "
                  f"मिश्रधन = {p}(1 + {_num(half_r)}/100)^2 = {_num(amt)}; ब्याज = {_num(ci)}।")
        stem = (f"Find the compound interest on {_rupees(p)} at {r}% per annum for {t} year, "
                f"compounded half-yearly.")
        sol = (f"Half-yearly: rate = {r}/2 = {_num(half_r)}% per half-year, periods = 2. "
               f"Amount = {p}(1 + {_num(half_r)}/100)^2 = {_num(amt)}; CI = {_num(ci)}.")
        annual = Fraction(p) * (1 + Fraction(r, 100)) - p
        return {"stem": stem, "correct": _rupees(float(ci)), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("halved the rate but forgot to double the periods",
                     _rupees(float(Fraction(p) * (1 + half_r / 100) - p))),
                    ("doubled the periods but kept the full rate",
                     _rupees(float(Fraction(p) * (1 + Fraction(r, 100)) ** 2 - p))),
                    ("compounded annually, ignoring 'half-yearly'", _rupees(float(annual)))),
                "concept": "Compound Interest"}
    # diff 4+ : reversed — amount after 2 years given, find the sum
    amt = Fraction(p) * (1 + Fraction(r, 100)) ** 2
    if amt.denominator != 1:                      # the amount is PRINTED, so keep it exact
        p = _mult(rng, 4, 20, 10000)
        amt = Fraction(p) * (1 + Fraction(r, 100)) ** 2
    stem_hi = (f"कोई राशि {r}% वार्षिक चक्रवृद्धि ब्याज की दर से 2 वर्षों में "
               f"{_ru_hi(float(amt))} हो जाती है। वह राशि ज्ञात कीजिए।")
    sol_hi = (f"मूलधन = मिश्रधन / (1 + दर/100)^2 = {_num(amt)} / (1 + {r}/100)^2 = {_ru_hi(p)}।")
    stem = (f"A sum of money amounts to {_rupees(float(amt))} in 2 years at {r}% per annum "
            f"compound interest. Find the sum.")
    sol = (f"P = Amount / (1 + R/100)^2 = {_num(amt)} / (1 + {r}/100)^2 = {_rupees(p)}.")
    return {"stem": stem, "correct": _rupees(p), "solution": sol,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "mistakes": mistakes(
                ("subtracted 2 x {}% of the amount, i.e. worked it as simple interest"
                 .format(r), _rupees(float(amt * (1 - Fraction(2 * r, 100))))),
                ("divided by (1 + R/100) once instead of twice",
                 _rupees(float(amt / (1 + Fraction(r, 100))))),
                ("gave the interest rather than the sum", _rupees(float(amt) - p))),
            "concept": "Compound Interest"}

def _b_ratio(rng, diff):
    """Ratio and proportion. Difficulty = whether the ratio can be used as given.

    diff 1  three-way split of a known total
    diff 2  the DIFFERENCE between two shares is given, not the total
    diff 3  two ratios chained (A:B and B:C) that must be linked before anything can be split
    diff 4+ a ratio that changes when a fixed amount is added to each part
    """
    a, b, c = rng.sample([2, 3, 4, 5, 6, 7], 3)
    unit = _mult(rng, 3, 12, 100)
    if diff <= 1:
        total = (a + b + c) * unit
        who = rng.randint(0, 2)
        parts = [a, b, c]
        share = parts[who] * unit
        who_hi = ["पहले", "दूसरे", "तीसरे"][who]
        stem_hi = (f"{_ru_hi(total)} की राशि तीन व्यक्तियों में {a} : {b} : {c} के अनुपात में "
                   f"बाँटी जाती है। {who_hi} व्यक्ति का हिस्सा ज्ञात कीजिए।")
        sol_hi = (f"कुल अनुपात इकाइयाँ = {a}+{b}+{c} = {a + b + c}। एक इकाई = "
                  f"{total}/{a + b + c} = {unit}। हिस्सा = {parts[who]} x {unit} = "
                  f"{_ru_hi(share)}।")
        stem = (f"An amount of {_rupees(total)} is divided among three people in the ratio "
                f"{a} : {b} : {c}. Find the share of the "
                f"{['first', 'second', 'third'][who]} person.")
        sol = (f"Total ratio units = {a}+{b}+{c} = {a + b + c}. One unit = {total}/{a + b + c} "
               f"= {unit}. Share = {parts[who]} x {unit} = {_rupees(share)}.")
        return {"stem": stem, "correct": _rupees(share), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("gave another person's share", _rupees(parts[(who + 1) % 3] * unit)),
                    ("divided the total equally instead of by the ratio",
                     _rupees(total // 3)),
                    ("divided by the person's ratio term instead of multiplying",
                     _rupees(total // parts[who]))),
                "concept": "Ratio & Proportion"}
    if diff == 2:
        hi, lo = max(a, b), min(a, b)
        gap = (hi - lo) * unit
        total = (hi + lo) * unit
        stem_hi = (f"दो व्यक्ति किसी राशि को {hi} : {lo} के अनुपात में बाँटते हैं। यदि पहले "
                   f"व्यक्ति को दूसरे से {_ru_hi(gap)} अधिक मिलते हैं, तो कुल राशि ज्ञात कीजिए।")
        sol_hi = (f"अंतर = {hi} - {lo} = {hi - lo} इकाई = {_ru_hi(gap)}, अतः एक इकाई = "
                  f"{_ru_hi(unit)}। कुल = ({hi} + {lo}) x {unit} = {_ru_hi(total)}।")
        stem = (f"Two people share an amount in the ratio {hi} : {lo}. If the first receives "
                f"{_rupees(gap)} more than the second, find the total amount shared.")
        sol = (f"The difference is {hi} - {lo} = {hi - lo} units = {_rupees(gap)}, so one unit "
               f"= {_rupees(unit)}. Total = ({hi} + {lo}) x {unit} = {_rupees(total)}.")
        return {"stem": stem, "correct": _rupees(total), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("treated the difference as the TOTAL and split it", _rupees(gap)),
                    ("divided the difference by the sum of the terms instead of the difference",
                     _rupees((hi + lo) * gap // (hi + lo))),
                    ("found only the larger share", _rupees(hi * unit))),
                "concept": "Ratio & Proportion"}
    if diff == 3:
        # A:B = a:b and B:C = b2:c2 -> link on B, then split a known total
        b2, c2 = rng.sample([2, 3, 4, 5, 6], 2)
        A, B, C = a * b2, b * b2, b * c2
        g = math.gcd(math.gcd(A, B), C)
        A, B, C = A // g, B // g, C // g
        total = (A + B + C) * unit
        stem_hi = (f"यदि A : B = {a} : {b} तथा B : C = {b2} : {c2} है, और {_ru_hi(total)} की "
                   f"राशि A, B तथा C में उसी अनुपात में बाँटी जाती है, तो C का हिस्सा ज्ञात कीजिए।")
        sol_hi = (f"A : B : C = {A} : {B} : {C}। एक इकाई = {total}/{A + B + C} = {unit}। "
                  f"C का हिस्सा = {C} x {unit} = {_ru_hi(C * unit)}।")
        stem = (f"If A : B = {a} : {b} and B : C = {b2} : {c2}, and {_rupees(total)} is divided "
                f"among A, B and C in that ratio, find C's share.")
        sol = (f"A : B : C = {A} : {B} : {C}. One unit = {total}/{A + B + C} = {unit}. "
               f"C's share = {C} x {unit} = {_rupees(C * unit)}.")
        return {"stem": stem, "correct": _rupees(C * unit), "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("used c2 as C's term without linking the two ratios through B",
                     _rupees(total * c2 // (a + b + c2))),
                    ("gave A's share instead of C's", _rupees(A * unit)),
                    ("split the amount equally", _rupees(total // 3))),
                "concept": "Ratio & Proportion"}
    # diff 4+ : the ratio changes when the same amount is added to both parts
    x = rng.choice([2, 3, 4, 5])
    y = rng.choice([w for w in (3, 4, 5, 7, 9) if w > x])
    k = _mult(rng, 2, 9, 10)
    add = _mult(rng, 1, 6, 10)
    A0, B0 = x * k, y * k
    g = math.gcd(A0 + add, B0 + add)
    stem_hi = (f"दो संख्याएँ {x} : {y} के अनुपात में हैं। यदि प्रत्येक में {add} जोड़ दिया जाए, "
               f"तो अनुपात {(A0 + add) // g} : {(B0 + add) // g} हो जाता है। छोटी संख्या "
               f"ज्ञात कीजिए।")
    sol_hi = (f"माना संख्याएँ {x}n तथा {y}n हैं। तब ({x}n + {add}) : ({y}n + {add}) = "
              f"{(A0 + add) // g} : {(B0 + add) // g}, जिससे n = {k}। "
              f"छोटी संख्या = {x} x {k} = {A0}।")
    stem = (f"Two numbers are in the ratio {x} : {y}. If {add} is added to each, the ratio "
            f"becomes {(A0 + add) // g} : {(B0 + add) // g}. Find the smaller number.")
    sol = (f"Let the numbers be {x}n and {y}n. Then ({x}n + {add}) : ({y}n + {add}) = "
           f"{(A0 + add) // g} : {(B0 + add) // g}, giving n = {k}. "
           f"Smaller number = {x} x {k} = {A0}.")
    return {"stem": stem, "correct": _num(A0), "solution": sol,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "mistakes": mistakes(
                ("gave the LARGER number", _num(B0)),
                ("gave the smaller number AFTER the addition", _num(A0 + add)),
                ("used the new ratio as though it were the original", _num(x * (k + add)))),
            "concept": "Ratio & Proportion"}

def _b_partnership(rng, diff):
    xa, xb = _mult(rng, 4, 12, 1000), _mult(rng, 4, 12, 1000)
    ta, tb = rng.randint(6, 12), rng.randint(6, 12)
    ca, cb = xa * ta, xb * tb
    g = math.gcd(ca, cb)
    ra, rb = ca // g, cb // g
    profit = (ra + rb) * rng.randint(20, 60) * 10
    shareA = profit * ra // (ra + rb)
    stem = (f"A started a business investing {_rupees(xa)} for {ta} months, and B invested "
            f"{_rupees(xb)} for {tb} months. If the total profit is {_rupees(profit)}, "
            f"find A's share.")
    sol = (f"Profit ratio = (A: {xa}x{ta}) : (B: {xb}x{tb}) = {ca} : {cb} = {ra} : {rb}. "
           f"A's share = {ra}/({ra}+{rb}) x {profit} = {shareA}.")
    d = [_rupees(profit - shareA), _rupees(profit * rb // (ra + rb) if ra != rb else shareA + 100),
         _rupees(profit // 2)]
    return {"stem": stem, "correct": _rupees(shareA), "distractors": d, "solution": sol,
            "concept": "Partnership"}

# ---- Averages & Ages --------------------------------------------------------

def _b_average(rng, diff):
    """Averages. Difficulty = how far the question sits from "add them and divide".

    diff 1  direct        : the average of n numbers
    diff 2  replacement   : a new member replaces one, the average moves
    diff 3  combined      : two groups of different sizes, one overall average
    diff 4+ correction    : an average was computed with one value read wrongly; fix it
    """
    if diff <= 1:
        n = rng.randint(5, 8)
        nums = [rng.randint(20, 90) for _ in range(n)]
        total = sum(nums)
        ans = Fraction(total, n)
        stem = f"Find the average of the numbers {', '.join(map(str, nums))}."
        sol = f"Sum = {total}; average = {total}/{n} = {_num(ans)}."
        d = mistakes(("divided by one count too many", _num(Fraction(total, n + 1))),
                     ("divided by one count too few", _num(Fraction(total, n - 1))),
                     ("gave the TOTAL instead of the average", _num(total)))
        return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
                "concept": "Averages"}
    if diff == 2:
        old_avg = rng.randint(30, 50)
        n2 = rng.randint(6, 10)
        change = rng.choice([2, 3, 4])
        old_m = rng.randint(20, 30)
        new_m = old_m + n2 * change
        stem = (f"The average age of {n2} students is {old_avg} years. When a new student "
                f"replaces one aged {old_m} years, the average increases by {change} years. "
                f"Find the age of the new student.")
        sol = (f"Total increase = {n2} x {change} = {n2 * change}. New student's age = "
               f"{old_m} + {n2 * change} = {new_m} years.")
        d = mistakes(
            ("forgot to multiply the rise by the number of students", _num(old_m + change)),
            ("added the rise to the OLD AVERAGE instead of the replaced student's age",
             _num(old_avg + n2 * change)),
            ("subtracted the total rise instead of adding it", _num(old_m - n2 * change)))
        return {"stem": stem, "correct": _num(new_m), "mistakes": d, "solution": sol,
                "concept": "Averages"}
    if diff == 3:
        n1, n2 = rng.randint(12, 25), rng.randint(12, 25)
        a1, a2 = rng.randint(30, 45), rng.randint(50, 70)
        ans = Fraction(n1 * a1 + n2 * a2, n1 + n2)
        stem = (f"The average weight of {n1} boys is {a1} kg and that of {n2} girls is {a2} kg. "
                f"Find the average weight of the whole class.")
        sol = (f"Total = {n1} x {a1} + {n2} x {a2} = {n1 * a1 + n2 * a2}; "
               f"count = {n1 + n2}; average = {_num(ans)} kg.")
        d = mistakes(("took the plain average of the two averages, ignoring the group sizes",
                      _num(Fraction(a1 + a2, 2))),
                     ("weighted each average by the OTHER group's size",
                      _num(Fraction(n2 * a1 + n1 * a2, n1 + n2))),
                     ("divided the combined total by 2 instead of by the head count",
                      _num(Fraction(n1 * a1 + n2 * a2, 2))))
        return {"stem": stem, "correct": _num(ans), "mistakes": d, "solution": sol,
                "concept": "Averages"}
    # diff 4+ : a wrongly-read value has to be corrected
    n = rng.randint(8, 15)
    wrong_avg = rng.randint(30, 60)
    misread, actual = rng.randint(20, 40), rng.randint(50, 90)
    correct_avg = Fraction(n * wrong_avg - misread + actual, n)
    stem = (f"The average of {n} numbers was found to be {wrong_avg}. Later it was discovered "
            f"that one number was read as {misread} instead of {actual}. Find the correct "
            f"average.")
    sol = (f"Correct total = {n} x {wrong_avg} - {misread} + {actual} = "
           f"{n * wrong_avg - misread + actual}. Correct average = {_num(correct_avg)}.")
    d = mistakes(("corrected the total but divided by n - 1",
                  _num(Fraction(n * wrong_avg - misread + actual, n - 1))),
                 ("adjusted the average by the whole difference instead of dividing it by n",
                  _num(wrong_avg + (actual - misread))),
                 ("applied the difference the wrong way round",
                  _num(Fraction(n * wrong_avg + misread - actual, n))))
    return {"stem": stem, "correct": _num(correct_avg), "mistakes": d, "solution": sol,
            "concept": "Averages"}

def _b_ages(rng, diff):
    """Ages, where the difficulty is how many time-frames the candidate has to hold at once.

    diff 1  one frame            : ratio now + one age -> the other age
    diff 2  two frames           : ratio now -> an age after n years
    diff 3  past and present     : ratio n years AGO + present age -> an age m years hence
    diff 4+ two ratios, no ages  : ratio n years ago AND m years hence -> present age. Nothing is
                                   given directly; it has to be set up and solved.
    """
    a, b = rng.choice([(4, 3), (5, 3), (7, 5), (3, 2), (5, 4)])
    k = rng.randint(3, 8)
    ageA, ageB = a * k, b * k
    yrs = rng.randint(3, 8)
    if diff <= 1:
        stem = (f"The present ages of A and B are in the ratio {a} : {b}. If A is {ageA} years "
                f"old, what is B's present age?")
        sol = f"One ratio unit = {ageA}/{a} = {k}. B's age = {b} x {k} = {ageB} years."
        return {"stem": stem, "correct": _num(ageB), "solution": sol,
                "mistakes": mistakes(
                    ("multiplied by A's ratio term instead of B's", _num(a * k + k)),
                    ("subtracted the ratio difference from A's age", _num(ageA - (a - b))),
                    ("swapped the ratio, giving A's age from B's", _num(a * a * k // b))),
                "concept": "Problems on Ages"}
    if diff == 2:
        ans = ageB + yrs
        stem = (f"The present ages of A and B are in the ratio {a} : {b}. If A's present age is "
                f"{ageA} years, what will be B's age after {yrs} years?")
        sol = (f"One ratio unit = {ageA}/{a} = {k}. B's present age = {b} x {k} = {ageB}. "
               f"After {yrs} years = {ageB} + {yrs} = {ans}.")
        return {"stem": stem, "correct": _num(ans), "solution": sol,
                "mistakes": mistakes(
                    ("added the years to A instead of B", _num(ageA + yrs)),
                    ("gave B's PRESENT age, forgetting the {} years".format(yrs), _num(ageB)),
                    ("added the ratio term instead of the years", _num(ageB + b))),
                "concept": "Problems on Ages"}
    if diff == 3:
        # the ratio is stated for `yrs` years AGO, and the present age is given
        pastA, pastB = a * k, b * k
        nowA, nowB = pastA + yrs, pastB + yrs
        m = rng.randint(2, 6)
        ans = nowB + m
        stem = (f"{yrs} years ago the ages of A and B were in the ratio {a} : {b}. If A is now "
                f"{nowA} years old, what will B's age be {m} years from now?")
        sol = (f"A's age {yrs} years ago = {nowA} - {yrs} = {pastA}, so one ratio unit = "
               f"{pastA}/{a} = {k}. B then = {b} x {k} = {pastB}; B now = {pastB} + {yrs} = "
               f"{nowB}; after {m} years = {ans}.")
        return {"stem": stem, "correct": _num(ans), "solution": sol,
                "mistakes": mistakes(
                    ("applied the ratio to A's PRESENT age instead of his age {} years ago"
                     .format(yrs), _num(b * (nowA // a) + m)),
                    ("forgot to bring B forward from the past to the present", _num(pastB + m)),
                    ("gave B's present age without the {} years".format(m), _num(nowB))),
                "concept": "Problems on Ages"}
    # diff 4+ : two ratios, neither age given
    n1, n2 = rng.randint(3, 6), rng.randint(3, 6)
    nowA, nowB = a * k + n1, b * k + n1                  # ratio a:b held n1 years ago
    from math import gcd
    fa, fb = nowA + n2, nowB + n2
    g = gcd(fa, fb)
    stem = (f"{n1} years ago the ages of A and B were in the ratio {a} : {b}. {n2} years from "
            f"now the ratio of their ages will be {fa // g} : {fb // g}. Find A's present age.")
    sol = (f"Let the ages {n1} years ago be {a}x and {b}x. Then ({a}x + {n1 + n2}) : "
           f"({b}x + {n1 + n2}) = {fa // g} : {fb // g}, giving x = {k}. "
           f"A's present age = {a} x {k} + {n1} = {nowA} years.")
    return {"stem": stem, "correct": _num(nowA), "solution": sol,
            "mistakes": mistakes(
                ("solved for B's present age instead of A's", _num(nowB)),
                ("gave A's age {} years ago rather than now".format(n1), _num(a * k)),
                ("added both time gaps to A instead of one", _num(nowA + n2))),
            "concept": "Problems on Ages"}


# ---- Time & Work + Pipes ----------------------------------------------------

def _b_time_work(rng, diff):
    """Time & work. Difficulty = how many phases of the job the candidate must track.

    diff 1  one phase        : A alone, B alone -> together
    diff 2  two phases       : A works some days, leaves, B finishes
    diff 3  three workers    : A, B, C together
    diff 4+ reversed         : A and B together, and A alone, are given -> find B alone. The same
                              relation read backwards, which is where the rate idea actually gets
                              tested rather than recited.
    """
    a = rng.choice([6, 8, 9, 10, 12, 15, 18, 20, 24])
    b = rng.choice([x for x in (6, 8, 9, 10, 12, 15, 18, 20, 24) if x != a])
    if diff <= 1:
        tog = Fraction(a * b, a + b)
        stem_hi = (f"A किसी कार्य को {a} दिन में तथा B उसी कार्य को {b} दिन में पूरा कर सकता है। "
                   f"दोनों मिलकर उस कार्य को कितने दिन में पूरा करेंगे ?")
        sol_hi = (f"A का एक दिन का कार्य = 1/{a}, B का = 1/{b}। मिलकर = 1/{a} + 1/{b}। "
                  f"समय = {a}x{b}/({a}+{b}) = {_num(Fraction(a * b, a + b))} दिन।")
        stem = (f"A can complete a work in {a} days and B can complete it in {b} days. Working "
                f"together, in how many days will they finish it?")
        sol = (f"A's one-day work = 1/{a}, B's = 1/{b}. Together = 1/{a} + 1/{b}. "
               f"Time = {a}x{b}/({a}+{b}) = {_num(tog)} days.")
        # At least one distractor must SURVIVE the check a good student applies — that the joint
        # time is below either time alone. Before this, on 15 of 34 questions every distractor sat
        # above min(a, b) and the question fell to that one insight with no arithmetic.
        d = mistakes(("used a x b / (a - b) instead of a x b / (a + b)",
                      _num(Fraction(a * b, abs(a - b))) + " days"),
                     ("halved the smaller time", _num(Fraction(min(a, b), 2)) + " days"),
                     ("added the two TIMES instead of adding the rates", _num(a + b) + " days"),
                     ("took the plain average of the two times",
                      _num(Fraction(a + b, 2)) + " days"))
        return {"stem": stem, "correct": _num(tog) + " days", "mistakes": d,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "solution": sol, "concept": "Time & Work"}
    if diff == 2:
        worked = rng.randint(2, a - 2)
        rem = 1 - Fraction(worked, a)
        b_time = rem * b
        stem_hi = (f"A किसी कार्य को {a} दिन में तथा B उसे {b} दिन में कर सकता है। A अकेले "
                   f"{worked} दिन कार्य करके छोड़ देता है। शेष कार्य को B कितने दिन में पूरा करेगा ?")
        sol_hi = (f"A ने {worked}/{a} कार्य किया, शेष = {_frac(rem)}। "
                  f"B को चाहिए {_frac(rem)} x {b} = {_num(b_time)} दिन।")
        stem = (f"A can do a piece of work in {a} days and B in {b} days. A works alone for "
                f"{worked} days and then leaves. In how many days will B finish the remaining "
                f"work?")
        sol = (f"A does {worked}/{a} of the work, leaving {_frac(rem)}. "
               f"B needs {_frac(rem)} x {b} = {_num(b_time)} days.")
        d = mistakes(("gave the days for the whole job rather than the remainder",
                      _num(b) + " days"),
                     ("subtracted the days worked from B's time",
                      _num(max(b - worked, 1)) + " days"),
                     ("applied the remaining fraction to A's time instead of B's",
                      _num(rem * a) + " days"))
        return {"stem": stem, "correct": _num(b_time) + " days", "mistakes": d,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "solution": sol, "concept": "Time & Work"}
    if diff == 3:
        c = rng.choice([x for x in (6, 8, 9, 10, 12, 15, 18, 20, 24) if x not in (a, b)])
        tog = Fraction(1, Fraction(1, a) + Fraction(1, b) + Fraction(1, c))
        stem_hi = (f"A, B तथा C किसी कार्य को क्रमशः {a}, {b} तथा {c} दिन में कर सकते हैं। "
                   f"तीनों मिलकर उस कार्य को कितने दिन में पूरा करेंगे ?")
        sol_hi = (f"तीनों का एक दिन का कार्य = 1/{a} + 1/{b} + 1/{c}। "
                  f"समय = {_num(Fraction(1, Fraction(1, a) + Fraction(1, b) + Fraction(1, c)))} दिन।")
        stem = (f"A, B and C can do a piece of work in {a}, {b} and {c} days respectively. "
                f"Working together, in how many days will they complete it?")
        sol = (f"Combined one-day work = 1/{a} + 1/{b} + 1/{c} = "
               f"{_frac(Fraction(1, a) + Fraction(1, b) + Fraction(1, c))}. "
               f"Time = {_num(tog)} days.")
        d = mistakes(("added the three TIMES instead of the rates", _num(a + b + c) + " days"),
                     ("took the average of the three times",
                      _num(Fraction(a + b + c, 3)) + " days"),
                     ("used only the two fastest workers",
                      _num(Fraction(1, Fraction(1, min(a, b, c)) +
                                    Fraction(1, sorted((a, b, c))[1]))) + " days"))
        return {"stem": stem, "correct": _num(tog) + " days", "mistakes": d,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "solution": sol, "concept": "Time & Work"}
    # diff 4+ : given together-time and A alone, find B alone.
    # The joint time is PRINTED, so it has to be exact. Left as a raw fraction it printed rounded
    # ("4.62 days") while the answer was derived from the unrounded value — a candidate solving
    # honestly from the page got 20.09 where the key said 20. A given that cannot be used as
    # printed is a broken question, however right the key is. So pick a pair whose joint time is
    # exact to the two decimals we print.
    pairs = [(x, y) for x in (6, 8, 9, 10, 12, 15, 18, 20, 24)
             for y in (6, 8, 9, 10, 12, 15, 18, 20, 24)
             if x != y and Fraction(x * y, x + y).denominator in (1, 2, 4, 5, 10, 20, 25, 50, 100)]
    a, b = rng.choice(pairs)
    tog = Fraction(a * b, a + b)
    stem_hi = (f"A और B मिलकर किसी कार्य को {_num(tog)} दिन में पूरा कर सकते हैं। A अकेले उसे "
               f"{a} दिन में कर सकता है। B अकेले उस कार्य को कितने दिन में पूरा करेगा ?")
    sol_hi = (f"B का एक दिन का कार्य = 1/{_num(tog)} - 1/{a} = {_frac(Fraction(1, b))}। "
              f"अतः B अकेले {b} दिन लेगा।")
    stem = (f"A and B together can complete a work in {_num(tog)} days. A alone can do it in "
            f"{a} days. In how many days can B alone complete the work?")
    sol = (f"B's one-day work = 1/{_num(tog)} - 1/{a} = {_frac(Fraction(1, b))}. "
           f"So B alone takes {b} days.")
    d = mistakes(("subtracted the TIMES instead of the rates",
                  _num(abs(a - tog)) + " days"),
                 ("added the times", _num(a + tog) + " days"),
                 ("doubled the joint time", _num(tog * 2) + " days"))
    return {"stem": stem, "correct": _num(b) + " days", "mistakes": d,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "solution": sol, "concept": "Time & Work"}

def _b_pipes(rng, diff):
    """Pipes & cisterns. Difficulty = whether anything works AGAINST the filling, and when.

    diff 1  two inlets
    diff 2  inlet plus an outlet (the sign is the whole test)
    diff 3  two inlets and an outlet
    diff 4+ reversed: the tank's fill time with a leak is given, find the leak's own time
    """
    a = rng.choice([6, 8, 10, 12, 15, 20])
    b = rng.choice([x for x in (6, 8, 10, 12, 15, 20) if x != a])
    if diff <= 1:
        together = Fraction(a * b, a + b)
        stem = (f"Two pipes can fill a tank in {a} hours and {b} hours respectively. If both are "
                f"opened together, in how many hours will the tank be full?")
        sol = (f"Together = 1/{a} + 1/{b} per hour, so time = {a}x{b}/({a}+{b}) = "
               f"{_num(together)} hours.")
        d = mistakes(("used a x b / (a - b) instead of a x b / (a + b)",
                      _num(Fraction(a * b, abs(a - b))) + " hours"),
                     ("halved the faster pipe's time",
                      _num(Fraction(min(a, b), 2)) + " hours"),
                     ("added the two filling TIMES instead of the rates",
                      _num(a + b) + " hours"),
                     ("took the average of the two times",
                      _num(Fraction(a + b, 2)) + " hours"))
        return {"stem": stem, "correct": _num(together) + " hours", "mistakes": d,
                "solution": sol, "concept": "Pipes & Cisterns"}
    if diff == 2:
        inlet, outlet = min(a, b), max(a, b)          # outlet must be slower or it never fills
        net = Fraction(1, inlet) - Fraction(1, outlet)
        t = Fraction(1, net)
        stem = (f"A pipe fills a tank in {inlet} hours while an outlet pipe empties it in "
                f"{outlet} hours. If both are opened together, in how many hours will the tank "
                f"be full?")
        sol = (f"Net filling per hour = 1/{inlet} - 1/{outlet} = {_frac(net)}. "
               f"Time = {_num(t)} hours.")
        d = mistakes(("ADDED the outlet instead of subtracting it",
                      _num(Fraction(inlet * outlet, inlet + outlet)) + " hours"),
                     ("ignored the outlet altogether", _num(inlet) + " hours"),
                     ("subtracted the times instead of the rates",
                      _num(outlet - inlet) + " hours"))
        return {"stem": stem, "correct": _num(t) + " hours", "mistakes": d,
                "solution": sol, "concept": "Pipes & Cisterns"}
    if diff == 3:
        c = rng.choice([x for x in (24, 30, 36, 40) ])
        net = Fraction(1, a) + Fraction(1, b) - Fraction(1, c)
        t = Fraction(1, net)
        stem = (f"Two pipes fill a tank in {a} hours and {b} hours, while a waste pipe empties "
                f"it in {c} hours. If all three are opened together, in how many hours will the "
                f"tank be full?")
        sol = (f"Net per hour = 1/{a} + 1/{b} - 1/{c} = {_frac(net)}. Time = {_num(t)} hours.")
        d = mistakes(("added all three rates, treating the waste pipe as a filler",
                      _num(Fraction(1, Fraction(1, a) + Fraction(1, b) + Fraction(1, c)))
                      + " hours"),
                     ("ignored the waste pipe",
                      _num(Fraction(a * b, a + b)) + " hours"),
                     ("subtracted the waste pipe's TIME from the joint time",
                      _num(abs(Fraction(a * b, a + b) - c)) + " hours"))
        return {"stem": stem, "correct": _num(t) + " hours", "mistakes": d,
                "solution": sol, "concept": "Pipes & Cisterns"}
    # diff 4+ : leak found from the delay
    # Same rule as time & work: the delayed filling time is a GIVEN, so it must print exactly.
    combos = [(f, l) for f in (6, 8, 10, 12, 15, 20) for l in (24, 30, 36, 40, 60) if l > f
              and Fraction(1, Fraction(1, f) - Fraction(1, l)).denominator in
              (1, 2, 4, 5, 10, 20, 25, 50, 100)]
    fill, leak = rng.choice(combos)
    with_leak = Fraction(1, Fraction(1, fill) - Fraction(1, leak))
    stem = (f"A pipe can fill a tank in {fill} hours, but because of a leak it takes "
            f"{_num(with_leak)} hours to fill. In how many hours can the leak alone empty the "
            f"full tank?")
    sol = (f"Leak's rate = 1/{fill} - 1/{_num(with_leak)} = {_frac(Fraction(1, leak))} per hour, "
           f"so the leak empties the tank in {leak} hours.")
    d = mistakes(("subtracted the two TIMES instead of the rates",
                  _num(with_leak - fill) + " hours"),
                 ("added the two times", _num(with_leak + fill) + " hours"),
                 ("gave the delayed filling time again", _num(with_leak) + " hours"))
    return {"stem": stem, "correct": _num(leak) + " hours", "mistakes": d,
            "solution": sol, "concept": "Pipes & Cisterns"}

def _b_std(rng, diff):
    speed = rng.choice([40, 45, 50, 54, 60, 72])
    t = rng.randint(2, 6)
    dist = speed * t
    stem = f"A car travels at a speed of {speed} km/hr. How far will it travel in {t} hours?"
    sol = f"Distance = speed x time = {speed} x {t} = {dist} km."
    d = [_num(speed + t) + " km", _num(dist + speed) + " km", _num(dist - speed) + " km"]
    return {"stem": stem, "correct": f"{dist} km", "distractors": d, "solution": sol,
            "concept": "Speed / Time / Distance"}

def _b_trains(rng, diff):
    length = rng.choice([100, 120, 150, 180, 200, 240])
    speed_kmph = rng.choice([36, 54, 72, 90])
    speed_ms = speed_kmph * 5 // 18
    mode = rng.choice(["pole", "platform"])
    if mode == "pole":
        t = Fraction(length, speed_ms)
        stem = (f"A train {length} m long is running at {speed_kmph} km/hr. How much time will "
                f"it take to cross a pole?")
        sol = (f"Speed = {speed_kmph} x 5/18 = {speed_ms} m/s. Time = length/speed = "
               f"{length}/{speed_ms} = {_num(t)} seconds.")
        d = [_num(float(t) + 3) + " s", _num(length // speed_kmph) + " s", _num(float(t) * 2) + " s"]
        return {"stem": stem, "correct": _num(t) + " s", "distractors": d, "solution": sol,
                "concept": "Trains"}
    plat = rng.choice([100, 150, 200, 250])
    t = Fraction(length + plat, speed_ms)
    stem = (f"A train {length} m long running at {speed_kmph} km/hr crosses a platform "
            f"{plat} m long. Find the time taken.")
    sol = (f"Speed = {speed_kmph} x 5/18 = {speed_ms} m/s. Total distance = {length}+{plat} = "
           f"{length+plat} m. Time = {length+plat}/{speed_ms} = {_num(t)} seconds.")
    d = [_num(Fraction(length, speed_ms)) + " s", _num(float(t) + 5) + " s", _num(float(t) - 3) + " s"]
    return {"stem": stem, "correct": _num(t) + " s", "distractors": d, "solution": sol,
            "concept": "Trains"}

def _b_boats(rng, diff):
    """Boats and streams. Difficulty = how many of {boat, stream, up, down} are unknown.

    diff 1  boat and stream given          -> distance one way
    diff 2  downstream and upstream SPEEDS -> the boat's speed and the stream's speed
    diff 3  a distance covered each way with times given -> the stream's speed
    diff 4+ the boat goes down and returns; total time given -> find the distance one way
    """
    b = rng.choice([8, 10, 12, 15, 18])
    s = rng.choice([x for x in (2, 3, 4, 5) if x < b])
    if diff <= 1:
        mode = rng.choice(["down", "up"])
        eff = b + s if mode == "down" else b - s
        t = rng.randint(2, 5)
        dist = eff * t
        dirn = "downstream" if mode == "down" else "upstream"
        dirn_hi = "धारा की दिशा में" if mode == "down" else "धारा के विपरीत"
        stem_hi = (f"शांत जल में एक नाव की चाल {b} किमी/घंटा तथा धारा की चाल {s} किमी/घंटा है। "
                   f"नाव {t} घंटों में {dirn_hi} कितनी दूर जा सकती है ?")
        sol_hi = (f"{dirn_hi} चाल = {b} {'+' if mode == 'down' else '-'} {s} = {eff} किमी/घंटा। "
                  f"दूरी = {eff} x {t} = {dist} किमी।")
        stem = (f"The speed of a boat in still water is {b} km/hr and the speed of the stream is "
                f"{s} km/hr. How far can the boat travel {dirn} in {t} hours?")
        sol = (f"{dirn.capitalize()} speed = {b} {'+' if mode == 'down' else '-'} {s} = {eff} "
               f"km/hr. Distance = {eff} x {t} = {dist} km.")
        wrong_dir = (b - s if mode == "down" else b + s) * t
        return {"stem": stem, "correct": f"{dist} km", "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("{} the stream speed instead of {}".format(
                        "subtracted" if mode == "down" else "added",
                        "adding it" if mode == "down" else "subtracting it"),
                     f"{wrong_dir} km"),
                    ("ignored the stream altogether", f"{b * t} km"),
                    ("added the stream speed to the distance rather than to the speed",
                     f"{b * t + s} km")),
                "concept": "Boats & Streams"}
    if diff == 2:
        down, up = b + s, b - s
        stem_hi = (f"एक नाव धारा की दिशा में {down} किमी/घंटा तथा धारा के विपरीत {up} किमी/घंटा "
                   f"की चाल से चलती है। शांत जल में नाव की चाल ज्ञात कीजिए।")
        sol_hi = (f"नाव की चाल = (अनुकूल + प्रतिकूल)/2 = ({down} + {up})/2 = {b} किमी/घंटा।")
        stem = (f"A boat covers {down} km/hr downstream and {up} km/hr upstream. Find the speed "
                f"of the boat in still water.")
        sol = (f"Boat speed = (downstream + upstream)/2 = ({down} + {up})/2 = {b} km/hr.")
        return {"stem": stem, "correct": f"{b} km/hr", "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("used the DIFFERENCE over 2, which gives the stream's speed",
                     f"{s} km/hr"),
                    ("added the two speeds without halving", f"{down + up} km/hr"),
                    ("took the downstream speed as the still-water speed", f"{down} km/hr")),
                "concept": "Boats & Streams"}
    if diff == 3:
        t_down = rng.randint(2, 4)
        dist = (b + s) * t_down
        t_up = Fraction(dist, b - s)
        if t_up.denominator != 1:                    # the time is PRINTED, keep it exact
            return _b_boats(rng, 2)
        stem_hi = (f"एक नाव {dist} किमी की दूरी धारा की दिशा में {t_down} घंटे में तथा उतनी ही "
                   f"दूरी धारा के विपरीत {_num(t_up)} घंटे में तय करती है। धारा की चाल "
                   f"ज्ञात कीजिए।")
        sol_hi = (f"अनुकूल चाल = {dist}/{t_down} = {b + s} किमी/घंटा; प्रतिकूल = "
                  f"{dist}/{_num(t_up)} = {b - s} किमी/घंटा। धारा = "
                  f"({b + s} - {b - s})/2 = {s} किमी/घंटा।")
        stem = (f"A boat covers {dist} km downstream in {t_down} hours and the same distance "
                f"upstream in {_num(t_up)} hours. Find the speed of the stream.")
        sol = (f"Downstream speed = {dist}/{t_down} = {b + s} km/hr; upstream = "
               f"{dist}/{_num(t_up)} = {b - s} km/hr. Stream = "
               f"({b + s} - {b - s})/2 = {s} km/hr.")
        return {"stem": stem, "correct": f"{s} km/hr", "solution": sol,
                "stem_hi": stem_hi, "solution_hi": sol_hi,
                "mistakes": mistakes(
                    ("used the SUM over 2, which gives the boat's speed", f"{b} km/hr"),
                    ("subtracted the two speeds without halving", f"{2 * s} km/hr"),
                    ("subtracted the two TIMES instead of the speeds",
                     f"{_num(abs(t_up - t_down))} km/hr")),
                "concept": "Boats & Streams"}
    # diff 4+ : down and back, total time given -> distance one way
    down, up = b + s, b - s
    dist = down * up * rng.randint(1, 3)            # makes both legs exact
    total = Fraction(dist, down) + Fraction(dist, up)
    stem_hi = (f"शांत जल में जिस नाव की चाल {b} किमी/घंटा है, वह एक स्थान तक जाकर वापस आती है। "
               f"धारा की चाल {s} किमी/घंटा है तथा पूरी यात्रा में {_num(total)} घंटे लगते हैं। "
               f"वह स्थान कितनी दूर है ?")
    sol_hi = (f"अनुकूल चाल {down} किमी/घंटा, प्रतिकूल {up} किमी/घंटा। "
              f"d/{down} + d/{up} = {_num(total)}, अतः d = {dist} किमी।")
    stem = (f"A boat whose speed in still water is {b} km/hr rows to a place and comes back. "
            f"The stream flows at {s} km/hr and the whole trip takes {_num(total)} hours. "
            f"How far is the place?")
    sol = (f"Downstream {down} km/hr, upstream {up} km/hr. d/{down} + d/{up} = {_num(total)}, "
           f"so d = {dist} km.")
    return {"stem": stem, "correct": f"{dist} km", "solution": sol,
            "stem_hi": stem_hi, "solution_hi": sol_hi,
            "mistakes": mistakes(
                ("used the still-water speed for both legs", f"{_num(Fraction(total * b, 2))} km"),
                ("treated the total time as the one-way time downstream",
                 f"{_num(total * down)} km"),
                ("gave the ROUND TRIP distance rather than the one-way distance",
                 f"{2 * dist} km")),
            "concept": "Boats & Streams"}

def _b_alligation(rng, diff):
    c1 = rng.choice([20, 24, 30])                   # cheaper price/kg
    c2 = c1 + rng.choice([10, 12, 20])              # dearer
    mean = rng.randint(c1 + 2, c2 - 2)
    ra, rb = c2 - mean, mean - c1
    g = math.gcd(ra, rb)
    ra, rb = ra // g, rb // g
    stem = (f"In what ratio must rice at {_rupees(c1)} per kg be mixed with rice at "
            f"{_rupees(c2)} per kg so that the mixture is worth {_rupees(mean)} per kg?")
    sol = (f"By alligation, ratio = (dearer - mean) : (mean - cheaper) = "
           f"({c2}-{mean}) : ({mean}-{c1}) = {c2-mean} : {mean-c1} = {ra} : {rb}.")
    d = [f"{rb} : {ra}", f"{ra+1} : {rb}", f"{c2-mean} : {mean-c1+1}"]
    return {"stem": stem, "correct": f"{ra} : {rb}", "distractors": d, "solution": sol,
            "concept": "Alligation"}

# ---- Mensuration ------------------------------------------------------------

def _b_mensuration(rng, diff):
    shape = rng.choice(["rect", "circle", "cylinder", "square", "cube"])
    if shape == "rect":
        l, w = rng.randint(8, 25), rng.randint(4, 15)
        stem = f"Find the area of a rectangle whose length is {l} cm and breadth is {w} cm."
        ans, sol = l * w, f"Area = length x breadth = {l} x {w} = {l*w} cm²."
        d = [f"{2*(l+w)} cm²", f"{l*w+l} cm²", f"{l*w-w} cm²"]
        return {"stem": stem, "correct": f"{ans} cm²", "distractors": d, "solution": sol,
                "concept": "2D Mensuration"}
    if shape == "square":
        a = rng.randint(6, 20)
        stem = f"The side of a square is {a} cm. Find its area."
        d = [f"{4*a} cm²", f"{a*a+a} cm²", f"{2*a} cm²"]
        return {"stem": stem, "correct": f"{a*a} cm²", "distractors": d,
                "solution": f"Area = side² = {a}² = {a*a} cm².", "concept": "2D Mensuration"}
    if shape == "circle":
        r = 7 * rng.randint(1, 4)                    # multiple of 7 → clean with 22/7
        area = Fraction(22, 7) * r * r
        stem = f"Find the area of a circle whose radius is {r} cm. (Use π = 22/7)"
        sol = f"Area = πr² = 22/7 x {r}² = {_num(area)} cm²."
        d = [f"{_num(Fraction(2)*Fraction(22,7)*r)} cm²", f"{_num(float(area)+r)} cm²", f"{r*r} cm²"]
        return {"stem": stem, "correct": f"{_num(area)} cm²", "distractors": d, "solution": sol,
                "concept": "2D Mensuration"}
    if shape == "cube":
        a = rng.randint(4, 14)
        stem = f"Find the volume of a cube of side {a} cm."
        d = [f"{6*a*a} cm³", f"{a*a} cm³", f"{a*a*a+a} cm³"]
        return {"stem": stem, "correct": f"{a**3} cm³", "distractors": d,
                "solution": f"Volume = side³ = {a}³ = {a**3} cm³.", "concept": "3D Mensuration"}
    r = 7 * rng.randint(1, 3)
    h = rng.randint(5, 20)
    vol = Fraction(22, 7) * r * r * h
    stem = f"Find the volume of a cylinder with radius {r} cm and height {h} cm. (Use π = 22/7)"
    sol = f"Volume = πr²h = 22/7 x {r}² x {h} = {_num(vol)} cm³."
    d = [f"{_num(Fraction(22,7)*r*r)} cm³", f"{_num(float(vol)+r)} cm³", f"{2*r*h} cm³"]
    return {"stem": stem, "correct": f"{_num(vol)} cm³", "distractors": d, "solution": sol,
            "concept": "3D Mensuration"}

# ---- Permutation, Combination & Probability --------------------------------

def _b_pnc(rng, diff):
    mode = rng.choice(["combo", "prob"])
    if mode == "combo":
        total = rng.randint(7, 11)
        pick = rng.randint(2, 3)
        ans = math.comb(total, pick)
        thing = rng.choice(["members for a committee", "players for a team", "books"])
        stem = f"In how many ways can {pick} {thing} be selected from {total}?"
        sol = f"Number of ways = C({total},{pick}) = {total}! / ({pick}! x {total-pick}!) = {ans}."
        d = [str(math.perm(total, pick)), str(ans + total), str(math.comb(total, pick - 1))]
        return {"stem": stem, "correct": str(ans), "distractors": d, "solution": sol,
                "concept": "Permutation & Combination"}
    # probability: bag of colored balls, P(one color)
    red, blue, green = rng.randint(3, 6), rng.randint(2, 5), rng.randint(2, 5)
    total = red + blue + green
    color, cnt = rng.choice([("red", red), ("blue", blue), ("green", green)])
    p = Fraction(cnt, total)
    stem = (f"A bag contains {red} red, {blue} blue and {green} green balls. One ball is drawn "
            f"at random. What is the probability that it is {color}?")
    sol = (f"Total balls = {red}+{blue}+{green} = {total}. P({color}) = {cnt}/{total} = {_frac(p)}.")
    d = [_frac(Fraction(total - cnt, total)), _frac(Fraction(cnt, total - cnt) if total != cnt else Fraction(1)),
         _frac(Fraction(cnt + 1, total))]
    return {"stem": stem, "correct": _frac(p), "distractors": d, "solution": sol,
            "concept": "Probability"}


# =============================================================================
# chapter -> builders
# =============================================================================

_CHAP_BUILDERS = {
    "Simplification & Approximation": [_b_simplify, _b_approx],
    "Number Series": [_b_series_missing, _b_series_wrong],
    "Quadratic Equations": [_b_quadratic],
    "Data Interpretation": [_b_di_table, _b_di_caselet],
    "Percentage": [_b_percentage],
    "Profit, Loss & Discount": [_b_profit_loss],
    "Simple & Compound Interest": [_b_si, _b_ci],
    "Ratio, Proportion & Partnership": [_b_ratio, _b_partnership],
    "Averages & Ages": [_b_average, _b_ages],
    "Time & Work": [_b_time_work, _b_pipes],
    "Speed, Time & Distance": [_b_std, _b_trains, _b_boats],
    "Mixtures & Alligations": [_b_alligation],
    "Mensuration": [_b_mensuration],
    "Permutation, Combination & Probability": [_b_pnc],
}


def _chapters_for(spec):
    ch = spec.get("chapter")
    if ch and ch in _CHAP_BUILDERS:
        return [ch]
    return list(_CHAP_BUILDERS.keys())              # no chapter → any


def generate_test(store, spec: dict, count: int = 5) -> dict:
    """Deterministic replacement for generator.generate_test — same return shape. Builds
    exam-authentic banking-quant questions and COMPUTES their answers; upserts them as
    verified generated questions (no figure, no LLM). Distinct within the run (retries on a
    stem-hash collision) so `count` fresh questions come back each call."""
    rng = random.Random()                           # system entropy → fresh numbers each run
    chapters = _chapters_for(spec)
    accepted, seen = [], set()
    attempts = 0
    while len(accepted) < count and attempts < count * 12:
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
        if q.hash in seen:
            continue
        seen.add(q.hash)
        store.upsert(q)
        accepted.append(q)
    return {
        "spec": spec,
        "generator": "quantgen-banking",
        "requested": count,
        "generated": len(accepted),
        "rejected": [],
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
    }
