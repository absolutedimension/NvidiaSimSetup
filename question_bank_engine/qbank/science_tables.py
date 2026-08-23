"""Verified fact tables for रसायन शास्त्र and जीव विज्ञान — the Class-10 half of Part II that
`sciencegen` cannot reach, since it only computes physics numericals. By the blueprint these are
25% + 25% of the General Science subsection and were both 0%.

⭐ THE POINT OF THIS FILE IS THAT THE TWO SUBJECTS GET DIFFERENT TREATMENT, BECAUSE ONE OF THEM
HAS AN AUTHORITATIVE MACHINE-READABLE SOURCE AND THE OTHER DOES NOT.

  CHEMISTRY  is DERIVED and MACHINE-VERIFIED. Element symbols and atomic numbers are not typed at
             all — tools/fetch_ptable.py pulls them from PubChem (NIH) into drop/bssc/ELEMENTS.json
             and this module reads that. Compound formulae ARE hand-written, but every one is
             checked against PubChem's own molecular formula for that compound name, which is a
             genuine oracle rather than a text-similarity guess. `CHEM_REVIEWED` can therefore be
             earned by a machine.

  BIOLOGY    has no equivalent oracle, so it gets the same HUMAN gate as history: an evidence sheet
             for a person to tick. `BIO_REVIEWED` stays False until someone signs it off.

This distinction is the lesson from history_tables, where two automated verifiers were written and
both were measured worthless. Automation is worth having exactly where an authoritative source can
be queried, and is worse than nothing where it cannot — because a green line gets mistaken for
verification.
"""
import io
import json
import os
import re

# Chemistry can be earned by machine (see verify_chemistry). Biology cannot — see
# drop/bssc/SCIENCE_REVIEW.md and set this only after a person has read it.
#
# ENABLED 2026-08-21. What earned it, and what would un-earn it:
#   - element symbols and atomic numbers are DERIVED from PubChem (NIH), never typed
#   - all 20 compound formulae confirmed against PubChem's own answer, live, with the cache cleared
#   - verify_chemistry() sabotage-tested on 11 corrupted rows: 11 of 11 caught
#   - the one hand-data step left is the ALIAS "Limestone -> Calcium carbonate"
# Re-run `python3 -m qbank.science_tables` after ANY edit to COMPOUND_FORMULA; this flag is a
# claim about a specific set of rows, not about the file.
CHEM_REVIEWED = True
BIO_REVIEWED = False

# Biology is not one thing. VITAMIN_CHEMICAL_NAME is a set of CHEMICAL IDENTITIES, and the same
# NIH oracle that earned CHEM_REVIEWED holds both names against one compound record — so this
# table can be earned by machine while the other three cannot. Splitting the flag is the same
# argument science_fact_tables() already makes for splitting chemistry from biology: one flag over
# two levels of evidence either holds back verified facts or ships unverified ones.
#
# ENABLED 2026-08-23. What earned it, and what would un-earn it:
#   - all 6 rows confirmed against PubChem's synonym list for that vitamin, live
#   - matching is EXACT after normalisation, never substring: "niacin" is inside "niacinamide",
#     which is a different compound, so a wrong row would have passed
#   - sabotage-tested; see verify_vitamin_names.__doc__ for what it does and does not check
#   - the 7th row, Vitamin D -> calciferol, is NOT here: see VITAMIN_CHEMICAL_NAME_PENDING
# Re-run `python3 -m qbank.science_tables` after ANY edit to VITAMIN_CHEMICAL_NAME.
BIO_NAMES_REVIEWED = True

_ELEM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "drop", "bssc", "ELEMENTS.json")

# WHICH elements a Bihar Class-10 student actually meets. A curriculum judgement, not a fact —
# generating "what is the symbol of Livermorium" from the full 118 would be correct and useless.
_CLASS10_ELEMENTS = [
    "Hydrogen", "Helium", "Carbon", "Nitrogen", "Oxygen", "Sodium", "Magnesium", "Aluminum",
    "Silicon", "Phosphorus", "Sulfur", "Chlorine", "Potassium", "Calcium", "Iron", "Copper",
    "Zinc", "Silver", "Gold", "Mercury", "Lead", "Tin", "Nickel", "Platinum", "Uranium",
    "Neon", "Argon", "Bromine", "Iodine", "Manganese",
]


def _load_elements():
    if not os.path.exists(_ELEM_PATH):
        return {}
    return json.load(io.open(_ELEM_PATH, encoding="utf-8"))["elements"]


_ELEMENTS = _load_elements()

# DERIVED — never typed. If ELEMENTS.json is missing these come out empty rather than wrong, which
# is the right failure: an absent table generates no questions, a guessed one generates bad ones.
ELEMENT_SYMBOL = {n: _ELEMENTS[n]["symbol"] for n in _CLASS10_ELEMENTS if n in _ELEMENTS}
ELEMENT_ATOMIC_NUMBER = {n: str(_ELEMENTS[n]["atomic_number"])
                         for n in _CLASS10_ELEMENTS if n in _ELEMENTS}

# ---- रसायन: common name -> chemical formula -------------------------------------
# Hand-written, and every row is checked against PubChem by verify_chemistry(). The everyday names
# are what the exam asks ("the chemical formula of baking soda"), and they are also what PubChem
# resolves, so the check is on exactly the pairing the paper prints.
COMPOUND_FORMULA = {
    "Common salt": "NaCl",
    "Baking soda": "NaHCO3",
    "Washing soda": "Na2CO3",
    "Quicklime": "CaO",
    "Slaked lime": "Ca(OH)2",
    "Limestone": "CaCO3",
    "Caustic soda": "NaOH",
    "Bleaching powder": "Ca(ClO)2",
    # NOT CaSO4 — that is anhydrous calcium sulfate. Plaster of Paris is the HEMIHYDRATE, and
    # PubChem said so when the first version of this row claimed otherwise. Written the way an
    # exam prints it; the verifier compares atom RATIOS, so this matches PubChem's Ca2H2O9S2.
    "Plaster of Paris": "CaSO4·½H2O",
    "Blue vitriol": "CuSO4",
    "Sulfuric acid": "H2SO4",
    "Nitric acid": "HNO3",
    "Hydrochloric acid": "HCl",
    # Written the way an Indian textbook writes it, NOT the way PubChem returns it. PubChem uses
    # Hill notation (H3N, C2H6O, CH4N2O); a Bihar student is taught NH3, C2H5OH, CO(NH2)2. The
    # verifier compares ATOM COUNTS, so both forms confirm against the same PubChem record — this
    # is a presentation choice, not a factual one, and the fact stays machine-checked either way.
    "Ammonia": "NH3",
    "Methane": "CH4",
    "Ethanol": "C2H5OH",
    "Glucose": "C6H12O6",
    "Urea": "CO(NH2)2",
    "Carbon dioxide": "CO2",
    "Ozone": "O3",
}

# ---- जीव विज्ञान ---------------------------------------------------------------
# Function tables, and the values are mutually exclusive so `_false_value` has room to work:
# scurvy comes only from vitamin C, so pairing it with vitamin A is false BY OUR OWN DATA.
# Held back from VITAMIN_CHEMICAL_NAME because a machine cannot settle it, which is the only
# reason a row is ever held back in this file. PubChem's "Calciferol" record IS ergocalciferol,
# i.e. vitamin D2 specifically, while "vitamin D" names a GROUP that also contains D3
# (cholecalciferol). "Vitamin D = calciferol" is what Indian Class-10 texts teach and what the
# commission would ask, so the row is very likely right for this paper — but "very likely right"
# is a human's call, not an oracle's, and the alternative is an ALIAS that forces a green line
# over a judgement (see the Limestone note in verify_chemistry). It joins the live table the
# moment BIO_REVIEWED flips.
VITAMIN_CHEMICAL_NAME_PENDING = {
    "Vitamin D": "calciferol",
}

VITAMIN_DEFICIENCY = {
    "Vitamin A": "night blindness",
    "Vitamin B1": "beriberi",
    "Vitamin B3": "pellagra",
    "Vitamin B12": "pernicious anaemia",
    "Vitamin C": "scurvy",
    "Vitamin D": "rickets",
    "Vitamin K": "delayed blood clotting",
    "Iron": "anaemia",
    "Iodine": "goitre",
}

VITAMIN_CHEMICAL_NAME = {
    "Vitamin A": "retinol",
    "Vitamin B1": "thiamine",
    "Vitamin B2": "riboflavin",
    "Vitamin B3": "niacin",
    "Vitamin C": "ascorbic acid",

    "Vitamin E": "tocopherol",
}

# hormone -> gland, NOT gland -> hormone. A gland secretes several hormones, so gland -> hormone is
# not a function and a "false" pairing built from it could be accidentally true — the same trap the
# 73rd/74th Amendment year collision exposed in polity_tables.
HORMONE_GLAND = {
    "Insulin": "the pancreas",
    "Thyroxine": "the thyroid gland",
    "Adrenaline": "the adrenal gland",
    "Growth hormone": "the pituitary gland",
    "Parathormone": "the parathyroid gland",
}

DISEASE_PATHOGEN = {
    "Malaria": "a protozoan (Plasmodium)",
    "Tuberculosis": "a bacterium (Mycobacterium tuberculosis)",
    "Dengue": "a virus spread by the Aedes mosquito",
    "Cholera": "a bacterium (Vibrio cholerae)",
    "Ringworm": "a fungus",
    "Kala-azar": "a protozoan spread by the sandfly",
}

_CHEM = {"ELEMENT_SYMBOL": ELEMENT_SYMBOL, "ELEMENT_ATOMIC_NUMBER": ELEMENT_ATOMIC_NUMBER,
         "COMPOUND_FORMULA": COMPOUND_FORMULA}
_BIO = {"VITAMIN_DEFICIENCY": VITAMIN_DEFICIENCY,
        "VITAMIN_CHEMICAL_NAME": VITAMIN_CHEMICAL_NAME,
        "HORMONE_GLAND": HORMONE_GLAND, "DISEASE_PATHOGEN": DISEASE_PATHOGEN}
_ALL = dict(_CHEM, **_BIO)


# ---- Hindi ---------------------------------------------------------------------
# Element names are printed in Devanagari as the exam prints them — mostly transliterations, with
# the traditional word where a Bihar textbook uses one (लोहा, ताँबा, चाँदी, सोना, पारा). Hand data,
# so it sits in the same review sheet as the biology facts.
HI = {
    "Hydrogen": "हाइड्रोजन", "Helium": "हीलियम", "Carbon": "कार्बन", "Nitrogen": "नाइट्रोजन",
    "Oxygen": "ऑक्सीजन", "Sodium": "सोडियम", "Magnesium": "मैग्नीशियम", "Aluminum": "एल्युमिनियम",
    "Silicon": "सिलिकॉन", "Phosphorus": "फॉस्फोरस", "Sulfur": "सल्फर", "Chlorine": "क्लोरीन",
    "Potassium": "पोटैशियम", "Calcium": "कैल्शियम", "Iron": "लोहा", "Copper": "ताँबा",
    "Zinc": "जस्ता", "Silver": "चाँदी", "Gold": "सोना", "Mercury": "पारा", "Lead": "सीसा",
    "Tin": "टिन", "Nickel": "निकल", "Platinum": "प्लैटिनम", "Uranium": "यूरेनियम",
    "Neon": "नियॉन", "Argon": "आर्गन", "Bromine": "ब्रोमीन", "Iodine": "आयोडीन",
    "Manganese": "मैंगनीज",
    # compounds by their everyday names
    "Common salt": "साधारण नमक", "Baking soda": "खाने का सोडा", "Washing soda": "धोने का सोडा",
    "Quicklime": "बिना बुझा चूना", "Slaked lime": "बुझा हुआ चूना", "Limestone": "चूना-पत्थर",
    "Caustic soda": "कॉस्टिक सोडा", "Bleaching powder": "विरंजक चूर्ण",
    "Plaster of Paris": "प्लास्टर ऑफ पेरिस", "Blue vitriol": "नीला थोथा",
    "Sulfuric acid": "सल्फ्यूरिक अम्ल", "Nitric acid": "नाइट्रिक अम्ल",
    "Hydrochloric acid": "हाइड्रोक्लोरिक अम्ल", "Ammonia": "अमोनिया", "Methane": "मीथेन",
    "Ethanol": "एथेनॉल", "Glucose": "ग्लूकोज", "Urea": "यूरिया",
    "Carbon dioxide": "कार्बन डाइऑक्साइड", "Ozone": "ओज़ोन",
    # biology
    "Vitamin A": "विटामिन A", "Vitamin B1": "विटामिन B1", "Vitamin B2": "विटामिन B2",
    "Vitamin B3": "विटामिन B3", "Vitamin B12": "विटामिन B12", "Vitamin C": "विटामिन C",
    "Vitamin D": "विटामिन D", "Vitamin E": "विटामिन E", "Vitamin K": "विटामिन K",
    "night blindness": "रतौंधी", "beriberi": "बेरी-बेरी", "pellagra": "पेलाग्रा",
    "pernicious anaemia": "घातक रक्ताल्पता", "scurvy": "स्कर्वी", "rickets": "रिकेट्स",
    "delayed blood clotting": "रक्त का देर से जमना", "anaemia": "रक्ताल्पता", "goitre": "घेंघा",
    "retinol": "रेटिनॉल", "thiamine": "थायमिन", "riboflavin": "राइबोफ्लेविन",
    "niacin": "नियासिन", "ascorbic acid": "एस्कॉर्बिक अम्ल", "calciferol": "कैल्सिफेरॉल",
    "tocopherol": "टोकोफेरॉल",
    "Insulin": "इंसुलिन", "Thyroxine": "थायरॉक्सिन", "Adrenaline": "एड्रिनेलिन",
    "Growth hormone": "वृद्धि हार्मोन", "Parathormone": "पैराथॉर्मोन",
    "the pancreas": "अग्न्याशय", "the thyroid gland": "थायरॉइड ग्रंथि",
    "the adrenal gland": "अधिवृक्क ग्रंथि", "the pituitary gland": "पीयूष ग्रंथि",
    "the parathyroid gland": "पैराथायरॉइड ग्रंथि",
    "Malaria": "मलेरिया", "Tuberculosis": "क्षय रोग", "Dengue": "डेंगू", "Cholera": "हैजा",
    "Ringworm": "दाद", "Kala-azar": "कालाजार",
    "a protozoan (Plasmodium)": "एक प्रोटोजोआ (प्लाज्मोडियम)",
    "a bacterium (Mycobacterium tuberculosis)": "एक जीवाणु (माइकोबैक्टीरियम ट्यूबरकुलोसिस)",
    # Oblique: the template appends "से होता है", so "वाला ... से" must be "वाले ... से".
    # Third time this exact agreement has bitten — seating (बैठा/बैठी), history (वाला आयोग), here.
    "a virus spread by the Aedes mosquito": "एडीज मच्छर से फैलने वाले एक विषाणु",
    "a bacterium (Vibrio cholerae)": "एक जीवाणु (विब्रियो कॉलेरी)",
    "a fungus": "एक कवक",
    "a protozoan spread by the sandfly": "बालू-मक्खी से फैलने वाले एक प्रोटोजोआ",
    "Iron": "लोहा", "Iodine": "आयोडीन",
}


# Chemical symbols, formulae and atomic numbers are LANGUAGE-NEUTRAL — a Hindi paper prints "NaCl",
# "Fe" and "26" exactly as an English one does. staticgk_hi's gate is all-or-nothing and correctly
# refuses anything it has no Hindi for, so these are registered as their own Hindi. Generated from
# the tables rather than typed, so the two can never drift apart.
HI.update({v: v for v in ELEMENT_SYMBOL.values()})
HI.update({v: v for v in ELEMENT_ATOMIC_NUMBER.values()})
HI.update({v: v for v in COMPOUND_FORMULA.values()})


def hindi_gaps():
    """Rows that cannot go on a bilingual paper because a key or value has no Hindi.
    Chemical formulae and atomic numbers are language-neutral and need no entry."""
    out = []
    for tname, table in _ALL.items():
        for k, v in table.items():
            miss = [x for x in (k, v) if x not in HI
                    and not re.fullmatch(r"[A-Za-z0-9()\u00b7\u00bd.]+", x)]
            if miss:
                out.append((tname, k, v, miss))
    return out


def write_review_sheet(path="drop/bssc/SCIENCE_REVIEW.md",
                       corpus_path="/tmp/biocorpus/CORPUS.txt"):
    """BIOLOGY rows beside the source sentences that bear on them, for a human to tick.

    Chemistry is NOT in this sheet: its element data is derived from PubChem and never typed, and
    every compound formula is checked against PubChem's own answer by verify_chemistry(), which was
    sabotage-tested on eleven corrupted rows and caught all eleven. That is a real oracle, so
    chemistry does not need a person. Biology has no such source, so it gets the same human gate as
    history — and the Hindi for BOTH subjects is hand-written, so it is reviewed here too.
    """
    import os
    lines = ["# General Science — biology fact review sheet", "",
             "Chemistry is machine-verified against PubChem (NIH) and is not listed here.",
             "**VITAMIN_CHEMICAL_NAME is not listed here either, as of 2026-08-23.** Vitamin ->",
             "chemical name is a set of CHEMICAL IDENTITIES, and the same NIH oracle answers",
             "those: all 6 rows are confirmed against PubChem's synonym list for that vitamin,",
             "matched exactly rather than by substring, and sabotage-tested (7 of 8 slips caught;",
             "the miss is written up in `verify_vitamin_names.__doc__`). It is gated separately",
             "on `BIO_NAMES_REVIEWED`, which is already True. **That is 6 rows you do not have",
             "to read.** One row was NOT machine-earnable and is below with the others.", "",
             "**Everything remaining is hand-written, facts and Hindi both.** Tick or correct",
             "each row. None of it is used by the paper builder until `BIO_REVIEWED` is set to",
             "True in `qbank/science_tables.py`.", "",
             "⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:", "",
             "1. `BIO_REVIEWED = True` in `qbank/science_tables.py`",
             "2. add these to `concepts` for **Biology** in `drop/bssc/SYLLABUS_MAP.json`,",
             "   alongside the `VITAMIN_CHEMICAL_NAME` already there:", "",
             "   `[\"VITAMIN_DEFICIENCY\", \"HORMONE_GLAND\", \"DISEASE_PATHOGEN\"]`",
             "", "A topic with `concepts` counts as GENERATABLE, so listing it before the flag is",
             "set promises questions the gate then refuses, and the section pads from elsewhere.",
             ""]
    sents = []
    if os.path.exists(corpus_path):
        sents = re.split(r"(?<=[.!?])\s+|\n+",
                         io.open(corpus_path, encoding="utf-8").read())
    n = 0
    # The machine-earned table is skipped; the one row it could not earn is shown on its own,
    # with the reason, so the reviewer knows why a single row is being asked of them.
    sheet = {k: v for k, v in _BIO.items() if k != "VITAMIN_CHEMICAL_NAME"}
    sheet["VITAMIN_CHEMICAL_NAME (the one row PubChem could not settle)"] = \
        VITAMIN_CHEMICAL_NAME_PENDING
    for tname, table in sheet.items():
        lines += [f"## {tname}", ""]
        if tname.startswith("VITAMIN_CHEMICAL_NAME ("):
            lines += ["PubChem's `Calciferol` record IS ergocalciferol — vitamin **D2** — while",
                      "\"vitamin D\" names a group that also contains D3 (cholecalciferol). The row",
                      "is what Class-10 texts teach and what the commission would ask, but that is",
                      "a teacher's call, not an oracle's.", ""]
        for k, v in table.items():
            n += 1
            lines += [f"- [ ] **{k}** → **{v}**   ·   हिंदी: {HI.get(k, '?')} → {HI.get(v, '?')}"]
            kw = [w for w in re.findall(r"[A-Za-z]+", (k + " " + v).lower()) if len(w) > 3]
            scored = sorted(((sum(1 for w in kw if w in s.lower()), -len(s), s.strip())
                             for s in sents), reverse=True)[:2]
            for hit, _, s2 in scored:
                if hit >= 2:
                    lines.append(f"      > {s2[:260]}")
            lines.append("")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} biology rows -> {path}")
    return n


def verify_chemistry(quiet=False):
    """Check every compound formula against PubChem's own answer for that name.

    A real oracle, not a similarity score: PubChem is asked for the molecular formula of the exact
    name the paper will print, and the row must match it. Formulae are compared after normalising
    Hill-notation spacing and dropping charge marks, because PubChem writes 'Ca(ClO)2' and
    'CaCl2O2' for the same substance depending on the record.

    Needs the network. Returns the rows that disagree, or None if the query could not be made —
    and NOT-CHECKED is reported as loudly as WRONG, because a silent skip is how an unverified
    table gets treated as a verified one.
    """
    import urllib.parse
    import urllib.request
    bad, unchecked = [], []
    # Cache PubChem's answers on disk. Without it a sabotage run — which re-verifies the whole
    # table once per corrupted row — makes hundreds of network calls and takes minutes, which in
    # practice means the sabotage test stops being run at all.
    cache_path = os.path.join(os.path.dirname(_ELEM_PATH), "PUBCHEM_FORMULAE.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(io.open(cache_path, encoding="utf-8"))
        except Exception:
            cache = {}

    # PubChem does not resolve every everyday name — "Limestone" is a rock, not a compound record.
    # The formula is still checked, against the substance's chemical name. The step
    # "limestone IS calcium carbonate" is then hand-data, and is called out here rather than hidden
    # behind a green line.
    ALIAS = {"Limestone": "Calcium carbonate"}

    def atoms(f):
        """{element: ratio} from a formula, normalised so hydrates compare correctly.

        'CaSO4·½H2O' and PubChem's 'Ca2H2O9S2' are the same substance written at different scales,
        so absolute counts disagree and ratios agree. Handles one bracket level and a '·' hydrate
        part with an integer or ½ coefficient — which is everything these formulae use.
        """
        f = f.replace(" ", "")
        total = {}
        for part in re.split(r"[\u00b7.]", f):
            if not part:
                continue
            m = re.match(r"^(\d+|\u00bd)", part)
            mult = 0.5 if (m and m.group(1) == "\u00bd") else (int(m.group(1)) if m else 1)
            part = part[m.end():] if m else part
            for el, n in _expand(part).items():
                total[el] = total.get(el, 0) + n * mult
        return total

    def compare(ours, ref):
        """Exact atom counts, EXCEPT for a hydrate, where the two sources may differ in scale.

        Normalising to ratios unconditionally was tried and let 'Ozone -> O2' through: a
        single-element formula always has ratio 1, so O2 and O3 compared equal. Scale-invariance
        is only legitimate where the formula actually carries a '·' hydrate part.
        """
        a, b = atoms(ours), atoms(ref)
        if a == b:
            return True
        if "\u00b7" not in ours and "." not in ours:
            return False
        def norm(d):
            lo = min(d.values()) if d else 1
            return {k: round(v / lo, 3) for k, v in d.items()}
        return norm(a) == norm(b)

    def _expand(f):
        """{element: count} for a bracket-expanded fragment."""
        for m in list(re.finditer(r"\(([^()]*)\)(\d*)", f)):
            inner, mult = m.group(1), int(m.group(2) or 1)
            f = f.replace(m.group(0), "".join(
                f"{el}{(int(n or 1) * mult)}" for el, n in re.findall(r"([A-Z][a-z]?)(\d*)", inner)))
        out = {}
        for el, n in re.findall(r"([A-Z][a-z]?)(\d*)", f):
            if el:
                out[el] = out.get(el, 0) + int(n or 1)
        return out

    for name, formula in COMPOUND_FORMULA.items():
        url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
               + urllib.parse.quote(ALIAS.get(name, name)) + "/property/MolecularFormula/JSON")
        if name in cache:
            ref = cache[name]
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "trigunai-qbank/1.0"})
                d = json.loads(urllib.request.urlopen(req, timeout=25).read().decode())
                ref = d["PropertyTable"]["Properties"][0]["MolecularFormula"]
                cache[name] = ref
            except Exception as e:
                unchecked.append((name, formula, repr(e)[:50]))
                continue
        if not compare(formula, ref):
            bad.append((name, formula, ref))
    try:
        json.dump(cache, io.open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    if not quiet:
        n = len(COMPOUND_FORMULA)
        print(f"COMPOUND_FORMULA: {n - len(bad) - len(unchecked)} of {n} confirmed against PubChem")
        for name, f, ref in bad:
            print(f"   WRONG      {name}: we say {f}, PubChem says {ref}")
        for name, f, why in unchecked:
            print(f"   NOT CHECKED {name} ({f}) — {why}")
        # the derived tables cannot be wrong, but they CAN be missing
        miss = [n for n in _CLASS10_ELEMENTS if n not in ELEMENT_SYMBOL]
        print(f"ELEMENT tables: {len(ELEMENT_SYMBOL)} elements derived from PubChem"
              + (f"; MISSING {miss}" if miss else "; none missing"))
    return bad, unchecked


def verify_vitamin_names(quiet=False):
    """Check every vitamin -> chemical name against PubChem's SYNONYM list for that vitamin.

    ⭐ WHY THIS TABLE AND NOT THE OTHER THREE. This file's own rule is that automation is worth
    having exactly where an authoritative source can be queried, and is worse than nothing where
    it cannot. "Vitamin C is ascorbic acid" is a chemical identity, and PubChem — the same NIH
    oracle that earned CHEM_REVIEWED — lists both names against one compound record. That is a
    real check, not a text-similarity guess.

    The other three biology tables have no such source and are not touched here. "Insulin is
    secreted by the pancreas" and "Vitamin A deficiency causes night blindness" are true, and
    there is no endpoint that will say so; writing a checker that gestures at a corpus and returns
    green would be the exact mistake history_tables measured and abandoned. Those stay behind the
    human gate.

    WHAT IT DOES NOT CATCH, measured rather than assumed. Sabotaged with eight plausible slips it
    caught seven: another row's value, an adjacent B vitamin, a real-but-wrong substance, a
    precursor ("Vitamin A -> beta-carotene"), and "Vitamin B3 -> niacinamide", which is one
    substring away from niacin and a different compound. It MISSED "Vitamin C -> ascorbate",
    because PubChem lists the anion against the same record as the acid — the oracle is answering
    "same compound record", which is not quite "the name a paper should print". An acid confused
    with its own salt would pass. That is the limit of what this check is worth, and it is written
    down here rather than left for someone to discover in front of a student.

    Returns (bad, unchecked). NOT-CHECKED is reported as loudly as WRONG — a silent skip is how an
    unverified table gets treated as a verified one.
    """
    import urllib.parse
    import urllib.request
    bad, unchecked = [], []
    cache_path = os.path.join(os.path.dirname(_ELEM_PATH), "PUBCHEM_VITAMINS.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(io.open(cache_path, encoding="utf-8"))
        except Exception:
            cache = {}

    def norm(x):
        """Compare names the way PubChem varies them: case, hyphens, and the stereo/vitamer
        prefixes it carries on the same record — 'l-ascorbic acid' and 'all-trans-Retinol' are
        the record's own words for what the paper prints as 'ascorbic acid' and 'retinol'."""
        x = re.sub(r"^(all-trans-|l-|d-|dl-|\(\+\)-|\(-\)-)+", "", str(x).strip().lower())
        return re.sub(r"[^a-z0-9]", "", x)

    for vit, chem in VITAMIN_CHEMICAL_NAME.items():
        if vit in cache:
            syns = cache[vit]
        else:
            url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                   + urllib.parse.quote(vit) + "/synonyms/JSON")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "trigunai-qbank/1.0"})
                d = json.loads(urllib.request.urlopen(req, timeout=25).read().decode())
                syns = d["InformationList"]["Information"][0]["Synonym"]
                cache[vit] = syns
            except Exception as e:
                unchecked.append((vit, chem, repr(e)[:50]))
                continue
        # The row is confirmed when the chemical name the paper will print is one of the names
        # PubChem holds for that vitamin. Substring matching was rejected: "niacin" is inside
        # "niacinamide", which is a DIFFERENT compound, so a wrong row would have passed.
        if not any(norm(sy) == norm(chem) for sy in syns):
            bad.append((vit, chem, ", ".join(syns[:6])))
    try:
        json.dump(cache, io.open(cache_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    if not quiet:
        n = len(VITAMIN_CHEMICAL_NAME)
        print(f"VITAMIN_CHEMICAL_NAME: {n - len(bad) - len(unchecked)} of {n} confirmed "
              f"against PubChem")
        for vit, chem, syns in bad:
            print(f"   WRONG       {vit}: we say {chem}; PubChem's names are {syns}")
        for vit, chem, why in unchecked:
            print(f"   NOT CHECKED {vit} ({chem}) — {why}")
    return bad, unchecked


if __name__ == "__main__":
    verify_chemistry()
    verify_vitamin_names()
    write_review_sheet()
