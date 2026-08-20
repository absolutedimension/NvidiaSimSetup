#!/usr/bin/env python3
"""Extract REAL, BILINGUAL questions from official BSSC question booklets.

These booklets print every question TWICE — once in Hindi, once in English — as one numbered
question. That is a gift: it gives us authentic Hindi *and* English for the same real question,
which is exactly what `Question.stem_hi` / `options_hi` were added for. No translation involved.

Three fixes over the generic `extractor.from_pdf` path, each from an observed failure:

  1. UNDER-EXTRACTION. The generic prompt returned 2 questions from a page holding ~5, because it
     treated the Hindi and English halves as ambiguous. The prompt now states the bilingual layout
     explicitly, and every page is re-asked once if it yields fewer than `MIN_PER_PAGE`, with the
     numbers already seen passed back so the model knows what it missed.

  2. LATEX EATEN BY JSON. The model writes `\\frac` inside a JSON string without escaping the
     backslash, so `json.loads` turns "\\f" into a form-feed and the option becomes "\x0crac{...}".
     Every extracted string is run through `models.repair_latex`, which maps those control
     characters back to their TeX commands.

  3. HINDI OPTIONS DROPPED. The model copied the English options into `options_hi`. The prompt now
     requires the Hindi options as printed, and we only keep `options_hi` when it is the same
     length as `options` — a mismatched pair would silently desync the bilingual paper.

Usage:
    python3 extract_bssc.py <paper.pdf> --exam "BSSC" --subject "General Studies" \
        [--year 2025] [--out out.json] [--dpi 220] [--max-pages N]
"""
import argparse
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank.llm import LLM                      # noqa: E402
from qbank.models import repair_latex          # noqa: E402

MIN_PER_PAGE = 3          # a full question page in these booklets carries ~4-6

BILINGUAL_SYS = (
    "You are parsing ONE page of an official BIHAR STAFF SELECTION COMMISSION (BSSC) exam booklet.\n"
    "CRITICAL: the paper is BILINGUAL. Every question is printed TWICE on the page — once in HINDI "
    "(Devanagari) and once in ENGLISH — and those two are the SAME numbered question, NOT two "
    "questions. Merge them into ONE entry.\n"
    "Return EVERY numbered question that appears on this page. A full page usually has 4 to 6 "
    "questions — if you return fewer, you have missed some; look again at the whole page.\n"
    'Return JSON: {"questions":[{"number":int,"stem":"English stem","stem_hi":"Hindi stem",'
    '"options":[{"label":"A","text":"English option"}],'
    '"options_hi":[{"label":"A","text":"Hindi option"}],'
    '"type":"MCQ_single","has_figure":false}]}\n'
    "RULES:\n"
    "- options and options_hi MUST have the SAME number of entries, in the SAME order, same labels.\n"
    "- Copy the Hindi option text AS PRINTED. If an option is purely numeric or a formula it will "
    "look identical in both — that is fine, repeat it.\n"
    "- Write maths as LaTeX and ESCAPE EVERY BACKSLASH for JSON: write \\\\frac, not \\frac.\n"
    "- If a question's numbering continues from the previous page, still return it with its number.\n"
    "- Never invent a question, an option, or a translation that is not printed on the page."
)


def _clean(s):
    return repair_latex(str(s or "")).strip()


def _norm_opts(raw):
    out = []
    for o in raw or []:
        if isinstance(o, dict):
            out.append({"label": str(o.get("label") or "").strip().upper()[:2],
                        "text": _clean(o.get("text"))})
        else:
            out.append({"label": "", "text": _clean(o)})
    return [o for o in out if o["text"]]


def parse_page(llm, img, pageno, seen_numbers):
    hint = ""
    if seen_numbers:
        hint = (f" Questions already captured elsewhere: {sorted(seen_numbers)[-6:]}. "
                "Return any question on THIS page even if numbering looks out of order.")
    d = llm.vision_json(BILINGUAL_SYS, f"Parse page {pageno}.{hint}", img)
    return (d or {}).get("questions", []) or []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--exam", default="BSSC")
    ap.add_argument("--subject", default="General Studies")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dpi", type=int, default=220)
    ap.add_argument("--max-pages", type=int, default=0)
    a = ap.parse_args()

    import pymupdf
    llm = LLM()
    if not llm.ok:
        sys.exit("vision LLM not reachable — export QBANK_LLM=on and the proxy vars")

    doc = pymupdf.open(a.pdf)
    pages = len(doc) if not a.max_pages else min(a.max_pages, len(doc))
    out, seen, retried = [], set(), 0
    t0 = time.time()

    for pno in range(pages):
        img = doc[pno].get_pixmap(dpi=a.dpi).tobytes("png")
        qs = parse_page(llm, img, pno + 1, seen)
        # FIX 1: a thin page is usually a miss, not an empty page — ask once more.
        if len(qs) < MIN_PER_PAGE:
            again = parse_page(llm, img, pno + 1, seen | {q.get("number") for q in qs})
            if len(again) > len(qs):
                qs, _ = again, None
                retried += 1
        kept = 0
        for q in qs:
            stem = _clean(q.get("stem")) or _clean(q.get("stem_hi"))
            if not stem:
                continue
            opts = _norm_opts(q.get("options"))
            opts_hi = _norm_opts(q.get("options_hi"))
            # FIX 3: only keep the Hindi options if they actually pair up.
            if len(opts_hi) != len(opts):
                opts_hi = []
            num = q.get("number")
            if isinstance(num, int) and num in seen:
                continue
            if isinstance(num, int):
                seen.add(num)
            out.append({
                "number": num, "page": pno + 1,
                "stem": _clean(q.get("stem")), "stem_hi": _clean(q.get("stem_hi")),
                "options": opts, "options_hi": opts_hi,
                "type": q.get("type") or "MCQ_single",
                "has_figure": bool(q.get("has_figure")),
                "exam": a.exam, "subject": a.subject, "year": a.year,
                "source_pdf": os.path.basename(a.pdf),
            })
            kept += 1
        print(f"  page {pno+1:3d}/{pages}: {kept:2d} questions  (total {len(out)})", flush=True)

    dst = a.out or os.path.splitext(a.pdf)[0] + "_EXTRACT.json"
    json.dump(out, io.open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hi = sum(1 for q in out if q["stem_hi"])
    hio = sum(1 for q in out if q["options_hi"])
    nums = [q["number"] for q in out if isinstance(q["number"], int)]
    gaps = []
    if nums:
        lo, hi_n = min(nums), max(nums)
        gaps = [n for n in range(lo, hi_n + 1) if n not in set(nums)]
    print(f"\n{len(out)} questions in {time.time()-t0:.0f}s  (retried {retried} thin pages)")
    print(f"  with Hindi stem   : {hi}/{len(out)}")
    print(f"  with Hindi options: {hio}/{len(out)}")
    print(f"  numbering: {min(nums) if nums else '-'}..{max(nums) if nums else '-'}  missing: {gaps or 'none'}")
    print(f"  -> {dst}")


if __name__ == "__main__":
    main()
