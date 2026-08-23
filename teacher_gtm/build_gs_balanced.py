#!/usr/bin/env python3
"""A General Studies section that maximises DIFFICULTY subject to covering the syllabus.

The two requirements pull against each other and this file is where the trade is made explicitly
rather than by accident:

  · TOPIC COVERAGE comes mostly from the REAL commission questions. They span 18 topics — current
    affairs, Bihar, history, economy, sports — which no generator of ours can produce. They are
    also, every one of them, difficulty 2 or below: measured, 0 of 501 servable real GS questions
    is difficulty 3.
  · DIFFICULTY comes from the GENERATED questions, which reach difficulty 3 only where the fact
    table gives measurably confusable options — Constitution articles (88), Panchayat articles (5),
    movement YEARS (11), capitals (5). Everything else tops out at 2 whatever we do.

So the draw goes topic by topic and takes the HARDEST source that topic has: generated-hard if the
topic has any, otherwise the hardest real question available. What comes out is the most difficult
paper that still covers the syllabus, and the report at the end says exactly how much of each was
possible — because "distribution AND all hard" is not achievable from today's content, and a
number is more useful than a promise.
"""
import argparse, io, json, random, sys, pathlib
from collections import Counter, defaultdict
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "question_bank_engine"))
import build_onestep_paper as B          # noqa: E402
import test_papers as TP                 # noqa: E402
import syllabus_blueprint as SB          # noqa: E402
from paper_common import esc, mathify    # noqa: E402
from qbank import gs_ask as GA           # noqa: E402


def _verified(row):
    stem = TP.strip(mathify(esc(row["stem"])))
    TP._LAST_OPTIONS[stem] = [o["text"] for o in row["options"]]
    for name, fn in TP.SOLVERS:
        try:
            want = fn(stem)
        except Exception:
            continue
        if not want:
            continue
        want = {want} if isinstance(want, str) else set(want)
        got = next((o["text"] for o in row["options"] if o["label"] == row["correct_answer"]), "")
        return name if got in want else None
    return None


def gen_hard_by_topic(tables, rng, tries=900):
    """Every generated question of difficulty 3, grouped by the syllabus topic it belongs to."""
    out = defaultdict(list)
    seen = set()
    for name in tables:
        for _ in range(tries):
            for style in ("rev", "comp", "wh"):
                b = GA.build(tables, name, style, rng, diff=3)
                if not b or b.get("difficulty") != 3 or not b.get("stem_hi"):
                    continue
                row = B._gs_row(b, 3)
                if B.gen_sig(row) in seen or not _verified(row):
                    continue
                seen.add(B.gen_sig(row))
                for en, _hi in B.question_topics(row):
                    out[en].append(row)
                    break
    return out


def real_by_topic():
    """Real commission questions, bilingual and servable, grouped by syllabus topic, hardest first."""
    out = defaultdict(list)
    for q in B.load(inter_level=True):
        t = q.get("tag") or {}
        if t.get("section") != "General Studies":
            continue
        q["_generated"] = False
        for en, _hi in B.question_topics(q):
            out[en].append(q)
            break
    for v in out.values():
        v.sort(key=lambda q: -((q.get("tag") or {}).get("difficulty") or 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--exclude", default="", help="comma-separated JSON files whose questions this "
                                                  "set must not repeat — how Set 2 stays unique")
    ap.add_argument("--out", default="GS_BALANCED_50")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    # Everything an earlier set already used. Matched on the STEM, because that is what a student
    # comparing two papers side by side actually sees; a signature that keeps the numbers apart
    # would let the same question through with fresh distractors.
    _prev = set()
    for _f in [x.strip() for x in a.exclude.split(",") if x.strip()]:
        for _q in json.load(io.open(_f, encoding="utf-8")):
            _prev.add(_q.get("stem"))
            if _q.get("fact"):
                _prev.add(_q["fact"])
    tables = B.gs_tables()
    gen = gen_hard_by_topic(tables, rng)

    real = real_by_topic()

    # ── TRUE syllabus shares. Not renormalised over the topics we can make hard. ────────────────
    # Renormalising was the previous version and it inflated Constitution & polity from the
    # commission's 14% to 46% of the section — 23 of 50 questions opening with the same sentence,
    # on a paper sold as "built to the syllabus". The owner counted them: "Syllabus mein toh
    # Constitution 14% hai." He was right, and the honest fix is to keep every topic at its real
    # weight and take the HARDEST source each one has:
    #
    #   · a topic with hard-capable content is filled with difficulty-3 generated questions
    #   · a topic without it is filled with the hardest REAL commission question available,
    #     which is difficulty 2 — because 0 of 501 servable real GS questions is difficulty 3
    #
    # That costs the "every question is hard" claim and buys back the syllabus. Both cannot hold
    # at once with today's content, and the report below says exactly which questions are which.
    share = {t["en"]: t["share"] for t in SB.topics("General Studies")}
    live = {k: v for k, v in share.items() if gen.get(k) or real.get(k)}
    tot = sum(live.values()) or 1
    quota = {k: max(1, round(v / tot * a.n)) for k, v in live.items()}

    got, used, sigs, facts, stems = [], Counter(), set(), set(), set()
    order = sorted(quota, key=lambda k: -quota[k])
    for t in order:
        pool = list(gen.get(t) or []); rng.shuffle(pool)
        pool += (real.get(t) or [])          # hardest real, only after the hard ones run out
        for q in pool:
            if used[t] >= quota[t] or len(got) >= a.n:
                break
            sg = B.gen_sig(q) if q.get("_generated", True) else str(B.qid(q))
            # gen_sig includes the OPTION SET, so one stem drawn twice with different distractors
            # counts as two questions. "Kohima is the capital of which state?" printed FOUR times
            # on a delivered paper for exactly that reason. The fact id and the stem are what a
            # reader compares, so dedup on those too.
            if (sg in sigs or q.get("fact") in facts or q["stem"] in stems
                    or q["stem"] in _prev or q.get("fact") in _prev):
                continue
            sigs.add(sg); stems.add(q["stem"])
            if q.get("fact"):
                facts.add(q["fact"])
            q["_pick"] = "generated-hard" if q.get("_generated", True) else "real"
            got.append(q); used[t] += 1
    # Spill ROUND-ROBIN across every topic that still has stock, not into the deepest pool.
    # Dumping it all into Constitution & polity took it to 22 of 50 against a target of 10 — the
    # section ends up dominated by whichever table happens to be biggest, which is the same
    # failure the topic quota exists to prevent, arriving through the back door.
    if len(got) < a.n:
        leftovers = {t: [q for q in gen.get(t, []) if B.gen_sig(q) not in sigs] for t in quota}
        leftovers = {t: v for t, v in leftovers.items() if v}
        while len(got) < a.n and leftovers:
            for t in sorted(leftovers, key=lambda k: used[k] - quota.get(k, 0)):
                if len(got) >= a.n:
                    break
                q = leftovers[t].pop(0) if leftovers[t] else None
                if not leftovers[t]:
                    leftovers.pop(t, None)
                if q is None:
                    continue
                sg = B.gen_sig(q)
                if (sg in sigs or q.get("fact") in facts or q["stem"] in stems
                        or q["stem"] in _prev or q.get("fact") in _prev):
                    continue
                sigs.add(sg); stems.add(q["stem"])
                if q.get("fact"):
                    facts.add(q["fact"])
                q["_pick"] = "generated-hard(spill)"
                got.append(q); used[t] += 1

    got = B.spread_questions(got, rng)
    d = Counter((q.get("tag") or {}).get("difficulty") or 0 for q in got)
    from collections import Counter as _C
    src = _C(q.get("_pick") for q in got)
    print(f"{len(got)} questions | {len(used)} topics | hard {d[3]}  medium {d[2]}  easy {d[1]}"
          f"  | {dict(src)}")
    for t in sorted(used, key=lambda k: -used[k]):
        print(f"   {used[t]:3d} / target {quota[t]:<3d}  {t}")
    dropped = [t for t in share if t not in live]
    print("   NO hard content, share redistributed: " + "; ".join(dropped))
    json.dump(got, io.open(f"{a.out}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=str)
    return got


if __name__ == "__main__":
    main()
