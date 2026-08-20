#!/usr/bin/env python3
"""Build a VERIFICATION SHEET for a set — so someone who does NOT know the answers can check it.

The problem this solves. Deepak and Rohan can confirm the paper prints correctly, but neither can
confirm that "the answer to Q47 is C", because they do not know the answers. My assurance is only
worth something if it can be independently checked, and "trust me, I solved them" is not a
checkable claim.

So every question gets a line saying WHERE ITS ANSWER COMES FROM, in a form that can be checked
without knowing any subject:

  REAL question      -> the commission's own advertisement, the question number IN THAT PAPER, and
                        the exact page of the official Model Answer PDF where that letter is
                        printed. Anyone can open the PDF from bssc.bihar.gov.in, find the row and
                        read the letter. No subject knowledge required — just matching a number to
                        a letter.

  GENERATED question -> the worked derivation ("OCEAN: O=15, C=3, E=5, A=1, N=14 -> 15 3 5 1 14").
                        Anyone can follow the arithmetic. No subject knowledge required either.

That turns "do you trust Claude?" into "here are 150 rows; spot-check any ten against the
commission's PDF." Ten random rows checked and matching is far stronger evidence than any
assurance I can write.

The numbering is NOT re-derived here. `build_onestep_paper.py --key-json` writes the key from
inside its own render loop, so row 47 of this sheet is by construction question 47 of the printed
paper. An independent re-implementation of the ordering would look right and drift silently — that
loop can skip a question that has nothing renderable, and the sheet would never know.

Usage:
    python3 build_onestep_paper.py --set 1 --pin ... --key-json Set1_key.json
    python3 build_verification_sheet.py --key Set1_key.json --set 1
"""
import argparse
import html
import io
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
sys.path.insert(0, str(REPO / "teacher_gtm"))
from paper_common import esc, MATH_CSS  # noqa: E402

BSSC = REPO / "question_bank_engine/drop/bssc"
# extract stem in VERIFIED_KEYS  ->  the source_pdf recorded on each question
STEM_FOR_PDF = {
    "GK1.PDF": "GK1", "GK(3649).PDF": "GK3649", "G.K_and_N.A_M.A.PDF": "G_K_and_N_A_M_A",
    "JE-0411-GK-QB-AND-MA.pdf": "JE-0411-GK-QB-AND-MA", "maths.PDF": "maths", "hindi1.PDF": "hindi1",
    "03_25_SET_A.pdf": "03_25_SET_A", "Qn_SET_A.pdf": "Qn_SET_A",
    "3102059_10_I.pdf": "3102059_10_I", "0225_SET-A.pdf": "0225",
    "PHARMACY.PDF": "PHARMACY", "CHEMISTRY_M.A.PDF": "CHEMISTRY_M_A",
    "JE-0411-CIVIL-QB-AND-MA.pdf": "JE-0411-CIVIL-QB-AND-MA",
    "JE-0411-MECH-QB-AND-MA.pdf": "JE-0411-MECH-QB-AND-MA",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=int, default=1)
    ap.add_argument("--key", required=True,
                    help="the --key-json written by build_onestep_paper.py for THIS set")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    vk = json.load(io.open(BSSC / "VERIFIED_KEYS.json", encoding="utf-8"))
    order = json.load(io.open(a.key, encoding="utf-8"))

    # `esc` typesets LaTeX, which is right for a question's own text and wrong for a filename —
    # it turned "03_25_Model_Ans.pdf" into "03₂5_Modelₐns.pdf". Plain-escape the provenance.
    def plain(t):
        return html.escape(str(t or ""))

    rows, n_real, n_gen, used = [], 0, 0, {}
    for q in order:
        num, ans, opt = q["n"], q["answer"], q["answer_text"]
        if q.get("generated"):
            n_gen += 1
            how = ("<b>Acharya-generated.</b> The answer is COMPUTED, not looked up. Working: "
                   + esc(q.get("solution") or "—"))
            cls = "gen"
        else:
            n_real += 1
            src = q.get("source_pdf") or ""
            spec = vk.get(STEM_FOR_PDF.get(src, ""), {})
            used.setdefault(src, [spec.get("exam", src), spec.get("source", "?"), 0])[2] += 1
            how = (f"<b>{plain(spec.get('exam', src))}</b> &mdash; question "
                   f"<b>{q.get('source_number')}</b> of that paper.<br>Official answer key: "
                   f"<b>{plain(spec.get('source', '?'))}</b> &mdash; find row "
                   f"{q.get('source_number')} and read the letter.")
            cls = "real"
        rows.append(
            f'<tr class="{cls}"><td class="n">{num}</td><td class="a">{plain(ans)}</td>'
            f'<td class="o">{esc(opt)}</td><td class="h">{how}</td></tr>')

    srcs = "".join(
        f'<tr><td class="o">{plain(e)}</td><td class="n">{n}</td>'
        f'<td class="h">{plain(f)} &middot; key: {plain(k)}</td></tr>'
        for f, (e, k, n) in sorted(used.items(), key=lambda kv: -kv[1][2]))

    HTML = f"""<style>
@page {{ size:A4; margin:11mm 9mm; }}
body {{ font-family:'Helvetica Neue',Arial,sans-serif; font-size:8.2pt; color:#1a1c24; margin:0; }}
h1 {{ font-size:14pt; margin:0 0 2px; color:#12141c; }}
.sub {{ font-size:8.5pt; color:#5a5f6e; margin-bottom:8px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227,#8a6d1a 55%,#c9a227);
        margin:6px 0 10px; border-radius:2px; }}
.how {{ border:1px solid #c9a227; background:#fdfaf0; border-radius:5px; padding:9px 11px;
       font-size:8.4pt; margin-bottom:10px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ background:#faf8f1; border:1px solid #e0dccc; padding:4px 6px; font-size:7.8pt;
     text-align:left; color:#5a5f6e; }}
td {{ border:1px solid #eee8d8; padding:4px 6px; vertical-align:top; }}
td.n {{ width:26px; font-weight:800; text-align:right; }}
td.a {{ width:22px; font-weight:800; color:#8a6d1a; text-align:center; }}
td.o {{ width:22%; }}
tr.gen td {{ background:#fbfaf5; }}
tr {{ page-break-inside:avoid; }}
{MATH_CSS}
</style>
<h1>Answer Key &mdash; how to check it yourself</h1>
<div class="sub">BSSC 2nd Inter Level practice paper &middot; <b>SET {a.set}</b> &middot;
{n_real} official questions + {n_gen} Acharya-generated</div>
<div class="rule"></div>
<div class="how">
<b>You do not need to know any answer to check this sheet.</b><br>
<b>For an official question</b> &mdash; open that advertisement's Model Answer PDF on
<b>bssc.bihar.gov.in</b>, go to the page named in the last column, find the row for that question
number, and read the letter. It must match column <b>Ans</b>. This is number-matching, not
subject knowledge.<br>
<b>For a generated question</b> &mdash; the working is printed. Follow the arithmetic.<br>
<b>Suggested check:</b> pick any ten rows at random and verify them. Ten matching rows is far
stronger evidence than any assurance &mdash; and if even one fails, tell us and we will pull the
question and rebuild.
</div>
<h2 style="font-size:10pt;margin:12px 0 4px">The official papers this set draws on</h2>
<div class="sub">All of these are free downloads from the commission's own notice board at
bssc.bihar.gov.in (search for &#2346;&#2381;&#2352;&#2358;&#2381;&#2344; &#2346;&#2340;&#2381;&#2352;
and &#2310;&#2342;&#2352;&#2381;&#2358; &#2313;&#2340;&#2381;&#2340;&#2352;). We can also hand over
our copies.</div>
<table style="margin-bottom:12px">
<tr><th>Advertisement / paper</th><th>Qs used</th><th>File &amp; official answer key</th></tr>
{srcs}
</table>
<table>
<tr><th>Q</th><th>Ans</th><th>Answer text</th><th>Where this answer comes from &mdash; and how to verify it</th></tr>
{''.join(rows)}
</table>
<div class="sub" style="margin-top:10px">Every official answer above was read off the commission's
own Model Answer page by a human, not by OCR &mdash; on one paper the machine read had five wrong
letters, which is why the pages were re-read by eye.</div>"""

    out = pathlib.Path(a.out or REPO / f"teacher_gtm/VerificationSheet_Set{a.set}.pdf").resolve()
    html_path = pathlib.Path(str(out).replace(".pdf", ".html"))
    html_path.write_text(HTML, encoding="utf-8")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", html_path.as_uri()],
                       capture_output=True, timeout=300)
    print(f"Set {a.set}: {len(rows)} rows ({n_real} official + {n_gen} generated) -> {out}")


if __name__ == "__main__":
    main()
