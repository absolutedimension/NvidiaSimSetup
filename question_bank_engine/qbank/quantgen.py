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
    mode = rng.choice(["findSP", "findCP", "discount"])
    if mode == "findSP":
        cp = _mult(rng, 4, 20, 100)                 # multiple of 100 → SP is always whole
        pct = rng.choice([10, 12, 15, 20, 25])
        gain = rng.choice([1, -1])
        sp = cp * (100 + gain * pct) // 100
        word = "profit" if gain > 0 else "loss"
        stem = f"An article is bought for {_rupees(cp)} and sold at a {word} of {pct}%. Find the selling price."
        sol = f"SP = CP x (100 {'+' if gain>0 else '-'} {pct})/100 = {_rupees(cp)} x {100+gain*pct}/100 = {_rupees(sp)}."
        d = [_rupees(cp * (100 - gain * pct) // 100), _rupees(cp), _rupees(cp + pct)]
        return {"stem": stem, "correct": _rupees(sp), "distractors": d, "solution": sol,
                "concept": "Profit / Loss %"}
    if mode == "findCP":
        cp = _mult(rng, 4, 20, 100)                 # multiple of 100 → SP & recovered CP whole
        pct = rng.choice([10, 20, 25])
        sp = cp * (100 + pct) // 100
        stem = f"By selling an article for {_rupees(sp)}, a shopkeeper gains {pct}%. Find the cost price."
        sol = f"CP = SP x 100/(100+{pct}) = {_rupees(sp)} x 100/{100+pct} = {_rupees(cp)}."
        d = [_rupees(sp * 100 // (100 - pct)), _rupees(sp - pct), _rupees(sp * (100 - pct) // 100)]
        return {"stem": stem, "correct": _rupees(cp), "distractors": d, "solution": sol,
                "concept": "Profit / Loss %"}
    mp = _mult(rng, 4, 20, 100)
    disc = rng.choice([10, 15, 20, 25])
    sp = mp * (100 - disc) // 100
    stem = f"The marked price of an article is {_rupees(mp)}. A discount of {disc}% is offered. Find the selling price."
    sol = f"SP = MP x (100-{disc})/100 = {_rupees(mp)} x {100-disc}/100 = {_rupees(sp)}."
    d = [_rupees(mp * (100 + disc) // 100), _rupees(mp), _rupees(mp - disc)]
    return {"stem": stem, "correct": _rupees(sp), "distractors": d, "solution": sol,
            "concept": "Marked Price & Discount"}

# ---- Simple & Compound Interest --------------------------------------------

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
        return {"stem": stem, "correct": _rupees(si), "solution": sol,
                "mistakes": mistakes(
                    ("gave the AMOUNT (P + SI) instead of the interest", _rupees(p + si)),
                    ("used one year too many", _rupees(p * r * (t + 1) // 100)),
                    ("divided by 10 instead of 100", _rupees(p * r * t // 10))),
                "concept": "Simple Interest"}
    if diff == 2:
        amt = p + si
        stem = (f"What amount is received on {_rupees(p)} at {r}% per annum simple interest "
                f"after {t} years?")
        sol = (f"SI = {p} x {r} x {t}/100 = {_rupees(si)}. Amount = P + SI = {p} + {si} "
               f"= {_rupees(amt)}.")
        return {"stem": stem, "correct": _rupees(amt), "solution": sol,
                "mistakes": mistakes(
                    ("stopped at the interest and never added the principal", _rupees(si)),
                    ("added one year's interest instead of all {} years".format(t),
                     _rupees(p + p * r // 100)),
                    ("compounded instead of using simple interest",
                     _rupees(int(p * (1 + r / 100) ** t)))),
                "concept": "Simple Interest"}
    if diff == 3:
        stem = (f"A sum of {_rupees(p)} earns {_rupees(si)} as simple interest in {t} years. "
                f"Find the rate of interest per annum.")
        sol = (f"R = SI x 100 / (P x T) = {si} x 100 / ({p} x {t}) = {r}%.")
        return {"stem": stem, "correct": _pct(r), "solution": sol,
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
    stem = (f"A sum of {_rupees(total)} is lent partly at {r}% and the rest at {r2}% per annum "
            f"simple interest. If the total interest for one year is {_rupees(interest)}, find "
            f"the part lent at {r}%.")
    sol = (f"Let the part at {r}% be x. Then x x {r}/100 + ({total} - x) x {r2}/100 = {interest}. "
           f"Solving, x = {_rupees(x)}.")
    return {"stem": stem, "correct": _rupees(x), "solution": sol,
            "mistakes": mistakes(
                ("solved for the OTHER part, lent at {}%".format(r2), _rupees(y)),
                ("split the sum in the ratio of the two rates instead of solving",
                 _rupees(total * r // (r + r2))),
                ("halved the sum", _rupees(total // 2))),
            "concept": "Simple Interest"}

def _b_ci(rng, diff):
    mode = rng.choice(["amount", "diff"])
    p = _mult(rng, 4, 20, 500)
    r = rng.choice([5, 10, 20])
    if mode == "amount":
        t = 2
        amt = Fraction(p) * (1 + Fraction(r, 100)) ** t
        ci = amt - p
        stem = f"Find the compound interest on {_rupees(p)} at {r}% per annum for {t} years (compounded annually)."
        sol = (f"Amount = P(1+R/100)^T = {p}(1+{r}/100)^2 = {_num(amt)}. "
               f"CI = Amount - P = {_num(amt)} - {p} = {_num(ci)}.")
        si = p * r * t // 100
        d = [_rupees(si), _rupees(float(ci) + p * r // 100), _rupees(float(amt))]
        return {"stem": stem, "correct": _rupees(float(ci)), "distractors": d, "solution": sol,
                "concept": "Compound Interest"}
    # difference between CI and SI for 2 years = P (R/100)^2
    diffv = Fraction(p) * Fraction(r, 100) ** 2
    stem = (f"The difference between the compound interest and the simple interest on a sum of "
            f"{_rupees(p)} at {r}% per annum for 2 years is:")
    sol = f"Difference (2 yrs) = P(R/100)^2 = {p} x ({r}/100)^2 = {_num(diffv)}."
    d = [_rupees(float(diffv) * 2), _rupees(p * r // 100), _rupees(float(diffv) + 10)]
    return {"stem": stem, "correct": _rupees(float(diffv)), "distractors": d, "solution": sol,
            "concept": "Compound Interest"}

# ---- Ratio, Proportion & Partnership ---------------------------------------

def _b_ratio(rng, diff):
    a, b, c = rng.sample([2, 3, 4, 5, 6, 7], 3)
    unit = _mult(rng, 3, 12, 100)
    total = (a + b + c) * unit
    who = rng.randint(0, 2)
    parts = [a, b, c]
    share = parts[who] * unit
    stem = (f"An amount of {_rupees(total)} is divided among three people in the ratio "
            f"{a} : {b} : {c}. Find the share of the {['first','second','third'][who]} person.")
    sol = (f"Total ratio units = {a}+{b}+{c} = {a+b+c}. One unit = {total}/{a+b+c} = {unit}. "
           f"Share = {parts[who]} x {unit} = {share}.")
    d = [_rupees(parts[(who + 1) % 3] * unit), _rupees(parts[(who + 2) % 3] * unit),
         _rupees(share + unit)]
    return {"stem": stem, "correct": _rupees(share), "distractors": d, "solution": sol,
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
                "solution": sol, "concept": "Time & Work"}
    if diff == 2:
        worked = rng.randint(2, a - 2)
        rem = 1 - Fraction(worked, a)
        b_time = rem * b
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
                "solution": sol, "concept": "Time & Work"}
    if diff == 3:
        c = rng.choice([x for x in (6, 8, 9, 10, 12, 15, 18, 20, 24) if x not in (a, b)])
        tog = Fraction(1, Fraction(1, a) + Fraction(1, b) + Fraction(1, c))
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
    stem = (f"A and B together can complete a work in {_num(tog)} days. A alone can do it in "
            f"{a} days. In how many days can B alone complete the work?")
    sol = (f"B's one-day work = 1/{_num(tog)} - 1/{a} = {_frac(Fraction(1, b))}. "
           f"So B alone takes {b} days.")
    d = mistakes(("subtracted the TIMES instead of the rates",
                  _num(abs(a - tog)) + " days"),
                 ("added the times", _num(a + tog) + " days"),
                 ("doubled the joint time", _num(tog * 2) + " days"))
    return {"stem": stem, "correct": _num(b) + " days", "mistakes": d,
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
    b = rng.choice([8, 10, 12, 15, 18])
    s = rng.choice([2, 3, 4, 5])
    if s >= b:
        s = 2
    mode = rng.choice(["down", "up"])
    eff = b + s if mode == "down" else b - s
    t = rng.randint(2, 5)
    dist = eff * t
    dirn = "downstream" if mode == "down" else "upstream"
    stem = (f"The speed of a boat in still water is {b} km/hr and the speed of the stream is "
            f"{s} km/hr. How far can the boat travel {dirn} in {t} hours?")
    sol = (f"{dirn.capitalize()} speed = {b} {'+' if mode=='down' else '-'} {s} = {eff} km/hr. "
           f"Distance = {eff} x {t} = {dist} km.")
    other = (b - s if mode == "down" else b + s) * t
    d = [f"{other} km", f"{b*t} km", f"{dist + s} km"]
    return {"stem": stem, "correct": f"{dist} km", "distractors": d, "solution": sol,
            "concept": "Boats & Streams"}

# ---- Mixtures & Alligations -------------------------------------------------

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
