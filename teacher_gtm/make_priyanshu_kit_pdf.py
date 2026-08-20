#!/usr/bin/env python3
"""Build PRIYANSHU_ARA_FIELD_KIT.pdf — the whole Ara region-head kit as one printable book.

Concatenates the numbered reference docs from skills/ara-region-head/references/ in reading
order, with a cover page and a section break before each doc, in the Acharya dark-gold print
theme. Priyanshu reads this offline / on the road; the skill folder is the live version.

Renderer chain and the Chrome-never-exits gotcha are lifted from make_visit_list_pdf.py —
see the comment above render().
"""
import markdown, subprocess, pathlib, re, time

HERE = pathlib.Path(__file__).parent
REFS = HERE.parent / "skills" / "ara-region-head" / "references"
HTML = pathlib.Path("/tmp/priyanshu_kit.html")
PDF  = HERE / "PRIYANSHU_ARA_FIELD_KIT.pdf"

# Reading order. The shared background docs are deliberately left out of the printed book —
# they are long, they are already in the skill folder, and a 60-page PDF does not get read.
DOCS = [
    "00_START_HERE.md",
    "01_PRODUCT_MASTER.md",
    "02_ARA_MARKET_BRIEF.md",
    "05_PRICING_AND_OFFER.md",
    "04_DEMO_PLAYBOOK.md",
    "06_OBJECTIONS.md",
    "03_ARA_SOURCING_GUIDE.md",
    "09_FIRST_15_DAYS.md",
    "10_RULES_AND_ESCALATION.md",
    "11_YOUR_TERMS.md",
    "08_TEAM_BUILD_PLAYBOOK.md",
]

md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])

parts = []
for i, name in enumerate(DOCS):
    src = REFS / name
    if not src.exists():
        print(f"  !! missing {name} — skipped")
        continue
    md.reset()
    html = md.convert(src.read_text())
    # Headerless tables still emit an empty <thead>, which prints as a stray band.
    html = re.sub(r"<thead>\s*<tr>(?:\s*<th></th>)+\s*</tr>\s*</thead>", "", html)
    cls = "doc" if i == 0 else "doc newpage"
    parts.append(f'<div class="{cls}">{html}</div>')
    print(f"  ok  {name}")

body_html = "\n".join(parts)

full_html = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Acharya — Ara Field Kit — Priyanshu</title>
<style>
  @page { size: A4; margin: 16mm 14mm 24mm 14mm; }
  * { box-sizing: border-box; }
  body {
    font-family: 'Georgia', 'Cambria', 'Times New Roman', serif;
    font-size: 10.5pt; line-height: 1.55; color: #1a1a1a;
    margin: 0; padding: 0; background: #ffffff;
  }
  .cover { text-align: center; padding-top: 55mm; page-break-after: always; }
  .cover .mark { font-size: 34pt; color: #d4af37; letter-spacing: 2px; }
  .cover h1 { font-size: 26pt; border: none; margin: 14px 0 4px; }
  .cover .sub { font-size: 13pt; color: #4a3f22; font-style: italic; margin-bottom: 26px; }
  .cover .who { font-size: 12pt; color: #2d2416; line-height: 2; }
  .cover .rule { width: 60mm; margin: 22px auto; border-top: 2px solid #d4af37; }
  .cover .foot { margin-top: 34mm; font-size: 9pt; color: #8a7c5c; }

  .newpage { page-break-before: always; }
  h1 {
    font-size: 19pt; font-weight: 700; color: #7a5c00;
    margin: 0 0 10px; padding-bottom: 8px;
    border-bottom: 2px solid #d4af37; page-break-after: avoid;
  }
  h2 {
    font-size: 13.5pt; font-weight: 700; color: #7a5c00;
    margin: 18px 0 8px; padding: 8px 0 5px;
    border-top: 1px solid #e8e2cc; page-break-after: avoid;
  }
  h3 { font-size: 11.5pt; font-weight: 700; color: #2d2416;
       margin: 13px 0 5px; page-break-after: avoid; }
  p { margin: 6px 0 8px; }
  strong { color: #2d2416; font-weight: 700; }
  em { color: #4a3f22; font-style: italic; }
  a { color: #7a5c00; text-decoration: none; }
  blockquote {
    margin: 10px 0 12px; padding: 9px 14px;
    background: #f9f4e2; border-left: 4px solid #d4af37;
    border-radius: 0 6px 6px 0; color: #4a3f22;
    page-break-inside: avoid;
  }
  blockquote strong { color: #6b4f00; }
  ul, ol { margin: 6px 0 10px 20px; padding: 0; }
  li { margin: 3px 0; }
  table {
    border-collapse: collapse; width: 100%; margin: 10px 0 14px;
    font-size: 9.5pt; page-break-inside: avoid;
  }
  th, td { border: 1px solid #d8d0b4; padding: 6px 9px; text-align: left; vertical-align: top; }
  th { background: #f5efdd; color: #4a3f22; font-weight: 700; }
  code { font-family: 'Menlo', monospace; font-size: 9pt;
         background: #f5efdd; padding: 1px 4px; border-radius: 3px; }
  pre { background: #f9f4e2; border-left: 3px solid #d4af37; padding: 8px 12px;
        font-size: 8.5pt; overflow-x: auto; page-break-inside: avoid; }
  pre code { background: none; padding: 0; }
  hr { border: none; border-top: 1px solid #e8e2cc; margin: 16px 0; }
  .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center;
            font-size: 8pt; color: #8a7c5c; padding-bottom: 3mm; }
</style>
</head>
<body>
<div class="cover">
  <div class="mark">&#9670;</div>
  <h1>Acharya &mdash; Ara Field Kit</h1>
  <div class="sub">Exam-authentic test papers, in your institute&rsquo;s name</div>
  <div class="rule"></div>
  <div class="who">
    <strong>Priyanshu</strong><br>
    Marketing Partner &amp; Regional Head<br>
    Ara &amp; Bhojpur, Bihar
  </div>
  <div class="rule"></div>
  <div class="foot">
    TrigunAI Innovations &middot; Issued 18 August 2026 &middot; Confidential<br>
    The live version of this kit lives in your Claude &mdash; say &ldquo;start my day&rdquo;.
  </div>
</div>
""" + body_html + """
<div class="footer">TrigunAI Innovations &middot; Ara Field Kit &middot; Priyanshu &middot; Confidential &middot; 2026-08-18</div>
</body></html>"""

HTML.write_text(full_html)
print(f"HTML written to {HTML} ({HTML.stat().st_size:,} bytes)")

WEASY = pathlib.Path.home() / "Library/Python/3.9/bin/weasyprint"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def render():
    # Delete first, else a failed render leaves the PREVIOUS pdf and the size check below
    # reports a false success on stale output.
    PDF.unlink(missing_ok=True)
    if WEASY.exists():
        r = subprocess.run([str(WEASY), str(HTML), str(PDF)],
                           capture_output=True, text=True, timeout=180)
        if PDF.exists() and PDF.stat().st_size > 20_000:
            return "weasyprint", r.stderr[-300:]
        print("weasyprint failed, trying Chrome:", r.stderr[-300:])
    # Chrome headless RENDERS fine while Chrome.app is open — it just never EXITS.
    # So don't wait on the process: poll for the finished PDF, then kill it.
    p = subprocess.Popen([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                          "--user-data-dir=/tmp/chrome_pdf_profile",
                          f"--print-to-pdf={PDF}", f"file://{HTML.absolute()}"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    stable, last = 0, -1
    for _ in range(120):                      # up to ~60s
        time.sleep(0.5)
        size = PDF.stat().st_size if PDF.exists() else 0
        stable = stable + 1 if size and size == last else 0
        last = size
        if stable >= 2:
            break
    p.kill()
    return "chrome", ""

engine, err = render()
if PDF.exists():
    print(f"PDF written to {PDF} ({PDF.stat().st_size:,} bytes) via {engine}")
    if err.strip():
        print("renderer notes:", err.strip()[:300])
else:
    print("PDF not produced:", err)
