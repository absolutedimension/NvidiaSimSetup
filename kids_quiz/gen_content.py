#!/usr/bin/env python3
"""
gen_content.py — Grade-3 Maths question GENERATOR for the kids quiz engine.

Produces a fresh content JSON (5 kid-friendly MCQs + JJ/Mikey narration) for a given
TOPIC + ADVENTURE. Questions are generated within ICSE Grade-3 bounds, so the daily
automation can run forever without repeating. Copyright-clean by construction.

  python3 gen_content.py --topic mul_fact --adventure "Multiplication Mountain" \
      --out content/auto.json --seed 42

Topics: place_value compare roman skip_count add sub mul_fact mul_word div
        fraction money time length weight shapes data patterns ordinal
"""
import json, random, argparse, os

BASE = os.path.dirname(os.path.abspath(__file__))
EMO = {"add": "➕", "sub": "➖", "mul": "✖️", "apple": "🍎", "star": "⭐", "fish": "🐟",
       "mango": "🥭", "spider": "🕷️", "coin": "🪙", "clock": "🕐", "ruler": "📏"}

def _opts(correct, distractors):
    """shuffle correct in with 3 distractors; return (options, answer_index)."""
    pool = [correct] + distractors[:3]
    random.shuffle(pool)
    return [str(o) for o in pool], pool.index(correct)

def _q(emoji, q, correct, distractors, explain, vq, va):
    options, ai = _opts(correct, distractors)
    return {"type": "mcq", "emoji": emoji, "q": q, "options": options, "answer": ai,
            "explain": explain, "voice_q": vq, "voice_a": va}

# ---------------- per-topic generators (return ONE question) ----------------
def g_mul_fact(r):
    a, b = r.randint(2, 9), r.randint(2, 9)
    p = a * b
    return _q("⭐", f"{a} × {b} = ?", p, [p+a, p-b, p+2, a+b, p*2],
              f"{a} times {b} makes {p}.",
              f"What is {a} times {b}?",
              f"It's {p}! {a} groups of {b} make {p}.")

def g_mul_word(r):
    a, b = r.randint(2, 6), r.randint(2, 6)
    thing = r.choice([("baskets","apples","🍎"),("ponds","fish","🐟"),("trees","mangoes","🥭"),
                      ("boxes","stars","⭐")])
    grp, item, em = thing; p = a*b
    return _q(em, f"{a} {grp}, each has {b} {item}. How many {item}?  {a} × {b} = ?",
              p, [p+b, p-a, a+b, p+2],
              f"{a} groups of {b} make {p}.",
              f"{a} {grp}, and each has {b} {item}. What is {a} times {b}?",
              f"It's {p}! {a} groups of {b} {item} make {p}.")

def g_add(r):
    a, b = r.randint(11, 480), r.randint(11, 480)
    s = a + b
    return _q("➕", f"{a} + {b} = ?", s, [s+10, s-1, s+100, s-10],
              f"{a} plus {b} makes {s}.",
              f"Add it up! {a} plus {b}.",
              f"It's {s}! {a} and {b} make {s}.")

def g_sub(r):
    a = r.randint(40, 900); b = r.randint(10, a-5)
    d = a - b
    return _q("➖", f"{a} − {b} = ?", d, [d+10, d-1, d+1, d+100],
              f"{a} take away {b} leaves {d}.",
              f"Take it away! {a} minus {b}.",
              f"It's {d}! {a} take away {b} leaves {d}.")

def g_div(r):
    b = r.randint(2, 9); q = r.randint(2, 9); a = b*q
    return _q("🍪", f"{a} ÷ {b} = ?", q, [q+1, q-1, q+2, b],
              f"{a} shared into {b} groups is {q} each.",
              f"Share {a} into {b} equal groups. How many in each?",
              f"It's {q}! {a} shared by {b} gives {q}.")

def g_place_value(r):
    n = r.randint(111, 9989)
    pos = r.choice([("hundreds", (n//100)%10), ("tens", (n//10)%10), ("ones", n%10),
                    ("thousands", n//1000)])
    name, val = pos
    dd = list({val, (val+1)%10, (val+2)%10, (val+3)%10});
    return _q("🔢", f"In {n}, what is the {name} digit?", val, [d for d in dd if d!=val],
              f"Look at the {name} place in {n}.",
              f"In the number {n}, which digit is in the {name} place?",
              f"It's {val}! The {name} digit of {n} is {val}.")

def g_compare(r):
    nums = r.sample(range(10, 999), 4)
    pick = r.choice(["big", "small"])
    ans = max(nums) if pick == "big" else min(nums)
    word = "BIGGEST" if pick == "big" else "SMALLEST"
    return _q("⚖️", f"Which number is the {word}?", ans, [n for n in nums if n != ans],
              f"{ans} is the {word.lower()}.",
              f"Look at {nums[0]}, {nums[1]}, {nums[2]} and {nums[3]}. Which is the {word.lower()}?",
              f"It's {ans}! {ans} is the {word.lower()} here.")

def g_skip_count(r):
    step = r.choice([2,3,4,5,10]); start = step*r.randint(1,6)
    seq = [start+step*i for i in range(3)]; nxt = seq[-1]+step
    return _q("🐾", f"Count in {step}s:  {seq[0]}, {seq[1]}, {seq[2]}, ?", nxt,
              [nxt+1, nxt-step, nxt+step],
              f"Keep adding {step}. Next is {nxt}.",
              f"Counting in {step}s: {seq[0]}, {seq[1]}, {seq[2]}. What comes next?",
              f"It's {nxt}! We keep adding {step}.")

def g_roman(r):
    n = r.randint(1, 20)
    romans = {1:"I",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",10:"X",
              11:"XI",12:"XII",13:"XIII",14:"XIV",15:"XV",16:"XVI",17:"XVII",18:"XVIII",
              19:"XIX",20:"XX"}
    rn = romans[n]; wrong = [romans[x] for x in r.sample([k for k in romans if k!=n], 3)]
    return _q("🏛️", f"What is {n} in Roman numerals?", rn, wrong,
              f"{n} is written {rn}.",
              f"How do we write {n} in Roman numerals?",
              f"It's {rn}! {n} in Roman numerals is {rn}.")

def g_fraction(r):
    names = {2: "half", 3: "one-third", 4: "one-quarter"}
    if r.random() < 0.4:
        d = r.choice([2, 3, 4])
        return _q("🍕", f"1 whole is cut into {d} equal parts. One part is…", names[d],
                  [v for k, v in names.items() if k != d] + ["one-fifth"],
                  f"{d} equal parts, so one part is {names[d]}.",
                  f"A pizza is cut into {d} equal parts. What is one part called?",
                  f"It's {names[d]}! One of {d} equal parts is {names[d]}.")
    d = r.choice([2, 3, 4]); base = d * r.randint(2, 6); ans = base // d
    return _q("🍕", f"{names[d].capitalize()} of {base} = ?", ans,
              [ans+1, ans-1 if ans > 1 else ans+2, base-ans if base-ans != ans else ans+3],
              f"{base} shared into {d} equal parts is {ans}.",
              f"What is {names[d]} of {base}?",
              f"It's {ans}! {names[d].capitalize()} of {base} is {ans}.")

def g_money(r):
    a, b = r.randint(5, 60), r.randint(5, 40)
    s = a+b
    return _q("🪙", f"₹{a} + ₹{b} = ?", f"₹{s}", [f"₹{s+10}", f"₹{s-1}", f"₹{s+5}"],
              f"₹{a} and ₹{b} make ₹{s}.",
              f"You have {a} rupees and get {b} more. How much now?",
              f"It's {s} rupees! ₹{a} and ₹{b} make ₹{s}.")

def g_time(r):
    h = r.randint(1, 12); kind = r.choice([("o'clock",f"{h}:00"),("half past",f"{h}:30")])
    word, ans = kind
    others = [f"{h}:15", f"{(h%12)+1}:00", f"{h}:45"]
    return _q("🕐", f"The clock shows {word} {h}. What time is it?", ans,
              [o for o in others if o!=ans],
              f"{word} {h} is {ans}.",
              f"If the clock shows {word} {h}, what time is it?",
              f"It's {ans}! {word} {h} is {ans}.")

def g_length(r):
    m = r.randint(1, 9)
    if r.random() < 0.5:
        ans = m*100
        return _q("📏", f"{m} metre{'s' if m>1 else ''} = ? cm", ans, [ans+10, ans+100, ans-10],
                  f"1 metre = 100 cm, so {m} m = {ans} cm.",
                  f"How many centimetres are in {m} metre{'s' if m>1 else ''}?",
                  f"It's {ans}! {m} metres is {ans} centimetres.")
    return _q("📏", f"{m*100} cm = ? metre{'s' if m>1 else ''}", m, [m+1, m-1 if m>1 else m+2, m*10],
              f"100 cm = 1 metre, so {m*100} cm = {m} m.",
              f"How many metres are in {m*100} centimetres?",
              f"It's {m}! {m*100} centimetres is {m} metres.")

def g_weight(r):
    k = r.randint(1, 9)
    if r.random() < 0.5:
        ans = k*1000
        return _q("⚖️", f"{k} kilogram{'s' if k>1 else ''} = ? grams", ans, [ans+100, ans-100, k*100],
                  f"1 kg = 1000 g, so {k} kg = {ans} g.",
                  f"How many grams are in {k} kilogram{'s' if k>1 else ''}?",
                  f"It's {ans}! {k} kilograms is {ans} grams.")
    return _q("⚖️", f"{k*1000} grams = ? kg", k, [k+1, k-1 if k>1 else k+2, k*10],
              f"1000 g = 1 kg, so {k*1000} g = {k} kg.",
              f"How many kilograms are in {k*1000} grams?",
              f"It's {k}! {k*1000} grams is {k} kilograms.")

def g_shapes(r):
    name, sides = r.choice([("triangle",3),("square",4),("rectangle",4),("pentagon",5),
                            ("hexagon",6),("octagon",8)])
    return _q("🔺", f"How many sides does a {name} have?", sides,
              [sides+1, sides-1, sides+2],
              f"A {name} has {sides} sides.",
              f"How many sides does a {name} have?",
              f"It's {sides}! A {name} has {sides} sides.")

def g_data(r):
    counts = [r.randint(2,9) for _ in range(3)]; total = sum(counts)
    fruit = ["apples","bananas","mangoes"]
    return _q("📊", f"In a chart: {counts[0]} {fruit[0]}, {counts[1]} {fruit[1]}, "
              f"{counts[2]} {fruit[2]}. How many fruits in all?", total,
              [total+1, total-2, total+3],
              f"{counts[0]}+{counts[1]}+{counts[2]} = {total}.",
              f"Add the chart: {counts[0]}, {counts[1]} and {counts[2]}. How many in all?",
              f"It's {total}! Together they make {total}.")

def g_patterns(r):
    step = r.choice([2,5,10]); start = r.randint(1,5)*step
    seq=[start+step*i for i in range(3)]; nxt=seq[-1]+step
    return _q("🔷", f"What comes next?  {seq[0]}, {seq[1]}, {seq[2]}, ?", nxt,
              [nxt+step,nxt-1,nxt+1],
              f"The pattern adds {step} each time.",
              f"Find the pattern: {seq[0]}, {seq[1]}, {seq[2]}. What's next?",
              f"It's {nxt}! The pattern grows by {step}.")

def g_ordinal(r):
    words=["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    n=r.randint(1,10)
    return _q("🏅", f"Which position is the {words[n-1]}?", n, [n+1,n-1 if n>1 else n+2,n+2],
              f"{words[n-1]} means position {n}.",
              f"What number position is '{words[n-1]}'?",
              f"It's {n}! {words[n-1]} is position number {n}.")

GEN = {"mul_fact": g_mul_fact, "mul_word": g_mul_word, "add": g_add, "sub": g_sub,
       "div": g_div, "place_value": g_place_value, "compare": g_compare,
       "skip_count": g_skip_count, "roman": g_roman, "fraction": g_fraction,
       "money": g_money, "time": g_time, "length": g_length, "weight": g_weight,
       "shapes": g_shapes, "data": g_data, "patterns": g_patterns, "ordinal": g_ordinal}

def make(topic, adventure, n=5, seed=None):
    r = random.Random(seed)
    gen = GEN[topic]
    qs, seen = [], set()
    tries = 0
    while len(qs) < n and tries < 400:
        tries += 1
        q = gen(r)
        key = (q["q"], tuple(sorted(q["options"])))   # full-question identity, not just stem
        if key in seen:      # no duplicate questions within one video
            continue
        seen.add(key); qs.append(q)
    return {
        "lang": "en", "voice": "en-IN-NeerjaExpressiveNeural",
        "series": "Treasure Trackers", "mascot": "🦊", "mascot_img": "jj.png",
        "mascot_name": "JJ", "mascot2": "🐵", "mascot2_img": "mikey.png",
        "mascot2_name": "Mikey", "subject": "Maths", "chapter": adventure,
        "adventure": adventure, "topic_line": "Help JJ & Mikey find the treasure!",
        "timer_seconds": 6, "cta": "Collect all 5 gems!",
        "intro_voice": f"Hi friends! I'm JJ, and this is Mikey! Welcome to {adventure}. "
                       f"Answer five questions, collect five gems, and we find the treasure! Ready? Let's go!",
        "outro_voice": "Woohoo! All five gems! You found the treasure! You're a maths superstar. See you next time!",
        "questions": qs,
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, choices=list(GEN))
    ap.add_argument("--adventure", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    data = make(a.topic, a.adventure, a.n, a.seed)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(data, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {a.out}  ({len(data['questions'])} Qs, topic={a.topic})")
