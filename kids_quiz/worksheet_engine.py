#!/usr/bin/env python3
"""
worksheet_engine.py — CURRICULUM-DRIVEN worksheet generator.

Pick ANY node (board / class / subject / chapter) and it generates a proper worksheet of
WORKSHEET_GRAMMAR archetypes that KidsWorksheet.render() (worksheet.js) draws:

  • Mathematics  → COMPUTED archetypes, ranges scaled by class (Class 1 small → Class 5 big).
  • EVS/English/GK/Hindi (knowledge) → LLM-GENERATED, grounded on the chapter/subtopic (litellm).

Reads the taxonomy the curriculum build produced: kids_quiz/curriculum/<board>_class<N>_<subject>.json.

  # Maths (computed, no endpoint needed):
  python3 worksheet_engine.py --board CBSE --class 2 --subject Mathematics --n 8 --out content/cbse_c2_maths.json
  # Knowledge (needs litellm at LITELLM_URL, e.g. via the EC2 tunnel):
  LITELLM_URL=http://localhost:4000/v1 python3 worksheet_engine.py --board CBSE --class 3 --subject EVS --n 6
"""
import json, os, argparse, random, re
import assessment_core as AC   # COMMON engine: difficulty radicals + misconception distractors + hints

BASE = os.path.dirname(os.path.abspath(__file__))
CURR = os.path.join(BASE, "curriculum")
COUNT_ASSETS = [("apple", "🍎"), ("star", "⭐"), ("fish", "🐟"), ("balloon", "🎈"),
                ("cookie", "🍪"), ("banana", "🍌"), ("grapes", "🍇"),
                # expanded countable props (art pooled via gpt-image; emoji is the fallback)
                ("ball", "⚽"), ("kite", "🪁"), ("flower", "🌸"), ("leaf", "🍃"), ("car", "🚗"),
                ("frog", "🐸"), ("duck", "🦆"), ("butterfly", "🦋"), ("pencil", "✏️"), ("book", "📚"),
                ("carrot", "🥕"), ("orange", "🍊"), ("rabbit", "🐰"), ("bee", "🐝")]
KNOWLEDGE = {"evs", "english", "generalknowledge", "gk", "general knowledge", "hindi"}

# ---------- class-scaled ranges ----------
RANGE = {
    "count": {1: (1, 10), 2: (1, 20), 3: (3, 12), 4: (5, 20), 5: (5, 25)},
    "add":   {1: (1, 10), 2: (10, 50), 3: (100, 500), 4: (1000, 5000), 5: (10000, 50000)},
    "sub":   {1: (2, 10), 2: (10, 60), 3: (50, 900), 4: (1000, 5000), 5: (10000, 50000)},
    "mulA":  {1: (2, 5), 2: (2, 9), 3: (2, 12), 4: (2, 20), 5: (2, 25)},
    "cmp":   {1: (1, 20), 2: (1, 100), 3: (10, 9999), 4: (1000, 99999), 5: (10000, 999999)},
    "nbr":   {1: (2, 19), 2: (10, 98), 3: (100, 998), 4: (1000, 9998), 5: (10000, 99998)},
}
def rr(r, cls, k): lo, hi = RANGE[k][max(1, min(5, cls))]; return r.randint(lo, hi)


def _item(t, instr, voice, payload, answer, explain, cls, chapter, subject):
    band = "1-2" if cls <= 2 else "3-5"
    return {"type": t, "subject": subject.lower(), "class": cls, "chapter": chapter, "band": band,
            "instruction": instr, "voice": voice, "payload": payload, "answer": answer, "explain": explain}


# ---------- Maths computed generators (class-scaled) ----------
_PLURAL = {"leaf": "leaves", "butterfly": "butterflies", "fish": "fish", "grapes": "grapes"}
def _plural(w):
    return _PLURAL.get(w, w + "s")

def g_count(r, cls, ch, subj):
    a, em = r.choice(COUNT_ASSETS); n = rr(r, cls, "count"); ap = _plural(a)
    return _item("count_write", f"Count the {ap} and write how many!", f"Count the {ap}.",
                 {"asset": a, "emoji": em, "n": n}, n, f"There are {n} {ap}!", cls, ch, subj)

def g_add(r, cls, ch, subj):
    a, b = rr(r, cls, "add"), rr(r, cls, "add"); return _item(
        "arith", f"Add it!  {a} + {b} = ?", f"What is {a} plus {b}?", {"op": "+", "a": a, "b": b},
        a + b, f"{a} plus {b} makes {a + b}.", cls, ch, subj)

def g_sub(r, cls, ch, subj):
    a = rr(r, cls, "sub"); b = r.randint(1, max(2, a - 1)); return _item(
        "arith", f"Subtract!  {a} − {b} = ?", f"What is {a} minus {b}?", {"op": "-", "a": a, "b": b},
        a - b, f"{a} minus {b} leaves {a - b}.", cls, ch, subj)

def g_mul(r, cls, ch, subj):
    a, b = rr(r, cls, "mulA"), r.randint(2, 9); return _item(
        "arith", f"Multiply!  {a} × {b} = ?", f"What is {a} times {b}?", {"op": "×", "a": a, "b": b},
        a * b, f"{a} times {b} makes {a * b}.", cls, ch, subj)

def g_compare(r, cls, ch, subj):
    a, b = rr(r, cls, "cmp"), rr(r, cls, "cmp")
    while a == b: b = rr(r, cls, "cmp")
    ans = "<" if a < b else ">"; return _item(
        "compare_symbol", "Put the right sign! 🐊", f"Compare {a} and {b}.", {"a": a, "b": b},
        ans, f"{a} is {'less' if ans == '<' else 'greater'} than {b}.", cls, ch, subj)

def g_neighbour(r, cls, ch, subj):
    mode = r.choice(["after", "before"]); n = rr(r, cls, "nbr"); ans = n + 1 if mode == "after" else n - 1
    disp = f"▢ , {n}" if mode == "after" else f"{n} , ▢"
    return _item("neighbour_number", f"What comes just {mode} {n}?", f"What is just {mode} {n}?",
                 {"mode": mode, "n": n, "display": disp}, ans, f"Just {mode} {n} is {ans}.", cls, ch, subj)

def g_seq(r, cls, ch, subj):
    step = r.choice([1, 2, 5, 10] if cls <= 2 else [2, 5, 10, 100]); start = r.randint(1, 5) * step
    seq = [start + i * step for i in range(4)]; hide = r.randint(1, 2)
    shown = [x if i != hide else None for i, x in enumerate(seq)]
    return _item("fill_sequence", "Fill in the missing number! 🚂", f"Skip count by {step}.",
                 {"seq": shown, "step": step}, [seq[hide]], f"Counting by {step}s → {seq[hide]}.", cls, ch, subj)

def g_money(r, cls, ch, subj):
    coins = r.choice([[1, 2, 5], [10, 5, 2], [10, 10, 5], [5, 2, 2, 1]]); tot = sum(coins)
    return _item("count_money", "How much money? 🪙", "Add the coins.",
                 {"coins": coins, "display": " + ".join(f"₹{c}" for c in coins)}, tot,
                 f"The coins make ₹{tot}.", cls, ch, subj)


# ---------- NEW computed strands: division / shapes / fractions / measurement / data ----------
# These fix the "silent addition under the wrong chapter" gap (Shapes/Fractions/Measurement/Division/Data
# used to fall back to number/add). All COMPUTED (no LLM), emitting only renderer-supported types.

def g_division(r, cls, ch, subj):
    """Exact division, class-scaled. The 'arith' renderer prints p.op, so ÷ shows correctly."""
    hi = 9 if cls <= 3 else 12
    b = r.randint(2, hi); c = r.randint(2, hi); a = b * c
    return _item("arith", f"Divide!  {a} ÷ {b} = ?", f"What is {a} divided by {b}?",
                 {"op": "÷", "a": a, "b": b}, c, f"{a} ÷ {b} = {c}.", cls, ch, subj)

# 2D polygons → number of sides (== corners for these); circle handled separately (no straight sides).
_SHAPE_SIDES = {"triangle": 3, "square": 4, "rectangle": 4, "pentagon": 5, "hexagon": 6}
_SHAPES_3D = ["cube", "sphere", "cylinder", "cone"]

def _num_bank(r, ans, lo=3, hi=6):
    pool = [x for x in range(lo, hi + 1) if x != ans]
    r.shuffle(pool)
    bank = [str(ans)] + [str(x) for x in pool[:2]]
    r.shuffle(bank)
    return bank

def g_shape(r, cls, ch, subj):
    mode = r.choice(["sides_cloze", "sides_tf", "match_sides", "odd_solid", "corners_cloze"])
    if mode == "match_sides":
        picks = r.sample(list(_SHAPE_SIDES), 4)
        pairs = [[s, str(_SHAPE_SIDES[s])] for s in picks]
        return _item("match_following", "Match each shape with its number of sides.",
                     "Match each shape with its number of sides.", {"pairs": pairs},
                     {s: str(_SHAPE_SIDES[s]) for s in picks}, "Great matching!", cls, ch, subj)
    if mode == "odd_solid":
        flats = r.sample(list(_SHAPE_SIDES), 3); solid = r.choice(_SHAPES_3D)
        opts = flats + [solid]; r.shuffle(opts)
        return _item("odd_one_out", "Which one is NOT a flat (2D) shape?",
                     "Which one is a solid shape?", {"options": opts}, solid,
                     f"A {solid} is a solid (3D) shape; the others are flat.", cls, ch, subj)
    sh = r.choice(list(_SHAPE_SIDES)); n = _SHAPE_SIDES[sh]
    if mode == "sides_cloze":
        return _item("cloze", f"A {sh} has ___ sides.", f"How many sides does a {sh} have?",
                     {"sentence": f"A {sh} has ___ sides.", "bank": _num_bank(r, n)}, str(n),
                     f"A {sh} has {n} sides.", cls, ch, subj)
    if mode == "corners_cloze":
        return _item("cloze", f"A {sh} has ___ corners.", f"How many corners does a {sh} have?",
                     {"sentence": f"A {sh} has ___ corners.", "bank": _num_bank(r, n)}, str(n),
                     f"A {sh} has {n} corners.", cls, ch, subj)
    # sides_tf
    true = r.random() < 0.5
    shown = n if true else r.choice([x for x in range(3, 7) if x != n])
    return _item("true_false", f"A {sh} has {shown} sides.", f"A {sh} has {shown} sides.",
                 {"statement": f"A {sh} has {shown} sides."}, bool(true),
                 f"A {sh} has {n} sides.", cls, ch, subj)

def g_fraction(r, cls, ch, subj):
    mode = r.choice(["half", "quarter", "compare"])
    if mode == "half":
        n = r.choice([2, 4, 6, 8, 10, 12, 14, 16, 20]); ans = n // 2
        return _item("cloze", f"Half of {n} is ___.", f"What is half of {n}?",
                     {"sentence": f"Half of {n} is ___.", "bank": _num_bank(r, ans, ans - 1, ans + 2)},
                     str(ans), f"Half of {n} is {ans}.", cls, ch, subj)
    if mode == "quarter":
        n = r.choice([4, 8, 12, 16, 20]); ans = n // 4
        return _item("cloze", f"A quarter of {n} is ___.", f"What is a quarter of {n}?",
                     {"sentence": f"A quarter of {n} is ___.", "bank": _num_bank(r, ans, max(1, ans - 1), ans + 2)},
                     str(ans), f"A quarter of {n} is {ans}.", cls, ch, subj)
    # compare unit fractions: smaller denominator = bigger fraction
    a, b = r.choice([(2, 4), (2, 3), (3, 4), (2, 6), (4, 8), (3, 6)])
    bigger = f"1/{a}"; other = f"1/{b}"
    bank = [bigger, other]; r.shuffle(bank)
    return _item("cloze", f"Which is bigger:  {bigger}  or  {other}?  ___",
                 f"Which is bigger, one over {a} or one over {b}?",
                 {"sentence": f"The bigger fraction is ___.", "bank": bank}, bigger,
                 f"{bigger} is bigger than {other} (fewer, larger pieces).", cls, ch, subj)

# measurement facts (universal conversions) — verified, correct by definition. Tagged by category
# so a "Length"/"Time"/"Weight" chapter serves on-topic facts (not a random unit).
_UNITS = [("hour", "minutes", 60, "time"), ("minute", "seconds", 60, "time"), ("day", "hours", 24, "time"),
          ("week", "days", 7, "time"), ("year", "months", 12, "time"), ("metre", "centimetres", 100, "length"),
          ("kilometre", "metres", 1000, "length"), ("kilogram", "grams", 1000, "weight"),
          ("litre", "millilitres", 1000, "capacity")]

def _measure_cats(ch):
    n = (ch or "").lower(); cats = set()
    if any(w in n for w in ("length", "metre", "meter", "distance")): cats |= {"length"}
    if any(w in n for w in ("weight", "lifting", "heavy", "mass", "kilogram")): cats |= {"weight"}
    if any(w in n for w in ("capacity", "filling", "volume", "litre", "liter")): cats |= {"capacity"}
    if any(w in n for w in ("time", "clock", "hour", "calendar")): cats |= {"time"}
    return cats or {"time", "length", "weight", "capacity"}   # generic "Measurement"

def g_measure(r, cls, ch, subj):
    cats = _measure_cats(ch)
    units = [u for u in _UNITS if u[3] in cats] or _UNITS
    a, b, v, _ = r.choice(units)
    same = [x for _, _, x, _ in units if x != v] or [x for _, _, x, _ in _UNITS if x != v]
    if r.random() < 0.5:   # cloze
        distract = sorted({str(x) for x in same}); r.shuffle(distract)
        bank = [str(v)] + distract[:2]; r.shuffle(bank)
        return _item("cloze", f"1 {a} = ___ {b}.", f"How many {b} are in one {a}?",
                     {"sentence": f"1 {a} = ___ {b}.", "bank": bank}, str(v),
                     f"1 {a} = {v} {b}.", cls, ch, subj)
    true = r.random() < 0.5
    shown = v if true else r.choice(same)
    return _item("true_false", f"1 {a} = {shown} {b}.", f"1 {a} = {shown} {b}.",
                 {"statement": f"1 {a} = {shown} {b}."}, bool(true), f"1 {a} = {v} {b}.", cls, ch, subj)

def g_data(r, cls, ch, subj):
    """Grade-3 data-handling stopgap: read simple counts and answer (contextual arithmetic).
    Full pictograph rendering is deferred; this is honest (it IS about reading quantities), not a plain drill."""
    items3 = r.sample([("🍎 apples", 3), ("🍌 bananas", 4), ("🍊 oranges", 5), ("🍇 grapes", 6), ("🍓 strawberries", 2)], 2)
    (n1lbl, n1), (n2lbl, n2) = items3
    if r.random() < 0.5:
        ans = n1 + n2
        instr = f"A basket has {n1} {n1lbl} and {n2} {n2lbl}. How many fruits in all?"
    else:
        hi_lbl, hi_n = (n1lbl, n1) if n1 >= n2 else (n2lbl, n2)
        lo_lbl, lo_n = (n2lbl, n2) if n1 >= n2 else (n1lbl, n1)
        ans = hi_n - lo_n
        instr = f"There are {hi_n} {hi_lbl} and {lo_n} {lo_lbl}. How many more {hi_lbl.split()[1]} than {lo_lbl.split()[1]}?"
    return _item("cloze", instr, instr, {"sentence": instr + "  ___", "bank": _num_bank(r, ans, max(0, ans - 2), ans + 3)},
                 str(ans), f"The answer is {ans}.", cls, ch, subj)

# concept → generator for the direct computed strands (bypass the style layer in generate())
DIRECT_MATHS = {"division": g_division, "shape": g_shape, "fraction": g_fraction,
                "measure": g_measure, "data": g_data}


# ---------- extra STYLE generators (one concept, different lens) ----------
STORY = [("apples", "basket"), ("stars", "box"), ("fish", "pond"), ("mangoes", "tree"),
         ("balloons", "bunch"), ("cookies", "jar"), ("pencils", "pack")]
NAMES = ["Rohan", "Meera", "Aditya", "Sara", "Aarav", "Diya"]

def g_story(r, cls, op, ch, subj):
    """Same arithmetic concept, real-life STORY lens (apply / DOK 2)."""
    thing, grp = r.choice(STORY)
    if op == "+":
        a, b = rr(r, cls, "add"), rr(r, cls, "add"); ans = a + b
        instr = f"{r.choice(NAMES)} has {a} {thing}. Then gets {b} more. How many {thing} in all?"
    elif op == "-":
        a = rr(r, cls, "sub"); b = r.randint(1, max(2, a - 1)); ans = a - b
        instr = f"There are {a} {thing}. {b} are given away. How many {thing} are left?"
    else:
        a, b = rr(r, cls, "mulA"), r.randint(2, 6); ans = a * b
        instr = f"There are {a} {grp}s. Each {grp} has {b} {thing}. How many {thing} in all?"
    return _item("arith", instr, instr, {"op": op, "a": a, "b": b}, ans, f"It makes {ans}.", cls, ch, subj)

def g_error(r, cls, concept, ch, subj):
    """Misconception-diagnosis lens (analyze / DOK 3): is this answer right?"""
    op = {"add": "+", "sub": "-", "mul": "×"}.get(concept, "+")
    if op == "+": a, b = rr(r, cls, "add"), rr(r, cls, "add"); right = a + b
    elif op == "-": a = rr(r, cls, "sub"); b = r.randint(1, max(2, a - 1)); right = a - b
    else: a, b = rr(r, cls, "mulA"), r.randint(2, 9); right = a * b
    correct = r.random() < 0.4
    shown = right if correct else right + r.choice([-2, -1, 1, 2, 10])
    instr = f"{r.choice(NAMES)} wrote:  {a} {op} {b} = {shown}.  Is this correct?"
    return _item("true_false", instr, instr, {"statement": f"{a} {op} {b} = {shown}"}, bool(correct),
                 f"{a} {op} {b} = {right}." + ("" if correct else f"  {shown} is wrong."), cls, ch, subj)

# ---------- chapter → concept families (keyword routed) ----------
def chapter_concepts(chapter, cls):
    n = (chapter or "").lower()
    # --- specific strands FIRST (so they aren't swallowed by the generic number branch) ---
    #   These fix the gap where Shapes/Fractions/Measurement/Division/Data silently became addition.
    #   Match ICSE's clean names AND CBSE's playful NCERT titles ("Fair Share"=fractions,
    #   "Filling and Lifting"=capacity, "Fun with Shapes"=geometry, "Time Goes On"=time).
    if any(w in n for w in ("shape", "geometr", "solid")): return ["shape"]
    if any(w in n for w in ("fraction", "fair share", "half", "part")): return ["fraction"]
    if "divi" in n: return ["division"]
    if any(w in n for w in ("data", "graph", "pictograph", "handling", "chart")): return ["data"]
    if any(w in n for w in ("measure", "length", "weight", "capacity", "time", "clock",
                            "filling", "lifting", "temperature")): return ["measure"]
    # --- arithmetic / number strands (computed number path is correct here) ---
    if "add" in n: return ["add", "number"]
    if "subtrac" in n: return ["sub", "number"]
    if "multipl" in n: return ["mul"]
    if "money" in n or "currency" in n: return ["money", "add"]
    if "pattern" in n: return ["pattern", "number"]
    if any(w in n for w in ("number", "place", "count", "compar", "order")): return ["number", "add", "compare"]
    return ["add", "number"]

# ---------- STYLE LAYER: concept x style dials, weighted per student profile ----------
def _load_json(name):
    return json.load(open(os.path.join(BASE, name), encoding="utf-8"))
STYLES = _load_json("assessment_styles.json")["styles"]
PROF = _load_json("student_profiles.json")

def _realize(style_id, concept, r, cls, ch, subj):
    if style_id == "abstract_fact":
        return {"add": g_add, "sub": g_sub, "mul": g_mul, "div": g_mul, "compare": g_compare,
                "number": r.choice([g_compare, g_neighbour])}.get(concept, g_add)(r, cls, ch, subj)
    if style_id == "pictorial_count": return g_count(r, cls, ch, subj)
    if style_id == "story_reallife": return g_story(r, cls, {"add": "+", "sub": "-", "mul": "×", "div": "×"}.get(concept, "+"), ch, subj)
    if style_id == "sequence_pattern": return g_seq(r, cls, ch, subj)
    if style_id == "money_context": return g_money(r, cls, ch, subj)
    if style_id == "error_spot": return g_error(r, cls, concept if concept in ("add", "sub", "mul") else "add", ch, subj)
    return g_add(r, cls, ch, subj)

def pick_style(concept, cls, profile, r):
    cands = []
    for st in STYLES:
        if st["status"] != "live": continue
        gb = st["grade_band"]
        if not (gb[0] <= cls <= gb[1]): continue
        if concept not in st["concepts"] and "*" not in st["concepts"]: continue
        w = profile.get(st["id"], 0)
        if w > 0: cands.append((st, w))
    if not cands:  # fallback: any live style that fits the concept + grade
        for st in STYLES:
            if st["status"] == "live" and (concept in st["concepts"] or "*" in st["concepts"]) and st["grade_band"][0] <= cls <= st["grade_band"][1]:
                cands.append((st, 1))
    if not cands: return None
    tot = sum(w for _, w in cands); x = r.random() * tot; acc = 0
    for st, w in cands:
        acc += w
        if x <= acc: return st
    return cands[-1][0]


# ---------- knowledge subjects → LLM (grounded on the subtopic) ----------
RENDERABLE_KNOWLEDGE = {"match_following", "odd_one_out", "true_false", "cloze", "sort_groups"}

def _valid_knowledge(it):
    """Reject degenerate LLM items (placeholder pairs, missing/mismatched answers, etc.)."""
    def txt(s): return isinstance(s, str) and len(s.strip()) >= 2 and not re.fullmatch(r"[A-Za-z]", s.strip())
    t = it.get("type"); p = it.get("payload", {})
    if t == "match_following":
        pr = p.get("pairs", [])
        if not (isinstance(pr, list) and len(pr) >= 3): return False
        seen = set()
        for pair in pr:
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2): return False
            a, b = pair
            if not (txt(a) and txt(b)) or str(a).strip().lower() == str(b).strip().lower(): return False
            if str(a).strip().lower() in seen: return False
            seen.add(str(a).strip().lower())
        return True
    if t == "odd_one_out":
        o = p.get("options", []); return len(o) >= 3 and it.get("answer") in o
    if t == "true_false":
        return isinstance(it.get("answer"), bool) and txt(p.get("statement", ""))
    if t == "cloze":
        s = p.get("sentence", ""); b = p.get("bank", []); a = it.get("answer")
        return "___" in s and isinstance(b, list) and a in b and txt(str(a))
    if t == "sort_groups":
        return len(p.get("items", [])) >= 2 and len(p.get("bins", [])) >= 2 and isinstance(it.get("answer"), dict)
    return False


def llm_knowledge(subject, cls, chapter, subtopics, n, _attempts=2):
    import urllib.request
    url = os.environ.get("LITELLM_URL", "http://localhost:4000/v1") + "/chat/completions"
    key = os.environ.get("LITELLM_KEY", "sk-trigunai-master-key-2026")
    model = os.environ.get("WS_LLM_MODEL", "gpt-4o-mini")
    schema = (
        'Return ONLY a JSON array of worksheet items. Each item is one of these shapes:\n'
        '{"type":"match_following","instruction":"Match ...","payload":{"pairs":[["A","its match"],["B","its match"]]}}\n'
        '{"type":"odd_one_out","instruction":"Which does not belong?","payload":{"options":["a","b","c","d"]},"answer":"c"}\n'
        '{"type":"true_false","instruction":"...","payload":{"statement":"..."},"answer":true}\n'
        '{"type":"cloze","instruction":"Fill in the blank.","payload":{"sentence":"The ___ gives us light.","bank":["sun","moon","star"]},"answer":"sun"}\n'
        '{"type":"sort_groups","instruction":"Sort them.","payload":{"items":["Dog","Chair"],"bins":["Living","Non-living"]},"answer":{"Dog":"Living","Chair":"Non-living"}}'
    )
    lang_rule = ""
    if subject.strip().lower() == "hindi":
        lang_rule = ("\nIMPORTANT: Write EVERYTHING — instructions, statements, sentences, options, "
                     "pairs and answers — ENTIRELY in HINDI (Devanagari script). Do NOT use any "
                     "English words or Latin letters anywhere. This is a Hindi-medium worksheet for "
                     "a Hindi-speaking child, NOT a Hindi-to-English translation exercise.\n")
    prompt = (
        f"You are making a printable practice worksheet for a Class {cls} child ({subject}).\n"
        f"Chapter: {chapter}. Sub-topics: {', '.join(subtopics[:8]) if subtopics else chapter}.\n"
        f"Create {n} SIMPLE, age-appropriate, factually-correct items grounded strictly in this chapter. "
        f"Use short words a young child knows. Vary the types. Every item must have a correct, unambiguous answer."
        f"{lang_rule}\n"
        f"{schema}\n\nReturn ONLY the JSON array, no prose."
    )
    def _call():
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                           "temperature": float(os.environ.get("WS_LLM_TEMP", "0.6")), "max_tokens": 1600}).encode()
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            txt = json.load(resp)["choices"][0]["message"]["content"]
        m = re.search(r"\[.*\]", txt, re.S)
        return json.loads(m.group(0)) if m else []

    out, seen = [], set()
    for _ in range(_attempts):
        if len(out) >= n:
            break
        try:
            raw = _call()
        except Exception:
            continue
        for it in raw:
            if not isinstance(it, dict) or it.get("type") not in RENDERABLE_KNOWLEDGE:
                continue
            if not _valid_knowledge(it):        # <-- the hardening: drop degenerate items
                continue
            k = json.dumps(it.get("payload", {}), sort_keys=True, ensure_ascii=False)
            if k in seen:
                continue
            seen.add(k)
            it.setdefault("subject", subject.lower()); it["class"] = cls; it["chapter"] = chapter
            it["band"] = "1-2" if cls <= 2 else "3-5"
            it.setdefault("voice", it.get("instruction", "")); it.setdefault("explain", "Well done!")
            out.append(it)
    return out[:n]


# ---------- curriculum loader ----------
def load_cell(board, cls, subject):
    slug = board.lower().replace(" ", "") + f"_class{cls}_" + subject.lower().replace(" ", "")
    p = os.path.join(CURR, slug + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def chapters_of(cell):
    chs = cell.get("chapters", []) if cell else []
    out = []
    for c in chs:
        if isinstance(c, dict):
            out.append((c.get("name") or c.get("id") or "", c.get("subtopics", [])))
        elif isinstance(c, str):
            out.append((c, []))
    return out


# ---------- top-level generate ----------
def generate(board, cls, subject, chapter=None, n=8, seed=7, profile=None):
    r = random.Random(seed)
    is_math = subject.lower().replace(" ", "") in ("mathematics", "maths", "math")
    cell = load_cell(board, cls, subject)
    chs = chapters_of(cell)
    if chapter:
        chs = [c for c in chs if chapter.lower() in c[0].lower()] or chs

    if is_math:
        prof_name = profile or PROF["class_to_profile"].get(str(cls), "kids_3_5")
        weights = PROF["profiles"].get(prof_name, PROF["profiles"]["kids_3_5"])
        items = []
        pool = chs or [("Numbers", [])]
        tries = 0
        while len(items) < n and tries < n * 40:
            tries += 1
            chname, _ = pool[len(items) % len(pool)]
            concept = r.choice(chapter_concepts(chname, cls))
            # DIRECT computed strands bypass the style layer (shapes/fractions/measurement/division/data).
            if concept in DIRECT_MATHS:
                it = DIRECT_MATHS[concept](r, cls, chname, subject)
                it["style"] = {"id": concept, "cognitive": "understand", "dok": 1,
                               "representation": "pictorial" if concept in ("shape", "fraction", "data") else "abstract",
                               "context": "maths", "concept": concept}
                if it["payload"] not in [x["payload"] for x in items]:
                    items.append(it)
                continue
            st = pick_style(concept, cls, weights, r)      # concept x style, weighted per student type
            if not st:
                continue
            it = _realize(st["id"], concept, r, cls, chname, subject)
            it["style"] = {"id": st["id"], "cognitive": st["cognitive"], "dok": st["dok"],
                           "representation": st["representation"], "context": st["context"], "concept": concept}
            if it["payload"] not in [x["payload"] for x in items]:
                items.append(it)
        return [AC.enrich(it) for it in items]   # common engine: difficulty + distractors + hints

    # knowledge subject → LLM, spread across chapters
    if not chs:
        chs = [(chapter or subject, [])]
    per = max(1, n // min(len(chs), 3))
    items = []
    for chname, subs in chs[:3]:
        try:
            items += llm_knowledge(subject, cls, chname, subs, per)
        except Exception as e:
            print(f"  ⚠ LLM failed for '{chname}': {e}")
        if len(items) >= n:
            break
    return [AC.enrich(it) for it in items[:n]]   # common engine: difficulty + hints (distractors where applicable)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--class", dest="cls", type=int, required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--chapter", default="")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--profile", default="", help="override student profile (kids_1_2/kids_3_5/board/jee_neet/upsc)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    items = generate(args.board, args.cls, args.subject, args.chapter or None, args.n, args.seed, args.profile or None)
    payload = {"board": args.board, "class": args.cls, "subject": args.subject,
               "chapter": args.chapter or "all", "count": len(items), "items": items}
    if args.out:
        out = os.path.join(BASE, args.out); os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"✓ {len(items)} items → {out}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    for it in items[:6]:
        print(f"  · {it['type']:16} {it.get('instruction','')[:52]}")


if __name__ == "__main__":
    main()
