#!/usr/bin/env python3
"""
gen_qbank_g3.py — book-faithful ICSE Grade-3 Maths question ROWS for the live qbank pool.

Grounded on *New Guided Mathematics — Class 3* (Children's Academy, Thane West).
Covers the book's Chapter 1 (Numbers) and Chapter 2 (Addition) EXACTLY as scoped in
his book: numbers up to 5 digits (Ten-Thousands), successor/predecessor, expanded form,
number names, forming greatest/smallest; 3-digit addition (±carry), three 3-digit
addends, additive properties, money (Rupees), estimating sums, and word problems.

Every question is COMPUTE-the-answer (correct by construction) => generated=1, verified=1.
Rows drop straight into `/pool` (exam="ICSE Class 3", subject="Mathematics") — no LLM,
no embeddings needed to serve (pool_questions is a plain SQL filter).

Chapters mirror the book's Ch1/Ch2 subtopics, folded onto the EXISTING live tiles so
nothing the child already sees is renamed or removed:
    Numbers & Place Value | Comparing Numbers | Skip Counting | Number Patterns | Addition

Usage (run ON the Gurukul VM where the qbank package + qbank.sqlite live):
    python3 gen_qbank_g3.py --dry                 # print samples + counts, NO db write
    python3 gen_qbank_g3.py --commit              # upsert into the live qbank.sqlite
    python3 gen_qbank_g3.py --commit --per 40     # rows-per-subtopic target
"""
import argparse, hashlib, random, sys, json

try:
    from qbank.models import Question, content_hash
    from qbank.storage import Store
    HAVE_QBANK = True
except Exception:                     # allow --dry on a box without the package
    HAVE_QBANK = False
    def content_hash(s):
        import re
        t = re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
        return hashlib.sha1(t.encode()).hexdigest()[:16]

EXAM = "ICSE Class 3"
SUBJECT = "Mathematics"
SOURCE = "New Guided Mathematics Class 3"

_ONES = ["zero","one","two","three","four","five","six","seven","eight","nine","ten",
         "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen",
         "eighteen","nineteen"]
_TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]

def _two(n):
    if n < 20: return _ONES[n]
    t, o = divmod(n, 10)
    return _TENS[t] + ("-" + _ONES[o] if o else "")

def _three(n):
    h, rest = divmod(n, 100)
    parts = []
    if h: parts.append(_ONES[h] + " hundred")
    if rest: parts.append(_two(rest))
    return " ".join(parts)

def number_name(n):
    """British/Indian primary-school number name for 0..99999 (as taught in the book)."""
    if n == 0: return "zero"
    th, rest = divmod(n, 1000)
    parts = []
    if th: parts.append(_three(th) + " thousand")
    if rest: parts.append(_three(rest))
    name = " ".join(parts).strip()
    return name[0].upper() + name[1:]


def _mcq(stem, correct, distractors, rng):
    """4 options [{label,text}], correct rotated out of a fixed slot. Answer by construction."""
    opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))
    i = 0
    while len(opts) < 4:                       # pad with unique nudges if a distractor collided
        i += 1
        cand = str(correct) + " " * 0
        try:
            cand = str(int(str(correct).lstrip("₹")) + i * 7)
            if str(correct).startswith("₹"): cand = "₹" + cand
        except ValueError:
            cand = str(correct) + "?" * i
        if cand not in opts: opts.append(cand)
    opts = opts[:4]
    if str(correct) not in opts: opts[-1] = str(correct)
    rot = sum(map(ord, stem)) % 4
    opts = opts[rot:] + opts[:rot]
    labels = ["A","B","C","D"]
    options = [{"label": l, "text": t} for l, t in zip(labels, opts)]
    return options, labels[opts.index(str(correct))]


def _mk(chapter, concept, difficulty, stem, correct, distractors, solution, rng):
    stem = stem.strip()
    options, ans = _mcq(stem, correct, distractors, rng)
    qid = "gen_g3icse_" + hashlib.md5((chapter + "|" + stem).encode()).hexdigest()[:14]
    row = dict(id=qid, exam=EXAM, subject=SUBJECT, stem=stem, qtype="MCQ_single",
               options=options, correct_answer=ans, solution=solution, chapter=chapter,
               concept=concept, difficulty=difficulty, source=SOURCE, generated=True,
               verified=True, needs_figure=False, hash=content_hash(stem))
    return row

# ---------------------------------------------------------------- Ch1: Numbers
PLACE = [("ones",1),("tens",10),("hundreds",100),("thousands",1000),("ten thousands",10000)]

def g_place_value(rng):
    n = rng.randint(1000, 99999)
    idx = rng.randint(0, 4 if n >= 10000 else 3)
    name, mult = PLACE[idx]
    digit = (n // mult) % 10
    pv = digit * mult
    d = [pv + mult, pv - mult if pv >= mult else pv + 2*mult, digit if digit != pv else pv + mult]
    return _mk("Numbers & Place Value", "place value", 1,
               f"In {n}, what is the PLACE VALUE of the {name} digit?", pv,
               d, f"The {name} digit is {digit}, so its place value is {digit} × {mult} = {pv}.", rng)

def g_face_value(rng):
    n = rng.randint(1000, 99999)
    idx = rng.randint(0, 4 if n >= 10000 else 3)
    name, mult = PLACE[idx]
    digit = (n // mult) % 10
    return _mk("Numbers & Place Value", "face value", 1,
               f"In {n}, what is the FACE VALUE of the {name} digit?", digit,
               [digit * mult, (digit + 1) % 10, (digit + 2) % 10],
               f"Face value is the digit itself, irrespective of its place — it is {digit}.", rng)

def g_expanded(rng):
    five = rng.random() < 0.5
    tt = rng.randint(1, 9) if five else 0
    th, h, t, o = rng.randint(0,9), rng.randint(0,9), rng.randint(0,9), rng.randint(0,9)
    if not five and th == 0: th = rng.randint(1,9)
    n = tt*10000 + th*1000 + h*100 + t*10 + o
    parts = []
    if five: parts.append(f"{tt} ten thousand{'s' if tt>1 else ''}")
    parts += [f"{th} thousand{'s' if th!=1 else ''}", f"{h} hundred{'s' if h!=1 else ''}",
              f"{t} ten{'s' if t!=1 else ''}", f"{o} one{'s' if o!=1 else ''}"]
    expr = " + ".join(parts)
    return _mk("Numbers & Place Value", "expanded form", 1 if not five else 2,
               f"Write the number:  {expr}  =  ?", n,
               [n+10, n+100, n-1 if n%10 else n+1],
               f"Add each part: {expr} = {n}.", rng)

def g_number_name(rng):
    n = rng.randint(1001, 99999)
    name = number_name(n)
    d = [n + rng.choice([10,100,1000]), n - rng.choice([1,10,100]),
         n + rng.choice([-1000, 1, 900])]
    return _mk("Numbers & Place Value", "number names", 2,
               f"Which number is '{name}'?", n, d,
               f"'{name}' is written {n}.", rng)

def g_successor(rng):
    n = rng.randint(100, 99998)
    return _mk("Numbers & Place Value", "successor", 1,
               f"What is the SUCCESSOR of {n}?", n+1, [n-1, n+2, n+10],
               f"The successor comes just after — add 1: {n} + 1 = {n+1}.", rng)

def g_predecessor(rng):
    n = rng.randint(101, 99999)
    return _mk("Numbers & Place Value", "predecessor", 1,
               f"What is the PREDECESSOR of {n}?", n-1, [n+1, n-2, n-10],
               f"The predecessor comes just before — subtract 1: {n} − 1 = {n-1}.", rng)

def g_form_number(rng):
    k = rng.choice([3, 4])
    digits = rng.sample(range(1, 10), k)         # distinct, non-zero -> clean no-repeat forming
    biggest = rng.random() < 0.5
    target = int("".join(str(x) for x in sorted(digits, reverse=biggest)))
    other = int("".join(str(x) for x in sorted(digits, reverse=not biggest)))
    word = "GREATEST" if biggest else "SMALLEST"
    ds = ", ".join(str(x) for x in digits)
    return _mk("Numbers & Place Value", "forming numbers", 2,
               f"Write the {word} {k}-digit number using {ds} (no digit repeated).",
               target, [other, target + (10 if biggest else -10), other + 1],
               f"For the {word.lower()} number, order the digits "
               f"{'largest to smallest' if biggest else 'smallest to largest'}: {target}.", rng)

def g_compare_pair(rng):
    a, b = rng.randint(100, 99999), rng.randint(100, 99999)
    while a == b: b = rng.randint(100, 99999)
    sign = ">" if a > b else "<"
    return _mk("Comparing Numbers", "compare", 1,
               f"Fill in the correct sign:  {a}  ___  {b}", sign, ["<" if sign==">" else ">", "="],
               f"{a} is {'greater' if sign=='>' else 'smaller'} than {b}, so {a} {sign} {b}.", rng)

def g_order(rng):
    nums = rng.sample(range(1000, 99999), 4)
    asc = rng.random() < 0.5
    ans = min(nums) if asc else max(nums)
    word = "ASCENDING (smallest first)" if asc else "DESCENDING (greatest first)"
    listed = ", ".join(str(x) for x in nums)
    return _mk("Comparing Numbers", "ordering", 2,
               f"Arrange in {word} order: {listed}. Which number comes FIRST?",
               ans, [x for x in nums if x != ans][:3],
               f"In {word.split()[0].lower()} order the first is the "
               f"{'smallest' if asc else 'greatest'}: {ans}.", rng)

def g_skip(rng):
    step = rng.choice([10, 100, 1000])
    start = rng.randint(1, 9) * step + rng.randint(0, 9) * (1 if step > 10 else 0)
    seq = [start + step*i for i in range(3)]
    nxt = seq[-1] + step
    return _mk("Skip Counting", f"count in {step}s", 1,
               f"Count ahead in {step}s:  {seq[0]}, {seq[1]}, {seq[2]}, ?", nxt,
               [nxt+step, nxt-step, nxt+1],
               f"Keep adding {step}: {seq[-1]} + {step} = {nxt}.", rng)

def g_pattern(rng):
    step = rng.choice([2, 3, 4, 5, 8, 10])
    start = rng.randint(3, 99) * (10 if step in (8,) else 1) + rng.randint(0, 9)
    seq = [start + step*i for i in range(3)]
    nxt = seq[-1] + step
    return _mk("Number Patterns", "growing pattern", 1,
               f"Observe the pattern and find the next number:  {seq[0]}, {seq[1]}, {seq[2]}, ?",
               nxt, [nxt+1, nxt-1, nxt+step],
               f"Each number goes up by {step}: {seq[-1]} + {step} = {nxt}.", rng)

# --------------------------------------------------------------- Ch2: Addition
def g_add_nocarry(rng):
    # build two 3-digit numbers whose columns never exceed 9 (no carrying)
    h1,h2 = rng.randint(1,8), rng.randint(1,9-1)
    while h1+h2 > 9: h2 = rng.randint(1,9-h1)
    def col():
        x = rng.randint(0,9); y = rng.randint(0,9-x); return x,y
    (t1,t2),(o1,o2) = col(), col()
    a, b = h1*100+t1*10+o1, h2*100+t2*10+o2
    s = a+b
    return _mk("Addition", "3-digit no carry", 1,
               f"{a} + {b} = ?", s, [s+10, s-1, s+100],
               f"Add ones, tens, hundreds: {a} + {b} = {s}.", rng)

def g_add_carry(rng):
    a, b = rng.randint(150, 899), rng.randint(150, 899)
    s = a+b
    return _mk("Addition", "3-digit with carry", 2,
               f"{a} + {b} = ?  (carry over if needed)", s, [s+10, s-1, s-100, s+1],
               f"Add with carrying: {a} + {b} = {s}.", rng)

def g_add_three(rng):
    a, b, c = (rng.randint(120, 480) for _ in range(3))
    s = a+b+c
    return _mk("Addition", "three 3-digit numbers", 2,
               f"{a} + {b} + {c} = ?", s, [s+10, s-1, s+100],
               f"Add all three: {a} + {b} + {c} = {s}.", rng)

def g_add_mixed(rng):
    a, b, c = rng.randint(200, 700), rng.randint(11, 99), rng.randint(1, 9)
    s = a+b+c
    return _mk("Addition", "3-digit + 2-digit + 1-digit", 2,
               f"{a} + {b} + {c} = ?", s, [s+10, s-1, s+1],
               f"Line up the ones and add: {a} + {b} + {c} = {s}.", rng)

def g_add_property(rng):
    kind = rng.choice(["zero", "one", "sum"])
    if kind == "zero":
        n = rng.randint(20, 99)
        return _mk("Addition", "adding zero", 1,
                   f"{n} + ___ = {n}", 0, [1, n, 10],
                   f"Adding zero does not change a number, so the box is 0.", rng)
    if kind == "one":
        n = rng.randint(20, 98)
        return _mk("Addition", "successor by adding 1", 1,
                   f"___ + 1 = {n+1}", n, [n+1, n-1, n+2],
                   f"1 more makes {n+1}, so the box is {n}.", rng)
    a, b = rng.randint(11, 45), rng.randint(11, 45)
    return _mk("Addition", "2-digit sum", 1,
               f"{a} + {b} = ?", a+b, [a+b+10, a+b-1, a+b+1],
               f"{a} + {b} = {a+b}.", rng)

def g_add_money(rng):
    if rng.random() < 0.5:
        a, b = rng.randint(15, 85), rng.randint(10, 60)
    else:
        a, b = rng.randint(110, 480), rng.randint(110, 480)
    s = a+b
    return _mk("Addition", "adding money", 1 if s < 100 else 2,
               f"₹{a} + ₹{b} = ?", f"₹{s}", [f"₹{s+10}", f"₹{s-1}", f"₹{s+5}"],
               f"Add the rupees: ₹{a} + ₹{b} = ₹{s}.", rng)

def g_estimate(rng):
    a, b = rng.randint(11, 89), rng.randint(11, 89)
    ra, rb = round(a, -1), round(b, -1)
    est = ra + rb
    return _mk("Addition", "estimating sums", 2,
               f"Estimate the sum by rounding each number to the nearest 10:  {a} + {b}",
               est, [est+10, est-10, a+b],
               f"{a}→{ra}, {b}→{rb}. Estimated sum = {ra} + {rb} = {est}.", rng)

def g_add_word(rng):
    a, b = rng.randint(105, 480), rng.randint(105, 480)
    ctx = rng.choice([
        (f"{a} boys and {b} girls took part in Sports Day. How many children in all?", "children"),
        (f"A garden has {a} roses and {b} daisies. How many flowers altogether?", "flowers"),
        (f"A shop sold {a} toys on Monday and {b} toys on Tuesday. How many in all?", "toys"),
        (f"There are {a} mango trees and {b} apple trees. How many trees in all?", "trees"),
    ])
    q, _ = ctx
    s = a+b
    return _mk("Addition", "word problem", 2,
               q, s, [s+10, s-1, s+100],
               f"Add the two amounts: {a} + {b} = {s}.", rng)

# --------------------------------------------------------------- Ch3: Subtraction
def g_sub_noborrow(rng):
    h = rng.randint(2, 9); t = rng.randint(0, 9); o = rng.randint(0, 9)
    a = h*100 + t*10 + o
    b = rng.randint(1, h)*100 + rng.randint(0, t)*10 + rng.randint(0, o)   # each column <= a's -> no borrow
    d = a - b
    return _mk("Subtraction", "3-digit no borrow", 1,
               f"{a} − {b} = ?", d, [d+10, d-1, d+100, d+1],
               f"Subtract ones, tens, hundreds: {a} − {b} = {d}.", rng)

def g_sub_borrow(rng):
    a = rng.randint(210, 998); b = rng.randint(120, a-1)
    d = a - b
    return _mk("Subtraction", "3-digit with borrow", 2,
               f"{a} − {b} = ?  (borrow if needed)", d, [d+10, d-1, d+100, d-10],
               f"Subtract with borrowing: {a} − {b} = {d}.", rng)

def g_sub_estimate(rng):
    a = rng.randint(31, 98); b = rng.randint(11, a-5)
    est = (a // 10) * 10 - (b // 10) * 10          # book method: subtract the tens (floor to tens)
    return _mk("Subtraction", "estimating differences", 2,
               f"Estimate the difference by taking the tens:  {a} − {b}", est,
               [est+10, est-10, a-b],
               f"{a}→{(a//10)*10}, {b}→{(b//10)*10}. Estimated difference = "
               f"{(a//10)*10} − {(b//10)*10} = {est}.", rng)

def g_sub_addsub(rng):
    a = rng.randint(200, 500); b = rng.randint(120, 400); c = rng.randint(100, a + b - 50)
    d = a + b - c
    return _mk("Subtraction", "add and subtract together", 2,
               f"{a} + {b} − {c} = ?", d, [d+10, d-1, d+100],
               f"First add: {a} + {b} = {a+b}. Then subtract: {a+b} − {c} = {d}.", rng)

def g_sub_money(rng):
    if rng.random() < 0.5:
        a, b = rng.randint(25, 99), rng.randint(10, 24)
    else:
        a, b = rng.randint(200, 800), rng.randint(105, 199)
    while b >= a:
        b = rng.randint(10, a-1)
    d = a - b
    return _mk("Subtraction", "subtracting money", 1 if a < 100 else 2,
               f"₹{a} − ₹{b} = ?", f"₹{d}", [f"₹{d+10}", f"₹{d-1}", f"₹{d+5}"],
               f"Subtract the rupees: ₹{a} − ₹{b} = ₹{d}.", rng)

def g_sub_property(rng):
    kind = rng.choice(["zero", "self", "one"])
    n = rng.randint(20, 99)
    if kind == "zero":
        return _mk("Subtraction", "subtracting zero", 1,
                   f"{n} − 0 = ?", n, [0, n-1, n+1],
                   f"Taking away zero changes nothing, so {n} − 0 = {n}.", rng)
    if kind == "self":
        return _mk("Subtraction", "subtract a number from itself", 1,
                   f"{n} − {n} = ?", 0, [n, 1, n-1],
                   f"Any number minus itself is 0, so {n} − {n} = 0.", rng)
    return _mk("Subtraction", "one less", 1,
               f"{n} − 1 = ?", n-1, [n, n+1, n-2],
               f"One less than {n} is {n-1}.", rng)

def g_sub_word(rng):
    a = rng.randint(210, 800); b = rng.randint(105, a-20)
    d = a - b
    q = rng.choice([
        f"There were {a} apples on a tree. {b} fell down. How many are still on the tree?",
        f"A seller had {a} mangoes and sold {b}. How many are left?",
        f"There were {a} people at the stadium. {b} went home. How many are left?",
        f"A shop had {a} candles and {b} were used. How many candles are left?",
    ])
    return _mk("Subtraction", "word problem", 2,
               q, d, [d+10, d-1, d+100],
               f"Take away what is gone: {a} − {b} = {d}.", rng)

# ----------------------------------------------------------------- registry
BUILDERS = {
    "Numbers & Place Value": [g_place_value, g_face_value, g_expanded, g_number_name,
                              g_successor, g_predecessor, g_form_number],
    "Comparing Numbers": [g_compare_pair, g_order],
    "Skip Counting": [g_skip],
    "Number Patterns": [g_pattern],
    "Addition": [g_add_nocarry, g_add_carry, g_add_three, g_add_mixed, g_add_property,
                 g_add_money, g_estimate, g_add_word],
    "Subtraction": [g_sub_noborrow, g_sub_borrow, g_sub_estimate, g_sub_addsub,
                    g_sub_money, g_sub_property, g_sub_word],
}

def generate(per_subtopic, seed, existing_hashes):
    rng = random.Random(seed)
    rows, seen = [], set(existing_hashes or set())
    for chapter, gens in BUILDERS.items():
        for g in gens:
            made, tries = 0, 0
            while made < per_subtopic and tries < per_subtopic * 60:
                tries += 1
                row = g(rng)
                if row["hash"] in seen:
                    continue
                seen.add(row["hash"]); rows.append(row); made += 1
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=12, help="target NEW questions per subtopic")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--dry", action="store_true", help="print samples + counts, no DB write")
    ap.add_argument("--commit", action="store_true", help="upsert into the live qbank.sqlite")
    ap.add_argument("--db", default=None, help="override qbank.sqlite path")
    a = ap.parse_args()

    existing = {}
    store = None
    if HAVE_QBANK and (a.commit or not a.dry):
        store = Store(a.db)
        existing = set(store.existing_hashes().keys())

    rows = generate(a.per, a.seed, existing)

    from collections import Counter
    by_ch = Counter(r["chapter"] for r in rows)
    by_diff = Counter((r["chapter"], r["difficulty"]) for r in rows)
    print(f"# generated {len(rows)} NEW rows (deduped vs {len(existing)} existing hashes)")
    for ch, n in by_ch.items():
        d1 = by_diff.get((ch,1),0); d2 = by_diff.get((ch,2),0)
        print(f"  {ch:<26} {n:>3}  (d1={d1}, d2={d2})")

    if a.dry or not a.commit:
        print("\n# ---- 8 SAMPLES ----")
        for r in random.Random(1).sample(rows, min(8, len(rows))):
            corr = next(o["text"] for o in r["options"] if o["label"] == r["correct_answer"])
            print(f"[{r['chapter']} d{r['difficulty']}] {r['stem']}")
            print(f"    options: {[o['text'] for o in r['options']]}  -> {r['correct_answer']} ({corr})")
            print(f"    {r['solution']}")
        if not a.commit:
            print("\n(dry run — nothing written. Re-run with --commit to upsert.)")
        return

    if not HAVE_QBANK:
        sys.exit("!! qbank package not importable here; run --commit on the Gurukul VM.")
    n = 0
    for r in rows:
        q = Question(**r)
        store.upsert(q); n += 1
    print(f"\n# upserted {n} rows into the live qbank (generated=1, verified=1).")

if __name__ == "__main__":
    main()
