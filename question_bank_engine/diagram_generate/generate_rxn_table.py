#!/usr/bin/env python3
"""Clean figures for REACTION-scheme and TABLE (Column I/II) chemistry diagram questions.

Companion to generate_chem_figures.py (which handles single/panel molecules). Same idea —
rebuild the figure from TEXT, never touch the watermarked original — but two more figure kinds:

  REACTION : reactant(s) -> product(s), all NAMED in text. Resolve each name (OPSIN->PubChem),
             build a reaction SMILES, render with RDKit Draw.ReactionToImage. A VLM match-gate
             confirms the drawn reaction matches what the question describes.
  TABLE    : a Column-I / Column-II match table whose rows are spelled out in the text. Re-render
             as a clean matplotlib table (deterministic — faithful to the extracted text).

Attaches with the same `<id>.gen.png` + figure_url convention (revertible, provenance-queryable).

    python3 generate_rxn_table.py [--limit 60] [--exam NEET] [--attach] [--use-llm-smiles]
"""
import argparse, base64, json, os, sqlite3, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank import config
from resolve import resolve_batch

from rdkit.Chem import AllChem, Draw
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
CHAT = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o")
VISION = os.environ.get("QBANK_VISION_MODEL", "gpt-4o")


def _post(model, messages, timeout=120):
    body = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}
    if not str(model).startswith("gpt-5"):
        body["temperature"] = 0
    data = json.dumps(body).encode()
    req = urllib.request.Request(PROXY, data=data, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return json.loads(r["choices"][0]["message"]["content"])


EXTRACT_SYS = r"""You rebuild the MISSING FIGURE of a chemistry MCQ from its TEXT. Decide which of two
figure kinds it was, and extract what's needed to redraw it. You get stem, options, answer, solution.

kind = "reaction" : the figure showed a chemical reaction as structures (reactant(s) -> product(s)).
  Extract "reactants" and "products" as lists of SPECIFIC compound NAMES (systematic IUPAC or
  well-known common names OPSIN/PubChem can parse). ONLY if every reactant AND product is named or
  clearly derivable from the text. Optional "reagent" = short over-arrow text (e.g. "conc. H2SO4").

kind = "table" : the figure was a Column-I / Column-II MATCH table (or a small data table) whose
  entries are ALL spelled out in the text. Extract "col1_title", "col2_title", and "rows" =
  list of [left, right] pairs. Keep entries short (a formula, a name, a phrase).

kind = "skip" : anything else — a single/panel of molecules (handled elsewhere), a graph, an
  apparatus, structures referenced only by labels (i, ii, X) with no names, or a reaction/table
  whose content is NOT fully in the text. When unsure, skip. NEVER invent compounds or rows.

Return ONLY JSON:
{"kind":"reaction|table|skip",
 "reactants":["..."], "products":["..."], "reagent":"...|null",
 "col1_title":"...", "col2_title":"...", "rows":[["left","right"], ...],
 "reason":"<=15 words"}"""


def extract(stem, options, ans, solution):
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    user = (f"STEM: {stem}\n\nOPTIONS: {opt[:900]}\n\nCORRECT ANSWER: {ans}\n\n"
            f"SOLUTION: {(solution or '')[:1500]}")
    return _post(CHAT, [{"role": "system", "content": EXTRACT_SYS},
                        {"role": "user", "content": user}])


def render_reaction(reactant_smiles, product_smiles, out_path):
    if not reactant_smiles or not product_smiles:
        return None
    smarts = ".".join(reactant_smiles) + ">>" + ".".join(product_smiles)
    try:
        rxn = AllChem.ReactionFromSmarts(smarts, useSmiles=True)
        img = Draw.ReactionToImage(rxn, subImgSize=(260, 220))
        img.save(out_path)
        return out_path
    except Exception:
        return None


def render_table(col1, col2, rows, out_path):
    rows = [r for r in rows if isinstance(r, (list, tuple)) and len(r) >= 2]
    if len(rows) < 2:
        return None
    cell = [[str(r[0])[:60], str(r[1])[:60]] for r in rows]
    h = 0.5 + 0.5 * len(cell)
    fig, ax = plt.subplots(figsize=(6.4, h))
    ax.axis("off")
    t = ax.table(cellText=cell, colLabels=[col1 or "Column I", col2 or "Column II"],
                 loc="center", cellLoc="left", colLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(11); t.scale(1, 1.5)
    for (r, c), cellobj in t.get_celld().items():
        cellobj.set_edgecolor("#888")
        if r == 0:
            cellobj.set_facecolor("#f0f0f0"); cellobj.set_text_props(weight="bold")
    fig.savefig(out_path, dpi=150, bbox_inches="tight"); plt.close(fig)
    return out_path


MATCH_SYS = """You are given a chemistry MCQ (stem + options) and OUR figure, rebuilt from the text to
replace the lost original. Judge ONLY whether our figure is a FAITHFUL representation of what the
question's figure should show — the described reaction (correct reactants -> products) OR the
Column-I/Column-II data the question matches. Do NOT solve the question. Ignore layout/style.
Return matches=false if compounds/entries are wrong, missing, or it is the wrong kind of figure.
Return ONLY JSON {"matches": true|false, "note": "<=12 words"}."""


def check_matches(stem, options, img_path):
    b64 = base64.b64encode(open(img_path, "rb").read()).decode()
    try:
        opt = "; ".join(f"{o.get('label')}) {o.get('text')}" for o in json.loads(options or "[]"))
    except Exception:
        opt = str(options or "")
    msg = [{"role": "system", "content": MATCH_SYS},
           {"role": "user", "content": [
               {"type": "text", "text": f"STEM: {stem}\n\nOPTIONS: {opt[:900]}\n\nOUR FIGURE:"},
               {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}]
    return _post(VISION, msg, timeout=120)


def process(row, out_dir, resolver_cache):
    qid, exam, chapter, stem, options, ans, solution = row
    rec = {"id": qid, "exam": exam, "chapter": chapter, "stem": stem, "options": options}
    try:
        ex = extract(stem, options, ans, solution)
    except Exception as e:
        rec.update(kind="error", err=str(e)[:80]); return rec
    kind = ex.get("kind")
    rec["kind"] = kind
    rec["reason"] = ex.get("reason")
    out_path = os.path.join(out_dir, f"{qid}.png")

    if kind == "reaction":
        names = [n for n in (ex.get("reactants") or []) + (ex.get("products") or []) if n]
        rec["names"] = names
        resolved = resolve_batch(names, use_llm=resolver_cache["use_llm"])
        rsmi = [resolved[n]["smiles"] for n in (ex.get("reactants") or []) if n in resolved]
        psmi = [resolved[n]["smiles"] for n in (ex.get("products") or []) if n in resolved]
        rec["resolved"] = len(rsmi) + len(psmi)
        rec["needed"] = len(names)
        if len(rsmi) + len(psmi) < len(names) or not rsmi or not psmi:
            rec["stage"] = "resolve_fail"; return rec
        if not render_reaction(rsmi, psmi, out_path):
            rec["stage"] = "render_fail"; return rec
    elif kind == "table":
        rows = ex.get("rows") or []
        rec["nrows"] = len(rows)
        if not render_table(ex.get("col1_title"), ex.get("col2_title"), rows, out_path):
            rec["stage"] = "render_fail"; return rec
    else:
        rec["stage"] = "skip"; return rec

    rec["png"] = out_path
    try:
        m = check_matches(stem, options, out_path)
        rec["matches"] = bool(m.get("matches")); rec["match_note"] = m.get("note")
    except Exception as e:
        rec["matches"] = None; rec["match_err"] = str(e)[:60]
    rec["stage"] = "rendered"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--exam", default=None)
    ap.add_argument("--ids", default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out-dir", default="/tmp/rxn_table")
    ap.add_argument("--out", default="/tmp/rxn_table/report.json")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--attach", action="store_true")
    ap.add_argument("--use-llm-smiles", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    c = sqlite3.connect(config.DB_PATH); c.execute("PRAGMA busy_timeout=30000")
    cols = "id, exam, chapter, stem, options, correct_answer, solution"
    if args.ids:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        rows = [c.execute(f"SELECT {cols} FROM questions WHERE id=?", (i,)).fetchone() for i in ids]
        rows = [r for r in rows if r]
    else:
        q = (f"SELECT {cols} FROM questions WHERE subject='Chemistry' AND needs_figure=1 AND verified=1 "
             f"AND solution IS NOT NULL AND length(solution)>40 "
             f"AND (figure_url IS NULL OR figure_url NOT LIKE '%.gen.png')")
        params = []
        if args.exam:
            q += " AND exam=?"; params.append(args.exam)
        q += " ORDER BY exam, id"
        allrows = c.execute(q, params).fetchall()
        rows = allrows if args.full else allrows[::max(1, len(allrows) // args.limit)][:args.limit]
    print(f"[rxn-table] processing {len(rows)} questions", flush=True)

    cache = {"use_llm": args.use_llm_smiles}
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, r, args.out_dir, cache): r for r in rows}
        for i, f in enumerate(as_completed(futs), 1):
            results.append(f.result())
            if i % 10 == 0:
                print(f"  {i}/{len(rows)}", flush=True)

    for r in results:
        r.pop("stem", None); r.pop("options", None)
    json.dump(results, open(args.out, "w"), indent=1)

    from collections import Counter
    n = len(results)
    kinds = Counter(r.get("kind") for r in results)
    rendered = [r for r in results if r.get("stage") == "rendered"]
    rxn_ok = [r for r in rendered if r.get("kind") == "reaction" and r.get("matches")]
    tbl_ok = [r for r in rendered if r.get("kind") == "table" and r.get("matches")]
    attachable = rxn_ok + tbl_ok
    print(f"\n=== kinds: {dict(kinds)} ===")
    print(f"  rendered: {len(rendered)}/{n}")
    print(f"  reaction attachable (rendered+match): {len(rxn_ok)}")
    print(f"  table    attachable (rendered+match): {len(tbl_ok)}")

    if args.attach:
        import shutil
        pub = config.PUBLIC_BASE.rstrip("/")
        os.makedirs(config.FIG_DIR, exist_ok=True)
        acon = sqlite3.connect(config.DB_PATH); acon.execute("PRAGMA busy_timeout=30000")
        done = 0
        for r in attachable:
            src = r.get("png")
            if not src or not os.path.exists(src):
                continue
            dst_name = f"{r['id']}.gen.png"
            shutil.copyfile(src, os.path.join(config.FIG_DIR, dst_name))
            acon.execute("UPDATE questions SET figure_url=?, needs_figure=1 WHERE id=?",
                         (f"{pub}/figures/{dst_name}", r["id"]))
            done += 1
        acon.commit(); acon.close()
        print(f"\n[ATTACH] wrote clean figure_url to {done} LIVE rows (base {pub})")


if __name__ == "__main__":
    main()
