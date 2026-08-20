#!/usr/bin/env python3
"""One Step Education — BSSC practice paper, 150 REAL bilingual questions.

Every question here was printed in an official BSSC paper and carries the commission's own
आदर्श उत्तर. Nothing is generated, nothing is translated: the Hindi is the Hindi the commission
printed, which is why each question shows both languages the way the real booklet does.

Section weights follow the measured blueprint of the five official papers we extracted
(GS ~38-51%, Maths ~20-31%, Hindi ~19-31%), NOT the textbook 50/50/50 — because Reasoning only
yielded 17 real questions and padding it with generated ones would break the "every question is
real" claim that makes this paper worth more than a competitor's mock.

Logo: pass --logo <path.png> to brand it with One Step's own mark; without it the name is set
in type. Never invent a client's logo.
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

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
sys.path.insert(0, str(REPO / "teacher_gtm"))
from paper_common import MATH_CSS, esc, servable, sig, inter_level_ok  # noqa: E402
LET = ["A", "B", "C", "D", "E"]


def load(inter_level=False):
    qs = []
    for f in glob.glob(str(REPO / "question_bank_engine/drop/bssc/*_KEYED.json")):
        for q in json.load(io.open(f, encoding="utf-8")):
            # servable() also drops the questions whose options are unusable — a bare option
            # LETTER as the text, or two identical options. 21 of these 497 are in that state and
            # 13 of them reached the first build of this paper.
            if not (q.get("tag") and servable(q, need_hindi=True)):
                continue
            # Advt 02/23(A) names an arithmetic-only maths syllabus. Our maths stock comes mostly
            # from Advt 0111, a CLERK exam whose paper ranged wider, so it carries polynomials,
            # APs, circle geometry, trigonometry and probability — above what an Inter Level
            # candidate is examined on. 34% of the maths pool is dropped here.
            if inter_level and not inter_level_ok(q):
                continue
            qs.append(q)
    return qs


def pick(pool, n, used, tmpl, cap=2):
    out = []
    random.shuffle(pool)
    for q in pool:
        if len(out) >= n:
            break
        qid = q.get("number"), q.get("source_pdf")
        if qid in used:
            continue
        k = sig(q["stem"])
        if tmpl.get(k, 0) >= cap:
            continue
        used.add(qid); tmpl[k] = tmpl.get(k, 0) + 1
        out.append(q)
    return out


def load_hindi_generated(n, cap_per_concept=6):
    """The Hindi Language section, from `hindigen` rather than from the real papers.

    This is a deliberate downgrade of the "every question is real" claim, made after rendering the
    real Hindi section and reading it. Hindi-LANGUAGE questions are the worst case for OCR: the
    question is ABOUT the Devanagari word, so a misread destroys it outright, and unlike a GS
    question there is no English twin to fall back on. What the real section actually printed:

        फिल्म में प्रायोगिक संधारण बताइए ?        (A) मिट्टी (B) मानव (C) इमारत (D) संपत्ति
        विशेषण शब्द को परिभाषित करें              (A) रेल (B) भेद (C) पटना (D) सड़क
        'मैं में दो जोड़ना' मुहावरा का क्या अर्थ होगा ?  (A) मैं में दो जोड़ना ...

    Roughly half the section read like that. `hindigen` is standard textbook grammar with correct
    answers ('लोहे के चने चबाना' -> 'बहुत कठिन काम करना'), so the section is right even though it is
    not a past question. Pass --hindi-source real to print the original anyway.

    Still open: a native Hindi reader has not reviewed hindigen's tables (skill §11 item 2).
    """
    p = REPO / "question_bank_engine/drop/bssc/HINDI_GEN.json"
    if not p.exists():
        return []
    buckets = {}
    for q in json.load(io.open(p, encoding="utf-8")):
        if not (q.get("stem") and q.get("correct_answer") and len(q.get("options") or []) == 4):
            continue
        q["_generated"] = True
        buckets.setdefault(q.get("concept") or "?", []).append(q)
    for b in buckets.values():
        random.shuffle(b)
    order = sorted(buckets, key=lambda k: -len(buckets[k]))
    out, rnd = [], 0
    while len(out) < n and rnd < cap_per_concept:
        for k in order:
            if len(out) >= n:
                break
            if len(buckets[k]) > rnd:
                out.append(buckets[k][rnd])
        rnd += 1
    return out[:n]


def load_generated(n, cap_per_concept=3):
    """Bilingual reasoning with COMPUTED answers, only used by --structure official3.

    Capped and dealt round-robin BY CONCEPT, not by stem text: three direction questions read
    "facing North, right then left" / "facing East, right then left" / "facing North, left then
    right" — different words, so a stem-signature cap lets all three onto one page, which is
    exactly what happened the first time.
    """
    p = REPO / "question_bank_engine/drop/bssc/REASONING_GEN.json"
    if not p.exists():
        return []
    buckets = {}
    for q in json.load(io.open(p, encoding="utf-8")):
        if not (q.get("stem") and q.get("correct_answer") and len(q.get("options") or []) == 4):
            continue
        q["_generated"] = True
        buckets.setdefault(q.get("concept") or "?", []).append(q)
    for b in buckets.values():
        random.shuffle(b)
    order = sorted(buckets, key=lambda k: -len(buckets[k]))
    # Raise the per-concept cap only as far as the request forces. With 11 concepts a cap of 3
    # tops out at 33, so a 35-question Part III silently came back short — the paper printed 148.
    if order:
        cap_per_concept = max(cap_per_concept, -(-n // len(order)))
    out, rnd = [], 0
    while len(out) < n and rnd < cap_per_concept:
        for k in order:
            if len(out) >= n:
                break
            if len(buckets[k]) > rnd:
                out.append(buckets[k][rnd])
        rnd += 1
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", default=None, help="path to the institute's logo PNG")
    ap.add_argument("--out", default=str(REPO / "teacher_gtm/OneStep_BSSC_150.pdf"))
    ap.add_argument("--structure", choices=["real4", "official3"], default="real4",
                    help="real4 = 100%% real, 4 parts shaped to what the papers actually contain "
                         "(GS/Sci+Maths/Hindi/Reasoning). official3 = the commission's 3x50 "
                         "layout, which needs ~35 GENERATED reasoning questions to fill Part III.")
    ap.add_argument("--inter-level", action="store_true",
                    help="Build for BSSC 2nd Inter Level (Advt 02/23-A). Forces the commission's "
                         "OWN three-section prelim structure — GS / Science+Maths / Mental Ability, "
                         "with NO Hindi Language section, because the official syllabus does not "
                         "have one — and drops maths that is above the Inter Level syllabus.")
    ap.add_argument("--hindi-source", choices=["generated", "real"], default="generated",
                    help="Which Hindi Language section to print. DEFAULT IS 'generated' because "
                         "the REAL Hindi-language questions in these papers are badly OCR-corrupted "
                         "- see the note in load_hindi_generated().")
    a = ap.parse_args()

    random.seed(20260820)
    qs = load(inter_level=a.inter_level)
    by = {}
    for q in qs:
        by.setdefault(q["tag"]["section"], []).append(q)

    used, tmpl = set(), {}
    if a.inter_level:
        a.structure = "official3"
    if a.structure == "real4":
        # The shape the PAPERS actually have. These five are 10th/8th-level and clerk-grade exams,
        # and the measured blueprints put Hindi at 19-31% of three of them and Reasoning at 0%.
        # A 4-part paper is therefore closer to what these candidates sat than the 3x50 template,
        # and — the reason it was chosen — it can be filled ENTIRELY with real questions.
        SPEC = [
            ("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", ["General Studies"], 50),
            ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (General Science & Mathematics)",
             ["Mathematics", "General Science"], 50),
            ("भाग–III / PART–III : हिंदी भाषा (Hindi Language)", ["Hindi"], 33),
            ("भाग–IV / PART–IV : सामान्य बुद्धि परीक्षण (Reasoning)", ["Reasoning", "English"], 17),
        ]
    else:
        # The commission's printed CGL / Inter-Level layout. Only 15 real bilingual reasoning
        # questions exist, so Part III is topped up from `reasoninggen` — computed answers, and
        # bilingual, so the paper stays bilingual throughout. This trades the "every question is
        # real" claim for the official shape; that is why it is not the default.
        # खंड (ग) मानसिक क्षमता जाँच lists ONLY reasoning shapes — सादृश्य, समानता एवं भिन्नता,
        # स्थान कल्पना, समस्या समाधान, विश्लेषण, दृश्य स्मृति, विभेद, अवलोकन, संबंध अवधारणा,
        # अंक गणितीय तर्कशक्ति, अंक गणितीय संख्या श्रृंखला, कूट लेखन एवं कूट व्याख्या. English
        # grammar/vocabulary is NOT among them, so it is excluded for an Inter Level paper even
        # though we hold 16 such real questions.
        third = ["Reasoning"] if a.inter_level else ["Reasoning", "English"]
        SPEC = [
            ("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", ["General Studies"], 50),
            ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (General Science & Mathematics)",
             ["Mathematics", "General Science"], 50),
            ("भाग–III / PART–III : मानसिक क्षमता जाँच (Mental Ability / Reasoning)", third, 50),
        ]

    paper, n = [], 0
    for title, secs, want in SPEC:
        pool = [q for s in secs for q in by.get(s, [])]
        got = pick(pool, want, used, tmpl)
        if a.structure == "official3" and len(got) < want:
            got += load_generated(want - len(got))
        if secs == ["Hindi"] and a.hindi_source == "generated":
            got = load_hindi_generated(want)
        paper.append((title, got)); n += len(got)

    logo_html = ""
    if a.logo and os.path.exists(a.logo):
        b64 = base64.b64encode(open(a.logo, "rb").read()).decode()
        ext = "png" if a.logo.lower().endswith("png") else "jpeg"
        logo_html = f'<img class="logo" src="data:image/{ext};base64,{b64}">'

    # The vision extraction was not consistent about WHICH field held which language: measured
    # across 497 pairs, only 59% were correct, 12% arrived swapped and 27% held Hindi in both.
    # Rendering by field name therefore printed some questions twice and some back-to-front.
    # Route by SCRIPT instead — Devanagari is Hindi, full stop — and print a language only once.
    DEV = re.compile(r"[\u0900-\u097f]")
    # "A 30 (B) 35 (C) 38 (D) 40" — an option list sitting in a stem field.
    OPTLIST = re.compile(r"\(?[Aa]\)?\s.{0,40}?\([Bb]\).{0,40}?\([Cc]\)")

    def split_lang(a, b):
        """(hindi, english) from two texts whose labels we do not trust."""
        a, b = (a or "").strip(), (b or "").strip()
        da, db = bool(DEV.search(a)), bool(DEV.search(b))
        if da and not db:
            return a, b
        if db and not da:
            return b, a
        if da and db:
            return (a if len(a) >= len(b) else b), ""      # both Hindi -> show once
        return "", (a if len(a) >= len(b) else b)          # both English -> show once

    n_gen = sum(1 for _, items in paper for q in items if q.get("_generated"))
    qh, keys, i = [], [], 0
    for title, items in paper:
        g = sum(1 for q in items if q.get("_generated"))
        note = ('<div class="pnote">इस भाग के सभी प्रश्न BSSC की आधिकारिक विगत परीक्षाओं से '
                '&middot; उत्तर आयोग की आदर्श उत्तर कुंजी से।</div>') if not g else (
               f'<div class="pnote">इस भाग के {g} प्रश्न Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं '
               f'(मानक व्याकरण पर आधारित) &middot; ये विगत परीक्षा के प्रश्न नहीं हैं।</div>')
        qh.append(f'<h2 class="sec">{html.escape(title)}</h2>{note}')
        for q in items:
            i += 1
            # Some stems in the 8th-Level paper are not stems at all — the extractor put the OPTION
            # LIST in the field ("A 30 (B) 35 (C) 38 (D) 40"). Printed, that is a junk line above
            # the real options. Blank it and let the other language carry the question.
            hi_raw, en_raw = q.get("stem_hi"), q.get("stem")
            if OPTLIST.search(hi_raw or ""):
                hi_raw = ""
            if OPTLIST.search(en_raw or ""):
                en_raw = ""
            hi_stem, en_stem = split_lang(hi_raw, en_raw)
            oh_l, oe_l = [], []
            for oa, ob in zip(q.get("options_hi") or q["options"], q["options"]):
                h, e = split_lang(oa.get("text"), ob.get("text"))
                oh_l.append((oa["label"], h)); oe_l.append((ob["label"], e))
            def render(pairs):
                return "".join(f'<span class="op"><b>({lb})</b> {esc(t)}</span>'
                               for lb, t in pairs if str(t).strip())
            oh_html, oe_html = render(oh_l), render(oe_l)
            # A language can lose SOME options, not just all of them: when split_lang routes option
            # (A) and (C) one way and (B) and (D) the other, one block prints two options and the
            # question is unanswerable. Only a FULL set is acceptable, so fall back whenever the
            # rendered count is short.
            want = len(q["options"])
            if oh_html.count("<span class=\"op\">") < want:
                oh_html = oe_html if oe_html.count("<span class=\"op\">") == want else ""
            if oe_html.count("<span class=\"op\">") < want:
                oe_html = oh_html if oh_html.count("<span class=\"op\">") == want else ""
            # When the options are language-NEUTRAL (numbers, formulae, single letters) split_lang
            # hands both copies to the English side, so a Hindi-only question rendered its options
            # block EMPTY and never rendered an English block — 26 of 470 questions showed a stem
            # with no options at all. Numbers read the same in both scripts, so reuse them.
            if not oh_html:
                oh_html = oe_html
            if not oe_html:
                oe_html = oh_html
            if not oh_html and not oe_html:      # nothing renderable at all — skip the question
                i -= 1
                continue
            block = f'<div class="q">'
            if hi_stem:
                block += (f'<div class="hi"><span class="n">{i}.</span> {esc(hi_stem)}</div>'
                          f'<div class="ops">{oh_html}</div>')
            if en_stem:
                lead = "" if hi_stem else f'<span class="n">{i}.</span> '
                block += (f'<div class="en">{lead}{esc(en_stem)}</div>'
                          f'<div class="ops">{oe_html}</div>')
            qh.append(block + "</div>")
            keys.append(f'<span class="k">{i}. <b>{q["correct_answer"]}</b>'
                        f'{"<i>*</i>" if q.get("_generated") else ""}</span>')

    TITLE_LINE = ("बिहार कर्मचारी चयन आयोग &mdash; द्वितीय इंटर स्तरीय संयुक्त प्रतियोगिता परीक्षा "
                  "(वि0सं0&ndash;02/23-A) &mdash; अभ्यास प्रश्न-पत्र" if a.inter_level
                  else "बिहार कर्मचारी चयन आयोग (BSSC) &mdash; अभ्यास प्रश्न-पत्र")
    PATTERN_NOTE = ("<br>5. यह प्रश्न-पत्र आयोग द्वारा वि0सं0&ndash;02/23(A) में प्रकाशित "
                    "<b>प्रारंभिक परीक्षा की योजना</b> के अनुरूप है &mdash; 150 प्रश्न, "
                    "प्रत्येक सही उत्तर 4 अंक, प्रत्येक गलत उत्तर &ndash;1, कुल 600 अंक, समय 2 घंटा 15 मिनट, "
                    "तीन खण्ड। गणित के प्रश्न आयोग के <b>अंकगणित-आधारित</b> पाठ्यक्रम तक सीमित रखे गए हैं।"
                    if a.inter_level else "")
    HEAD = f"""<div class="lh">{logo_html}<div>
<div class="co">ONE STEP EDUCATION</div><div class="sub2">PATNA</div>
<div class="sub">{TITLE_LINE}</div>
<div class="sub"><b>भाग I, II एवं IV: आयोग के वास्तविक विगत प्रश्न</b> &middot; आदर्श उत्तर कुंजी सहित</div>
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
.pnote {{ font-size:7.4pt; color:#8d8676; margin:0 0 7px 10px; page-break-after:avoid; }}
h2.sec {{ font-size:10.5pt; color:#8a6d1a; border-left:3px solid #c9a227; padding-left:7px;
         margin:14px 0 3px; page-break-after:avoid; }}
.q {{ margin:0 0 9px; page-break-inside:avoid; }}
.q .n {{ font-weight:800; margin-right:3px; }}
.hi {{ font-weight:500; }}
.en {{ color:#3a3f4e; margin-top:2px; }}
.ops {{ margin:1px 0 2px 15px; }}
.op {{ display:inline-block; min-width:47%; padding-right:6px; vertical-align:top; }}
{MATH_CSS}
.keyhead {{ page-break-before:always; }}
.keys {{ display:flex; flex-wrap:wrap; gap:3px 14px; font-size:9pt; }} .k {{ min-width:54px; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:12px; padding-top:4px; font-size:7.3pt; color:#9296a2; text-align:center; }}
</style></head><body>
{HEAD}
<div class="meta"><span><b>कुल प्रश्न:</b> {n}</span><span><b>पूर्णांक:</b> {n * 4}</span>
<span><b>समय:</b> 2 घंटे 15 मिनट</span><span><b>नाम:</b> ____________</span>
<span><b>अनुक्रमांक:</b> ________</span></div>
<div class="inst">
<b>निर्देश / INSTRUCTIONS</b><br>
1. सभी प्रश्न वस्तुनिष्ठ हैं। प्रत्येक प्रश्न <b>हिंदी एवं अंग्रेज़ी</b> दोनों में दिया गया है &mdash; किसी एक भाषा में पढ़कर उत्तर दें।<br>
2. प्रत्येक <b>सही उत्तर के लिए 4 अंक</b>; प्रत्येक <b>गलत उत्तर के लिए 1 अंक</b> काटा जाएगा।<br>
3. दिए गए विकल्पों में से <b>केवल एक</b> सही है। उत्तर OMR पत्रक पर काले/नीले बॉलपॉइंट पेन से भरें।<br>
4. जिन भागों में <b>*</b> चिह्नित प्रश्न हैं वे Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं; शेष सभी
   प्रश्न BSSC की <b>आधिकारिक विगत परीक्षाओं</b> से हैं और उत्तर आयोग की <b>आदर्श उत्तर कुंजी</b> से।{PATTERN_NOTE}
</div>
{''.join(qh)}
<div class="keyhead">{HEAD}<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2>
<div class="keys">{''.join(keys)}</div>
<div class="foot">* = Acharya द्वारा निर्मित अभ्यास-प्रश्न &middot; शेष सभी आयोग की आदर्श उत्तर कुंजी से।<br>
शिक्षक हेतु &mdash; विद्यार्थियों को देने से पूर्व यह पृष्ठ अलग कर लें।</div></div>
<div class="foot">One Step Education, Patna &middot; संकलन: Acharya (TrigunAI Innovations Pvt Ltd)</div>
</body></html>"""

    # follow --out; this was hardcoded, so building a second paper silently overwrote
    # the first one's HTML while its PDF sat elsewhere.
    out_html = pathlib.Path(str(a.out).replace(".pdf", ".html")).resolve()
    out_html.write_text(HTML, encoding="utf-8")
    pdf = pathlib.Path(a.out).resolve()
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", out_html.as_uri()], capture_output=True, timeout=300)
    for t, items in paper:
        print(f"  {t[:52]:54s} {len(items):3d}")
    print(f"\n{n} bilingual questions | {n - n_gen} REAL official + {n_gen} generated "
          f"| logo: {'yes' if logo_html else 'TEXT ONLY'} | {pdf}")


if __name__ == "__main__":
    main()
