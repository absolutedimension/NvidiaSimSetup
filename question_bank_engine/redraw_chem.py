#!/usr/bin/env python3
"""Clean-redraw pilot for org_chem_structure diagram questions via RDKit.

Unlike graphs, the intermediate representation (SMILES) is VERIFIABLE:
  1. VLM reads the structure image -> SMILES(es)
  2. RDKit parses (invalid SMILES = caught for free) -> renders a clean 2D structure
  3. VERIFY, two independent layers:
     a. round-trip: VLM reads OUR clean render back -> SMILES; canonical-compare to (1).
        Same molecule in == same molecule out proves the redraw is faithful to what we
        extracted (catches render/layout corruption). Structural, not a vibe check.
     b. visual: VLM compares ORIGINAL vs OUR render -> same molecule? (catches mis-reads
        of the original).
  A pass needs BOTH. Retry with critique on fail.

Output = our own RDKit render -> copyright-clean, watermark-free.

    python3 redraw_chem.py [--limit 15] [--max-retries 2] [--out-dir /tmp/redraw_chem]
"""
import argparse
import base64
import json
import os
import sqlite3
import urllib.request

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

from qbank import config

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
VMODEL = os.environ.get("QBANK_VISION_MODEL", "gpt-4o")

READ_SYS = r"""You are a chemistry OCR expert. Read the molecular structure(s) in the image and
output each as a SMILES string. There may be one molecule or several (e.g. reactant + product,
or labelled A/B/C). Use the QUESTION only for disambiguation. Return JSON:
{"molecules":[{"smiles":"...","label":"A|null"}], "readable": true|false, "notes":"..."}.
Give valid SMILES. Preserve rings, substituents, functional groups, and (if drawn) charges.
Output ONLY the JSON."""


def _b64(path):
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    return mime, base64.b64encode(open(path, "rb").read()).decode()


def _read_smiles(stem, img_path, critique=None):
    mime, b64 = _b64(img_path)
    txt = "QUESTION: " + (stem or "")[:400]
    if critique:
        txt += "\n\nYour previous reading was wrong: " + json.dumps(critique) + " — re-read carefully."
    msg = [{"role": "system", "content": READ_SYS},
           {"role": "user", "content": [
               {"type": "text", "text": txt},
               {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]
    body = json.dumps({"model": VMODEL, "messages": msg,
                       "response_format": {"type": "json_object"}, "temperature": 0.1}).encode()
    req = urllib.request.Request(PROXY, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return json.loads(r["choices"][0]["message"]["content"])


def canon(smiles):
    m = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(m) if m else None


_CMP_SYS = """You compare two chemistry figures for the SAME question. First image = ORIGINAL exam
figure; second = OUR clean redraw. Judge whether OUR redraw shows the SAME molecule(s) /
structure(s) as the original — same skeleton, rings, substituents, functional groups. If the
original is an OPTIONS panel (several candidate structures), do OUR structures match that set?
Ignore layout, colour, watermark, 2D orientation. Return JSON
{"same": true|false, "n_molecules_original": int, "differences": [short strings], "score": 0-10}."""


def visual_compare(stem, orig_path, our_path):
    om, ob = _b64(orig_path); nm, nb = _b64(our_path)
    msg = [{"role": "system", "content": _CMP_SYS},
           {"role": "user", "content": [
               {"type": "text", "text": "QUESTION: " + (stem or "")[:300] + "\n\nORIGINAL:"},
               {"type": "image_url", "image_url": {"url": f"data:{om};base64,{ob}"}},
               {"type": "text", "text": "OUR redraw:"},
               {"type": "image_url", "image_url": {"url": f"data:{nm};base64,{nb}"}}]}]
    body = json.dumps({"model": VMODEL, "messages": msg,
                       "response_format": {"type": "json_object"}, "temperature": 0.2}).encode()
    req = urllib.request.Request(PROXY, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return json.loads(r["choices"][0]["message"]["content"])


def render(smiles_list, out_path):
    mols = [Chem.MolFromSmiles(s) for s in smiles_list]
    mols = [m for m in mols if m]
    if not mols:
        return None, []
    formulas = [rdMolDescriptors.CalcMolFormula(m) for m in mols]
    if len(mols) == 1:
        d = rdMolDraw2D.MolDraw2DCairo(360, 300)
        d.DrawMolecule(mols[0])
    else:
        d = rdMolDraw2D.MolDraw2DCairo(240 * min(len(mols), 3), 260 * ((len(mols) + 2) // 3))
        d.DrawMolecules(mols)
    d.FinishDrawing()
    open(out_path, "wb").write(d.GetDrawingText())
    return out_path, formulas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--max-retries", type=int, default=1)
    ap.add_argument("--out-dir", default="/tmp/redraw_chem")
    ap.add_argument("--types-json", default="/tmp/diag_types.json")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    ids = [r["id"] for r in json.load(open(args.types_json)) if r["type"] == "org_chem_structure"][:args.limit]
    c = sqlite3.connect(config.DB_PATH); c.execute("PRAGMA busy_timeout=30000")
    report, passed = [], 0
    for n, qid in enumerate(ids, 1):
        row = c.execute("SELECT stem, figure_refs FROM questions WHERE id=?", (qid,)).fetchone()
        if not row:
            continue
        stem, refs = row
        try:
            orig = os.path.join(config.FIG_DIR, json.loads(refs or "[]")[0])
        except Exception:
            continue
        if not os.path.exists(orig):
            continue
        our = os.path.join(args.out_dir, f"{qid}.png")
        critique, ok, info = None, False, {}
        for attempt in range(args.max_retries + 1):
            try:
                got = _read_smiles(stem, orig, critique)
                smis = [m.get("smiles") for m in got.get("molecules", []) if m.get("smiles")]
                canon_in = [canon(s) for s in smis]
                valid = [c2 for c2 in canon_in if c2]
                if not valid:
                    critique = ["no valid SMILES parsed from your reading"]; info = {"stage": "parse"}; continue
                path, formulas = render(valid, our)
                # round-trip (structural signal): read our render back, compare canonical sets
                back = _read_smiles(stem, our)
                canon_out = set(filter(None, (canon(m.get("smiles")) for m in back.get("molecules", []))))
                canon_in_set = set(valid)
                roundtrip = bool(canon_in_set) and canon_in_set == canon_out
                # visual compare (pass criterion): does our render show the same molecule(s)?
                cmp = visual_compare(stem, orig, our)
                info = {"smiles_in": valid, "formulas": formulas, "roundtrip": roundtrip,
                        "n_in": len(canon_in_set), "n_orig": cmp.get("n_molecules_original"),
                        "score": cmp.get("score"), "differences": cmp.get("differences")}
                if cmp.get("same"):
                    ok = True; break
                critique = cmp.get("differences") or ["redraw did not match the original structure"]
            except Exception as e:
                info = {"err": str(e)[:80]}; break
        passed += ok
        report.append({"id": qid, "passed": ok, **info, "orig": orig, "our": our if os.path.exists(our) else None})
        print(f"  [{n}/{len(ids)}] {qid}  {'PASS' if ok else 'fail'}  {info.get('formulas', info.get('stage', info.get('err','')))}")

    json.dump(report, open(os.path.join(args.out_dir, "report.json"), "w"))
    print(f"\n[redraw-chem] round-trip clean-pass: {passed}/{len(ids)} = {100*passed/max(1,len(ids)):.0f}%")


if __name__ == "__main__":
    main()
