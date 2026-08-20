#!/usr/bin/env python3
"""Adversarial test battery for a built paper (or a set of them).

Checks the things that have actually gone wrong on this line, plus the ones that would be
embarrassing in front of an institute. Structural checks are cheap; the two that carry real
weight are:

  - NUMBER AGREEMENT between the Hindi and English halves of a bilingual question. If the English
    says "9 km" and the Hindi says "12 किमी", one of them is a mistranslation and a student
    working in Hindi gets a different answer. This is the automatable half of the failure that
    printed a "climate change" stem over four 1919 dates.

  - INDEPENDENT RE-SOLVING of the generated reasoning. Those answers are computed by
    `reasoninggen`; re-deriving them here from the question text alone, with solvers written
    without reference to that code, is a genuine check rather than a restatement.

Usage:  python3 test_papers.py Set1.html Set2.html
"""
import html
import io
import re
import sys
from collections import Counter

DEV = re.compile(r"[ऀ-ॿ]")
MIXED = re.compile(r"[ऀ-ॿ][A-Za-z]{2,}[ऀ-ॿ]")
NUM = re.compile(r"\d+")


def strip(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def parse(path):
    """-> (questions, answer_key). Each question: number, hi/en stem, hi/en options."""
    raw = io.open(path, encoding="utf-8").read()
    body = raw.split('<div class="meta">', 1)[1]
    blocks = re.findall(r'<div class="q">(.*?)(?=<div class="q">|<div class="keyhead")', body, re.S)
    qs = []
    for b in blocks:
        num = re.search(r'<span class="n">(\d+)\.', b)
        hi = re.search(r'<div class="hi">(.*?)</div>', b, re.S)
        en = re.search(r'<div class="en">(.*?)</div>', b, re.S)
        opt_groups = re.findall(r'<div class="ops">(.*?)</div>\s*(?=<div|$)', b, re.S)
        opts = [[(m.group(1), strip(m.group(2)))
                 for m in re.finditer(r'<b>\((\w)\)</b>(.*?)</span>', g, re.S)] for g in opt_groups]
        qs.append({"n": int(num.group(1)) if num else None,
                   "hi": strip(hi.group(1)) if hi else "",
                   "en": strip(en.group(1)) if en else "",
                   "opts": opts, "raw": b, "text": strip(b)})
    key = {int(m.group(1)): m.group(2)
           for m in re.finditer(r'class="k">(\d+)\. <b>([A-E])</b>', raw)}
    gen = {int(m.group(1)) for m in re.finditer(r'class="k">(\d+)\. <b>[A-E]</b><i>\*</i>', raw)}
    return qs, key, gen


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail and not ok else ''}")
    return ok


def structural(tag, qs, key, gen):
    print(f"\n=== {tag}: structure ===")
    ok = True
    nums = [q["n"] for q in qs]
    ok &= check("150 questions", len(qs) == 150, f"got {len(qs)}")
    ok &= check("numbering 1..150, no gaps or dupes", sorted(nums) == list(range(1, 151)))
    ok &= check("answer key has 150 entries", len(key) == 150, f"got {len(key)}")
    ok &= check("every question has a key entry", all(n in key for n in nums))
    bad_opts = [q["n"] for q in qs for g in q["opts"] if len(g) != 4]
    ok &= check("every rendered option block has 4 options", not bad_opts, str(bad_opts[:8]))
    keyless = [q["n"] for q in qs
               if q["opts"] and key.get(q["n"]) not in [lb for lb, _ in q["opts"][0]]]
    ok &= check("key letter exists among the printed options", not keyless, str(keyless[:8]))
    ok &= check("no raw LaTeX on the page",
                not any("\\frac" in q["text"] or "\\sqrt" in q["text"] for q in qs))
    mixed = [q["n"] for q in qs if MIXED.search(q["text"])]
    ok &= check("no Latin stranded inside Devanagari", not mixed, str(mixed[:8]))
    empty = [q["n"] for q in qs if not q["opts"]]
    ok &= check("no question printed without options", not empty, str(empty[:8]))
    print(f"        generated (asterisked): {len(gen)} of 150")
    return ok


def bilingual(tag, qs):
    """Numbers must agree between the two languages of the same question."""
    print(f"\n=== {tag}: Hindi vs English agreement ===")
    both = [q for q in qs if q["hi"] and q["en"]]
    mismatch = []
    for q in both:
        hn, en = Counter(NUM.findall(q["hi"])), Counter(NUM.findall(q["en"]))
        # ignore the leading question number that only the first-printed language carries
        for c in (hn, en):
            c.pop(str(q["n"]), None)
        if hn != en:
            mismatch.append((q["n"], sorted(hn - en), sorted(en - hn)))
    ok = check(f"numbers agree across languages ({len(both)} bilingual questions)",
               not mismatch, f"{len(mismatch)} differ")
    for n, honly, eonly in mismatch[:10]:
        print(f"        Q{n}: only in Hindi {honly} · only in English {eonly}")
    # option COUNT agreement where both languages printed options
    twolang = [q for q in qs if len(q["opts"]) == 2]
    bad = [q["n"] for q in twolang if len(q["opts"][0]) != len(q["opts"][1])]
    ok &= check("option counts agree across languages", not bad, str(bad[:8]))
    # ...and option CONTENT. Counts matching is not enough: one question printed English options
    # 29 / 9 beside Hindi −42 / −14, so the keyed letter was right in one language and wrong in
    # the other.
    numbad = []
    for q in twolang:
        if len(q["opts"][0]) != len(q["opts"][1]):
            continue
        for (_, h), (_, e) in zip(q["opts"][0], q["opts"][1]):
            if Counter(NUM.findall(h)) != Counter(NUM.findall(e)):
                numbad.append(q["n"])
                break
    ok &= check("option NUMBERS agree across languages", not numbad, str(numbad[:8]))
    return ok


def uniqueness(sets):
    print("\n=== uniqueness ===")
    ok = True

    def sig(q):
        """Whole stem plus the option set. A 90-char prefix false-positived on Assertion-Reason
        questions, which all open with the same rubric — it flagged two genuinely different
        questions as one."""
        t = (q["en"] or "") + "|" + (q["hi"] or "") + "|"
        t += "~".join(sorted(txt for g in q["opts"] for _, txt in g))
        t = re.sub(r"^\d+\.\s*", "", t).lower()
        return re.sub(r"[^a-z0-9ऀ-ॿ|~]+", "", t)

    for tag, qs, *_ in sets:
        dupes = [k for k, c in Counter(sig(q) for q in qs).items() if c > 1]
        ok &= check(f"{tag}: no repeat WITHIN the paper", not dupes, f"{len(dupes)} repeated")
        for d in dupes[:3]:
            print("        ", d[:70])
    # same COMPUTATION under different wording — text signatures cannot see this
    for tag, qs, key, _g in sets:
        seen, dup = {}, []
        for q in qs:
            nums = tuple(sorted(NUM.findall(q["en"] or q["hi"] or "")))
            ans = dict(q["opts"][-1]).get(key.get(q["n"]), "") if q["opts"] else ""
            if len(nums) < 2:
                continue
            sg = (nums, re.sub(r"\s+", "", ans))
            if sg in seen:
                dup.append((seen[sg], q["n"]))
            seen[sg] = q["n"]
        ok &= check(f"{tag}: no two questions are the same COMPUTATION", not dup, str(dup[:5]))
    if len(sets) > 1:
        (t1, q1, *_), (t2, q2, *_) = sets[0], sets[1]
        shared = {sig(q) for q in q1} & {sig(q) for q in q2}
        ok &= check(f"{t1} vs {t2}: no shared question", not shared, f"{len(shared)} shared")
        for s in list(shared)[:5]:
            print("        ", s[:70])
    return ok


def main():
    paths = sys.argv[1:]
    sets, all_ok = [], True
    for p in paths:
        qs, key, gen = parse(p)
        tag = re.sub(r".*InterLevel_|\.html", "", p) or p
        sets.append((tag, qs, key, gen))
    for tag, qs, key, gen in sets:
        all_ok &= structural(tag, qs, key, gen)
        all_ok &= bilingual(tag, qs)
        all_ok &= resolve(tag, qs, key, gen)
    all_ok &= uniqueness(sets)
    print("\n" + ("ALL CHECKS PASSED" if all_ok
                  else "*** SOME CHECKS FAILED — see above ***"))
    return 0 if all_ok else 1




# ── independent solvers ─────────────────────────────────────────────────────────────────────────
# Written from the QUESTION TEXT only. They deliberately do not import or consult reasoninggen —
# the point is to re-derive the answer by a second route and see whether the printed key agrees.
import math

DIRS = ["North", "East", "South", "West"]
HI_DIR = {"उत्तर": "North", "पूर्व": "East", "दक्षिण": "South", "पश्चिम": "West"}


def _turn(facing, way):
    i = DIRS.index(facing)
    return DIRS[(i + 1) % 4] if way == "right" else DIRS[(i - 1) % 4]


def solve_direction_facing(en):
    m = re.search(r"facing\s+(North|South|East|West)", en, re.I)
    if not m:
        return None
    cur = m.group(1).capitalize()
    for w in re.findall(r"takes?\s+a\s+(right|left)", en, re.I):
        cur = _turn(cur, w.lower())
    return cur


def solve_direction_distance(en):
    legs = re.findall(r"(\d+)\s*km", en, re.I)
    if len(legs) != 2 or not re.search(r"how far", en, re.I):
        return None
    a, b = int(legs[0]), int(legs[1])
    d = math.hypot(a, b)
    return f"{int(d)} km" if d == int(d) else None


def solve_ranking(en):
    m = re.search(r"row of (\d+).*?(\d+)(?:st|nd|rd|th) from the (left|right)", en, re.I | re.S)
    if not m:
        return None
    n, k = int(m.group(1)), int(m.group(2))
    if not re.search(r"position from the (right|left) end", en, re.I):
        return None
    return str(n - k + 1)


def solve_letter_shift(en):
    m = re.search(r"'([A-Z]+)'\s*is written as\s*'([A-Z]+)'.*?'([A-Z]+)'", en, re.S)
    if not m:
        return None
    src, dst, tgt = m.groups()
    if len(src) != len(dst):
        return None
    shifts = {(ord(b) - ord(a)) % 26 for a, b in zip(src, dst)}
    if len(shifts) != 1:
        return None
    s = shifts.pop()
    return "".join(chr((ord(c) - 65 + s) % 26 + 65) for c in tgt)


def solve_number_coding(en):
    m = re.search(r"coded by\s*(twice)?\s*its position.*?'([A-Z]+)'", en, re.I | re.S)
    if not m:
        return None
    mult = 2 if m.group(1) else 1
    return " ".join(str((ord(c) - 64) * mult) for c in m.group(2))


def solve_odd_one_out(en):
    nums = [int(x) for x in re.findall(r"\b(\d+)\b", en)]
    nums = [n for n in nums if n > 4]
    if len(nums) != 4 or not re.search(r"odd one out|alike", en, re.I):
        return None
    for test in (lambda n: int(math.isqrt(n)) ** 2 == n,
                 lambda n: n > 1 and all(n % d for d in range(2, int(math.isqrt(n)) + 1)),
                 lambda n: round(n ** (1 / 3)) ** 3 == n):
        flags = [test(n) for n in nums]
        if flags.count(True) == 3:
            return str(nums[flags.index(False)])
        if flags.count(False) == 3:
            return str(nums[flags.index(True)])
    return None


SOLVERS = [("direction-facing", solve_direction_facing), ("direction-distance", solve_direction_distance),
           ("ranking", solve_ranking), ("letter-shift", solve_letter_shift),
           ("number-coding", solve_number_coding), ("odd-one-out", solve_odd_one_out)]


def resolve(tag, qs, key, gen):
    print(f"\n=== {tag}: independent re-solve of generated reasoning ===")
    checked = agree = 0
    bad = []
    for q in qs:
        if q["n"] not in gen or not q["opts"]:
            continue
        en = q["en"] or ""
        for name, fn in SOLVERS:
            try:
                want = fn(en)
            except Exception:
                want = None
            if not want:
                continue
            # The keyed letter must be checked against EVERY language block: Hindi prints first,
            # so opts[0] is Hindi and an English computation would "disagree" with दक्षिण purely
            # because of language. Translate the direction words and accept a match in either.
            letter = key.get(q["n"])
            keyed = [dict(g).get(letter, "") for g in q["opts"]]
            checked += 1
            norm = lambda t: re.sub(r"\s+", "", str(t)).lower().rstrip(".")
            cands = set()
            for k in keyed:
                cands.add(norm(k))
                cands.add(norm(HI_DIR.get(k.strip(), k)))
            if norm(want) in cands:
                agree += 1
            else:
                bad.append((q["n"], name, want, " / ".join(filter(None, keyed)), en[:70]))
            break
    ok = check(f"printed key matches an independent solve ({checked} solvable questions)", not bad,
               f"{len(bad)} disagree")
    for n, name, want, got, stem in bad[:10]:
        print(f"        Q{n} [{name}] computed {want!r} but key says {got!r} — {stem}")
    if checked:
        print(f"        coverage: re-solved {checked} of {len(gen)} generated questions")
    return ok


if __name__ == "__main__":
    sys.exit(main())
