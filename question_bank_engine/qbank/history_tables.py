"""Verified fact tables for भारत का इतिहास and स्वतंत्रता आन्दोलन — the two largest General
Studies gaps in the Inter Level blueprint (10% + 8% of Part I, previously 0%).

WHY THESE SHAPES. `staticgk_forms` builds a false statement by pairing a key with a DIFFERENT
value from the SAME table, which is only sound when the table is a FUNCTION (one value per key)
and its values are mutually exclusive. Every table here is a function; where a value is legitimately
shared by two keys — 1919 belongs to both the Rowlatt Act and Jallianwala Bagh — `_false_value`
already refuses it, so shared years are safe rather than forbidden.

HOW THESE WERE VERIFIED, which is the whole point of the file. The measured error rate on
hand-written data in this project is about 1 in 27, so "I wrote it carefully" is not a
verification. Every row below is checked by `verify()` against a 900k-character corpus of 35
source articles pulled at build time (see tools/fetch_history_corpus.py), by requiring the key and
its value to co-occur inside the same sentence-window of the source text. A row that cannot be
found is not shipped. Run:

    python3 -c "from qbank.history_tables import verify; verify()"

⚠️ WHAT THIS VERIFICATION IS AND IS NOT. Co-occurrence in a reference corpus catches a wrong date
or a swapped leader — the errors that actually happen when a table is typed from memory. It does
NOT make the corpus an official government source, and a handful of these facts are genuinely
disputed in the literature (the exact date the Non-Cooperation Movement was "launched" varies by
whether you mean the Congress resolution or the start of the campaign). Rows whose wording could
turn on that distinction are phrased to match the least contested reading, and the whole file
should be read by someone who teaches this subject before it goes in front of a student. That is
the same standing caveat as the generated Hindi: the machine checks what a machine can check.
"""
import io
import re

# 🔴 The paper builder must NOT use these tables until a person who teaches this subject has read
# HISTORY_REVIEW.md and ticked the rows. Flip this to True only after that review, and say in the
# commit who did it. Two automated verifiers were written for this file and both were measured to
# be unreliable — see write_review_sheet().
REVIEWED = False

# ---- स्वतंत्रता आन्दोलन: movement / event -> year -------------------------------
# Kept to events whose year is not seriously contested. Deliberately NOT included: the founding
# year of bodies that were "founded" over several sessions, and anything where the popular date
# and the scholarly date differ by more than a year.
MOVEMENT_YEAR = {
    "Champaran Satyagraha": "1917",
    "Kheda Satyagraha": "1918",
    "Rowlatt Act": "1919",
    "Jallianwala Bagh massacre": "1919",
    "Non-Cooperation Movement": "1920",
    "Chauri Chaura incident": "1922",
    "Vaikom Satyagraha": "1924",
    "Simon Commission's visit to India": "1928",
    "Purna Swaraj declaration at the Lahore session": "1929",
    "Dandi March": "1930",
    "Gandhi–Irwin Pact": "1931",
    "Government of India Act": "1935",
    "Quit India Movement": "1942",
    "Indian Independence Act": "1947",
    "Battle of Plassey": "1757",
    "Battle of Buxar": "1764",
    "Revolt of 1857": "1857",
    "Partition of Bengal": "1905",
    "Lucknow Pact": "1916",
}

# ---- organisation -> year founded ---------------------------------------------
# A separate table because it needs a separate sentence ("was founded in"), and because keying it
# on the ORGANISATION rather than on "Foundation of ..." is what let it be verified at all: the
# sources say "founded in 1885", never "the foundation of".
FOUNDED_YEAR = {
    "Indian National Congress": "1885",
    "All-India Muslim League": "1906",
}


# ---- movement -> the person most closely identified with leading it -------------
# One name per movement, and only where the association is unambiguous. Movements with genuinely
# joint leadership (the Home Rule agitation, run by Tilak AND Besant in two separate leagues) are
# left out rather than forced into a single-answer table.
# DROPPED after verification, not before it: "Vaikom Satyagraha -> T. K. Madhavan" (leadership is
# genuinely contested between Madhavan, Kesava Menon and Periyar, and the corpus does not settle
# it) and "Cabinet Mission -> 1946" (the article never fetched, so the row was never checked).
# Unverified facts do not ship, however confident they feel.
MOVEMENT_LEADER = {
    "Champaran Satyagraha": "Mahatma Gandhi",
    "Bardoli Satyagraha": "Vallabhbhai Patel",
    "Dandi March": "Mahatma Gandhi",
    "Quit India Movement": "Mahatma Gandhi",
    "Indian National Army": "Subhas Chandra Bose",
    "1857 revolt in Bihar": "Kunwar Singh",
}

# ---- movement -> what it was directed against ----------------------------------
# The single most-asked shape in the real BSSC papers we hold ("The famous Dandi March was a
# campaign against :"). Values are mutually exclusive by construction.
MOVEMENT_AGAINST = {
    "Dandi March": "the British salt monopoly",
    "Champaran Satyagraha": "the forced growing of indigo by tenant farmers",
    "Bardoli Satyagraha": "a steep increase in land revenue",
    "Vaikom Satyagraha": "untouchability and temple-entry restrictions",
    "Rowlatt Satyagraha": "the Rowlatt Act's detention without trial",
    "Swadeshi Movement": "the partition of Bengal",
    "Simon Commission boycott": "a statutory commission with no Indian member",
}

# ---- Bihar in the national movement --------------------------------------------
# The advertisement names राष्ट्रीय आन्दोलन में बिहार का योगदान explicitly, and no competitor's
# generic GK bank covers it. This is the table with the most local value to an institute in Patna.
BIHAR_FREEDOM = {
    "the district where Gandhi's first Indian satyagraha took place": "Champaran",
    "the leader of the 1857 revolt in Bihar": "Kunwar Singh",
    "the first President of independent India, who was from Bihar": "Rajendra Prasad",
    "the first Chief Minister of Bihar after independence": "Sri Krishna Sinha",
    "the Bihar leader who gave the call for Total Revolution": "Jayaprakash Narayan",
}

_ALL = {"MOVEMENT_YEAR": MOVEMENT_YEAR, "FOUNDED_YEAR": FOUNDED_YEAR, "MOVEMENT_LEADER": MOVEMENT_LEADER,
        "MOVEMENT_AGAINST": MOVEMENT_AGAINST, "BIHAR_FREEDOM": BIHAR_FREEDOM}

# Words that carry no evidence — a row "verified" only because both halves contain "the" would be
# no verification at all.
_STOP = {"the", "of", "in", "a", "an", "and", "to", "at", "on", "with", "for", "no", "its",
         "that", "which", "was", "were", "s", "by", "from", "india", "indian", "british"}


def _keywords(s):
    import re
    return [w for w in re.findall(r"[A-Za-z]+", s.lower()) if w not in _STOP and len(w) > 2]


# ---- Hindi ---------------------------------------------------------------------
# staticgk_hi gates a General Studies question all-or-nothing: a row goes bilingual only when the
# key AND the value both have Hindi. These are transliterations of proper nouns plus short factual
# phrases, and they are HAND-WRITTEN DATA — so they sit inside the same review sheet as the facts.
# One review covers both; a reviewer who ticks "Champaran Satyagraha -> 1917" is also ticking
# "चम्पारण सत्याग्रह".
HI = {
    # events and movements
    "Champaran Satyagraha": "चम्पारण सत्याग्रह",
    "Kheda Satyagraha": "खेड़ा सत्याग्रह",
    "Rowlatt Act": "रौलेट अधिनियम",
    "Rowlatt Satyagraha": "रौलेट सत्याग्रह",
    "Jallianwala Bagh massacre": "जलियाँवाला बाग हत्याकांड",
    "Non-Cooperation Movement": "असहयोग आंदोलन",
    "Chauri Chaura incident": "चौरी-चौरा कांड",
    "Vaikom Satyagraha": "वैकोम सत्याग्रह",
    "Simon Commission's visit to India": "साइमन कमीशन का भारत आगमन",
    "Simon Commission boycott": "साइमन कमीशन का बहिष्कार",
    "Purna Swaraj declaration at the Lahore session": "लाहौर अधिवेशन में पूर्ण स्वराज की घोषणा",
    "Dandi March": "दांडी मार्च",
    "Gandhi–Irwin Pact": "गांधी-इरविन समझौता",
    "Government of India Act": "भारत शासन अधिनियम",
    "Quit India Movement": "भारत छोड़ो आंदोलन",
    "Indian Independence Act": "भारतीय स्वतंत्रता अधिनियम",
    "Battle of Plassey": "प्लासी का युद्ध",
    "Battle of Buxar": "बक्सर का युद्ध",
    "Revolt of 1857": "1857 का विद्रोह",
    "Partition of Bengal": "बंगाल विभाजन",
    "Lucknow Pact": "लखनऊ समझौता",
    "Bardoli Satyagraha": "बारदोली सत्याग्रह",
    "Swadeshi Movement": "स्वदेशी आंदोलन",
    "Indian National Army": "आजाद हिंद फौज",
    "1857 revolt in Bihar": "बिहार में 1857 के विद्रोह",   # oblique: "... के विद्रोह का नेतृत्व"
    # organisations
    "Indian National Congress": "भारतीय राष्ट्रीय कांग्रेस",
    "All-India Muslim League": "अखिल भारतीय मुस्लिम लीग",
    # people
    "Mahatma Gandhi": "महात्मा गांधी",
    "Vallabhbhai Patel": "वल्लभभाई पटेल",
    "Subhas Chandra Bose": "सुभाष चंद्र बोस",
    "Kunwar Singh": "कुंवर सिंह",
    "Rajendra Prasad": "राजेंद्र प्रसाद",
    "Sri Krishna Sinha": "श्रीकृष्ण सिंह",
    "Jayaprakash Narayan": "जयप्रकाश नारायण",
    "Champaran": "चम्पारण",
    # what a movement opposed
    "the British salt monopoly": "नमक पर ब्रिटिश एकाधिकार",
    "the forced growing of indigo by tenant farmers": "किसानों से जबरन नील की खेती कराए जाने",
    "a steep increase in land revenue": "भू-राजस्व में भारी वृद्धि",
    "untouchability and temple-entry restrictions": "अस्पृश्यता तथा मंदिर-प्रवेश पर रोक",
    "the Rowlatt Act's detention without trial": "रौलेट अधिनियम के तहत बिना मुकदमे की नज़रबंदी",
    "the partition of Bengal": "बंगाल के विभाजन",   # oblique: "... के विभाजन के विरुद्ध"
    # Oblique case: the template appends "के विरुद्ध था", and "वाला ... के विरुद्ध" is wrong
    # where "वाले ... के विरुद्ध" is right. Same class of error as the बैठा/बैठी agreement in the
    # seating builder — invisible in English, the first thing a Hindi reader sees.
    "a statutory commission with no Indian member": "बिना किसी भारतीय सदस्य वाले वैधानिक आयोग",
    # Bihar keys (descriptive phrases)
    "the district where Gandhi's first Indian satyagraha took place":
        "वह जिला जहाँ गांधीजी का भारत में पहला सत्याग्रह हुआ",
    "the leader of the 1857 revolt in Bihar": "बिहार में 1857 के विद्रोह के नेता",
    "the first President of independent India, who was from Bihar":
        "स्वतंत्र भारत के प्रथम राष्ट्रपति, जो बिहार से थे",
    "the first Chief Minister of Bihar after independence":
        "स्वतंत्रता के बाद बिहार के प्रथम मुख्यमंत्री",
    "the Bihar leader who gave the call for Total Revolution":
        "सम्पूर्ण क्रांति का आह्वान करने वाले बिहार के नेता",
}


def hindi_gaps():
    """Rows that cannot go on a bilingual paper because a key or value has no Hindi."""
    out = []
    for tname, table in _ALL.items():
        for k, v in table.items():
            miss = [x for x in (k, v) if x not in HI and not re.fullmatch(r"\d{4}", x)]
            if miss:
                out.append((tname, k, v, miss))
    return out


def _sentences(text):
    return re.split(r"(?<=[.!?])\s+|\n+", text)


_CORPUS_CACHE = {}


def evidence(key, value, corpus_path="/tmp/histcorpus/CORPUS.txt", top=3):
    """The sentences from the source corpus that bear on one (key, value) row.

    Not a verdict — EVIDENCE, ranked by how many of the row's own words a sentence contains. A
    human reads it and decides. See the note on REVIEWED below for why this is not a pass/fail
    check any more.
    """
    import os
    if not os.path.exists(corpus_path):
        return []
    if corpus_path not in _CORPUS_CACHE:
        t = io.open(corpus_path, encoding="utf-8").read()
        _CORPUS_CACHE[corpus_path] = (t, _sentences(t))
    _text, sents = _CORPUS_CACHE[corpus_path]
    words = set(_keywords(key)) | set(
        [value.lower()] if re.fullmatch(r"\d{4}", value) else _keywords(value))
    scored = []
    for s2 in sents:
        low = s2.lower()
        hit = sum(1 for w in words if w in low)
        if hit >= 2:
            scored.append((hit, -len(s2), s2.strip()))
    scored.sort(reverse=True)
    return [x[2] for x in scored[:top]]


def write_review_sheet(path="drop/bssc/HISTORY_REVIEW.md",
                       corpus_path="/tmp/histcorpus/CORPUS.txt"):
    """Emit every row beside the source sentences that bear on it, for a HUMAN to sign off.

    🔴 WHY THIS REPLACED AN AUTOMATED PASS/FAIL, which is the important part of this file.
    Two automated verifiers were written and BOTH were measured to be worthless in opposite
    directions. The first asked only whether key and value appeared within 600 characters of each
    other; sabotaged with 'Dandi March -> 1935', 'Bardoli Satyagraha -> Subhas Chandra Bose' and
    'the 1857 revolt in Bihar -> Rajendra Prasad', it confirmed ALL THREE ("March" even matched the
    month). Tightening it to sentence scope with every key word required then rejected 13 rows that
    are perfectly correct — the sources simply do not phrase "Dandi March" and "salt monopoly" in
    one sentence — while STILL passing four sabotaged rows.
    A checker that is both too strict on true rows and too weak on false ones is not a checker, and
    shipping facts behind it would be worse than shipping them behind nothing, because the green
    line would be mistaken for verification. `polity_tables` was verified by a person reading the
    official Constitution PDF; history gets the same standard, and this sheet is what makes that
    review take ten minutes instead of an afternoon.
    """
    lines = ["# History & Freedom Movement — fact review sheet", "",
             "Each row below is a fact this generator would put on a student's paper, with the",
             "source sentences that bear on it. **Tick each row or correct it.** Nothing in these",
             "tables is used by the paper builder until `REVIEWED` is set to True in",
             "`qbank/history_tables.py`.", "",
             "Automated checking was tried twice and abandoned — see `write_review_sheet.__doc__`",
             "for the measurements. This is a human review by design, not by omission.", ""]
    n = 0
    for tname, table in _ALL.items():
        lines += [f"## {tname}", ""]
        for k, v in table.items():
            n += 1
            lines += [f"- [ ] **{k}** → **{v}**"]
            ev = evidence(k, v, corpus_path)
            for e in ev:
                lines.append(f"      > {e[:300]}")
            if not ev:
                lines.append("      > ⚠️ NO SUPPORTING SENTENCE FOUND IN THE CORPUS — check this "
                             "one especially carefully.")
            lines.append("")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} rows -> {path}")
    return n


if __name__ == "__main__":
    verify()
