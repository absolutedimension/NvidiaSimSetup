#!/usr/bin/env python3
"""daily_worksheet.py — today's school day → one printable worksheet + an app link.

    python3 kids_quiz/school/daily_worksheet.py                 # today, default profile
    python3 kids_quiz/school/daily_worksheet.py --date 2026-08-19 --n 4
    python3 kids_quiz/school/daily_worksheet.py --tomorrow      # tonight, for tomorrow

Reads the stored weekly timetable (school/timetable.py), takes the subjects the child
ACTUALLY had that day, generates questions for each with the same engine the live kids app
uses, and renders them through the SAME print renderer the app uses
(lms/app/static/kids/worksheet_print.js) so the paper sheet looks identical to the product.

Output (kids_quiz/school/out/):
  worksheet_<profile>_<YYYY-MM-DD>.pdf   — print this
  worksheet_<profile>_<YYYY-MM-DD>.json  — the items, for reference/debugging
and prints an on-screen link per subject into the live kids app.

Nothing here touches the school portal. See timetable.py for why (image CAPTCHA on login).
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time
from datetime import date, timedelta
from urllib.parse import quote

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent                      # repo root
OUT = HERE / "out"
STATIC = ROOT / "lms" / "app" / "static" / "kids"
KIDS_APP = "https://kids-education.trigunai.com"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "kids_quiz"))
import timetable as TT                          # noqa: E402
import worksheet_engine as WE                   # noqa: E402
import assessment_core as AC                    # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WEASY = pathlib.Path.home() / "Library/Python/3.9/bin/weasyprint"


def _bank_items(board, cls, subject, chapter=""):
    """The pooled bank the app serves knowledge subjects from (Maths is computed live)."""
    slug = f"{board}".lower().replace(" ", "") + f"_class{cls}_" + f"{subject}".lower().replace(" ", "")
    p = ROOT / "lms" / "app" / "kidsengine" / "content" / "bank" / f"{slug}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    items = d if isinstance(d, list) else d.get("items", [])
    out = []
    for it in items:
        try:
            out.append(AC.enrich(it) if "difficulty" not in it else it)
        except Exception:
            out.append(it)
    return out


def make_items(board, cls, subject, n, seed):
    """n questions for one subject — computed for Maths, drawn from the bank otherwise.
    Mirrors the app's serving order so the paper sheet matches what he'd get on screen."""
    try:
        live = WE.generate(board, cls, subject, None, n=n, seed=seed) or []
    except Exception:
        live = []
    items = [i for i in live if i]
    if len(items) < n:                                   # knowledge subject → pooled bank
        import random
        pool = _bank_items(board, cls, subject)
        if pool:
            r = random.Random(seed)
            items = r.sample(pool, min(n, len(pool)))
    return items[:n]


SUBJECT_TITLE = {"Mathematics": "Maths", "EVS": "EVS", "English": "English",
                 "GK": "General Knowledge", "Hindi": "हिंदी"}


def build_html(sheet, title, subtitle):
    """A page that drives the app's OWN print renderer (no second renderer to keep in sync).

    Loaded over http://127.0.0.1 rather than file:// — assets.js fetches
    /static/kids/asset_manifest.json, and fetch() is blocked on file://, which silently
    degrades picture questions to bare words ("rabbit rabbit rabbit"). Served, the sheet
    gets the same generated art the on-screen worksheet uses."""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<link rel="stylesheet" href="/static/kids/worksheet_print.css">
<style>
  @page {{ size: A4; margin: 12mm 12mm 14mm 12mm; }}
  body {{ background:#fff; font-family:-apple-system,'Segoe UI',sans-serif; }}
  .dwhead {{ text-align:center; margin:0 0 10px }}
  .dwhead h1 {{ font-size:20px; margin:0 0 2px }}
  .dwhead p {{ font-size:12px; color:#666; margin:0 }}
  /* the renderer draws a Name/Date block per sheet — keep it once, at the top */
  .dwsec:not(:first-of-type) .wp-meta {{ display:none }}
  .dwsec + .dwsec {{ page-break-before: auto; margin-top:10px }}
  .wp-topbar {{ display:none }}
</style></head><body>
<div class="dwhead"><h1>{title}</h1><p>{subtitle}</p></div>
<div id="mount"></div>
<script src="/static/kids/assets.js"></script>
<script src="/static/kids/worksheet_print.js"></script>
<script>
  var SHEET = {json.dumps(sheet)};
  var TITLES = {json.dumps(SUBJECT_TITLE)};
  var mount = document.getElementById('mount');
  // load the art manifest FIRST — the renderer resolves pictures synchronously off it, so
  // rendering before it lands is what degrades a picture question to bare words.
  (window.KidsAssets ? KidsAssets.load() : Promise.resolve()).then(function(){{
    SHEET.sections.forEach(function(sec){{
      var box = document.createElement('div'); box.className = 'dwsec'; mount.appendChild(box);
      KidsWorksheetPrint.render(box, sec.items,
        {{title: (TITLES[sec.subject] || sec.subject) + ' Worksheet'}});
    }});
    setTimeout(function(){{ window.__ready = true; }}, 600);   // let the <img>s decode
  }});
</script></body></html>"""


class _Serve:
    """Serve the sheet + /static/kids/* on localhost for the duration of the print.

    Needed because the art manifest is fetched, and fetch() is blocked on file:// —
    printing off disk silently drops every picture. Bound to 127.0.0.1 and shut down
    immediately after the PDF is written."""

    def __init__(self, html: str):
        import http.server, socketserver, threading, tempfile, os
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="kids_sheet_"))
        (self.dir / "sheet.html").write_text(html, encoding="utf-8")
        (self.dir / "static").mkdir()
        os.symlink(STATIC, self.dir / "static" / "kids")     # /static/kids/* → the app's assets
        d = str(self.dir)

        class H(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=d, **k)

            def log_message(self, *a):
                pass

        self.srv = socketserver.TCPServer(("127.0.0.1", 0), H)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/sheet.html"

    def close(self):
        try:
            self.srv.shutdown()
        except Exception:
            pass


def to_pdf(html: str, pdf_path: pathlib.Path) -> str:
    """Headless Chrome over a throwaway localhost server. Chrome renders fine while
    Chrome.app is open but never exits, so poll for a stable file size and kill it
    (same trick as the teacher_gtm PDF scripts). weasyprint isn't usable here — it has no
    JS engine, and this sheet is rendered by the app's JS renderer."""
    srv = _Serve(html)
    try:
        p = subprocess.Popen([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                              "--virtual-time-budget=8000",
                              "--user-data-dir=/tmp/chrome_pdf_kidsdaily",
                              f"--print-to-pdf={pdf_path}", srv.url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        stable, last = 0, -1
        for _ in range(120):
            time.sleep(0.5)
            size = pdf_path.stat().st_size if pdf_path.exists() else 0
            stable = stable + 1 if size and size == last else 0
            last = size
            if stable >= 2:
                break
        p.kill()
    finally:
        srv.close()
    return "chrome"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="shivaay")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--tomorrow", action="store_true", help="build tonight for tomorrow")
    ap.add_argument("--n", type=int, default=5, help="questions per subject")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()

    d = date.fromisoformat(a.date) if a.date else date.today()
    if a.tomorrow:
        d += timedelta(days=1)

    prof = TT.load(a.profile)
    board, cls = prof["board"], int(prof["cls"])
    subjects, skipped = TT.subjects_for(prof, d)
    day = TT.DAY_LABEL[TT.day_key(d)]

    print(f"{prof['name']} · {board} class {cls} · {day} {d.isoformat()}")
    if not subjects:
        print("  No academic periods that day — nothing to build.")
        for s in skipped:
            print(f"  skipped: {s['subject']} ({s['why']})")
        return

    OUT.mkdir(exist_ok=True)
    seed = int(d.strftime("%Y%m%d"))            # same day → same sheet; next day → new one
    sections, links = [], []
    for i, ent in enumerate(subjects):
        subj, periods = ent["subject"], ent["periods"]
        # weight by school time: a day with 3 English periods earns more English practice.
        want = min(a.n + (periods - 1), a.n * 2)
        items = make_items(board, cls, subj, want, seed + i)
        if not items:
            print(f"  {subj}: no questions available — skipped")
            continue
        sections.append({"subject": subj, "periods": periods, "items": items})
        links.append((subj, f"{KIDS_APP}/exam-prep/worksheet?cls={cls}&board={quote(board)}"
                            f"&subject={quote(subj)}&n={want}"))
        print(f"  {subj}: {len(items)} questions ({periods} period{'s' if periods > 1 else ''})")
    for s in skipped:
        print(f"  skipped {s['subject']} — {s['why']}")
    if not sections:
        print("  Nothing generated.")
        return

    stem = f"worksheet_{a.profile}_{d.isoformat()}"
    sheet = {"date": d.isoformat(), "day": day, "board": board, "cls": cls, "sections": sections}
    (OUT / f"{stem}.json").write_text(json.dumps(sheet, ensure_ascii=False, indent=1), encoding="utf-8")

    if not a.no_pdf:
        title = f"{prof['name'].split()[0]} · {day} {d.strftime('%d %b %Y')}"
        subtitle = f"{prof.get('section', 'Class ' + str(cls))} · {board} · " + " · ".join(s["subject"] for s in sections)
        html = build_html(sheet, title, subtitle)
        (OUT / f"{stem}.html").write_text(html, encoding="utf-8")   # kept for debugging
        pdf = OUT / f"{stem}.pdf"
        engine = to_pdf(html, pdf)
        print(f"\nPDF ({engine}): {pdf}  [{pdf.stat().st_size // 1024} KB]" if pdf.exists()
              else "\nPDF FAILED — open the .html and print from the browser")

    print("\nOn-screen (read-aloud, adaptive):")
    for subj, url in links:
        print(f"  {subj}: {url}")


if __name__ == "__main__":
    main()
