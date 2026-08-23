"""Verified fact tables for भारतीय कृषि तथा प्राकृतिक संसाधन — 5% of Part I, previously 0%.

WHAT IS DELIBERATELY NOT HERE, and it is the table everyone reaches for first: **crop → largest
producing state.** It is asked constantly and it is exactly the kind of fact this bank must not
hold, because it is a LIVE STATE in the sense `current_affairs` defines rather than a settled one.
Leadership in rice and wheat moves between states from one Agricultural Statistics release to the
next, so a row that is right when written goes WRONG — not merely stale — and a paper that prints
it teaches a student the wrong answer for an exam they sit next month. The two tables below were
chosen instead because neither can move: a revolution's subject and an institute's city are
settled the moment they exist.

If One Step wants crop-leader questions, the honest way is the same one `current_affairs` uses —
the institute supplies the figures from the current release and dates them. Not this file.

🔴 REVIEWED = False. Every row is HAND-WRITTEN, Hindi included, at this repo's measured ~1-in-27
hand-data error rate. Read `drop/bssc/AGRICULTURE_REVIEW.md`, tick each row, then flip the flag
AND restore this file's concepts to SYLLABUS_MAP.json — both edits, one commit.
"""
import io

REVIEWED = False
REVIEWED_BY = ""          # name the person, and the date, when this is flipped

# ---- हरित क्रांति आदि: revolution -> what it relates to -------------------------------
# Only the colours whose subject is NOT contested. Excluded on purpose: Pink (prawn / onion /
# meat, depending on the source), Brown (leather / cocoa / non-conventional energy) and Red
# (meat / tomato). A key whose value differs between two textbooks cannot be used to build a
# FALSE statement either, because the "wrong" pairing may be some other book's right one.
REVOLUTION_PRODUCT = {
    "Green Revolution": "foodgrains",
    "White Revolution": "milk",
    "Blue Revolution": "fish",
    "Yellow Revolution": "oilseeds",
    "Golden Revolution": "horticulture and fruits",
    "Silver Revolution": "eggs and poultry",
    "Grey Revolution": "fertilisers",
    "Round Revolution": "potatoes",
}

# ---- कृषि अनुसंधान संस्थान: institute -> city ------------------------------------------
# Cities are distinct across the table, which is what makes this the strongest shape available
# for the topic: every value can serve as a false one. Institutes are named as the commission
# names them, in full, because the abbreviation and the expansion are asked as separate questions.
AGRI_INSTITUTE_CITY = {
    "Indian Agricultural Research Institute": "New Delhi",
    # Renamed the National Rice Research Institute in 2014; the corpus fetch is what surfaced
    # that, against a key written from the older name. Both are carried for the same reason the
    # stadium row carries Feroz Shah Kotla — papers of the last decade print either one.
    "National Rice Research Institute (formerly Central Rice Research Institute)": "Cuttack",
    "Indian Institute of Sugarcane Research": "Lucknow",
    "Central Potato Research Institute": "Shimla",
    "Indian Institute of Pulses Research": "Kanpur",
    "National Dairy Research Institute": "Karnal",
    "Indian Institute of Horticultural Research": "Bengaluru",
    "Central Institute of Fisheries Education": "Mumbai",
}

_ALL = {"REVOLUTION_PRODUCT": REVOLUTION_PRODUCT, "AGRI_INSTITUTE_CITY": AGRI_INSTITUTE_CITY}

HI = {
    "Green Revolution": "हरित क्रांति",
    "White Revolution": "श्वेत क्रांति",
    "Blue Revolution": "नीली क्रांति",
    "Yellow Revolution": "पीली क्रांति",
    "Golden Revolution": "स्वर्ण क्रांति",
    "Silver Revolution": "रजत क्रांति",
    "Grey Revolution": "धूसर क्रांति",
    "Round Revolution": "गोल क्रांति",
    "foodgrains": "खाद्यान्न",
    "milk": "दुग्ध",
    "fish": "मत्स्य",
    "oilseeds": "तिलहन",
    "horticulture and fruits": "बागवानी एवं फल",
    "eggs and poultry": "अंडा एवं कुक्कुट",
    "fertilisers": "उर्वरक",
    "potatoes": "आलू",
    "Indian Agricultural Research Institute": "भारतीय कृषि अनुसंधान संस्थान",
    "National Rice Research Institute (formerly Central Rice Research Institute)":
        "राष्ट्रीय चावल अनुसंधान संस्थान (पूर्व नाम केंद्रीय चावल अनुसंधान संस्थान)",
    "Indian Institute of Sugarcane Research": "भारतीय गन्ना अनुसंधान संस्थान",
    "Central Potato Research Institute": "केंद्रीय आलू अनुसंधान संस्थान",
    "Indian Institute of Pulses Research": "भारतीय दलहन अनुसंधान संस्थान",
    "National Dairy Research Institute": "राष्ट्रीय डेयरी अनुसंधान संस्थान",
    "Indian Institute of Horticultural Research": "भारतीय बागवानी अनुसंधान संस्थान",
    "Central Institute of Fisheries Education": "केंद्रीय मत्स्यिकी शिक्षा संस्थान",
    "New Delhi": "नई दिल्ली", "Cuttack": "कटक", "Lucknow": "लखनऊ", "Shimla": "शिमला",
    "Kanpur": "कानपुर", "Karnal": "करनाल", "Bengaluru": "बेंगलुरु", "Mumbai": "मुंबई",
}


def hindi_gaps():
    return sorted({t for tbl in _ALL.values() for pair in tbl.items() for t in pair} - set(HI))


def self_check():
    """The structural properties the question forms depend on — see staticgk_forms.shape_report."""
    from .staticgk_forms import shape_report
    return shape_report(_ALL, HI)


def write_review_sheet(path="drop/bssc/AGRICULTURE_REVIEW.md",
                       corpus_path="/tmp/agricorpus/CORPUS.txt"):
    from .history_tables import evidence
    lines = ["# Agriculture & natural resources — fact review sheet", "",
             "Each row is a fact this generator would put on a student's paper, with the source",
             "sentences that bear on it, and its Hindi. **Tick each row or correct it.**", "",
             "The evidence is an AID, not a verdict. A row with no supporting sentence is not",
             "wrong — it means the corpus does not phrase it that way, and it needs YOUR eye more.",
             "", "Note what is NOT in this file: crop → largest producing state. That fact moves",
             "between releases, so it belongs with the institute's own current figures, not here.",
             "", "⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:", "",
             "1. `REVIEWED = True` in `qbank/agri_tables.py`",
             "2. add to `concepts` for **Agriculture & natural resources** in "
             "`drop/bssc/SYLLABUS_MAP.json`:", "",
             '   `["REVOLUTION_PRODUCT", "AGRI_INSTITUTE_CITY"]`', ""]
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
                lines.append("      > \u26a0\ufe0f NO SUPPORTING SENTENCE IN THE CORPUS — check this one "
                             "especially carefully.")
            lines.append("")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} rows -> {path}")
    return n


if __name__ == "__main__":
    self_check()
