#!/usr/bin/env python3
# generic caller-kit PDF builder
"""Convert a field rep's COMPANY_CONTEXT_<NAME>.md into a print-styled HTML, then to PDF via Chrome headless."""
import markdown, subprocess, pathlib

NAME = "<NAME>"   # field rep the caller kit is for
KIT_DIR = pathlib.Path.home() / "Downloads" / f"{NAME}_Caller_Kit"
MD  = KIT_DIR / f"COMPANY_CONTEXT_{NAME}.md"
HTML = pathlib.Path(f"/tmp/{NAME}_context.html")
PDF  = KIT_DIR / f"COMPANY_CONTEXT_{NAME}.pdf"

md_text = MD.read_text()
body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])

full_html = f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>TrigunAI + Acharya — Field Handbook for {NAME}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm 20mm 16mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Georgia', 'Cambria', 'Times New Roman', serif;
    font-size: 10.5pt; line-height: 1.55; color: #1a1a1a;
    max-width: 100%; margin: 0; padding: 0;
    background: #ffffff;
  }}
  h1 {{
    font-family: 'Georgia', serif; font-size: 20pt; font-weight: 700;
    color: #7a5c00; margin: 0 0 6px; padding-bottom: 8px;
    border-bottom: 2px solid #d4af37;
    page-break-after: avoid;
  }}
  h2 {{
    font-family: 'Georgia', serif; font-size: 14pt; font-weight: 700;
    color: #7a5c00; margin: 22px 0 8px; padding-top: 10px;
    border-top: 1px solid #e8e2cc;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11.5pt; font-weight: 700; color: #2d2416;
    margin: 14px 0 6px; page-break-after: avoid;
  }}
  p {{ margin: 6px 0 8px; }}
  strong {{ color: #2d2416; font-weight: 700; }}
  em {{ color: #4a3f22; font-style: italic; }}
  a {{ color: #7a5c00; text-decoration: none; border-bottom: 1px dotted #d4af37; }}
  code {{ font-family: 'SFMono-Regular', 'Consolas', monospace; font-size: 9.5pt;
          background: #f5efdd; padding: 1px 5px; border-radius: 3px; color: #4a3f22; }}
  pre code {{ display: block; padding: 10px 12px; background: #1e1e1e;
              color: #e8e2cc; border-radius: 6px; }}
  blockquote {{
    margin: 10px 0 12px; padding: 8px 14px;
    background: #f9f4e2; border-left: 4px solid #d4af37;
    border-radius: 0 6px 6px 0; font-style: italic; color: #4a3f22;
    page-break-inside: avoid;
  }}
  ul, ol {{ margin: 6px 0 10px 22px; padding: 0; }}
  li {{ margin: 3px 0; }}
  table {{
    border-collapse: collapse; width: 100%; margin: 10px 0 14px;
    font-size: 9.5pt; page-break-inside: avoid;
  }}
  th, td {{ border: 1px solid #d8d0b4; padding: 6px 9px; text-align: left; vertical-align: top; }}
  th {{ background: #f5efdd; color: #4a3f22; font-weight: 700; }}
  hr {{ border: none; border-top: 1px solid #e8e2cc; margin: 20px 0; }}
  /* pretty header emoji */
  h1:first-of-type::before {{ content: "🧭 "; }}
  /* page breaks before major sections */
  h2 {{ page-break-before: auto; }}
  /* keep tables intact */
  table, blockquote, pre {{ page-break-inside: avoid; }}
  /* footer at bottom of each printed page */
  .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center;
             font-size: 8pt; color: #8a7c5c; padding-bottom: 6mm; }}
</style>
</head>
<body>
{body_html}
<div class="footer">TrigunAI Innovations · Field Handbook for {NAME} · Confidential · Revised 2026-07-08</div>
</body></html>"""

HTML.write_text(full_html)
print(f"✅ HTML written to {HTML} ({HTML.stat().st_size} bytes)")

# Convert to PDF via Chrome headless
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    CHROME, "--headless", "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF}",
    f"file://{HTML.absolute()}",
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
if PDF.exists():
    print(f"✅ PDF written to {PDF} ({PDF.stat().st_size:,} bytes)")
else:
    print("❌ PDF not produced")
    print(result.stderr[-500:])
