#!/usr/bin/env python3
"""A General Studies drill of N questions that are ALL genuinely difficulty 3.

Why this is not the paper builder. `build_onestep_paper` draws Part I to two constraints that both
pull difficulty DOWN, on purpose: the commission's syllabus topic quota (capitals, dance and rivers
together are ~46% of General Studies and none of them can produce a hard question) and the
commission's asking-style mix (only reverse-lookup reaches difficulty 3, and it is 14.3% of a real
paper). Those constraints are correct for a MOCK PAPER and wrong for a DRILL.

So this file abandons both and keeps the one rule that matters: **every question here is difficulty
3 as DERIVED by gs_ask.difficulty_of or by requiring 3-4 separate table lookups.** Nothing is
stamped. A question that cannot be shown to be hard is not included, which is why the composition
below is lopsided toward the Constitution — that is simply where the hard questions are.

Two sources, both already verified elsewhere:
  · gs_ask reverse-lookup with measurably confusable distractors (+1 backwards, +1 tight)
  · the statement forms, which need 3-4 lookups against the fact tables to answer at all

Every question is re-solved by test_papers' independent solvers before it is accepted; anything
unsolvable is dropped rather than shipped, so the count at the end is a verified count.
"""
import argparse, io, random, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "question_bank_engine"))
import build_onestep_paper as B          # noqa: E402
import test_papers as TP                 # noqa: E402
from qbank import staticgk_forms as SF, gs_ask as GA   # noqa: E402

# How many of each source may appear. Caps exist because "all hard" would otherwise be ~90%
# Constitution articles — the owner's "only one topic" complaint, reintroduced through the back
# door by a difficulty filter.
CAPS = [("articles",   20), ("panchayat",  5), ("capitals",   5),
        ("multi",       6), ("count",      5), ("which",      5), ("incorrect", 6)]

# Sources dropped with --drop give their allowance to the Constitution, which is the only pool deep
# enough to absorb it (89 hard articles available against a cap of 20). Capitals are the usual one:
# they ARE genuinely hard here — "Amaravati is the capital of which state?" against four different
# Pradeshes — but they read as a soft question to anyone skimming the paper, and on a drill sold as
# "50 hard" that impression costs more than the five questions are worth.


def _verified(row):
    """Re-solve with the independent solvers, against the PAGE TEXT; None if nothing reads it.

    Not the raw stem. The solvers were written against what test_papers.parse() reads out of
    rendered HTML — after esc(), mathify() and tag-stripping — and mathify materially changes some
    stems (it eats `$`, and turns `^2` into a <sup> that stripping flattens). Verifying the raw
    stem rejected 99 of 400 reasoning questions the real harness solves fine.
    """
    from paper_common import esc as _e, mathify as _m
    stem = TP.strip(_m(_e(row["stem"])))
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


def draw(tables, rng, source):
    if source in ("articles", "panchayat", "capitals"):
        name = {"articles": "ARTICLE_SUBJECT", "panchayat": "PANCHAYAT_ARTICLE",
                "capitals": "STATE_CAPITAL"}[source]
        if name not in tables:
            return None
        b = GA.build(tables, name, rng.choice(["rev", "comp", "wh"]), rng, diff=3)
        return b if b and b.get("difficulty") == 3 else None
    # Statement forms get only the tables whose CLAIMS require real knowledge. Handed everything,
    # a "hard" three-statement question came out as "Chhau is a dance of Jharkhand / Patna is the
    # capital of Bihar / Article 243C deals with Constitution of Panchayats" — two thirds of it
    # free, so the lookup count says hard and the work says otherwise. Dropping the standalone
    # capital questions was not enough; the easy facts were still arriving as ingredients.
    hard_only = {k: v for k, v in tables.items()
                 if k in ("ARTICLE_SUBJECT", "PANCHAYAT_ARTICLE", "AMENDMENT_DID")}
    f = {"multi": SF.b_multi_statement, "count": SF.b_count_statements,
         "which": SF.b_which_statement}.get(source)
    if f:
        return f(hard_only)(rng, 3)
    return GA.build_neg_statement(hard_only, rng, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--out", default="GS_HARD_50")
    ap.add_argument("--drop", default="", help="comma-separated sources to exclude; their quota "
                                               "goes to the Constitution articles")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    drop = {x.strip() for x in a.drop.split(",") if x.strip()}
    caps = dict(CAPS)
    freed = sum(caps[d] for d in drop if d in caps)
    for d in drop:
        caps[d] = 0
    caps["articles"] += freed
    globals()["CAPS"] = [(k, caps[k]) for k, _ in CAPS]
    if drop:
        print(f"  dropped {', '.join(sorted(drop))}; {freed} question(s) reassigned to articles "
              f"(cap now {caps['articles']})")
    tables = B.gs_tables()
    got, used, facts, sigs = [], {k: 0 for k, _ in CAPS}, set(), set()
    guard = 0
    while len(got) < a.n and guard < 40000:
        guard += 1
        room = [s for s, cap in CAPS if used[s] < cap]
        if not room:
            break
        src = room[len(got) % len(room)]
        b = draw(tables, rng, src)
        if not b or not b.get("stem_hi"):
            continue
        row = B._gs_row(b, 3)
        if row["tag"]["difficulty"] != 3:
            continue
        if B.gen_sig(row) in sigs or (row.get("fact") and row["fact"] in facts):
            continue
        by = _verified(row)
        if not by:                      # unreadable by every independent solver -> do not ship
            continue
        sigs.add(B.gen_sig(row))
        if row.get("fact"):
            facts.add(row["fact"])
        row["_src"], row["_by"] = src, by
        used[src] += 1
        got.append(row)
    got = B.spread_questions(got, rng)
    print(f"{len(got)} hard questions | " + " ".join(f"{k}:{used[k]}" for k, _ in CAPS))
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
    D = {3: "कठिन / Hard"}
    md = ["# General Studies — 50 HARD questions", "",
          "Every question below is difficulty **3 as derived, not as labelled** — either a reverse",
          "lookup whose distractors are measurably confusable, or a statement question needing 3-4",
          "separate lookups. Each one was re-solved by an independent solver before inclusion.", ""]
    for i, q in enumerate(rows, 1):
        md.append(f"**{i}.** {q.get('stem_hi','')}  ")
        md.append(f"    {q['stem']}  ")
        for o in q["options"]:
            md.append(f"    ({o['label']}) {o['text']}")
        md.append(f"    **उत्तर / Answer: ({q['correct_answer']})**   ·   {q['_src']}\n")
    io.open(f"{out}.md", "w", encoding="utf-8").write("\n".join(md))
    import json as _json
    _json.dump([{k: v for k, v in q.items() if not k.startswith("_") or k in ("_src", "_by")}
                for q in rows],
               io.open(f"{out}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"-> {out}.md")

    # HTML + PDF, using the CSS of a previously built paper so the drill looks like the real thing
    import re as _re, subprocess, os
    from paper_common import esc, mathify
    src_html = HERE / "OneStep_BSSC_InterLevel_STD_TAGGED.html"
    head = io.open(src_html, encoding="utf-8").read().split("<body")[0] if src_html.exists() else \
        "<html><head><meta charset='utf-8'></head>"

    def ops(o_list):
        return '<div class="ops">' + "".join(
            f'<span class="op"><b>({o["label"]})</b> {mathify(esc(o["text"]))}</span>'
            for o in o_list) + "</div>"

    body = ['<div class="wrap">',
            '<h2 class="sec">सामान्य अध्ययन — 50 कठिन प्रश्न / General Studies — 50 HARD questions</h2>',
            '<div class="pnote">प्रत्येक प्रश्न की कठिनाई <b>निर्धारित</b> की गई है, अंकित नहीं — '
            'या तो विपरीत-दिशा का प्रश्न जिसके विकल्प भ्रामक रूप से निकट हैं, या ऐसा कथन-प्रश्न '
            'जिसे हल करने के लिए 3-4 तथ्यों की जाँच आवश्यक है। '
            'Every question is difficulty 3 as DERIVED, and was re-solved independently before '
            'inclusion. This is a DRILL, not a mock paper: it deliberately ignores the syllabus '
            'topic quota and the commission’s asking-style mix, both of which pull difficulty '
            'down.</div>']
    for i, q in enumerate(rows, 1):
        hi = mathify(esc(q.get("stem_hi") or ""))
        en = mathify(esc(q["stem"]))
        body.append(_qblock(i, q, ops))
    body.append('<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2><div class="keys">' + "".join(
        f'<span class="k">{i}. <b>{q["correct_answer"]}</b></span>'
        for i, q in enumerate(rows, 1)) + "</div></div>")
    html_path = HERE / f"{out}.html"
    io.open(html_path, "w", encoding="utf-8").write(head + "<body>" + "".join(body) + "</body></html>")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={HERE / (out + '.pdf')}", html_path.as_uri()],
                       capture_output=True, timeout=300)
    print(f"-> {out}.html and {out}.pdf")
