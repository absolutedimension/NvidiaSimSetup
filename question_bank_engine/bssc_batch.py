#!/usr/bin/env python3
"""Batch: extract every BSSC paper bilingually, read its official key, and match the two.

One pair per run of the loop so a failure on one paper never costs the others. Writes
<stem>_KEYED.json per paper plus a summary, and prints the honest per-paper yield: how many
questions came out, how many carry Hindi, and how many got an OFFICIAL answer.
"""
import io
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
IN = os.path.expanduser("~/bssc_in")

# (question paper, official key, label, subject)
PAIRS = [
    ("3102059_10_I.pdf", "10_Model.pdf",     "BSSC 10th Level 2024",        "General Studies"),
    ("5101136_08_A.pdf", "08_Model.pdf",     "BSSC 8th Level 2024",         "General Studies"),
    ("Qn_SET_A.pdf",     "Model_ans.pdf",    "BSSC Office Attendant 02/22", "General Studies"),
    ("03_25_SET_A.pdf",  "03_25_Model_Ans.pdf", "BSSC Field Assistant 03/25", "General Studies"),
]

KEY_SYS = ("You are reading an official ANSWER KEY (आदर्श उत्तर) page from a Bihar SSC exam. "
           "It is a grid/table of question numbers and their correct option letters. Extract EVERY "
           'pair. Return JSON {"key":{"1":"A","2":"C",...}} using the printed question number and '
           "the printed option letter (A/B/C/D). Read every column of the grid. Do not guess or skip.")


def read_key(llm, path):
    import pymupdf
    d = pymupdf.open(path)
    key = {}
    for i in range(len(d)):
        img = d[i].get_pixmap(dpi=260).tobytes("png")
        r = llm.vision_json(KEY_SYS, f"Extract every question-number to answer-letter pair on page {i+1}.", img)
        for k, v in ((r or {}).get("key") or {}).items():
            k = "".join(ch for ch in str(k) if ch.isdigit())
            v = str(v).strip().upper()[:1]
            if k and v in "ABCDE":
                key[int(k)] = v
    return key


def main():
    from qbank.llm import LLM
    llm = LLM()
    if not llm.ok:
        sys.exit("vision LLM not reachable")
    summary = []
    for paper, keyfile, label, subject in PAIRS:
        p_in, k_in = os.path.join(IN, paper), os.path.join(IN, keyfile)
        if not os.path.exists(p_in):
            print(f"SKIP {label}: {paper} missing"); continue
        stem = os.path.splitext(paper)[0]
        ex_out = os.path.join(IN, stem + "_EXTRACT.json")
        t0 = time.time()
        print(f"\n=== {label} ===", flush=True)
        if not os.path.exists(ex_out):
            r = subprocess.run([sys.executable, "extract_bssc.py", p_in, "--exam", "BSSC",
                                "--subject", subject, "--year", "2025", "--out", ex_out],
                               capture_output=True, text=True)
            print(r.stdout[-700:] or r.stderr[-500:], flush=True)
        try:
            qs = json.load(io.open(ex_out, encoding="utf-8"))
        except Exception as e:
            print("  extract failed:", e); continue
        try:
            key = read_key(llm, k_in)
        except Exception as e:
            print("  key read failed:", e); key = {}
        keyed = 0
        for q in qs:
            n = q.get("number")
            a = key.get(n) if isinstance(n, int) else None
            labels = [o["label"] for o in q.get("options") or []]
            q["correct_answer"] = a if (a and a in labels) else ""
            q["paper_label"] = label
            keyed += bool(q["correct_answer"])
        dst = os.path.join(IN, stem + "_KEYED.json")
        json.dump(qs, io.open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        hi = sum(1 for q in qs if q.get("stem_hi"))
        hio = sum(1 for q in qs if q.get("options_hi"))
        summary.append({"paper": label, "questions": len(qs), "hindi_stem": hi,
                        "hindi_options": hio, "keyed": keyed, "key_entries": len(key),
                        "secs": round(time.time() - t0)})
        print(f"  -> {len(qs)} q | hindi {hi} | hindi-opts {hio} | KEYED {keyed} "
              f"| key had {len(key)} | {time.time()-t0:.0f}s", flush=True)
    json.dump(summary, io.open(os.path.join(IN, "BATCH_SUMMARY.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n===== SUMMARY =====")
    tq = tk = th = 0
    for s in summary:
        print(f"  {s['paper']:32s} {s['questions']:4d} q  hindi {s['hindi_stem']:4d}  KEYED {s['keyed']:4d}")
        tq += s["questions"]; tk += s["keyed"]; th += s["hindi_stem"]
    print(f"  {'TOTAL':32s} {tq:4d} q  hindi {th:4d}  KEYED {tk:4d}")


if __name__ == "__main__":
    main()
