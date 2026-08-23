"""Verified fact tables for खेल-खिलाड़ी — 5% of Part I, previously 0%.

WHAT IS NOT HERE: who won anything. A winners table is the single most-asked sports shape and the
single worst fit for this bank — every row expires, and `current_affairs` already exists for facts
with a shelf life, with a date column and a staleness check this file has neither of. Winners
belong there, supplied and dated by the institute. What is left when the expiring half is removed
is still the half the commission asks most: which sport a trophy belongs to, and where a ground
is.

A STRUCTURAL CAVEAT, stated because it is easy to miss. `_false_value` will only use a value
owned by exactly ONE key, so a table whose values repeat is weaker than its row count suggests.
TROPHY_SPORT is that shape by nature — several trophies per sport is what the real world looks
like — and it is written with as few repeats as possible for that reason: two cricket, two
football, one each of the rest. `shape_report` prints the usable count so the thinness is visible
rather than assumed. Excluded on purpose for the same reason: Uber Cup (a second badminton),
Rangaswami Cup (a second hockey), Corbillon Cup (a second table tennis) — each would have cost a
usable distractor without adding a askable row.

🔴 REVIEWED = False. Hand-written, Hindi included, ~1 error in 27 measured on hand data here.
Read `drop/bssc/SPORTS_REVIEW.md`, tick each row, then flip the flag AND restore this file's
concepts to SYLLABUS_MAP.json — both edits, one commit.
"""
import io

REVIEWED = False
REVIEWED_BY = ""          # name the person, and the date, when this is flipped

# ---- ट्रॉफी / कप -> खेल ----------------------------------------------------------------
TROPHY_SPORT = {
    "Ranji Trophy": "Cricket",
    "Duleep Trophy": "Cricket",
    "Durand Cup": "Football",
    "Santosh Trophy": "Football",
    "Agha Khan Cup": "Hockey",
    "Thomas Cup": "Badminton",
    "Davis Cup": "Tennis",
    "Ryder Cup": "Golf",
    "Swaythling Cup": "Table Tennis",
    "Ezra Cup": "Polo",
}

# ---- स्टेडियम -> शहर -------------------------------------------------------------------
# Cities are distinct, so every value can serve as a false one — the strongest shape the topic
# allows. Moin-ul-Haq is in the table deliberately: the advertisement names Bihar as its own
# emphasis, and a Patna ground is the one sports fact a Patna student is certain to know.
# Arun Jaitley Stadium carries its former name in the key because papers of the last decade print
# both and a student needs to recognise either.
STADIUM_CITY = {
    "Eden Gardens": "Kolkata",
    "Wankhede Stadium": "Mumbai",
    "M. Chinnaswamy Stadium": "Bengaluru",
    "Arun Jaitley Stadium (formerly Feroz Shah Kotla)": "New Delhi",
    "Moin-ul-Haq Stadium": "Patna",
    "Green Park Stadium": "Kanpur",
    "M. A. Chidambaram Stadium": "Chennai",
    "Barabati Stadium": "Cuttack",
}

_ALL = {"TROPHY_SPORT": TROPHY_SPORT, "STADIUM_CITY": STADIUM_CITY}

HI = {
    "Ranji Trophy": "रणजी ट्रॉफी",
    "Duleep Trophy": "दलीप ट्रॉफी",
    "Durand Cup": "डूरंड कप",
    "Santosh Trophy": "संतोष ट्रॉफी",
    "Agha Khan Cup": "आगा खान कप",
    "Thomas Cup": "थॉमस कप",
    "Davis Cup": "डेविस कप",
    "Ryder Cup": "राइडर कप",
    "Swaythling Cup": "स्वेथलिंग कप",
    "Ezra Cup": "एज़रा कप",
    "Cricket": "क्रिकेट", "Football": "फुटबॉल", "Hockey": "हॉकी", "Badminton": "बैडमिंटन",
    "Tennis": "टेनिस", "Golf": "गोल्फ", "Table Tennis": "टेबल टेनिस", "Polo": "पोलो",
    "Eden Gardens": "ईडन गार्डन्स",
    "Wankhede Stadium": "वानखेड़े स्टेडियम",
    "M. Chinnaswamy Stadium": "एम. चिन्नास्वामी स्टेडियम",
    "Arun Jaitley Stadium (formerly Feroz Shah Kotla)":
        "अरुण जेटली स्टेडियम (पूर्व नाम फ़िरोज़शाह कोटला)",
    "Moin-ul-Haq Stadium": "मोइनुल हक़ स्टेडियम",
    "Green Park Stadium": "ग्रीन पार्क स्टेडियम",
    "M. A. Chidambaram Stadium": "एम. ए. चिदंबरम स्टेडियम",
    "Barabati Stadium": "बाराबाटी स्टेडियम",
    "Kolkata": "कोलकाता", "Mumbai": "मुंबई", "Bengaluru": "बेंगलुरु", "New Delhi": "नई दिल्ली",
    "Patna": "पटना", "Kanpur": "कानपुर", "Chennai": "चेन्नई", "Cuttack": "कटक",
}


def hindi_gaps():
    return sorted({t for tbl in _ALL.values() for pair in tbl.items() for t in pair} - set(HI))


def self_check():
    """The structural properties the question forms depend on — see staticgk_forms.shape_report."""
    from .staticgk_forms import shape_report
    return shape_report(_ALL, HI)


def write_review_sheet(path="drop/bssc/SPORTS_REVIEW.md",
                       corpus_path="/tmp/sportscorpus/CORPUS.txt"):
    from .history_tables import evidence
    lines = ["# Sports — fact review sheet", "",
             "Each row is a fact this generator would put on a student's paper, with the source",
             "sentences that bear on it, and its Hindi. **Tick each row or correct it.**", "",
             "The evidence is an AID, not a verdict. A row with no supporting sentence is not",
             "wrong — it means the corpus does not phrase it that way, and it needs YOUR eye more.",
             "", "Note what is NOT in this file: who won what. Those rows expire; they belong in",
             "`current_affairs`, dated, supplied by the institute.", "",
             "⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:", "",
             "1. `REVIEWED = True` in `qbank/sports_tables.py`",
             "2. add to `concepts` for **Sports** in `drop/bssc/SYLLABUS_MAP.json`:", "",
             '   `["TROPHY_SPORT", "STADIUM_CITY"]`', ""]
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
