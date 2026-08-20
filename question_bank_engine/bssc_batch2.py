#!/usr/bin/env python3
"""Batch-extract and key the 2016-2018 BSSC booklets (the facing-page layout).

`bssc_batch.py` drove the 2022-2025 papers, where the question booklet and the आदर्श उत्तर arrive
as TWO separate PDFs, so its PAIRS list is (paper, keyfile). That list cannot express this set,
for two reasons found by probing every page of every file:

  1. MOST OF THESE CARRY THE KEY INSIDE THE SAME PDF — usually the last page, but PHARMACY puts it
     on page 1. So a key source here is a (file, pages) pair, and the file is often the paper
     itself. `key` below is either "self" or another filename; `key_pages` says which pages.

  2. The question pages are a SUBSET of the file. These booklets open with a cover and
     instructions and close with OMR samples and rough-work pages. Extracting those wastes vision
     calls and invites junk, so every entry carries the measured question page range.

Both fields come from the full-page sweep in PDF_STRUCTURE_FULL.json, which classified all 325
pages rather than guessing from filenames (gotcha #8: the filename is the booklet series, not the
exam). They are written out literally here so the run is auditable without re-probing.

The Hindi stays quarantined — see extract_bssc_paired.py's docstring for the measured reason.

NOT IN THIS LIST, deliberately: JE-0411-QB-GK-GS.pdf, JE-0411-QB-Civil.pdf and
JE-0411-QB-Mechanical.pdf. Those are the commission's 2016 booklet-only releases of the SAME three
JE papers; there is no JE-0411-MA-* key file anywhere on the notice board, which is why the earlier
attempt to download "the three JE keys" could not succeed. In 2018 the commission re-published all
three as "Test Booklet AND Model Answer" at Advertisement/gk.PDF, civil.PDF and mechanical.PDF
(uppercase .PDF — the lowercase spelling 404s). Those combined files are what this list uses, so
the three booklet-only PDFs are redundant duplicates carrying no answers.
"""
import io
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
IN = os.path.expanduser("~/bssc_in")

# file, question pages, key source, key pages, label, subject, year
PAPERS = [
    # ---- GK first: General Studies is the binding constraint on how many papers we can build ----
    ("GK1.PDF",                  "3-28",  "self", "29",  "BSSC GK Booklet (Advt 3646)",      "General Studies", 2016),
    ("GK(3649).PDF",             "6-31",  "self", "32",  "BSSC GK Kara Mishrak (Advt 3649)", "General Studies", 2016),
    ("G.K_and_N.A_M.A.PDF",      "4-45",  "self", "49",  "BSSC GK & Numerical Ability",      "General Studies", 2017),
    # the commission's own link for this paper's Model Answer (01010116-MA-GK.pdf) is a dead 404,
    # so these 150 GS questions can be mined for the blueprint but NOT served as practice.
    ("01010116-QB-GK.pdf",       "4-21",  None,   None,  "BSSC Asst Teacher GK (01010116)",  "General Studies", 2016),
    ("JE-0411-GK-QB-AND-MA.pdf", "10-35", "self", "37",  "BSSC JE GK/GS (Advt 0411)",        "General Studies", 2018),
    # ---- Hindi subject paper: feeds the Hindi SECTION (its questions are ABOUT Hindi) ----------
    ("hindi1.PDF",               "2-11",  "self", "12",  "BSSC Hindi Booklet (Advt 3646)",   "Hindi",           2016),
    # ---- Maths ---------------------------------------------------------------------------------
    ("maths.PDF",                "2-27",  "self", "29",  "BSSC Maths Booklet (Advt 3646)",   "Mathematics",     2016),
    # ---- Technical posts: least reusable, extracted last ---------------------------------------
    ("JE-0411-CIVIL-QB-AND-MA.pdf", "4-37", "self", "41", "BSSC JE Civil (Advt 0411)",        "Civil Engineering", 2018),
    ("JE-0411-MECH-QB-AND-MA.pdf", "4-37",  "self", "41", "BSSC JE Mechanical (Advt 0411)",   "Mechanical Engineering", 2018),
    ("CHEMISTRY_M.A.PDF",        "4-66",  "self", "71",  "BSSC Chemistry",                   "Chemistry",       2017),
    ("PHARMACY.PDF",             "6-23",  "self", "1",   "BSSC Pharmacy",                    "Pharmacy",        2017),
]

KEY_SYS = ("You are reading an official ANSWER KEY (आदर्श उत्तर / Model Answer) page from a Bihar "
           "SSC exam booklet. It is a grid/table of question numbers and their correct option "
           'letters. Extract EVERY pair. Return JSON {"key":{"1":"A","2":"C",...}} using the '
           "printed question number and the printed option letter (A/B/C/D). Read every column of "
           "the grid, left to right and top to bottom. Do not guess and do not skip a row.")

STRUCT = os.path.join(IN, "PDF_STRUCTURE_FULL.json")


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
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
    return sorted(p for p in out if 0 <= p < n)


def read_key(llm, path, pages_spec):
    """Read the key grid. `pages_spec` may be None -> fall back to the probed structure, then to
    a scan of the whole file (small, and only for the JE files whose layout we did not pre-measure)."""
    import pymupdf
    d = pymupdf.open(path)
    pages = parse_pages(pages_spec, len(d))
    key = {}
    for i in pages:
        # keys are dense grids: crop-free but high dpi, and ask twice if the first read is thin
        for dpi in (260, 400):
            img = d[i].get_pixmap(dpi=dpi).tobytes("png")
            try:
                r = llm.vision_json(KEY_SYS, f"Extract every number->letter pair on page {i+1}.", img)
            except Exception:
                r = None
            got = 0
            for k, v in ((r or {}).get("key") or {}).items():
                k = "".join(ch for ch in str(k) if ch.isdigit())
                v = str(v).strip().upper()[:1]
                if k and v in "ABCDE":
                    key[int(k)] = v
                    got += 1
            if got >= 40:        # a full key page carries 100-150 pairs; a thin read means retry
                break
    return key


def find_key_pages(fn):
    """Key pages measured by the full-page sweep, when we have it."""
    try:
        s = json.load(io.open(STRUCT, encoding="utf-8"))
        kp = (s.get(fn) or {}).get("key_pages") or []
        return ",".join(str(p) for p in kp) or None
    except Exception:
        return None


def find_q_pages(fn):
    try:
        s = json.load(io.open(STRUCT, encoding="utf-8"))
        qp = (s.get(fn) or {}).get("question_pages") or []
        return f"{min(qp)}-{max(qp)}" if qp else None
    except Exception:
        return None


def main():
    from qbank.llm import LLM
    llm = LLM()
    if not llm.ok:
        sys.exit("vision LLM not reachable")
    only = set(sys.argv[1:])
    summary = []
    for fn, qpages, keysrc, kpages, label, subject, year in PAPERS:
        if only and fn not in only:
            continue
        path = os.path.join(IN, fn)
        if not os.path.exists(path):
            print(f"SKIP {label}: {fn} missing"); continue
        stem = os.path.splitext(fn)[0].replace("(", "").replace(")", "").replace(".", "_")
        ex_out = os.path.join(IN, stem + "_EXTRACT.json")
        dst = os.path.join(IN, stem + "_KEYED.json")
        qpages = qpages or find_q_pages(fn)
        t0 = time.time()
        print(f"\n=== {label}  [{fn}] ===", flush=True)

        if not os.path.exists(ex_out):
            cmd = [sys.executable, "extract_bssc_paired.py", path, "--exam", "BSSC",
                   "--subject", subject, "--year", str(year), "--out", ex_out,
                   "--dpi", "400", "--bands", "3"]
            if qpages:
                cmd += ["--pages", qpages]
            r = subprocess.run(cmd, capture_output=True, text=True)
            print((r.stdout or "")[-900:] or (r.stderr or "")[-600:], flush=True)
        try:
            qs = json.load(io.open(ex_out, encoding="utf-8"))
        except Exception as e:
            print("  extract failed:", e); continue

        key = {}
        if keysrc:
            kpath = path if keysrc == "self" else os.path.join(IN, keysrc)
            spec = kpages or find_key_pages(fn)
            try:
                key = read_key(llm, kpath, spec)
            except Exception as e:
                print("  key read failed:", e)
            print(f"  key source: {os.path.basename(kpath)} pages {spec or 'ALL'} "
                  f"-> {len(key)} entries", flush=True)
        else:
            print("  NO KEY AVAILABLE — the commission's link for this key is dead (404)", flush=True)

        keyed = 0
        for q in qs:
            n = q.get("number")
            ans = key.get(n) if isinstance(n, int) else None
            labels = [o["label"] for o in q.get("options") or []]
            q["correct_answer"] = ans if (ans and (not labels or ans in labels)) else ""
            q["paper_label"] = label
            keyed += bool(q["correct_answer"])
        json.dump(qs, io.open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

        servable = sum(1 for q in qs if q.get("stem") and q.get("options"))
        hi = sum(1 for q in qs if q.get("stem_hi_unverified") or q.get("stem_hi"))
        nums = sorted(q["number"] for q in qs if isinstance(q.get("number"), int))
        gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)] if nums else []
        summary.append({"paper": label, "file": fn, "questions": len(qs), "english_servable": servable,
                        "hindi_captured_unverified": hi, "keyed": keyed, "key_entries": len(key),
                        "numbering": f"{nums[0]}-{nums[-1]}" if nums else "-",
                        "gaps": gaps, "secs": round(time.time() - t0)})
        print(f"  -> {len(qs)} q | EN servable {servable} | HI captured {hi} | KEYED {keyed} "
              f"| gaps {gaps or 'none'} | {time.time()-t0:.0f}s", flush=True)

    out = os.path.join(IN, "BATCH2_SUMMARY.json")
    json.dump(summary, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n===== SUMMARY =====")
    tq = tk = te = 0
    for s in summary:
        print(f"  {s['paper']:36s} {s['questions']:4d} q  EN {s['english_servable']:4d}  "
              f"KEYED {s['keyed']:4d}  gaps {len(s['gaps'])}")
        tq += s["questions"]; tk += s["keyed"]; te += s["english_servable"]
    print(f"  {'TOTAL':36s} {tq:4d} q  EN {te:4d}  KEYED {tk:4d}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
