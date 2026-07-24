#!/usr/bin/env python3
"""Classify diagram questions by TYPE (renderer-aligned) via a vision LLM.

Reads a proportional sample of banked diagram questions (figure + stem) and buckets each
into a type that maps to a clean-figure RENDERER, so we know where the volume is before
building the redraw pipeline. Calls the LiteLLM proxy directly (localhost:4000) with a
thread pool — no shared LLM state.

    python3 classify_diagrams.py [--per-cell 60] [--workers 10] [--out /tmp/diag_types.json]
"""
import argparse
import base64
import collections
import json
import os
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from qbank import config

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
MODEL = os.environ.get("QBANK_VISION_MODEL", "gpt-4o-mini")

TYPES = [
    "circuit",            # resistors/capacitors/batteries/Wheatstone  -> schemdraw
    "graph_plot",         # x-y function graph, P-V/PT, v-t/x-t motion  -> matplotlib
    "ray_optics",         # lenses/mirrors/prisms/ray diagrams          -> SVG/TikZ
    "mechanics_setup",    # blocks/pulleys/incline/springs/free-body    -> SVG/TikZ
    "field_diagram",      # E/B field lines, charges layout             -> SVG/matplotlib
    "geometry",           # pure geometric figure (math)                -> SVG/TikZ
    "org_chem_structure", # molecular structure / benzene ring          -> RDKit
    "reaction_scheme",    # chemical reaction with arrows/conditions     -> RDKit/chemfig
    "data_chart",         # bar/pie/pyramid/flowchart                    -> matplotlib
    "biology_diagram",    # anatomical/cell/organism/cycle              -> SVG (hard)
    "table_matching",     # list-I/II or data TABLE captured as image    -> HTML table (not a diagram)
    "other",
]

SYS = (
    "You are triaging exam-paper figures so an engineer can pick the right tool to REDRAW each "
    "one cleanly. Given the figure image and the question text, classify the figure into EXACTLY "
    "one type from this list:\n- " + "\n- ".join(TYPES) + "\n"
    "Return JSON {\"type\":\"<one type>\", \"labels_readable\": true|false, "
    "\"redraw_difficulty\": \"easy|medium|hard\", \"confidence\": \"high|medium|low\"}. "
    "labels_readable = are the numbers/labels in the figure legible (not obscured by watermark)? "
    "redraw_difficulty = how hard to reproduce faithfully as clean vector/code."
)


def classify(qid, stem, fpath):
    try:
        data = open(fpath, "rb").read()
        ext = fpath.rsplit(".", 1)[-1].lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
        b64 = base64.b64encode(data).decode()
        body = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYS},
                {"role": "user", "content": [
                    {"type": "text", "text": "QUESTION: " + stem[:500]},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ]},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }).encode()
        req = urllib.request.Request(PROXY, data=body, headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
        r = json.load(urllib.request.urlopen(req, timeout=90))
        out = json.loads(r["choices"][0]["message"]["content"])
        t = out.get("type", "other")
        return qid, (t if t in TYPES else "other"), out
    except Exception as e:
        return qid, None, {"err": str(e)[:80]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=60, help="sample per (exam,subject)")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="/tmp/diag_types.json")
    args = ap.parse_args()

    c = sqlite3.connect(config.DB_PATH)
    c.execute("PRAGMA busy_timeout=30000")
    cells = c.execute("""SELECT DISTINCT exam, subject FROM questions
        WHERE verified=1 AND generated=0 AND duplicate_of IS NULL AND figure_url LIKE '%/figures/%'""").fetchall()
    jobs = []
    for exam, subj in cells:
        rows = c.execute("""SELECT id, stem, figure_refs FROM questions
            WHERE exam=? AND subject=? AND verified=1 AND generated=0 AND duplicate_of IS NULL
              AND figure_url LIKE '%/figures/%' ORDER BY id LIMIT ?""", (exam, subj, args.per_cell)).fetchall()
        for qid, stem, refs in rows:
            try:
                fn = json.loads(refs or "[]")[0]
            except Exception:
                continue
            fp = os.path.join(config.FIG_DIR, fn)
            if os.path.exists(fp):
                jobs.append((exam, subj, qid, stem or "", fp))
    print(f"[classify] {len(jobs)} figures across {len(cells)} exam×subject cells | model={MODEL}")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(classify, j[2], j[3], j[4]): j for j in jobs}
        for fut in as_completed(futs):
            exam, subj, qid, _, _ = futs[fut]
            _, t, meta = fut.result()
            if t:
                results.append({"exam": exam, "subject": subj, "id": qid, "type": t,
                                "labels_readable": meta.get("labels_readable"),
                                "difficulty": meta.get("redraw_difficulty")})
            done += 1
            if done % 50 == 0:
                print(f"  classified {done}/{len(jobs)}")

    json.dump(results, open(args.out, "w"))
    ok = len(results)
    print(f"\n[classify] done: {ok}/{len(jobs)} classified\n")

    # ---- report ----
    by_type = collections.Counter(r["type"] for r in results)
    print("TYPE DISTRIBUTION (sample):")
    for t, n in by_type.most_common():
        easy = sum(1 for r in results if r["type"] == t and r["difficulty"] == "easy")
        rd = sum(1 for r in results if r["type"] == t and r["labels_readable"])
        print(f"  {t:20s} {n:4d}  ({100*n/ok:4.1f}%)  easy={easy:<4d} labels_readable={rd}")
    print("\nBY EXAM × TYPE (top types):")
    top = [t for t, _ in by_type.most_common(6)]
    exams = sorted(set(r["exam"] for r in results))
    print(f"  {'type':20s}" + "".join(f"{e[:12]:>14s}" for e in exams))
    for t in top:
        row = "".join(f"{sum(1 for r in results if r['type']==t and r['exam']==e):>14d}" for e in exams)
        print(f"  {t:20s}{row}")


if __name__ == "__main__":
    main()
