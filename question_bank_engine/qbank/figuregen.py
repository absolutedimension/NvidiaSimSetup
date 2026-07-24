"""FIGURE-FIRST diagram-question generation — the deterministic diagram engine.

Instead of asking an LLM to draw an SVG (crude, unreliable), we DRAW the figure ourselves from a
known structure and let a deterministic engine COMPUTE the answer, then phrase an MCQ. The figure
is correct because we drew it; the answer is correct because RDKit computed it — copyright-clean,
and impossible to serve a wrong figure or a wrong key.

Live path: when /generate is called with require_figure=true and can_generate() covers the
(subject, chapter), generate_test() here is used INSTEAD of the LLM-SVG path.

Currently covers CHEMISTRY structures (RDKit). Maths (SymPy) and Physics (matplotlib/schemdraw)
are the next plug-ins — add a builder + widen can_generate().
"""
import os
import hashlib
import random

from . import config
from .models import Question, content_hash

# ---- verified exam-compound seed: (name, canonical SMILES, [topics]) — pre-resolved via OPSIN ----
SEED = [
    ('ethanol', 'CCO', ['alcohol', 'goc']),
    ('propan-2-ol', 'CC(C)O', ['alcohol', 'goc']),
    ('2-methylpropan-2-ol', 'CC(C)(C)O', ['alcohol', 'goc']),
    ('phenol', 'Oc1ccccc1', ['alcohol', 'aromatic', 'goc']),
    ('ethane-1,2-diol', 'OCCO', ['alcohol']),
    ('propane-1,2,3-triol', 'OCC(O)CO', ['alcohol', 'biomolecule']),
    ('methoxybenzene', 'COc1ccccc1', ['alcohol', 'aromatic']),
    ('benzene-1,2-diol', 'Oc1ccccc1O', ['alcohol', 'aromatic']),
    ('butan-1-ol', 'CCCCO', ['alcohol']),
    ('cyclohexanol', 'OC1CCCCC1', ['alcohol']),
    ('ethanal', 'CC=O', ['carbonyl']),
    ('benzaldehyde', 'O=Cc1ccccc1', ['carbonyl', 'aromatic']),
    ('propan-2-one', 'CC(C)=O', ['carbonyl']),
    ('acetophenone', 'CC(=O)c1ccccc1', ['carbonyl', 'aromatic']),
    ('benzophenone', 'O=C(c1ccccc1)c1ccccc1', ['carbonyl', 'aromatic']),
    ('acetic acid', 'CC(=O)O', ['carbonyl', 'goc']),
    ('benzoic acid', 'O=C(O)c1ccccc1', ['carbonyl', 'aromatic']),
    ('2-hydroxybenzoic acid', 'O=C(O)c1ccccc1O', ['carbonyl', 'aromatic']),
    ('oxalic acid', 'O=C(O)C(=O)O', ['carbonyl']),
    ('propanoic acid', 'CCC(=O)O', ['carbonyl']),
    ('butanedioic acid', 'O=C(O)CCC(=O)O', ['carbonyl']),
    ('methanamine', 'CN', ['amine']),
    ('aniline', 'Nc1ccccc1', ['amine', 'aromatic', 'goc']),
    ('N,N-dimethylaniline', 'CN(C)c1ccccc1', ['amine', 'aromatic']),
    ('ethane-1,2-diamine', 'NCCN', ['amine']),
    ('pyridine', 'c1ccncc1', ['amine', 'aromatic']),
    ('N-methylmethanamine', 'CNC', ['amine']),
    ('N,N-diethylethanamine', 'CCN(CC)CC', ['amine']),
    ('benzene', 'c1ccccc1', ['hydrocarbon', 'aromatic', 'goc']),
    ('methylbenzene', 'Cc1ccccc1', ['hydrocarbon', 'aromatic']),
    ('naphthalene', 'c1ccc2ccccc2c1', ['hydrocarbon', 'aromatic']),
    ('cyclohexane', 'C1CCCCC1', ['hydrocarbon']),
    ('cyclohexene', 'C1=CCCCC1', ['hydrocarbon']),
    ('but-2-ene', 'CC=CC', ['hydrocarbon']),
    ('2-methylbuta-1,3-diene', 'C=CC(=C)C', ['hydrocarbon']),
    ('ethenylbenzene', 'C=Cc1ccccc1', ['hydrocarbon', 'aromatic']),
    ('but-1-yne', 'C#CCC', ['hydrocarbon']),
    ('2,2-dimethylbutane', 'CCC(C)(C)C', ['hydrocarbon']),
    ('chlorobenzene', 'Clc1ccccc1', ['haloalkane', 'aromatic']),
    ('chloromethylbenzene', 'ClCc1ccccc1', ['haloalkane', 'aromatic']),
    ('2-chloro-2-methylpropane', 'CC(C)(C)Cl', ['haloalkane']),
    ('1,2-dibromoethane', 'BrCCBr', ['haloalkane']),
    ('bromobenzene', 'Brc1ccccc1', ['haloalkane', 'aromatic']),
    ('2,3-dibromobutane', 'CC(Br)C(C)Br', ['haloalkane', 'stereo']),
    ('trichloromethane', 'ClC(Cl)Cl', ['haloalkane']),
    ('glucose', 'O=C[C@H](O)[C@@H](O)[C@H](O)[C@H](O)CO', ['biomolecule', 'stereo']),
    ('fructose', 'O=C(CO)[C@@H](O)[C@H](O)[C@H](O)CO', ['biomolecule', 'stereo']),
    ('2-aminopropanoic acid', 'CC(N)C(=O)O', ['biomolecule', 'amine']),
    ('aminoacetic acid', 'NCC(=O)O', ['biomolecule', 'amine']),
    ('2-amino-3-hydroxypropanoic acid', 'NC(CO)C(=O)O', ['biomolecule']),
    ('2-hydroxypropanoic acid', 'CC(O)C(=O)O', ['biomolecule', 'carbonyl', 'stereo']),
    ('2-hydroxypropane-1,2,3-tricarboxylic acid', 'O=C(O)CC(O)(CC(=O)O)C(=O)O', ['biomolecule', 'carbonyl']),
    ('urea', 'NC(N)=O', ['biomolecule', 'amine']),
    ('nitrobenzene', 'O=[N+]([O-])c1ccccc1', ['aromatic', 'amine']),
    ('4-nitrophenol', 'O=[N+]([O-])c1ccc(O)cc1', ['aromatic', 'alcohol']),
]

# chapter keyword -> topic tags this figure-first engine can serve
_CHAP_TOPIC = {
    "alcohol": ["alcohol"], "phenol": ["alcohol"], "ether": ["alcohol"],
    "aldehyde": ["carbonyl"], "ketone": ["carbonyl"], "carboxylic": ["carbonyl"],
    "amine": ["amine"], "nitrogen": ["amine"],
    "hydrocarbon": ["hydrocarbon"], "haloalkane": ["haloalkane"], "haloarene": ["haloalkane"],
    "biomolecule": ["biomolecule"],
    "basics of organic": ["goc"], "general organic": ["goc"], "organic chemistry": ["goc"],
}


def _topics_for_chapter(chapter):
    ch = (chapter or "").lower()
    t = set()
    for kw, tags in _CHAP_TOPIC.items():
        if kw in ch:
            t.update(tags)
    return t


def can_generate(exam, subject, chapter=None) -> bool:
    """True when the figure-first engine can serve this (subject, chapter) — i.e. an organic
    chemistry chapter where a molecular-structure diagram question makes sense."""
    if (subject or "").strip().lower() != "chemistry":
        return False
    if not chapter:
        return True
    return bool(_topics_for_chapter(chapter))


# ---- RDKit helpers (lazy import so the module is cheap to import) ------------

def _rdkit():
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
    return Chem, rdMolDescriptors, rdMolDraw2D


def _props(smiles):
    Chem, rdM, _ = _rdkit()
    m = Chem.MolFromSmiles(smiles)
    if not m:
        return None
    from collections import Counter
    cnt = Counter(a.GetSymbol() for a in Chem.AddHs(m).GetAtoms())
    C, H, N = cnt.get("C", 0), cnt.get("H", 0), cnt.get("N", 0)
    X = sum(cnt.get(x, 0) for x in ("F", "Cl", "Br", "I"))
    dou = (2 * C + 2 + N - H - X) // 2
    oh = len(m.GetSubstructMatches(Chem.MolFromSmarts("[OX2H]")))
    return {
        "mol": m,
        "formula": rdM.CalcMolFormula(m),
        "stereo": len(Chem.FindMolChiralCenters(m, includeUnassigned=True, useLegacyImplementation=False)),
        "dou": dou,
        "rings": rdM.CalcNumRings(m),
        "oh": oh,
        "n_o": sum(1 for a in m.GetAtoms() if a.GetSymbol() == "O"),
    }


def _render(mol, out_path):
    _, _, rdMolDraw2D = _rdkit()
    d = rdMolDraw2D.MolDraw2DCairo(360, 300)
    d.DrawMolecule(mol)
    d.FinishDrawing()
    with open(out_path, "wb") as f:
        f.write(d.GetDrawingText())


def _distractors_num(correct, k=3):
    out = []
    for c in (correct + 1, correct - 1, correct + 2, max(0, correct - 2), correct + 3):
        if c != correct and c >= 0 and c not in out:
            out.append(c)
        if len(out) == k:
            break
    return out


def _distractors_formula(smiles):
    from collections import Counter
    Chem, _, _ = _rdkit()
    cnt = Counter(a.GetSymbol() for a in Chem.AddHs(Chem.MolFromSmiles(smiles)).GetAtoms())
    order = ["C", "H", "N", "O", "F", "Cl", "Br", "I", "S", "P"]
    def fmt(c):
        s = ""
        for el in order:
            if c.get(el):
                s += el + (str(c[el]) if c[el] > 1 else "")
        return s
    outs = []
    for dC, dH in [(0, 2), (0, -2), (1, 0)]:
        c = dict(cnt); c["H"] = c.get("H", 0) + dH; c["C"] = c.get("C", 0) + dC
        if c["H"] > 0 and c["C"] > 0:
            outs.append(fmt(Counter(c)))
    return outs


# ---- question builders: each returns (stem, correct, distractors, solution) or None --------

def _q_formula(name, p):
    return ("What is the molecular formula of the compound shown below?",
            p["formula"], _distractors_formula_from_p(name, p),
            f"Counting all atoms (including implicit H) gives {p['formula']}.")

def _distractors_formula_from_p(name, p):
    smi = None
    for n, s, _ in SEED:
        if n == name:
            smi = s; break
    return _distractors_formula(smi) if smi else []

def _q_stereo(name, p):
    n = p["stereo"]
    return ("How many stereocentres (chiral centres) are present in the compound shown?",
            n, _distractors_num(n),
            f"The structure has {n} tetrahedral stereocentre(s).")

def _q_dou(name, p):
    n = p["dou"]
    return ("The degree of unsaturation (index of hydrogen deficiency) of the compound shown is:",
            n, _distractors_num(n),
            f"DoU = (2C+2+N-H-X)/2 = {n} (rings + pi bonds).")

def _q_rings(name, p):
    if p["rings"] < 1:
        return None
    n = p["rings"]
    return ("How many rings are present in the structure shown?",
            n, _distractors_num(n), f"The structure contains {n} ring(s).")

def _q_oh(name, p):
    if p["oh"] < 1:
        return None
    n = p["oh"]
    return ("How many hydroxyl (-OH) groups are present in the structure shown?",
            n, _distractors_num(n), f"The structure contains {n} -OH group(s).")

_BUILDERS = [("formula", _q_formula), ("stereo", _q_stereo), ("dou", _q_dou),
             ("rings", _q_rings), ("oh", _q_oh)]


def _mcq(name, stem, correct, distractors):
    opts = [str(correct)] + [str(d) for d in distractors]
    opts = list(dict.fromkeys(opts))          # dedup, keep order
    while len(opts) < 4:                        # pad if a distractor collided
        opts.append(str(int(float(opts[-1])) + 1) if opts[-1].lstrip("-").isdigit() else opts[-1] + "x")
    opts = opts[:4]
    rot = sum(map(ord, name + stem)) % 4        # spread the correct position
    opts = opts[rot:] + opts[:rot]
    labels = ["A", "B", "C", "D"]
    ans = labels[opts.index(str(correct))]
    return [{"label": l, "text": t} for l, t in zip(labels, opts)], ans


def _make_question(name, smiles, qkey, builder, exam, subject, chapter, difficulty):
    p = _props(smiles)
    if not p:
        return None
    built = builder(name, p)
    if not built:
        return None
    stem, correct, distractors, solution = built
    opts, ans = _mcq(name, stem, correct, distractors)
    qid = "gen_diag_chem_" + hashlib.md5((smiles + "|" + qkey).encode()).hexdigest()[:12]
    fname = f"{qid}.gen.png"
    os.makedirs(config.FIG_DIR, exist_ok=True)
    _render(p["mol"], os.path.join(config.FIG_DIR, fname))
    figure_url = config.PUBLIC_BASE.rstrip("/") + "/figures/" + fname
    q = Question(
        id=qid, exam=exam or "", subject=subject or "Chemistry", stem=stem, qtype="MCQ_single",
        options=opts, correct_answer=ans, solution=solution,
        chapter=chapter, concept=name, difficulty=difficulty,
        needs_figure=True, figure_url=figure_url, figure_refs=[fname],
        source="figure-first", generated=True, hash=content_hash(stem))
    q.verified = True
    return q


def _eligible_combos(chapter):
    topics = None
    if chapter:
        topics = _topics_for_chapter(chapter)
        if not topics:
            return []   # chapter is not an organic-structure chapter → draw nothing (guard)
    combos = []
    for name, smiles, tags in SEED:
        if topics and not (set(tags) & topics):
            continue
        for qkey, builder in _BUILDERS:
            combos.append((name, smiles, qkey, builder))
    return combos


def generate_test(store, spec: dict, count: int = 5) -> dict:
    """Figure-first replacement for generator.generate_test — same return shape. Draws structures
    and computes answers with RDKit; upserts verified diagram questions with real figure_url."""
    exam, subject, chapter = spec.get("exam"), spec.get("subject"), spec.get("chapter")
    difficulty = spec.get("dmax") or spec.get("dmin") or 2
    combos = _eligible_combos(chapter)
    random.shuffle(combos)
    accepted = []
    for name, smiles, qkey, builder in combos:
        if len(accepted) >= count:
            break
        try:
            q = _make_question(name, smiles, qkey, builder, exam, subject, chapter, difficulty)
        except Exception:
            q = None
        if q is None:
            continue
        store.upsert(q)
        accepted.append(q)
    return {
        "spec": spec,
        "generator": "figure-first-chem",
        "requested": count,
        "generated": len(accepted),
        "rejected": [],
        "questions": [q.to_dict() for q in accepted],
        "answer_key": {q.id: q.correct_answer for q in accepted},
    }
