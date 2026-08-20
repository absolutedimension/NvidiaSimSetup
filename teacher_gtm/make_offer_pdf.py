#!/usr/bin/env python3
"""Build ../team/heena/OFFER_HEENA.pdf — a printable field visit sheet from the .md.

Same Acharya dark-gold print theme as make_context_pdf.py, but tuned for a sheet Rohan
fills in by hand: each STOP starts a new page, note-lines stay intact, tables never split.
"""
import markdown, subprocess, pathlib, re, time

HERE = pathlib.Path(__file__).parent
MD   = HERE / "../team/heena/OFFER_HEENA.md"
HTML = pathlib.Path("/tmp/offer_heena.html")
PDF  = HERE / "../team/heena/OFFER_HEENA.pdf"

body_html = markdown.markdown(MD.read_text(), extensions=["tables", "fenced_code", "sane_lists"])

# The per-stop fact tables are headerless, but markdown still emits an empty <thead>, which
# prints as a stray band. Strip it in Python so it works in any renderer — the CSS-only fix
# (`thead:has(th:empty)`) is Chrome-specific.
body_html = re.sub(r"<thead>\s*<tr>(?:\s*<th></th>)+\s*</tr>\s*</thead>", "", body_html)

full_html = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>TrigunAI — Offer of Engagement</title>
<style>
  /* bottom margin must clear the fixed footer, or the last line prints on top of it */
  @page { size: A4; margin: 16mm 14mm 24mm 14mm; }
  * { box-sizing: border-box; }
  body {
    font-family: 'Georgia', 'Cambria', 'Times New Roman', serif;
    font-size: 10.5pt; line-height: 1.5; color: #1a1a1a;
    margin: 0; padding: 0; background: #ffffff;
  }
  h1 {
    font-size: 20pt; font-weight: 700; color: #7a5c00;
    margin: 0 0 6px; padding-bottom: 8px;
    border-bottom: 2px solid #d4af37; page-break-after: avoid;
  }
  h1:first-of-type::before { content: "\\1F9ED  "; }
  /* every STOP / DAY heading starts a fresh page so there's room to write */
  h2 {
    font-size: 14.5pt; font-weight: 700; color: #7a5c00;
    margin: 0 0 10px; padding: 10px 0 6px;
    border-top: 2px solid #d4af37; border-bottom: 1px solid #e8e2cc;
    page-break-after: avoid; page-break-before: auto;
  }
  /* ...except the first one, which must share page 1 with the title */
  h2:first-of-type { page-break-before: avoid; }
  h3 { font-size: 11.5pt; font-weight: 700; color: #2d2416;
       margin: 14px 0 6px; page-break-after: avoid; }
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
  /* the Hindi opening lines read as speech, not italic body copy */
  blockquote strong { color: #6b4f00; }
  ul, ol { margin: 6px 0 10px 20px; padding: 0; }
  li { margin: 3px 0; }
  table {
    border-collapse: collapse; width: 100%; margin: 10px 0 14px;
    font-size: 9.5pt; page-break-inside: avoid;
  }
  th, td { border: 1px solid #d8d0b4; padding: 6px 9px; text-align: left; vertical-align: top; }
  th { background: #f5efdd; color: #4a3f22; font-weight: 700; }
  /* first col of the per-stop fact tables = the label column */
  td:first-child strong { color: #7a5c00; }
  hr { border: none; border-top: 1px solid #e8e2cc; margin: 16px 0; }
  /* hand-writing area — a plain open box, ~4 lines of handwriting.
     NOTE: do NOT rule this with repeating-linear-gradient. A sub-mm repeating stripe
     across 8 print-paginated boxes makes Chrome headless hang indefinitely. */
  .notebox {
    height: 34mm; margin: 8px 0 14px;
    border: 1px solid #d8d0b4; border-radius: 4px; background: #fffdf7;
    page-break-inside: avoid;
  }
  .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center;
            font-size: 8pt; color: #8a7c5c; padding-bottom: 3mm; }
  /* inline fill-in blank — bare underscores get eaten by markdown's emphasis parser */
  .blank { display: inline-block; min-width: 34mm; border-bottom: 1px solid #8a7c5c;
           vertical-align: baseline; }
</style>
</head>
<body>
""" + body_html + """
<div class="footer">TrigunAI Innovations &middot; Acharya Acharya Field Visit List &middot; Rohan &middot; Confidential &middot; 2026-08-17middot; Ara & Bhojpur Institute List Acharya Field Visit List &middot; Rohan &middot; Confidential &middot; 2026-08-17middot; Priyanshu Acharya Field Visit List &middot; Rohan &middot; Confidential &middot; 2026-08-17middot; Confidential Acharya Field Visit List &middot; Rohan &middot; Confidential &middot; 2026-08-17middot; 2026-08-18</div>
</body></html>"""

HTML.write_text(full_html)
print(f"HTML written to {HTML} ({HTML.stat().st_size:,} bytes)")

# Renderer chain.
#   Chrome is what actually works here. THE GOTCHA: while Chrome.app is open, headless
#   Chrome renders and writes the PDF correctly but then NEVER EXITS — so subprocess.run()
#   with a timeout looks like a total failure when the output is already on disk. We poll
#   for the file and kill the process instead of waiting for it.
#   WeasyPrint is tried first only because it is a clean library call; on this machine it
#   currently fails (`libpango-1.0-0` not found), so it just falls through to Chrome.
#   To make it work: brew install pango, or re-install weasyprint for python3.14.
WEASY = pathlib.Path.home() / "Library/Python/3.9/bin/weasyprint"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def render():
    # Delete first: otherwise a failed render leaves the PREVIOUS pdf in place and the
    # exists()/size check below reports a false success on stale output.
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
        # two consecutive equal non-zero sizes == write finished
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
