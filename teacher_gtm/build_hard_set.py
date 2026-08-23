#!/usr/bin/env python3
"""Assemble the three hard drills into ONE 150-question paper in the standard One Step template.

Renders from the drills' JSON, not from their HTML. Scraping the rendered pages worked and was
fragile in a way that had already bitten once: the assembled paper lost its last question because
the harness's parser looks ahead for a marker the wrapper did not emit. Reading the questions as
DATA and rendering them once, here, removes that whole class of problem.

What this prints, and what it deliberately does not:
  · the full paper preamble — cover, examination scheme, official syllabus, qualifying marks,
    instructions — taken verbatim from the paper builder's own output, so the drill looks like
    every other One Step paper
  · a TOPIC tag on every question, and a topic-distribution table under each section header
  · NO difficulty badge. A student who reads "कठिन" before answering has been primed, and this set
    is for students rather than for the owner's calibration.
"""
import io, json, re, sys, pathlib, subprocess, os
from collections import Counter
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "question_bank_engine"))
import build_onestep_paper as B          # noqa: E402
from paper_common import esc, mathify    # noqa: E402

SECTIONS = [("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", "GS_BALANCED_50"),
            ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (Mathematics)", "MATHS_HARD_50"),
            ("भाग–III / PART–III : मानसिक क्षमता जाँच (Reasoning)", "REASONING_HARD_50")]

# Reasoning and maths carry a `concept`, not a syllabus `src`, so question_topics() resolves them
# through SYLLABUS_MAP exactly as the paper builder does.
def topics_of(q):
    tp = B.question_topics(q)
    return [h for _e, h in tp] or [str(q.get("concept") or "?")]


def badge(q):
    """Topic and question type. No difficulty — see the module docstring."""
    tp = topics_of(q)
    lab = " · ".join(B.short_hi(h) for h in tp[:2]) + (" आदि" if len(tp) > 2 else "")
    return (f'<span class="dbadge">{esc(lab)}'
            f'<i class="ty">{esc(str(q.get("concept") or ""))}</i></span>')


def topic_table(rows):
    """Questions per syllabus topic — the distribution, without difficulty."""
    c = Counter(t for q in rows for t in topics_of(q))
    n = sum(c.values())
    body = "".join(f'<tr><td>{esc(t)}</td><td class="n"><b>{v}</b></td></tr>'
                   for t, v in c.most_common())
    note = ("एक प्रश्न एक से अधिक विषय छू सकता है, अतः विषय-योग %d है। " % n) if n != len(rows) else ""
    return (f'<table class="cov"><caption>विषय-वार वितरण / Topic distribution — '
            f'{len(rows)} प्रश्न, {len(c)} विषय। {note}</caption>'
            f'<tr><th>विषय / Topic</th><th class="n">प्रश्न</th></tr>{body}</table>')


def ops(o_list):
    return '<div class="ops">' + "".join(
        f'<span class="op"><b>({o["label"]})</b> {mathify(esc(o["text"]))}</span>'
        for o in o_list) + "</div>"


def qblock(i, q):
    hi = (q.get("stem_hi") or "").strip()
    en = (q["stem"] or "").strip()
    same = (not hi) or mathify(esc(hi)) == mathify(esc(en))
    r = ['<div class="q">', badge(q)]
    if same:
        # One block, emitted as ENGLISH so the harness can still read and re-solve it. A pure
        # symbol question ("2 : 5 :: 10 : ?") has no words to translate.
        r.append(f'<div class="en"><span class="n">{i}.</span> '
                 f'{mathify(esc(en)).replace(chr(10), "<br>")}</div>{ops(q["options"])}')
    else:
        r.append(f'<div class="hi"><span class="n">{i}.</span> '
                 f'{mathify(esc(hi)).replace(chr(10), "<br>")}</div>{ops(q["options"])}')
        r.append(f'<div class="en">{mathify(esc(en)).replace(chr(10), "<br>")}</div>'
                 f'{ops(q["options"])}')
    return "".join(r) + "</div>"


if __name__ == "__main__":
    src = io.open(HERE / "OneStep_BSSC_InterLevel_STD_TAGGED.html", encoding="utf-8").read()
    head = src[:src.index("<body")]
    # the standard preamble: cover, scheme, syllabus, qualifying marks, meta line, instructions
    # Anchor on the PART header, not on the first <h2 class="sec">. The cover page's own headings
    # ("परीक्षा की योजना", "आधिकारिक पाठ्यक्रम", "न्यूनतम अर्हतांक") use the same class, so slicing
    # to the first one cut the preamble off before the instructions and the meta line — and losing
    # the meta line made the paper unparseable by test_papers.
    preamble = src[src.index("<body") + len("<body>"):src.index('<h2 class="sec">भाग')]

    out, allkeys, n = ['<div class="wrap">' if '<div class="wrap">' not in preamble else ""], [], 0
    out.append(preamble)
    for title, stem in SECTIONS:
        rows = json.load(io.open(HERE / f"{stem}.json", encoding="utf-8"))
        out.append(f'<h2 class="sec">{esc(title)}</h2>')
        out.append('<div class="pnote">इस भाग के 50 प्रश्न Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं '
                   '· ये विगत परीक्षा के प्रश्न नहीं हैं।</div>')
        out.append(topic_table(rows))
        for q in rows:
            n += 1
            out.append(qblock(n, q))
            allkeys.append((q["correct_answer"], bool(q.get("_generated", True))))
    # keyhead is what test_papers.parse() looks ahead for to close the LAST question block;
    # <i>*</i> marks a question generated, without which the re-solve check runs on an empty set.
    out.append('<div class="keyhead"></div>'
               '<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2><div class="keys">' + "".join(
                   # the asterisk means GENERATED and independently re-solved. A real commission
                   # question carries the commission's OWN answer key instead, so marking it
                   # generated would claim a verification we did not perform.
                   f'<span class="k">{i}. <b>{k}</b>{"<i>*</i>" if g else ""}</span>'
                   for i, (k, g) in enumerate(allkeys, 1)) + '</div></div>')
    hp = HERE / "OneStep_BSSC_HARD_SET_150.html"
    io.open(hp, "w", encoding="utf-8").write(head + "<body>" + "".join(out) + "</body></html>")
    print(f"{n} questions, {len(allkeys)} key entries")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={HERE / 'OneStep_BSSC_HARD_SET_150.pdf'}", hp.as_uri()],
                       capture_output=True, timeout=300)
    print("-> OneStep_BSSC_HARD_SET_150.html / .pdf")
