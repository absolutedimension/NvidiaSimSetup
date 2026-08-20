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
    options, ans = _mcq(stem, built["correct"], built.get("distractors", []),
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

def _b_coding_shift(rng, diff):
    w1, w2 = rng.sample(_WORDS, 2)
    k = rng.choice([1, 2, 3, 4, -1, -2, -3])
    c1, c2 = _shift_word(w1, k), _shift_word(w2, k)
    sign = f"+{k}" if k > 0 else str(k)
    stem = (f"In a certain code language, '{w1}' is written as '{c1}'. "
            f"How is '{w2}' written in that same code?")
    sol = (f"Each letter is shifted by {sign} position(s) in the alphabet "
           f"({w1}→{c1}). Applying the same shift to {w2} gives {c2}.")
    d = [_shift_word(w2, k + 1), _shift_word(w2, k - 1), _shift_word(w2, -k or 1)]
    d = [x for x in dict.fromkeys(d) if x != c2][:3]
    stem_hi = (f"एक निश्चित कूट भाषा में '{w1}' को '{c1}' लिखा जाता है। "
               f"उसी कूट भाषा में '{w2}' को कैसे लिखा जाएगा?")
    sol_hi = f"प्रत्येक अक्षर को वर्णमाला में {sign} स्थान खिसकाया गया है ({w1}→{c1}); अतः {w2} → {c2}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": c2, "distractors": d, "solution": sol,
            "concept": "Letter-Shift Coding"}

def _b_coding_number(rng, diff):
    w = rng.choice(_WORDS)
    op = rng.choice(["pos", "pos+1", "pos*2"])
    if op == "pos":
        vals = [_pos(c) for c in w]; desc = "its position in the alphabet (A=1, B=2, …)"
    elif op == "pos+1":
        vals = [_pos(c) + 1 for c in w]; desc = "one more than its position in the alphabet (A=2, B=3, …)"
    else:
        vals = [_pos(c) * 2 for c in w]; desc = "twice its position in the alphabet (A=2, B=4, …)"
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
    stem_hi = f"यदि प्रत्येक अक्षर को उसकी वर्णमाला-स्थिति के अनुसार कूटबद्ध किया जाए, तो '{w}' का कूट क्या होगा?"
    sol_hi = f"{w} के अक्षरों की स्थिति के अनुसार कूट = {code}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": code, "distractors": d, "solution": sol,
            "concept": "Number Coding"}

# ---- Alphabet / Letter Series ----------------------------------------------

def _b_letter_series(rng, diff):
    start = rng.randint(1, 12)
    step = rng.choice([1, 2, 3, 4, 5])
    terms = [start + i * step for i in range(5)]
    letters = [_letter(t) for t in terms[:4]]
    ans = _letter(terms[4])
    shown = ", ".join(letters) + ", ?"
    stem = f"Find the next term in the letter series:\n{shown}"
    sol = (f"The letters advance by {step} position(s) each time "
           f"({'→'.join(letters)}). Next = {ans}.")
    cands = [_letter(terms[4] + 1), _letter(terms[4] - 1), _letter(terms[4] + 2),
             _letter(terms[4] + step), _letter(terms[4] - 2)]
    d = [x for x in dict.fromkeys(cands) if x != ans][:3]
    stem_hi = f"अक्षर श्रृंखला में अगला पद ज्ञात कीजिए:\n{shown}"
    sol_hi = f"प्रत्येक बार अक्षर {step} स्थान आगे बढ़ता है; अतः अगला पद = {ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans, "distractors": d, "solution": sol,
            "concept": "Letter Series"}

def _b_alnum_series(rng, diff):
    lstart = rng.randint(1, 15)
    lstep = rng.choice([2, 3, 4])
    nstart = rng.choice([2, 3, 5])
    nstep = rng.choice([2, 3, 4])
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
    left = rng.randint(3, 12)
    right = rng.randint(3, 12)
    total = left + right - 1
    name = rng.choice(["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Anjali", "Rohan"])
    stem = (f"In a row of students, {name} is {_ord(left)} from the left end and "
            f"{_ord(right)} from the right end. How many students are there in the row?")
    sol = (f"Total = (position from left) + (position from right) − 1 = "
           f"{left} + {right} − 1 = {total}.")
    cands = [str(total + 1), str(total - 1), str(total + 2), str(total - 2)]
    d = [x for x in dict.fromkeys(cands) if x != str(total)][:3]
    stem_hi = (f"विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से {HI.ordinal(left)} स्थान पर "
               f"तथा दाईं ओर से {HI.ordinal(right)} स्थान पर है। पंक्ति में कुल कितने विद्यार्थी हैं?")
    sol_hi = f"कुल = बाएँ से स्थान + दाएँ से स्थान − 1 = {left} + {right} − 1 = {total}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(total), "distractors": d, "solution": sol,
            "concept": "Ranking"}

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
    # walk that returns an axis-aligned or 3-4-5 right triangle so distance is clean
    a = rng.choice([3, 6, 8, 9, 12])
    b = rng.choice([4, 8, 15, 5, 12])
    # ensure a Pythagorean-clean hypotenuse when both legs used
    triples = {(3, 4): 5, (6, 8): 10, (8, 15): 17, (9, 12): 15, (5, 12): 13, (12, 5): 13}
    key = (a, b) if (a, b) in triples else next(iter(triples))
    a, b = key
    hyp = triples[key]
    name = rng.choice(["A man", "Ravi", "A boy", "Sita"])
    stem = (f"{name} starts from a point and walks {a} km towards North, then turns right "
            f"and walks {b} km towards East. How far is {'he' if name!='Sita' else 'she'} "
            f"now from the starting point?")
    sol = (f"North {a} km and East {b} km are perpendicular. Straight-line distance = "
           f"√({a}² + {b}²) = √({a*a} + {b*b}) = √{a*a+b*b} = {hyp} km.")
    d = [f"{a + b} km", f"{hyp + 1} km", f"{abs(a - b)} km"]
    d = [x for x in dict.fromkeys(d) if x != f"{hyp} km"][:3]
    stem_hi = (f"एक व्यक्ति एक बिंदु से चलना आरम्भ करता है और उत्तर दिशा में {a} किमी चलता है, "
               f"फिर दाएँ मुड़कर पूर्व दिशा में {b} किमी चलता है। अब वह प्रारम्भिक बिंदु से "
               f"कितनी दूर है?")
    sol_hi = f"उत्तर व पूर्व लम्बवत हैं; दूरी = √({a}² + {b}²) = √{a*a+b*b} = {hyp} किमी।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": f"{hyp} km", "distractors": d, "solution": sol,
            "concept": "Direction — Distance"}

def _b_direction_final(rng, diff):
    # net facing after a sequence of turns; compute exactly on the compass
    dirs = ["North", "East", "South", "West"]
    start = rng.randint(0, 3)
    turns = [rng.choice(["left", "right"]) for _ in range(rng.randint(2, 4))]
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
_REL_GENDER = {"father": "M", "mother": "F", "son": "M", "daughter": "F",
               "brother": "M", "sister": "F"}
_ALL_RELS = ["grandfather", "grandmother", "father", "mother", "brother", "sister",
             "uncle", "aunt", "nephew", "niece", "grandson", "granddaughter", "cousin"]

def _b_blood_relation(rng, diff):
    (r1, r2), ans = rng.choice(list(_KIN.items()))
    A = rng.choice(_MALE if _REL_GENDER[r1] == "M" else _FEMALE)          # A's gender ⇐ r1
    B = rng.choice([x for x in (_MALE if _REL_GENDER[r2] == "M" else _FEMALE)
                    if x != A])                                          # B's gender ⇐ r2
    C = rng.choice([x for x in (_MALE + _FEMALE) if x not in (A, B)])
    stem = (f"{A} is the {r1} of {B}, and {B} is the {r2} of {C}. "
            f"How is {A} related to {C}?")
    sol = (f"{A} is {B}'s {r1}; {B} is {C}'s {r2}. Tracing the relationship, "
           f"{A} is the {ans} of {C}.")
    same_gender = [r for r in _ALL_RELS if r != ans and _rel_is_male(r) == _rel_is_male(ans)]
    d = rng.sample(same_gender, min(3, len(same_gender)))
    stem_hi = (f"{HI.name(A)}, {HI.possessive(HI.name(B), r1)} हैं तथा "
               f"{HI.name(B)}, {HI.possessive(HI.name(C), r2)} हैं। "
               f"{HI.name(A)} का {HI.name(C)} से क्या सम्बन्ध है?")
    sol_hi = f"सम्बन्ध जोड़ने पर {HI.name(A)}, {HI.possessive(HI.name(C), ans)} हुए।"
    hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts, "correct": ans.capitalize(),
            "distractors": [x.capitalize() for x in d], "solution": sol,
            "concept": "Blood Relations"}

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
