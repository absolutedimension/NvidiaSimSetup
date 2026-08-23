"""More of the Constitution — the seam we had already parsed and were not using.

`drop/bssc/CONSTITUTION_ARTICLES.json` holds **462 article headings parsed from the official
Constitution PDF**, and the question bank was using **31** of them. 431 sat unused.

That matters more than the raw number, because Articles are the ONE General Studies sub-topic that
reliably produces a HARD question. Measured across the live tables: Articles 31 of 31 hard,
Capitals 5 of 28, and Dance, Rivers and Amendments **zero**. Article numbers give numerically
adjacent distractors (343 against 352 / 356 / 360) and the headings share legal vocabulary, so
`gs_ask._tight` can actually discriminate. Nothing else in the GS bank does both.

So this is the cheapest available increase in HARD General Studies: same official source, already
extracted, no new pipeline. 66 articles selected from the 350 clean candidates, chosen for what
BSSC and BPSC actually ask.

Selection was filtered, not skimmed. Rejected automatically: 27 omitted/repealed articles, 20 with
truncated parses, 17 boilerplate ("Definitions", "Short title") and 17 too short to key. Headings
were also CLEANED — the parse runs consecutive headings together, so "Protection against arrest and
detention in certain cases.Right against Exploitation" had to be cut back to the article's own
heading before it could be asked.

🔴 **REVIEWED = False.** The English headings come from the official PDF and are as trustworthy as
that document. **The Hindi is hand-written** — 66 legal headings, in the terminology of the
official Hindi text, and that is exactly the kind of hand data this repo measures at ~1 error in 27.
Read `drop/bssc/POLITY_EXTRA_REVIEW.md`, tick each row, then set the flag.
"""
import io

REVIEWED = False
REVIEWED_BY = ""

# Merged into polity_tables.ARTICLE_SUBJECT when the gate opens, so every existing template,
# form and solver picks these up with NO new wiring — 31 articles becomes 89.
ARTICLE_SUBJECT_EXTRA = {
    "13": "Laws inconsistent with or in derogation of the fundamental rights",
    "20": "Protection in respect of conviction for offences",
    "22": "Protection against arrest and detention in certain cases",
    "26": "Freedom to manage religious affairs",
    "29": "Protection of interests of minorities",
    "38": "State to secure a social order for the promotion of welfare of the people",
    "39A": "Equal justice and free legal aid",
    "41": "Right to work, to education and to public assistance in certain cases",
    "43A": "Participation of workers in management of Industries",
    "43B": "Promotion of co-operative societies",
    "52": "The President of India",
    "54": "Election of President",
    "56": "Term of office of President",
    "58": "Qualifications for election as President",
    "61": "Procedure for impeachment of the President",
    "63": "The Vice-President of India",
    "76": "Attorney-General for India",
    "79": "Constitution of Parliament",
    "80": "Composition of the Council of States",
    "81": "Composition of the House of the People",
    "83": "Duration of Houses of Parliament",
    "84": "Qualification for membership of Parliament",
    "85": "Sessions of Parliament, prorogation and dissolution",
    "93": "The Speaker and Deputy Speaker of the House of the People",
    "124A": "National Judicial Appointments Commission",
    "129": "Supreme Court to be a court of record",
    "130": "Seat of Supreme Court",
    "143": "Power of the President to consult the Supreme Court",
    "154": "Executive power of State",
    "156": "Term of office of Governor",
    "161": "Power of Governor to grant pardons, etc., and to suspend, remit or commute sentences in certain cases",
    "163": "Council of Ministers to aid and advise Governor",
    "168": "Constitution of Legislatures in States",
    "169": "Abolition or creation of Legislative Councils in States",
    "170": "Composition of the Legislative Assemblies",
    "171": "Composition of the Legislative Councils",
    "172": "Duration of State Legislatures",
    "214": "High Courts for States",
    "265": "Taxes not to be imposed save by authority of law",
    "266": "Consolidated Funds and public accounts of India and of the States",
    "267": "Contingency Fund",
    "269A": "Levy and collection of goods and services tax in course of inter-State trade or commerce",
    "317": "Removal and suspension of a member of a Public Service Commission",
    "320": "Functions of Public Service Commissions",
    "326": "Elections to the House of the People and to the Legislative Assemblies of States to be on the basis of adult suffrage",
    "335": "Claims of Scheduled Castes and Scheduled Tribes to services and posts",
    "338": "National Commission for Scheduled Castes",
    "338A": "National Commission for Scheduled Tribes",
    "338B": "National Commission for Backward Classes",
    "345": "Official language or languages of a State",
    "348": "Language to be used in the Supreme Court and in the High Courts and for Acts, Bills, etc",
    "350A": "Facilities for instruction in mother-tongue at primary stage",
    "350B": "Special Officer for linguistic minorities",
    "351": "Directive for development of the Hindi language",
    "355": "Duty of the Union to protect States against external aggression and internal disturbance",
    "358": "Suspension of provisions of article 19 during emergencies",
    "370": "Temporary provisions with respect to the State of Jammu and Kashmir",
    "371A": "Special provision with respect to the State of Nagaland",
}

# Part IX / IX-A, kept SEPARATE because "Panchayati Raj" is its own topic in the commission's
# syllabus (5% of General Studies) and had no content at all. Splitting these out fills that
# topic rather than burying them inside Constitution & polity.
PANCHAYAT_ARTICLE = {
    "243A": "Gram Sabha",
    "243D": "Reservation of seats in Panchayats",
    "243F": "Disqualifications for membership of Panchayats",
    "243H": "Powers to impose taxes by, and Funds of, the Panchayats",
    "243J": "Audit of accounts of Panchayats",
    "243L": "Application to Union territories",
    "243M": "Part not to apply to certain areas",
    "243N": "Continuance of existing laws and Panchayats",
    "243R": "Composition of Municipalities",
    "243S": "Constitution and composition of Wards Committees",
    "243T": "Reservation of seats in Municipalities",
    "243U": "Duration of Municipalities",
    "243V": "Disqualifications for membership of Municipalities",
    "243X": "Power to impose taxes by, and Funds of, the Municipalities",
    "243Y": "Finance Commission for Panchayats and Municipalities",
    "243B": "Constitution of Panchayats",
    "243C": "Composition of Panchayats",
    "243E": "Duration of Panchayats, etc",
    "243G": "Powers, authority and responsibilities of Panchayats",
    "243K": "Elections to the Panchayats",
    "243Q": "Constitution of Municipalities",
    "243W": "Powers, authority and responsibilities of Municipalities, etc",
}

HI = {
    "Gram Sabha": "ग्राम सभा",
    "Reservation of seats in Panchayats": "पंचायतों में स्थानों का आरक्षण",
    "Disqualifications for membership of Panchayats": "पंचायतों की सदस्यता के लिए निरर्हताएँ",
    "Powers to impose taxes by, and Funds of, the Panchayats":
        "पंचायतों द्वारा कर लगाने की शक्ति तथा पंचायतों की निधियाँ",
    "Audit of accounts of Panchayats": "पंचायतों के लेखाओं की संपरीक्षा",
    "Application to Union territories": "संघ राज्यक्षेत्रों पर लागू होना",
    "Part not to apply to certain areas": "कुछ क्षेत्रों पर इस भाग का लागू न होना",
    "Continuance of existing laws and Panchayats": "विद्यमान विधियों और पंचायतों का बना रहना",
    "Composition of Municipalities": "नगरपालिकाओं की संरचना",
    "Constitution and composition of Wards Committees": "वार्ड समितियों का गठन और संरचना",
    "Reservation of seats in Municipalities": "नगरपालिकाओं में स्थानों का आरक्षण",
    "Duration of Municipalities": "नगरपालिकाओं की अवधि",
    "Disqualifications for membership of Municipalities":
        "नगरपालिकाओं की सदस्यता के लिए निरर्हताएँ",
    "Power to impose taxes by, and Funds of, the Municipalities":
        "नगरपालिकाओं द्वारा कर लगाने की शक्ति तथा निधियाँ",
    "Finance Commission for Panchayats and Municipalities":
        "पंचायतों और नगरपालिकाओं के लिए वित्त आयोग",
    "Laws inconsistent with or in derogation of the fundamental rights": "मौलिक अधिकारों से असंगत या उनका अल्पीकरण करने वाली विधियाँ",
    "Protection in respect of conviction for offences": "अपराधों के लिए दोषसिद्धि के संबंध में संरक्षण",
    "Protection against arrest and detention in certain cases": "कुछ दशाओं में गिरफ्तारी और निरोध से संरक्षण",
    "Freedom to manage religious affairs": "धार्मिक कार्यों के प्रबंध की स्वतंत्रता",
    "Protection of interests of minorities": "अल्पसंख्यक-वर्गों के हितों का संरक्षण",
    "State to secure a social order for the promotion of welfare of the people": "राज्य द्वारा लोक कल्याण की अभिवृद्धि के लिए सामाजिक व्यवस्था बनाना",
    "Equal justice and free legal aid": "समान न्याय और निःशुल्क विधिक सहायता",
    "Right to work, to education and to public assistance in certain cases": "कुछ दशाओं में काम, शिक्षा और लोक सहायता पाने का अधिकार",
    "Participation of workers in management of Industries": "उद्योगों के प्रबंध में कर्मकारों का भाग लेना",
    "Promotion of co-operative societies": "सहकारी समितियों का संवर्धन",
    "The President of India": "भारत का राष्ट्रपति",
    "Election of President": "राष्ट्रपति का निर्वाचन",
    "Term of office of President": "राष्ट्रपति की पदावधि",
    "Qualifications for election as President": "राष्ट्रपति के रूप में निर्वाचन के लिए अर्हताएँ",
    "Procedure for impeachment of the President": "राष्ट्रपति पर महाभियोग चलाने की प्रक्रिया",
    "The Vice-President of India": "भारत का उपराष्ट्रपति",
    "Attorney-General for India": "भारत का महान्यायवादी",
    "Constitution of Parliament": "संसद का गठन",
    "Composition of the Council of States": "राज्य सभा की संरचना",
    "Composition of the House of the People": "लोक सभा की संरचना",
    "Duration of Houses of Parliament": "संसद के सदनों की अवधि",
    "Qualification for membership of Parliament": "संसद की सदस्यता के लिए अर्हता",
    "Sessions of Parliament, prorogation and dissolution": "संसद के सत्र, सत्रावसान और विघटन",
    "The Speaker and Deputy Speaker of the House of the People": "लोक सभा का अध्यक्ष और उपाध्यक्ष",
    "National Judicial Appointments Commission": "राष्ट्रीय न्यायिक नियुक्ति आयोग",
    "Supreme Court to be a court of record": "उच्चतम न्यायालय का अभिलेख न्यायालय होना",
    "Seat of Supreme Court": "उच्चतम न्यायालय का स्थान",
    "Power of the President to consult the Supreme Court": "उच्चतम न्यायालय से परामर्श करने की राष्ट्रपति की शक्ति",
    "Executive power of State": "राज्य की कार्यपालिका शक्ति",
    "Term of office of Governor": "राज्यपाल की पदावधि",
    "Power of Governor to grant pardons, etc., and to suspend, remit or commute sentences in certain cases": "क्षमादान करने की राज्यपाल की शक्ति",
    "Council of Ministers to aid and advise Governor": "राज्यपाल को सहायता और सलाह देने के लिए मंत्रि-परिषद",
    "Constitution of Legislatures in States": "राज्यों के विधान-मंडलों का गठन",
    "Abolition or creation of Legislative Councils in States": "राज्यों में विधान परिषदों का उत्सादन या सृजन",
    "Composition of the Legislative Assemblies": "विधान सभाओं की संरचना",
    "Composition of the Legislative Councils": "विधान परिषदों की संरचना",
    "Duration of State Legislatures": "राज्य के विधान-मंडलों की अवधि",
    "High Courts for States": "राज्यों के लिए उच्च न्यायालय",
    "Taxes not to be imposed save by authority of law": "विधि के प्राधिकार के बिना करों का अधिरोपण न किया जाना",
    "Consolidated Funds and public accounts of India and of the States": "भारत और राज्यों की संचित निधियाँ तथा लोक लेखे",
    "Contingency Fund": "आकस्मिकता निधि",
    "Levy and collection of goods and services tax in course of inter-State trade or commerce": "अंतर्राज्यिक व्यापार के दौरान माल और सेवा कर का उद्ग्रहण और संग्रहण",
    "Removal and suspension of a member of a Public Service Commission": "लोक सेवा आयोग के सदस्य का हटाया जाना और निलंबन",
    "Functions of Public Service Commissions": "लोक सेवा आयोगों के कृत्य",
    "Elections to the House of the People and to the Legislative Assemblies of States to be on the basis of adult suffrage": "लोक सभा और विधान सभाओं के निर्वाचनों का वयस्क मताधिकार पर आधारित होना",
    "Claims of Scheduled Castes and Scheduled Tribes to services and posts": "सेवाओं और पदों के लिए अनुसूचित जातियों और अनुसूचित जनजातियों के दावे",
    "National Commission for Scheduled Castes": "राष्ट्रीय अनुसूचित जाति आयोग",
    "National Commission for Scheduled Tribes": "राष्ट्रीय अनुसूचित जनजाति आयोग",
    "National Commission for Backward Classes": "राष्ट्रीय पिछड़ा वर्ग आयोग",
    "Official language or languages of a State": "राज्य की राजभाषा या राजभाषाएँ",
    "Language to be used in the Supreme Court and in the High Courts and for Acts, Bills, etc": "उच्चतम न्यायालय और उच्च न्यायालयों में प्रयोग की जाने वाली भाषा",
    "Facilities for instruction in mother-tongue at primary stage": "प्राथमिक स्तर पर मातृभाषा में शिक्षा की सुविधाएँ",
    "Special Officer for linguistic minorities": "भाषाई अल्पसंख्यक-वर्गों के लिए विशेष अधिकारी",
    "Directive for development of the Hindi language": "हिंदी भाषा के विकास के लिए निदेश",
    "Duty of the Union to protect States against external aggression and internal disturbance": "बाह्य आक्रमण और आंतरिक अशांति से राज्यों की संरक्षा करने का संघ का कर्तव्य",
    "Suspension of provisions of article 19 during emergencies": "आपात के दौरान अनुच्छेद 19 के उपबंधों का निलंबन",
    "Temporary provisions with respect to the State of Jammu and Kashmir": "जम्मू-कश्मीर राज्य के संबंध में अस्थायी उपबंध",
    "Special provision with respect to the State of Nagaland": "नागालैंड राज्य के संबंध में विशेष उपबंध",
    "Constitution of Panchayats": "पंचायतों का गठन",
    "Composition of Panchayats": "पंचायतों की संरचना",
    "Duration of Panchayats, etc": "पंचायतों की अवधि",
    "Powers, authority and responsibilities of Panchayats": "पंचायतों की शक्तियाँ, प्राधिकार और उत्तरदायित्व",
    "Elections to the Panchayats": "पंचायतों के लिए निर्वाचन",
    "Constitution of Municipalities": "नगरपालिकाओं का गठन",
    "Powers, authority and responsibilities of Municipalities, etc": "नगरपालिकाओं की शक्तियाँ, प्राधिकार और उत्तरदायित्व",
}

_TABLES = {"ARTICLE_SUBJECT_EXTRA": ARTICLE_SUBJECT_EXTRA, "PANCHAYAT_ARTICLE": PANCHAYAT_ARTICLE}


def review_sheet(path="drop/bssc/POLITY_EXTRA_REVIEW.md"):
    """Each article beside its hand-written Hindi, for a person to tick.

    The ENGLISH needs only a sanity check — it is the official PDF's own heading, cleaned. The
    HINDI is the hand-written half and is what this sheet exists for.
    """
    lines = ["# Constitution articles — review sheet", "",
             "English headings are parsed from the **official Constitution PDF** and cleaned;",
             "check them for parse damage only. **The Hindi is hand-written** — check it properly.",
             "",
             "⚠️ **TWO edits to go live, made together:**", "",
             "1. `REVIEWED = True` in `qbank/polity_extra.py`",
             "2. add `[\"PANCHAYAT_ARTICLE\"]` to `concepts` for **Panchayati Raj** in",
             "   `drop/bssc/SYLLABUS_MAP.json` (the extra Articles need no map change — they",
             "   merge into the existing ARTICLE_SUBJECT table).", ""]
    n = 0
    for name, table in _TABLES.items():
        lines += [f"## {name}  ({len(table)} articles)", ""]
        for a, v in table.items():
            n += 1
            lines += [f"- [ ] **Article {a}** — {v}",
                      f"      हिंदी: {HI.get(v, '⚠️ MISSING')}", ""]
    io.open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{n} article rows -> {path}")
    return n
