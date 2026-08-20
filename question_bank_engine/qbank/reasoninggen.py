"""COMPUTE-THE-ANSWER reasoning engine — the deterministic generator for the SSC / Railway /
Banking / BPSC "Reasoning" (General Intelligence & Reasoning / Reasoning Ability) section.

The sibling of qbank.quantgen: govt-job reasoning has NO usable pre-tagged/pre-keyed bank on
HuggingFace (checked 2026-08-12 — every candidate was junk), but the common reasoning question
types are ALGORITHMIC — coding-decoding, blood relations, direction sense, series, analogy,
odd-one-out, ranking. So we PARAMETRICALLY build an exam-authentic reasoning question and
COMPUTE its answer in plain Python. Exam-shaped because templated from real SSC/Banking
patterns; correct because Python computed it → impossible to serve a wrong key, copyright-clean
(our own values), UNLIMITED (fresh every call).

Live path: generator.generate_test() routes here when can_generate() covers the (exam, subject),
bypassing the LLM/RAG path entirely — so reasoning works with ZERO ingested data.

Each chapter maps to one or more builders. A builder(rng, diff) returns:
  {stem, correct, distractors, solution, [options], [concept]}
where `correct` and each distractor are already-formatted option strings.
"""
import hashlib
import math
import random

from . import reasoning_hi as HI
from .models import Question, content_hash

SUBJECT = "Reasoning"
EXAM = "SSC CGL"

_SUBJECT_ALIASES = {
    "reasoning", "reasoning ability", "general intelligence & reasoning",
    "general intelligence and reasoning", "general intelligence", "logical reasoning",
}


def can_generate(exam, subject, chapter=None) -> bool:
    """True when the compute-the-answer reasoning engine covers this (subject, chapter).
    Reasoning is entirely generator-served, so every chapter in the taxonomy is coverable."""
    if (subject or "").strip().lower() not in _SUBJECT_ALIASES:
        return False
    if not chapter:
        return True
    return chapter in _CHAP_BUILDERS


# ---- MCQ assembly (mirrors quantgen) ---------------------------------------

def _mcq(seed: str, correct: str, distractors, rng, n: int = 4, fixed=None):
    labels = ["A", "B", "C", "D", "E"][:n]
    if fixed:
        opts = list(fixed)[:n]
    else:
        opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))
        if len(opts) < n:
            opts = _pad(opts, str(correct), n)          # backstop: never serve < n options
        opts = opts[:n]
        if str(correct) not in opts:
            opts[-1] = str(correct)
        rot = sum(map(ord, seed)) % n
        opts = opts[rot:] + opts[:rot]
    options = [{"label": l, "text": t} for l, t in zip(labels, opts)]
    ans = labels[opts.index(str(correct))]
    return options, ans


def _pad(opts, correct, n):
    """Backstop so we never serve fewer than n options. If the answer is numeric (optionally
    with a trailing unit like ' km'), add ±k perturbations; otherwise append short letter
    variants. Only fires when a builder's distractors collapsed on dedup."""
    def parse(s):
        head = str(s).split(" ", 1)
        try:
            return float(head[0].replace(",", "")), (" " + head[1] if len(head) > 1 else "")
        except ValueError:
            return None, None
    base, unit = parse(correct)
    k = 1
    while len(opts) < n and k < 80:
        if base is not None:
            for cand in (base + k, base - k, base + 2 * k):
                if cand <= 0:
                    continue
                head = str(int(cand)) if float(cand).is_integer() else str(round(cand, 2))
                s = head + unit
                if s not in opts:
                    opts.append(s)
                    if len(opts) >= n:
                        break
        else:
            s = str(correct) + "'" * k
            if s not in opts:
                opts.append(s)
        k += 1
    return opts


def _make_question(built: dict, rng, spec) -> Question:
    stem = built["stem"].strip()
    n_opts = len(built["options"]) if built.get("options") else 4
    # Error-derived distractors win over hand-nudged ones. A "mistake" that lands ON the correct
    # answer is dropped and flagged: those numbers reward a wrong method, so a candidate who
    # forgets the -1 scores the mark and learns the wrong lesson.
    mis = [m for m in (built.get("mistakes") or []) if m["text"] != str(built["correct"])]
    collided = [m for m in (built.get("mistakes") or []) if m["text"] == str(built["correct"])]
    options, ans = _mcq(stem, built["correct"],
                        [m["text"] for m in mis] or built.get("distractors", []),
                        rng, n=n_opts, fixed=built.get("options"))
    diff = spec.get("dmax") or spec.get("dmin") or 2
    qid = "gen_reason_" + hashlib.md5(
        (spec.get("chapter", "") + "|" + stem).encode()).hexdigest()[:14]
    # Hindi mirrors. Options are mapped AFTER _mcq has shuffled, so the Hindi option order
    # always matches the English one — a student comparing the two halves must see (B) = (B).
    hi_map = built.get("hi_opts") or {}
    options_hi = ([{"label": o["label"], "text": hi_map.get(o["text"], o["text"])} for o in options]
                  if built.get("stem_hi") else [])
    q = Question(
        id=qid, exam=spec.get("exam") or EXAM, subject=spec.get("subject") or SUBJECT,
        stem=stem, qtype="MCQ_single", options=options, correct_answer=ans,
        solution=built.get("solution", ""),
        stem_hi=(built.get("stem_hi") or "").strip(),
        options_hi=options_hi,
        solution_hi=(built.get("solution_hi") or "").strip(),
        chapter=spec.get("chapter"), concept=built.get("concept"), difficulty=diff,
        source="reasoninggen", generated=True, hash=content_hash(stem))
    q.verified = True
    by_text = {m["text"]: m["why"] for m in mis}
    q.distractor_why = {o["label"]: by_text[o["text"]] for o in options if o["text"] in by_text}
    q.rewards_a_wrong_method = [m["why"] for m in collided]
    return q


# ---- letter helpers ---------------------------------------------------------

_A = ord("A")

def _shift_word(word, k):
    return "".join(chr((ord(c) - _A + k) % 26 + _A) for c in word)

def _pos(c):                      # A=1..Z=26
    return ord(c) - _A + 1

def _letter(n):                   # 1->A (1-indexed, wraps)
    return chr((n - 1) % 26 + _A)


# =============================================================================
# BUILDERS
# =============================================================================

_WORDS = ["TABLE", "CHAIR", "PLANT", "WATER", "LIGHT", "STONE", "BRAIN", "CLOUD",
          "HORSE", "MONEY", "PAPER", "RIVER", "TIGER", "GRAPE", "MUSIC", "FIELD",
          "BREAD", "SUGAR", "NIGHT", "EARTH", "OCEAN", "FRUIT", "GLASS", "SNAKE"]

# ---- Coding-Decoding --------------------------------------------------------


def mistakes(*pairs):
    """Distractors COMPUTED BY MAKING A NAMED MISTAKE, not by nudging the answer.

    Same argument as quantgen's: an attractive wrong answer is the one a candidate actually
    arrives at — forgetting the -1 in a ranking count, turning the wrong way, shifting the
    alphabet one place too far. Distractors built as answer±1 are attractive to nobody and let
    the question fall to elimination. The label also survives into the paper, so "picked C" can
    later mean "counted the person twice" instead of just "wrong".
    """
    out = []
    for why, value in pairs:
        if value is not None and str(value).strip():
            out.append({"why": why, "text": str(value)})
    return out


def _b_coding_shift(rng, diff):
    """Letter coding. Difficulty = how the shift varies across the word.

    diff 1  one shift for every letter
    diff 2  alternating shifts (+k on odd positions, -k on even)
    diff 3  the word is REVERSED and then shifted
    diff 4+ a positional shift: the first letter moves 1, the second 2, and so on
    """
    w1, w2 = rng.sample(_WORDS, 2)
    k = rng.choice([1, 2, 3, 4, -1, -2, -3])
    sign = f"+{k}" if k > 0 else str(k)
    if diff <= 1:
        c1, c2 = _shift_word(w1, k), _shift_word(w2, k)
        rule = f"Each letter is shifted by {sign} position(s) in the alphabet"
        rule_hi = f"प्रत्येक अक्षर को वर्णमाला में {sign} स्थान खिसकाया गया है"
        d = mistakes(("shifted one place too far", _shift_word(w2, k + 1)),
                     ("shifted one place short", _shift_word(w2, k - 1)),
                     ("shifted in the opposite direction", _shift_word(w2, -k)))
    elif diff == 2:
        alt = lambda w: "".join(chr((ord(c) - _A + (k if i % 2 == 0 else -k)) % 26 + _A)
                                for i, c in enumerate(w))
        c1, c2 = alt(w1), alt(w2)
        rule = (f"Letters in odd positions move {sign} and letters in even positions move the "
                f"opposite way")
        rule_hi = (f"विषम स्थान के अक्षर {sign} खिसकते हैं तथा सम स्थान के अक्षर विपरीत दिशा में")
        d = mistakes(("shifted every letter the same way", _shift_word(w2, k)),
                     ("applied the two shifts the other way round",
                      "".join(chr((ord(c) - _A + (-k if i % 2 == 0 else k)) % 26 + _A)
                              for i, c in enumerate(w2))),
                     ("shifted every letter the opposite way", _shift_word(w2, -k)))
    elif diff == 3:
        rev = lambda w: _shift_word(w[::-1], k)
        c1, c2 = rev(w1), rev(w2)
        rule = f"The word is reversed and then each letter is shifted by {sign}"
        rule_hi = f"शब्द को उल्टा लिखकर प्रत्येक अक्षर को {sign} स्थान खिसकाया गया है"
        d = mistakes(("shifted without reversing", _shift_word(w2, k)),
                     ("reversed without shifting", w2[::-1]),
                     ("shifted first and then reversed", _shift_word(w2, k)[::-1]))
    else:
        posn = lambda w: "".join(chr((ord(c) - _A + (i + 1)) % 26 + _A) for i, c in enumerate(w))
        c1, c2 = posn(w1), posn(w2)
        rule = ("The first letter moves 1 place, the second 2 places, the third 3, and so on")
        rule_hi = ("पहला अक्षर 1 स्थान, दूसरा 2 स्थान, तीसरा 3 स्थान — इसी क्रम में आगे बढ़ता है")
        d = mistakes(("used the same shift for every letter", _shift_word(w2, 1)),
                     ("started the count from 0 instead of 1",
                      "".join(chr((ord(c) - _A + i) % 26 + _A) for i, c in enumerate(w2))),
                     ("moved each letter backwards by its position",
                      "".join(chr((ord(c) - _A - (i + 1)) % 26 + _A) for i, c in enumerate(w2))))
    stem = (f"In a certain code language, '{w1}' is written as '{c1}'. "
            f"How is '{w2}' written in that same code?")
    sol = f"{rule} ({w1}->{c1}). Applying the same rule to {w2} gives {c2}."
    stem_hi = (f"एक निश्चित कूट भाषा में '{w1}' को '{c1}' लिखा जाता है। "
               f"उसी कूट भाषा में '{w2}' को कैसे लिखा जाएगा?")
    sol_hi = f"{rule_hi} ({w1}→{c1}); अतः {w2} → {c2}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": c2,
            "mistakes": d, "solution": sol, "concept": "Letter-Shift Coding"}

def _b_coding_number(rng, diff):
    w = rng.choice(_WORDS)
    op = rng.choice(["pos", "pos+1", "pos*2"])
    # The Hindi USED to say only "अपनी वर्णमाला-स्थिति के अनुसार" for all three rules, dropping the
    # "one more than" / "twice" that IS the question. A Hindi-medium candidate was shown a
    # different, easier question than the English one — and paper_common.numbers_agree() then
    # silently discarded every such question from the paper, so the pool lost them too. Naming the
    # rule in Hindi fixes both: 103 of 1,300 generated questions were failing that check.
    if op == "pos":
        vals = [_pos(c) for c in w]
        desc = "its position in the alphabet (A=1, B=2, …)"
        desc_hi = "उसकी वर्णमाला-स्थिति के अनुसार (A=1, B=2, …)"
    elif op == "pos+1":
        vals = [_pos(c) + 1 for c in w]
        desc = "one more than its position in the alphabet (A=2, B=3, …)"
        desc_hi = "उसकी वर्णमाला-स्थिति से एक अधिक (A=2, B=3, …)"
    else:
        vals = [_pos(c) * 2 for c in w]
        desc = "twice its position in the alphabet (A=2, B=4, …)"
        desc_hi = "उसकी वर्णमाला-स्थिति से दोगुना (A=2, B=4, …)"
    code = " ".join(str(v) for v in vals)
    stem = (f"If each letter is coded by {desc}, how is '{w}' coded?")
    sol = f"{w}: " + ", ".join(f"{c}={v}" for c, v in zip(w, vals)) + f" → {code}."
    cands = [" ".join(str(_pos(c)) for c in w),
             " ".join(str(_pos(c) * 2) for c in w),
             " ".join(str(_pos(c) * 2 + 1) for c in w),
             " ".join(str(_pos(c) + 2) for c in w),
             " ".join(str(_pos(c) + 1) for c in w),
             " ".join(str(_pos(c) - 1) for c in w)]
    d = [x for x in dict.fromkeys(cands) if x != code][:3]
    stem_hi = (f"यदि प्रत्येक अक्षर को {desc_hi} कूटबद्ध किया जाए, तो '{w}' का कूट क्या होगा?")
    sol_hi = f"{w}: " + ", ".join(f"{c}={v}" for c, v in zip(w, vals)) + f" → {code}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": code,
            "mistakes": mistakes(
                ("used the plain position, ignoring the rule",
                 " ".join(str(_pos(c)) for c in w)),
                ("doubled the position instead of applying the stated rule",
                 " ".join(str(_pos(c) * 2) for c in w)),
                ("added one to the position instead of applying the stated rule",
                 " ".join(str(_pos(c) + 1) for c in w))),
            "solution": sol, "concept": "Number Coding"}

# ---- Alphabet / Letter Series ----------------------------------------------

def _b_letter_series(rng, diff):
    """Letter series. Difficulty = how the step behaves.

    diff 1  a constant step
    diff 2  the step ALTERNATES between two values
    diff 3  the step GROWS by one each time
    diff 4+ two series interleaved, so alternate terms belong to different progressions
    """
    start = rng.randint(1, 12)
    if diff <= 1:
        step = rng.choice([2, 3, 4, 5])
        terms = [start + i * step for i in range(5)]
        rule = f"The letters advance by {step} position(s) each time"
        rule_hi = f"प्रत्येक बार अक्षर {step} स्थान आगे बढ़ता है"
        wrong = [("used a step of {} instead".format(step + 1), start + 4 * (step + 1)),
                 ("used a step of {} instead".format(step - 1), start + 4 * (step - 1)),
                 ("stopped one term early", start + 3 * step)]
    elif diff == 2:
        s1, s2 = rng.choice([(2, 3), (3, 1), (4, 2), (1, 4)])
        terms = [start]
        for i in range(4):
            terms.append(terms[-1] + (s1 if i % 2 == 0 else s2))
        rule = f"The step alternates: +{s1}, +{s2}, +{s1}, +{s2}"
        rule_hi = f"अंतराल क्रमशः बदलता है: +{s1}, +{s2}, +{s1}, +{s2}"
        wrong = [("used the other step for the last gap", terms[3] + s2),
                 ("used a constant step of {}".format(s1), start + 4 * s1),
                 ("used a constant step of {}".format(s2), start + 4 * s2)]
    elif diff == 3:
        step = rng.choice([1, 2])
        terms, st = [start], step
        for _ in range(4):
            terms.append(terms[-1] + st)
            st += 1
        rule = f"The gap grows by one each time: +{step}, +{step + 1}, +{step + 2}, +{step + 3}"
        rule_hi = f"अंतराल हर बार एक बढ़ता है: +{step}, +{step + 1}, +{step + 2}, +{step + 3}"
        wrong = [("kept the gap constant", start + 4 * step),
                 ("grew the gap but from the wrong start", terms[3] + step + 2),
                 ("repeated the previous gap", terms[3] + step + 1)]
    else:
        s1, s2 = rng.choice([(2, 3), (3, 4), (1, 5)])
        # odd terms advance by s1, even terms by s2; the 5th term continues the ODD series
        odd = [start, start + s1, start + 2 * s1]
        even = [start + 7, start + 7 + s2]
        terms = [odd[0], even[0], odd[1], even[1], odd[2]]
        rule = (f"Two series are interleaved: the 1st, 3rd and 5th terms advance by {s1}, "
                f"while the 2nd and 4th advance by {s2}")
        rule_hi = (f"दो श्रृंखलाएँ मिली हुई हैं: पहला, तीसरा और पाँचवाँ पद {s1} बढ़ता है, "
                   f"जबकि दूसरा और चौथा पद {s2} बढ़ता है")
        wrong = [("treated it as one series", terms[3] + s1),
                 ("continued the SECOND series instead of the first", even[1] + s2),
                 ("advanced the first series by the second series' step", odd[1] + s2)]
    letters = [_letter(t) for t in terms[:4]]
    ans = _letter(terms[4])
    shown = ", ".join(letters) + ", ?"
    stem = f"Find the next term in the letter series:\n{shown}"
    sol = f"{rule} ({'->'.join(letters)}). Next = {ans}."
    stem_hi = f"अक्षर श्रृंखला में अगला पद ज्ञात कीजिए:\n{shown}"
    sol_hi = f"{rule_hi}; अतः अगला पद = {ans}।"
    d = mistakes(*[(why, _letter(v)) for why, v in wrong])
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans,
            "mistakes": d, "solution": sol, "concept": "Letter Series"}

def _b_alnum_series(rng, diff):
    """Letter+number series. Difficulty = how the two components behave.

    diff 1  both steps constant
    diff 2  the NUMBER step alternates while the letter step stays constant
    diff 3  the number step grows by one each time
    diff 4+ the letters run BACKWARDS while the numbers still climb — two components moving in
            opposite directions is where a candidate who spotted only one of them comes unstuck
    """
    lstart = rng.randint(1, 15)
    lstep = rng.choice([2, 3, 4])
    nstart = rng.choice([2, 3, 5])
    nstep = rng.choice([2, 3, 4])
    if diff == 2:
        alt = rng.choice([x for x in (1, 2, 3, 5) if x != nstep])   # else d2 == d1
        nums = [nstart]
        for i in range(4):
            nums.append(nums[-1] + (nstep if i % 2 == 0 else alt))
        pairs = [(_letter(lstart + i * lstep), nums[i]) for i in range(5)]
    elif diff == 3:
        nums, st = [nstart], nstep
        for _ in range(4):
            nums.append(nums[-1] + st)
            st += 1
        pairs = [(_letter(lstart + i * lstep), nums[i]) for i in range(5)]
    elif diff >= 4:
        lstart = rng.randint(14, 24)
        pairs = [(_letter(lstart - i * lstep), nstart + i * nstep) for i in range(5)]
    else:
        pairs = [(_letter(lstart + i * lstep), nstart + i * nstep) for i in range(5)]
    shown = ", ".join(f"{c}{n}" for c, n in pairs[:4]) + ", ?"
    ans = f"{pairs[4][0]}{pairs[4][1]}"
    stem = f"What comes next in the series?\n{shown}"
    sol = (f"Letters advance by {lstep} ({'→'.join(p[0] for p in pairs)}); "
           f"numbers increase by {nstep} ({'→'.join(str(p[1]) for p in pairs)}). Next = {ans}.")
    d = [f"{_letter(lstart + 4 * lstep + 1)}{pairs[4][1]}",
         f"{pairs[4][0]}{pairs[4][1] + 1}",
         f"{pairs[4][0]}{pairs[4][1] - nstep}"]
    d = [x for x in dict.fromkeys(d) if x != ans][:3]
    stem_hi = f"निम्नलिखित श्रृंखला में आगे क्या आएगा?\n{shown}"
    sol_hi = f"अक्षर {lstep} स्थान तथा संख्याएँ {nstep} बढ़ती हैं; अतः अगला पद = {ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans, "distractors": d, "solution": sol,
            "concept": "Alphanumeric Series"}

# ---- Analogy ----------------------------------------------------------------

def _b_number_analogy(rng, diff):
    rule = rng.choice(["square", "cube", "double", "next", "triple"])
    a = rng.randint(2, 12)
    c = rng.randint(2, 12)
    while c == a:
        c = rng.randint(2, 12)
    fn = {"square": lambda x: x * x, "cube": lambda x: x ** 3, "double": lambda x: 2 * x,
          "next": lambda x: x + 1, "triple": lambda x: 3 * x}[rule]
    desc = {"square": "square of the number", "cube": "cube of the number",
            "double": "twice the number", "next": "the number plus 1",
            "triple": "thrice the number"}[rule]
    b, ans = fn(a), fn(c)
    stem = f"{a} : {b} :: {c} : ?"
    sol = f"The second term is {desc} ({a}→{b}). So {c}→{ans}."
    cands = [str(ans + c), str(ans - 1), str(ans + 1), str(fn(c + 1)), str(ans + c + 1)]
    d = [x for x in dict.fromkeys(cands) if x != str(ans)][:3]
    stem_hi = f"{a} : {b} :: {c} : ?"
    sol_hi = f"दूसरा पद पहले पद का सम्बन्ध दर्शाता है ({a}→{b}); उसी नियम से {c}→{ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(ans), "distractors": d, "solution": sol,
            "concept": "Number Analogy"}

def _b_letter_analogy(rng, diff):
    k = rng.choice([1, 2, 3, 4])
    a = rng.randint(1, 10)
    c = rng.randint(1, 18)
    while c == a:
        c = rng.randint(1, 18)
    pa = _letter(a) + _letter(a + 1)
    pb = _letter(a + k) + _letter(a + 1 + k)
    pc = _letter(c) + _letter(c + 1)
    ans = _letter(c + k) + _letter(c + 1 + k)
    stem = f"{pa} : {pb} :: {pc} : ?"
    sol = (f"Each letter moves +{k} in the alphabet ({pa}→{pb}). "
           f"Applying +{k} to {pc} gives {ans}.")
    d = [_letter(c + k + 1) + _letter(c + 2 + k),
         _letter(c - k) + _letter(c + 1 - k),
         _letter(c + k) + _letter(c + k)]
    d = [x for x in dict.fromkeys(d) if x != ans][:3]
    stem_hi = f"{pa} : {pb} :: {pc} : ?"
    sol_hi = f"प्रत्येक अक्षर वर्णमाला में +{k} स्थान बढ़ता है ({pa}→{pb}); अतः {pc} → {ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans, "distractors": d, "solution": sol,
            "concept": "Letter Analogy"}

# ---- Odd One Out ------------------------------------------------------------

def _b_odd_square(rng, diff):
    squares = rng.sample([n * n for n in range(3, 13)], 3)
    odd = rng.choice([x for x in range(20, 140) if int(x ** 0.5) ** 2 != x])
    opts = squares + [odd]
    rng.shuffle(opts)
    stem = "Three of the following four numbers are alike; find the ODD one out:\n" + \
           ",  ".join(str(x) for x in opts)
    sol = (f"{', '.join(str(s) for s in squares)} are perfect squares "
           f"({'; '.join(f'{int(s**0.5)}²={s}' for s in squares)}); {odd} is not. "
           f"So {odd} is the odd one out.")
    d = [str(x) for x in squares]
    stem_hi = ("निम्नलिखित चार संख्याओं में से तीन एक समान हैं; असंगत (ODD) संख्या चुनिए:\n"
               + ",  ".join(str(x) for x in opts))
    sol_hi = f"शेष तीनों पूर्ण वर्ग हैं; {odd} पूर्ण वर्ग नहीं है, अतः यही असंगत है।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(odd), "distractors": d, "solution": sol,
            "concept": "Odd One Out (Numbers)"}

def _b_odd_prime(rng, diff):
    primes = rng.sample([7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43], 3)
    def is_prime(n):
        return n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
    comp = rng.choice([x for x in range(8, 50) if not is_prime(x)])
    opts = primes + [comp]
    rng.shuffle(opts)
    stem = "Three of the following four numbers are alike; find the ODD one out:\n" + \
           ",  ".join(str(x) for x in opts)
    sol = (f"{', '.join(str(p) for p in primes)} are prime numbers; "
           f"{comp} is composite ({comp} = {comp//_smallest_factor(comp)} × {_smallest_factor(comp)}). "
           f"So {comp} is the odd one out.")
    d = [str(x) for x in primes]
    stem_hi = ("निम्नलिखित चार संख्याओं में से तीन एक समान हैं; असंगत (ODD) संख्या चुनिए:\n"
               + ",  ".join(str(x) for x in opts))
    sol_hi = f"शेष तीनों अभाज्य संख्याएँ हैं; {comp} भाज्य है, अतः यही असंगत है।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(comp), "distractors": d, "solution": sol,
            "concept": "Odd One Out (Numbers)"}

def _smallest_factor(n):
    for i in range(2, n):
        if n % i == 0:
            return i
    return n

# ---- Ranking & Ordering -----------------------------------------------------

def _b_ranking(rng, diff):
    """Ranking. Difficulty = how many positions have to be held at once.

    diff 1  two positions      -> the total (the -1 is the whole test)
    diff 2  total and one end  -> the other end
    diff 3  two people         -> how many sit between them
    diff 4+ an interchange     -> a new position after two people swap
    """
    name = rng.choice(["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Anjali", "Rohan"])
    other = rng.choice([x for x in ("Rahul", "Priya", "Amit", "Sneha", "Vikas") if x != name])
    if diff <= 1:
        left, right = rng.randint(3, 12), rng.randint(3, 12)
        total = left + right - 1
        stem = (f"In a row of students, {name} is {_ord(left)} from the left end and "
                f"{_ord(right)} from the right end. How many students are there in the row?")
        sol = (f"Total = (position from left) + (position from right) - 1 = "
               f"{left} + {right} - 1 = {total}.")
        stem_hi = (f"विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से {HI.ordinal(left)} स्थान "
                   f"पर तथा दाईं ओर से {HI.ordinal(right)} स्थान पर है। पंक्ति में कुल कितने विद्यार्थी हैं?")
        sol_hi = f"कुल = बाएँ से स्थान + दाएँ से स्थान - 1 = {left} + {right} - 1 = {total}।"
        d = mistakes(("counted the person twice by forgetting the -1", str(total + 1)),
                     ("subtracted 1 twice", str(total - 1)),
                     ("added the two positions and then added 1", str(total + 2)))
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(total),
                "mistakes": d, "solution": sol, "concept": "Ranking"}
    if diff == 2:
        total = rng.randint(20, 45)
        left = rng.randint(5, total - 5)
        right = total - left + 1
        stem = (f"In a row of {total} students, {name} is {_ord(left)} from the left end. "
                f"What is {name}'s position from the right end?")
        sol = (f"Position from right = total - position from left + 1 = "
               f"{total} - {left} + 1 = {right}.")
        stem_hi = (f"{total} विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से "
                   f"{HI.ordinal(left)} स्थान पर है। दाईं ओर से उसका स्थान क्या है?")
        sol_hi = f"दाएँ से स्थान = कुल - बाएँ से स्थान + 1 = {total} - {left} + 1 = {right}।"
        d = mistakes(("forgot the +1", str(right - 1)),
                     ("added 1 twice", str(right + 1)),
                     ("subtracted the position from the total and stopped there",
                      str(total - left))) 
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(right),
                "mistakes": d, "solution": sol, "concept": "Ranking"}
    if diff == 3:
        total = rng.randint(25, 45)
        a_left = rng.randint(4, 12)
        b_right = rng.randint(4, 12)
        b_left = total - b_right + 1
        if b_left <= a_left + 1:
            return _b_ranking(rng, 2)
        between = b_left - a_left - 1
        stem = (f"In a row of {total} students, {name} is {_ord(a_left)} from the left end and "
                f"{other} is {_ord(b_right)} from the right end. How many students are sitting "
                f"between {name} and {other}?")
        sol = (f"{other}'s position from the left = {total} - {b_right} + 1 = {b_left}. "
               f"Students between = {b_left} - {a_left} - 1 = {between}.")
        stem_hi = (f"{total} विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से "
                   f"{HI.ordinal(a_left)} स्थान पर तथा {HI.name(other)} दाईं ओर से "
                   f"{HI.ordinal(b_right)} स्थान पर है। {HI.name(name)} और {HI.name(other)} के "
                   f"बीच कितने विद्यार्थी बैठे हैं?")
        sol_hi = (f"{HI.name(other)} का बाएँ से स्थान = {total} - {b_right} + 1 = {b_left}। "
                  f"बीच में = {b_left} - {a_left} - 1 = {between}।")
        d = mistakes(("counted one of the two people as 'between'", str(between + 1)),
                     ("counted both of them", str(between + 2)),
                     ("subtracted the two given positions directly, without converting "
                      "the right-end one", str(abs(b_right - a_left))))
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(between),
                "mistakes": d, "solution": sol, "concept": "Ranking"}
    # diff 4+ : an interchange
    total = rng.randint(28, 45)
    a_left = rng.randint(5, 14)
    b_left = rng.randint(a_left + 3, min(a_left + 14, total - 2))
    new_right = total - b_left + 1
    stem = (f"In a row of {total} students, {name} is {_ord(a_left)} from the left end. "
            f"{other} is {_ord(b_left)} from the left end. If {name} and {other} interchange "
            f"their places, what will be {name}'s new position from the RIGHT end?")
    sol = (f"After the swap {name} stands where {other} stood, i.e. {_ord(b_left)} from the "
           f"left. Position from right = {total} - {b_left} + 1 = {new_right}.")
    stem_hi = (f"{total} विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से "
               f"{HI.ordinal(a_left)} स्थान पर तथा {HI.name(other)} बाईं ओर से "
               f"{HI.ordinal(b_left)} स्थान पर है। यदि {HI.name(name)} और {HI.name(other)} अपने "
               f"स्थान बदल लें, तो {HI.name(name)} का दाईं ओर से नया स्थान क्या होगा?")
    sol_hi = (f"स्थान बदलने पर {HI.name(name)} बाएँ से {HI.ordinal(b_left)} स्थान पर आ जाता है। "
              f"दाएँ से स्थान = {total} - {b_left} + 1 = {new_right}।")
    d = mistakes(("gave the new position from the LEFT instead of the right", str(b_left)),
                 ("used the original position from the left", str(total - a_left + 1)),
                 ("forgot the +1 after subtracting", str(total - b_left)))
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(new_right),
            "mistakes": d, "solution": sol, "concept": "Ranking"}

def _b_ranking_pos(rng, diff):
    total = rng.randint(20, 45)
    left = rng.randint(5, total - 5)
    right = total - left + 1
    name = rng.choice(["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Anjali"])
    stem = (f"In a row of {total} students, {name} is {_ord(left)} from the left end. "
            f"What is {name}'s position from the right end?")
    sol = (f"Position from right = total − position from left + 1 = "
           f"{total} − {left} + 1 = {right}.")
    cands = [str(right + 1), str(right - 1), str(right + 2), str(right - 2)]
    d = [x for x in dict.fromkeys(cands) if x != str(right) and x != "0"][:3]
    stem_hi = (f"{total} विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से {HI.ordinal(left)} "
               f"स्थान पर है। दाईं ओर से उसका स्थान क्या है?")
    sol_hi = f"दाएँ से स्थान = कुल − बाएँ से स्थान + 1 = {total} − {left} + 1 = {right}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(right), "distractors": d, "solution": sol,
            "concept": "Ranking"}

def _ord(n):
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"

# ---- Direction Sense --------------------------------------------------------

def _b_direction_distance(rng, diff):
    """Direction sense by displacement. Difficulty = how many legs, and whether the DIRECTION
    of the displacement is asked as well as its size.

    diff 1  two perpendicular legs        -> straight-line distance
    diff 2  three legs, two of them on the same axis -> distance (the cancellation is the test)
    diff 3  four legs                     -> distance AND the direction from the start
    diff 4+ four legs                     -> the direction only, which cannot be got by
                                             Pythagoras and forces the candidate to track signs
    """
    TRIPLES = {(3, 4): 5, (6, 8): 10, (8, 15): 17, (9, 12): 15, (5, 12): 13}
    (a, b), hyp = rng.choice(list(TRIPLES.items()))
    name = rng.choice(["A man", "Ravi", "A boy", "Sita"])
    he = "she" if name == "Sita" else "he"
    he_hi = "वह"
    if diff <= 1:
        stem = (f"{name} starts from a point and walks {a} km towards North, then turns right "
                f"and walks {b} km towards East. How far is {he} now from the starting point?")
        sol = (f"North {a} km and East {b} km are perpendicular. Distance = "
               f"sqrt({a}^2 + {b}^2) = sqrt({a * a + b * b}) = {hyp} km.")
        stem_hi = (f"एक व्यक्ति एक बिंदु से चलना आरम्भ करता है और उत्तर दिशा में {a} किमी चलता है, "
                   f"फिर दाएँ मुड़कर पूर्व दिशा में {b} किमी चलता है। अब {he_hi} प्रारम्भिक बिंदु से "
                   f"कितनी दूर है?")
        sol_hi = (f"उत्तर और पूर्व लम्बवत हैं; दूरी = √({a}² + {b}²) = √{a * a + b * b} = "
                  f"{hyp} किमी।")
        d = mistakes(("added the two distances instead of using Pythagoras", f"{a + b} km"),
                     ("subtracted them", f"{abs(a - b)} km"),
                     ("used only the longer leg", f"{max(a, b)} km"))
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi,
                "correct": f"{hyp} km", "mistakes": d, "solution": sol,
                "concept": "Direction — Distance"}
    if diff == 2:
        # Build the NET legs from a triple rather than hoping a random walk lands on one. The
        # first version retried at difficulty 1 when the root came out irrational, so d2 silently
        # printed the d1 question for most seeds — a difficulty level that quietly wasn't one.
        (net_n, b), root = rng.choice(list(TRIPLES.items()))
        back = rng.randint(1, 4)
        a = net_n + back
        stem = (f"{name} walks {a} km towards North, then turns right and walks {b} km, and "
                f"finally walks {back} km towards South. How far is {he} from the starting "
                f"point?")
        sol = (f"North {a} then South {back} leaves {net_n} km North; East {b} km is unchanged. "
               f"Distance = sqrt({net_n}^2 + {b}^2) = {root} km.")
        stem_hi = (f"एक व्यक्ति उत्तर दिशा में {a} किमी चलता है, फिर दाएँ मुड़कर {b} किमी चलता है, "
                   f"और अंत में दक्षिण दिशा में {back} किमी चलता है। {he_hi} प्रारम्भिक बिंदु से "
                   f"कितनी दूर है?")
        sol_hi = (f"उत्तर {a} और दक्षिण {back} मिलकर {net_n} किमी उत्तर शेष; पूर्व {b} किमी। "
                  f"दूरी = √({net_n}² + {b}²) = {root} किमी।")
        d = mistakes(("ignored the southward leg", f"{hyp} km"),
                     ("added all three distances", f"{a + b + back} km"),
                     ("cancelled the wrong pair", f"{abs(b - back)} km"))
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi,
                "correct": f"{root} km", "mistakes": d, "solution": sol,
                "concept": "Direction — Distance"}
    # diff 3 and 4+ : four legs, net displacement East and North.
    # d3 asks the DISTANCE, so the net legs are built from a Pythagorean pair and the answer is
    # whole. d4 asks the DIRECTION, which Pythagoras cannot give — the candidate has to track
    # signs on both axes. Deriving the legs from the net (rather than hoping a random set of legs
    # happens to be clean) is what keeps the two levels distinct: the first version fell back to
    # the direction question whenever the root was not exact, so d3 and d4 printed the SAME
    # question for most seeds.
    import math as _m
    if diff == 3:
        (net_n, net_e), root = rng.choice(list(TRIPLES.items()))
    else:
        net_n, net_e = rng.choice([4, 6, 8, 9]), rng.choice([3, 5, 7, 11])
        root = int(_m.isqrt(net_n * net_n + net_e * net_e))
    n2 = rng.choice([1, 2, 3])
    e2 = rng.choice([1, 2, 3])
    n1, e1 = net_n + n2, net_e + e2
    quad = "North-East"
    quad_hi = "उत्तर-पूर्व"
    stem_tail = ("How far is {} from the starting point?".format(he) if diff == 3 else
                 "In which direction is {} from the starting point?".format(he))
    stem = (f"{name} walks {n1} km towards North, then {e1} km towards East, then {n2} km "
            f"towards South, and finally {e2} km towards West. " + stem_tail)
    sol = (f"Net movement = {n1} - {n2} = {net_n} km North and {e1} - {e2} = {net_e} km East, "
           f"so the finishing point lies {quad} of the start"
           + (f", at sqrt({net_n}^2 + {net_e}^2) = {root} km." if "How far" in stem_tail else "."))
    stem_hi = (f"एक व्यक्ति उत्तर दिशा में {n1} किमी, फिर पूर्व दिशा में {e1} किमी, फिर दक्षिण "
               f"दिशा में {n2} किमी और अंत में पश्चिम दिशा में {e2} किमी चलता है। "
               + ("{} प्रारम्भिक बिंदु से कितनी दूर है?".format(he_hi) if "How far" in stem_tail
                  else "प्रारम्भिक बिंदु से {} किस दिशा में है?".format(he_hi)))
    sol_hi = (f"शुद्ध गति = {n1} - {n2} = {net_n} किमी उत्तर तथा {e1} - {e2} = {net_e} किमी पूर्व, "
              f"अतः अंतिम बिंदु प्रारम्भ के {quad_hi} में है"
              + (f", दूरी = √({net_n}² + {net_e}²) = {root} किमी।" if "How far" in stem_tail
                 else "।"))
    if "How far" in stem_tail:
        d = mistakes(("added every leg walked", f"{n1 + e1 + n2 + e2} km"),
                     ("forgot to cancel the southward and westward legs", f"{hyp} km"),
                     ("added the two net legs instead of using Pythagoras",
                      f"{net_e + net_n} km"))
        correct = f"{root} km"
    else:
        d = mistakes(("read the first leg as the answer", "North"),
                     ("cancelled the wrong pair, landing South-West", "South-West"),
                     ("used only the East-West net movement", "East"))
        correct = quad
        stem_hi = stem_hi.replace("कितनी दूर है?", "किस दिशा में है?")
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": correct,
            "mistakes": d, "solution": sol,
            "hi_opts": {"North": "उत्तर", "South": "दक्षिण", "East": "पूर्व", "West": "पश्चिम",
                        "North-East": "उत्तर-पूर्व", "South-West": "दक्षिण-पश्चिम",
                        "North-West": "उत्तर-पश्चिम", "South-East": "दक्षिण-पूर्व"},
            "concept": "Direction — Distance"}

def _b_direction_final(rng, diff):
    # net facing after a sequence of turns; compute exactly on the compass
    # diff 1-2 two or three 90° turns; diff 3+ four or five, so the count itself is the test and
    # a candidate cannot get there by picturing one turn.
    dirs = ["North", "East", "South", "West"]
    start = rng.randint(0, 3)
    n_turns = 2 if diff <= 1 else 3 if diff == 2 else (4 if diff == 3 else 5)
    turns = [rng.choice(["left", "right"]) for _ in range(n_turns)]
    cur = start
    for t in turns:
        cur = (cur + (1 if t == "right" else -1)) % 4
    ans = dirs[cur]
    seq = ", then takes a ".join(turns)
    stem = (f"A person is initially facing {dirs[start]}. He takes a {seq} turn. "
            f"Which direction is he facing now? (Each turn is 90°.)")
    steps = " ".join(f"{t}→{dirs[(start + sum(1 if turns[j]=='right' else -1 for j in range(i+1)))%4]}"
                     for i, t in enumerate(turns))
    sol = f"Starting {dirs[start]}, applying each 90° turn: {steps}. Final = {ans}."
    d = [d2 for d2 in dirs if d2 != ans]
    seq_hi = ", फिर ".join(HI.TURN[t] for t in turns)
    stem_hi = (f"एक व्यक्ति आरम्भ में {HI.DIR[dirs[start]]} दिशा की ओर मुख किए है। वह {seq_hi} मुड़ता है। "
               f"अब उसका मुख किस दिशा की ओर है? (प्रत्येक मोड़ 90° का है।)")
    sol_hi = f"{HI.DIR[dirs[start]]} से आरम्भ कर प्रत्येक 90° मोड़ लगाने पर अंतिम दिशा = {HI.DIR[ans]}।"
    hi_opts = HI.dir_opts(dirs)
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts, "correct": ans, "distractors": d[:3], "solution": sol,
            "concept": "Direction — Facing"}

# ---- Blood Relations --------------------------------------------------------

_MALE = ["Ram", "Amit", "Vikas", "Rohan", "Arun", "Sunil"]
_FEMALE = ["Sita", "Priya", "Anjali", "Meena", "Radha", "Neha"]

# (A is R1 of B) + (B is R2 of C) -> A is <answer> of C.  Only unambiguous compositions.
_KIN = {
    ("father", "father"): "grandfather", ("father", "mother"): "grandfather",
    ("mother", "father"): "grandmother", ("mother", "mother"): "grandmother",
    ("son", "son"): "grandson", ("son", "daughter"): "grandson",
    ("daughter", "son"): "granddaughter", ("daughter", "daughter"): "granddaughter",
    ("brother", "father"): "uncle", ("brother", "mother"): "uncle",
    ("sister", "father"): "aunt", ("sister", "mother"): "aunt",
    ("father", "brother"): "father", ("father", "sister"): "father",
    ("mother", "brother"): "mother", ("mother", "sister"): "mother",
    ("son", "brother"): "nephew", ("son", "sister"): "nephew",
    ("daughter", "brother"): "niece", ("daughter", "sister"): "niece",
}
# Hindi names the ROUTE, English does not. One English "niece" is भतीजी through a brother and
# भांजी through a sister; "uncle" is चाचा on the father's side and मामा on the mother's. Mapping
# the English word to one Hindi word therefore printed a wrong Hindi answer on 4 of these 20
# pairs, with the English half of the same question perfectly correct — invisible to every check
# that compares the two languages by their numbers. Found by solving the HINDI blind.
_KIN_HI = {
    # Grandparents and grandchildren split the same way, on whether the link is a son or a
    # daughter: पोती is a son's daughter, नातिन a daughter's daughter. The first pass at this
    # table covered only uncle/aunt/nephew/niece, so a blind Hindi solve came straight back with
    # "मीना राम की नातिन है, पोती नहीं" on the very next paper.
    ("father", "father"): "दादा", ("father", "mother"): "नाना",
    ("mother", "father"): "दादी", ("mother", "mother"): "नानी",
    ("son", "son"): "पोता", ("son", "daughter"): "नाती",
    ("daughter", "son"): "पोती", ("daughter", "daughter"): "नातिन",
    ("brother", "father"): "चाचा", ("brother", "mother"): "मामा",
    ("sister", "father"): "बुआ", ("sister", "mother"): "मौसी",
    ("son", "brother"): "भतीजा", ("son", "sister"): "भांजा",
    ("daughter", "brother"): "भतीजी", ("daughter", "sister"): "भांजी",
}
_REL_GENDER = {"father": "M", "mother": "F", "son": "M", "daughter": "F",
               "brother": "M", "sister": "F"}
_ALL_RELS = ["grandfather", "grandmother", "father", "mother", "brother", "sister",
             "uncle", "aunt", "nephew", "niece", "grandson", "granddaughter", "cousin"]

# Reading a relation the other way round. "A is the father of C" means "C is the son OR daughter
# of A" — which is only decidable from C's gender, so those are handled by choosing C's gender in
# the builder. Entries here are the ones that invert unambiguously.
_INV = {"grandfather": "grandson", "grandmother": "granddaughter",
        "grandson": "grandfather", "granddaughter": "grandmother",
        "uncle": "nephew", "aunt": "niece", "nephew": "uncle", "niece": "aunt",
        "father": "son", "mother": "daughter", "brother": "brother", "sister": "sister",
        "son": "father", "daughter": "mother"}


def _b_blood_relation(rng, diff):
    """Blood relations. Difficulty = how many links, and whether the chain is stated plainly.

    diff 1  two links, plainly stated      : A is the r1 of B, B is the r2 of C
    diff 2  three links                    : one more hop to hold
    diff 3  stated as a DIALOGUE           : "Pointing to a photograph, X said..." — the same
                                             chain, but the candidate must first work out who is
                                             speaking about whom, which is where most go wrong
    diff 4+ the chain runs BACKWARDS       : the relation of C to A rather than A to C, so the
                                             answer is the inverse of the one being traced
    """
    (r1, r2), ans = rng.choice(list(_KIN.items()))
    A = rng.choice(_MALE if _REL_GENDER[r1] == "M" else _FEMALE)
    B = rng.choice([x for x in (_MALE if _REL_GENDER[r2] == "M" else _FEMALE) if x != A])
    C = rng.choice([x for x in (_MALE + _FEMALE) if x not in (A, B)])
    ans_hi = _KIN_HI.get((r1, r2), HI.rel(ans))
    same_gender = [r for r in _ALL_RELS if r != ans and _rel_is_male(r) == _rel_is_male(ans)]
    d = rng.sample(same_gender, min(3, len(same_gender)))
    hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
    hi_opts[ans.capitalize()] = ans_hi
    sol = (f"{A} is {B}'s {r1}; {B} is {C}'s {r2}. Tracing the relationship, "
           f"{A} is the {ans} of {C}.")
    sol_hi = (f"सम्बन्ध जोड़ने पर {HI.name(A)}, {HI.name(C)} की {ans_hi} हुईं।"
              if not _rel_is_male(ans)
              else f"सम्बन्ध जोड़ने पर {HI.name(A)}, {HI.name(C)} के {ans_hi} हुए।")
    if diff <= 1:
        stem = (f"{A} is the {r1} of {B}, and {B} is the {r2} of {C}. "
                f"How is {A} related to {C}?")
        stem_hi = (f"{HI.name(A)}, {HI.possessive(HI.name(B), r1)} हैं तथा "
                   f"{HI.name(B)}, {HI.possessive(HI.name(C), r2)} हैं। "
                   f"{HI.name(A)} का {HI.name(C)} से क्या सम्बन्ध है?")
    elif diff == 3:
        # the SAME chain, spoken. A points at C and describes B in the middle.
        spk = "she" if A in _FEMALE else "he"
        spk_hi = "उसने" 
        stem = (f"Pointing to {C} in a photograph, {A} said, \"{B} is my {_INV.get(r1, r1)}, "
                f"and {C} is {B}'s {r2}.\" How is {A} related to {C}?")
        # "मेरा/मेरी" printed as a literal slash is an unfinished sentence on a real paper.
        # The possessive agrees with the RELATION's gender, which we already know.
        _spoken = _INV.get(r1, r1)
        _my = "मेरे" if _rel_is_male(_spoken) else "मेरी"
        stem_hi = (f"एक तस्वीर में {HI.name(C)} की ओर संकेत करते हुए {HI.name(A)} ने कहा, "
                   f"\"{HI.name(B)} {_my} {HI.rel(_spoken)} हैं तथा {HI.name(C)}, "
                   f"{HI.possessive(HI.name(B), r2)} हैं।\" {HI.name(A)} का {HI.name(C)} से "
                   f"क्या सम्बन्ध है?")
    elif diff == 2:
        # three links: A -r1-> B -r2-> C -r3-> D, asked A to D via the known two-step answer
        # A three-link chain only composes if the FIRST two links resolve to a basic relation —
        # _KIN is keyed on basic relations, so a derived one like "grandmother" has nowhere to go.
        # Guessing and retrying meant d2 printed the two-link question for 93 of 120 seeds: a
        # difficulty level that silently wasn't one. So pick the first pair from the chains that
        # DO land on a basic relation, then compose again.
        basic = {"father", "mother", "son", "daughter", "brother", "sister"}
        seeds2 = [(k, v) for k, v in _KIN.items() if v in basic]
        (r1, r2), ans = rng.choice(seeds2)
        A = rng.choice(_MALE if _REL_GENDER[r1] == "M" else _FEMALE)
        B = rng.choice([x for x in (_MALE if _REL_GENDER[r2] == "M" else _FEMALE) if x != A])
        C = rng.choice([x for x in (_MALE + _FEMALE) if x not in (A, B)])
        ans_hi = _KIN_HI.get((r1, r2), HI.rel(ans))
        D = rng.choice([x for x in (_MALE + _FEMALE) if x not in (A, B, C)])
        options3 = [(r3, _KIN[(ans, r3)]) for r3 in ("son", "daughter", "father", "mother",
                                                     "brother", "sister")
                    if (ans, r3) in _KIN]
        r3, final = rng.choice(options3)
        stem = (f"{A} is the {r1} of {B}, {B} is the {r2} of {C}, and {C} is the {r3} of {D}. "
                f"How is {A} related to {D}?")
        stem_hi = (f"{HI.name(A)}, {HI.possessive(HI.name(B), r1)} हैं; {HI.name(B)}, "
                   f"{HI.possessive(HI.name(C), r2)} हैं तथा {HI.name(C)}, "
                   f"{HI.possessive(HI.name(D), r3)} हैं। {HI.name(A)} का {HI.name(D)} से "
                   f"क्या सम्बन्ध है?")
        fin_hi = _KIN_HI.get((ans, r3), HI.rel(final))
        sol = (f"{A} is the {ans} of {C}; {C} is the {r3} of {D}. So {A} is the {final} of {D}.")
        sol_hi = (f"{HI.name(A)}, {HI.name(C)} के {ans_hi} हैं; {HI.name(C)}, "
                  f"{HI.possessive(HI.name(D), r3)} हैं। अतः {HI.name(A)}, {HI.name(D)} के "
                  f"{fin_hi} हुए।")
        same_gender = [r for r in _ALL_RELS if r != final
                       and _rel_is_male(r) == _rel_is_male(final)]
        d = rng.sample(same_gender, min(3, len(same_gender)))
        hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
        hi_opts[final.capitalize()] = fin_hi
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
                "correct": final.capitalize(), "distractors": [x.capitalize() for x in d],
                "solution": sol, "concept": "Blood Relations"}
    else:
        # diff 4+ : ask the INVERSE — how is C related to A
        inv = _INV.get(ans)
        if inv is None:
            return _b_blood_relation(rng, 1)
        stem = (f"{A} is the {r1} of {B}, and {B} is the {r2} of {C}. "
                f"How is {C} related to {A}?")
        stem_hi = (f"{HI.name(A)}, {HI.possessive(HI.name(B), r1)} हैं तथा "
                   f"{HI.name(B)}, {HI.possessive(HI.name(C), r2)} हैं। "
                   f"{HI.name(C)} का {HI.name(A)} से क्या सम्बन्ध है?")
        sol = (f"{A} is the {ans} of {C}, so read the other way, {C} is the {inv} of {A}.")
        sol_hi = (f"{HI.name(A)}, {HI.name(C)} के {ans_hi} हैं; उल्टा पढ़ने पर {HI.name(C)}, "
                  f"{HI.name(A)} के {HI.rel(inv)} हुए।")
        same_gender = [r for r in _ALL_RELS if r != inv and _rel_is_male(r) == _rel_is_male(inv)]
        d = rng.sample(same_gender, min(3, len(same_gender)))
        hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
                "correct": inv.capitalize(), "distractors": [x.capitalize() for x in d],
                "solution": sol, "concept": "Blood Relations"}
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
            "correct": ans.capitalize(), "distractors": [x.capitalize() for x in d],
            "solution": sol, "concept": "Blood Relations"}


def _rel_is_male(r):
    return r in ("grandfather", "father", "brother", "uncle", "nephew", "grandson")


# =============================================================================
# chapter -> builders
# =============================================================================

_CHAP_BUILDERS = {
    "Coding-Decoding": [_b_coding_shift, _b_coding_number],
    "Series": [_b_letter_series, _b_alnum_series],
    "Analogy": [_b_number_analogy, _b_letter_analogy],
    "Classification (Odd One Out)": [_b_odd_square, _b_odd_prime],
    "Ranking & Ordering": [_b_ranking, _b_ranking_pos],
    "Direction Sense": [_b_direction_distance, _b_direction_final],
    "Blood Relations": [_b_blood_relation],
}


def _chapters_for(spec):
    ch = spec.get("chapter")
    if ch and ch in _CHAP_BUILDERS:
        return [ch]
    return list(_CHAP_BUILDERS.keys())


def generate_test(store, spec: dict, count: int = 5) -> dict:
    """Deterministic replacement for generator.generate_test — same return shape. Builds
    exam-authentic reasoning questions and COMPUTES their answers; upserts them as verified
    generated questions (no figure, no LLM)."""
    rng = random.Random()
    chapters = _chapters_for(spec)
    accepted, seen = [], set()
    attempts = 0
    while len(accepted) < count and attempts < count * 15:
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
        if store is not None:
            store.upsert(q)
        accepted.append(q)
    return {
        "spec": spec,
        "generator": "reasoninggen",
        "requested": count,
        "generated": len(accepted),
        "rejected": [],
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
    }
