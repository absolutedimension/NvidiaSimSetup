#!/usr/bin/env python3
"""BSSC 150-question practice paper built from the NEWLY EXTRACTED stock (2026-08-20).

This is a companion to `build_onestep_paper.py`, not a replacement, and the difference matters:

  build_onestep_paper.py  -> the five 2022-25 papers. BILINGUAL, 100% real. Use it when the
                             institute needs Hindi.
  this script             -> the 2016-18 papers extracted on 2026-08-20. ENGLISH-ONLY, because
                             the Hindi from those scans is quarantined (see the skill's gotcha
                             #15 — vision garbles Devanagari proper nouns on those scans, and a
                             wrong name in a Hindi option is the first thing a Bihar reader spots).

Why English-only is still worth shipping: the new stock is what lifted real General Studies from
259 to 631 questions, so this is the paper that could not be built before. Every question in Parts
I and II is a question the commission actually printed, and every answer is the commission's own
आदर्श उत्तर — transcribed BY HAND, because the machine read of those key pages was 40% wrong.

PART III IS THE ONE COMPROMISE, AND IT IS LABELLED ON THE PAPER. The real papers yielded only 20
reasoning questions, nowhere near the 50 a full-length BSSC paper needs. Rather than repeat 20
questions or drop the part, Part III is filled from `qbank.reasoninggen`, whose answers are
COMPUTED rather than asserted by a model — a direction question knows where you end up facing.
Those are bilingual, so Part III carries Hindi even though Parts I and II cannot.

Structure follows the official BSSC prelims: 3 parts x 50, 4 marks each (600), -1 negative,
2h15m, 4 options. Do NOT use the 5-option BPSC TRE layout here.

Usage:
    python3 build_bssc_150_newstock.py [--logo teacher_gtm/onestep_logo.png] [--out out.pdf]
"""
import argparse
import base64
import glob
import html
import io
import json
import os
import pathlib
import random
import re
import subprocess
import sys
from collections import Counter

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
BSSC = REPO / "question_bank_engine/drop/bssc"
sys.path.insert(0, str(REPO / "question_bank_engine"))

# Post-specific subject papers. They tag as "General Studies" only because the taxonomy has no
# better bucket; a clerk candidate will never see a Pharmacy or Civil-Engineering question.
TECHNICAL = {"BSSC Chemistry", "BSSC Pharmacy",
             "BSSC JE Civil (Advt 0411)", "BSSC JE Mechanical (Advt 0411)"}

# The papers extracted on 2026-08-20 — "the new stock" this paper is built from.
NEW_SOURCES = {"GK1.PDF", "GK(3649).PDF", "G.K_and_N.A_M.A.PDF",
               "JE-0411-GK-QB-AND-MA.pdf", "maths.PDF"}

DEV = re.compile(r"[ऀ-ॿ]")


_GREEK = {"pi": "π", "theta": "θ", "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
          "lambda": "λ", "mu": "μ", "omega": "ω", "sigma": "σ", "phi": "φ"}
_OPS = {"times": "×", "div": "÷", "pm": "±", "mp": "∓", "le": "≤", "leq": "≤", "ge": "≥",
        "geq": "≥", "ne": "≠", "neq": "≠", "approx": "≈", "cdot": "·", "infty": "∞",
        "rightarrow": "→", "Rightarrow": "⇒", "circ": "°", "degree": "°", "%": "%"}


def mathify(text):
    """Turn the extracted LaTeX into something a student can read on paper.

    The maths booklet's questions carry real LaTeX (`\\frac{5}{9}`, `\\sqrt{2}`, `x^2`) because
    that is how the extractor was told to transcribe formulae. Printed verbatim it reads as
    "\\frac{5}{9}" on the page — worse than useless in an exam. There is no network in the headless
    print, so instead of a JS math renderer this maps the handful of constructs these papers
    actually use onto HTML and Unicode. Input MUST already be HTML-escaped; output contains tags.
    """
    t = str(text or "")
    t = t.replace("\\left", "").replace("\\right", "").replace("\\!", "").replace("\\,", " ")
    t = re.sub(r"\$+", "", t)
    for _ in range(3):                                   # nested fractions
        new = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
                     r'<span class="fr"><span class="nu">\1</span>'
                     r'<span class="de">\2</span></span>', t)
        if new == t:
            break
        t = new
    t = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r'<span class="rad">\1</span>', t)
    t = re.sub(r"\\sqrt\s*(\w)", r'<span class="rad">\1</span>', t)
    for k, v in list(_GREEK.items()) + list(_OPS.items()):
        t = re.sub(r"\\" + k + r"\b", v, t)
    t = re.sub(r"\^\s*\{([^{}]*)\}", r"<sup>\1</sup>", t)
    t = re.sub(r"\^\s*(-?\w)", r"<sup>\1</sup>", t)
    t = re.sub(r"_\s*\{([^{}]*)\}", r"<sub>\1</sub>", t)
    t = re.sub(r"_\s*(\w)", r"<sub>\1</sub>", t)
    t = t.replace("\\%", "%").replace("\\$", "$")
    t = re.sub(r"\\[a-zA-Z]+", "", t)                    # drop anything still unrecognised
    return t.replace("{", "").replace("}", "")


def esc(text):
    """Escape first, then typeset — so the maths becomes tags and the rest stays inert."""
    return mathify(html.escape(str(text or "")))


def servable(q):
    """A question we can actually put in front of a student.

    Beyond "has a stem, four options and an answer", two extraction defects have to be caught here
    or they reach the page. Both are rare (about 2% of the pool) and both are fatal to the question:

      - an option whose text is a bare option LETTER ("(D) A"), where the extractor swallowed the
        real text and kept a stray label;
      - two options with identical text, which makes the question unanswerable no matter what the
        official key says.

    Neither is repairable from the JSON — the words are simply not there — so the question is
    dropped. The pool is large enough that dropping 21 of 1,036 costs nothing.
    """
    if not (q.get("stem") and len(q.get("options") or []) == 4 and q.get("correct_answer")):
        return False
    texts = [re.sub(r"\s+", " ", str(o.get("text", ""))).strip() for o in q["options"]]
    if any(re.fullmatch(r"[A-Ea-e]", t) for t in texts):
        return False
    return len({t.lower() for t in texts}) == 4


def load_real():
    out = []
    for f in glob.glob(str(BSSC / "*_KEYED.json")):
        if "hindi1" in f:                 # Hindi-only booklet: no English, nothing servable
            continue
        rows = json.load(io.open(f, encoding="utf-8"))
        if not rows or (rows[0].get("paper_label") in TECHNICAL):
            continue
        for q in rows:
            if servable(q) and q.get("tag"):
                q["_new"] = q.get("source_pdf") in NEW_SOURCES
                out.append(q)
    return out


def sig(stem):
    """Collapse numbers so two clones of one template do not both land in the paper."""
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", stem or "")).strip()[:70]


def pick(pool, want, used, tmpl, cap=2, prefer_new=True):
    """Take `want` questions, newest stock first, never more than `cap` per template."""
    pool = list(pool)
    random.shuffle(pool)
    if prefer_new:
        pool.sort(key=lambda q: not q.get("_new"))     # stable: new stock first
    out = []
    for q in pool:
        if len(out) >= want:
            break
        qid = (q.get("number"), q.get("source_pdf"))
        if qid in used:
            continue
        k = sig(q["stem"])
        if tmpl.get(k, 0) >= cap:
            continue
        used.add(qid)
        tmpl[k] = tmpl.get(k, 0) + 1
        out.append(q)
    return out


def blueprint_pick(pool, want, used, tmpl):
    """Fill Part I to the topic mix MEASURED in the real papers, not an invented one.

    Without this the shuffle alone can hand a student 11 blood-relation questions in 50 — the exact
    failure that made us mine blueprints in the first place. Proportions come from the tagged real
    questions themselves, so the paper's shape is the exam's shape.
    """
    from tag_bssc import effective_topic
    mix = Counter(effective_topic(q["tag"]) for q in pool)
    total = sum(mix.values()) or 1
    out = []
    for topic, n in mix.most_common():
        quota = max(1, round(want * n / total))
        out += pick([q for q in pool if effective_topic(q["tag"]) == topic],
                    quota, used, tmpl)
        if len(out) >= want:
            break
    if len(out) < want:                                  # top up from whatever is left
        out += pick(pool, want - len(out), used, tmpl)
    return out[:want]


def load_generated(n, cap_per_concept=3):
    """Generated reasoning, spread across question TYPES.

    The stem-signature cap used elsewhere does not work here. Three direction questions read
    "facing North / take a right then a left", "facing East / a right then a left", "facing North /
    a left then a right" — different words, different signatures, and the first build duly put all
    three on one page. What actually repeats is the CONCEPT, so cap on that instead and deal the
    concepts round-robin so the part opens varied rather than front-loading one type.
    """
    p = BSSC / "REASONING_GEN.json"
    if not p.exists():
        return []
    qs = [q for q in json.load(io.open(p, encoding="utf-8"))
          if q.get("stem") and q.get("correct_answer") and len(q.get("options") or []) == 4]
    buckets = {}
    for q in qs:
        q["_generated"] = True
        buckets.setdefault(q.get("concept") or q.get("qtype") or "?", []).append(q)
    for b in buckets.values():
        random.shuffle(b)
    order = sorted(buckets, key=lambda k: -len(buckets[k]))
    out, round_i = [], 0
    while len(out) < n and round_i < cap_per_concept:
        for k in order:
            if len(out) >= n:
                break
            if len(buckets[k]) > round_i:
                out.append(buckets[k][round_i])
        round_i += 1
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", default=str(REPO / "teacher_gtm/onestep_logo.png"))
    ap.add_argument("--out", default=str(REPO / "teacher_gtm/BSSC_150_NewStock.pdf"))
    ap.add_argument("--institute", default="ONE STEP EDUCATION")
    ap.add_argument("--city", default="PATNA")
    a = ap.parse_args()

    random.seed(20260820)
    real = load_real()
    by = {}
    for q in real:
        by.setdefault(q["tag"]["section"], []).append(q)

    used, tmpl = set(), {}
    part1 = blueprint_pick(by.get("General Studies", []), 50, used, tmpl)
    part2 = pick(by.get("General Science", []) + by.get("Mathematics", []), 50, used, tmpl)
    part3 = pick(by.get("Reasoning", []), 50, used, tmpl)
    if len(part3) < 50:
        part3 += load_generated(50 - len(part3))

    PARTS = [
        ("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", part1),
        ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (General Science & Mathematics)", part2),
        ("भाग–III / PART–III : सामान्य बुद्धि परीक्षण (General Intelligence / Reasoning)", part3),
    ]
    n = sum(len(p) for _, p in PARTS)

    logo_html = ""
    if a.logo and os.path.exists(a.logo):
        b64 = base64.b64encode(open(a.logo, "rb").read()).decode()
        logo_html = f'<img class="logo" src="data:image/png;base64,{b64}">'

    qh, keys, i = [], [], 0
    n_gen = 0
    for title, items in PARTS:
        gen_here = sum(1 for q in items if q.get("_generated"))
        n_gen += gen_here
        note = ""
        if gen_here:
            note = (f'<div class="pnote">इस भाग के {gen_here} प्रश्न Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं '
                    f'(उत्तर गणना से प्राप्त, अनुमान से नहीं) &middot; शेष {len(items)-gen_here} आयोग के वास्तविक प्रश्न।</div>')
        else:
            note = ('<div class="pnote">इस भाग के सभी प्रश्न BSSC की आधिकारिक विगत परीक्षाओं से '
                    '&middot; उत्तर आयोग की आदर्श उत्तर कुंजी से।</div>')
        qh.append(f'<h2 class="sec">{html.escape(title)}</h2>{note}')
        for q in items:
            i += 1
            stem = (q.get("stem") or "").strip()
            hi = (q.get("stem_hi") or "").strip()
            # Only print Hindi when it is genuinely Devanagari AND trusted. The new stock's Hindi
            # is quarantined in stem_hi_unverified and must never reach this page.
            hi = hi if DEV.search(hi) else ""
            block = '<div class="q">'
            block += f'<div class="en"><span class="n">{i}.</span> {esc(stem)}</div>'
            block += ('<div class="ops">' + "".join(
                f'<span class="op"><b>({o["label"]})</b> {esc(o["text"])}</span>'
                for o in q["options"]) + "</div>")
            if hi:
                block += f'<div class="hi">{esc(hi)}</div>'
                oh = q.get("options_hi") or []
                if len(oh) == len(q["options"]):
                    block += ('<div class="ops">' + "".join(
                        f'<span class="op"><b>({o["label"]})</b> {esc(o["text"])}</span>'
                        for o in oh) + "</div>")
            qh.append(block + "</div>")
            src = "gen" if q.get("_generated") else ""
            keys.append(f'<span class="k">{i}. <b>{q["correct_answer"]}</b>'
                        f'{"<i>*</i>" if src else ""}</span>')

    HEAD = f"""<div class="lh">{logo_html}<div>
<div class="co">{html.escape(a.institute)}</div><div class="sub2">{html.escape(a.city)}</div>
<div class="sub">बिहार कर्मचारी चयन आयोग (BSSC) &mdash; पूर्ण अभ्यास प्रश्न-पत्र (150 प्रश्न)</div>
<div class="sub"><b>भाग I &amp; II: आयोग के वास्तविक विगत प्रश्न</b> &middot; आदर्श उत्तर कुंजी सहित</div>
</div></div><div class="rule"></div>"""

    HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:12mm 11mm 12mm 11mm; }}
body {{ font-family:'Helvetica Neue',Arial,sans-serif; color:#1a1c24; font-size:9pt; line-height:1.34; margin:0; }}
.lh {{ display:flex; align-items:center; gap:14px; }} .logo {{ width:74px; height:auto; }}
.co {{ font-size:16pt; font-weight:800; letter-spacing:.6px; color:#12141c; }}
.sub2 {{ font-size:9pt; letter-spacing:3px; color:#8a6d1a; font-weight:700; margin-top:-2px; }}
.sub {{ font-size:8pt; color:#5a5f6e; margin-top:2px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227,#8a6d1a 55%,#c9a227); margin:8px 0 10px; border-radius:2px; }}
.meta {{ display:flex; justify-content:space-between; font-size:8.4pt; color:#4a4f5e;
        border:1px solid #e0dccc; background:#faf8f1; border-radius:4px; padding:7px 10px; margin-bottom:8px; }}
.inst {{ font-size:8.2pt; border:1px solid #e0dccc; border-radius:4px; padding:8px 10px; margin-bottom:11px; }}
.inst b {{ color:#8a6d1a; }}
h2.sec {{ font-size:10.5pt; color:#8a6d1a; border-left:3px solid #c9a227; padding-left:7px;
         margin:14px 0 3px; page-break-after:avoid; }}
.pnote {{ font-size:7.4pt; color:#8d8676; margin:0 0 7px 10px; page-break-after:avoid; }}
.q {{ margin:0 0 9px; page-break-inside:avoid; }}
.q .n {{ font-weight:800; margin-right:3px; }}
.en {{ font-weight:500; }}
.hi {{ color:#3a3f4e; margin-top:2px; }}
.ops {{ margin:1px 0 2px 15px; }}
.op {{ display:inline-block; min-width:47%; padding-right:6px; vertical-align:top; }}
.fr {{ display:inline-block; vertical-align:middle; text-align:center; margin:0 2px; }}
.fr .nu {{ display:block; padding:0 3px; border-bottom:1px solid #1a1c24; line-height:1.15; }}
.fr .de {{ display:block; padding:0 3px; line-height:1.15; }}
.rad {{ border-top:1px solid #1a1c24; padding:0 2px; margin-left:1px; }}
.rad::before {{ content:"\\221A"; margin-left:-3px; border-top:0; }}
sup, sub {{ font-size:75%; }}
.keyhead {{ page-break-before:always; }}
.keys {{ display:flex; flex-wrap:wrap; gap:3px 14px; font-size:9pt; }} .k {{ min-width:56px; }}
.k i {{ color:#b08a1e; font-style:normal; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:12px; padding-top:4px; font-size:7.3pt; color:#9296a2; text-align:center; }}
</style></head><body>
{HEAD}
<div class="meta"><span><b>कुल प्रश्न:</b> {n}</span><span><b>पूर्णांक:</b> {n * 4}</span>
<span><b>समय:</b> 2 घंटे 15 मिनट</span><span><b>नाम:</b> ____________</span>
<span><b>अनुक्रमांक:</b> ________</span></div>
<div class="inst">
<b>निर्देश / INSTRUCTIONS</b><br>
1. कुल {n} प्रश्न, तीन भागों में। प्रत्येक <b>सही उत्तर के लिए 4 अंक</b>; प्रत्येक <b>गलत उत्तर के लिए 1 अंक</b> काटा जाएगा।<br>
2. दिए गए चार विकल्पों में से <b>केवल एक</b> सही है। उत्तर OMR पत्रक पर काले/नीले बॉलपॉइंट पेन से भरें।<br>
3. भाग I एवं II के प्रश्न BSSC की <b>आधिकारिक विगत परीक्षाओं</b> से लिए गए हैं और उत्तर आयोग की
   <b>आदर्श उत्तर कुंजी</b> पर आधारित हैं। ये प्रश्न मूल पुस्तिका में जिस रूप में छपे थे, उसी रूप में
   <b>अंग्रेज़ी</b> में दिए गए हैं।<br>
4. भाग III के {n_gen} प्रश्न Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं (हिंदी सहित); इनके उत्तर
   <b>गणना द्वारा</b> निकाले गए हैं।
</div>
{''.join(qh)}
<div class="keyhead">{HEAD}<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2>
<div class="keys">{''.join(keys)}</div>
<div class="foot">* = Acharya द्वारा निर्मित अभ्यास-प्रश्न (उत्तर गणना से) &middot; शेष सभी आयोग की आदर्श उत्तर कुंजी से।<br>
शिक्षक हेतु &mdash; विद्यार्थियों को देने से पूर्व यह पृष्ठ अलग कर लें।</div></div>
<div class="foot">{html.escape(a.institute)}, {html.escape(a.city)} &middot; संकलन: Acharya (TrigunAI Innovations Pvt Ltd)</div>
</body></html>"""

    out_html = pathlib.Path(str(a.out).replace(".pdf", ".html"))
    out_html.write_text(HTML, encoding="utf-8")
    pdf = pathlib.Path(a.out)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", out_html.as_uri()], capture_output=True, timeout=300)

    print(f"{'PART':62s} {'n':>3} {'real':>5} {'new':>4} {'gen':>4}")
    for t, items in PARTS:
        r = sum(1 for q in items if not q.get("_generated"))
        nw = sum(1 for q in items if q.get("_new"))
        g = sum(1 for q in items if q.get("_generated"))
        print(f"  {t[:60]:60s} {len(items):3d} {r:5d} {nw:4d} {g:4d}")
    print(f"\n{n} questions, {n*4} marks | {n-n_gen} real official + {n_gen} generated "
          f"| {sum(1 for _,it in PARTS for q in it if q.get('_new'))} from the NEW stock")
    print(f"-> {pdf}")


if __name__ == "__main__":
    main()
