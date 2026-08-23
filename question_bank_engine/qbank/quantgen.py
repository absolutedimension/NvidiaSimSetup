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
    if f.denominator == 1:            # "1/1" is not how anyone writes one
        return str(f.numerator)
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


def mistakes(*pairs, correct=None):
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

    Pass `correct` and any mistake that happens to LAND on the right answer is dropped rather
    than offered — HCF(a, b) equals min(a, b) whenever a divides b, and 8^57 ends in 8 just as 8
    does. Without it those collapse into a duplicate option, which `_mcq` dedupes and then pads
    with `_perturb`: a question that looked like it had four error-derived options quietly ends up
    with three and a nudge. Every builder has this hazard; the ones written before this argument
    existed have not been audited for it.

    Usage:  "mistakes": mistakes(("added the times instead of the rates", _num(a + b) + " days"),
                                 ("took the average of the two times",    _num(avg) + " days"))
    """
    out = []
    for why, value in pairs:
        if value is None or not str(value).strip():
            continue
        if correct is not None and str(value) == str(correct):
            continue          # see the `correct` note in the signature
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

# ---- Simplification (BODMAS) ------------------------------------------------
# A simplification question is a SIGNED SUM OF TERMS, each term one small operation that has to be
# resolved before the additions can be done. It is built that way so that one difficulty band can
# print many different SHAPES.
#
# The previous version hard-coded exactly ONE expression per band. A delivered paper therefore
# printed SEVEN CONSECUTIVE questions of the identical form "(x)^2 + a/b - p% of c" — different
# numbers, indistinguishable to a reader. Every structural check passed; the page was indefensible.
# The per-template cap in build_onestep_paper is the guard, but a cap can only spread a section
# across shapes that exist, so the shapes had to exist first.
#
# Every term renders using ONLY the characters test_papers.solve_bodmas will re-parse — digits,
# space, ( ) x ^ % + - / . and the word "of" — so the independent solver can evaluate whatever
# shape the draw happens to compose, rather than knowing the four expressions by heart.

def _t_square(rng):
    r = rng.choice([7, 8, 9, 11, 12, 13, 14, 15])
    return {"en": f"({r})^2", "hi": f"({r})^2", "val": Fraction(r * r),
            "step_en": f"({r})^2 = {r * r}", "step_hi": f"({r})^2 = {r * r}",
            "wrong": [("doubled the base instead of squaring it", Fraction(2 * r)),
                      (f"left {r} as it stands instead of squaring it", Fraction(r))]}


def _t_percent(rng):
    p = rng.choice([10, 15, 20, 25, 40])
    q = _mult(rng, 4, 12, 20)
    val = Fraction(p * q, 100)
    return {"en": f"{p}% of {q}", "hi": f"{q} का {p}%", "val": val,
            "step_en": f"{p}% of {q} = {_num(val)}", "step_hi": f"{q} का {p}% = {_num(val)}",
            "wrong": [(f"read '{p}% of {q}' as the bare number {p}", Fraction(p)),
                      (f"used {q} itself instead of {p}% of it", Fraction(q))]}


def _t_divide(rng):
    n = rng.randint(3, 9)
    dvd = n * rng.randint(8, 30)                    # exact, so the answer stays clean
    return {"en": f"{dvd} / {n}", "hi": f"{dvd} / {n}", "val": Fraction(dvd, n),
            "step_en": f"{dvd} / {n} = {dvd // n}", "step_hi": f"{dvd} / {n} = {dvd // n}",
            # Both wrong values are whole numbers on purpose. "Divided the wrong way round" was
            # tried and printed options like -14.96 on a page whose every other number is an
            # integer — a named mistake nobody makes and an option anybody discards on sight.
            "wrong": [(f"subtracted {n} instead of dividing by it", Fraction(dvd - n)),
                      (f"multiplied by {n} instead of dividing by it", Fraction(dvd * n))]}


def _t_multiply(rng):
    m, n = rng.randint(6, 15), rng.randint(3, 9)
    return {"en": f"{m} x {n}", "hi": f"{m} x {n}", "val": Fraction(m * n),
            "step_en": f"{m} x {n} = {m * n}", "step_hi": f"{m} x {n} = {m * n}",
            "wrong": [(f"added {m} and {n} instead of multiplying them", Fraction(m + n)),
                      (f"subtracted {n} from {m} instead of multiplying them", Fraction(m - n))]}


def _t_bracket(rng):
    m, n = rng.randint(6, 15), rng.randint(3, 9)
    k = rng.randint(3, 9)
    return {"en": f"({m} x {n} - {k})", "hi": f"({m} x {n} - {k})", "val": Fraction(m * n - k),
            "step_en": f"bracket first: {m} x {n} - {k} = {m * n - k}",
            "step_hi": f"पहले कोष्ठक: {m} x {n} - {k} = {m * n - k}",
            "wrong": [("ignored the bracket and used only the product", Fraction(m * n)),
                      (f"took the bracket term by term, flipping the sign on {k}",
                       Fraction(m * n + k))]}


# Which KINDS of term each band composes. The ladder is the number of terms and whether an
# operation can be got out of order: 2 terms, then 3, then 3 with a division that must precede the
# addition, then 4 including a bracket that must be resolved first.
_BODMAS_BANDS = {
    1: lambda rng: [_t_percent, rng.choice([_t_square, _t_multiply])],
    2: lambda rng: [_t_percent, _t_square, _t_multiply],
    3: lambda rng: [_t_percent, _t_divide, rng.choice([_t_square, _t_multiply])],
    4: lambda rng: [_t_percent, _t_bracket, _t_square, rng.choice([_t_divide, _t_multiply])],
}


def _b_simplify(rng, diff):
    """BODMAS, composed from terms so that each band has many shapes rather than one.

    diff 1  two terms, no precedence trap
    diff 2  three terms, a square and a percentage among them
    diff 3  three terms including a division that must be done before the addition
    diff 4+ four terms including a bracket to resolve first
    """
    band = _BODMAS_BANDS[min(max(int(diff), 1), 4)]
    terms, signs, total = None, None, None
    for _ in range(40):
        terms = [f(rng) for f in band(rng)]
        rng.shuffle(terms)
        # Band 1 is additions only. With a subtraction, most of a two-term question's named
        # mistakes land BELOW zero — "15 x 6 - 20% of 200" had just two positive ones for three
        # slots, so the easy question printed -19 as an option. Making the easy band additive
        # removes the whole class rather than filtering the symptom.
        signs = [1] * len(terms) if int(diff) <= 1 else \
            [1] + [rng.choice([1, -1]) for _ in terms[1:]]
        total = sum(s * t["val"] for s, t in zip(signs, terms))
        if total > 0:                    # a negative answer reads as a typo, not as a hard question
            break
    else:
        signs = [1] * len(terms)
        total = sum(t["val"] for t in terms)

    def render(key):
        out = terms[0][key]
        for s, t in zip(signs[1:], terms[1:]):
            out += (" + " if s > 0 else " - ") + t[key]
        return out

    subbed = _num(terms[0]["val"]) + "".join(
        (" + " if s > 0 else " - ") + _num(t["val"]) for s, t in zip(signs[1:], terms[1:]))
    sol = "; ".join(t["step_en"] for t in terms) + f". So {subbed} = {_num(total)}."
    sol_hi = "; ".join(t["step_hi"] for t in terms) + f"। अतः {subbed} = {_num(total)}।"

    # Each named mistake is the SAME expression with one term resolved wrongly — so the distractor
    # is what a candidate who makes that specific slip actually writes down, not a nudge.
    mis = []
    for s, t in zip(signs, terms):
        for why, wrong_val in t.get("wrong", []):
            mis.append((why, _num(total - s * t["val"] + s * wrong_val)))
    neg = [i for i, s in enumerate(signs) if s < 0]
    if neg:
        i = neg[-1]
        mis.append((f"dropped the minus sign and added '{terms[i]['en']}' instead",
                    _num(total + 2 * terms[i]["val"])))
    # Six or seven named mistakes compete for three option slots, so which ones reach the page is a
    # CHOICE — the same dial reasoninggen.order_mistakes turns, which the maths builders never had.
    # Nothing here invents a distractor; the engine rests on every option being a mistake somebody
    # actually makes. It only orders the ones already computed.
    #
    #   - positive before negative, always. A sum of positive terms whose options include two
    #     negatives is answered by glancing at the signs.
    #   - hard bands take the CLOSEST wrong values, easy bands the farthest. Measured on a rebuilt
    #     page, "174/6 + (9)^2 + 20% of 180" was offering 285, 1161 and 83 against an answer of
    #     146; 1161 is a real slip (multiplying instead of dividing) and still discarded on sight.
    #     The same question's closest three are 130, 83 and 74.
    pos = [m for m in mis if float(m[1]) > 0]
    neg = [m for m in mis if float(m[1]) <= 0]
    if int(diff) >= 3:
        pos.sort(key=lambda m: abs(float(m[1]) - float(total)))
    elif int(diff) <= 1:
        pos.sort(key=lambda m: -abs(float(m[1]) - float(total)))
    mis = pos + neg

    return {"stem": f"What is the value of  {render('en')} ?",
            # The Hindi names what is being asked BEFORE the expression. Written the other way
            # round — "… - 140 का 15% का मान क्या है?" — a reader cannot tell whether the "मान"
            # belongs to the whole expression or only to the 15% term. Shipped that way once.
            #
            # NOT "निम्नलिखित व्यंजक" — व्यंजक is on paper_common._ABOVE_SYLLABUS, because
            # evaluating an algebraic expression is outside the Inter Level arithmetic syllabus.
            # Writing it here made the gate reject EVERY computation question and the topic came
            # back 0/7 on the next build. The gate was right; the wording was wrong.
            "stem_hi": f"निम्नलिखित का मान ज्ञात कीजिए:  {render('hi')}",
            "solution": sol, "solution_hi": sol_hi,
            "correct": _num(total), "mistakes": mistakes(*mis),
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

_SERIES_KINDS = ["arith2", "geom", "sqk", "muladd", "diffinc"]


def _series_seq(rng, diff, kinds=None):
    """Return (list_of_terms, description) for a valid banking-style series of 6 terms."""
    kind = rng.choice(kinds or _SERIES_KINDS)
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
    return {"stem": stem,
            "stem_hi": ("निम्नलिखित श्रृंखला में प्रश्नवाचक चिह्न (?) के स्थान पर क्या आएगा?\n"
                        f"{shown}"),
            "solution_hi": f"श्रृंखला का नियम देखने पर अगला पद {ans} है।",
            "correct": _num(ans), "distractors": d, "solution": sol,
            "concept": "Missing-Term Series"}

def _b_series_wrong(rng, diff):
    # "differences increase by k" is EXCLUDED here, and only here. Spoiling one term of such a
    # series can be re-read as a different starting term and a different step, so two different
    # terms are each defensibly "the wrong one" — measured at 67 of 798, while the other four
    # families gave 0 of 3,200. Continuing the series (_b_series_missing) is unaffected, so the
    # family stays available there.
    seq, desc = _series_seq(rng, diff, kinds=["arith2", "geom", "sqk", "muladd"])
    bad_i = rng.randint(1, 4)                        # never corrupt first term
    for delta in rng.sample([-3, -2, 2, 3, 4], 5):
        shown_vals = list(seq)
        shown_vals[bad_i] = seq[bad_i] + delta
        # The answer to this question is a VALUE, so the spoiled term must not equal another term
        # of the series. "2, 2, 8, 16, 32, 64" keys to "2" and prints 2 twice; only the second one
        # breaks the rule, so it is not mismarkable, but it reads as ambiguous. Found by rendering
        # the page — no structural check can see it.
        if shown_vals.count(shown_vals[bad_i]) == 1:
            break
    correct = str(shown_vals[bad_i])                # the wrong term (the answer they must spot)
    shown = ", ".join(str(x) for x in shown_vals)
    stem = (f"Find the WRONG term in the following number series:\n{shown}")
    sol = (f"The correct pattern is: {desc}. The term should be {seq[bad_i]}, "
           f"but {shown_vals[bad_i]} is given — so {shown_vals[bad_i]} is the wrong term.")
    # Hindi added 2026-08-21. Without it this builder could never appear on a bilingual paper, so
    # the Number Series topic had exactly ONE usable shape and its syllabus quota came back 4/5
    # every build — the shortfall was being topped up from a generator the section had not asked
    # for. Spotting the wrong term is also a different question from continuing the series, which
    # is the point: the quota is filled with variety rather than with a fifth "?" question.
    stem_hi = (f"निम्नलिखित संख्या श्रृंखला में गलत पद ज्ञात कीजिए:\n{shown}")
    sol_hi = (f"श्रृंखला का सही नियम लागू करने पर यह पद {seq[bad_i]} होना चाहिए, जबकि "
              f"{shown_vals[bad_i]} दिया गया है — अतः {shown_vals[bad_i]} गलत पद है।")
    d = mistakes(
        ("gave the term the pattern REQUIRES instead of the wrong term actually printed",
         str(seq[bad_i])),
        ("picked the term just after the one that breaks the pattern",
         str(shown_vals[bad_i + 1]) if bad_i + 1 < len(shown_vals) else ""),
        ("picked the term just before the one that breaks the pattern",
         str(shown_vals[bad_i - 1]) if bad_i - 1 >= 0 else ""),
        ("picked the last term of the series", str(shown_vals[-1])))
    return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "mistakes": d,
            "solution": sol, "solution_hi": sol_hi, "concept": "Wrong-Term Series"}

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

def _pc_of(rng):
    """d1 — one step, the percentage is given and the base is given."""
    p = rng.choice([12, 15, 18, 24, 35, 45])
    n = _mult(rng, 4, 15, 100)
    ans = Fraction(p * n, 100)
    return {"stem": f"What is {p}% of {n}?", "stem_hi": f"{n} का {p}% कितना है?",
            "solution": f"{p}% of {n} = {p}/100 x {n} = {_num(ans)}.",
            "solution_hi": f"{n} का {p}% = {p}/100 x {n} = {_num(ans)}।",
            "correct": _num(ans), "concept": "Percentage of a Number",
            "mistakes": mistakes(
                ("divided by 10 instead of by 100", _num(Fraction(p * n, 10))),
                (f"subtracted {p} from {n} instead of taking a percentage", _num(n - p)),
                (f"took {p}% of 100 instead of {p}% of {n}", _num(p)))}


def _pc_is_what(rng):
    """d2 — the percentage is what is asked for, so the division has a direction to get wrong."""
    b = _mult(rng, 4, 12, 50)
    a = b * rng.choice([20, 25, 40, 60, 75]) // 100
    pct = Fraction(a * 100, b)
    return {"stem": f"{a} is what percent of {b}?", "stem_hi": f"{a}, {b} का कितना प्रतिशत है?",
            "solution": f"Required % = ({a}/{b}) x 100 = {_num(pct)}%.",
            "solution_hi": f"अभीष्ट प्रतिशत = ({a}/{b}) x 100 = {_num(pct)}%।",
            "correct": _pct(pct), "concept": "Percentage of a Number",
            "mistakes": mistakes(
                (f"worked out what percent {b} is of {a} — the division the other way round",
                 _pct(Fraction(b * 100, a))),
                ("called the plain difference a percentage", _pct(b - a)),
                (f"gave {a}/{b} without multiplying by 100", _pct(Fraction(a, b))))}


def _pc_reverse(rng):
    """d2 — the base is the unknown. Dividing by the percentage instead of multiplying is the slip."""
    p = rng.choice([15, 20, 25, 30, 40])
    x = _mult(rng, 10, 60, 20)
    v = Fraction(p * x, 100)
    return {"stem": f"If {p}% of a number is {_num(v)}, what is the number?",
            "stem_hi": f"यदि किसी संख्या का {p}% {_num(v)} है, तो वह संख्या क्या है?",
            "solution": f"Number = {_num(v)} x 100/{p} = {x}.",
            "solution_hi": f"संख्या = {_num(v)} x 100/{p} = {x}।",
            "correct": _num(x), "concept": "Percentage of a Number",
            "mistakes": mistakes(
                (f"took {p}% of {_num(v)} instead of working backwards",
                 _num(Fraction(p, 100) * v)),
                (f"multiplied by {p} instead of dividing by it", _num(v * p)),
                (f"subtracted {p}% from {_num(v)}", _num(v * Fraction(100 - p, 100))))}


def _pc_change(rng):
    """d3 — the percentage change between two values. Which value is the base is the whole question."""
    # a = 100 is excluded on purpose: there the plain difference and the percentage are the same
    # number, so the "used the difference itself" distractor lands on the answer.
    a = _mult(rng, 6, 30, 20)
    pct = rng.choice([20, 25, 40, 50, 60])
    up = rng.choice([1, -1])
    b = Fraction(a * (100 + up * pct), 100)
    word, word_hi = ("increases", "बढ़कर") if up > 0 else ("decreases", "घटकर")
    ask, ask_hi = ("increase", "वृद्धि") if up > 0 else ("decrease", "कमी")
    return {"stem": f"A value {word} from {a} to {_num(b)}. What is the percentage {ask}?",
            "stem_hi": f"कोई मान {a} से {word_hi} {_num(b)} हो जाता है। प्रतिशत {ask_hi} क्या है?",
            "solution": (f"Change = {_num(abs(b - a))}. Percentage {ask} = "
                         f"{_num(abs(b - a))}/{a} x 100 = {pct}%."),
            "solution_hi": (f"परिवर्तन = {_num(abs(b - a))}। प्रतिशत {ask_hi} = "
                            f"{_num(abs(b - a))}/{a} x 100 = {pct}%।"),
            "correct": _pct(pct), "concept": "Percentage Change",
            "mistakes": mistakes(
                (f"took the change as a percentage of the NEW value {_num(b)} instead of "
                 f"the original {a}", _pct(abs(b - a) * 100 / b)),
                ("used the difference itself as the percentage", _pct(abs(b - a))),
                (f"gave {_num(b)} as a percentage of {a} rather than the change",
                 _pct(Fraction(100) * b / a)))}


def _pc_of_of(rng):
    """d3 — two percentages in succession. Adding them is the standard error."""
    p, q_ = rng.choice([10, 20, 25, 40, 50]), rng.choice([10, 20, 25, 40, 50])
    n = _mult(rng, 2, 10, 200)
    ans = Fraction(p * q_ * n, 10000)
    return {"stem": f"What is {p}% of {q_}% of {n}?",
            "stem_hi": f"{n} के {q_}% का {p}% कितना है?",
            "solution": (f"{q_}% of {n} = {_num(Fraction(q_ * n, 100))}; {p}% of that = "
                         f"{_num(ans)}."),
            "solution_hi": (f"{n} का {q_}% = {_num(Fraction(q_ * n, 100))}; उसका {p}% = "
                            f"{_num(ans)}।"),
            "correct": _num(ans), "concept": "Percentage of a Number",
            "mistakes": mistakes(
                (f"added the two percentages and took {p + q_}% of {n}",
                 _num(Fraction((p + q_) * n, 100))),
                (f"took {q_}% of {n} and stopped", _num(Fraction(q_ * n, 100))),
                ("divided by 100 once instead of twice", _num(Fraction(p * q_ * n, 100))))}


def _pc_to_original(rng):
    """d4 — the successive change is given and the ORIGINAL is asked. Two steps, both reversed."""
    for _ in range(40):
        x = _mult(rng, 2, 15, 400)
        up, dn = rng.choice([20, 25, 50]), rng.choice([10, 20, 25])
        f = Fraction(x * (100 + up) * (100 - dn), 10000)
        if f.denominator == 1:
            break
    return {"stem": (f"A value is first increased by {up}% and the result is then decreased by "
                     f"{dn}%, leaving {_num(f)}. What was the original value?"),
            "stem_hi": (f"किसी मान में पहले {up}% की वृद्धि की जाती है और फिर प्राप्त परिणाम में "
                        f"{dn}% की कमी की जाती है, जिससे {_num(f)} बचता है। मूल मान क्या था?"),
            "solution": (f"Original = {_num(f)} x 100/{100 - dn} x 100/{100 + up} = {x}."),
            "solution_hi": (f"मूल मान = {_num(f)} x 100/{100 - dn} x 100/{100 + up} = {x}।"),
            "correct": _num(x), "concept": "Percentage Change",
            "mistakes": mistakes(
                (f"treated the two changes as a net {up - dn}% and worked back from that",
                 _num(f * 100 / Fraction(100 + up - dn))),
                ("reversed only the increase", _num(f * 100 / Fraction(100 + up))),
                ("reversed only the decrease", _num(f * 100 / Fraction(100 - dn))))}


def _pc_more_less(rng):
    """d4 — 'A is p% more than B' and 'B is q% less than A' are NOT the same number, and the
    question is built so that answering p is the natural wrong move."""
    # p = 100 is excluded: 100/(100+p) and p/(100+p) are both 50% there, so one named mistake
    # would land on the answer.
    p = rng.choice([20, 25, 50])
    # Three percentages alone would be three questions. The context is an incidental feature — it
    # does not change the work — but without it this template can only ever appear three times.
    what, what_hi = rng.choice([("salary", "वेतन"), ("income", "आय"),
                                ("weight", "भार"), ("marks", "अंक")])
    ans = Fraction(p * 100, 100 + p)
    return {"stem": (f"A's {what} is {p}% more than B's. B's {what} is what percent less "
                     f"than A's?"),
            "stem_hi": (f"A का {what_hi} B के {what_hi} से {p}% अधिक है। B का {what_hi}, A के "
                        f"{what_hi} से कितने प्रतिशत कम है?"),
            "solution": (f"Take B = 100, so A = {100 + p}. B is less than A by {p}, which is "
                         f"{p}/{100 + p} x 100 = {_num(ans)}% of A."),
            "solution_hi": (f"मान लीजिए B = 100, तब A = {100 + p}। B, A से {p} कम है, जो A का "
                            f"{p}/{100 + p} x 100 = {_num(ans)}% है।"),
            "correct": _pct(ans), "concept": "Percentage Change",
            "mistakes": mistakes(
                (f"answered {p}% — assumed 'more than' and 'less than' are symmetric", _pct(p)),
                (f"gave 100/{100 + p} as a percentage instead of {p}/{100 + p}",
                 _pct(Fraction(100 * 100, 100 + p))),
                (f"subtracted {p} from 100", _pct(100 - p)))}


# Which templates each band may use. The old builder picked one of three modes at random and
# ignored `diff` entirely, so the difficulty badge on a percentage question was decoration — and
# with only three shapes a quota of nine could not be spread across templates at all.
_PCT_BANDS = {
    1: [_pc_of],
    2: [_pc_is_what, _pc_reverse],
    3: [_pc_change, _pc_of_of],
    4: [_pc_to_original, _pc_more_less],
}


def _b_percentage(rng, diff):
    return rng.choice(_PCT_BANDS[min(max(int(diff), 1), 4)])(rng)

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
        return {"stem": stem,
                "stem_hi": ("निम्नलिखित संख्याओं का औसत ज्ञात कीजिए: "
                            + ", ".join(map(str, nums)) + "।"),
                "solution_hi": f"योग = {total}; औसत = {total}/{n} = {_num(ans)}।",
                "correct": _num(ans), "mistakes": d, "solution": sol,
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
        cand = [("forgot to multiply the rise by the number of students", old_m + change),
                ("gave the NEW AVERAGE instead of the new student's age", old_avg + change),
                ("added the rise to the OLD AVERAGE instead of the replaced student's age",
                 old_avg + n2 * change),
                ("subtracted the total rise instead of adding it", old_m - n2 * change)]
        # An age of zero or less is not a wrong answer anybody writes down — it is an option a
        # candidate crosses out without reading it. Found by RENDERING the page: with old_m = 24,
        # 8 students and a rise of 3, "subtracted the total rise" lands exactly on 0, and the
        # paper offered "0" as a student's age. The mistake is still named and still offered; it
        # is simply only offered when it lands on an age that could exist.
        d = mistakes(*[(why, _num(v)) for why, v in cand if v > 0])
        return {"stem": stem,
                "stem_hi": (f"{n2} विद्यार्थियों की औसत आयु {old_avg} वर्ष है। जब {old_m} वर्ष "
                            f"आयु वाले एक विद्यार्थी के स्थान पर एक नया विद्यार्थी आता है, तो "
                            f"औसत {change} वर्ष बढ़ जाता है। नए विद्यार्थी की आयु ज्ञात कीजिए।"),
                "solution_hi": (f"कुल वृद्धि = {n2} x {change} = {n2 * change}। नए विद्यार्थी की "
                                f"आयु = {old_m} + {n2 * change} = {new_m} वर्ष।"),
                "correct": _num(new_m), "mistakes": d, "solution": sol,
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
        return {"stem": stem,
                "stem_hi": (f"{n1} लड़कों का औसत भार {a1} किग्रा तथा {n2} लड़कियों का औसत भार "
                            f"{a2} किग्रा है। पूरी कक्षा का औसत भार ज्ञात कीजिए।"),
                "solution_hi": (f"कुल = {n1} x {a1} + {n2} x {a2} = {n1 * a1 + n2 * a2}; "
                                f"संख्या = {n1 + n2}; औसत = {_num(ans)} किग्रा।"),
                "correct": _num(ans), "mistakes": d, "solution": sol,
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
    return {"stem": stem,
            "stem_hi": (f"{n} संख्याओं का औसत {wrong_avg} पाया गया। बाद में ज्ञात हुआ कि एक "
                        f"संख्या {actual} के स्थान पर {misread} पढ़ ली गई थी। सही औसत ज्ञात कीजिए।"),
            "solution_hi": (f"सही योग = {n} x {wrong_avg} - {misread} + {actual} = "
                            f"{n * wrong_avg - misread + actual}। सही औसत = {_num(correct_avg)}।"),
            "correct": _num(correct_avg), "mistakes": d, "solution": sol,
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

def _pick3(cands, correct):
    """Three DISTINCT named mistakes, none of them the answer, in the order given.

    Builders offer more candidates than they need because a computed mistake can collide — with
    the answer, or with another mistake. Stress-testing `_b_number_system` over 1,600 draws found
    400 questions where it did: HCF(a, b) is min(a, b) whenever a divides b, |a - b| is 0 when the
    two numbers coincide, and a unit-digit question has only ten possible values to begin with, so
    three independent errors land on the same digit constantly. None of it failed loudly — `_mcq`
    deduped and `_perturb` filled the gap with a nudge of the answer.
    """
    out, seen = [], {str(correct)}
    for why, val in cands:
        if val is None:
            continue
        t = str(val)
        if t in seen or not t.strip():
            continue
        seen.add(t)
        out.append((why, t))
        if len(out) == 3:
            break
    return mistakes(*out, correct=correct)


def _b_number_system(rng, diff):
    """संख्या पद्धति. 10% of the BSSC Inter Level maths syllabus and previously ungenerated.

    diff 1  HCF / LCM of two numbers — computed with math.gcd, never by factor-hunting
    diff 2  place value vs face value, which the commission asks by that name
    diff 3  the unit digit of a large power, by its 4-cycle
    diff 4+ the classic LCM word problem: bells tolling together

    Every answer is computed, so the key cannot be wrong. What can still be wrong is the OPTION
    SET — see `_pick3`, which every band here routes through.
    """
    if diff <= 1:
        # Redraw while either number divides the other. That degeneracy is not just an option-set
        # problem — when a divides b the HCF simply IS the smaller number and the LCM IS the
        # larger, so a student answers by inspection and every named mistake collapses onto the
        # answer. Found by stress-testing 6,000 draws: 11 of them were "the HCF of 46 and 92".
        a = rng.randint(12, 60) * 2
        b = rng.randint(12, 60) * 2
        while b == a or a % b == 0 or b % a == 0:
            b = rng.randint(12, 60) * 2
        g, l = math.gcd(a, b), a * b // math.gcd(a, b)
        if rng.random() < 0.5:
            stem = f"Find the HCF (greatest common divisor) of {a} and {b}."
            stem_hi = f"{a} तथा {b} का महत्तम समापवर्तक (HCF) ज्ञात कीजिए।"
            ans, sol = g, f"HCF({a}, {b}) = {g}."
            sol_hi = f"HCF({a}, {b}) = {g}।"
            cands = [("gave the LCM instead of the HCF", _num(l)),
                     ("took the difference of the two numbers", _num(abs(a - b))),
                     ("gave the smaller number itself", _num(min(a, b))),
                     ("divided the product by the smaller number", _num(a * b // min(a, b))),
                     ("doubled the HCF", _num(2 * g)),
                     ("halved the smaller number", _num(min(a, b) // 2))]
        else:
            stem = f"Find the LCM (least common multiple) of {a} and {b}."
            stem_hi = f"{a} तथा {b} का लघुत्तम समापवर्त्य (LCM) ज्ञात कीजिए।"
            ans, sol = l, f"LCM({a}, {b}) = ({a} x {b}) / HCF = {a * b} / {g} = {l}."
            sol_hi = f"LCM({a}, {b}) = ({a} x {b}) / HCF = {a * b} / {g} = {l}।"
            cands = [("gave the HCF instead of the LCM", _num(g)),
                     ("multiplied the two numbers without dividing by the HCF", _num(a * b)),
                     ("gave the larger number itself", _num(max(a, b))),
                     ("added the two numbers", _num(a + b)),
                     ("halved the LCM", _num(l // 2)),
                     ("doubled the larger number", _num(2 * max(a, b)))]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _num(ans),
                "mistakes": _pick3(cands, _num(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "HCF & LCM"}

    if diff == 2:
        # A repeated digit would leave "place value" ambiguous about WHICH occurrence is meant,
        # so the chosen digit appears once and the others are drawn to avoid it.
        digit = rng.randint(2, 9)
        pos = rng.randint(1, 4)                     # never the units place: the difference is 0
        others = [str(rng.choice([x for x in range(1, 10) if x != digit])) for _ in range(5)]
        ds = others[:]
        ds.insert(len(ds) - pos, str(digit))
        number = int("".join(ds))
        place = digit * (10 ** pos)
        ans = place - digit
        stem = (f"In the number {number:,}, what is the difference between the place value "
                f"and the face value of the digit {digit}?")
        stem_hi = (f"संख्या {number:,} में अंक {digit} के स्थानीय मान तथा जातीय मान का "
                   f"अंतर क्या है?")
        sol = (f"Place value = {digit} x {10 ** pos} = {place}; face value = {digit}. "
               f"Difference = {place} - {digit} = {ans}.")
        sol_hi = (f"स्थानीय मान = {digit} x {10 ** pos} = {place}; जातीय मान = {digit}। "
                  f"अंतर = {place} - {digit} = {ans}।")
        cands = [("gave the PLACE VALUE instead of the difference", _num(place)),
                 ("gave the FACE VALUE instead of the difference", _num(digit)),
                 ("added the two values instead of subtracting", _num(place + digit)),
                 ("read the digit one place further left", _num(digit * 10 ** (pos + 1) - digit)),
                 ("read the digit one place further right", _num(digit * 10 ** (pos - 1) - digit))]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _num(ans),
                "mistakes": _pick3(cands, _num(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "Place & Face Value"}

    if diff == 3:
        # The answer is ONE DIGIT, so there are only nine possible wrong answers in the whole
        # question and three independent "errors" collide constantly. Distractors are therefore
        # drawn from the structure the question is about — the other positions of the base's own
        # repeating cycle — and only then topped up from the digits its powers never produce.
        base, power = rng.choice([2, 3, 4, 7, 8, 9]), rng.randint(20, 99)
        ans = pow(base, power, 10)
        cyc = [pow(base, e, 10) for e in range(1, 5)]
        stem = f"What is the unit digit of {base}^{power}?"
        stem_hi = f"{base}^{power} का इकाई अंक क्या है?"
        sol = (f"The unit digits of {base}^1, {base}^2, ... repeat with period 4: "
               f"{cyc}. {power} mod 4 = {power % 4}, so the unit digit is {ans}.")
        sol_hi = (f"{base} की घातों के इकाई अंक 4 के चक्र में दोहराते हैं: {cyc}। "
                  f"{power} mod 4 = {power % 4}, अतः इकाई अंक {ans} है।")
        cands = [("read the wrong position of the repeating cycle", _num(c))
                 for c in dict.fromkeys(cyc) if c != ans]
        cands += [("chose a digit the powers of this base never end in", _num(d))
                  for d in (1, 6, 4, 9, 5, 0, 2, 3, 7, 8) if d != ans and d not in cyc]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _num(ans),
                "mistakes": _pick3(cands, _num(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "Unit Digit"}

    ints = sorted(rng.sample([4, 6, 8, 9, 10, 12, 15, 16, 18], 3))
    l = ints[0]
    for x in ints[1:]:
        l = l * x // math.gcd(l, x)
    g3 = math.gcd(math.gcd(ints[0], ints[1]), ints[2])
    l2 = ints[0] * ints[1] // math.gcd(ints[0], ints[1])
    stem = (f"Three bells toll at intervals of {ints[0]}, {ints[1]} and {ints[2]} minutes "
            f"respectively. If they toll together now, after how many minutes will they "
            f"next toll together?")
    stem_hi = (f"तीन घंटियाँ क्रमशः {ints[0]}, {ints[1]} तथा {ints[2]} मिनट के अंतराल पर "
               f"बजती हैं। यदि वे अभी एक साथ बजती हैं, तो कितने मिनट बाद पुनः एक साथ बजेंगी?")
    sol = f"They coincide after LCM({ints[0]}, {ints[1]}, {ints[2]}) = {l} minutes."
    sol_hi = f"वे LCM({ints[0]}, {ints[1]}, {ints[2]}) = {l} मिनट बाद एक साथ बजेंगी।"
    # "1 minute" is not an answer anyone writes down — it is one they cross out unread, the same
    # defect _b_average documents at age 0. The HCF mistake is still named, and only offered when
    # it lands on a time that could plausibly be meant.
    cands = [("took the HCF instead of the LCM", _num(g3) if g3 > 1 else None),
             ("added the three intervals", _num(sum(ints))),
             ("multiplied the three intervals", _num(ints[0] * ints[1] * ints[2])),
             ("took the LCM of only the first two intervals", _num(l2)),
             ("doubled the largest interval", _num(2 * ints[2])),
             ("halved the LCM", _num(l // 2)),
             ("took the LCM of the two largest intervals",
              _num(ints[1] * ints[2] // math.gcd(ints[1], ints[2])))]
    return {"stem": stem, "stem_hi": stem_hi, "correct": _num(l),
            "mistakes": _pick3(cands, _num(l)),
            "solution": sol, "solution_hi": sol_hi, "concept": "LCM Word Problem"}


def _b_decimal_fraction(rng, diff):
    """दशमलव और भिन्न. 8% of the BSSC Inter Level maths syllabus and previously ungenerated.

    diff 1  order four fractions and name the largest / smallest
    diff 2  a fraction OF a quantity, in two steps
    diff 3  a recurring decimal converted to a fraction in lowest terms
    diff 4+ a compound fraction expression, evaluated exactly

    Everything is held as a Fraction and only formatted at the end, so "0.333" never enters the
    arithmetic. The answer is exact by construction; `_pick3` keeps the option set honest.
    """
    if diff <= 1:
        # Denominators drawn distinct so no two fractions can be equal, and numerators kept
        # proper — an improper fraction among proper ones is orderable at a glance and the
        # question stops being about comparison.
        dens = rng.sample([3, 4, 5, 6, 7, 8, 9, 11, 13], 4)
        fr = []
        for d0 in dens:
            n0 = rng.randint(1, d0 - 1)
            fr.append(Fraction(n0, d0))
        if len(set(fr)) < 4:
            return _b_decimal_fraction(rng, 2)          # degenerate draw: ask something else
        want_max = rng.random() < 0.5
        ans = max(fr) if want_max else min(fr)
        shown = ", ".join(_frac(f) for f in fr)
        word, word_hi = ("largest", "सबसे बड़ी") if want_max else ("smallest", "सबसे छोटी")
        stem = f"Which of the following fractions is the {word}?  {shown}"
        stem_hi = f"निम्नलिखित भिन्नों में {word_hi} भिन्न कौन-सी है?  {shown}"
        sol = ("As decimals: " + ", ".join(f"{_frac(f)} = {round(float(f), 4)}" for f in fr)
               + f". The {word} is {_frac(ans)}.")
        sol_hi = ("दशमलव में: " + ", ".join(f"{_frac(f)} = {round(float(f), 4)}" for f in fr)
                  + f"। {word_hi} भिन्न {_frac(ans)} है।")
        other = min(fr) if want_max else max(fr)
        by_num = max(fr, key=lambda f: f.numerator) if want_max else min(fr, key=lambda f: f.numerator)
        by_den = max(fr, key=lambda f: f.denominator) if want_max else min(fr, key=lambda f: f.denominator)
        cands = [(f"gave the {'smallest' if want_max else 'largest'} instead", _frac(other)),
                 ("compared the numerators only", _frac(by_num)),
                 ("compared the denominators only", _frac(by_den))]
        cands += [("picked another fraction from the list", _frac(f)) for f in fr if f != ans]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _frac(ans),
                "mistakes": _pick3(cands, _frac(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "Comparing Fractions"}

    if diff == 2:
        d1, d2 = rng.choice([(3, 5), (4, 7), (5, 8), (3, 8), (5, 9), (4, 9)])
        n1, n2 = rng.randint(1, d1 - 1), rng.randint(1, d2 - 1)
        total = rng.randint(6, 30) * d1 * d2                  # keeps every step a whole number
        f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
        first = total * f1
        # `total`, not `first`: the question asks for f2 of the NUMBER, not of the part already
        # given. Writing `first * f2` here made the key the very mistake this builder's own
        # distractor list names two screens down ("applied the second fraction to the given part,
        # not to the number") — and the printed solution disagreed with the printed key without
        # anything noticing. Caught by the independent solver in test_papers.py, on 2,201 of
        # 16,000 draws, which is the entire reason that house rule exists.
        ans = total * f2
        stem = (f"{_frac(f1)} of a number is {_num(first)}. What is {_frac(f2)} of that "
                f"same number?")
        stem_hi = (f"किसी संख्या का {_frac(f1)} भाग {_num(first)} है। उसी संख्या का "
                   f"{_frac(f2)} भाग कितना है?")
        sol = (f"The number = {_num(first)} / ({_frac(f1)}) = {_num(total)}. "
               f"{_frac(f2)} of {_num(total)} = {_num(ans)}.")
        sol_hi = (f"संख्या = {_num(first)} / ({_frac(f1)}) = {_num(total)}। "
                  f"{_num(total)} का {_frac(f2)} भाग = {_num(ans)}।")
        # The answer is always a whole number here (total is drawn as a multiple of d1*d2), so a
        # distractor that comes out fractional is eliminated on sight and the question loses an
        # option without losing a line. Only whole-valued mistakes are offered.
        def _whole(x):
            return _num(x) if Fraction(x).denominator == 1 else None
        cands = [("applied the second fraction to the given part, not to the number",
                  _whole(first * f2)),
                 ("gave the whole number instead of the fraction of it", _whole(total)),
                 ("multiplied the two fractions and applied that to the given part",
                  _whole(first * f1 * f2)),
                 ("divided instead of multiplying at the last step", _whole(total / f2)),
                 ("gave the given part back", _whole(first)),
                 ("applied the FIRST fraction again instead of the second", _whole(total * f1)),
                 ("added the two fractions and applied that", _whole(total * (f1 + f2)))]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _num(ans),
                "mistakes": _pick3(cands, _num(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "Fraction of a Quantity"}

    if diff == 3:
        # PURELY recurring, one or two repeating digits: the value is (repeat)/(as many 9s), which
        # is a rule a candidate either knows or does not. A mixed recurring decimal needs the
        # (whole - non-recurring)/(9s then 0s) form and is above Inter Level.
        digits = rng.choice([1, 2])
        rep = rng.randint(1, 8) if digits == 1 else rng.randint(10, 98)
        nines = int("9" * digits)
        ans = Fraction(rep, nines)
        shown = "0." + (str(rep).zfill(digits) * 3) + "..."
        stem = f"Express the recurring decimal {shown} as a fraction in its lowest terms."
        stem_hi = f"आवर्ती दशमलव {shown} को न्यूनतम रूप की भिन्न में व्यक्त कीजिए।"
        reduced = "" if f"{rep}/{nines}" == _frac(ans) else f" = {_frac(ans)}"
        sol = (f"A purely recurring decimal equals the repeating block over as many 9s: "
               f"{rep}/{nines}{reduced}.")
        sol_hi = (f"शुद्ध आवर्ती दशमलव = आवर्ती अंक / उतने ही 9 : "
                  f"{rep}/{nines}{reduced}।")
        cands = [("put the repeating block over 10s instead of 9s",
                  _frac(Fraction(rep, 10 ** digits))),
                 ("used one 9 too many", _frac(Fraction(rep, int("9" * (digits + 1))))),
                 ("used one 9 too few",
                  _frac(Fraction(rep, int("9" * (digits - 1)))) if digits > 1 else None),
                 ("inverted the fraction", _frac(Fraction(nines, rep))),
                 ("put the block over 99 regardless of its length", _frac(Fraction(rep, 99)))]
        return {"stem": stem, "stem_hi": stem_hi, "correct": _frac(ans),
                "mistakes": _pick3(cands, _frac(ans)),
                "solution": sol, "solution_hi": sol_hi, "concept": "Recurring Decimal"}

    b1, b2, b3 = rng.choice([2, 3, 4, 6]), rng.choice([3, 5, 7, 8]), rng.choice([2, 4, 5])
    a1, a2, a3 = rng.randint(1, b1 - 1), rng.randint(1, b2 - 1), rng.randint(1, b3 - 1)
    f1, f2, f3 = Fraction(a1, b1), Fraction(a2, b2), Fraction(a3, b3)
    ans = (f1 + f2) * f3
    stem = f"Evaluate:  ({_frac(f1)} + {_frac(f2)}) x {_frac(f3)}"
    stem_hi = f"मान ज्ञात कीजिए:  ({_frac(f1)} + {_frac(f2)}) x {_frac(f3)}"
    sol = (f"{_frac(f1)} + {_frac(f2)} = {_frac(f1 + f2)}; "
           f"{_frac(f1 + f2)} x {_frac(f3)} = {_frac(ans)}.")
    sol_hi = (f"{_frac(f1)} + {_frac(f2)} = {_frac(f1 + f2)}; "
              f"{_frac(f1 + f2)} x {_frac(f3)} = {_frac(ans)}।")
    cands = [("added all three instead of multiplying the last", _frac(f1 + f2 + f3)),
             ("multiplied before adding, ignoring the bracket", _frac(f1 + f2 * f3)),
             ("added the numerators and the denominators separately",
              _frac(Fraction(a1 + a2, b1 + b2) * f3)),
             ("divided by the third fraction instead of multiplying", _frac((f1 + f2) / f3)),
             ("left out the third fraction", _frac(f1 + f2))]
    return {"stem": stem, "stem_hi": stem_hi, "correct": _frac(ans),
            "mistakes": _pick3(cands, _frac(ans)),
            "solution": sol, "solution_hi": sol_hi, "concept": "Fraction Simplification"}


_CHAP_BUILDERS = {
    "Simplification & Approximation": [_b_simplify, _b_approx],
    "Number System": [_b_number_system],
    "Decimals & Fractions": [_b_decimal_fraction],
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
