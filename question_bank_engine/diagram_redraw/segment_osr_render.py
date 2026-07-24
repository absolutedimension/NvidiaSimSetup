"""Segment an MCQ option-panel into individual molecule crops, then OSR each.

Tailored to exam option panels (not scientific pages): binarize -> dilate so each
molecule's parts merge into one blob while separate options stay apart -> connected
components -> size/shape filter -> order by position -> DECIMER per crop -> RDKit.
Dependency-light (scikit-image + numpy + PIL + DECIMER + rdkit)."""
import os, json, glob, sys
import numpy as np
from PIL import Image
from skimage.filters import threshold_otsu
from skimage.morphology import binary_dilation, footprint_rectangle
from skimage.measure import label, regionprops
from DECIMER import predict_SMILES
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

FIGS = os.path.expanduser("~/molscribe_pilot/figs")
OUT = os.path.expanduser("~/molscribe_pilot/seg_out")
os.makedirs(OUT, exist_ok=True)


def segment(path):
    img = Image.open(path).convert("L")
    arr = np.asarray(img)
    H, W = arr.shape
    ink = arr < threshold_otsu(arr)                      # True = dark (ink)
    # merge parts of one molecule: dilate horizontally + vertically
    d = binary_dilation(ink, footprint_rectangle((max(3, H // 40), max(3, W // 25))))
    lab = label(d)
    boxes = []
    for r in regionprops(lab):
        minr, minc, maxr, maxc = r.bbox
        h, w = maxr - minr, maxc - minc
        area = h * w
        # drop tiny (labels/noise) and full-width text lines (very wide + short)
        if area < 0.01 * H * W:
            continue
        if w > 0.9 * W and h < 0.09 * H:
            continue
        boxes.append((minr, minc, maxr, maxc, area))
    # order row-major (top->bottom, then left->right within a band)
    boxes.sort(key=lambda b: (round(b[0] / (0.12 * H)), b[1]))
    crops = []
    pad = 6
    for (minr, minc, maxr, maxc, _) in boxes:
        c = arr[max(0, minr - pad):min(H, maxr + pad), max(0, minc - pad):min(W, maxc + pad)]
        crops.append(c)
    return crops


def read_and_render(crop, out_png):
    tmp = out_png.replace(".png", "_crop.png")
    Image.fromarray(crop).save(tmp)
    try:
        smi = predict_SMILES(tmp)
    except Exception:
        return None
    m = Chem.MolFromSmiles(smi) if smi else None
    if not m:
        return {"smiles": smi, "valid": False}
    heavy = m.GetNumHeavyAtoms()
    formula = rdMolDescriptors.CalcMolFormula(m)
    # sanity gate: reject the C300-ish garbage a bad crop produces
    reasonable = heavy <= 40 and "." not in Chem.MolToSmiles(m)[:0] or heavy <= 40
    d = rdMolDraw2D.MolDraw2DCairo(300, 260); d.DrawMolecule(m); d.FinishDrawing()
    open(out_png, "wb").write(d.GetDrawingText())
    return {"smiles": Chem.MolToSmiles(m), "valid": True, "formula": formula,
            "heavy_atoms": heavy, "reasonable": heavy <= 40}


def main():
    ids = sys.argv[1:] or [os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(FIGS + "/*"))]
    report = []
    for qid in ids:
        matches = glob.glob(f"{FIGS}/{qid}.*")
        if not matches:
            continue
        crops = segment(matches[0])
        opts = []
        for i, crop in enumerate(crops):
            res = read_and_render(crop, os.path.join(OUT, f"{qid}_opt{i}.png"))
            if res and res.get("valid"):
                opts.append({"idx": i, **res})
        good = [o for o in opts if o.get("reasonable")]
        report.append({"id": qid, "segments": len(crops), "valid_mols": len(opts), "reasonable_mols": len(good),
                       "formulas": [o["formula"] for o in good]})
        print(f"  {qid}: segments={len(crops)} valid={len(opts)} reasonable={len(good)}  {[o['formula'] for o in good]}")
    json.dump(report, open(os.path.join(OUT, "seg_report.json"), "w"), indent=1)
    print(f"\n[seg] panels where >=3 clean option-molecules recovered: "
          f"{sum(1 for r in report if r['reasonable_mols']>=3)}/{len(report)}")


if __name__ == "__main__":
    main()
