import os, json, glob
from DECIMER import predict_SMILES
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

FIGS = os.path.expanduser("~/molscribe_pilot/figs")
OUT = os.path.expanduser("~/molscribe_pilot/out")
os.makedirs(OUT, exist_ok=True)

rows = []
for fp in sorted(glob.glob(FIGS + "/*")):
    qid = os.path.splitext(os.path.basename(fp))[0]
    try:
        smiles = predict_SMILES(fp)
    except Exception as e:
        rows.append({"id": qid, "smiles": None, "err": str(e)[:80]}); continue
    m = Chem.MolFromSmiles(smiles) if smiles else None
    formula = rdMolDescriptors.CalcMolFormula(m) if m else None
    canon = Chem.MolToSmiles(m) if m else None
    if m:
        d = rdMolDraw2D.MolDraw2DCairo(360, 300); d.DrawMolecule(m); d.FinishDrawing()
        open(os.path.join(OUT, qid + ".png"), "wb").write(d.GetDrawingText())
    rows.append({"id": qid, "smiles": smiles, "canonical": canon,
                 "valid": bool(m), "formula": formula})
    print(f"  {qid}: valid={bool(m)} {formula or ''}  {(smiles or '')[:60]}")

json.dump(rows, open(os.path.join(OUT, "decimer_report.json"), "w"), indent=1)
ok = sum(1 for r in rows if r.get("valid"))
print(f"\n[DECIMER] {ok}/{len(rows)} produced a valid parseable structure")
