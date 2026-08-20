#!/usr/bin/env python3
"""BPSC CCE (Prelims) practice paper for One Step Education — built from REAL past questions.

Deliberately different from the BSSC builder:
  * BPSC prelims is ONE undivided General Studies paper, not three sections.
  * 150 questions, 1 mark each (150 marks), 2 hours — NOT the 4-mark/600 BSSC scheme.
  * Every question here is `generated=0` — an actual past-paper question, not authored by us.
  * Option order is NOT shuffled. For real PYQs the option order is part of the question, and the
    answer distribution is already healthy (A27 B28 C25 D19), so shuffling would only reduce
    authenticity. (The shuffle exists for the ingested banks whose answer sits at A ~96% of the time.)
"""
import base64, json, pathlib, subprocess, html, io

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
logo = base64.b64encode((REPO / "brand_logo/pack/trigunai_mark_chrome.png").read_bytes()).decode()
qs = json.load(io.open("/tmp/bpsc_raw.json", encoding="utf-8"))

LET = ["A", "B", "C", "D", "E"]
qhtml, keys = [], []
for i, q in enumerate(qs, 1):
    opts = q.get("options") or []
    o = "".join(f'<span class="op"><b>({LET[j].lower()})</b> {html.escape(str(op.get("text","")))}</span>'
                for j, op in enumerate(opts))
    qhtml.append(f'<div class="q"><span class="n">{i}.</span> '
                 f'<span class="t">{html.escape(str(q.get("stem","")))}</span>'
                 f'<div class="ops">{o}</div></div>')
    keys.append(f'<span class="k">{i}. <b>{html.escape(str(q.get("correct_answer","")).strip().lower())}</b></span>')

LETHEAD = f"""<div class="lh"><img class="mark" src="data:image/png;base64,{logo}">
<div><div class="co">ONE STEP EDUCATION &middot; PATNA</div>
<div class="sub">बिहार लोक सेवा आयोग &mdash; संयुक्त प्रतियोगिता (प्रारंभिक) परीक्षा &middot; सामान्य अध्ययन</div>
<div class="sub">अभ्यास प्रश्न-पत्र &mdash; <b>पिछले वर्षों के वास्तविक प्रश्नों पर आधारित</b> &middot; Set&ndash;1</div></div></div>
<div class="rule"></div>"""

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:13mm 12mm 14mm 12mm; }}
body {{ font-family:'Helvetica Neue',Arial,sans-serif; color:#1a1c24; font-size:9.4pt; line-height:1.38; margin:0; }}
.lh {{ display:flex; align-items:center; gap:12px; }} .lh .mark {{ width:52px; }}
.co {{ font-size:13pt; font-weight:700; letter-spacing:.3px; }}
.sub {{ font-size:8pt; color:#5a5f6e; margin-top:1px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227,#8a6d1a 55%,#c9a227); margin:8px 0 10px; border-radius:2px; }}
.meta {{ display:flex; justify-content:space-between; font-size:8.6pt; color:#4a4f5e;
        border:1px solid #e0dccc; background:#faf8f1; border-radius:4px; padding:7px 10px; margin-bottom:9px; }}
.inst {{ font-size:8.4pt; border:1px solid #e0dccc; border-radius:4px; padding:8px 10px; margin-bottom:12px; }}
.inst b {{ color:#8a6d1a; }}
.q {{ margin:0 0 7px; page-break-inside:avoid; }}
.q .n {{ font-weight:700; margin-right:3px; }}
.ops {{ margin:2px 0 0 14px; }}
.op {{ display:inline-block; min-width:47%; padding-right:6px; vertical-align:top; }}
.keyhead {{ page-break-before:always; }}
h2.sec {{ font-size:10.5pt; color:#8a6d1a; border-left:3px solid #c9a227; padding-left:7px; margin:14px 0 7px; }}
.keys {{ display:flex; flex-wrap:wrap; gap:3px 14px; font-size:9pt; }} .k {{ min-width:56px; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:14px; padding-top:4px; font-size:7.4pt; color:#9296a2; text-align:center; }}
table {{ border-collapse:collapse; margin:3px 0; font-size:8.8pt; }}
td, th {{ border:1px solid #d7d3c4; padding:2px 5px; }}
</style></head><body>
{LETHEAD}
<div class="meta"><span><b>कुल प्रश्न:</b> {len(qs)}</span>
<span><b>पूर्णांक:</b> {len(qs)}</span>
<span><b>समय:</b> 2 घंटे</span>
<span><b>अनुक्रमांक / Roll No.:</b> __________</span></div>
<div class="inst">
<b>महत्वपूर्ण निर्देश / IMPORTANT INSTRUCTIONS</b><br>
1. इस प्रश्न-पत्र में <b>सामान्य अध्ययन</b> के कुल <b>{len(qs)} वस्तुनिष्ठ प्रश्न</b> हैं। प्रश्न-पत्र भागों में विभाजित नहीं है।<br>
2. प्रत्येक <b>सही उत्तर के लिए 1 अंक</b> दिया जाएगा। प्रत्येक प्रश्न के दिए गए विकल्पों में से <b>केवल एक</b> सही है।<br>
3. उत्तर OMR उत्तर-पत्रक पर काले/नीले बॉलपॉइंट पेन से ही अंकित करें।<br>
4. प्रारंभिक परीक्षा केवल <b>छँटनी (screening)</b> हेतु है; इसके अंक अंतिम मेधा-सूची में नहीं जुड़ते।<br>
5. <b>ऋणात्मक अंकन</b> के लिए आयोग की नवीनतम अधिसूचना देखें (हाल के चक्रों में लागू)।
</div>
<h2 class="sec">सामान्य अध्ययन / GENERAL STUDIES</h2>
{''.join(qhtml)}
<div class="keyhead">{LETHEAD}<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2>
<div class="keys">{''.join(keys)}</div>
<div class="foot">Answer key &mdash; for the teacher. Detach before distributing to students.</div></div>
<div class="foot">प्रश्न पिछले वर्षों की वास्तविक BPSC परीक्षाओं से लिए गए हैं &middot; संकलन: Acharya &middot; TrigunAI Innovations Pvt Ltd &middot; One Step Education, Patna</div>
</body></html>"""

out_html = REPO / "teacher_gtm/BPSC_150_OneStep.html"
out_html.write_text(HTML, encoding="utf-8")
out_pdf = REPO / "teacher_gtm/BPSC_150_OneStep.pdf"
for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",):
    if pathlib.Path(c).exists():
        subprocess.run([c, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out_pdf}", out_html.as_uri()], capture_output=True, timeout=240)
print("questions:", len(qs), "| pdf:", out_pdf, out_pdf.stat().st_size if out_pdf.exists() else "FAILED")
