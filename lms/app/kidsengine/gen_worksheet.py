#!/usr/bin/env python3
"""
gen_worksheet.py — WORKSHEET-ITEM generator (Phase 3).

Where gen_content.py emits MCQs, this emits the non-MCQ WORKSHEET archetypes from
WORKSHEET_GRAMMAR.md — the shapes KidsWorksheet.render() (worksheet.js) actually draws:
trace, count_write, arith, fill_sequence, compare_symbol, neighbour_number, pattern_next,
match_following, count_money. Items reference pool assets by id (asset:"apple") so the asset
pool fills real art, with emoji fallback. Grade-3 Maths ranges (ICSE, his real book).

Every item is copyright-clean by construction (computed values + templates).

  python3 gen_worksheet.py --topic add --n 5 --out content/ws_add.json
  python3 gen_worksheet.py --all --n 12 --out content/ws_grade3.json   # mixed worksheet
"""
import json, random, argparse, os

BASE = os.path.dirname(os.path.abspath(__file__))
SUBJECT, CHAPTER_DEFAULT = "Mathematics", "grade3"
COUNT_ASSETS = [("apple", "🍎"), ("star", "⭐"), ("fish", "🐟"), ("balloon", "🎈"),
                ("cookie", "🍪"), ("banana", "🍌"), ("grapes", "🍇")]


def _item(t, instruction, voice, payload, answer, explain, chapter=CHAPTER_DEFAULT, band="1-2"):
    return {"type": t, "subject": SUBJECT.lower(), "chapter": chapter, "band": band,
            "instruction": instruction, "voice": voice, "payload": payload,
            "answer": answer, "explain": explain}


# ---------------- per-topic worksheet-item generators ----------------
def g_count_write(r):
    asset, emoji = r.choice(COUNT_ASSETS)
    n = r.randint(3, 12)
    return _item("count_write", f"Count the {asset}s and write the number!",
                 f"Count the {asset}s and write how many.",
                 {"asset": asset, "emoji": emoji, "n": n}, n,
                 f"Yes — there are {n} {asset}s!")


def g_arith(r, op=None):
    op = op or r.choice(["+", "-", "×"])
    if op == "+":
        a, b = r.randint(101, 480), r.randint(101, 480); ans = a + b; word = "plus"
    elif op == "-":
        a = r.randint(200, 900); b = r.randint(50, a - 20); ans = a - b; word = "minus"
    else:  # ×
        a, b = r.randint(2, 12), r.randint(2, 9); ans = a * b; word = "times"
    return _item("arith", f"Solve it!  {a} {op} {b} = ?",
                 f"What is {a} {word} {b}?", {"op": op, "a": a, "b": b}, ans,
                 f"{a} {word} {b} makes {ans}.", chapter="operations", band="3-5")


def g_fill_sequence(r):
    step = r.choice([2, 5, 10, 100])
    start = r.choice([0, step, 2 * step]) + r.randint(0, 3) * step
    seq = [start + i * step for i in range(4)]
    hide = r.randint(1, 2)
    ans = [seq[hide]]
    shown = [x if i != hide else None for i, x in enumerate(seq)]
    return _item("fill_sequence", "Fill in the missing number! 🚂",
                 f"Skip count by {step}. What number is missing?",
                 {"seq": shown, "step": step}, ans, f"Counting by {step}s, the missing number is {ans[0]}.",
                 chapter="patterns")


def g_compare(r):
    a, b = r.randint(10, 9999), r.randint(10, 9999)
    while a == b:
        b = r.randint(10, 9999)
    ans = "<" if a < b else ">"
    return _item("compare_symbol", "Which is bigger? Put the right sign! 🐊",
                 f"Compare {a} and {b}.", {"a": a, "b": b}, ans,
                 f"{a} is {'less' if ans == '<' else 'greater'} than {b}.", chapter="numbers", band="3-5")


def g_neighbour(r):
    mode = r.choice(["after", "before"])
    n = r.randint(100, 998)
    ans = n + 1 if mode == "after" else n - 1
    disp = f"___ , {n}" if mode == "after" else f"{n} , ___"
    return _item("neighbour_number", f"What comes just {mode} {n}? ➡️",
                 f"What number comes just {mode} {n}?",
                 {"mode": mode, "n": n, "display": disp}, ans,
                 f"Just {mode} {n} is {ans}.", chapter="numbers")


def g_pattern(r):
    kind = r.choice(["shape", "num"])
    if kind == "shape":
        base = r.choice([["🔺", "🔵"], ["🟢", "🟡", "🔴"], ["⬛", "⬜"]])
        seq = (base * 3)[:4]
        nxt = base[len(seq) % len(base)]
        opts = list(dict.fromkeys(base + [nxt]))
        return _item("pattern_next", "What comes next? 🔁", "What comes next in the pattern?",
                     {"seq": seq, "options": opts}, nxt, "Follow the repeating pattern!", chapter="patterns")
    step = r.choice([2, 5, 10])
    start = r.randint(1, 8)
    seq = [str(start + i * step) for i in range(4)]
    nxt = str(start + 4 * step)
    opts = [nxt, str(int(nxt) + step), str(int(nxt) - 1)]
    r.shuffle(opts)
    return _item("pattern_next", "What number comes next? 🔢", "What number comes next?",
                 {"seq": seq, "options": opts}, nxt, f"The numbers go up by {step}.", chapter="patterns")


def g_match(r):
    # match quantity picture-group to numeral OR animal to home (EVS-flavoured but pool-backed)
    picks = r.sample(COUNT_ASSETS, 3)
    pairs = [[f"{em}×{r.randint(2,6)}", None] for (a, em) in picks]
    # build "N emoji" left, numeral right
    left, right = [], []
    for (a, em) in picks:
        n = r.randint(2, 6)
        left.append({"asset": a, "emoji": em, "n": n} if False else (em + " " * 0) * n)  # simple emoji strip
        right.append(n)
    pairs = [[left[i], right[i]] for i in range(3)]
    return _item("match_following", "Match the group to its number! ✏️",
                 "Match each group to how many.", {"pairs": pairs}, None,
                 "Count each group and match it!", chapter="numbers")


def g_money(r):
    coins = r.choice([[10, 5, 2], [10, 10, 5], [5, 2, 2, 1], [10, 5, 2, 1]])
    total = sum(coins)
    disp = " + ".join(f"₹{c}" for c in coins)
    return _item("count_money", "How much money is it? 🪙", "Add up the coins.",
                 {"coins": coins, "display": disp}, total, f"All the coins make ₹{total}.", chapter="money", band="3-5")


TOPICS = {
    "count": g_count_write, "add": lambda r: g_arith(r, "+"), "sub": lambda r: g_arith(r, "-"),
    "mul": lambda r: g_arith(r, "×"), "arith": g_arith, "skip": g_fill_sequence,
    "compare": g_compare, "neighbour": g_neighbour, "pattern": g_pattern,
    "match": g_match, "money": g_money,
}
MIX = ["count", "add", "sub", "mul", "skip", "compare", "neighbour", "pattern", "money"]


def build(topic, n, seed):
    r = random.Random(seed)
    gens = [TOPICS[topic]] if topic in TOPICS else [TOPICS[t] for t in MIX]
    items, seen = [], set()
    tries = 0
    while len(items) < n and tries < n * 20:
        tries += 1
        it = (gens[len(items) % len(gens)] if topic == "all" else r.choice(gens))(r)
        key = json.dumps(it["payload"], sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        items.append(it)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="all")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="content/ws_grade3.json")
    args = ap.parse_args()
    items = build(args.topic, args.n, args.seed)
    out = os.path.join(BASE, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"subject": SUBJECT, "grade": 3, "count": len(items), "items": items}, f, ensure_ascii=False, indent=2)
    print(f"✓ {len(items)} worksheet items ({args.topic}) → {out}")
    for it in items[:4]:
        print(f"  · {it['type']:16} {it['instruction'][:52]}")


if __name__ == "__main__":
    main()
