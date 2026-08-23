#!/usr/bin/env python3
"""A Mathematics drill of N questions that are all genuinely hard.

The GS drill had to fight for 50 hard questions; maths has 6,313 distinct ones available, so the
work here is not finding difficulty but refusing the things that only LOOK like it.

Two refusals, both measured rather than assumed:

1. **Only builders that actually respond to `diff`.** Measured by generating 300 questions at
   difficulty 1 and 300 at difficulty 4 and comparing the SHAPES: `_b_simplify` goes 4 shapes -> 184,
   `_b_percentage` 1 -> 5. But `_b_alligation`, `_b_approx`, `_b_partnership`, `_b_series_missing`
   and `_b_series_wrong` produce the SAME shapes at both bands — for those the difficulty is a
   label stamped at storage time, exactly as the skill records, and putting them in a "hard" drill
   would be the badge problem all over again. Seven builders survive.

2. **The Inter Level syllabus still applies.** A drill may ignore the topic QUOTA — that is what
   makes it a drill — but it may not ignore the SYLLABUS. Advt 02/23(A) names arithmetic only, so
   `paper_common.inter_level_ok` gates every question and the builders excluded from an Inter Level
   paper (time & work, trains, boats, mensuration, quadratics ...) never enter.

Every question is re-solved by an independent solver in test_papers before it is accepted, and
capped per TEMPLATE — a delivered paper once printed seven identical "(x)^2 + a/b - p% of c"
questions in a row, and a difficulty filter alone would not have stopped that happening again.
"""
import argparse, io, json, random, sys, pathlib, subprocess, os, re
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "question_bank_engine"))
import build_onestep_paper as B          # noqa: E402
import test_papers as TP                 # noqa: E402
from paper_common import inter_level_ok, esc, mathify   # noqa: E402
from qbank import quantgen as Q          # noqa: E402

# builder -> how many it may contribute. Only diff-responsive, bilingual, in-syllabus builders.
# Caps in the COMMISSION'S OWN PROPORTIONS, not equal shares. Equal caps put INTEREST at 12 of 50
# against a syllabus target of 2, and computation at 8 against a target of 15 — the exact
# inversion (ब्याज 32%, प्रतिशत 0%) that syllabus_blueprint was written to fix, reintroduced by a
# drill script that had never heard of it. Shares are from drop/bssc/SYLLABUS_MAP.json, measured
# against 330 real BSSC maths questions.
_SHARE = {"_b_simplify": 0.22, "_b_percentage": 0.20, "_b_ratio": 0.12,
          "_b_average": 0.08, "_b_profit_loss": 0.07, "_b_si": 0.02, "_b_ci": 0.01}
CAPS = [(k, max(1, round(v / sum(_SHARE.values()) * 50) + 2)) for k, v in _SHARE.items()]
# Per digit-stripped stem shape. 3 was tried first and the drill came back 44 of 50: several
# builders have only two or three distinct SHAPES at the hard bands (ratio and compound interest
# especially), so 3-per-shape capped them below their question quota. 4 of 50 is still tighter
# than Part III's per-concept cap and reaches the full count.
TEMPLATE_CAP = 4

_NAMES = {b.__name__: b for bs in Q._CHAP_BUILDERS.values() for b in bs}


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


def draw(nm, rng):
    d = rng.choice([3, 4])
    try:
        q = Q._make_question(_NAMES[nm](rng, d), rng, {"chapter": "Arithmetic", "dmax": d})
    except Exception:
        return None
    if not q.stem_hi:
        return None
    row = {"stem": q.stem, "stem_hi": q.stem_hi, "options": q.options,
           "options_hi": q.options_hi, "correct_answer": q.correct_answer,
           "solution": q.solution, "solution_hi": q.solution_hi, "concept": q.concept,
           "_generated": True, "source_pdf": "quantgen", "number": None,
           "src": [nm], "tag": {"section": "Mathematics", "difficulty": d}}
    return row if inter_level_ok(row) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--exclude", default="", help="comma-separated JSON files whose questions this "
                                                  "set must not repeat — how Set 2 stays unique")
    ap.add_argument("--out", default="MATHS_HARD_50")
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
    used = {k: 0 for k, _ in CAPS}
    tmpl, sigs, got, comp = {}, set(), [], set()
    caps = dict(CAPS)
    guard = 0
    while len(got) < a.n and guard < 60000:
        guard += 1
        room = [s for s, _ in CAPS if used[s] < caps[s]]
        if not room:
            break
        # Pick the builder furthest BELOW its syllabus target, not the next one in a rotation.
        # Round-robin fills every builder evenly and only stops at its cap, so computation came out
        # 7 against a target of 15 while interest — capped at 3 — was full. A quota is only a quota
        # if the selector is driven by the deficit.
        tgt = {k: round(_SHARE[k] / sum(_SHARE.values()) * a.n) for k, _ in CAPS}
        nm = max(room, key=lambda k: (tgt.get(k, 0) - used[k], -[c for c, _ in CAPS].index(k)))
        row = draw(nm, rng)
        if not row:
            continue
        # Dedup on SORTED numbers as well as gen_sig. Successive discounts of "10% and 20%" and
        # "20% and 10%" are the SAME computation with the same answer; gen_sig keeps the numbers in
        # order so it saw two questions, and the harness — which sorts them — did not.
        import re as _re
        csig = (row["concept"], tuple(sorted(_re.findall(r"\d+", row["stem"]))))
        if csig in comp:
            continue
        t = B.template_sig(row)
        if (tmpl.get(t, 0) >= TEMPLATE_CAP or B.gen_sig(row) in sigs
                or row["stem"] in _prev):
            continue
        by = _verified(row)
        if not by:
            continue
        sigs.add(B.gen_sig(row)); comp.add(csig); tmpl[t] = tmpl.get(t, 0) + 1
        used[nm] += 1; row["_by"] = by
        got.append(row)
    got = B.spread_questions(got, rng)
    print(f"{len(got)} hard maths | " + " ".join(f"{k.replace('_b_','')}:{used[k]}" for k, _ in CAPS))
    print(f"  distinct templates: {len(tmpl)}  most-repeated: {max(tmpl.values(), default=0)}")
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
    md = ["# Mathematics — 50 HARD questions", "",
          "Only builders that MEASURABLY respond to difficulty are used — five quantgen builders",
          "produce identical shapes at difficulty 1 and 4, so their band is a label and they are",
          "excluded. Every question is inside the Inter Level arithmetic syllabus and was",
          "re-solved by an independent solver before inclusion.", ""]
    for i, q in enumerate(rows, 1):
        md.append(f"**{i}.** {q.get('stem_hi','')}  ")
        md.append(f"    {q['stem']}  ")
        for o in q["options"]:
            md.append(f"    ({o['label']}) {o['text']}")
        md.append(f"    **उत्तर / Answer: ({q['correct_answer']})**   ·   {q['concept']}\n")
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
            '<h2 class="sec">गणित — 50 कठिन प्रश्न / Mathematics — 50 HARD questions</h2>',
            '<div class="pnote">केवल वे जनक प्रयुक्त हैं जिनकी कठिनाई मापी जा सकी है; पाँच जनक '
            'कठिनाई 1 और 4 पर समान प्रश्न देते हैं, अतः वे बाहर रखे गए हैं। सभी प्रश्न इंटर स्तर '
            'के अंकगणित पाठ्यक्रम के भीतर हैं। '
            'Only builders that measurably respond to difficulty are used; five produce identical '
            'shapes at difficulty 1 and 4, so their band is a label and they are excluded. Every '
            'question is inside the Inter Level arithmetic syllabus and independently re-solved.'
            '</div>']
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
