#!/usr/bin/env python3
"""Build the One Step Education BSSC Inter-Level prelims mock (150 Q) as a print-ready PDF."""
import base64, json, pathlib, subprocess, html, io

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
logo = base64.b64encode((REPO / "brand_logo/pack/trigunai_mark_chrome.png").read_bytes()).decode()
paper = json.load(io.open("/tmp/bssc_paper.json", encoding="utf-8"))

LET = f"""<div class="lh"><img class="mark" src="data:image/png;base64,{logo}">
<div><div class="co">ONE STEP EDUCATION &middot; PATNA</div>
<div class="sub">बिहार कर्मचारी चयन आयोग &mdash; द्वितीय इंटर स्तरीय संयुक्त प्रतियोगिता (प्रारंभिक) परीक्षा</div>
<div class="sub">अभ्यास प्रश्न-पत्र / PRACTICE QUESTION BOOKLET &middot; Set&ndash;1 &middot; Series&nbsp;A</div></div></div>
<div class="rule"></div>"""

LETTERS = ["A", "B", "C", "D", "E"]
qhtml, key_rows, n = [], [], 0
for title, qs in paper:
    qhtml.append(f'<h2 class="sec">{html.escape(title)}</h2>')
    for q in qs:
        n += 1
        opts = q.get("options") or []
        o = "".join(
            f'<span class="op"><b>({html.escape(str(op.get("label") or LETTERS[i]))})</b> '
            f'{html.escape(str(op.get("text","")))}</span>'
            for i, op in enumerate(opts))
        qhtml.append(f'<div class="q"><span class="n">{n}.</span> '
                     f'<span class="t">{html.escape(str(q.get("stem","")))}</span>'
                     f'<div class="ops">{o}</div></div>')
        key_rows.append(f'<span class="k">{n}. <b>{html.escape(str(q.get("correct_answer","")).strip())}</b></span>')

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
h2.sec {{ font-size:10.5pt; color:#8a6d1a; border-left:3px solid #c9a227; padding-left:7px;
         margin:14px 0 7px; page-break-after:avoid; }}
.q {{ margin:0 0 7px; page-break-inside:avoid; }}
.q .n {{ font-weight:700; margin-right:3px; }}
.ops {{ margin:2px 0 0 14px; }}
.op {{ display:inline-block; min-width:47%; padding-right:6px; vertical-align:top; }}
.keyhead {{ page-break-before:always; }}
.keys {{ display:flex; flex-wrap:wrap; gap:3px 14px; font-size:9pt; }}
.k {{ min-width:56px; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:14px; padding-top:4px; font-size:7.4pt; color:#9296a2; text-align:center; }}
</style></head><body>
{LET}
<div class="meta"><span><b>कुल प्रश्न:</b> {n}</span>
<span><b>पूर्णांक / Max Marks:</b> {n * 4}</span>
<span><b>समय:</b> 2 घंटे 15 मिनट</span>
<span><b>अनुक्रमांक / Roll No.:</b> __________</span></div>
<div class="inst">
<b>महत्वपूर्ण निर्देश / IMPORTANT INSTRUCTIONS</b><br>
1. यह प्रश्न-पुस्तिका <b>तीन भागों</b> में विभाजित है &mdash; भाग&ndash;I, भाग&ndash;II तथा भाग&ndash;III।
भाग&ndash;I में सामान्य अध्ययन, भाग&ndash;II में सामान्य विज्ञान एवं गणित तथा भाग&ndash;III में सामान्य बुद्धि परीक्षण के प्रश्न हैं।<br>
2. भाग&ndash;I में प्रश्न संख्या <b>1 से 50</b>, भाग&ndash;II में <b>51 से 100</b> तथा भाग&ndash;III में <b>101 से 150</b> तक हैं।<br>
3. प्रत्येक <b>सही उत्तर के लिए 4 अंक</b>। &nbsp;&nbsp; 4. प्रत्येक <b>गलत उत्तर के लिए 1 अंक काटा जाएगा</b> (ऋणात्मक अंकन)।<br>
5. सभी प्रश्न वस्तुनिष्ठ हैं; दिए गए विकल्पों में से <b>केवल एक</b> सही है।<br>
6. उत्तर OMR उत्तर-पत्रक पर काले/नीले बॉलपॉइंट पेन से ही अंकित करें।<br>
7. वास्तविक परीक्षा <b>कंप्यूटर आधारित (CBT)</b> होती है; यह अभ्यास हेतु मुद्रित प्रारूप है।
</div>
{''.join(qhtml)}
<div class="keyhead">{LET}<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2>
<div class="keys">{''.join(key_rows)}</div>
<div class="foot">Answer key &mdash; for the teacher. Detach before distributing to students.</div></div>
<div class="foot">Prepared by Acharya &middot; TrigunAI Innovations Pvt Ltd &middot; for One Step Education, Patna</div>
</body></html>"""

out_html = REPO / "teacher_gtm/BSSC_150_OneStep.html"
out_html.write_text(HTML, encoding="utf-8")
out_pdf = REPO / "teacher_gtm/BSSC_150_OneStep.pdf"
for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",):
    if pathlib.Path(c).exists():
        subprocess.run([c, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out_pdf}", out_html.as_uri()],
                       capture_output=True, timeout=240)
print("questions:", n, "| pdf:", out_pdf, out_pdf.stat().st_size if out_pdf.exists() else "FAILED")
