#!/usr/bin/env python3
"""kb_engine.py — KNOWLEDGE-BASE + TEMPLATES worksheet generator (no LLM).

The durable engine for knowledge subjects (GK/EVS/…), mirroring how the Maths engine makes
infinite CORRECT questions: separate FACTS from FORM.

  • FACTS  = a VERIFIED knowledge base (kids_quiz/kb/<subject>_class<N>.json): categories,
             groupings, relations (a→b pairs) and standalone facts. Hand-checked ONCE.
  • FORM   = templates below that COMBINE those facts into the 5 renderable worksheet types
             (odd_one_out / match_following / true_false / cloze / sort_groups).

Because every question is assembled from verified facts — and every "false"/distractor is a
value the engine PROVES belongs to a different key — each emitted item is correct BY
CONSTRUCTION. Unlimited combinations, ~free, ~100% clean. No model call, no fact-checking.

  python3 kb_engine.py --kb gk_class3 --n 1000 --board CBSE --out content/bank/cbse_class3_gk.json
  python3 kb_engine.py --kb gk_class3 --n 20            # print samples to stdout

Output shape matches the pre-pooled bank the app serves (kids_worksheet._bank_items):
  {board, class, subject, count, items:[ {type,instruction,payload,answer,subject,class,chapter,band,voice,explain} ]}
Items are enriched through the COMMON assessment core (difficulty + hints) like every other item.
"""
import json, os, argparse, random, re
import assessment_core as AC

BASE = os.path.dirname(os.path.abspath(__file__))
KBDIR = os.path.join(BASE, "kb")


# ---------------------------------------------------------------- KB load + validate
def load_kb(name):
    p = name if os.path.isabs(name) else os.path.join(KBDIR, name if name.endswith(".json") else name + ".json")
    kb = json.load(open(p, encoding="utf-8"))
    _validate(kb)
    return kb


def _validate(kb):
    """Fail LOUD on any KB shape that would let a template emit a wrong question.
    This is the guarantee: if validation passes, correctness is structural."""
    errs = []
    for c in kb.get("categories", []):
        m = c.get("members", [])
        if len(m) < 4:
            errs.append(f"category {c.get('name')}: needs >=4 members")
        if len(set(map(str.lower, m))) != len(m):
            errs.append(f"category {c.get('name')}: duplicate members")
    for g in kb.get("groupings", []):
        bins = g.get("bins", {})
        seen = {}
        for b, items in bins.items():
            for it in items:
                k = str(it).lower()
                if k in seen:
                    errs.append(f"grouping {g.get('name')}: '{it}' is in two bins ({seen[k]}, {b}) — negation unsafe")
                seen[k] = b
        if len(bins) < 2:
            errs.append(f"grouping {g.get('name')}: needs >=2 bins")
        tf = g.get("tf_template", "")
        bad = set(re.findall(r"\{(\w+)\}", tf)) - {"item", "bin", "art"}
        if bad:
            errs.append(f"grouping {g.get('name')}: tf_template uses unknown placeholders {bad} (allowed: item, bin, art)")
    for rel in kb.get("relations", []):
        pairs = rel.get("pairs", [])
        if len(pairs) < 3:
            errs.append(f"relation {rel.get('name')}: needs >=3 pairs")
        for pr in pairs:
            if not (isinstance(pr, (list, tuple)) and len(pr) == 2):
                errs.append(f"relation {rel.get('name')}: malformed pair {pr}")
        a_seen = {}
        for pr in pairs:
            if not (isinstance(pr, (list, tuple)) and len(pr) == 2):
                continue
            a, b = pr
            if str(a).lower() in a_seen:
                errs.append(f"relation {rel.get('name')}: left value '{a}' repeats — a→b must be a function")
            a_seen[str(a).lower()] = b
        allowed = {"a", "b", "art", "artb", "Artb"}
        for key in ("tf_template", "cloze_template"):
            bad = set(re.findall(r"\{(\w+)\}", rel.get(key, ""))) - allowed
            if bad:
                errs.append(f"relation {rel.get('name')}: {key} uses unknown placeholders {bad} (allowed: {sorted(allowed)})")
        if "___" not in rel.get("cloze_template", ""):
            errs.append(f"relation {rel.get('name')}: cloze_template must contain the blank '___'")
        # b's need not be globally unique; the engine checks string-inequality per distractor.
    if errs:
        raise ValueError("KB validation failed:\n  - " + "\n  - ".join(errs))


# ---------------------------------------------------------------- item builder
def _item(t, instr, payload, answer, chapter, subject, cls, band, explain, voice=None):
    return {"type": t, "instruction": instr, "payload": payload, "answer": answer,
            "subject": subject.lower(), "class": cls, "chapter": chapter, "band": band,
            "voice": voice or instr, "explain": explain}


def _art(s):
    """'a'/'an' article for nicer sentences (lowercase, mid-sentence)."""
    return "an" if str(s)[:1].lower() in "aeiou" else "a"


def _Art(s):
    """'A'/'An' article for the start of a sentence."""
    return "An" if str(s)[:1].lower() in "aeiou" else "A"


def _fmt(tmpl, a="", b=""):
    """Format a relation template, always supplying art/artb so templates can put the
    correct article before {a} or {b} regardless of whether the word starts with a vowel."""
    return tmpl.format(a=a, b=b, art=_Art(a), artb=_art(b), Artb=_Art(b))


def _S(kb, key, default, **fmt):
    """Fixed UI string with an optional per-KB override (kb['strings'][key]) — lets a Hindi KB
    supply Devanagari instructions/explanations while English KBs use the defaults."""
    s = kb.get("strings", {}).get(key, default)
    try:
        return s.format(**fmt) if fmt else s
    except Exception:
        return default


# ---------------------------------------------------------------- generators (FORM)
def g_odd_one_out(kb, r):
    cats = kb.get("categories", [])
    if len(cats) < 2:
        return None
    c1 = r.choice(cats)
    m1 = set(x.lower() for x in c1["members"])
    # a category whose members are DISJOINT from c1 → the odd item provably doesn't belong
    others = [c for c in cats if c is not c1 and not (set(x.lower() for x in c["members"]) & m1)]
    if not others:
        return None
    c2 = r.choice(others)
    three = r.sample(c1["members"], 3)
    odd = r.choice(c2["members"])
    opts = three + [odd]
    r.shuffle(opts)
    w1 = c1["label"].split()[-1]; w2 = c2["label"].split()[-1]
    w1pl = w1 if w1.endswith("s") else w1 + "s"
    rich = f"{odd} is {_art(w2)} {w2}, the others are all {w1pl}."
    return _item("odd_one_out", _S(kb, "odd_instruction", "Which one does NOT belong?"),
                 {"options": opts}, odd, c1.get("chapter", "General Knowledge"), kb["subject"],
                 kb["class"], 2, _S(kb, "odd_explain", rich, odd=odd))


def g_match(kb, r):
    rels = kb.get("relations", [])
    if not rels:
        return None
    rel = r.choice(rels)
    pairs = rel["pairs"]
    k = min(len(pairs), r.choice([4, 4, 5]))
    chosen = r.sample(pairs, k)
    payload_pairs = [[a, b] for a, b in chosen]
    return _item("match_following", rel.get("match_instruction", _S(kb, "match_default_instruction", "Match the pairs.")),
                 {"pairs": payload_pairs}, {a: b for a, b in chosen},
                 rel.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 3,
                 _S(kb, "match_explain", "Great matching!"))


def g_true_false(kb, r):
    """Half from relations (swap a→b to make a PROVABLY false statement), half from groupings,
    plus verified standalone facts (always true)."""
    src = r.choice(["rel", "rel", "grp", "grp", "fact"])
    if src == "fact" and kb.get("facts"):
        f = r.choice(kb["facts"])
        return _item("true_false", _S(kb, "tf_instruction", "Is this true or false?"), {"statement": f["statement"]}, True,
                     f.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 1, _S(kb, "tf_true_fact", "That's true! Well done."))
    if src == "grp" and kb.get("groupings"):
        g = r.choice(kb["groupings"])
        tf = g.get("tf_template", "A {item} is a {bin}.")
        bins = list(g["bins"].items())
        (bin_name, items) = r.choice([bi for bi in bins if bi[1]])
        x = r.choice(items)
        art = "An" if x[:1].lower() in "aeiou" else "A"
        make_true = r.random() < 0.5
        if make_true:
            stmt = tf.format(art=art, item=x, bin=bin_name.lower())
            return _item("true_false", _S(kb, "tf_instruction", "Is this true or false?"), {"statement": stmt}, True,
                         g.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 2, _S(kb, "tf_true", "Correct — that's true!"))
        wrong_bins = [b for b, _ in bins if b != bin_name]
        wb = r.choice(wrong_bins)
        stmt = tf.format(art=art, item=x, bin=wb.lower())
        corrected = tf.format(art=art, item=x, bin=bin_name.lower())   # the TRUE statement
        return _item("true_false", _S(kb, "tf_instruction", "Is this true or false?"), {"statement": stmt}, False,
                     g.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 2,
                     _S(kb, "tf_false_grouping", "Not quite — it should be: {corrected}", corrected=corrected))
    # relations
    rels = kb.get("relations", [])
    if not rels:
        return None
    rel = r.choice(rels)
    pairs = rel["pairs"]
    a, b = r.choice(pairs)
    tf = rel.get("tf_template")
    if not tf:
        return None
    make_true = r.random() < 0.5
    if make_true:
        return _item("true_false", _S(kb, "tf_instruction", "Is this true or false?"), {"statement": _fmt(tf, a, b)}, True,
                     rel.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 2, _S(kb, "tf_true", "Correct — that's true!"))
    # a PROVABLY false statement: another pair's b that is string-different from the true b
    alts = [bb for aa, bb in pairs if str(bb).strip().lower() != str(b).strip().lower()]
    if not alts:
        return None
    b2 = r.choice(alts)
    return _item("true_false", _S(kb, "tf_instruction", "Is this true or false?"), {"statement": _fmt(tf, a, b2)}, False,
                 rel.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 2,
                 _S(kb, "tf_false_relation", "That's false — the right answer is {b}.", b=b))


def g_cloze(kb, r):
    rels = [rl for rl in kb.get("relations", []) if rl.get("cloze_template")]
    if not rels:
        return None
    rel = r.choice(rels)
    pairs = rel["pairs"]
    a, b = r.choice(pairs)
    invert = rel.get("invert")
    if invert:  # blank is the LEFT value (a); distractors are other a's
        answer = a
        sentence = _fmt(rel["cloze_template"], a, b)
        pool = [aa for aa, bb in pairs if str(aa).strip().lower() != str(a).strip().lower()]
    else:       # blank is the RIGHT value (b); distractors are other b's
        answer = b
        sentence = _fmt(rel["cloze_template"], a, b)
        pool = [bb for aa, bb in pairs if str(bb).strip().lower() != str(b).strip().lower()]
    # dedupe distractors, keep those different from the answer
    seen = {str(answer).strip().lower()}
    distract = []
    for x in pool:
        k = str(x).strip().lower()
        if k not in seen:
            seen.add(k)
            distract.append(x)
    if len(distract) < 2:
        return None
    bank = [answer] + r.sample(distract, 2)
    r.shuffle(bank)
    return _item("cloze", _S(kb, "cloze_instruction", "Fill in the blank."), {"sentence": sentence, "bank": bank}, answer,
                 rel.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 3,
                 _S(kb, "cloze_explain", "The answer is {answer}.", answer=answer))


def g_sort(kb, r):
    grps = [g for g in kb.get("groupings", []) if len(g["bins"]) >= 2]
    if not grps:
        return None
    g = r.choice(grps)
    bins = [(b, items) for b, items in g["bins"].items() if items]
    if len(bins) < 2:
        return None
    use = r.sample(bins, min(len(bins), r.choice([2, 2, 3])))
    per = 2 if len(use) >= 3 else 3
    items, answer = [], {}
    for bin_name, members in use:
        pick = r.sample(members, min(per, len(members)))
        for x in pick:
            items.append(x)
            answer[x] = bin_name
    if len(items) < 3:
        return None
    r.shuffle(items)
    return _item("sort_groups", g.get("sort_instruction", _S(kb, "sort_default_instruction", "Sort these into the right groups.")),
                 {"items": items, "bins": [b for b, _ in use]}, answer,
                 g.get("chapter", "General Knowledge"), kb["subject"], kb["class"], 3, _S(kb, "sort_explain", "Great sorting!"))


GENERATORS = [g_odd_one_out, g_match, g_true_false, g_cloze, g_sort]
# rough target mix (matches the old pool balance); each may return None → we retry
WEIGHTS = {"g_true_false": 3, "g_cloze": 3, "g_odd_one_out": 3, "g_match": 2, "g_sort": 2}


def _sig(it):
    return json.dumps({"t": it["type"], "p": it["payload"]}, sort_keys=True, ensure_ascii=False)


def generate(kb, n, seed=7):
    r = random.Random(seed)
    weighted = []
    for gen in GENERATORS:
        weighted += [gen] * WEIGHTS.get(gen.__name__, 1)
    out, seen = [], set()
    stalls = 0
    while len(out) < n and stalls < n * 60:
        gen = r.choice(weighted)
        it = gen(kb, r)
        if not it:
            stalls += 1
            continue
        s = _sig(it)
        if s in seen:
            stalls += 1
            continue
        seen.add(s)
        out.append(it)
        stalls = 0
    return [AC.enrich(it) for it in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", required=True, help="KB name in kids_quiz/kb/ (e.g. gk_class3) or a path")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--board", default="CBSE")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    kb = load_kb(args.kb)
    items = generate(kb, args.n, args.seed)
    payload = {"board": args.board, "class": kb["class"], "subject": kb["subject"],
               "count": len(items), "items": items}
    if args.out:
        out = os.path.join(BASE, args.out) if not os.path.isabs(args.out) else args.out
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"✓ {len(items)} items → {out}")
    else:
        for it in items[:24]:
            print(f"  · {it['type']:15} {it.get('instruction','')[:40]:40} | ans={str(it.get('answer'))[:40]}")
        print(f"\n{len(items)} items generated.")


if __name__ == "__main__":
    main()
