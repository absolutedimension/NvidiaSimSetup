#!/usr/bin/env python3
"""Name -> structure resolution with fallbacks: OPSIN -> PubChem -> LLM-SMILES.

OPSIN is deterministic and covers IUPAC + common names but NOT drug trade names,
organometallics, or many common-name compounds. PubChem PUG-REST covers those
(chlordiazepoxide, ferrocene, aspirin, peracetic acid...). LLM-SMILES is the last
resort for compounds only DESCRIBED, not named. Every candidate is validated by RDKit.

    from resolve import resolve_batch
    resolved = resolve_batch(["aniline","chlordiazepoxide", ...], use_llm=True)
    # -> {name: {"smiles":canonical, "formula":..., "source":"opsin|pubchem|llm"}}
"""
import json
import os
import time
import urllib.parse
import urllib.request

from py2opsin import py2opsin
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

PROXY = os.environ.get("QBANK_LLM_BASE_URL", "http://localhost:4000/v1").rstrip("/") + "/chat/completions"
KEY = os.environ.get("QBANK_LLM_API_KEY", "sk-trigunai-master-key-2026")
CHAT = os.environ.get("QBANK_CHAT_MODEL", "gpt-4o")


def _canon(smiles):
    if not smiles:
        return None
    m = Chem.MolFromSmiles(smiles)
    if not m:
        return None
    return Chem.MolToSmiles(m), rdMolDescriptors.CalcMolFormula(m)


def opsin_names(names):
    """Batch OPSIN (single JVM call, no temp-file race). {name: smiles}."""
    names = [n for n in names if n]
    if not names:
        return {}
    try:
        smis = py2opsin(names)
    except Exception:
        smis = []
    if isinstance(smis, str):
        smis = [smis]
    return {n: s for n, s in zip(names, smis) if s}


def pubchem_name(name, timeout=12):
    """PubChem PUG-REST name -> SMILES (isomeric preferred). None on 404/miss."""
    enc = urllib.parse.quote(name, safe="")
    for prop in ("IsomericSMILES", "CanonicalSMILES"):
        url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{enc}/property/{prop}/TXT")
        try:
            r = urllib.request.urlopen(url, timeout=timeout)
            txt = r.read().decode().strip().splitlines()
            if txt and not txt[0].startswith("Status:"):
                return txt[0].strip()
        except Exception:
            continue
    return None


def llm_smiles(names, timeout=90):
    """One LLM call: names -> SMILES for the still-unresolved. {name: smiles}."""
    names = [n for n in names if n]
    if not names:
        return {}
    sys_p = ("You are a chemistry expert. For each compound name, give a valid SMILES string. "
             "Use your best chemical knowledge; if a name is a generic class or you are unsure, "
             "use null. Return ONLY JSON: {\"<name>\": \"<smiles-or-null>\", ...}.")
    body = {"model": CHAT, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": "Names:\n" + "\n".join(names)}]}
    if not str(CHAT).startswith("gpt-5"):
        body["temperature"] = 0
    data = json.dumps(body).encode()
    req = urllib.request.Request(PROXY, data=data, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        out = json.loads(r["choices"][0]["message"]["content"])
        return {k: v for k, v in out.items() if v}
    except Exception:
        return {}


def resolve_batch(names, use_llm=False, pubchem_delay=0.25):
    """OPSIN -> PubChem -> (optional) LLM. Returns {name: {smiles, formula, source}}."""
    names = sorted({n for n in names if n})
    out = {}

    # 1) OPSIN
    op = opsin_names(names)
    for n, s in op.items():
        c = _canon(s)
        if c:
            out[n] = {"smiles": c[0], "formula": c[1], "source": "opsin"}

    # 2) PubChem for OPSIN misses (serialized — respect rate limit)
    misses = [n for n in names if n not in out]
    for n in misses:
        s = pubchem_name(n)
        time.sleep(pubchem_delay)
        c = _canon(s) if s else None
        if c:
            out[n] = {"smiles": c[0], "formula": c[1], "source": "pubchem"}

    # 3) LLM-SMILES for still-missing (one batched call)
    if use_llm:
        still = [n for n in names if n not in out]
        if still:
            for n, s in llm_smiles(still).items():
                c = _canon(s)
                if c:
                    out[n] = {"smiles": c[0], "formula": c[1], "source": "llm"}
    return out


if __name__ == "__main__":
    import sys
    test = sys.argv[1:] or ["aniline", "chlordiazepoxide", "ferrocene", "peracetic acid",
                            "polystyrene", "manganese decacarbonyl", "tert-butanol"]
    res = resolve_batch(test, use_llm=True)
    for n in test:
        r = res.get(n)
        print(f"  {'OK ' if r else 'XX '} {n:28s} {r['source'] if r else '-':8s} {r['smiles'] if r else ''}")
    print(f"resolved {len(res)}/{len(test)}")
