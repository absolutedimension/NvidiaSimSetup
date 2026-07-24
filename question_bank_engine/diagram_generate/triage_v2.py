#!/usr/bin/env python3
"""Richer diagram triage — map every diagram question to the APPROACH that could rebuild it.

Beyond triage_chem.py's coarse types, this sorts each question into an approach-relevant
bucket and flags recoverability, so we can estimate how much of the diagram pool each
generation technique could serve. Text-only (stem+options+answer+solution), no image.

    python3 triage_v2.py [--subject Chemistry] [--exam NEET] [--limit 200] [--out ...]
"""
import argparse, json, os, sqlite3, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qbank import config

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
MODEL = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o-mini")

SYS = r"""You triage exam questions that originally had a FIGURE (the figure is gone; you get only
text). Sort the MISSING figure into ONE bucket. Be STRICT about recoverability.

CRITICAL TEST for `recoverable`: could you REDRAW the figure using ONLY the text? That means every
visual entity the figure showed must be NAMED or fully SPECIFIED in the stem/options/solution.
- If the question compares / orders / counts entities that appear ONLY as labels — "i, ii, iii",
  "X and Y", "a, b, c, d", "(A)(B)(C)", "the compound shown", "the following carbocation" — and
  those entities are NOT given as names/formulas/SMILES anywhere in the text, then recoverable=FALSE.
  A solution that merely states the ANSWER ORDER ("iii < i < ii") does NOT make it recoverable —
  you still cannot draw i, ii, iii.
- recoverable=TRUE only when you could actually reproduce the figure: compounds are NAMED, the
  reaction's reactants/products are NAMED, the table's rows are spelled out in text, or the graph's
  axes AND curve behaviour are fully stated.

bucket — pick ONE:
  "mol_named"      : molecular structure(s), and EVERY compound is named/derivable in text.
  "mol_labelled"   : molecular structure(s) compared/referenced only by LABELS (i, X, a...) with
                     the structures NOT named in text -> you'd need the original image.
  "reaction"       : a reaction as structures (reactant->product / mechanism).
  "graph"          : axes + curve(s): P-V, energy/Ellingham, titration/rate/plot.
  "table"          : a Column-I/II match or data table.
  "apparatus"      : lab apparatus / setup / electrochemical cell.
  "struct_diagram" : non-molecule drawing: MO diagram, crystal lattice, VSEPR/3D geometry, Newman.
  "no_fig_needed"  : answerable from a STANDARD fact/formula with NO reference to any labelled
                     entity in the figure (RARE — do NOT use it just because the solution reasons).
  "other"          : none of the above.

Return ONLY JSON: {"bucket":"...","recoverable":true|false,"note":"<=10 words"}"""


def classify(stem, options, solution):
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    user = f"STEM: {stem}\n\nOPTIONS: {opt[:700]}\n\nSOLUTION: {(solution or '')[:1300]}"
    body = json.dumps({"model": MODEL, "temperature": 0, "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(PROXY, data=body, headers={"Content-Type": "application/json",
                                                            "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=90))
    return json.loads(r["choices"][0]["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", default="Chemistry")
    ap.add_argument("--exam", default=None)
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="/tmp/triage_v2.json")
    args = ap.parse_args()

    c = sqlite3.connect(config.DB_PATH); c.execute("PRAGMA busy_timeout=30000")
    q = ("SELECT id, exam, stem, options, solution FROM questions WHERE subject=? AND verified=1 "
         "AND needs_figure=1 AND (figure_url IS NULL OR figure_url NOT LIKE '%.gen.png')")
    params = [args.subject]
    if args.exam:
        q += " AND exam=?"; params.append(args.exam)
    q += " ORDER BY exam, id"
    allrows = c.execute(q, params).fetchall()
    step = max(1, len(allrows) // args.limit)
    rows = allrows[::step][:args.limit]
    print(f"[triage-v2] {len(rows)} {args.subject} diagram Qs (of {len(allrows)} remaining)", flush=True)

    results = []
    def work(r):
        qid, exam, stem, options, solution = r
        try:
            v = classify(stem, options, solution)
        except Exception as e:
            v = {"bucket": "ERROR", "recoverable": False, "note": str(e)[:40]}
        return {"id": qid, "exam": exam, **v}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, r): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            results.append(f.result())
            if i % 25 == 0: print(f"  {i}/{len(rows)}", flush=True)
    json.dump(results, open(args.out, "w"), indent=1)

    n = len(results)
    buckets = Counter(r["bucket"] for r in results)
    print("\n=== BUCKET DISTRIBUTION ===")
    for b, k in buckets.most_common():
        rec = sum(1 for r in results if r["bucket"] == b and r.get("recoverable"))
        print(f"  {b:16s} {k:4d} ({100*k//n:3d}%)   recoverable-from-text: {rec}/{k}")
    print(f"\n  total recoverable-from-text: {sum(1 for r in results if r.get('recoverable'))}/{n}")
    print(f"[triage-v2] wrote {args.out}")


if __name__ == "__main__":
    main()
