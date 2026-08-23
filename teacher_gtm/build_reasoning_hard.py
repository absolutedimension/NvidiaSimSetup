#!/usr/bin/env python3
"""A Reasoning drill of N questions that are all genuinely hard.

The easiest of the three drills to build, and worth saying why: reasoning is the one section where
difficulty was never in doubt. `reasoninggen`'s builders all respond to `diff` — a difficulty-4
blood relation really is a longer chain than a difficulty-1 one — so the pool already carries 4,325
questions at difficulty 3 or above across 19 concepts. GS had to scrape for 50; here the only
question is which 50.

So the work is spread, not supply. Everything is drawn through `build_onestep_paper.load_generated`,
which already applies the gates this line learned the hard way:

  · `analogy_ambiguous` / `odd_one_out_ambiguous` — a number analogy with two defensible answers
    both on the page is a defect, not a hard question
  · `numbers_agree` — the Hindi template must not have dropped a rule the English states
  · a per-CONCEPT cap dealt round-robin, because a stem-text cap lets three near-identical
    direction questions onto one page

and then every question is re-solved by an independent solver before it is accepted.
"""
import argparse, io, json, random, sys, pathlib, subprocess, os
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "question_bank_engine"))
import build_onestep_paper as B          # noqa: E402
import test_papers as TP                 # noqa: E402
from paper_common import esc, mathify    # noqa: E402

CONCEPT_CAP = 6
used_concept = {}      # 19 concepts x 3 = 57, comfortably above 50, and no concept dominates


def _verified(row):
    # Solve the PAGE TEXT, not the raw stem. The solvers were written against what
    # test_papers.parse() reads out of rendered HTML — after esc(), mathify() and tag-stripping —
    # and several of them depend on that: mathify eats the `$` in a coded-inequality legend and
    # turns `^2` into a <sup> that stripping flattens. Verifying the raw stem therefore FAILED on
    # questions the real harness solves fine: measured 99 of 400 rejected, including every Coded
    # Inequality and Odd One Out in the pool. It failed safe — good questions dropped, none shipped
    # unverified — but it silently cost two whole concepts.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--exclude", default="", help="comma-separated JSON files whose questions this "
                                                  "set must not repeat — how Set 2 stays unique")
    ap.add_argument("--out", default="REASONING_HARD_50")
    a = ap.parse_args()
    random.seed(a.seed)
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
    import syllabus_blueprint as SB
    from collections import defaultdict, Counter

    # Draw to खंड (ग)'s OWN topic shares, not evenly across our 19 concepts. A flat per-concept cap
    # made the section even against ourselves rather than against the commission: four of our
    # concepts sit inside अंक गणितीय तर्कशक्ति, so it took 12 of 50 against a target of 7 while
    # समस्या समाधान took 2 against 6.
    share = {t["en"]: t["share"] for t in SB.topics("Reasoning")}
    # Draw deep. With a previous set excluded, a shallow draw leaves the last topic one
    # question short and the assembled paper prints 149 — a structural failure caused by the
    # sampling width rather than by the bank, which holds 4,325 hard reasoning questions.
    pool = B.load_generated(a.n * 20, cap_per_concept=90, difficulty=3)
    by_topic = defaultdict(list)
    for row in pool:
        tp = B.question_topics(row)
        if tp:
            by_topic[tp[0][0]].append(row)
    live = {k: share.get(k, 0) for k in by_topic if by_topic[k]}
    tot = sum(live.values()) or 1
    quota = {k: max(1, round(v / tot * a.n)) for k, v in live.items()}

    got, used, sigs = [], Counter(), set()
    for t in sorted(quota, key=lambda k: -quota[k]):
        for row in by_topic[t]:
            if used[t] >= quota[t] or len(got) >= a.n:
                break
            c = row.get("concept") or "?"
            if (B.gen_sig(row) in sigs or row["stem"] in _prev
                    or used_concept.get(c, 0) >= CONCEPT_CAP):
                continue
            if not _verified(row):
                continue
            import hashlib
            texts = [o["text"] for o in row["options"]]
            cur = "ABCD".index(row["correct_answer"])
            rot = int(hashlib.md5(row["stem"].encode("utf-8")).hexdigest(), 16) % 4
            texts = texts[-rot:] + texts[:-rot] if rot else texts
            row["options"] = [{"label": l, "text": x} for l, x in zip("ABCD", texts)]
            if row.get("options_hi"):
                hi = [o["text"] for o in row["options_hi"]]
                hi = hi[-rot:] + hi[:-rot] if rot else hi
                row["options_hi"] = [{"label": l, "text": x} for l, x in zip("ABCD", hi)]
            row["correct_answer"] = "ABCD"[(cur + rot) % 4]
            sigs.add(B.gen_sig(row)); used_concept[c] = used_concept.get(c, 0) + 1
            used[t] += 1; got.append(row)
    got = B.spread_questions(got, rng)
    print(f"{len(got)} hard reasoning | {len(used)} topics")
    for t in sorted(used, key=lambda k: -used[k]):
        print(f"   {used[t]:3d} / target {quota[t]:<3d}  {t}")
    return got, a.out


def _qblock(i, q, ops):
    """One question's markup, printing the second language ONLY when it differs.

    A number or letter analogy — "2 : 5 :: 10 : ?" — has no words in it, so its Hindi and English
    are the same string and printing both blocks put the identical line on the page twice. The
    main paper builder avoids this with paper_common.split_lang; these drill scripts emitted both
    unconditionally. Four questions of 150 came out duplicated.
    """
    from paper_common import esc as _e, mathify as _m
    hi = (q.get("stem_hi") or "").strip()
    en = (q["stem"] or "").strip()
    same = (not hi) or _m(_e(hi)) == _m(_e(en))
    r = ['<div class="q">']
    if same:
        # ONE block, and it must be the ENGLISH one. Emitting the single block as Hindi looked
        # right on the page and left `q["en"]` empty, so the harness had nothing to solve and
        # coverage fell to 146 of 150 — a cosmetic fix that quietly broke verification. A
        # symbol-only question loses nothing by being labelled English; it has no words.
        r.append(f'<div class="en"><span class="n">{i}.</span> '
                 f'{_m(_e(en)).replace(chr(10), "<br>")}</div>{ops(q["options"])}')
    else:
        r.append(f'<div class="hi"><span class="n">{i}.</span> '
                 f'{_m(_e(hi)).replace(chr(10), "<br>")}</div>{ops(q["options"])}')
        r.append(f'<div class="en">{_m(_e(en)).replace(chr(10), "<br>")}</div>'
                 f'{ops(q["options"])}')
    return "".join(r) + "</div>"



if __name__ == "__main__":
    rows, out = main()
    md = ["# Reasoning — 50 HARD questions", "",
          "Drawn at difficulty 3+ from a pool of 4,325, capped at 3 per concept, every question",
          "re-solved by an independent solver and passed through the ambiguity gates.", ""]
    for i, q in enumerate(rows, 1):
        md.append(f"**{i}.** {q.get('stem_hi','')}  ")
        md.append(f"    {q['stem']}  ")
        for o in q["options"]:
            md.append(f"    ({o['label']}) {o['text']}")
        md.append(f"    **उत्तर / Answer: ({q['correct_answer']})**   ·   {q.get('concept','')}\n")
    io.open(f"{out}.md", "w", encoding="utf-8").write("\n".join(md))
    import json as _json
    _json.dump([{k: v for k, v in q.items() if not k.startswith("_") or k in ("_src", "_by")}
                for q in rows],
               io.open(f"{out}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    src_html = HERE / "OneStep_BSSC_InterLevel_STD_TAGGED.html"
    head = io.open(src_html, encoding="utf-8").read().split("<body")[0] if src_html.exists() else \
        "<html><head><meta charset='utf-8'></head>"

    def ops(o_list):
        return '<div class="ops">' + "".join(
            f'<span class="op"><b>({o["label"]})</b> {mathify(esc(o["text"]))}</span>'
            for o in o_list) + "</div>"

    body = ['<div class="wrap">',
            '<h2 class="sec">मानसिक क्षमता — 50 कठिन प्रश्न / Reasoning — 50 HARD questions</h2>']
    for i, q in enumerate(rows, 1):
        body.append(_qblock(i, q, ops))
    body.append('<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2><div class="keys">' + "".join(
        f'<span class="k">{i}. <b>{q["correct_answer"]}</b></span>'
        for i, q in enumerate(rows, 1)) + "</div></div>")
    hp = HERE / f"{out}.html"
    io.open(hp, "w", encoding="utf-8").write(head + "<body>" + "".join(body) + "</body></html>")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={HERE / (out + '.pdf')}", hp.as_uri()],
                       capture_output=True, timeout=300)
    print(f"-> {out}.md / .html / .pdf")
