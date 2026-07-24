#!/usr/bin/env python3
"""Triage chemistry diagram questions by FIGURE TYPE — from TEXT only (no image).

The go-forward diagram approach (see skill §DIAGRAMS GO-FORWARD) generates our OWN
clean figure from the text we already have, rather than reading the watermarked
getmarks image. This script measures the ADDRESSABLE population: of the chem
diagram questions, how many are "a molecular structure of a compound that is NAMED
or DERIVABLE from the stem/solution" — the subset OPSIN+RDKit can serve deterministically.

One cheap LLM pass over (stem + options + solution) returns, per question:
  figure_type          — molecular_structure | reaction_scheme | matching_table
                         | graph_plot | newman_sawhorse | apparatus | other
  compounds            — list of compound NAMES mentioned in the text (for OPSIN)
  recoverable          — is the figure's essential content reconstructable from text?
  opsin_addressable    — figure is structure(s)/scheme AND every needed compound is named

Runs ON the Gurukul box (LiteLLM proxy is local there). Sample mode by default.

    python3 triage_chem.py [--limit 60] [--exam NEET] [--full] [--out triage_chem.json]
"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qbank import config

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
MODEL = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o-mini")

SYS = r"""You triage CHEMISTRY exam questions that originally had a FIGURE. You are given
the question text, options, and worked solution (NOT the figure). Classify what the
missing figure most likely was, and whether we could REBUILD it from the text alone.

figure_type — pick ONE:
  "molecular_structure" : the figure is one or more 2D molecular structures (skeletal or
                          condensed), e.g. "the structure of the product", an options panel
                          of candidate molecules, a labelled organic compound.
  "reaction_scheme"     : reactant(s) -> product(s) drawn as structures / a mechanism arrow-push.
  "matching_table"      : a Column-I / Column-II match table (text, not a real drawing).
  "graph_plot"          : axes + curve(s): P-V, energy diagram, titration curve, rate plot.
  "newman_sawhorse"     : a Newman projection or sawhorse/conformational drawing.
  "apparatus"           : lab apparatus / experimental setup drawing.
  "other"               : anything else (crystal lattice, geometry, etc.).

compounds — list every CHEMICAL COMPOUND NAME that appears in the stem or solution and would
  be needed to redraw the structure(s). Use the exact name/formula as written (IUPAC name,
  common name, or formula like "XeF4"). [] if none / not a structure question.

recoverable — true if the figure's ESSENTIAL content is reconstructable from the text
  (compounds are named, table is spelled out, graph values are stated). false if the figure
  carries data present NOWHERE in the text (e.g. "the compound shown below" with no name).

opsin_addressable — true ONLY if figure_type is molecular_structure or reaction_scheme AND
  every compound needed is NAMED (so OPSIN name->structure can rebuild it). false otherwise.

Return ONLY JSON:
{"figure_type":"...","compounds":["..."],"recoverable":true|false,"opsin_addressable":true|false,"note":"<=12 words"}"""


def classify(stem, options, solution):
    opt = ""
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    user = f"STEM: {stem}\n\nOPTIONS: {opt[:800]}\n\nSOLUTION: {(solution or '')[:1400]}"
    body = json.dumps({"model": MODEL, "temperature": 0,
                       "messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": user}],
                       "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request(PROXY, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=90))
    return json.loads(r["choices"][0]["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--exam", default=None)
    ap.add_argument("--full", action="store_true", help="all chem diagram Qs, ignore --limit")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="/tmp/triage_chem.json")
    args = ap.parse_args()

    c = sqlite3.connect(config.DB_PATH)
    c.execute("PRAGMA busy_timeout=30000")
    q = """SELECT id, exam, chapter, stem, options, correct_answer, solution FROM questions
           WHERE subject='Chemistry' AND needs_figure=1 AND verified=1
           AND solution IS NOT NULL AND length(solution)>40"""
    params = []
    if args.exam:
        q += " AND exam=?"; params.append(args.exam)
    # stratified-ish: order by exam then id so a --limit sample spans exams
    q += " ORDER BY exam, id"
    rows = c.execute(q, params).fetchall()
    if not args.full:
        # take an even slice across the ordered list (spans exams)
        step = max(1, len(rows) // args.limit)
        rows = rows[::step][:args.limit]
    print(f"[triage] classifying {len(rows)} chem diagram questions "
          f"({'FULL' if args.full else 'sample'})", flush=True)

    results = []

    def work(row):
        qid, exam, chapter, stem, options, ans, sol = row
        try:
            v = classify(stem, options, sol)
        except Exception as e:
            v = {"figure_type": "ERROR", "compounds": [], "recoverable": False,
                 "opsin_addressable": False, "note": str(e)[:60]}
        return {"id": qid, "exam": exam, "chapter": chapter, **v}

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, r): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            results.append(f.result())
            if i % 10 == 0:
                print(f"  {i}/{len(rows)}", flush=True)

    json.dump(results, open(args.out, "w"), indent=1)

    # aggregate
    from collections import Counter
    by_type = Counter(r["figure_type"] for r in results)
    addr = sum(1 for r in results if r.get("opsin_addressable"))
    recov = sum(1 for r in results if r.get("recoverable"))
    print("\n=== FIGURE TYPE DISTRIBUTION ===")
    for t, n in by_type.most_common():
        print(f"  {t:22s} {n:4d}  ({100*n//len(results)}%)")
    print(f"\n  OPSIN-addressable : {addr}/{len(results)} = {100*addr//max(1,len(results))}%")
    print(f"  recoverable-from-text : {recov}/{len(results)} = {100*recov//max(1,len(results))}%")
    print(f"\n[triage] wrote {args.out}")
    # per-exam addressable
    exams = sorted(set(r["exam"] for r in results))
    for e in exams:
        er = [r for r in results if r["exam"] == e]
        ea = sum(1 for r in er if r.get("opsin_addressable"))
        print(f"    {e:16s} addressable {ea}/{len(er)}")


if __name__ == "__main__":
    main()
