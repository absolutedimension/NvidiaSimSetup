"""Bihar facts — the single biggest content hole on a paper sold to a Patna institute.

Measured on the delivered paper: **3 of 150 questions touched Bihar, and all three were "Patna is
the capital of which state?"** The real BSSC papers run ~11% Bihar-specific (skill §6), the
advertisement's own syllabus says "बिहार, भारत एवं उसके पड़ोसी देशों पर विशेष बल" and names
"राष्ट्रीय आन्दोलन में बिहार का योगदान" as its own topic, and the institute's owner put it plainly:
*"Ye BSSC ka paper hai — Bihar kahan hai?"*

🔴 **REVIEWED = True, and the paper builder honours it.** Every row below is HAND-WRITTEN, and the
measured error rate on hand-written data in this repo is about 1 in 27. That is tolerable for a
capital city and intolerable here: these are the questions a Patna coaching owner will check
FIRST, because they are the ones he teaches every day. One wrong district and the paper is dead.

The gate is a human one for the same reason history's is: no machine-readable oracle exists for
"which district is Vikramshila in". Two automated verifiers were written for the history table and
BOTH were measured worse than useless — one confirmed three sabotaged rows, the other rejected
thirteen correct ones. Do not write a third. Read `drop/bssc/BIHAR_REVIEW.md`, tick each row, then
set the flag and record who reviewed it.

Chosen for what BSSC actually asks and for what STAYS TRUE — no current office-holders, no
figures that change with an election, nothing that needs updating between one paper and the next.
"""
import io
import re

REVIEWED = False
REVIEWED_BY = ""          # fill in when the flag is flipped

# ── historical / archaeological sites → the district they stand in ──────────────────────────────
BIHAR_SITE_DISTRICT = {
    "Nalanda University ruins": "Nalanda",
    "Mahabodhi Temple": "Gaya",
    "Vikramshila University ruins": "Bhagalpur",
    "Rajgir": "Nalanda",
    "Pawapuri": "Nalanda",
    "Kesaria Stupa": "East Champaran",
    "Tomb of Sher Shah Suri": "Rohtas",
    "Barabar Caves": "Jehanabad",
    "Vishnupad Temple": "Gaya",
    "Golghar": "Patna",
    "Lauriya Nandangarh Ashokan Pillar": "West Champaran",
    "Ashoka Pillar at Vaishali": "Vaishali",
}

# ── GI-tagged products → the district they are registered to ────────────────────────────────────
# A BSSC favourite, and stable: a GI registration does not change year to year.
BIHAR_GI_PRODUCT = {
    "Shahi Litchi": "Muzaffarpur",
    "Katarni Rice": "Bhagalpur",
    "Jardalu Mango": "Bhagalpur",
    "Bhagalpuri Tussar Silk": "Bhagalpur",
    "Silao Khaja": "Nalanda",
    "Mithila Painting": "Madhubani",
}

# ── the national movement in Bihar → what each person is known for ──────────────────────────────
# A DASH, not a copula, exactly as history_tables.BIHAR_FREEDOM does it: "{k} {v} थे।" needs the
# verb to agree with the value's gender and number, and this table holds people and events alike.
# Every value is a NOUN PHRASE. Written as verb phrases first ("led the 1857 revolt...") they read
# fine after the dash of a statement template and broke the moment a completion template used them:
# "Kunwar Singh was known as led the 1857 revolt in Bihar" went straight onto a rendered page.
# One value shape that every template can consume beats a template per value shape.
BIHAR_FREEDOM_ROLE = {
    "Kunwar Singh": "the leader of the 1857 revolt in Bihar at Jagdishpur",
    "Rajkumar Shukla": "the man who brought Mahatma Gandhi to Champaran in 1917",
    "Dr. Rajendra Prasad": "the first President of India, born at Zeradei in Siwan",
    "Swami Sahajanand Saraswati": "the leader of the Kisan Sabha peasant movement",
    "Jayaprakash Narayan": "the leader of the Sampoorna Kranti movement of 1974",
    "Sri Krishna Sinha": "the first Chief Minister of Bihar",
    "Anugrah Narayan Sinha": "the first Deputy Chief Minister of Bihar",
    "Bhikhari Thakur": "the Bhojpuri playwright who created Bidesia",
}

# ── folk art forms → the region of Bihar they belong to ─────────────────────────────────────────
BIHAR_FOLK_REGION = {
    "Jat-Jatin": "Mithila",
    "Jhijhiya": "Mithila",
    "Bidesia": "Bhojpur",
    "Domkach": "Magadh",
    "Paika": "Magadh",
}

_TABLES = {"BIHAR_SITE_DISTRICT": BIHAR_SITE_DISTRICT,
           "BIHAR_GI_PRODUCT": BIHAR_GI_PRODUCT,
           "BIHAR_FREEDOM_ROLE": BIHAR_FREEDOM_ROLE,
           "BIHAR_FOLK_REGION": BIHAR_FOLK_REGION}

# ── Hindi, hand-written, reviewed in the same sheet as the facts ────────────────────────────────
HI = {
    # districts and regions
    "Nalanda": "नालंदा", "Gaya": "गया", "Bhagalpur": "भागलपुर", "Patna": "पटना",
    "Rohtas": "रोहतास", "Jehanabad": "जहानाबाद", "Vaishali": "वैशाली",
    "Muzaffarpur": "मुजफ्फरपुर", "Madhubani": "मधुबनी",
    "East Champaran": "पूर्वी चंपारण", "West Champaran": "पश्चिमी चंपारण",
    "Mithila": "मिथिला", "Bhojpur": "भोजपुर", "Magadh": "मगध",
    # sites
    "Nalanda University ruins": "नालंदा विश्वविद्यालय के अवशेष",
    "Mahabodhi Temple": "महाबोधि मंदिर",
    "Vikramshila University ruins": "विक्रमशिला विश्वविद्यालय के अवशेष",
    "Rajgir": "राजगीर", "Pawapuri": "पावापुरी", "Kesaria Stupa": "केसरिया स्तूप",
    "Tomb of Sher Shah Suri": "शेरशाह सूरी का मकबरा", "Barabar Caves": "बराबर की गुफाएँ",
    "Vishnupad Temple": "विष्णुपद मंदिर", "Golghar": "गोलघर",
    "Lauriya Nandangarh Ashokan Pillar": "लौरिया नंदनगढ़ का अशोक स्तंभ",
    "Ashoka Pillar at Vaishali": "वैशाली का अशोक स्तंभ",
    # GI products
    "Shahi Litchi": "शाही लीची", "Katarni Rice": "कतरनी चावल",
    "Jardalu Mango": "जर्दालु आम", "Bhagalpuri Tussar Silk": "भागलपुरी तसर रेशम",
    "Silao Khaja": "सिलाव खाजा", "Mithila Painting": "मिथिला चित्रकला",
    # people
    "Kunwar Singh": "कुंवर सिंह", "Rajkumar Shukla": "राजकुमार शुक्ल",
    "Dr. Rajendra Prasad": "डॉ. राजेंद्र प्रसाद",
    "Swami Sahajanand Saraswati": "स्वामी सहजानंद सरस्वती",
    "Jayaprakash Narayan": "जयप्रकाश नारायण", "Sri Krishna Sinha": "श्रीकृष्ण सिंह",
    "Anugrah Narayan Sinha": "अनुग्रह नारायण सिंह", "Bhikhari Thakur": "भिखारी ठाकुर",
    # roles — written as noun phrases so a dash template needs no verb agreement
    "the leader of the 1857 revolt in Bihar at Jagdishpur":
        "जगदीशपुर में 1857 के विद्रोह के नेता",
    "the man who brought Mahatma Gandhi to Champaran in 1917":
        "1917 में महात्मा गांधी को चंपारण लाने वाले",
    "the first President of India, born at Zeradei in Siwan":
        "भारत के प्रथम राष्ट्रपति, जन्म सिवान के जीरादेई में",
    "the leader of the Kisan Sabha peasant movement": "किसान सभा आंदोलन के नेता",
    "the leader of the Sampoorna Kranti movement of 1974": "1974 के सम्पूर्ण क्रांति आंदोलन के नेता",
    "the first Chief Minister of Bihar": "बिहार के प्रथम मुख्यमंत्री",
    "the first Deputy Chief Minister of Bihar": "बिहार के प्रथम उप-मुख्यमंत्री",
    "the Bhojpuri playwright who created Bidesia": "बिदेसिया के रचयिता भोजपुरी नाटककार",
    # folk forms
    "Jat-Jatin": "जट-जटिन", "Jhijhiya": "झिझिया", "Bidesia": "बिदेसिया",
    "Domkach": "डोमकच", "Paika": "पाइका",
}


def review_sheet(path="drop/bssc/BIHAR_REVIEW.md"):
    """Every Bihar row, with its Hindi, for a person to tick before any of it reaches a student.

    No supporting-sentence column, unlike the history sheet. There is no corpus for "which district
    is Barabar Caves in" that would not be a guess dressed as evidence, and a weak evidence column
    is worse than none — it invites the reviewer to trust it. This sheet asks a person who knows
    Bihar to read forty rows, which takes ten minutes and is the actual gate.
    """
    lines = ["# Bihar facts — review sheet", "",
             "**Every fact and every Hindi rendering below is HAND-WRITTEN.** Measured error rate",
             "on hand-written data in this repo is about 1 in 27, and these are the rows a Patna",
             "institute owner checks first. Tick or correct each one.", "",
             "Nothing here reaches a paper until `REVIEWED = True` in `qbank/bihar_tables.py`,",
             "and `REVIEWED_BY` records who signed it off.", "",
             "⚠️ **TWO edits, made at the same moment** — the flag alone is not enough:", "",
             "1. `REVIEWED = True` in `qbank/bihar_tables.py`", 
             "2. add these to `concepts` for **Bihar in the national movement** in",
             "   `drop/bssc/SYLLABUS_MAP.json`:", "",
             "   `[\"BIHAR_SITE_DISTRICT\", \"BIHAR_GI_PRODUCT\", \"BIHAR_FREEDOM_ROLE\", "
             "\"BIHAR_FOLK_REGION\"]`", "",
             "A topic with `concepts` counts as GENERATABLE, so listing them before the flag is",
             "set promises questions the gate then refuses, and the section pads from elsewhere.",
             "Verified once with both flipped: the paper builds ALL CHECKS PASSED, 150 of 150",
             "re-solved, and Bihar reaches 7 of its 8-question quota.", ""]
    n = 0
    for name, table in _TABLES.items():
        lines += [f"## {name}", ""]
        for k, v in table.items():
            n += 1
            lines.append(f"- [ ] **{k}** → **{v}**")
            lines.append(f"      हिंदी: {HI.get(k, '⚠️ MISSING')} → {HI.get(v, '⚠️ MISSING')}")
        lines.append("")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} Bihar rows -> {path}")
    return n


def missing_hindi():
    """Rows whose key or value has no Hindi — these can never be drawn on a bilingual paper."""
    out = []
    for name, table in _TABLES.items():
        for k, v in table.items():
            if k not in HI or v not in HI:
                out.append((name, k, v, "key" if k not in HI else "value"))
    return out
