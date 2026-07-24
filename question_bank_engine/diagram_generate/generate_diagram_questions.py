#!/usr/bin/env python3
"""FIGURE-FIRST diagram-question generation — correct by construction, copyright-clean.

The most reliable way to have diagram questions: don't reproduce anyone's figure. Instead
  1. draw a CORRECT structure ourselves (name -> OPSIN/PubChem -> RDKit),
  2. let RDKit COMPUTE a property as GROUND TRUTH (formula, stereocenters, DoU, groups...),
  3. phrase an MCQ around that property with deterministic distractors.
The figure is right because we drew it; the answer is right because RDKit calculated it.
No perception, no hallucination, no copyright. Unlimited supply.

    python3 generate_diagram_questions.py [--out-dir /tmp/genq] [--per-compound 1]
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resolve import resolve_batch

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

# exam-relevant seed compounds spanning topics (all OPSIN/PubChem-resolvable)
SEEDS = [
    "aspirin", "ibuprofen", "paracetamol", "glucose", "lactic acid", "citric acid",
    "aniline", "2,3-dibromobutane", "limonene", "alanine", "salicylic acid",
    "benzaldehyde", "tert-butanol", "phenol", "acetic acid", "caffeine",
]


def render(mol, out_path, legend=""):
    d = rdMolDraw2D.MolDraw2DCairo(380, 320)
    d.DrawMolecule(mol, legend=legend)
    d.FinishDrawing()
    open(out_path, "wb").write(d.GetDrawingText())


def dou(mol):  # degree of unsaturation from atom counts
    from collections import Counter
    cnt = Counter(a.GetSymbol() for a in Chem.AddHs(mol).GetAtoms())
    C, H, N = cnt.get("C", 0), cnt.get("H", 0), cnt.get("N", 0)
    X = sum(cnt.get(x, 0) for x in ("F", "Cl", "Br", "I"))
    return (2 * C + 2 + N - H - X) // 2


def count_smarts(mol, smarts):
    p = Chem.MolFromSmarts(smarts)
    return len(mol.GetSubstructMatches(p)) if p else 0


def distractors_num(correct, k=3):
    cands = [correct + 1, correct - 1, correct + 2, max(0, correct - 2), correct + 3]
    out = []
    for c in cands:
        if c != correct and c >= 0 and c not in out:
            out.append(c)
        if len(out) == k:
            break
    return out


def distractors_formula(mol):
    """Perturb the real formula into 3 plausible-but-wrong ones."""
    from collections import Counter
    mh = Chem.AddHs(mol)
    cnt = Counter(a.GetSymbol() for a in mh.GetAtoms())
    def fmt(c):
        order = ["C", "H", "N", "O", "F", "Cl", "Br", "I", "S", "P"]
        s = ""
        for el in order:
            if c.get(el):
                s += el + (str(c[el]) if c[el] > 1 else "")
        for el in sorted(c):
            if el not in order and c.get(el):
                s += el + (str(c[el]) if c[el] > 1 else "")
        return s
    outs = []
    for dC, dH in [(0, 2), (0, -2), (1, 0)]:
        c = dict(cnt); c["H"] = c.get("H", 0) + dH; c["C"] = c.get("C", 0) + dC
        if c["H"] > 0 and c["C"] > 0:
            outs.append(fmt(Counter(c)))
    return outs


def make_questions(name, mol):
    """Return list of MCQ dicts, each with a RDKit-GROUND-TRUTH answer."""
    qs = []
    formula = rdMolDescriptors.CalcMolFormula(mol)
    stereo = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True, useLegacyImplementation=False))
    d = dou(mol)
    n_o = sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "O")
    n_oh = count_smarts(mol, "[OX2H]")
    rings = rdMolDescriptors.CalcNumRings(mol)

    def mcq(stem, correct, distractors, solution):
        opts = [str(correct)] + [str(x) for x in distractors]
        # spread the correct-answer position deterministically (avoid always-C leak)
        rot = sum(map(ord, name + stem)) % len(opts)
        opts = opts[rot:] + opts[:rot]
        labels = ["A", "B", "C", "D"][:len(opts)]
        ans = labels[opts.index(str(correct))]
        return {"stem": stem, "options": [{"label": l, "text": t} for l, t in zip(labels, opts)],
                "correct_answer": ans, "solution": solution, "answer_source": "rdkit-computed"}

    qs.append(mcq("What is the molecular formula of the compound shown below?",
                  formula, distractors_formula(mol),
                  f"Counting atoms (with implicit H) in the structure gives {formula}."))
    qs.append(mcq("How many stereocentres (chiral centres) are present in the compound shown?",
                  stereo, distractors_num(stereo),
                  f"RDKit identifies {stereo} tetrahedral stereocentre(s) in this structure."))
    qs.append(mcq("The degree of unsaturation (index of hydrogen deficiency) of the compound shown is:",
                  d, distractors_num(d),
                  f"DoU = (2C+2+N-H-X)/2 = {d} for this molecule (rings + pi bonds)."))
    if n_oh > 0:
        qs.append(mcq("How many hydroxyl (-OH) groups are present in the structure shown?",
                      n_oh, distractors_num(n_oh),
                      f"The structure contains {n_oh} -OH group(s)."))
    if rings > 0:
        qs.append(mcq("How many rings are present in the structure shown?",
                      rings, distractors_num(rings),
                      f"The structure contains {rings} ring(s)."))
    return qs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/tmp/genq")
    ap.add_argument("--per-compound", type=int, default=1, help="questions per compound")
    ap.add_argument("--out", default="/tmp/genq/questions.json")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    resolved = resolve_batch(SEEDS, use_llm=False)
    print(f"resolved {len(resolved)}/{len(SEEDS)} seed compounds")
    out = []
    for name in SEEDS:
        r = resolved.get(name)
        if not r:
            continue
        mol = Chem.MolFromSmiles(r["smiles"])
        if not mol:
            continue
        fig = os.path.join(args.out_dir, f"gen_{name.replace(' ', '_')}.png")
        render(mol, fig)
        allq = make_questions(name, mol)
        # rotate which type per compound so the set is varied
        pick = allq[:args.per_compound] if args.per_compound else allq
        for i, q in enumerate(pick):
            q.update(compound=name, smiles=r["smiles"], figure=fig,
                     id=f"gen_diag_{name.replace(' ', '_')}_{i}")
            out.append(q)
            print(f"  [{name}] {q['stem'][:60]}  ans={q['correct_answer']} "
                  f"({[o['text'] for o in q['options']]})")
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\nwrote {len(out)} generated diagram questions -> {args.out}")


if __name__ == "__main__":
    main()
