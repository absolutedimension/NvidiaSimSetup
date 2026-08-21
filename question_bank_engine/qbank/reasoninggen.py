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
import re

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


# ---- distractor PROXIMITY, as a difficulty dial ------------------------------
#
# Measured across every builder before this existed: the median gap between a distractor and the
# answer ranged from 0.01 to 5.47 times the answer, with no relation to the difficulty asked for.
# A wrong option five times the size of the right one is eliminated at a glance and the question
# collapses to a three-way guess; one within a few percent forces the candidate to actually finish
# the work. Distractor plausibility is a well-established difficulty radical, and ours was an
# accident of which mistake happened to be written first.
#
# This does NOT invent closer distractors — that would break the rule the whole engine rests on,
# that a wrong option must be the result of a NAMED mistake rather than a nudge. It CHOOSES among
# the named mistakes a builder offers. So it only has an effect where a builder supplies more
# mistakes than there are option slots, which is why the two halves of this change go together.

def _as_number(s):
    """The number inside an option, ignoring units and separators: '17 km' -> 17.0, 'Rs. 1,250' ->
    1250.0. Returns None when the option is not numeric at all."""
    m = re.search(r"-?\d+(?:\.\d+)?", str(s).replace(",", ""))
    return float(m.group()) if m else None


def _edit_ratio(a, b):
    """Levenshtein distance normalised by length — proximity for options that are WORDS or CODES.

    'shifted one place too far' produces a code that differs from the answer in every letter but is
    still recognisably the same shape; 'reversed without shifting' produces something a candidate
    can reject instantly. Letters need a distance too, or half the engine sits outside the dial.
    """
    a, b = str(a), str(b)
    if not a or not b:
        return 1.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(len(a), len(b))


def mistake_distance(text, correct):
    """0 = indistinguishable from the answer, 1 = obviously different. None = no opinion."""
    na, nb = _as_number(text), _as_number(correct)
    if na is not None and nb is not None:
        return min(abs(na - nb) / max(abs(nb), 1.0), 1.0)
    ta, tb = str(text).strip(), str(correct).strip()
    if len(ta) == 1 and len(tb) == 1 and ta.isupper() and tb.isupper():
        return abs(ord(ta) - ord(tb)) / 25.0          # a series answer: alphabet distance
    # Edit distance ONLY for the ALL-CAPS codes and words the exam prints — a shifted code, a
    # series term, a word built from letters. Deliberately not for 'Rahul' vs 'Priya' or 'Sunday'
    # vs 'Monday': those are equally far apart whatever the arithmetic says, and scoring them
    # would sort the options by a number that means nothing.
    if ta.isupper() and tb.isupper() and ta.replace(" ", "").isalnum() and len(tb) <= 24:
        return _edit_ratio(ta, tb)
    return None                       # names, weekdays, rubric labels — no meaningful distance


def order_mistakes(mis, correct, diff):
    """Reorder named mistakes so the ones that survive into the options suit the difficulty.

    diff 3-4  CLOSEST first  — the candidate must finish the calculation to tell them apart
    diff 1    FARTHEST first — one clearly-wrong option per slot, so the question stays an entry point
    diff 2    the builder's own order, which is roughly 'most common mistake first'

    Stable, so mistakes we cannot measure a distance for (names, rubric labels) keep their original
    position instead of being shuffled to one end by a None.
    """
    if diff == 2 or len(mis) <= 3:
        return list(mis)
    scored = [(mistake_distance(m["text"], correct), m) for m in mis]
    if sum(1 for d, _ in scored if d is not None) < 2:
        return list(mis)              # nothing measurable — leave the builder's order alone
    far = diff <= 1
    return [m for _, m in sorted(
        scored, key=lambda p: (p[0] is None, -p[0] if (far and p[0] is not None) else p[0]))]


def _make_question(built: dict, rng, spec) -> Question:
    stem = built["stem"].strip()
    n_opts = len(built["options"]) if built.get("options") else 4
    # Error-derived distractors win over hand-nudged ones. A "mistake" that lands ON the correct
    # answer is dropped and flagged: those numbers reward a wrong method, so a candidate who
    # forgets the -1 scores the mark and learns the wrong lesson.
    mis = [m for m in (built.get("mistakes") or []) if m["text"] != str(built["correct"])]
    collided = [m for m in (built.get("mistakes") or []) if m["text"] == str(built["correct"])]
    # Choose WHICH named mistakes reach the four option slots, by how hard they are to eliminate.
    # _mcq takes the first n-1, so ordering here is the whole mechanism. See order_mistakes.
    mis = order_mistakes(mis, built["correct"], spec.get("dmax") or spec.get("dmin") or 2)
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

    Each entry is (why, value) or (why, value, why_hi). The Hindi reason is what lets the SAME
    computation be re-asked as an error-spotting question (item_forms.as_error_spot) instead of
    only as "what is the answer" — the diagnosis we already compute becomes a second, harder
    question rather than metadata nobody sees. Without it the form is English-only, so it is
    gated all-or-nothing per item, the same way staticgk_hi gates General Studies.
    """
    out = []
    for p in pairs:
        why, value = p[0], p[1]
        why_hi = p[2] if len(p) > 2 else None
        if value is not None and str(value).strip():
            out.append({"why": why, "text": str(value), "why_hi": why_hi})
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
        d = mistakes(("shifted one place too far", _shift_word(w2, k + 1),
                      "एक स्थान अधिक खिसका दिया"),
                     ("shifted one place short", _shift_word(w2, k - 1),
                      "एक स्थान कम खिसकाया"),
                     ("shifted in the opposite direction", _shift_word(w2, -k),
                      "विपरीत दिशा में खिसका दिया"),
                     ("shifted twice as far", _shift_word(w2, 2 * k),
                      "दुगुने स्थान खिसका दिया"),
                     ("shifted the word and then reversed it", _shift_word(w2, k)[::-1],
                      "शब्द को खिसकाकर उसे उल्टा भी लिख दिया"))
    elif diff == 2:
        alt = lambda w: "".join(chr((ord(c) - _A + (k if i % 2 == 0 else -k)) % 26 + _A)
                                for i, c in enumerate(w))
        c1, c2 = alt(w1), alt(w2)
        rule = (f"Letters in odd positions move {sign} and letters in even positions move the "
                f"opposite way")
        rule_hi = (f"विषम स्थान के अक्षर {sign} खिसकते हैं तथा सम स्थान के अक्षर विपरीत दिशा में")
        d = mistakes(("shifted every letter the same way", _shift_word(w2, k),
                      "सभी अक्षरों को एक ही तरह खिसका दिया"),
                     ("applied the two shifts the other way round",
                      "".join(chr((ord(c) - _A + (-k if i % 2 == 0 else k)) % 26 + _A)
                              for i, c in enumerate(w2)),
                      "दोनों अंतरालों को उल्टा लगा दिया"),
                     ("shifted every letter the opposite way", _shift_word(w2, -k),
                      "सभी अक्षरों को विपरीत दिशा में खिसका दिया"))
    elif diff == 3:
        rev = lambda w: _shift_word(w[::-1], k)
        c1, c2 = rev(w1), rev(w2)
        rule = f"The word is reversed and then each letter is shifted by {sign}"
        rule_hi = f"शब्द को उल्टा लिखकर प्रत्येक अक्षर को {sign} स्थान खिसकाया गया है"
        d = mistakes(("shifted without reversing", _shift_word(w2, k),
                      "उल्टा किए बिना केवल खिसका दिया"),
                     ("reversed without shifting", w2[::-1],
                      "खिसकाए बिना केवल उल्टा लिख दिया"),
                     ("shifted first and then reversed", _shift_word(w2, k)[::-1],
                      "पहले खिसकाया फिर उल्टा किया — क्रम बदल दिया"))
    else:
        posn = lambda w: "".join(chr((ord(c) - _A + (i + 1)) % 26 + _A) for i, c in enumerate(w))
        c1, c2 = posn(w1), posn(w2)
        rule = ("The first letter moves 1 place, the second 2 places, the third 3, and so on")
        rule_hi = ("पहला अक्षर 1 स्थान, दूसरा 2 स्थान, तीसरा 3 स्थान — इसी क्रम में आगे बढ़ता है")
        d = mistakes(("used the same shift for every letter", _shift_word(w2, 1),
                      "हर अक्षर के लिए एक ही अंतराल लगा दिया"),
                     ("started the count from 0 instead of 1",
                      "".join(chr((ord(c) - _A + i) % 26 + _A) for i, c in enumerate(w2)),
                      "गिनती 1 के बजाय 0 से शुरू कर दी"),
                     ("moved each letter backwards by its position",
                      "".join(chr((ord(c) - _A - (i + 1)) % 26 + _A) for i, c in enumerate(w2)),
                      "प्रत्येक अक्षर को उसकी स्थिति जितना पीछे खिसका दिया"))
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
    # Disjoint bands, so d3 cannot emit the d1 rule. d4 counts the alphabet BACKWARDS (A=26),
    # which is the standard step up and cannot be reached by adjusting the forward count.
    op = rng.choice({1: ["pos"], 2: ["pos+1"], 3: ["pos*2"]}.get(min(diff, 4), ["rev"]))
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
    elif op == "pos*2":
        vals = [_pos(c) * 2 for c in w]
        desc = "twice its position in the alphabet (A=2, B=4, …)"
        desc_hi = "उसकी वर्णमाला-स्थिति से दोगुना (A=2, B=4, …)"
    else:
        vals = [27 - _pos(c) for c in w]
        desc = "its position counted BACKWARDS from Z (Z=1, Y=2, …, A=26)"
        desc_hi = "Z से उल्टी गिनती में उसकी स्थिति (Z=1, Y=2, …, A=26)"
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
                 " ".join(str(_pos(c)) for c in w),
                 "नियम को छोड़कर केवल वर्णमाला-स्थिति का प्रयोग किया"),
                ("doubled the position instead of applying the stated rule",
                 " ".join(str(_pos(c) * 2) for c in w),
                 "दिए गए नियम के बजाय स्थिति को दुगुना कर दिया"),
                ("added one to the position instead of applying the stated rule",
                 " ".join(str(_pos(c) + 1) for c in w),
                 # "एक", not "1" — the English says "one" as a word, and paper_common's
                 # option-number check compares the DIGITS in the two languages. A numeral here
                 # made the halves disagree and failed the whole paper.
                 "दिए गए नियम के बजाय स्थिति में एक जोड़ दिया")),
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
        wrong = [("used a step of {} instead".format(step + 1), start + 4 * (step + 1),
                  "{} के अंतराल का प्रयोग कर लिया".format(step + 1)),
                 ("used a step of {} instead".format(step - 1), start + 4 * (step - 1),
                  "{} के अंतराल का प्रयोग कर लिया".format(step - 1)),
                 ("stopped one term early", start + 3 * step,
                  "एक पद पहले ही रुक गया")]
    elif diff == 2:
        s1, s2 = rng.choice([(2, 3), (3, 1), (4, 2), (1, 4)])
        terms = [start]
        for i in range(4):
            terms.append(terms[-1] + (s1 if i % 2 == 0 else s2))
        rule = f"The step alternates: +{s1}, +{s2}, +{s1}, +{s2}"
        rule_hi = f"अंतराल क्रमशः बदलता है: +{s1}, +{s2}, +{s1}, +{s2}"
        wrong = [("used the other step for the last gap", terms[3] + s2,
                  "अंतिम अंतराल में दूसरा वाला अंतराल लगा दिया"),
                 ("used a constant step of {}".format(s1), start + 4 * s1,
                  "पूरी श्रृंखला में {} का स्थिर अंतराल मान लिया".format(s1)),
                 ("used a constant step of {}".format(s2), start + 4 * s2,
                  "पूरी श्रृंखला में {} का स्थिर अंतराल मान लिया".format(s2))]
    elif diff == 3:
        step = rng.choice([1, 2])
        terms, st = [start], step
        for _ in range(4):
            terms.append(terms[-1] + st)
            st += 1
        rule = f"The gap grows by one each time: +{step}, +{step + 1}, +{step + 2}, +{step + 3}"
        rule_hi = f"अंतराल हर बार एक बढ़ता है: +{step}, +{step + 1}, +{step + 2}, +{step + 3}"
        wrong = [("kept the gap constant", start + 4 * step,
                  "अंतराल को स्थिर मान लिया"),
                 ("grew the gap but from the wrong start", terms[3] + step + 2,
                  "अंतराल बढ़ाया तो सही पर आरम्भ गलत जगह से किया"),
                 ("repeated the previous gap", terms[3] + step + 1,
                  "पिछला अंतराल ही दोहरा दिया")]
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
        wrong = [("treated it as one series", terms[3] + s1,
                  "दोनों को एक ही श्रृंखला मान लिया"),
                 ("continued the SECOND series instead of the first", even[1] + s2,
                  "पहली के बजाय दूसरी श्रृंखला को आगे बढ़ा दिया"),
                 ("advanced the first series by the second series' step", odd[1] + s2,
                  "पहली श्रृंखला को दूसरी वाले अंतराल से बढ़ा दिया")]
    letters = [_letter(t) for t in terms[:4]]
    ans = _letter(terms[4])
    shown = ", ".join(letters) + ", ?"
    stem = f"Find the next term in the letter series:\n{shown}"
    sol = f"{rule} ({'->'.join(letters)}). Next = {ans}."
    stem_hi = f"अक्षर श्रृंखला में अगला पद ज्ञात कीजिए:\n{shown}"
    sol_hi = f"{rule_hi}; अतः अगला पद = {ans}।"
    d = mistakes(*[(why, _letter(v), why_hi) for why, v, why_hi in wrong])
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
    # Two components move independently, so every named mistake is "got one right and the other
    # wrong" — which is exactly how a candidate fails this question type.
    al, an_ = pairs[4][0], pairs[4][1]
    pl, pn = pairs[3][0], pairs[3][1]
    d = mistakes(("advanced the letter one place too far", f"{_letter(_pos(al) + 1)}{an_}",
                  "अक्षर को एक स्थान अधिक बढ़ा दिया"),
                 ("advanced the letter one place short", f"{_letter(_pos(al) - 1)}{an_}",
                  "अक्षर को एक स्थान कम बढ़ाया"),
                 ("advanced the number by 1 instead of by the series step", f"{al}{pn + 1}",
                  "संख्या को श्रृंखला के अंतराल के बजाय केवल 1 बढ़ाया"),
                 ("advanced the letter but left the number where it was", f"{al}{pn}",
                  "अक्षर तो बढ़ाया परन्तु संख्या वहीं छोड़ दी"),
                 ("advanced the number but left the letter where it was", f"{pl}{an_}",
                  "संख्या तो बढ़ाई परन्तु अक्षर वहीं छोड़ दिया"))
    stem_hi = f"निम्नलिखित श्रृंखला में आगे क्या आएगा?\n{shown}"
    sol_hi = f"अक्षर {lstep} स्थान तथा संख्याएँ {nstep} बढ़ती हैं; अतः अगला पद = {ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans,
            "mistakes": d, "solution": sol, "concept": "Alphanumeric Series"}

# ---- Analogy ----------------------------------------------------------------

def _analogy_rivals(a, b, c):
    """Every DEFENSIBLE answer to 'a : b :: c : ?', as strings.

    Mirrors paper_common.analogy_candidates, which is the gate the pool and the paper both apply.
    Kept here so the builder can avoid generating an ambiguous item in the first place rather than
    producing one and having it thrown away — and so a distractor is never accidentally a second
    right answer.
    """
    out = {str(c + (b - a))}
    if a:
        if b % a == 0:
            out.add(str(c * (b // a)))
        if a * a == b:
            out.add(str(c * c))
        if a ** 3 == b:
            out.add(str(c ** 3))
        if b == a * (a + 1) // 2:
            out.add(str(c * (c + 1) // 2))
        if b == a * a + a:
            out.add(str(c * c + c))
        if b == a * a - a:
            out.add(str(c * c - c))
        if b == 2 * a + 1:
            out.add(str(2 * c + 1))
    return out


def _b_number_analogy(rng, diff):
    # Difficulty is the relation itself. Bands are disjoint, so a level cannot quietly emit an
    # easier one — the failure that has bitten four builders in this work.
    rule = rng.choice({1: ["double", "next"], 2: ["triple", "square"],
                       3: ["cube", "sq_plus"], 4: ["sq_minus", "double_plus"]
                       }.get(min(diff, 4), ["square"]))
    a = rng.randint(2, 12)
    c = rng.randint(2, 12)
    while c == a:
        c = rng.randint(2, 12)
    fn = {"square": lambda x: x * x, "cube": lambda x: x ** 3, "double": lambda x: 2 * x,
          "next": lambda x: x + 1, "triple": lambda x: 3 * x,
          "sq_plus": lambda x: x * x + x, "sq_minus": lambda x: x * x - x,
          "double_plus": lambda x: 2 * x + 1}[rule]
    desc = {"sq_plus": "n squared plus n", "sq_minus": "n squared minus n",
            "double_plus": "twice the number plus one",
            "square": "square of the number", "cube": "cube of the number",
            "double": "twice the number", "next": "the number plus 1",
            "triple": "thrice the number"}[rule]
    b, ans = fn(a), fn(c)
    stem = f"{a} : {b} :: {c} : ?"
    sol = f"The second term is {desc} ({a}→{b}). So {c}→{ans}."
    # Was answer±1 and answer+c — arithmetic nudges, attractive to nobody. These are the rules a
    # candidate actually mistakes this one for.
    # 🔴 A number analogy is the ONE place where "apply a different plausible rule" must NOT be
    # used as a named mistake. Applying a rival rule to a : b :: c : ? is a DEFENSIBLE answer, not
    # an error — "5 : 25 :: 4 : ?" is 16 by squaring and 20 by x5 — so offering one puts a second
    # correct answer on the page. Measured when this was first converted: 261 of 400 items came
    # back ambiguous. The named mistakes here are therefore errors in APPLYING the given rule, and
    # anything that collides with a rival reading is dropped by _analogy_rivals.
    rivals = _analogy_rivals(a, b, c)
    cand = [("applied the rule to the number one higher", fn(c + 1),
             "नियम को एक अधिक संख्या पर लगा दिया"),
            ("applied the rule to the number one lower", fn(c - 1),
             "नियम को एक कम संख्या पर लगा दिया"),
            ("applied the rule twice over", fn(fn(c)),
             "नियम को दो बार लगा दिया"),
            ("copied the first pair's second term instead of working out the third", b,
             "तीसरे पद पर नियम लगाने के बजाय पहले युग्म का दूसरा पद ही लिख दिया"),
            ("applied the rule and then added the number back", fn(c) + c,
             "नियम लगाकर उसमें वही संख्या फिर से जोड़ दी")]
    seen_v, picked = set(), []
    for why, v, why_hi in cand:
        if v == ans or v <= 0 or str(v) in rivals or v in seen_v:
            continue
        seen_v.add(v)
        picked.append((why, str(v), why_hi))
    if len(picked) < 3:
        return None
    d = mistakes(*picked)
    stem_hi = f"{a} : {b} :: {c} : ?"
    sol_hi = f"दूसरा पद पहले पद का सम्बन्ध दर्शाता है ({a}→{b}); उसी नियम से {c}→{ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(ans),
            "mistakes": d, "solution": sol, "concept": "Number Analogy",
            # An analogy is only unambiguous RELATIVE TO ITS PRINTED OPTIONS — "3 : 9 :: 6 : ?" is
            # 18 by x3 and 36 by squaring, and analogy_ambiguous passes it only because just one of
            # those is on offer. A form that replaces the numeric options (error-spot offers
            # REASONS) throws that protection away, and a candidate reading the other rule then
            # finds no option that fits at all. So such items must not be re-asked in any form
            # that drops the numbers.
            "ambiguous_without_options": len(rivals - {str(ans)}) > 0}

def _b_letter_analogy(rng, diff):
    # d1 a short forward shift | d2 a longer one | d3 BACKWARD | d4 three-letter groups
    k = {1: rng.choice([1, 2]), 2: rng.choice([4, 5, 6]),
         3: rng.choice([-2, -3, -4])}.get(min(diff, 4), rng.choice([3, 5]))
    width = 3 if diff >= 4 else 2
    a = rng.randint(5, 10)
    c = rng.randint(5, 18)
    while c == a:
        c = rng.randint(5, 18)
    grp = lambda st, sh: "".join(_letter(st + i + sh) for i in range(width))
    pa, pb = grp(a, 0), grp(a, k)
    pc, ans = grp(c, 0), grp(c, k)
    stem = f"{pa} : {pb} :: {pc} : ?"
    sol = (f"Each letter moves +{k} in the alphabet ({pa}→{pb}). "
           f"Applying +{k} to {pc} gives {ans}.")
    d = mistakes(("shifted one place too far", grp(c, k + 1), "एक स्थान अधिक खिसका दिया"),
                 ("shifted one place short", grp(c, k - 1), "एक स्थान कम खिसकाया"),
                 ("shifted in the opposite direction", grp(c, -k),
                  "विपरीत दिशा में खिसका दिया"),
                 ("shifted only the first letter and copied the rest",
                  _letter(c + k) + "".join(_letter(c + i) for i in range(1, width)),
                  "केवल पहला अक्षर खिसकाया, शेष ज्यों के त्यों रख दिए"),
                 ("shifted by the position of the first letter instead of by the given step",
                  grp(c, a), "दिए गए अंतराल के बजाय पहले अक्षर की स्थिति जितना खिसका दिया"))
    stem_hi = f"{pa} : {pb} :: {pc} : ?"
    sol_hi = f"प्रत्येक अक्षर वर्णमाला में +{k} स्थान बढ़ता है ({pa}→{pb}); अतः {pc} → {ans}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": ans,
            "mistakes": d, "solution": sol, "concept": "Letter Analogy"}

# ---- Odd One Out ------------------------------------------------------------

def _b_odd_square(rng, diff):
    lo, hi = (3, 8) if diff <= 2 else (8, 16)
    squares = rng.sample([n * n for n in range(lo, hi)], 3)
    # At the easy end any non-square will do. Higher up it must sit NEXT TO a square, so it cannot
    # be spotted by size alone and the candidate has to actually test each number.
    near = [x + o for x in squares for o in (-1, 1, 2)]
    pool = ([x for x in range(lo * lo, hi * hi) if int(x ** 0.5) ** 2 != x] if diff <= 2
            else [x for x in near if int(x ** 0.5) ** 2 != x and x not in squares])
    odd = rng.choice(pool)
    opts = squares + [odd]
    rng.shuffle(opts)
    stem = "Three of the following four numbers are alike; find the ODD one out:\n" + \
           ",  ".join(str(x) for x in opts)
    sol = (f"{', '.join(str(s) for s in squares)} are perfect squares "
           f"({'; '.join(f'{int(s**0.5)}²={s}' for s in squares)}); {odd} is not. "
           f"So {odd} is the odd one out.")
    # The four printed numbers ARE the option set here, so there is no choice for the proximity
    # dial — but each wrong option still gets the reason it belongs with the others, which is what
    # puts a diagnosis on the paper and lets the item be re-asked as an error-spot.
    d = mistakes(*[(f"picked {x}, which IS a perfect square ({int(x ** 0.5)}² = {x}) and so "
                    f"belongs with the other two", str(x),
                    f"{x} चुन लिया, जो स्वयं पूर्ण वर्ग है ({int(x ** 0.5)}² = {x}) और शेष "
                    f"दोनों के साथ ही आता है") for x in squares])
    stem_hi = ("निम्नलिखित चार संख्याओं में से तीन एक समान हैं; असंगत (ODD) संख्या चुनिए:\n"
               + ",  ".join(str(x) for x in opts))
    sol_hi = f"शेष तीनों पूर्ण वर्ग हैं; {odd} पूर्ण वर्ग नहीं है, अतः यही असंगत है।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(odd),
            "mistakes": d, "solution": sol, "concept": "Odd One Out (Numbers)"}

def _b_odd_prime(rng, diff):
    primes = rng.sample([7, 11, 13, 17, 19, 23] if diff <= 2 else
                        [53, 59, 61, 67, 71, 73, 79, 83, 89, 97], 3)
    def is_prime(n):
        return n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
    # 91 = 7 x 13 and 51 = 3 x 17 read as primes at a glance; that IS the question at the top end.
    comp = rng.choice([x for x in range(8, 50) if not is_prime(x)] if diff <= 2
                      else [51, 57, 87, 91, 93, 111, 119, 133])
    opts = primes + [comp]
    rng.shuffle(opts)
    stem = "Three of the following four numbers are alike; find the ODD one out:\n" + \
           ",  ".join(str(x) for x in opts)
    sol = (f"{', '.join(str(p) for p in primes)} are prime numbers; "
           f"{comp} is composite ({comp} = {comp//_smallest_factor(comp)} × {_smallest_factor(comp)}). "
           f"So {comp} is the odd one out.")
    d = mistakes(*[(f"picked {x}, which IS prime and so belongs with the other two", str(x),
                    f"{x} चुन लिया, जो स्वयं अभाज्य है और शेष दोनों के साथ ही आता है")
                   for x in primes])
    stem_hi = ("निम्नलिखित चार संख्याओं में से तीन एक समान हैं; असंगत (ODD) संख्या चुनिए:\n"
               + ",  ".join(str(x) for x in opts))
    sol_hi = f"शेष तीनों अभाज्य संख्याएँ हैं; {comp} भाज्य है, अतः यही असंगत है।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(comp),
            "mistakes": d, "solution": sol, "concept": "Odd One Out (Numbers)"}

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
        d = mistakes(("counted the person twice by forgetting the -1", str(total + 1),
                      "−1 करना भूलकर उस व्यक्ति को दो बार गिन लिया"),
                     ("subtracted 1 twice", str(total - 1), "1 को दो बार घटा दिया"),
                     ("added the two positions and then added 1", str(total + 2),
                      "दोनों स्थान जोड़कर उसमें 1 और जोड़ दिया"),
                     ("used only the position from the left", str(left),
                      "केवल बाएँ से वाले स्थान को ही उत्तर मान लिया"),
                     ("used only the position from the right", str(right),
                      "केवल दाएँ से वाले स्थान को ही उत्तर मान लिया"),
                     ("counted the people on one side twice", str(2 * left - 1),
                      "एक ओर के व्यक्तियों को दो बार गिन लिया"))
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
        d = mistakes(("forgot the +1", str(right - 1), "+1 करना भूल गया"),
                     ("added 1 twice", str(right + 1), "1 को दो बार जोड़ दिया"),
                     ("subtracted the position from the total and stopped there",
                      str(total - left),
                      "कुल में से स्थान घटाकर वहीं रुक गया"),
                     ("repeated the position from the left", str(left),
                      "बाएँ से वाला स्थान ही दोहरा दिया"),
                     ("gave the total instead of a position", str(total),
                      "स्थान के बजाय कुल संख्या बता दी")) 
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
        d = mistakes(("counted one of the two people as 'between'", str(between + 1),
                      "दोनों में से एक व्यक्ति को भी 'बीच में' गिन लिया"),
                     ("counted both of them", str(between + 2),
                      "दोनों व्यक्तियों को भी बीच में गिन लिया"),
                     ("subtracted the two given positions directly, without converting "
                      "the right-end one", str(abs(b_right - a_left)),
                      "दाएँ छोर वाले स्थान को बदले बिना दोनों दिए गए स्थानों को सीधे घटा दिया"),
                     ("gave the gap between the two positions instead of the count between them",
                      str(b_left - a_left),
                      "बीच के व्यक्तियों के बजाय दोनों स्थानों का अंतर बता दिया"),
                     ("subtracted one too many", str(between - 1),
                      "एक अधिक घटा दिया"),
                     ("subtracted both positions from the total",
                      str(abs(total - a_left - b_right)),
                      "कुल में से दोनों स्थान घटा दिए"))
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
    d = mistakes(("gave the new position from the LEFT instead of the right", str(b_left),
                  "दाएँ के बजाय बाएँ से नया स्थान बता दिया"),
                 ("used the original position from the left", str(total - a_left + 1),
                  "बाएँ से मूल स्थान का ही प्रयोग कर लिया"),
                 ("forgot the +1 after subtracting", str(total - b_left),
                  "घटाने के बाद +1 करना भूल गया"),
                 ("added 1 instead of subtracting it", str(total - b_left + 2),
                  "1 घटाने के बजाय जोड़ दिया"),
                 ("swapped the two people the wrong way round", str(a_left),
                  "दोनों व्यक्तियों की अदला-बदली उल्टी दिशा में कर दी"),
                 ("moved the wrong person, keeping the second one in place",
                  str(total - a_left), "गलत व्यक्ति को हिलाया, दूसरे को वहीं रहने दिया"))
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(new_right),
            "mistakes": d, "solution": sol, "concept": "Ranking"}

def _b_ranking_pos(rng, diff):
    total = rng.randint(20, 45) if diff <= 2 else rng.randint(46, 90)
    left = rng.randint(5, total - 5)
    right = total - left + 1
    name = rng.choice(["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Anjali"])
    stem = (f"In a row of {total} students, {name} is {_ord(left)} from the left end. "
            f"What is {name}'s position from the right end?")
    sol = (f"Position from right = total − position from left + 1 = "
           f"{total} − {left} + 1 = {right}.")
    # Was right±1 and right±2 — four nudges, none of which is a mistake anyone actually makes.
    d = mistakes(("forgot the +1", str(right - 1), "+1 करना भूल गया"),
                 ("added 1 twice", str(right + 1), "1 को दो बार जोड़ दिया"),
                 ("subtracted the position from the total and stopped there", str(total - left),
                  "कुल में से स्थान घटाकर वहीं रुक गया"),
                 ("repeated the position from the left", str(left),
                  "बाएँ से वाला स्थान ही दोहरा दिया"),
                 ("gave the size of the row instead of a position", str(total),
                  "स्थान के बजाय पंक्ति की कुल संख्या बता दी"))
    stem_hi = (f"{total} विद्यार्थियों की एक पंक्ति में {HI.name(name)} बाईं ओर से {HI.ordinal(left)} "
               f"स्थान पर है। दाईं ओर से उसका स्थान क्या है?")
    sol_hi = f"दाएँ से स्थान = कुल − बाएँ से स्थान + 1 = {total} − {left} + 1 = {right}।"
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "correct": str(right),
            "mistakes": d, "solution": sol, "concept": "Ranking"}

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
        d = mistakes(("added the two distances instead of using Pythagoras", f"{a + b} km",
                      "पाइथागोरस लगाने के बजाय दोनों दूरियाँ जोड़ दीं"),
                     ("subtracted them", f"{abs(a - b)} km", "दोनों दूरियों को घटा दिया"),
                     ("used only the longer leg", f"{max(a, b)} km",
                      "केवल लंबी भुजा को ही उत्तर मान लिया"),
                     ("used only the shorter leg", f"{min(a, b)} km",
                      "केवल छोटी भुजा को ही उत्तर मान लिया"),
                     ("added the squares but forgot to take the square root",
                      f"{a * a + b * b} km",
                      "वर्गों का योग तो किया परन्तु वर्गमूल लेना भूल गया"))
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
        d = mistakes(("ignored the southward leg", f"{hyp} km",
                      "दक्षिण वाली दूरी को छोड़ दिया"),
                     ("added all three distances", f"{a + b + back} km",
                      "तीनों दूरियाँ जोड़ दीं"),
                     ("cancelled the wrong pair", f"{abs(b - back)} km",
                      "गलत जोड़े को काट दिया"),
                     ("cancelled the two north-south legs but then added the eastward one",
                      f"{net_n + b} km",
                      "उत्तर-दक्षिण तो काटे पर पूर्व वाली दूरी जोड़ दी"))
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
        d = mistakes(("added every leg walked", f"{n1 + e1 + n2 + e2} km",
                      "चली गई सभी दूरियों को जोड़ दिया"),
                     ("forgot to cancel the southward and westward legs", f"{hyp} km",
                      "दक्षिण और पश्चिम वाली दूरियाँ काटना भूल गया"),
                     ("added the two net legs instead of using Pythagoras",
                      f"{net_e + net_n} km",
                      "पाइथागोरस के बजाय दोनों शुद्ध दूरियाँ जोड़ दीं"),
                     ("cancelled only the north-south pair and left the east-west legs",
                      f"{net_n + e1 + e2} km",
                      "केवल उत्तर-दक्षिण जोड़ा काटा, पूर्व-पश्चिम वैसे ही छोड़ दिए"),
                     ("added the squares but forgot the square root",
                      f"{net_n * net_n + net_e * net_e} km",
                      "वर्गों का योग किया परन्तु वर्गमूल लेना भूल गया"),
                     ("used the larger net leg on its own", f"{max(net_n, net_e)} km",
                      "केवल बड़ी शुद्ध दूरी को ही उत्तर मान लिया"))
        correct = f"{root} km"
    else:
        d = mistakes(("read the first leg as the answer", "North",
                      "पहली दिशा को ही उत्तर मान लिया"),
                     ("cancelled the wrong pair, landing South-West", "South-West",
                      "गलत जोड़ा काटने पर दक्षिण-पश्चिम पहुँच गया"),
                     ("used only the East-West net movement", "East",
                      "केवल पूर्व-पश्चिम की शुद्ध गति देखी"))
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
    # Only three wrong compass points exist, so the option set is fixed — but each one is now the
    # result of a NAMED turning error rather than "the other three directions".
    net = sum(1 if t == "right" else -1 for t in turns)
    d = mistakes(("turned the wrong way at every turn", dirs[(start - net) % 4],
                  "हर मोड़ पर विपरीत दिशा में मुड़ा"),
                 ("counted one turn too many", dirs[(cur + 1) % 4],
                  "एक मोड़ अधिक गिन लिया"),
                 ("counted one turn too few", dirs[(cur - 1) % 4],
                  "एक मोड़ कम गिना"),
                 ("gave the starting direction, forgetting to turn at all", dirs[start],
                  "मुड़ना ही भूल गया और आरम्भिक दिशा बता दी"))
    seq_hi = ", फिर ".join(HI.TURN[t] for t in turns)
    stem_hi = (f"एक व्यक्ति आरम्भ में {HI.DIR[dirs[start]]} दिशा की ओर मुख किए है। वह {seq_hi} मुड़ता है। "
               f"अब उसका मुख किस दिशा की ओर है? (प्रत्येक मोड़ 90° का है।)")
    sol_hi = f"{HI.DIR[dirs[start]]} से आरम्भ कर प्रत्येक 90° मोड़ लगाने पर अंतिम दिशा = {HI.DIR[ans]}।"
    hi_opts = HI.dir_opts(dirs)
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
            "correct": ans, "mistakes": d, "solution": sol, "concept": "Direction — Facing"}

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


# One generation apart — the commonest blood-relation slip after reading the chain backwards.
_GEN_UP = {"father": "grandfather", "mother": "grandmother",
           "son": "grandson", "daughter": "granddaughter"}
_GEN_DOWN = {v: k for k, v in _GEN_UP.items()}


def _blood_mistakes(ans, links, rng):
    """NAMED wrong relations for a blood-relation item, all of the SAME GENDER as the answer.

    Same gender is deliberate and pre-dates this function: a mixed-gender option list hands the
    answer to anyone who only tracks whether the person is male or female, without tracing the
    chain at all. What is new is that each option now carries the reason it is wrong — before,
    three same-gender relations were drawn at RANDOM, so a wrong answer meant nothing more than
    "wrong" and the item could not be re-asked as an error-spot.

    The named errors come first and a same-gender filler backs them up, because gender narrows the
    pool so sharply that the named ones cannot always fill four slots.
    """
    male = _rel_is_male(ans)
    out = []

    def add(why, rel, why_hi):
        if not rel or rel == ans or _rel_is_male(rel) != male:
            return
        if any(o[1] == rel.capitalize() for o in out):
            return
        out.append((why, rel.capitalize(), why_hi))

    add("read the chain the other way round", _INV.get(ans),
        "सम्बन्ध-शृंखला को उल्टी दिशा में पढ़ लिया")
    for i, r in enumerate(links):
        add(f"stopped at the {_ord(i + 1)} link instead of tracing the whole chain", r,
            f"पूरी शृंखला जोड़ने के बजाय {i + 1}वीं कड़ी पर ही रुक गया")
    add("went one generation too far", _GEN_UP.get(ans), "एक पीढ़ी आगे चला गया")
    add("went one generation too few", _GEN_DOWN.get(ans), "एक पीढ़ी पीछे रह गया")
    pool = [r for r in _ALL_RELS if r != ans and _rel_is_male(r) == male]
    rng.shuffle(pool)
    for r in pool:
        if len(out) >= 5:
            break
        add("picked another relation of the same gender without tracing the chain", r,
            "शृंखला जोड़े बिना उसी लिंग का कोई अन्य सम्बन्ध चुन लिया")
    return mistakes(*out)


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
        d = _blood_mistakes(final, (r1, r2, r3, ans), rng)
        hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
        hi_opts[final.capitalize()] = fin_hi
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
                "correct": final.capitalize(), "mistakes": d,
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
        d = _blood_mistakes(inv, (r1, r2, ans), rng)
        hi_opts = {x.capitalize(): HI.rel(x) for x in _ALL_RELS}
        return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
                "correct": inv.capitalize(), "mistakes": d,
                "solution": sol, "concept": "Blood Relations"}
    return {"stem": stem, "stem_hi": stem_hi, "solution_hi": sol_hi, "hi_opts": hi_opts,
            "correct": ans.capitalize(), "mistakes": _blood_mistakes(ans, (r1, r2), rng),
            "solution": sol, "concept": "Blood Relations"}


def _rel_is_male(r):
    return r in ("grandfather", "father", "brother", "uncle", "nephew", "grandson")


# =============================================================================
# खंड (ग) — the families the eleven builders above do NOT reach
# =============================================================================
# One Step's owner read the generated papers and said Part III "has very basic questions and it
# contains only one topic, not distributed across the syllabus." Measured, he was right twice over:
# one concept took 16 of 50 questions, and all eleven concepts are ONE FAMILY — trace a
# relationship, or shift letters and numbers along a sequence. Our own difficulty tag said 32 of
# those 50 were difficulty 4; he still called them basic, because he is judging the TOPIC and the
# tag counts steps. A four-step blood-relation chain is still blood relations.
#
# खंड (ग) मानसिक क्षमता जाँच names सादृश्य · समानता एवं भिन्नता · स्थान कल्पना · समस्या समाधान ·
# विश्लेषण · दृश्य स्मृति · अवलोकन · संबंध अवधारणा · अंक गणितीय तर्कशक्ति · श्रृंखला · कूट लेखन.
# The five builders below are the strands we had nothing for: syllogism (विश्लेषण), seating
# arrangement (समस्या समाधान), coded inequality (विश्लेषण), calendar (अंक गणितीय तर्कशक्ति on the
# calendar) and dice (स्थान कल्पना). All five are ALGORITHMIC, so each answer is COMPUTED — the
# same guarantee the eleven above carry, extended to families a candidate actually finds hard.
#
# Non-verbal / figure series is the one खंड (ग) strand still missing; it needs SVG and is a
# separate build.

# ---- Syllogism (न्याय-निगमन) -------------------------------------------------
#
# The answer is decided by MODEL CHECKING, not by a table of valid moods. A conclusion follows iff
# it is true in EVERY arrangement of the terms that satisfies the premises, so the engine reasons
# about arrangements directly: every membership pattern over the k terms is a "cell", a model is a
# choice of which cells are occupied, and a universal premise simply forbids certain cells.
#
# Two exam conventions are built in, and both are load-bearing:
#   - every term names a real, non-empty category (so "All A are B" carries existential import)
#   - a conclusion must hold in every model, not merely in a possible one — the single mistake that
#     costs candidates the most marks on this question type

_SYL_TERMS = [
    ("cats", "बिल्लियाँ"), ("dogs", "कुत्ते"), ("animals", "जानवर"), ("birds", "पक्षी"),
    ("flowers", "फूल"), ("trees", "पेड़"), ("books", "पुस्तकें"), ("pens", "कलमें"),
    ("doctors", "डॉक्टर"), ("teachers", "शिक्षक"), ("students", "विद्यार्थी"),
    ("chairs", "कुर्सियाँ"), ("tables", "मेज़ें"), ("fruits", "फल"), ("stones", "पत्थर"),
    ("rivers", "नदियाँ"), ("cities", "नगर"), ("soldiers", "सैनिक"),
]

_SYL_EN = {"all": "All {X} are {Y}.", "no": "No {X} are {Y}.",
           "some": "Some {X} are {Y}.", "some_not": "Some {X} are not {Y}."}
_SYL_HI = {"all": "सभी {X}, {Y} हैं।", "no": "कोई भी {X}, {Y} नहीं है।",
           "some": "कुछ {X}, {Y} हैं।", "some_not": "कुछ {X}, {Y} नहीं हैं।"}

_SYL_OPTS = ["Only conclusion I follows", "Only conclusion II follows",
             "Both I and II follow", "Neither I nor II follows"]
_SYL_OPTS_HI = ["केवल निष्कर्ष I अनुसरण करता है", "केवल निष्कर्ष II अनुसरण करता है",
                "I और II दोनों अनुसरण करते हैं", "न तो I और न ही II अनुसरण करता है"]
_SYL_HI_OPTS = dict(zip(_SYL_OPTS, _SYL_OPTS_HI))

# A pair of CONTRADICTORY conclusions on the same ordered pair of terms — exactly one of them must
# be true of any arrangement, so when neither follows the honest exam answer is "Either I or II
# follows". We do not offer that option, so an instance that lands there is refused rather than
# keyed "Neither" and argued about with a teacher who is right.
_SYL_CONTRA = {frozenset(("all", "some_not")), frozenset(("no", "some"))}


def _syl_permits(cell, st):
    """Does this membership pattern survive a UNIVERSAL premise? Particulars constrain models,
    not individual cells, so they permit everything here."""
    kind, x, y = st
    inx, iny = bool(cell >> x & 1), bool(cell >> y & 1)
    if kind == "all":
        return not (inx and not iny)
    if kind == "no":
        return not (inx and iny)
    return True


def _syl_sat(cells, sts, k):
    """Occupy exactly `cells`: do all the statements hold, and is every term inhabited?"""
    cells = list(cells)
    if not cells:
        return False
    for t in range(k):
        if not any(c >> t & 1 for c in cells):
            return False                                   # a term with no members
    for st in sts:
        kind, x, y = st
        if kind in ("all", "no"):
            if not all(_syl_permits(c, st) for c in cells):
                return False
        elif kind == "some":
            if not any((c >> x & 1) and (c >> y & 1) for c in cells):
                return False
        elif kind == "some_not":
            if not any((c >> x & 1) and not (c >> y & 1) for c in cells):
                return False
    return True


def _syl_follows(sts, k, concl):
    """True / False / None(premises impossible). Checked by looking for a COUNTERMODEL.

    A universal conclusion is broken by occupying one offending cell, and occupying every permitted
    cell is the arrangement most likely to satisfy the premises — so the maximal model settles it.
    A particular conclusion is broken by occupying NO cell that would make it true, so the maximal
    model minus those cells settles that one. Two lines, and no enumeration of 2^cells models.
    """
    allowed = [c for c in range(1, 1 << k) if all(_syl_permits(c, s) for s in sts)]
    if not _syl_sat(allowed, sts, k):
        return None
    kind, x, y = concl
    if kind in ("all", "no"):
        broken = [c for c in allowed if (c >> x & 1)
                  and ((not (c >> y & 1)) if kind == "all" else (c >> y & 1))]
        return not broken
    avoid = [c for c in allowed if (c >> x & 1)
             and ((c >> y & 1) if kind == "some" else not (c >> y & 1))]
    return not _syl_sat([c for c in allowed if c not in avoid], sts, k)


def _syl_text(st, terms, hi=False):
    kind, x, y = st
    tmpl = (_SYL_HI if hi else _SYL_EN)[kind]
    return tmpl.format(X=terms[x][1 if hi else 0], Y=terms[y][1 if hi else 0])


def _b_syllogism(rng, diff):
    """Syllogism. Difficulty = the SHAPE of the premises, so a band can never emit an easier one.

    diff 1  two universal affirmatives      : All A are B; All B are C
    diff 2  one universal NEGATIVE           : the "no ... is" premise, where conversion goes wrong
    diff 3  one PARTICULAR premise           : "some", where a candidate who reads it as "all" fails
    diff 4+ THREE premises over four terms   : the chain has to be held, not pictured
    """
    n_terms = 4 if diff >= 4 else 3
    terms = rng.sample(_SYL_TERMS, n_terms)
    for _ in range(60):
        if diff <= 1:
            sts = [("all", 0, 1), ("all", 1, 2)]
        elif diff == 2:
            sts = ([("all", 0, 1), ("no", 1, 2)] if rng.random() < 0.5
                   else [("no", 0, 1), ("all", 1, 2)])
        elif diff == 3:
            sts = ([("all", 0, 1), ("some", 1, 2)] if rng.random() < 0.5
                   else [("some", 0, 1), ("all", 1, 2)])
        else:
            kinds = rng.sample(["all", "no", "some", "all"], 3)
            sts = [(kinds[i], i, i + 1) for i in range(3)]
        a, z = 0, n_terms - 1
        cands = [("all", a, z), ("all", z, a), ("no", a, z),
                 ("some", a, z), ("some", z, a), ("some_not", a, z), ("some_not", z, a)]
        truth = {c: _syl_follows(sts, n_terms, c) for c in cands}
        if None in truth.values():
            continue                                        # premises cannot all hold at once
        # Aim at a randomly chosen ANSWER and then look for a conclusion pair that produces it, so
        # the four options come up about equally often. Drawing two conclusions at random instead
        # makes "Neither" the answer to most questions, which a candidate learns to exploit.
        want = rng.choice([(True, False), (False, True), (True, True), (False, False)])
        pairs = [(c1, c2) for c1 in cands for c2 in cands if c1 != c2
                 and (truth[c1], truth[c2]) == want
                 and not (truth[c1] is False and truth[c2] is False
                          and c1[1:] == c2[1:]
                          and frozenset((c1[0], c2[0])) in _SYL_CONTRA)]
        if not pairs:
            continue
        c1, c2 = rng.choice(pairs)
        correct = _SYL_OPTS[{(True, False): 0, (False, True): 1,
                             (True, True): 2, (False, False): 3}[want]]
        st_en = " ".join(_syl_text(s, terms) for s in sts)
        st_hi = " ".join(_syl_text(s, terms, hi=True) for s in sts)
        stem = (f"Statements: {st_en}  Conclusions: I. {_syl_text(c1, terms)} "
                f"II. {_syl_text(c2, terms)}  Which of the conclusions follows from the "
                f"statements?")
        stem_hi = (f"कथन: {st_hi}  निष्कर्ष: I. {_syl_text(c1, terms, hi=True)} "
                   f"II. {_syl_text(c2, terms, hi=True)}  कौन-सा निष्कर्ष कथनों का अनुसरण करता है?")
        sol = (f"Conclusion I {'follows' if truth[c1] else 'does not follow'} and conclusion II "
               f"{'follows' if truth[c2] else 'does not follow'}: a conclusion counts only if it "
               f"is true in EVERY arrangement the statements allow, not merely in one of them. "
               f"Hence — {correct}.")
        sol_hi = (f"निष्कर्ष I {'अनुसरण करता है' if truth[c1] else 'अनुसरण नहीं करता'} तथा "
                  f"निष्कर्ष II {'अनुसरण करता है' if truth[c2] else 'अनुसरण नहीं करता'}। "
                  f"निष्कर्ष तभी मान्य है जब वह कथनों से बनने वाली हर सम्भव स्थिति में सत्य हो, "
                  f"केवल किसी एक स्थिति में नहीं। अतः — {_SYL_HI_OPTS[correct]}।")
        d = mistakes(
            ("converted a premise — read 'All A are B' as though it also gave 'All B are A'",
             _SYL_OPTS[2],
             "कथन को उलट दिया — 'सभी A, B हैं' को 'सभी B, A हैं' भी मान लिया"),
            ("accepted a conclusion that holds in ONE possible arrangement instead of every one",
             _SYL_OPTS[0 if correct != _SYL_OPTS[0] else 1],
             "ऐसा निष्कर्ष मान लिया जो किसी एक सम्भव स्थिति में सत्य है, हर स्थिति में नहीं"),
            ("read 'Some' as 'All'", _SYL_OPTS[3], "'कुछ' को 'सभी' पढ़ लिया"),
            ("took the second conclusion alone because it repeats a premise's wording",
             _SYL_OPTS[1],
             "दूसरे निष्कर्ष को केवल इसलिए चुन लिया क्योंकि उसके शब्द कथन जैसे हैं"))
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": correct, "mistakes": d, "options": _SYL_OPTS,
                "hi_opts": _SYL_HI_OPTS, "concept": "Syllogism"}
    return None


# ---- Seating arrangement (बैठक व्यवस्था) --------------------------------------
#
# The clues are DERIVED from a randomly chosen arrangement and then checked by brute force to admit
# exactly one arrangement before the question is allowed out. That check is the whole builder: a
# seating question with two valid arrangements has two defensible answers, and no amount of careful
# clue-writing tells you which you have written.

_SEAT_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikas", "Anjali", "Rohan",
               "Meena", "Arun", "Radha", "Sunil", "Neha"]


def _seat_holds(clue, perm, n, circular):
    """One clue against one candidate arrangement. `perm[i]` is the person in seat i.

    Linear seats run left to right. Circular seats run CLOCKWISE and everyone faces the centre, so
    a person's left hand points clockwise (seat i+1) and their right hand anticlockwise (seat i-1).
    Getting that backwards is the single most common error on this question type, which is why it
    is written down once here and used by both the clue check and the answer.
    """
    kind = clue[0]
    at = {p: i for i, p in enumerate(perm)}
    if kind == "end":
        _, p, side = clue
        return at[p] == (0 if side == "left" else n - 1)
    if kind == "from_end":
        _, p, k, side = clue
        return at[p] == (k - 1 if side == "left" else n - k)
    if kind == "next_to":
        _, p, q, side = clue                 # p is immediately to the `side` of q
        if circular:
            step = 1 if side == "left" else -1
            return at[p] == (at[q] + step) % n
        return at[p] == at[q] + (-1 if side == "left" else 1)
    if kind == "between":
        _, p, q, m = clue
        return abs(at[p] - at[q]) == m + 1
    if kind == "nth_of":
        _, p, k, side, q = clue              # p sits k-th to the `side` of q
        step = k if side == "left" else -k
        return at[p] == (at[q] + step) % n
    raise ValueError(kind)


def _seat_solutions(clues, names, n, circular):
    """Every arrangement the clues allow. Circular arrangements are counted up to ROTATION, which
    is what makes 'who sits second to the right of X' a well-posed question."""
    import itertools
    out = []
    if circular:
        head, rest = names[0], names[1:]
        for tail in itertools.permutations(rest):
            perm = [head] + list(tail)
            if all(_seat_holds(c, perm, n, True) for c in clues):
                out.append(perm)
                if len(out) > 1:
                    return out
    else:
        for perm in itertools.permutations(names):
            if all(_seat_holds(c, list(perm), n, False) for c in clues):
                out.append(list(perm))
                if len(out) > 1:
                    return out
    return out


def _seat_render(clue, circular):
    """(english, hindi) for one clue. Both halves carry the SAME digits, which is what
    paper_common.numbers_agree() checks — a Hindi clue that spelled '2' as 'दो' would be silently
    dropped from the paper along with the whole question."""
    kind = clue[0]
    side_en = {"left": "left", "right": "right"}
    side_hi = {"left": "बाएँ", "right": "दाएँ"}
    if kind == "end":
        _, p, s = clue
        return (f"{p} sits at the extreme {side_en[s]} end.",
                f"{HI.name(p)} पंक्ति के अत्यंत {side_hi[s]} छोर पर {HI.sits(p)}।")
    if kind == "from_end":
        _, p, k, s = clue
        return (f"{p} sits {_ord(k)} from the {side_en[s]} end.",
                f"{HI.name(p)} {side_hi[s]} छोर से {k}वें स्थान पर {HI.sits(p)}।")
    if kind == "next_to":
        _, p, q, s = clue
        return (f"{p} sits immediately to the {side_en[s]} of {q}.",
                f"{HI.name(p)}, {HI.name(q)} के ठीक {side_hi[s]} {HI.sits(p)}।")
    if kind == "between":
        _, p, q, m = clue
        return (f"There are exactly {m} persons between {p} and {q}.",
                f"{HI.name(p)} और {HI.name(q)} के बीच ठीक {m} व्यक्ति बैठे हैं।")
    _, p, k, s, q = clue
    word_en = {2: "second", 3: "third"}[k]
    word_hi = {2: "दूसरे", 3: "तीसरे"}[k]
    return (f"{p} sits {word_en} to the {side_en[s]} of {q}.",
            f"{HI.name(p)}, {HI.name(q)} के {side_hi[s]} से {word_hi} स्थान पर {HI.sits(p)}।")


def _seat_candidate_clues(perm, n, circular, rng):
    """Every clue TRUE of this arrangement, shuffled — the pool the question is built from."""
    cl = []
    if not circular:
        for i, p in enumerate(perm):
            if i == 0:
                cl.append(("end", p, "left"))
            elif i == n - 1:
                cl.append(("end", p, "right"))
            else:
                cl.append(("from_end", p, i + 1, "left"))
                cl.append(("from_end", p, n - i, "right"))
        for i in range(n - 1):
            cl.append(("next_to", perm[i + 1], perm[i], "right"))
            cl.append(("next_to", perm[i], perm[i + 1], "left"))
        for i in range(n):
            for j in range(i + 2, n):
                cl.append(("between", perm[i], perm[j], j - i - 1))
    else:
        for i in range(n):
            cl.append(("next_to", perm[(i + 1) % n], perm[i], "left"))
            cl.append(("next_to", perm[(i - 1) % n], perm[i], "right"))
            for k in (2, 3):
                cl.append(("nth_of", perm[(i + k) % n], k, "left", perm[i]))
                cl.append(("nth_of", perm[(i - k) % n], k, "right", perm[i]))
    rng.shuffle(cl)
    return cl


def _b_seating(rng, diff):
    """Seating arrangement. Difficulty = the table and how the answer must be counted.

    diff 1  five in a ROW              -> who is at the far end
    diff 2  six in a ROW               -> who is third from the left, so the seat must be counted
    diff 3  five around a CIRCLE       -> who sits second to the RIGHT, where facing the centre
                                          reverses left and right
    diff 4+ seven around a CIRCLE      -> third to the left, over a longer table
    """
    circular = diff >= 3
    n = {1: 5, 2: 6, 3: 5}.get(min(diff, 4), 7)
    for _ in range(40):
        names = rng.sample(_SEAT_NAMES, n)
        perm = names[:]
        rng.shuffle(perm)
        if circular:
            perm = [names[0]] + [p for p in perm if p != names[0]]   # anchor, see _seat_solutions
        clues = []
        for c in _seat_candidate_clues(perm, n, circular, rng):
            clues.append(c)
            if len(_seat_solutions(clues, names, n, circular)) == 1:
                break
        if len(_seat_solutions(clues, names, n, circular)) != 1 or len(clues) > 6:
            continue
        # Drop any clue the others already imply — a redundant clue makes the question look harder
        # while giving the answer away twice.
        trimmed = list(clues)
        for c in list(trimmed):
            if len(trimmed) > 1:
                rest = [x for x in trimmed if x is not c]
                if len(_seat_solutions(rest, names, n, circular)) == 1:
                    trimmed = rest
        clues = trimmed
        rng.shuffle(clues)
        rendered = [_seat_render(c, circular) for c in clues]
        who = rng.choice(perm)
        i = perm.index(who)
        if diff <= 1:
            ans = perm[n - 1]
            ask_en, ask_hi = ("Who is sitting at the extreme right end?",
                              "अत्यंत दाएँ छोर पर कौन बैठा है?")
            d = mistakes(("read the row from the wrong end", perm[0], "पंक्ति को गलत छोर से पढ़ा"),
                         ("stopped one seat short of the end", perm[n - 2], "छोर से एक सीट पहले ही रुक गया"),
                         ("took the person next to the left end", perm[1], "बाएँ छोर के बगल वाले व्यक्ति को चुन लिया"))
        elif diff == 2:
            ans = perm[2]
            ask_en, ask_hi = ("Who is sitting third from the left end?",
                              "बाएँ छोर से तीसरे स्थान पर कौन बैठा है?")
            d = mistakes(("counted from the right end instead of the left", perm[n - 3], "बाएँ के बजाय दाएँ छोर से गिना"),
                         ("started the count at the second seat", perm[3], "गिनती दूसरी सीट से शुरू कर दी"),
                         ("counted the third seat starting from zero", perm[1], "तीसरी सीट की गिनती शून्य से शुरू कर दी"))
        elif diff == 3:
            ans = perm[(i - 2) % n]
            ask_en = f"Who sits second to the right of {who}?"
            ask_hi = f"{HI.name(who)} के दाएँ से दूसरे स्थान पर कौन बैठा है?"
            d = mistakes(("took left for right — facing the centre reverses them",
                          perm[(i + 2) % n],
                          "बाएँ-दाएँ उलट दिए — केंद्र की ओर मुख होने पर ये बदल जाते हैं"),
                         (f"counted {who} as the first place", perm[(i - 1) % n],
                          f"{HI.name(who)} को ही पहला स्थान गिन लिया"),
                         ("turned the wrong way and counted one place", perm[(i + 1) % n],
                          "गलत दिशा में मुड़कर एक ही स्थान गिना"))
        else:
            ans = perm[(i + 3) % n]
            ask_en = f"Who sits third to the left of {who}?"
            ask_hi = f"{HI.name(who)} के बाएँ से तीसरे स्थान पर कौन बैठा है?"
            d = mistakes(("took left for right — facing the centre reverses them",
                          perm[(i - 3) % n],
                          "बाएँ-दाएँ उलट दिए — केंद्र की ओर मुख होने पर ये बदल जाते हैं"),
                         (f"counted {who} as the first place", perm[(i + 2) % n],
                          f"{HI.name(who)} को ही पहला स्थान गिन लिया"),
                         ("counted only one place instead of three", perm[(i + 1) % n],
                          "तीन के बजाय केवल एक स्थान गिना"))
        seat_en = (f"{', '.join(names[:-1])} and {names[-1]} are sitting "
                   + ("around a circular table facing the centre. "
                      if circular else "in a row. "))
        seat_hi = (f"{', '.join(HI.name(x) for x in names[:-1])} तथा {HI.name(names[-1])} "
                   + ("एक गोल मेज़ के चारों ओर बैठे हैं और सभी का मुख केंद्र की ओर है। "
                      if circular else "एक पंक्ति में बैठे हैं। "))
        stem = seat_en + " ".join(e for e, _ in rendered) + "  " + ask_en
        stem_hi = seat_hi + " ".join(h for _, h in rendered) + "  " + ask_hi
        order = " → ".join(perm) if not circular else " → ".join(perm) + " (clockwise)"
        sol = (f"The clues admit exactly one arrangement — {order}. " + (
               "Facing the centre, a person's right hand points anticlockwise. " if circular
               else "") + f"So the answer is {ans}.")
        sol_hi = ("दिए गए संकेतों से केवल एक ही व्यवस्था बनती है — "
                  + " → ".join(HI.name(x) for x in perm)
                  + ("  (घड़ी की दिशा में)। केंद्र की ओर मुख होने पर व्यक्ति का दाहिना हाथ "
                     "घड़ी की विपरीत दिशा में होता है। " if circular else "। ")
                  + f"अतः उत्तर {HI.name(ans)} है।")
        hi_opts = {p: HI.name(p) for p in names}
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": ans, "mistakes": d, "hi_opts": hi_opts,
                "concept": "Seating Arrangement"}
    return None


# ---- Coded inequality (कूटबद्ध असमिका) ----------------------------------------

_INEQ_REL = {
    "gt": ("is greater than", "से बड़ा है"),
    "lt": ("is smaller than", "से छोटा है"),
    "eq": ("is equal to", "के बराबर है"),
    "ge": ("is either greater than or equal to", "से बड़ा है अथवा उसके बराबर है"),
    "le": ("is either smaller than or equal to", "से छोटा है अथवा उसके बराबर है"),
}
# NOT "$". The paper renders every string through paper_common.mathify, which strips `$` as a LaTeX
# math delimiter — so the symbol was DELETED from the page and three questions per paper printed
# "'A  B' means 'A is smaller than B'" with no symbol at all, then used that symbol in the
# statements. Every structural check passed on that page; the only thing that caught it was the
# independent solver refusing to read the question. Anything mathify touches is unusable here:
# `$`, `\`, `^`, `_`, `{`, `}`.
_INEQ_SYMS = ["@", "#", "*", "%", "&"]
_INEQ_DIR = {"gt": (1, True), "ge": (1, False), "lt": (-1, True), "le": (-1, False),
             "eq": (0, False)}
_INEQ_BACK = {(1, True): "gt", (1, False): "ge", (-1, True): "lt", (-1, False): "le",
              (0, False): "eq"}
_INEQ_FLIP = {"gt": "lt", "lt": "gt", "ge": "le", "le": "ge", "eq": "eq"}


def _ineq_compose(a, b):
    """Chain two relations. Opposite directions give NOTHING — which is the whole question."""
    if a is None or b is None:
        return None
    if a == "eq":
        return b
    if b == "eq":
        return a
    da, sa = _INEQ_DIR[a]
    db, sb = _INEQ_DIR[b]
    if da != db:
        return None
    return _INEQ_BACK[(da, sa or sb)]


def _ineq_true(derived, claim):
    """Is `claim` DEFINITELY true given the relation the chain establishes?"""
    if derived is None:
        return False
    return {"gt": derived == "gt",
            "ge": derived in ("gt", "ge", "eq"),
            "lt": derived == "lt",
            "le": derived in ("lt", "le", "eq"),
            "eq": derived == "eq"}[claim]


def _b_coded_inequality(rng, diff):
    """Coded inequality. Difficulty = the length of the chain the conclusion has to cross.

    diff 1  three terms, strict relations only
    diff 2  four terms, non-strict relations allowed — where '>' and '>=' stop being interchangeable
    diff 3  five terms
    diff 4+ six terms, with at least one non-strict link guaranteed, so the answer turns on whether
            equality is still possible after four links
    """
    n = {1: 3, 2: 4, 3: 5}.get(min(diff, 4), 6)
    kinds = ["gt", "lt", "eq"] if diff <= 1 else ["gt", "lt", "eq", "ge", "le"]
    letters = rng.sample(["P", "Q", "R", "S", "T", "U", "V", "W"], n)
    syms = dict(zip(["gt", "lt", "eq", "ge", "le"], rng.sample(_INEQ_SYMS, 5)))
    for _ in range(60):
        links = [rng.choice(kinds) for _ in range(n - 1)]
        if diff >= 4 and not any(l in ("ge", "le") for l in links):
            continue
        # every derivable relation, both ways round
        rel = {}
        for i in range(n):
            cur = "eq"
            for j in range(i + 1, n):
                cur = _ineq_compose(cur, links[j - 1])
                rel[(i, j)] = cur
                rel[(j, i)] = _INEQ_FLIP[cur] if cur else None
        spans = [(i, j) for i in range(n) for j in range(n) if i != j]
        if diff >= 3:
            spans = [(i, j) for i, j in spans if abs(i - j) >= 2] or spans
        c1 = (rng.choice(spans), rng.choice(list(_INEQ_REL)))
        c2 = (rng.choice(spans), rng.choice(list(_INEQ_REL)))
        if c1 == c2:
            continue
        t1 = _ineq_true(rel[c1[0]], c1[1])
        t2 = _ineq_true(rel[c2[0]], c2[1])
        # A complementary pair — "P > S" beside "S >= P" — has exactly one true member in any real
        # ordering, so when neither DEFINITELY follows the honest answer is "Either I or II", which
        # this four-option paper does not offer. Refuse the instance instead of keying it "Neither"
        # and being right only by a technicality.
        if not t1 and not t2:
            (i1, j1), k1 = c1
            (i2, j2), k2 = c2
            same = (i1, j1) == (i2, j2)
            flipped = (i1, j1) == (j2, i2)
            k2n = k2 if same else _INEQ_FLIP[k2]
            if (same or flipped) and {k1, k2n} in ({"gt", "le"}, {"lt", "ge"}):
                continue
        correct = _SYL_OPTS[{(True, False): 0, (False, True): 1,
                             (True, True): 2, (False, False): 3}[(t1, t2)]]
        legend_en = "; ".join(f"'A {syms[k]} B' means 'A {_INEQ_REL[k][0]} B'"
                              for k in ("gt", "lt", "eq", "ge", "le"))
        legend_hi = "; ".join(f"'A {syms[k]} B' का अर्थ है 'A, B {_INEQ_REL[k][1]}'"
                              for k in ("gt", "lt", "eq", "ge", "le"))
        chain = ", ".join(f"{letters[i]} {syms[links[i]]} {letters[i + 1]}"
                          for i in range(n - 1))
        cc = lambda c: f"{letters[c[0][0]]} {syms[c[1]]} {letters[c[0][1]]}"
        stem = (f"In the following, the symbols are used as: {legend_en}.  "
                f"Statements: {chain}.  Conclusions: I. {cc(c1)}  II. {cc(c2)}  "
                f"Which of the conclusions is definitely true?")
        stem_hi = (f"नीचे दिए गए प्रश्न में संकेतों का प्रयोग इस प्रकार किया गया है: {legend_hi}।  "
                   f"कथन: {chain}।  निष्कर्ष: I. {cc(c1)}  II. {cc(c2)}  "
                   f"कौन-सा निष्कर्ष निश्चित रूप से सत्य है?")
        def _say(c, t):
            der = rel[c[0]]
            names = {"gt": ">", "lt": "<", "eq": "=", "ge": ">=", "le": "<="}
            got = names[der] if der else "no fixed relation"
            return (f"the chain gives {letters[c[0][0]]} {got} {letters[c[0][1]]}, so "
                    f"'{cc(c)}' is {'true' if t else 'not necessarily true'}")
        sol = (f"Reading the chain {chain}: I — {_say(c1, t1)}. II — {_say(c2, t2)}. "
               f"Hence — {correct}.")
        sol_hi = (f"शृंखला {chain} से: निष्कर्ष I "
                  f"{'सत्य है' if t1 else 'निश्चित रूप से सत्य नहीं है'}, निष्कर्ष II "
                  f"{'सत्य है' if t2 else 'निश्चित रूप से सत्य नहीं है'}। "
                  f"अतः — {_SYL_HI_OPTS[correct]}।")
        d = mistakes(
            ("treated '>=' as '>' — an equality is still possible across the chain",
             _SYL_OPTS[2],
             "'बड़ा या बराबर' को केवल 'बड़ा' मान लिया — शृंखला में बराबरी अब भी सम्भव है"),
            ("joined two links running in OPPOSITE directions as though they gave a relation",
             _SYL_OPTS[0 if correct != _SYL_OPTS[0] else 1],
             "विपरीत दिशाओं की दो कड़ियों को जोड़कर सम्बन्ध निकाल लिया"),
            ("read a conclusion backwards, swapping the two letters", _SYL_OPTS[1],
             "निष्कर्ष को उल्टा पढ़ लिया — दोनों अक्षरों की अदला-बदली कर दी"),
            ("assumed that when neither conclusion is proved the answer must still be one of them",
             _SYL_OPTS[3],
             "यह मान लिया कि कोई निष्कर्ष सिद्ध न होने पर भी उत्तर उन्हीं में से होगा"))
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": correct, "mistakes": d, "options": _SYL_OPTS,
                "hi_opts": _SYL_HI_OPTS, "concept": "Coded Inequality"}
    return None


# ---- Calendar (कैलेंडर) --------------------------------------------------------
#
# Every date here is resolved by a HAND-WRITTEN day count, not by `datetime`. That is deliberate:
# the independent solver in test_papers.py uses `datetime`, so the printed key and the check are
# reached by two genuinely different routes. A shared library would have made the check a
# restatement.

_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
_DAYS_HI = ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"]
_DAY_HI = dict(zip(_DAYS, _DAYS_HI))
_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]
_MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून",
              "जुलाई", "अगस्त", "सितम्बर", "अक्टूबर", "नवम्बर", "दिसम्बर"]
_MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _daynum(y, m, d):
    """Days elapsed to this date, counting 1 January 0001 as day 1 (proleptic Gregorian).

    The century rule is the whole difficulty of this topic: 1900 was NOT a leap year and 2000 was,
    and a candidate who applies 'divisible by 4' alone is a day out for every date after 1900.
    """
    y0 = y - 1
    n = 365 * y0 + y0 // 4 - y0 // 100 + y0 // 400
    n += sum(_MDAYS[:m - 1])
    if m > 2 and _leap(y):
        n += 1
    return n + d


def _weekday(y, m, d):
    return _DAYS[_daynum(y, m, d) % 7]


def _fmt(y, m, d, hi=False):
    return f"{d} {(_MONTHS_HI if hi else _MONTHS)[m - 1]} {y}"


def _b_calendar(rng, diff):
    """Calendar. Difficulty = which calendar fact has to be applied.

    diff 1  a day counted forward from a known day   : the remainder on division by 7
    diff 2  an absolute date                          : the century leap-year rule bites here
    diff 3  the same date some years later            : leap days inside the span must be counted
    diff 4+ the next year with an IDENTICAL calendar  : both the odd days and the leap cycle
    """
    if diff <= 1:
        start = rng.randrange(7)
        n = rng.choice([37, 45, 58, 61, 73, 88, 95, 100, 111, 125, 143, 160])
        ans = _DAYS[(start + n) % 7]
        stem = (f"Today is {_DAYS[start]}. What day of the week will it be after {n} days?")
        stem_hi = (f"आज {_DAYS_HI[start]} है। आज से {n} दिन बाद सप्ताह का कौन-सा दिन होगा?")
        sol = (f"{n} = 7 x {n // 7} + {n % 7}, so {n} days is {n // 7} full weeks and {n % 7} "
               f"odd day(s). {n % 7} day(s) after {_DAYS[start]} is {ans}.")
        sol_hi = (f"{n} = 7 x {n // 7} + {n % 7}; अतः {n} दिनों में {n // 7} पूरे सप्ताह तथा "
                  f"{n % 7} विषम दिन हैं। {_DAYS_HI[start]} के {n % 7} दिन बाद {_DAY_HI[ans]} होगा।")
        d = mistakes(("used the QUOTIENT of the division by 7 instead of the remainder",
                      _DAYS[(start + n // 7) % 7],
                      "7 से भाग देकर शेषफल के स्थान पर भागफल का प्रयोग किया"),
                     ("counted backwards instead of forwards", _DAYS[(start - n) % 7],
                      "आगे की ओर गिनने के बजाय पीछे की ओर गिना"),
                     ("counted today itself as the first day", _DAYS[(start + n + 1) % 7],
                      "आज के दिन को ही पहला दिन गिन लिया"),
                     ("stopped one day short", _DAYS[(start + n - 1) % 7],
                      "एक दिन पहले ही गिनती रोक दी"),
                     ("counted the odd days from Sunday instead of from today",
                      _DAYS[n % 7],
                      "विषम दिनों की गिनती आज के बजाय रविवार से शुरू कर दी"))
    elif diff == 2:
        y = rng.randint(1901, 2099)
        m = rng.randint(1, 12)
        dd = rng.randint(1, _MDAYS[m - 1])
        ans = _weekday(y, m, dd)
        stem = f"What was/will be the day of the week on {_fmt(y, m, dd)}?"
        stem_hi = f"{_fmt(y, m, dd, hi=True)} को सप्ताह का कौन-सा दिन था/होगा?"
        sol = (f"Counting the odd days from the start of the Gregorian cycle to "
               f"{_fmt(y, m, dd)} — remembering that a century year is a leap year only when it "
               f"is divisible by 400 — leaves {_daynum(y, m, dd) % 7} odd day(s), i.e. {ans}.")
        sol_hi = (f"{_fmt(y, m, dd, hi=True)} तक के विषम दिनों की गणना करने पर "
                  f"(शताब्दी वर्ष तभी लीप वर्ष होता है जब वह 400 से विभाज्य हो) "
                  f"{_daynum(y, m, dd) % 7} विषम दिन बचते हैं, अर्थात् {_DAY_HI[ans]}।")
        i = _DAYS.index(ans)
        d = mistakes(("counted one leap day too many", _DAYS[(i + 1) % 7],
                      "एक लीप-दिवस अधिक गिन लिया"),
                     ("counted one leap day too few", _DAYS[(i - 1) % 7],
                      "एक लीप-दिवस कम गिना"),
                     ("gave the day for the same date in the FOLLOWING year",
                      _weekday(y + 1, m, dd),
                      "अगले वर्ष की इसी तारीख का दिन बता दिया"),
                     ("gave the day for the same date in the PREVIOUS year",
                      _weekday(y - 1, m, dd),
                      "पिछले वर्ष की इसी तारीख का दिन बता दिया"),
                     ("gave the day for the first of that month",
                      _weekday(y, m, 1),
                      "उसी माह की पहली तारीख का दिन बता दिया"),
                     ("treated every century year as a leap year", _DAYS[(i + 2) % 7],
                      "प्रत्येक शताब्दी वर्ष को लीप वर्ष मान लिया"))
    elif diff == 3:
        y = rng.randint(1950, 2080)
        m = rng.randint(1, 12)
        dd = rng.randint(1, 28)
        k = rng.randint(2, 8)
        was = _weekday(y, m, dd)
        ans = _weekday(y + k, m, dd)
        leaps = sum(1 for t in range(y, y + k) if _leap(t + (0 if m > 2 else 0)))
        stem = (f"{_fmt(y, m, dd)} was a {was}. What day of the week will "
                f"{_fmt(y + k, m, dd)} be?")
        stem_hi = (f"{_fmt(y, m, dd, hi=True)} को {_DAY_HI[was]} था। "
                   f"{_fmt(y + k, m, dd, hi=True)} को सप्ताह का कौन-सा दिन होगा?")
        sol = (f"{k} years carry {k} odd days plus one for each 29 February in the span; "
               f"the total shift is {(_daynum(y + k, m, dd) - _daynum(y, m, dd)) % 7} day(s), "
               f"so {was} becomes {ans}.")
        sol_hi = (f"{k} वर्षों में {k} विषम दिन तथा बीच में आने वाली प्रत्येक 29 फ़रवरी के लिए "
                  f"एक अतिरिक्त दिन जुड़ता है; कुल खिसकाव "
                  f"{(_daynum(y + k, m, dd) - _daynum(y, m, dd)) % 7} दिन है, "
                  f"अतः {_DAY_HI[was]} बदलकर {_DAY_HI[ans]} हो जाएगा।")
        i0 = _DAYS.index(was)
        d = mistakes(("counted every year as 365 days, ignoring the leap years",
                      _DAYS[(i0 + k) % 7],
                      "प्रत्येक वर्ष को 365 दिन मानकर लीप वर्षों को छोड़ दिया"),
                     ("counted one leap day too many", _DAYS[(_DAYS.index(ans) + 1) % 7],
                      "एक लीप-दिवस अधिक गिन लिया"),
                     ("counted the shift backwards", _DAYS[(i0 - k) % 7],
                      "दिनों का खिसकाव उल्टी दिशा में गिना"))
        _ = leaps
    else:
        y = rng.randint(1901, 2070)
        ans_y = next(t for t in range(y + 1, y + 60)
                     if _weekday(t, 1, 1) == _weekday(y, 1, 1) and _leap(t) == _leap(y))
        ans = str(ans_y)
        stem = (f"Which of the following years will have exactly the same calendar as the "
                f"year {y}?")
        stem_hi = (f"निम्नलिखित में से किस वर्ष का कैलेंडर {y} के कैलेंडर के बिल्कुल समान होगा?")
        sol = (f"A year repeats its calendar only when 1 January falls on the same weekday AND "
               f"the leap status matches. {y} is {'a leap' if _leap(y) else 'an ordinary'} year "
               f"beginning on a {_weekday(y, 1, 1)}; the first later year meeting both conditions "
               f"is {ans_y}.")
        sol_hi = (f"किसी वर्ष का कैलेंडर तभी दोहराता है जब 1 जनवरी उसी वार को पड़े और लीप-स्थिति "
                  f"भी समान हो। {y} {'लीप' if _leap(y) else 'सामान्य'} वर्ष है तथा उसका आरम्भ "
                  f"{_DAY_HI[_weekday(y, 1, 1)]} से होता है; दोनों शर्तें पूरी करने वाला "
                  f"पहला वर्ष {ans_y} है।")
        named = [("added 6 years — the usual gap, but it fails across a leap year", y + 6,
                  "6 वर्ष जोड़ दिए — सामान्य अंतराल, किंतु लीप वर्ष पार करने पर यह गलत है"),
                 ("added 11 years — the gap that applies only after a leap year", y + 11,
                  "11 वर्ष जोड़ दिए — यह अंतराल केवल लीप वर्ष के बाद लागू होता है"),
                 ("added 28 years, which repeats only away from a century boundary", y + 28,
                  "28 वर्ष जोड़ दिए, जो केवल शताब्दी-सीमा से दूर ही दोहराता है"),
                 ("added 5 years", y + 5, "5 वर्ष जोड़ दिए"),
                 ("added 12 years", y + 12, "12 वर्ष जोड़ दिए")]
        d = mistakes(*[(w, str(v), h) for w, v, h in named if str(v) != ans])
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": ans, "mistakes": d, "concept": "Calendar"}
    return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
            "correct": ans, "mistakes": d, "hi_opts": dict(_DAY_HI), "concept": "Calendar"}


# ---- Dice (पासा) --------------------------------------------------------------
#
# A dice question normally needs two DRAWINGS of the cube, which we cannot produce. These are the
# text-only forms the same papers print: the faces are deduced by elimination from stated opposite
# pairs and adjacency lists, so the question is complete on the page. That matters — a question
# pointing at a figure we do not hold is unanswerable however good the key is.

def _b_dice(rng, diff):
    """Dice. Difficulty = how much of the pairing has to be deduced before the answer appears.

    diff 1  two opposite pairs stated      -> the third pair by elimination
    diff 2  the four faces ADJACENT to one -> its opposite is the number missing from that list
    diff 3  two adjacency lists            -> both have to be used before the third pair appears
    diff 4+ one adjacency list, one pair, and a SUM asked -> all three pairs must be settled
    """
    faces = [1, 2, 3, 4, 5, 6]
    sh = faces[:]
    rng.shuffle(sh)
    pairs = [(sh[0], sh[1]), (sh[2], sh[3]), (sh[4], sh[5])]
    opp = {}
    for a, b in pairs:
        opp[a], opp[b] = b, a
    adj = lambda f: sorted(x for x in faces if x != f and x != opp[f])
    if diff <= 1:
        (p1, p2), (q1, q2), (r1, r2) = pairs
        ask = r1
        ans = r2
        given_en = (f"In a dice with the faces numbered 1 to 6, {p1} is opposite {p2} and "
                    f"{q1} is opposite {q2}.")
        given_hi = (f"1 से 6 तक अंकित एक पासे में {p1} के सामने {p2} है तथा {q1} के सामने "
                    f"{q2} है।")
        sol = (f"{p1}-{p2} and {q1}-{q2} account for four faces, so the remaining two, "
               f"{r1} and {r2}, must be opposite each other. Hence {ask} is opposite {ans}.")
        sol_hi = (f"{p1}-{p2} तथा {q1}-{q2} से चार फलक तय हो जाते हैं; अतः शेष दो फलक "
                  f"{r1} और {r2} एक-दूसरे के सामने होंगे। इसलिए {ask} के सामने {ans} है।")
    elif diff == 2:
        ask = rng.choice(faces)
        ans = opp[ask]
        lst = adj(ask)
        given_en = (f"In a dice with the faces numbered 1 to 6, the four faces adjacent to "
                    f"{ask} are {', '.join(map(str, lst[:-1]))} and {lst[-1]}.")
        given_hi = (f"1 से 6 तक अंकित एक पासे में {ask} से लगे हुए चारों फलक "
                    f"{', '.join(map(str, lst[:-1]))} तथा {lst[-1]} हैं।")
        sol = (f"A face touches four others and is opposite the fifth. The only number missing "
               f"from the list is {ans}, so {ask} is opposite {ans}.")
        sol_hi = (f"कोई भी फलक चार फलकों से लगा होता है और पाँचवें के सामने होता है। "
                  f"सूची में केवल {ans} नहीं है, अतः {ask} के सामने {ans} है।")
    elif diff == 3:
        (p1, _p2), (q1, _q2), (r1, r2) = pairs
        l1, l2 = adj(p1), adj(q1)
        ask, ans = r1, r2
        given_en = (f"In a dice with the faces numbered 1 to 6, the faces adjacent to {p1} are "
                    f"{', '.join(map(str, l1))}, and the faces adjacent to {q1} are "
                    f"{', '.join(map(str, l2))}.")
        given_hi = (f"1 से 6 तक अंकित एक पासे में {p1} से लगे फलक "
                    f"{', '.join(map(str, l1))} हैं तथा {q1} से लगे फलक "
                    f"{', '.join(map(str, l2))} हैं।")
        sol = (f"The number missing from {p1}'s list is {_p2}, so {p1} is opposite {_p2}; "
               f"likewise {q1} is opposite {_q2}. That leaves {r1} and {r2}, which must face "
               f"each other, so {ask} is opposite {ans}.")
        sol_hi = (f"{p1} की सूची में {_p2} नहीं है, अतः {p1} के सामने {_p2} है; इसी प्रकार "
                  f"{q1} के सामने {_q2} है। शेष {r1} और {r2} एक-दूसरे के सामने होंगे, "
                  f"अतः {ask} के सामने {ans} है।")
    else:
        (p1, p2), (q1, q2), (r1, r2) = pairs
        l1 = adj(q1)
        a, b = r1, p1
        ans = opp[a] + opp[b]
        given_en = (f"In a dice with the faces numbered 1 to 6, {p1} is opposite {p2}, and the "
                    f"faces adjacent to {q1} are {', '.join(map(str, l1))}.")
        given_hi = (f"1 से 6 तक अंकित एक पासे में {p1} के सामने {p2} है तथा {q1} से लगे फलक "
                    f"{', '.join(map(str, l1))} हैं।")
        sol = (f"{q1}'s list is missing {q2}, so {q1} is opposite {q2}; with {p1} opposite {p2} "
               f"that leaves {r1} opposite {r2}. The face opposite {a} is {opp[a]} and the face "
               f"opposite {b} is {opp[b]}, so the sum is {opp[a]} + {opp[b]} = {ans}.")
        sol_hi = (f"{q1} की सूची में {q2} नहीं है, अतः {q1} के सामने {q2} है; {p1} के सामने "
                  f"{p2} होने से शेष {r1} के सामने {r2} रह जाता है। {a} के सामने {opp[a]} तथा "
                  f"{b} के सामने {opp[b]} है, अतः योग = {opp[a]} + {opp[b]} = {ans}।")
        stem = given_en + f"  What is the SUM of the numbers on the faces opposite to {a} and {b}?"
        stem_hi = given_hi + f"  {a} तथा {b} के सामने वाले फलकों की संख्याओं का योग क्या है?"
        d = mistakes(("added the two faces themselves instead of the faces opposite them",
                      str(a + b),
                      "सामने वाले फलकों के बजाय उन्हीं दोनों फलकों को जोड़ दिया"),
                     ("assumed opposite faces always add up to 7", str(14 - a - b),
                      "यह मान लिया कि आमने-सामने के फलकों का योग सदैव 7 होता है"),
                     (f"gave only the face opposite {a}", str(opp[a]),
                      f"केवल {a} के सामने वाला फलक बता दिया"))
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": str(ans), "mistakes": d, "concept": "Dice"}
    stem = given_en + f"  Which number is on the face opposite to {ask}?"
    stem_hi = given_hi + f"  {ask} के सामने वाले फलक पर कौन-सी संख्या है?"
    d = mistakes(("named the face itself instead of the one opposite it", str(ask),
                  "सामने वाले फलक के बजाय उसी फलक की संख्या बता दी"),
                 ("assumed opposite faces always add up to 7", str(7 - ask),
                  "यह मान लिया कि आमने-सामने के फलकों का योग सदैव 7 होता है"),
                 ("picked a face that touches it rather than the one opposite",
                  str(adj(ask)[0]),
                  "सामने वाले फलक के बजाय उससे लगा हुआ कोई फलक चुन लिया"),
                 ("picked another face that touches it", str(adj(ask)[-1]),
                  "उससे लगा हुआ कोई दूसरा फलक चुन लिया"),
                 ("gave the face opposite the wrong number", str(opp[adj(ask)[0]]),
                  "गलत संख्या के सामने वाला फलक बता दिया"))
    return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
            "correct": str(ans), "mistakes": d, "concept": "Dice"}


# ---- Symbol substitution (प्रतीक प्रतिस्थापन) ---------------------------------
#
# The real papers print this exact form — "If '–' stands for '+', '+' stands for '×' ... which of
# the following equations is correct?" — so it is authentic rather than invented. It is also two
# tests at once: applying the substitution, and then applying BODMAS to the result. Candidates who
# do the first and forget the second are the reason the left-to-right value is one of the options.
#
# Glyphs: +, -, × and ÷ all survive paper_common.mathify (checked, after `$` was silently deleted
# from the coded-inequality legend). Anything mathify touches would vanish from the page.

_OPGLYPH = ["+", "-", "×", "÷"]


def _eval_ops(nums, ops):
    """Evaluate with × and ÷ before + and −, written out by hand.

    Deliberately NOT Python's eval: the independent solver in test_papers.py uses eval, so the two
    routes only agree if this precedence walk is right. Fractions throughout, so a division that
    does not come out exact is visible rather than rounded away.
    """
    from fractions import Fraction as F
    vals, o = [F(n) for n in nums], list(ops)
    i = 0
    while i < len(o):
        if o[i] in ("×", "÷"):
            if o[i] == "÷" and vals[i + 1] == 0:
                return None
            vals[i:i + 2] = [vals[i] * vals[i + 1] if o[i] == "×" else vals[i] / vals[i + 1]]
            o.pop(i)
        else:
            i += 1
    r = vals[0]
    for i, op in enumerate(o):
        r = r + vals[i + 1] if op == "+" else r - vals[i + 1]
    return r


def _eval_l2r(nums, ops):
    """The value a candidate gets by working strictly left to right — a named mistake, not a nudge."""
    from fractions import Fraction as F
    r = F(nums[0])
    for i, op in enumerate(ops):
        n = F(nums[i + 1])
        if op == "+":
            r += n
        elif op == "-":
            r -= n
        elif op == "×":
            r *= n
        else:
            if n == 0:
                return None
            r /= n
    return r


def _eval_rev_prec(nums, ops):
    """The value a candidate gets by doing + and − FIRST and × and ÷ afterwards.

    A fourth named mistake, added because the obvious three collapse at the easy level: with only
    two operators, 'as printed', 'left to right' and 'backwards' keep landing on the same number.
    """
    from fractions import Fraction as F
    vals, o = [F(n) for n in nums], list(ops)
    i = 0
    while i < len(o):
        if o[i] in ("+", "-"):
            vals[i:i + 2] = [vals[i] + vals[i + 1] if o[i] == "+" else vals[i] - vals[i + 1]]
            o.pop(i)
        else:
            i += 1
    r = vals[0]
    for i, op in enumerate(o):
        if op == "÷":
            if vals[i + 1] == 0:
                return None
            r /= vals[i + 1]
        else:
            r *= vals[i + 1]
    return r


def _whole(x):
    return x is not None and x.denominator == 1 and abs(x) < 10 ** 6


def _b_symbol_substitution(rng, diff):
    """Symbol substitution. Difficulty = how much is re-mapped and how long the expression is.

    diff 1  two symbols swapped, three terms
    diff 2  all four symbols re-mapped, four terms
    diff 3  all four re-mapped, five terms
    diff 4+ WHICH EQUATION IS CORRECT — four candidate equations, each wrong one true under a
            named wrong method, so elimination by arithmetic does not work
    """
    for _ in range(80):
        real = list(_OPGLYPH)
        if diff <= 1:
            # A 3-CycLE, not a two-symbol swap. A swap is its own inverse, so "applied the
            # substitution the other way round" produces exactly the correct answer and can never
            # be offered as a distractor — measured, that alone killed every difficulty-1 draw
            # (0 questions from 400 seeds) while looking like an unlucky retry budget.
            i, j, k = rng.sample(range(4), 3)
            real[i], real[j], real[k] = real[j], real[k], real[i]
        else:
            for _ in range(40):                    # a derangement: no symbol may mean itself
                rng.shuffle(real)
                if all(a != b for a, b in zip(real, _OPGLYPH)):
                    break
            else:
                continue
        mapping = dict(zip(_OPGLYPH, real))        # printed symbol -> the operation to use
        inverse = {v: k for k, v in mapping.items()}
        n_terms = 3 if diff <= 1 else 4 if diff == 2 else 5
        nums = [rng.randint(2, 30) for _ in range(n_terms)]
        shown = [rng.choice(_OPGLYPH) for _ in range(n_terms - 1)]
        used = [mapping[s] for s in shown]
        val = _eval_ops(nums, used)
        if not _whole(val):
            continue
        expr = " ".join(str(nums[k]) + (f" {shown[k]}" if k < len(shown) else "")
                        for k in range(n_terms))
        legend_en = ", ".join(f"'{s}' stands for '{mapping[s]}'" for s in _OPGLYPH)
        legend_hi = ", ".join(f"'{s}' का अर्थ '{mapping[s]}' है" for s in _OPGLYPH)
        as_printed = _eval_ops(nums, shown)
        reversed_map = _eval_ops(nums, [inverse[s] for s in shown])
        l2r = _eval_l2r(nums, used)
        rev_prec = _eval_rev_prec(nums, used)
        if diff <= 3:
            stem = (f"If {legend_en}, then what is the value of {expr}?")
            stem_hi = (f"यदि {legend_hi}, तो {expr} का मान क्या होगा?")
            sol = (f"Substituting gives {' '.join(str(nums[k]) + (f' {used[k]}' if k < len(used) else '') for k in range(n_terms))}. "
                   f"Applying × and ÷ before + and −, the value is {val}.")
            sol_hi = (f"प्रतिस्थापन के बाद व्यंजक बनता है "
                      f"{' '.join(str(nums[k]) + (f' {used[k]}' if k < len(used) else '') for k in range(n_terms))}। "
                      f"× तथा ÷ को + और − से पहले हल करने पर मान = {val}।")
            d = mistakes(
                ("read the expression as printed, without applying the substitution at all",
                 str(as_printed) if _whole(as_printed) else None,
                 "प्रतिस्थापन लगाए बिना व्यंजक को जैसा छपा है वैसा ही हल कर दिया"),
                ("applied the substitution the other way round — used the symbol that the printed "
                 "one stands for", str(reversed_map) if _whole(reversed_map) else None,
                 "प्रतिस्थापन उल्टा लगा दिया — छपे प्रतीक के बजाय उसके अर्थ वाले प्रतीक का प्रयोग किया"),
                ("worked strictly left to right, ignoring the order of operations",
                 str(l2r) if _whole(l2r) else None,
                 "संक्रियाओं के क्रम को छोड़कर बाएँ से दाएँ हल कर दिया"),
                ("did the + and − first and the × and ÷ afterwards",
                 str(rev_prec) if _whole(rev_prec) else None,
                 "पहले + और − किए, उसके बाद × और ÷"))
            # Four candidate mistakes, of which any three distinct ones will do. They collide often
            # at the easy end — with two operators, "as printed" and "left to right" frequently
            # give the same number — so offering a fourth is what keeps difficulty 1 producible.
            seen_t = set()
            # Keep EVERY distinct named mistake. This used to truncate to three, which handed
            # order_mistakes a list exactly as long as the option slots and so silently disabled
            # the proximity dial on this builder. _mcq takes the first three AFTER ordering.
            d = [m for m in d
                 if m["text"] != str(val) and not (m["text"] in seen_t or seen_t.add(m["text"]))]
            texts = {m["text"] for m in d}
            # The substitution must actually BITE. A two-symbol swap can leave every operator in
            # the printed expression mapping to itself, and then "If '+' stands for '+', '-' stands
            # for '-' ... what is 2 + 23 - 26?" is plain arithmetic wearing a substitution costume —
            # the topic label is the only thing that makes it a reasoning question. Requiring the
            # answer to DIFFER from the as-printed value rules that out by construction.
            if len(texts) < 3 or str(val) in texts:
                continue                            # not three DISTINCT named mistakes
            return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                    "correct": str(val), "mistakes": d, "concept": "Symbol Substitution"}
        # diff 4+ : four equations, exactly one true under the substitution.
        # All four are built to the SAME length. The first version reused the five-term expression
        # from above as the correct equation while generating four-term distractors, so the answer
        # was the long one every time — findable without doing any arithmetic at all.
        eqs, whys, whys_hi = [], [], []
        for method, why, why_hi in (
                ("printed", "is true only if the substitution is ignored",
                 "तभी सत्य है जब प्रतिस्थापन को छोड़ दिया जाए"),
                ("reverse", "is true only if the substitution is applied backwards",
                 "तभी सत्य है जब प्रतिस्थापन उल्टा लगाया जाए"),
                ("l2r", "is true only if the expression is worked left to right",
                 "तभी सत्य है जब व्यंजक बाएँ से दाएँ हल किया जाए")):
            for _ in range(80):
                nn = [rng.randint(2, 30) for _ in range(4)]
                ss = [rng.choice(_OPGLYPH) for _ in range(3)]
                right = _eval_ops(nn, [mapping[s] for s in ss])
                wrong = {"printed": _eval_ops(nn, ss),
                         "reverse": _eval_ops(nn, [inverse[s] for s in ss]),
                         "l2r": _eval_l2r(nn, [mapping[s] for s in ss])}[method]
                if not _whole(wrong) or wrong == right:
                    continue                        # it would be a SECOND correct equation
                eqs.append(" ".join(str(nn[k]) + (f" {ss[k]}" if k < 3 else "")
                                    for k in range(4)) + f" = {wrong}")
                whys.append(why)
                whys_hi.append(why_hi)
                break
        good = None
        for _ in range(80):
            gn = [rng.randint(2, 30) for _ in range(4)]
            gs = [rng.choice(_OPGLYPH) for _ in range(3)]
            gv = _eval_ops(gn, [mapping[s] for s in gs])
            if not _whole(gv) or gv == _eval_ops(gn, gs):
                continue                            # substitution must change the value
            good = " ".join(str(gn[k]) + (f" {gs[k]}" if k < 3 else "")
                            for k in range(4)) + f" = {gv}"
            val = gv
            break
        if len(eqs) != 3 or good is None or len({good, *eqs}) != 4:
            continue
        stem = (f"If {legend_en}, which of the following equations is correct?")
        stem_hi = (f"यदि {legend_hi}, तो निम्नलिखित में से कौन-सा समीकरण सही है?")
        sol = (f"Only '{good}' holds once each printed symbol is replaced by the operation it "
               f"stands for and × and ÷ are done before + and −.")
        sol_hi = (f"प्रत्येक प्रतीक को उसके निर्दिष्ट संक्रिया से बदलने तथा × और ÷ को + व − से "
                  f"पहले हल करने पर केवल '{good}' सत्य है।")
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": good,
                "mistakes": mistakes(*[(w, e, h) for w, e, h in zip(whys, eqs, whys_hi)]),
                "concept": "Symbol Substitution"}
    return None


# ---- Word formation (शब्द रचना) -----------------------------------------------
#
# "From the given alternative words, select the word which cannot be formed using the letters of
# the given word : MISFORTUNE" — printed verbatim in the papers we hold, and purely mechanical: a
# word is formable iff its letter MULTISET fits inside the source's. So the answer is computed, not
# judged.
#
# The only hand-written data is the vocabulary, and it carries the one risk this project keeps
# meeting: a misspelling would make an option a non-word. Every entry is therefore checked against
# the system dictionary by `validate_wordlist()`, which the test harness runs — the words are not
# trusted because they were typed carefully.
#
# Words stay UPPERCASE. paper_common's Latin-inside-Hindi gate looks for a lower-case run of three
# or more letters between Devanagari, so an upper-case English word inside a Hindi stem passes,
# which is also exactly how the commission prints these.

_WF_SOURCES = [
    "MISFORTUNE", "DEPARTMENT", "ACHIEVEMENT", "CONSTITUTION", "INTERNATIONAL",
    "PHOTOGRAPHER", "ADMINISTRATION", "TRANSPORTATION", "DETERMINATION", "ENVIRONMENTAL",
    "COMMUNICATION", "DEVELOPMENT", "GOVERNMENT", "INDEPENDENCE", "AGRICULTURE",
    "TEMPERATURE", "ELECTRICITY", "INFORMATION", "MOUNTAINEER", "PARLIAMENT",
    "DEMOCRATIC", "MATHEMATICS", "INDUSTRIAL", "POPULATION", "CELEBRATION",
    "EXAMINATION", "PHILOSOPHER", "RESTAURANT", "UNIVERSITY", "WATERMELON",
    "NEWSPAPER", "LABORATORY", "MICROSCOPE", "TELEVISION", "STRANGULATION",
    "REVOLUTION", "PUNISHMENT", "MANAGEMENT", "COMPARISON", "NATIONALIST",
]

_WF_WORDS = [
    "ABLE", "ACID", "ACTOR", "AGENT", "ALERT", "ALTER", "AMEND", "ANGEL", "ANGER", "ANGLE",
    "ANIMAL", "APRON", "ARENA", "ARISE", "AROUND", "AROMA", "ARROW", "ASIDE", "ATOM", "AUNT",
    "BAND", "BARN", "BEAM", "BEAR", "BOAST", "BOAT", "BONE", "BRAIN", "BRAND", "BREAD",
    "BROOM", "CAMEL", "CANE", "CARE", "CART", "CAUSE", "CHAIN", "CHAIR", "CHARM", "CHEAT",
    "CITE", "CLAIM", "CLEAN", "CLOUD", "COAST", "COIN", "COMET", "CORAL", "COURT", "CRANE",
    "CREAM", "CRIME", "CROWN", "CURE", "DAIRY", "DANCE", "DARE", "DEAL", "DEAR", "DEBATE",
    "DEPTH", "DINE", "DIRT", "DOCTOR", "DONATE", "DRAIN", "DREAM", "DRESS", "DRIVE", "EARN",
    "EARTH", "ENTER", "ERASE", "EVENT", "FAIR", "FARM", "FEAST", "FIELD", "FIRM", "FLOAT",
    "FORT", "FRAME", "FRUIT", "GAIN", "GATE", "GIANT", "GLASS", "GRACE", "GRAIN", "GRAND",
    "GRAPE", "GRASS", "GREAT", "GUARD", "HAND", "HEAP", "HEART", "HORSE", "HOTEL", "HOUSE",
    "HUNT", "IDEA", "IRON", "ISLE", "ITEM", "LABOUR", "LANE", "LARGE", "LATER", "LEARN",
    "LEAST", "LEMON", "LIGHT", "LION", "LIVE", "LOCATE", "MAIN", "MANOR", "MARCH", "MASTER",
    "MATE", "MEAN", "MEAT", "MEDAL", "MELON", "MENTAL", "METAL", "METER", "MINE", "MINOR",
    "MODEL", "MOON", "MORAL", "MOTOR", "MOUNT", "MOUSE", "NAME", "NATION", "NEAR", "NEAT",
    "NOISE", "NORTH", "NOTE", "OCEAN", "ONION", "ORAL", "ORDER", "ORGAN", "OTTER", "PAINT",
    "PANEL", "PAPER", "PARENT", "PARK", "PARTY", "PASTE", "PATIENT", "PEACE", "PEARL", "PILOT",
    "PLACE", "PLAIN", "PLANE", "PLANT", "PLATE", "POINT", "POLICE", "PORT", "POSTER", "PRICE",
    "PRIDE", "PRINT", "PRIZE", "PROTEIN", "RADIO", "RAIN", "RATIO", "REACT", "READ", "REASON",
    "RENT", "RIVER", "ROAD", "ROAM", "ROAST", "ROUND", "ROUTE", "SAINT", "SALT", "SAND",
    "SCENE", "SEAT", "SENATE", "SHARE", "SHORE", "SHORT", "SILENT", "SLATE", "SMART", "SNAKE",
    "SOFT", "SOLAR", "SOUND", "SPACE", "SPEAR", "SPORT", "STAGE", "STAIN", "STAR", "START",
    "STEAM", "STONE", "STORE", "STORM", "STREAM", "SUGAR", "SWEAT", "TABLE", "TAILOR", "TEAM",
    "TEMPLE", "TENANT", "TENT", "TERM", "THREAD", "TIGER", "TIME", "TIRE", "TONE", "TOUR",
    "TOWER", "TRACE", "TRACK", "TRADE", "TRAIN", "TRAP", "TREAT", "TREND", "TRIAL", "TRIBE",
    "TRUST", "TURN", "UNIT", "UNITE", "URBAN", "VALUE", "VOICE", "VOTER", "WATER", "WHEAT",
]


def validate_wordlist(dict_path="/usr/share/dict/words"):
    """Every source and option word must be a real dictionary word. Returns the offenders.

    Not called at runtime — the paper must build on a machine with no dictionary. It is called by
    the test harness, which is the point: the list is checked rather than trusted, the same way
    the Constitution tables were gated against the official PDF before a single new row was kept.
    """
    import os
    if not os.path.exists(dict_path):
        return None                                  # cannot check here; harness reports that
    with open(dict_path, encoding="utf-8", errors="ignore") as fh:
        known = {w.strip().upper() for w in fh}
    return [w for w in _WF_SOURCES + _WF_WORDS if w not in known]


def _wf_status(src, w):
    """'ok' | 'count' (every letter present but not often enough) | 'missing' (a letter absent)."""
    from collections import Counter
    wc = Counter(w)
    if any(c not in src for c in wc):
        return "missing"
    if any(wc[c] > src[c] for c in wc):
        return "count"
    return "ok"


def _b_word_formation(rng, diff):
    """Word formation. Difficulty = the direction of the question and HOW the wrong words fail.

    diff 1  which CAN be formed    : the three others each need a letter the source does not have
    diff 2  which CANNOT be formed : the odd one needs a letter the source does not have
    diff 3  which CANNOT be formed : the odd one uses every letter, but needs one of them MORE
                                     times than the source has it — invisible unless counted
    diff 4+ which CAN be formed    : all three wrong ones fail on letter COUNT alone
    """
    from collections import Counter
    want_can = diff <= 1 or diff >= 4
    fail_mode = "missing" if diff <= 2 else "count"
    for _ in range(60):
        source = rng.choice(_WF_SOURCES)
        src = Counter(source)
        pool = {"ok": [], "count": [], "missing": []}
        for w in _WF_WORDS:
            if w == source:
                continue
            pool[_wf_status(src, w)].append(w)
        n_ok = 1 if want_can else 3
        n_bad = 4 - n_ok
        if len(pool["ok"]) < n_ok or len(pool[fail_mode]) < n_bad:
            continue
        oks = rng.sample(pool["ok"], n_ok)
        bads = rng.sample(pool[fail_mode], n_bad)
        opts = oks + bads
        if len(set(opts)) != 4:
            continue
        rng.shuffle(opts)
        ans = oks[0] if want_can else bads[0]
        ask_en = ("select the word which can be formed using the letters of the given word"
                  if want_can else
                  "select the word which cannot be formed using the letters of the given word")
        ask_hi = ("उस शब्द को चुनिए जो दिए गए शब्द के अक्षरों से बनाया जा सकता है"
                  if want_can else
                  "उस शब्द को चुनिए जो दिए गए शब्द के अक्षरों से नहीं बनाया जा सकता")
        stem = f"From the given alternative words, {ask_en} : {source}"
        stem_hi = f"दिए गए वैकल्पिक शब्दों में से {ask_hi} : {source}"
        def _bad_letter(w):
            return next((c for c in Counter(w)
                         if c not in src or Counter(w)[c] > src.get(c, 0)), None)

        def why(w):
            bad = _bad_letter(w)
            if bad is None:
                return f"{w} can be formed"
            return (f"{w} cannot — {source} has no '{bad}'" if bad not in src else
                    f"{w} cannot — it needs {Counter(w)[bad]} '{bad}'s and {source} has "
                    f"{src[bad]}")

        def why_hi(w):
            bad = _bad_letter(w)
            if bad is None:
                return f"{w} बनाया जा सकता है"
            return (f"{w} नहीं — {source} में '{bad}' अक्षर है ही नहीं" if bad not in src else
                    f"{w} नहीं — इसके लिए {Counter(w)[bad]} '{bad}' चाहिए जबकि {source} में "
                    f"{src[bad]} है")
        sol = "; ".join(why(w) for w in opts) + f". So the answer is {ans}."
        bad_letter = None
        if _wf_status(src, ans) != "ok":
            bad_letter = next(c for c in Counter(ans)
                              if c not in src or Counter(ans)[c] > src.get(c, 0))
        sol_hi = (f"{source} के अक्षरों से {ans} नहीं बनाया जा सकता, क्योंकि इसमें "
                  f"'{bad_letter}' अक्षर पर्याप्त नहीं है।" if bad_letter else
                  f"{source} के अक्षरों से केवल {ans} बनाया जा सकता है; शेष तीनों शब्दों के लिए "
                  f"आवश्यक अक्षर {source} में नहीं हैं।")
        # Each wrong option IS a named mistake: it is the word a candidate picks by checking only
        # that the letters "look like" they are there instead of counting them.
        # Offer MORE named mistakes than there are slots, so order_mistakes has a real choice:
        # at the hard end it can pick the near-misses (a word failing on one letter's COUNT) and
        # at the easy end the ones missing a letter outright. Every extra is still a real word
        # with a computed, named reason — never a nudge.
        # The spares must be the same KIND of option as the distractors they may replace, or the
        # question gains a second correct answer. Measured when this was wrong: on a "which CANNOT
        # be formed" item the distractors are the formable words, and drawing spares from the
        # other failure pool put a second NON-formable word on the page — 54 ambiguous items,
        # found by the harness rather than by reading the code.
        spare_src = pool[fail_mode] if want_can else pool["ok"]
        spare = [w for w in spare_src if w not in opts][:3]
        d = mistakes(*[(why(w), w, why_hi(w)) for w in opts if w != ans],
                     *[(why(w), w, why_hi(w)) for w in spare])
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": ans, "mistakes": d, "concept": "Word Formation"}
    return None


# ---- Number grid / matrix (संख्या-क्रम) ---------------------------------------
#
# The last of the families the real papers use and we could not generate. Three appear in the
# extracted bank, and working them out by hand is what fixed the rule families below:
#
#     1 2 3 / 4 5 6 / 7 8 9 / 27 38 ?      column (a,b,c) -> b*c - a      4*7-1 = 27   ans 51
#     3 4 5 / 2 3 4 / 1 2 3 / 14 29 ?      column -> a² + b² + c²         9+4+1 = 14   ans 50
#     6 9 12 / 36 81 144 / 216 729 ?       column -> (n, n², n³)          6*36  = 216  ans 1728
#
# so there are two SHAPES: three input rows feeding a result row, and three rows where each is
# built from the ones above. Both are here.
#
# 🔴 The hazard specific to this type is AMBIGUITY, not arithmetic. A grid can satisfy two
# different rules by coincidence — (1,2,3) sums to 6 and multiplies to 6 — and then a candidate who
# spots the other rule is marked wrong for a correct inference. So a grid is only accepted if every
# rule in the family that fits the SHOWN columns agrees on the missing one. Same defect the analogy
# and odd-one-out gates exist for, and the same fix.
#
# The grid is printed as labelled rows rather than aligned columns: HTML collapses runs of spaces,
# so the column alignment the original booklet relied on cannot survive the page.

_GRID_RULES = {
    "sum":     ("the three numbers in each column are added", lambda a, b, c: a + b + c),
    "ab_c":    ("the first two are multiplied and the third added", lambda a, b, c: a * b + c),
    "ab_mc":   ("the first two are multiplied and the third subtracted", lambda a, b, c: a * b - c),
    "bc_a":    ("the last two are multiplied and the first subtracted", lambda a, b, c: b * c - a),
    "bc_pa":   ("the last two are multiplied and the first added", lambda a, b, c: b * c + a),
    "ac_b":    ("the first and third are multiplied and the second subtracted",
                lambda a, b, c: a * c - b),
    "squares": ("the squares of the three numbers are added",
                lambda a, b, c: a * a + b * b + c * c),
    "ab_x_c":  ("the first two are added and the sum multiplied by the third",
                lambda a, b, c: (a + b) * c),
    "ac_x_b":  ("the first and third are added and the sum multiplied by the second",
                lambda a, b, c: (a + c) * b),
    "abc":     ("the three numbers are multiplied", lambda a, b, c: a * b * c),
}
_GRID_HI = {
    "sum": "प्रत्येक स्तम्भ की तीनों संख्याओं को जोड़ा गया है",
    "ab_c": "पहली दो संख्याओं का गुणनफल करके तीसरी जोड़ी गई है",
    "ab_mc": "पहली दो संख्याओं का गुणनफल करके तीसरी घटाई गई है",
    "bc_a": "अंतिम दो संख्याओं का गुणनफल करके पहली घटाई गई है",
    "bc_pa": "अंतिम दो संख्याओं का गुणनफल करके पहली जोड़ी गई है",
    "ac_b": "पहली और तीसरी का गुणनफल करके दूसरी घटाई गई है",
    "squares": "तीनों संख्याओं के वर्गों को जोड़ा गया है",
    "ab_x_c": "पहली दो का योग तीसरी से गुणा किया गया है",
    "ac_x_b": "पहली और तीसरी का योग दूसरी से गुणा किया गया है",
    "abc": "तीनों संख्याओं का गुणनफल किया गया है",
}
_GRID_BANDS = {1: ["sum"], 2: ["ab_c", "ab_mc", "bc_a", "bc_pa", "ac_b"], 3: ["squares"]}


def _grid_rows(cols, hi=False):
    """Label the rows rather than aligning columns — HTML eats the spacing that a printed booklet
    uses to make a grid a grid."""
    lab = "पंक्ति" if hi else "Row"
    n_rows = len(cols[0])
    return "\n".join(f"{lab} {r + 1}: " + ", ".join(str(c[r]) for c in cols)
                     for r in range(n_rows))


def _b_number_grid(rng, diff):
    """Number grid. Difficulty = the rule joining each column, and at the top end the SHAPE.

    diff 1  the column is added
    diff 2  two of the three are multiplied and the other added or subtracted
    diff 3  the squares are added — the step most candidates never try
    diff 4+ a different grid entirely: each row is built from the rows above it (n, n², n³)
    """
    if diff >= 4:
        return _b_number_grid_powers(rng, diff)
    kind = rng.choice(_GRID_BANDS[min(diff, 3)])
    _, fn = _GRID_RULES[kind]
    for _ in range(80):
        cols = [[rng.randint(1, 12) for _ in range(3)] for _ in range(3)]
        res = [fn(*c) for c in cols]
        if len(set(res)) != 3 or any(v <= 0 or v > 9999 for v in res):
            continue
        # AMBIGUITY GATE: any other rule that also explains the two shown columns must reach the
        # same missing number, or a candidate reasoning by that rule is punished for being right.
        rival = [g(*cols[2]) for k, (_, g) in _GRID_RULES.items()
                 if k != kind and all(g(*cols[i]) == res[i] for i in (0, 1))]
        if any(v != res[2] for v in rival):
            continue
        a, b, c = cols[2]
        shown = [[*cols[0]], [*cols[1]], [*cols[2]]]
        grid = _grid_rows(shown) + "\n" + "Row 4: " + \
            f"{res[0]}, {res[1]}, ?"
        grid_hi = _grid_rows(shown, hi=True) + "\n" + "पंक्ति 4: " + \
            f"{res[0]}, {res[1]}, ?"
        stem = ("Study the following number arrangement and find the number that should replace "
                "the question mark:\n" + grid +
                "\nIn each column, the numbers in the first three rows combine by the same rule "
                "to give the number in Row 4.")
        stem_hi = ("निम्नलिखित संख्या-क्रम का अध्ययन कीजिए तथा प्रश्नवाचक चिह्न के स्थान पर आने "
                   "वाली संख्या ज्ञात कीजिए:\n" + grid_hi +
                   "\nप्रत्येक स्तम्भ में पहली तीन पंक्तियों की संख्याएँ एक ही नियम से मिलकर "
                   "पंक्ति 4 की संख्या देती हैं।")
        sol = (f"In every column {_GRID_RULES[kind][0]} — "
               f"column 1 gives {res[0]} and column 2 gives {res[1]}. "
               f"Applying it to {a}, {b} and {c} gives {res[2]}.")
        sol_hi = (f"प्रत्येक स्तम्भ में {_GRID_HI[kind]} — पहला स्तम्भ {res[0]} तथा दूसरा "
                  f"{res[1]} देता है। उसी नियम से {a}, {b}, {c} से {res[2]} प्राप्त होता है।")
        row3 = cols[0][2], cols[1][2], cols[2][2]
        cand = [("added the three numbers instead of applying the rule the other columns follow",
                 a + b + c,
                 "अन्य स्तम्भों वाले नियम के बजाय तीनों संख्याओं को जोड़ दिया"),
                ("multiplied the three numbers", a * b * c,
                 "तीनों संख्याओं का गुणनफल कर दिया"),
                ("applied the rule ACROSS the bottom row instead of DOWN the column", fn(*row3),
                 "नियम को स्तम्भ में नीचे की ओर लगाने के बजाय पंक्ति में आड़ा लगा दिया"),
                ("added the squares instead", a * a + b * b + c * c,
                 "इसके स्थान पर तीनों संख्याओं के वर्ग जोड़ दिए")]
        seen, d = set(), []
        for why, v, wh in cand:
            if v == res[2] or v in seen or v <= 0:
                continue
            seen.add(v)
            d.append((why, str(v), wh))
        if len(d) < 3:
            continue
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": str(res[2]), "mistakes": mistakes(*d), "concept": "Number Grid"}
    return None


def _b_number_grid_powers(rng, diff):
    """The other real shape: each row is built from the rows above it, and the ? is in the grid.

    Verified against the paper's own example — 6/9/12, 36/81/144, 216/729/? is (n, n², n³), and
    n³ is also 'the two numbers above it multiplied', which is how a candidate actually reads it.
    """
    for _ in range(60):
        tops = rng.sample(range(3, 15), 3)
        geometric = rng.random() < 0.5
        k = rng.choice([2, 3, 4])
        if geometric:
            cols = [[n, k * n, k * k * n] for n in tops]
            desc = f"each number is {k} times the one above it"
            desc_hi = f"प्रत्येक संख्या अपने ऊपर वाली संख्या की {k} गुनी है"
        else:
            cols = [[n, n * n, n * n * n] for n in tops]
            desc = ("the second row is the square of the first and the third is its cube — "
                    "equivalently, each bottom number is the product of the two above it")
            desc_hi = ("दूसरी पंक्ति पहली का वर्ग है तथा तीसरी उसका घन — अर्थात् नीचे की संख्या "
                       "अपने ऊपर की दोनों संख्याओं का गुणनफल है")
        ans = cols[2][2]
        if ans > 99999 or len({c[2] for c in cols}) != 3:
            continue
        # Same ambiguity gate: the two shown columns must not be explained by a second rule that
        # disagrees about the third. v1*v2, v2²/v1 and 2*v2−v1 are the readings a candidate has.
        def rivals(col):
            v1, v2 = col[0], col[1]
            out = {v1 * v2, 2 * v2 - v1}
            if v1 and v2 * v2 % v1 == 0:
                out.add(v2 * v2 // v1)
            return out
        fits = {r for r in rivals(cols[0]) if r == cols[0][2]}
        consistent = [r for r in ("prod", "geom", "arith")
                      if all({"prod": c[0] * c[1],
                              "geom": (c[1] * c[1] // c[0]) if c[0] and c[1] * c[1] % c[0] == 0
                                      else None,
                              "arith": 2 * c[1] - c[0]}[r] == c[2] for c in cols[:2])]
        answers = {{"prod": cols[2][0] * cols[2][1],
                    "geom": (cols[2][1] ** 2 // cols[2][0]),
                    "arith": 2 * cols[2][1] - cols[2][0]}[r] for r in consistent}
        if len(answers) > 1:
            continue
        _ = fits
        shown = [[*cols[0]], [*cols[1]], [cols[2][0], cols[2][1], "?"]]
        stem = ("Study the following number arrangement and find the number that should replace "
                "the question mark:\n" + _grid_rows(shown) +
                "\nIn each column, every row is obtained from the rows above it by the same rule.")
        stem_hi = ("निम्नलिखित संख्या-क्रम का अध्ययन कीजिए तथा प्रश्नवाचक चिह्न के स्थान पर आने "
                   "वाली संख्या ज्ञात कीजिए:\n" + _grid_rows(shown, hi=True) +
                   "\nप्रत्येक स्तम्भ में हर पंक्ति अपने ऊपर वाली पंक्तियों से एक ही नियम द्वारा "
                   "प्राप्त होती है।")
        v1, v2 = cols[2][0], cols[2][1]
        sol = f"In every column {desc}. So the missing number is {ans}."
        sol_hi = f"प्रत्येक स्तम्भ में {desc_hi}। अतः लुप्त संख्या {ans} है।"
        cand = [("added the two numbers above it instead of combining them by the rule", v1 + v2,
                 "नियम से जोड़ने के बजाय ऊपर की दोनों संख्याओं को जोड़ दिया"),
                ("doubled the number directly above it", 2 * v2,
                 "ठीक ऊपर वाली संख्या को दुगुना कर दिया"),
                ("continued the column by adding the same difference again", v2 + (v2 - v1),
                 "स्तम्भ को वही अंतर पुनः जोड़कर आगे बढ़ा दिया"),
                ("squared the number above it", v2 * v2,
                 "ऊपर वाली संख्या का वर्ग कर दिया")]
        seen, d = set(), []
        for why, v, wh in cand:
            if v == ans or v in seen or v <= 0 or v > 999999:
                continue
            seen.add(v)
            d.append((why, str(v), wh))
        if len(d) < 3:
            continue
        return {"stem": stem, "stem_hi": stem_hi, "solution": sol, "solution_hi": sol_hi,
                "correct": str(ans), "mistakes": mistakes(*d), "concept": "Number Grid"}
    return None


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
    # खंड (ग) strands the seven chapters above do not reach — see the block comment there.
    "Syllogism": [_b_syllogism],
    "Seating Arrangement": [_b_seating],
    "Coded Inequality": [_b_coded_inequality],
    "Calendar": [_b_calendar],
    "Dice": [_b_dice],
    # Both of these are printed VERBATIM in the papers we extracted and we could not generate
    # either — found by classifying the 60 real reasoning questions rather than by guessing.
    "Symbol Substitution": [_b_symbol_substitution],
    "Word Formation": [_b_word_formation],
    "Number Grid": [_b_number_grid],
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
