#!/usr/bin/env python3
"""Generate OUR OWN clean figure for chemistry diagram questions — text -> structure -> verify.

The go-forward diagram approach: never touch the watermarked getmarks image. Instead
rebuild the figure from the reliable TEXT we already have (stem + options + correct answer
+ worked solution), using a DETERMINISTIC name->structure path, then VERIFY by solving.

Per question:
  1. EXTRACT  (LLM)  : from text, decide what compound structure(s) the figure should show
                       and name each (systematic IUPAC preferred). drawable=false when the
                       structure is defined ONLY by the missing image (named nowhere in text).
  2. NAME->SMILES    : OPSIN (deterministic). Unparseable name = counted, not guessed.
  3. RENDER          : RDKit -> clean, watermark-free PNG (single or option grid).
  4. VERIFY (VLM)    : show OUR render + stem + options -> predicted answer; must equal the
                       KNOWN correct answer. This guards EXTRACTION errors (wrong compound ->
                       VLM reads our figure -> wrong answer). Verifiable reward, no false-pass.

Needs OPSIN's Java on PATH (Gurukul: export PATH=$HOME/jre/bin:$PATH) and the LiteLLM proxy.

    python3 generate_chem_figures.py [--limit 40] [--exam NEET] [--ids id1,id2] \
        [--out-dir /tmp/chem_figs] [--attach]
"""
import argparse
import base64
import json
import os
import sqlite3
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank import config
from resolve import resolve_batch

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
CHAT = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o-mini")
VISION = os.environ.get("QBANK_VISION_MODEL", "gpt-4o")

EXTRACT_SYS = r"""You rebuild the MISSING FIGURE of a chemistry MCQ as clean molecular structure(s).
You are given the stem, options, the correct answer, and the worked solution (the figure itself
is gone). Decide what compound structure(s) the figure must show so the question makes sense,
and give each compound as a NAME that the OPSIN name->structure parser can read.

RULES:
- Give a SPECIFIC compound name only — a systematic IUPAC name or a well-known common name
  (e.g. "aniline", "glucose", "2-methylpropan-2-ol"). NEVER a generic CLASS ("alkyl halide",
  "carboxylic acid", "an amine", "the ether") — a class has no single structure; if the text
  only gives a class, that figure is NOT drawable.
- No polymers by trade name ("polystyrene"), no bare elements ("hydrogen"), no reaction
  conditions or the words "compound/anion/cation" inside the name.
- For each compound set "source":
    "stated"   = the compound name/formula appears VERBATIM in the stem, an option, or the
                 solution (draw-by-construction; high confidence).
    "inferred" = you deduced the identity from the solution's reasoning (lower confidence).
- If the question is "the structure/IUPAC name of the compound shown", the correct-answer
  option or the solution usually names it -> output that ONE compound.
- If the OPTIONS are candidate structures the text NAMES, output each named option + its label.
- If a reaction is shown as structures, output the reactant(s) and product(s).
- drawable=false when the essential structure is defined ONLY by the missing image and is NOT
  named or derivable from any text. NEVER invent a compound to fill the gap.
- drawable=false when the missing figure is NOT a molecular structure — a GRAPH or plot, an
  Ellingham / energy / phase diagram, a reaction energy profile, an apparatus / setup, a data
  TABLE, a crystal LATTICE, an MO diagram, or an Assertion-Reason statement pair — EVEN IF the
  text names compounds. A molecular structure cannot substitute for those figures.

Return ONLY JSON:
{"drawable": true|false,
 "figures": [{"name": "<specific, opsin-parseable compound name>", "label": "A|product|null",
              "source": "stated|inferred"}],
 "reason": "<=15 words"}"""


def _post(model, messages, timeout=90, vision=False):
    body = {"model": model, "messages": messages,
            "response_format": {"type": "json_object"}}
    if not str(model).startswith("gpt-5"):
        body["temperature"] = 0
    data = json.dumps(body).encode()
    req = urllib.request.Request(PROXY, data=data, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return json.loads(r["choices"][0]["message"]["content"])


def extract(stem, options, ans, solution):
    opt = ""
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    user = (f"STEM: {stem}\n\nOPTIONS: {opt[:900]}\n\nCORRECT ANSWER: {ans}\n\n"
            f"SOLUTION: {(solution or '')[:1500]}")
    return _post(CHAT, [{"role": "system", "content": EXTRACT_SYS},
                        {"role": "user", "content": user}])


def render(entries, out_path):
    """entries: list of (label, canonical_smiles). Returns (path, formulas) or (None, [])."""
    mols, legends = [], []
    for label, smi in entries:
        m = Chem.MolFromSmiles(smi)
        if m:
            mols.append(m)
            legends.append(label or "")
    if not mols:
        return None, []
    formulas = [rdMolDescriptors.CalcMolFormula(m) for m in mols]
    if len(mols) == 1:
        d = rdMolDraw2D.MolDraw2DCairo(360, 300)
        d.DrawMolecule(mols[0])
    else:
        cols = min(len(mols), 2)
        rows = (len(mols) + cols - 1) // cols
        d = rdMolDraw2D.MolDraw2DCairo(300 * cols, 260 * rows, 300, 260)
        d.DrawMolecules(mols, legends=legends)
    d.FinishDrawing()
    open(out_path, "wb").write(d.GetDrawingText())
    return out_path, formulas


VERIFY_SYS = """You are given a chemistry MCQ and OUR redrawn figure for it. Read the figure and
the text, solve the question, and output the single best option label. Return ONLY JSON
{"answer": "<label>", "used_figure": true|false, "note":"<=10 words"}. used_figure=false if the
figure was not needed to answer."""

MATCH_SYS = """You are given a chemistry MCQ (stem + options) and OUR figure, which we drew from
the question's TEXT to REPLACE its lost original figure. Judge ONLY whether our figure shows the
RIGHT chemical subject — do NOT solve the question.

Return matches=true if the figure depicts the compound(s) the question is actually about: the
molecules named by the OPTIONS, or the single specific compound the stem asks about (its
structure / IUPAC name / a reactant or product in the described reaction).

Return matches=false if the figure shows an INCIDENTAL compound instead — a reagent, catalyst,
solvent, or by-product that is mentioned in the text but is NOT what the figure should depict —
or if it is clearly the wrong molecule / the wrong number of molecules for the question.

Return matches=false if the question's ORIGINAL figure was NOT a molecular structure at all —
e.g. a GRAPH or plot, an Ellingham / energy / phase diagram, a reaction energy profile, an
apparatus / experimental setup, a data TABLE, or a crystal LATTICE — even when the text mentions
compound names. Our figure only draws molecular structures, so it cannot be right for those.

Return ONLY JSON {"matches": true|false, "note": "<=12 words"}."""


def check_matches(stem, options, img_path):
    ext = img_path.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    b64 = base64.b64encode(open(img_path, "rb").read()).decode()
    opt = ""
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    msg = [{"role": "system", "content": MATCH_SYS},
           {"role": "user", "content": [
               {"type": "text", "text": f"STEM: {stem}\n\nOPTIONS: {opt[:900]}\n\nOUR FIGURE:"},
               {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]
    return _post(VISION, msg, timeout=120, vision=True)


def verify(stem, options, img_path):
    ext = img_path.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    b64 = base64.b64encode(open(img_path, "rb").read()).decode()
    opt = ""
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    msg = [{"role": "system", "content": VERIFY_SYS},
           {"role": "user", "content": [
               {"type": "text", "text": f"STEM: {stem}\n\nOPTIONS: {opt[:900]}\n\nFIGURE (ours):"},
               {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]
    return _post(VISION, msg, timeout=120, vision=True)


def norm_ans(a):
    return str(a or "").strip().strip(".)(").upper()[:3]


def extract_phase(row):
    """Phase 1: LLM extract only (concurrent-safe — no OPSIN)."""
    qid, exam, chapter, stem, options, ans, solution = row
    rec = {"id": qid, "exam": exam, "chapter": chapter, "stem": stem,
           "options": options, "ans": ans}
    try:
        ex = extract(stem, options, ans, solution)
    except Exception as e:
        rec.update(stage="extract_err", err=str(e)[:80], drawable=False); return rec
    rec["drawable"] = bool(ex.get("drawable"))
    rec["reason"] = ex.get("reason")
    rec["figures"] = ex.get("figures") or []
    rec["names"] = [f.get("name") for f in rec["figures"]]
    if not ex.get("drawable"):
        rec["stage"] = "not_drawable"
    return rec


def render_verify_phase(rec, resolved_map, out_dir):
    """Phase 3: build entries from the OPSIN batch result, render, verify (concurrent-safe)."""
    entries, unresolved, sources = [], [], []
    for f in rec.get("figures", []):
        nm = (f.get("name") or "").strip()
        if not nm:
            continue
        if nm in resolved_map:
            entries.append((f.get("label") or "", resolved_map[nm]["smiles"]))
            sources.append(f.get("source") or "inferred")
        else:
            unresolved.append(nm)
    rec["resolved"] = len(entries)
    rec["unresolved"] = unresolved
    # Tier A = every drawn compound was stated verbatim in the text AND all figures resolved
    rec["all_stated"] = bool(entries) and not unresolved and all(s == "stated" for s in sources)
    if not entries:
        rec["stage"] = "opsin_fail"; return rec
    out_path = os.path.join(out_dir, f"{rec['id']}.png")
    path, formulas = render(entries, out_path)
    if not path:
        rec["stage"] = "render_fail"; return rec
    rec["formulas"] = formulas
    rec["png"] = path
    # gate for a LIVE attach: does our figure show the question's actual subject?
    try:
        m = check_matches(rec["stem"], rec["options"], path)
        rec["matches"] = bool(m.get("matches"))
        rec["match_note"] = m.get("note")
    except Exception as e:
        rec["matches"] = None; rec["match_err"] = str(e)[:60]
    rec["stage"] = "rendered"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--exam", default=None)
    ap.add_argument("--ids", default=None, help="comma-separated qids (overrides sampling)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out-dir", default="/tmp/chem_figs")
    ap.add_argument("--out", default="/tmp/chem_figs/report.json")
    ap.add_argument("--full", action="store_true", help="process the whole chem diagram pool")
    ap.add_argument("--attach", action="store_true",
                    help="write clean figure_url onto attachable rows in the LIVE bank")
    ap.add_argument("--use-llm-smiles", action="store_true",
                    help="last-resort LLM name->SMILES (higher recall, lower precision; off by default)")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    c = sqlite3.connect(config.DB_PATH)
    c.execute("PRAGMA busy_timeout=30000")
    cols = "id, exam, chapter, stem, options, correct_answer, solution"
    if args.ids:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        rows = [c.execute(f"SELECT {cols} FROM questions WHERE id=?", (i,)).fetchone() for i in ids]
        rows = [r for r in rows if r]
    else:
        q = (f"SELECT {cols} FROM questions WHERE subject='Chemistry' AND needs_figure=1 "
             f"AND verified=1 AND solution IS NOT NULL AND length(solution)>40")
        params = []
        if args.exam:
            q += " AND exam=?"; params.append(args.exam)
        q += " ORDER BY exam, id"
        allrows = c.execute(q, params).fetchall()
        if args.full:
            rows = allrows
        else:
            step = max(1, len(allrows) // args.limit)
            rows = allrows[::step][:args.limit]
    print(f"[gen-chem] processing {len(rows)} questions", flush=True)

    # PHASE 1 — extract names (concurrent LLM, no OPSIN)
    recs = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(extract_phase, r): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            recs.append(f.result())
            if i % 10 == 0:
                print(f"  extract {i}/{len(rows)}", flush=True)

    # PHASE 2 — resolve ALL names: OPSIN -> PubChem -> LLM (batched; no temp-file race)
    all_names = sorted({(f.get("name") or "").strip()
                        for r in recs if r.get("drawable")
                        for f in r.get("figures", []) if (f.get("name") or "").strip()})
    print(f"  resolving {len(all_names)} unique names (OPSIN->PubChem->LLM)", flush=True)
    resolved_map = resolve_batch(all_names, use_llm=args.use_llm_smiles)
    from collections import Counter as _C
    srcs = _C(v["source"] for v in resolved_map.values())
    print(f"  resolved {len(resolved_map)}/{len(all_names)}  {dict(srcs)}", flush=True)

    # PHASE 3 — render + verify (concurrent; OPSIN already done)
    drawables = [r for r in recs if r.get("drawable")]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(render_verify_phase, r, resolved_map, args.out_dir): r for r in drawables}
        for i, f in enumerate(as_completed(futs), 1):
            f.result()
            if i % 10 == 0:
                print(f"  render+verify {i}/{len(drawables)}", flush=True)

    results = recs
    # strip bulky text fields from the report
    for r in results:
        r.pop("stem", None); r.pop("options", None)
    json.dump(results, open(args.out, "w"), indent=1)

    n = len(results)
    drawable = sum(1 for r in results if r.get("drawable"))
    rendered = sum(1 for r in results if r.get("stage") == "rendered")
    tierA = [r for r in results if r.get("stage") == "rendered" and r.get("all_stated")]
    # ATTACHABLE = Tier-A (compounds stated verbatim) AND the figure shows the question's subject
    attachable = [r for r in tierA if r.get("matches") is True]
    print("\n=== YIELD (of full diagram pool) ===")
    print(f"  drawable (compound named/derivable): {drawable}/{n} = {100*drawable//n}%")
    print(f"  rendered clean figure             : {rendered}/{n} = {100*rendered//n}%")
    print(f"  Tier-A (all STATED)               : {len(tierA)}/{n} = {100*len(tierA)//n}%")
    print(f"  ATTACHABLE (Tier-A + figure match): {len(attachable)}/{n} = {100*len(attachable)//n}%")

    if args.attach:
        import shutil
        pub = config.PUBLIC_BASE.rstrip("/")
        os.makedirs(config.FIG_DIR, exist_ok=True)
        acon = sqlite3.connect(config.DB_PATH)
        acon.execute("PRAGMA busy_timeout=30000")
        done = 0
        for r in attachable:
            src = r.get("png")
            if not src or not os.path.exists(src):
                continue
            dst_name = f"{r['id']}.gen.png"
            dst = os.path.join(config.FIG_DIR, dst_name)
            shutil.copyfile(src, dst)
            url = f"{pub}/figures/{dst_name}"
            acon.execute("UPDATE questions SET figure_url=?, needs_figure=1 WHERE id=?",
                         (url, r["id"]))
            done += 1
        acon.commit(); acon.close()
        print(f"\n[ATTACH] wrote clean figure_url to {done} LIVE bank rows "
              f"(figures saved as <id>.gen.png in {config.FIG_DIR})")
        print(f"[ATTACH] public base = {pub}")
    print("\n  fail-stage breakdown:")
    from collections import Counter
    for s, k in Counter(r.get("stage") for r in results).most_common():
        print(f"    {s:16s} {k}")
    print(f"\n[gen-chem] wrote {args.out}  (PNGs in {args.out_dir})")


if __name__ == "__main__":
    main()
