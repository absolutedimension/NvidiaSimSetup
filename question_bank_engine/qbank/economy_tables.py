"""Verified fact tables for आर्थिक परिदृश्य / पंचवर्षीय योजना — 6% of Part I, previously 0%.

WHY THESE TWO SHAPES AND NOT THE OBVIOUS THIRD. `staticgk_forms._false_value` builds a false
statement by pairing a key with a DIFFERENT value from the same table, and it will only use a
value owned by exactly ONE key. So a table earns its place by having values that are largely
distinct — plan periods and years are, which is why both tables here are of that shape.

The table this file deliberately does NOT contain is "which plan aimed at what". Plan objectives
are stated in prose and paraphrased differently by every textbook ("removal of poverty" vs
"garibi hatao" vs "poverty alleviation and self-reliance"), so a distractor drawn from a sibling
row is not reliably FALSE — two plans can both be described as aiming at self-reliance. A table
whose false statements might be true is worse than no table, because every check downstream
reports green. Periods and years do not have that problem: exactly one plan ran 1951–56.

SHELF LIFE. Everything here is a settled fact in the sense `current_affairs` defines — it was true
the moment it happened and does not go wrong later. The Twelfth Plan was India's last; the
Planning Commission was replaced by NITI Aayog in 2015 and no Thirteenth Plan exists, so this
table does not need an annual update the way a "current" table does.

🔴 REVIEWED = False. Every row is HAND-WRITTEN, including the Hindi, and this repo measures
hand-written data at about 1 error in 27. Read `drop/bssc/ECONOMY_REVIEW.md`, tick each row, then
flip the flag AND restore this file's concepts to SYLLABUS_MAP.json — both edits, one commit.
"""
import io

REVIEWED = False
REVIEWED_BY = ""          # name the person, and the date, when this is flipped

# ---- पंचवर्षीय योजना: plan -> its period ---------------------------------------------
# The three PLAN HOLIDAY years (1966-69) and the gap between the Seventh and Eighth plans
# (1990-92) are why the periods are not a clean arithmetic run, and they are themselves a
# commonly asked fact. Written as an en dash with no spaces, matching how the paper prints a year
# range elsewhere.
PLAN_PERIOD = {
    "First Five-Year Plan": "1951–56",
    "Second Five-Year Plan": "1956–61",
    "Third Five-Year Plan": "1961–66",
    "Fourth Five-Year Plan": "1969–74",
    "Fifth Five-Year Plan": "1974–79",
    "Sixth Five-Year Plan": "1980–85",
    "Seventh Five-Year Plan": "1985–90",
    "Eighth Five-Year Plan": "1992–97",
    "Ninth Five-Year Plan": "1997–2002",
    "Tenth Five-Year Plan": "2002–07",
    "Eleventh Five-Year Plan": "2007–12",
    "Twelfth Five-Year Plan": "2012–17",
}

# ---- आर्थिक संस्थाएँ और घटनाएँ: body or landmark event -> year ------------------------
# Bodies and events share one table on purpose: a distractor is only useful if it is the same KIND
# of thing as the answer, and here the kind is "a year in Indian economic history". Splitting them
# would leave two tables too small to draw four options from.
#
# Deliberately excluded: anything whose date is given differently depending on whether you mean
# the Act, the notification or the first operation. SEBI is the reason — it existed from 1988 and
# became statutory in 1992, so the row below says which one it means in the key itself.
ECON_EVENT_YEAR = {
    "establishment of the Reserve Bank of India": "1935",
    "setting up of the Planning Commission": "1950",
    "nationalisation of the State Bank of India": "1955",
    "establishment of the Life Insurance Corporation of India": "1956",
    "nationalisation of fourteen major commercial banks": "1969",
    "establishment of NABARD": "1982",
    "grant of statutory powers to SEBI": "1992",
    "launch of economic liberalisation in India": "1991",
    "replacement of the Planning Commission by NITI Aayog": "2015",
    "coming into force of the Goods and Services Tax": "2017",
}

_ALL = {"PLAN_PERIOD": PLAN_PERIOD, "ECON_EVENT_YEAR": ECON_EVENT_YEAR}

# ---- Hindi ---------------------------------------------------------------------------
# Hand-written, next to the facts, so ONE review sheet covers both — a reviewer ticking
# "First Five-Year Plan -> 1951–56" is also ticking "प्रथम पंचवर्षीय योजना". Registered into
# staticgk_hi by gs_tables() only when REVIEWED is True.
#
# The VALUES need Hindi too, not just the keys: _false_value skips any value it cannot render,
# so a year without an entry here silently shrinks the distractor pool instead of failing.
HI = {
    "First Five-Year Plan": "प्रथम पंचवर्षीय योजना",
    "Second Five-Year Plan": "द्वितीय पंचवर्षीय योजना",
    "Third Five-Year Plan": "तृतीय पंचवर्षीय योजना",
    "Fourth Five-Year Plan": "चतुर्थ पंचवर्षीय योजना",
    "Fifth Five-Year Plan": "पंचम पंचवर्षीय योजना",
    "Sixth Five-Year Plan": "षष्ठ पंचवर्षीय योजना",
    "Seventh Five-Year Plan": "सप्तम पंचवर्षीय योजना",
    "Eighth Five-Year Plan": "अष्टम पंचवर्षीय योजना",
    "Ninth Five-Year Plan": "नवम पंचवर्षीय योजना",
    "Tenth Five-Year Plan": "दशम पंचवर्षीय योजना",
    "Eleventh Five-Year Plan": "ग्यारहवीं पंचवर्षीय योजना",
    "Twelfth Five-Year Plan": "बारहवीं पंचवर्षीय योजना",
    "1951–56": "1951–56", "1956–61": "1956–61", "1961–66": "1961–66",
    "1969–74": "1969–74", "1974–79": "1974–79", "1980–85": "1980–85",
    "1985–90": "1985–90", "1992–97": "1992–97", "1997–2002": "1997–2002",
    "2002–07": "2002–07", "2007–12": "2007–12", "2012–17": "2012–17",
    "establishment of the Reserve Bank of India": "भारतीय रिज़र्व बैंक की स्थापना",
    "setting up of the Planning Commission": "योजना आयोग का गठन",
    "nationalisation of the State Bank of India": "भारतीय स्टेट बैंक का राष्ट्रीयकरण",
    "establishment of the Life Insurance Corporation of India":
        "भारतीय जीवन बीमा निगम की स्थापना",
    "nationalisation of fourteen major commercial banks":
        "चौदह प्रमुख वाणिज्यिक बैंकों का राष्ट्रीयकरण",
    "establishment of NABARD": "नाबार्ड की स्थापना",
    "grant of statutory powers to SEBI": "सेबी को वैधानिक शक्तियाँ मिलना",
    "launch of economic liberalisation in India": "भारत में आर्थिक उदारीकरण की शुरुआत",
    "replacement of the Planning Commission by NITI Aayog":
        "योजना आयोग के स्थान पर नीति आयोग की स्थापना",
    "coming into force of the Goods and Services Tax": "वस्तु एवं सेवा कर का लागू होना",
    "1935": "1935", "1950": "1950", "1955": "1955", "1956": "1956", "1969": "1969",
    "1982": "1982", "1991": "1991", "1992": "1992", "2015": "2015", "2017": "2017",
}


def hindi_gaps():
    """Every key and value with no hand-written Hindi. Must be empty before the flag is flipped."""
    return sorted({t for tbl in _ALL.values() for pair in tbl.items() for t in pair}
                  - set(HI))


def self_check():
    """The structural properties the question forms depend on — see staticgk_forms.shape_report."""
    from .staticgk_forms import shape_report
    return shape_report(_ALL, HI)


def write_review_sheet(path="drop/bssc/ECONOMY_REVIEW.md", corpus_path="/tmp/econcorpus/CORPUS.txt"):
    """Every row beside the source sentences that bear on it, for a HUMAN to sign off.

    Same standard as history_tables: the evidence is an aid to the reviewer, NOT a verdict. Two
    automated verifiers were written for that file and both were measured worthless — one
    confirmed "Dandi March -> 1935" — so nothing here is passed by a machine.
    """
    from .history_tables import evidence
    lines = ["# Economy & Five-Year Plans — fact review sheet", "",
             "Each row is a fact this generator would put on a student's paper, with the source",
             "sentences that bear on it, and its Hindi. **Tick each row or correct it.**", "",
             "The evidence is an AID, not a verdict — it is shown so the check takes ten minutes",
             "instead of an afternoon. A row with no supporting sentence is not wrong; it means",
             "the corpus does not phrase it that way, and it needs YOUR eye more, not less.", "",
             "⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:", "",
             "1. `REVIEWED = True` in `qbank/economy_tables.py`",
             "2. add to `concepts` for **Economy & Five-Year Plans** in `drop/bssc/SYLLABUS_MAP.json`:",
             "",
             '   `["PLAN_PERIOD", "ECON_EVENT_YEAR"]`', "",
             "A topic with `concepts` counts as GENERATABLE, so listing them before the flag is",
             "set promises questions the gate then refuses, and the section pads from elsewhere.", ""]
    n = 0
    for tname, table in _ALL.items():
        lines += [f"## {tname}", ""]
        for k, v in table.items():
            n += 1
            lines.append(f"- [ ] **{k}** → **{v}**")
            lines.append(f"      हिन्दी: {HI.get(k, '⚠️ MISSING')} → {HI.get(v, '⚠️ MISSING')}")
            ev = evidence(k, v, corpus_path, require_value=True)
            for e in ev:
                lines.append(f"      > {e[:300]}")
            if not ev:
                lines.append("      > ⚠️ NO SUPPORTING SENTENCE IN THE CORPUS — check this one "
                             "especially carefully.")
            lines.append("")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} rows -> {path}")
    return n


if __name__ == "__main__":
    self_check()
