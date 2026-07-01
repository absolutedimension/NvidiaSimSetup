#!/usr/bin/env python3
"""Render AI_TUTOR_PIPELINE.md into a branded 'Acharya' PDF.
Run with the venv python (has `markdown`):  /tmp/pdfvenv/bin/python build_acharya_pdf.py
Then weasyprint converts the HTML -> PDF.
"""
import re, os, subprocess, markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "AI_TUTOR_PIPELINE.md")
LOGO = os.path.join(ROOT, "brand_logo", "logo_gold.png")
HTML = os.path.join(ROOT, "tutor_rl", "Acharya_Tutor_Pipeline.html")
PDF = os.path.join(ROOT, "Acharya_Tutor_Pipeline.pdf")

md = open(SRC).read()
# strip the leading H1 + subtitle block (cover carries the title) — keep from the first '---'
md = md.split("\n---\n", 1)[1] if "\n---\n" in md else md

body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])

CSS = """
@page { size: A4; margin: 15mm 14mm; }
@page cover { margin: 0; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Arial, "Apple Color Emoji", sans-serif;
       color: #23222e; font-size: 9.6pt; line-height: 1.5;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }

/* ---------- COVER ---------- */
.cover { page: cover; height: 297mm; width: 210mm; background: #0E0E14; color: #EDE7D6;
         display: flex; flex-direction: column; align-items: center; justify-content: center;
         text-align: center; page-break-after: always; position: relative; }
.cover .glow { position:absolute; top:0; left:0; right:0; bottom:0;
   background: radial-gradient(circle at 50% 38%, rgba(212,162,58,0.16), rgba(14,14,20,0) 60%); }
.cover img { width: 120px; height: 120px; border-radius: 22px; margin-bottom: 26px; position: relative; }
.cover h1 { font-family: Georgia, "Times New Roman", serif; font-size: 52pt; letter-spacing: 2px;
   margin: 0; color: #E8C66B; font-weight: 600; position: relative; }
.cover .sanskrit { color:#b9a878; font-size: 11pt; letter-spacing: 6px; margin-top: 6px; text-transform: uppercase; }
.cover .rule { width: 120px; height: 2px; background: linear-gradient(90deg, transparent, #D4A23A, transparent);
   margin: 26px 0; position: relative; }
.cover h2 { font-family: Georgia, serif; font-weight: 400; font-size: 16pt; color: #EDE7D6;
   margin: 0 0 6px; position: relative; }
.cover .sub { color:#9b8f72; font-size: 10.5pt; max-width: 360px; position: relative; }
.cover .foot { position: absolute; bottom: 30mm; color:#7e745c; font-size: 9pt; letter-spacing: 1px; }
.cover .tag  { position:absolute; top: 26mm; color:#8a7c58; font-size:8.5pt; letter-spacing:3px; text-transform:uppercase; }

/* ---------- BODY ---------- */
h1 { font-family: Georgia, serif; color:#1C1B2E; font-size: 19pt; margin: 26px 0 4px;
     border-bottom: 2px solid #D4A23A; padding-bottom: 5px; }
h2 { font-family: Georgia, serif; color:#A9781C; font-size: 14pt; margin: 22px 0 6px; }
h3 { font-family: Georgia, serif; color:#1C1B2E; font-size: 11pt; margin: 16px 0 4px; }
h2, h3 { page-break-after: avoid; }
p { margin: 6px 0; }
a { color:#A9781C; text-decoration: none; }
strong { color:#1C1B2E; }
ul, ol { margin: 6px 0 6px 18px; padding: 0; }
li { margin: 3px 0; }
hr { border: none; border-top: 1px solid #e7ddc6; margin: 18px 0; }

blockquote { margin: 10px 0; padding: 8px 14px; background: #FBF6EA;
   border-left: 4px solid #D4A23A; color:#4a4738; font-style: italic; }

table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 8.8pt; page-break-inside: avoid; }
th { background: #1C1B2E; color:#EDE7D6; text-align: left; padding: 6px 8px; font-weight: 600; }
td { border-bottom: 1px solid #ece3cd; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #FBF8F1; }

pre { background: #0E0E14; color:#cfc6ad; font-family: "SF Mono","Menlo",monospace; font-size: 7.4pt;
   line-height: 1.4; padding: 11px 13px; border-radius: 6px; border-left: 3px solid #D4A23A;
   overflow: hidden; white-space: pre; page-break-inside: avoid; }
code { font-family: "SF Mono","Menlo",monospace; font-size: 8.4pt; background:#F3ECDB; color:#8a5a12;
   padding: 1px 4px; border-radius: 3px; }
pre code { background: none; color: inherit; padding: 0; font-size: 7.4pt; }
h2 { page-break-inside: avoid; }
"""

COVER = f"""
<div class="cover">
  <div class="glow"></div>
  <div class="tag">TrigunAI Innovations</div>
  <img src="file://{LOGO}" alt="TrigunAI"/>
  <h1>Acharya</h1>
  <div class="sanskrit">the guide · आचार्य</div>
  <div class="rule"></div>
  <h2>The TrigunAI Tutor Pipeline</h2>
  <div class="sub">How a live AI tutor and a reinforcement-learning engine
  teach — and keep getting better. The whole system, explained.</div>
  <div class="foot">Internal &amp; Confidential  ·  2026-06-29</div>
</div>
"""

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{COVER}{body}</body></html>"""
open(HTML, "w").write(html)
print("wrote", HTML)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--no-sandbox", "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=8000",
                f"--print-to-pdf={PDF}", f"file://{HTML}"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("wrote", PDF, os.path.getsize(PDF), "bytes")
