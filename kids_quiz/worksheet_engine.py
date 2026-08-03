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
                ("cookie", "🍪"), ("banana", "🍌"), ("grapes", "🍇")]
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
def g_count(r, cls, ch, subj):
    a, em = r.choice(COUNT_ASSETS); n = rr(r, cls, "count")
    return _item("count_write", f"Count the {a}s and write how many!", f"Count the {a}s.",
                 {"asset": a, "emoji": em, "n": n}, n, f"There are {n} {a}s!", cls, ch, subj)

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
    if "add" in n: return ["add", "number"]
    if "subtrac" in n: return ["sub", "number"]
    if "multipl" in n: return ["mul"]
    if "divi" in n: return ["div", "mul"]
    if "money" in n or "currency" in n: return ["money", "add"]
    if "pattern" in n: return ["pattern", "number"]
    if any(w in n for w in ("number", "place", "count", "compar", "order")): return ["number", "add", "compare"]
    if any(w in n for w in ("measure", "length", "weight", "capacity")): return ["compare", "add"]
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
