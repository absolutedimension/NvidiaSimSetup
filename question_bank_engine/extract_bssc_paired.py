#!/usr/bin/env python3
"""Extract REAL bilingual questions from BSSC booklets printed as FACING PAGES.

`extract_bssc.py` handles the 2022-2025 papers, where Hindi and English sit SIDE BY SIDE on one
page and must be merged within the page. The older booklets (2016-2018 advertisements: GK1,
GK(3649), G.K_and_N.A, maths, CHEMISTRY, PHARMACY, the JE papers) use a different layout entirely,
verified by rendering the pages and looking at them:

    PDF page 24  ->  ENGLISH  Q72-78   (printed page 22)
    PDF page 25  ->  HINDI    Q72-78   (printed page 23)

One language per page, the SAME question numbers repeating on the facing page. Feeding those pages
to the side-by-side prompt is actively harmful — it is told every question appears twice on the
page and to merge, so on a single-language page it either invents a translation or fuses two
different consecutive questions into one.

So this script does the opposite and simpler thing:

  1. Read each page MONOLINGUALLY, in horizontal BANDS (see below). No merging, no translation,
     no cross-page assumption.
  2. Merge afterwards BY QUESTION NUMBER, routing each copy by the SCRIPT ACTUALLY PRESENT
     (Devanagari vs Latin), never by any language label the model reports. That is gotcha #10 in
     the skill: across 497 measured pairs the model's own language field was right only 59% of the
     time, swapped 12%, and Hindi-in-both 27%.

WHY BANDS — the single most important thing measured here. On these 2016 scans, a whole-page image
produced HALLUCINATED Devanagari, and raising --dpi did nothing to fix it, because the vision API
downscales a large image to a fixed budget: past a point, more dpi is thrown away. What actually
raises the characters-per-pixel the model sees is CROPPING. Measured on GK(3649) p25, Q76:

    whole page @220 dpi   "वायु प्रदूषण में उपयोगी ओजोन की मात्रा एक प्रभावी कवक ..."   (nonsense)
    whole page @450 dpi   "वायु प्रदूषण में उपयोगी ओज़ोन परतों की एक प्रमुख कवक ..."     (still nonsense)
    CROPPED band @450     "वायुमंडल में उपस्थित ओज़ोन जीवों के लिए एक प्रभावी कवच ..."   (verbatim)

English is transcribed correctly even whole-page, so bands are what rescue the Hindi half. Bands
overlap so a question straddling a cut is still seen whole by one of them; the duplicate copies
that produces are collapsed by the same best-per-(number, script) rule used for the two languages.

⚠ HINDI IS QUARANTINED BY DEFAULT, and this is the most important behaviour in this file.
Bands fix the Hindi STEMS (Q72 went from "निर्माणबंद में से…" to the verbatim "निम्नलिखित में से…"),
but PROPER NOUNS and technical vocabulary still come back wrong on these degraded 2016 scans:

    बैकुंठनाथ शुक्ला      -> बंकिमनाथ झा
    सत्येन्द्र नारायण सिन्हा -> सत्येंद्र नारायण सिंह
    बादलों की तड़ित झंझा  -> बालों की ताजगी

A wrong name in a Hindi option is exactly what a Bihar student notices first, and "asli, verified"
is the whole pitch. So the Hindi is written to `stem_hi_unverified` / `options_hi_unverified` and
`stem_hi` / `options_hi` are left EMPTY. Nothing downstream can print it by accident, no
re-extraction is needed later, and a Hindi reader (or a stronger Indic OCR model — the repo has
already proven Qwen2.5-VL for this in `exact-question-making-pipeline-from-pdf`) can promote the
quarantined fields in one pass. Pass --hindi-verified only once that review has actually happened.

The ENGLISH from these papers is verbatim and safe — it was correct even before bands.

The same code therefore handles all three real cases without a flag:
  - facing-page bilingual  -> both stem and stem_hi populated
  - Hindi-only booklet     -> stem_hi only (hindi1.PDF, the Hindi subject paper)
  - English-only booklet   -> stem only

Usage:
    python3 extract_bssc_paired.py <paper.pdf> --exam BSSC --subject "General Studies" \
        [--pages 6-31] [--year 2016] [--out out.json] [--dpi 400] [--bands 3] [--workers 5]
"""
import argparse
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank.llm import LLM                      # noqa: E402
from qbank.models import repair_latex          # noqa: E402

DEVA = re.compile(r"[\u0900-\u097F]")
LATIN = re.compile(r"[A-Za-z]")

MONO_SYS = (
    "You are parsing ONE page of an official BIHAR STAFF SELECTION COMMISSION (BSSC) exam booklet.\n"
    "This page is printed in ONE language only — either HINDI (Devanagari) or ENGLISH. Transcribe "
    "it EXACTLY as printed, in whatever language it is printed in.\n"
    "DO NOT TRANSLATE. DO NOT add a second language. DO NOT merge two questions together.\n"
    "Return EVERY numbered question on the page. These pages are dense — a full page normally "
    "carries 6 to 9 questions. If you return fewer than 6, look again at the whole page.\n"
    'Return JSON: {"questions":[{"number":int,"stem":"the stem exactly as printed",'
    '"options":[{"label":"A","text":"option exactly as printed"}],"has_figure":false}]}\n'
    "RULES:\n"
    "- Use the question number PRINTED next to the question, not its position on the page.\n"
    "- Keep option labels as printed (A/B/C/D).\n"
    "- Write maths as LaTeX and ESCAPE EVERY BACKSLASH for JSON: write \\\\frac, not \\frac.\n"
    "- These are scans and the right margin is sometimes clipped. Transcribe what IS legible; "
    "never guess a word that is cut off, and never invent an option that is not printed.\n"
    "- This image may be a CROPPED HORIZONTAL SLICE of a page, so the first or last question may be "
    "cut off mid-way. Return a question only if you can see its number AND its text. SKIP any "
    "question that is sliced through — another slice covers it. Never complete it from imagination.\n"
    "- Never invent a question that is not on this page."
)


def bands_of(page, n, overlap=0.10):
    """n horizontal slices of a page, overlapping so a question straddling a cut survives whole."""
    import pymupdf
    if n <= 1:
        return [None]
    r = page.rect
    h = r.height / n
    out = []
    for i in range(n):
        top = r.y0 + i * h - (overlap * h if i else 0)
        bot = r.y0 + (i + 1) * h + (overlap * h if i < n - 1 else 0)
        out.append(pymupdf.Rect(r.x0, max(top, r.y0), r.x1, min(bot, r.y1)))
    return out


def _clean(s):
    return repair_latex(str(s or "")).strip()


def _norm_opts(raw):
    out = []
    for o in raw or []:
        if isinstance(o, dict):
            out.append({"label": str(o.get("label") or "").strip().upper().strip("().")[:2],
                        "text": _clean(o.get("text"))})
        else:
            out.append({"label": "", "text": _clean(o)})
    return [o for o in out if o["text"]]


def script_of(rec):
    """Devanagari or Latin — decided by counting characters, never by a model's language claim."""
    txt = (rec.get("stem") or "")
    if len(DEVA.findall(txt)) == 0 and len(LATIN.findall(txt)) == 0:
        txt = " ".join(o["text"] for o in rec.get("options") or [])
    return "hi" if len(DEVA.findall(txt)) > len(LATIN.findall(txt)) else "en"


def parse_pages(spec, npages):
    """'6-31' or '3-10,14,20-22' -> sorted 0-based page indices."""
    if not spec:
        return list(range(npages))
    out = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a) - 1, int(b)))
        else:
            out.add(int(part) - 1)
    return sorted(p for p in out if 0 <= p < npages)


def richness(rec):
    return (len(rec.get("options") or []), len(rec.get("stem") or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--exam", default="BSSC")
    ap.add_argument("--subject", default="General Studies")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--pages", default=None, help="1-based page range holding QUESTIONS, e.g. 6-31")
    ap.add_argument("--bands", type=int, default=3,
                    help="horizontal slices per page; 1 = whole page. Bands are what make the "
                         "Devanagari legible — see the module docstring.")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--hindi-verified", action="store_true",
                    help="promote the Hindi into stem_hi/options_hi. ONLY pass this once a Hindi "
                         "reader has actually checked this paper — see the module docstring.")
    a = ap.parse_args()

    import pymupdf
    llm = LLM()
    if not llm.ok:
        sys.exit("vision LLM not reachable — export QBANK_LLM=on and the proxy vars")

    doc = pymupdf.open(a.pdf)
    pages = parse_pages(a.pages, len(doc))
    jobs = []          # (page_index, band_index, png bytes)
    for p in pages:
        for bi, clip in enumerate(bands_of(doc[p], a.bands)):
            jobs.append((p, bi, doc[p].get_pixmap(dpi=a.dpi, clip=clip).tobytes("png")))
    t0 = time.time()
    print(f"{os.path.basename(a.pdf)}: {len(pages)} question pages "
          f"(p{pages[0]+1}-{pages[-1]+1}) @ {a.dpi} dpi x {a.bands} bands = {len(jobs)} calls",
          flush=True)

    def one(job):
        p, bi, img = job
        for attempt in range(3):
            try:
                d = llm.vision_json(MONO_SYS,
                                    f"Transcribe every question fully visible in this slice "
                                    f"(page {p+1}, slice {bi+1} of {a.bands}).", img)
                qs = (d or {}).get("questions") or []
                if qs:
                    return p, qs
            except Exception:
                time.sleep(1 + attempt)
        return p, []

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        raw = {}
        for p, qs in ex.map(one, jobs):
            raw.setdefault(p, []).extend(qs)

    # ---- flatten, keeping the best copy per (number, script) --------------------------------
    best = {}
    thin = []
    for p in pages:
        qs = raw.get(p) or []
        if len(qs) < 4:
            thin.append(p + 1)
        for q in qs:
            num = q.get("number")
            if not isinstance(num, int):
                continue
            rec = {"number": num, "page": p + 1, "stem": _clean(q.get("stem")),
                   "options": _norm_opts(q.get("options")),
                   "has_figure": bool(q.get("has_figure"))}
            if not rec["stem"] and not rec["options"]:
                continue
            k = (num, script_of(rec))
            if k not in best or richness(rec) > richness(best[k]):
                best[k] = rec

    # ---- merge the two scripts of the same question number ---------------------------------
    numbers = sorted({n for (n, _) in best})
    out = []
    for n in numbers:
        en, hi = best.get((n, "en")), best.get((n, "hi"))
        opts = (en or {}).get("options") or []
        opts_hi = (hi or {}).get("options") or []
        # gotcha #5: a mismatched pair desyncs a bilingual paper silently — drop rather than risk it.
        if opts and opts_hi and len(opts) != len(opts_hi):
            opts_hi = []
        hi_stem = (hi or {}).get("stem", "")
        rec = {
            "number": n,
            "page": (en or hi)["page"],
            "page_hi": (hi or {}).get("page"),
            "stem": (en or {}).get("stem", ""),
            "options": opts if en else [],
            "lang": "both" if (en and hi) else ("en" if en else "hi"),
            "type": "MCQ_single",
            "has_figure": bool((en or hi).get("has_figure")),
            "exam": a.exam, "subject": a.subject, "year": a.year,
            "source_pdf": os.path.basename(a.pdf),
            "layout": "facing_pages",
        }
        if a.hindi_verified:
            rec["stem_hi"], rec["options_hi"] = hi_stem, opts_hi
            rec["hindi_status"] = "verified"
        else:
            # Quarantine: keep every character we read, but under names nothing downstream reads,
            # so a wrong Devanagari proper noun cannot reach a student's paper by accident.
            rec["stem_hi"], rec["options_hi"] = "", []
            rec["stem_hi_unverified"], rec["options_hi_unverified"] = hi_stem, opts_hi
            rec["hindi_status"] = "unverified_ocr" if hi_stem else "absent"
        if not en and hi_stem:
            # A Hindi-only booklet has no English at all. There is no verbatim English to fall back
            # on, so the record carries no servable stem until the Hindi is reviewed. Say so.
            rec["note"] = "hindi-only source; no English printed in the booklet"
        out.append(rec)

    dst = a.out or os.path.splitext(a.pdf)[0] + "_EXTRACT.json"
    json.dump(out, io.open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    both = sum(1 for q in out if q["lang"] == "both")
    en_only = sum(1 for q in out if q["lang"] == "en")
    hi_only = sum(1 for q in out if q["lang"] == "hi")
    hi_any = sum(1 for q in out if q.get("stem_hi") or q.get("stem_hi_unverified"))
    servable = sum(1 for q in out if q["stem"] and q["options"])
    gaps = [n for n in range(min(numbers), max(numbers) + 1) if n not in set(numbers)] if numbers else []
    print(f"\n{len(out)} questions in {time.time()-t0:.0f}s")
    print(f"  bilingual pairs   : {both}")
    print(f"  English only      : {en_only}")
    print(f"  Hindi only        : {hi_only}")
    print(f"  English servable  : {servable}/{len(out)}   <- the real deliverable")
    print(f"  Hindi captured    : {hi_any}/{len(out)}"
          f"  ({'PROMOTED' if a.hindi_verified else 'QUARANTINED as *_unverified'})")
    print(f"  numbering         : {min(numbers) if numbers else '-'}..{max(numbers) if numbers else '-'}"
          f"  MISSING: {gaps or 'none'}")
    if thin:
        print(f"  ⚠ thin pages (<4 q): {thin}")
    print(f"  -> {dst}")


if __name__ == "__main__":
    main()
