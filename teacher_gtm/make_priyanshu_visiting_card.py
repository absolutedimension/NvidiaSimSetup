#!/usr/bin/env python3
"""Build Priyanshu Jain's visiting card — print-ready PDF (2 pages: front, back) + PNG proof.

Standard Indian/US business card: 88.9 x 50.8 mm trim, 3 mm bleed on every side
=> 94.9 x 56.8 mm page. Content sits 4 mm inside the trim (7 mm from the bleed edge),
so nothing important dies at the guillotine.

Front is dark: the chrome triskelion mark and the silver wordmark only read properly on a
dark ground, and a dark card suits a regional head. Back is the Acharya cream/orange system
from ACHARYA_CARD_TEACHER.html so it sits in the same family as the institute cards.

Renderer: Chrome headless. THE GOTCHA (same as make_visit_list_pdf.py) — while Chrome.app is
open, headless Chrome writes the PDF correctly but never exits, so we poll for the file and
kill the process rather than waiting on it.
"""
import subprocess, pathlib, sys, time

# Front face theme: "light" (cream, the default) or "dark". The BACK is cream either way.
THEME = sys.argv[1] if len(sys.argv) > 1 else "light"
if THEME not in ("light", "dark"):
    sys.exit('usage: make_priyanshu_visiting_card.py [light|dark]')
SUFFIX = "" if THEME == "light" else "_dark"

HERE = pathlib.Path(__file__).parent
LOGO = (HERE.parent / "brand_logo/pack/trigunai_mark_chrome.png").absolute()
HTML = pathlib.Path(f"/tmp/priyanshu_card{SUFFIX}.html")
PROOF_HTML = pathlib.Path(f"/tmp/priyanshu_card_proof{SUFFIX}.html")
PDF = HERE / f"PRIYANSHU_VISITING_CARD{SUFFIX}.pdf"
PNG = HERE / f"PRIYANSHU_VISITING_CARD{SUFFIX}_proof.png"

# ---- the only lines anyone should need to edit ----------------------------------
NAME      = "Priyanshu Jain"
TITLE     = "Marketing Partner"
SUBTITLE  = "Regional Head &mdash; Ara &amp; Bhojpur"
PHONE     = "+91 94722 72634"
SITE      = "acharya.trigunai.com"
COMPANY   = "TRIGUNAI INNOVATIONS PVT LTD"
# EMAIL intentionally omitted — no @trigunai.com address exists for him yet.
# ---------------------------------------------------------------------------------

CSS = """
  @page { size: 94.9mm 56.8mm; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: #555; }

  .card {
    width: 94.9mm; height: 56.8mm; position: relative; overflow: hidden;
    font-family: 'Figtree', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    page-break-after: always;
  }
  .card:last-child { page-break-after: auto; }
  /* content sits 9.5mm from the bleed edge = 6.5mm inside the trim */
  .safe { position: absolute; left: 9.5mm; right: 9.5mm; top: 8mm; bottom: 8mm; }

  /* ---------- FRONT (dark) ---------- */
  .front {
    background:
      radial-gradient(60mm 40mm at 78% -10%, rgba(185,139,52,.22), transparent 70%),
      radial-gradient(50mm 40mm at 8% 115%, rgba(194,89,31,.16), transparent 72%),
      linear-gradient(160deg, #191510 0%, #0E0B07 55%, #14100A 100%);
    color: #F4EDDF;
  }
  /* Hairline gold frame. Keep it >=3mm INSIDE the trim (i.e. >=6mm from the bleed edge):
     a frame closer than that turns any cutting drift into visibly uneven borders. */
  .front .frame {
    position: absolute; left: 6.5mm; right: 6.5mm; top: 5.2mm; bottom: 5.2mm;
    border: .22mm solid rgba(185,139,52,.34); border-radius: 1.6mm; pointer-events: none;
  }
  .brandrow { display: flex; align-items: center; gap: 2.6mm; }
  .brandrow img { width: 8.4mm; height: 8.4mm; object-fit: contain;
                  filter: drop-shadow(0 .4mm .8mm rgba(0,0,0,.6)); }
  .wordmark {
    font-family: 'Bricolage Grotesque', 'Avenir Next', Georgia, serif;
    font-weight: 700; font-size: 11pt; letter-spacing: -.01em; line-height: 1;
    background: linear-gradient(180deg,#FFFFFF 8%,#C9CDD3 46%,#8E949C 66%,#EDEFF2 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .wordmark small {
    display: block; -webkit-text-fill-color: #B98B34; color: #B98B34;
    font-family: 'Figtree', Helvetica, sans-serif; font-weight: 600;
    font-size: 4.6pt; letter-spacing: .22em; text-transform: uppercase; margin-top: .7mm;
  }

  .who { position: absolute; left: 0; bottom: 12.4mm; }
  .who .name {
    font-family: 'Bricolage Grotesque', 'Avenir Next', Georgia, serif;
    font-weight: 800; font-size: 16pt; line-height: 1.04; letter-spacing: -.015em;
    color: #FBF4E9;
  }
  .who .rule { width: 12mm; height: .5mm; background: #B98B34; margin: 2.1mm 0 1.9mm; }
  .who .role { font-size: 7.4pt; font-weight: 700; color: #E4C87E; letter-spacing: .02em; }
  .who .region { font-size: 6.6pt; font-weight: 500; color: #9C907A; margin-top: .5mm; }

  .contact {
    position: absolute; left: 0; right: 0; bottom: 0;
    display: flex; align-items: baseline; justify-content: space-between;
    border-top: .18mm solid rgba(185,139,52,.28); padding-top: 2mm;
  }
  .contact .ph { font-size: 8.4pt; font-weight: 700; color: #FBF4E9; letter-spacing: .01em; }
  .contact .web { font-size: 6.4pt; font-weight: 600; color: #B98B34; letter-spacing: .04em; }

  /* ---------- FRONT, light variant ----------
     On cream the silver wordmark gradient disappears, so it reverts to solid ink — the same
     treatment ACHARYA_CARD_TEACHER.html uses. The chrome mark itself still reads on cream. */
  .front.light {
    background:
      radial-gradient(58mm 38mm at 80% -12%, rgba(194,89,31,.13), transparent 70%),
      radial-gradient(46mm 36mm at 4% 112%, rgba(185,139,52,.16), transparent 72%),
      linear-gradient(165deg, #FEFAF3 0%, #FAF1E2 55%, #F5E8D3 100%);
    color: #2B2113;
  }
  .front.light .frame { border-color: rgba(185,139,52,.55); }
  .front.light .brandrow img { filter: drop-shadow(0 .3mm .6mm rgba(90,60,20,.28)); }
  .front.light .wordmark {
    background: none; -webkit-background-clip: initial; background-clip: initial;
    -webkit-text-fill-color: #2B2113; color: #2B2113;
  }
  .front.light .wordmark small { -webkit-text-fill-color: #B98B34; color: #B98B34; }
  .front.light .who .name { color: #241B0F; }
  .front.light .who .rule { background: #C2591F; }
  .front.light .who .role { color: #C2591F; }
  .front.light .who .region { color: #8a7d63; }
  .front.light .contact { border-top-color: rgba(120,90,40,.24); }
  .front.light .contact .ph { color: #241B0F; }
  .front.light .contact .web { color: #C2591F; }

  /* ---------- BACK (cream) ---------- */
  .back {
    background:
      radial-gradient(70mm 40mm at 50% -18mm, rgba(194,89,31,.10), transparent 70%),
      linear-gradient(180deg,#FDF7EE,#F6EAD6);
    color: #2B2113;
  }
  .back .safe { display: flex; flex-direction: column; justify-content: center;
                text-align: center; align-items: center; }
  .back .ach {
    font-family: 'Bricolage Grotesque', 'Avenir Next', Georgia, serif;
    font-weight: 800; font-size: 15pt; letter-spacing: -.01em; color: #2B2113;
  }
  .back .ach span { color: #C2591F; }
  .back .by { font-size: 5.4pt; font-weight: 600; letter-spacing: .2em;
              text-transform: uppercase; color: #B98B34; margin-top: .9mm; }
  .back .line { width: 16mm; height: .4mm; background: rgba(185,139,52,.5); margin: 2.6mm 0; }
  .back .prop { font-size: 8pt; font-weight: 700; line-height: 1.35; color: #3d2f1a; max-width: 66mm; }
  .back .prop b { color: #C2591F; }
  .back .exams { font-size: 5.6pt; font-weight: 600; letter-spacing: .11em;
                 text-transform: uppercase; color: #8a7d63; margin-top: 2.4mm; }
  .back .foot { position: absolute; left: 0; right: 0; bottom: 0; display: flex;
                align-items: baseline; justify-content: space-between;
                border-top: .18mm solid rgba(120,90,40,.2); padding-top: 1.8mm; }
  .back .foot .web { font-size: 6.6pt; font-weight: 700; color: #C2591F; }
  .back .foot .co  { font-size: 4.9pt; font-weight: 600; letter-spacing: .09em; color: #8a7d63; }
"""

CARDS = f"""
<div class="card front {THEME}">
  <div class="frame"></div>
  <div class="safe">
    <div class="brandrow">
      <img src="file://{LOGO}" alt="" />
      <div class="wordmark">TrigunAI<small>Acharya</small></div>
    </div>
    <div class="who">
      <div class="name">{NAME}</div>
      <div class="rule"></div>
      <div class="role">{TITLE}</div>
      <div class="region">{SUBTITLE}</div>
    </div>
    <div class="contact">
      <span class="ph">{PHONE}</span>
      <span class="web">{SITE}</span>
    </div>
  </div>
</div>

<div class="card back">
  <div class="safe">
    <div class="ach">आचार्य &nbsp;<span>Acharya</span></div>
    <div class="by">by TrigunAI</div>
    <div class="line"></div>
    <div class="prop">Exam-authentic test papers,<br><b>in your institute&rsquo;s name</b> &mdash; in 30 seconds.</div>
    <div class="exams">TRE &middot; SSC &middot; Railway &middot; Banking &middot; Board</div>
    <div class="foot">
      <span class="web">{SITE}</span>
      <span class="co">{COMPANY}</span>
    </div>
  </div>
</div>
"""

FONTS = ('<link href="https://fonts.googleapis.com/css2?'
         'family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&'
         'family=Figtree:wght@500;600;700;800&display=swap" rel="stylesheet" />')

HTML.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<title>Priyanshu Jain — visiting card</title>{FONTS}<style>{CSS}</style></head>
<body>{CARDS}</body></html>""")

# Proof sheet: both faces side by side on one canvas, for a quick on-screen check.
PROOF_HTML.write_text(f"""<!doctype html><html><head><meta charset="utf-8">{FONTS}
<style>{CSS}
  body {{ background:#6b6b6b; padding:8mm; }}
  .sheet {{ display:flex; gap:8mm; }}
  .card {{ page-break-after:auto; box-shadow:0 3mm 8mm rgba(0,0,0,.45); }}
</style></head>
<body><div class="sheet">{CARDS}</div></body></html>""")

print(f"HTML written to {HTML}")

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def chrome_wait(args, outfile, label):
    """Run headless Chrome and poll for the output file — it never exits if Chrome.app is open."""
    outfile.unlink(missing_ok=True)
    p = subprocess.Popen([CHROME, "--headless", "--disable-gpu",
                          "--user-data-dir=/tmp/chrome_card_profile"] + args,
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    stable, last = 0, -1
    for _ in range(120):
        time.sleep(0.5)
        size = outfile.stat().st_size if outfile.exists() else 0
        stable = stable + 1 if size and size == last else 0
        last = size
        if stable >= 2:
            break
    p.kill()
    if outfile.exists():
        print(f"{label}: {outfile} ({outfile.stat().st_size:,} bytes)")
    else:
        print(f"{label}: FAILED")


chrome_wait(["--no-pdf-header-footer", f"--print-to-pdf={PDF}",
             f"file://{HTML.absolute()}"], PDF, "PDF (2 pages: front, back)")

chrome_wait(["--screenshot=" + str(PNG), "--window-size=920,320",
             "--force-device-scale-factor=4", "--hide-scrollbars",
             f"file://{PROOF_HTML.absolute()}"], PNG, "PNG proof")
