"""Hand-written Hindi for the Static GK engine.

Not machine translation, and not transliteration-by-rule. Every entry here was written out
deliberately, for the same reason the bank has a standing rule against translating itself: a
Static GK question is ABOUT the proper noun, so a wrong rendering does not merely read badly, it
makes the question wrong. 'दक्षिण अफ्रीका' scanned as 'दीक्षा अफ्रीका' was a real word that no
corruption check caught; a machine-transliterated 'Godavari' would fail the same way and be just
as invisible from the English side.

Coverage is deliberately PARTIAL, and the gate below is what makes that safe: a question is only
offered in Hindi when its stem template AND its correct answer AND every distractor are all in
these maps. Anything short of that stays English-only and a bilingual paper simply will not draw
it. So the map can grow one table at a time without ever shipping half-Hindi.

To extend: add the entities of one more fact table, run the coverage report in
`bilingual_coverage()`, and the paper picks them up automatically.
"""

# ── question templates ──────────────────────────────────────────────────────────────────────────
# Keyed by the ENGLISH template so a builder needs no change beyond passing its template through.
TEMPLATE = {
    "What is the capital of {k}?": "{k} की राजधानी क्या है ?",
    "The classical/folk dance '{k}' belongs to which state?":
        "शास्त्रीय/लोक नृत्य '{k}' किस राज्य से सम्बन्धित है ?",
    "Where does the river {k} originate?": "{k} नदी का उद्गम स्थल कहाँ है ?",
    "'{k}' is the national {t} of India.": "'{k}' भारत का राष्ट्रीय {t} है।",
    "In which state is {k} located?": "{k} किस राज्य में स्थित है ?",
    "The city of {k} is situated on the bank of which river?":
        "{k} नगर किस नदी के तट पर स्थित है ?",
    "{k} is built on which river?": "{k} किस नदी पर बना है ?",
    "Which city is known as the '{k}'?": "किस शहर को '{k}' कहा जाता है ?",
    "The festival '{k}' is mainly celebrated in which state?":
        "'{k}' त्योहार मुख्यतः किस राज्य में मनाया जाता है ?",
    "Which city is {k} located in?": "{k} किस शहर में स्थित है ?",
    "{k} is known as the father of which field?": "{k} को किस क्षेत्र का जनक कहा जाता है ?",
}

# ── entities ────────────────────────────────────────────────────────────────────────────────────
STATES = {
    "Andhra Pradesh": "आंध्र प्रदेश", "Arunachal Pradesh": "अरुणाचल प्रदेश", "Assam": "असम",
    "Bihar": "बिहार", "Chhattisgarh": "छत्तीसगढ़", "Goa": "गोवा", "Gujarat": "गुजरात",
    "Haryana": "हरियाणा", "Himachal Pradesh": "हिमाचल प्रदेश", "Jharkhand": "झारखंड",
    "Karnataka": "कर्नाटक", "Kerala": "केरल", "Madhya Pradesh": "मध्य प्रदेश",
    "Maharashtra": "महाराष्ट्र", "Manipur": "मणिपुर", "Meghalaya": "मेघालय", "Mizoram": "मिज़ोरम",
    "Nagaland": "नागालैंड", "Odisha": "ओडिशा", "Punjab": "पंजाब", "Rajasthan": "राजस्थान",
    "Sikkim": "सिक्किम", "Tamil Nadu": "तमिलनाडु", "Telangana": "तेलंगाना", "Tripura": "त्रिपुरा",
    "Uttar Pradesh": "उत्तर प्रदेश", "Uttarakhand": "उत्तराखंड", "West Bengal": "पश्चिम बंगाल",
    "Delhi": "दिल्ली", "Jammu and Kashmir": "जम्मू और कश्मीर", "Ladakh": "लद्दाख",
    "Puducherry": "पुडुचेरी",
}

CITIES = {
    "Amaravati": "अमरावती", "Itanagar": "ईटानगर", "Dispur": "दिसपुर", "Patna": "पटना",
    "Raipur": "रायपुर", "Panaji": "पणजी", "Gandhinagar": "गांधीनगर", "Chandigarh": "चंडीगढ़",
    "Shimla": "शिमला", "Ranchi": "रांची", "Bengaluru": "बेंगलुरु", "Thiruvananthapuram":
    "तिरुवनंतपुरम", "Bhopal": "भोपाल", "Mumbai": "मुंबई", "Imphal": "इंफाल", "Shillong": "शिलांग",
    "Aizawl": "आइजोल", "Kohima": "कोहिमा", "Bhubaneswar": "भुवनेश्वर", "Jaipur": "जयपुर",
    "Gangtok": "गंगटोक", "Chennai": "चेन्नई", "Hyderabad": "हैदराबाद", "Agartala": "अगरतला",
    "Lucknow": "लखनऊ", "Dehradun": "देहरादून", "Kolkata": "कोलकाता", "New Delhi": "नई दिल्ली",
    "Srinagar": "श्रीनगर", "Leh": "लेह", "Agra": "आगरा", "Delhi": "दिल्ली", "Amritsar": "अमृतसर",
    "Ahmedabad": "अहमदाबाद", "Nashik": "नासिक", "Varanasi": "वाराणसी", "Allahabad": "प्रयागराज",
    "Prayagraj": "प्रयागराज", "Jodhpur": "जोधपुर", "Udaipur": "उदयपुर", "Mysuru": "मैसूरु",
}

DANCES = {
    "Bharatanatyam": "भरतनाट्यम", "Kathak": "कथक", "Kathakali": "कथकली", "Odissi": "ओडिसी",
    "Kuchipudi": "कुचिपुड़ी", "Manipuri": "मणिपुरी", "Mohiniyattam": "मोहिनीअट्टम",
    "Sattriya": "सत्रिया", "Bhangra": "भांगड़ा", "Garba": "गरबा", "Bihu": "बिहू",
    "Lavani": "लावणी", "Ghoomar": "घूमर", "Chhau": "छऊ", "Yakshagana": "यक्षगान",
    "Giddha": "गिद्दा", "Kalbelia": "कालबेलिया", "Dandiya": "डांडिया", "Jhumar": "झूमर",
    "Rouf": "रौफ",
}

RIVERS = {
    "Ganga": "गंगा", "Yamuna": "यमुना", "Godavari": "गोदावरी", "Krishna": "कृष्णा",
    "Narmada": "नर्मदा", "Kaveri": "कावेरी", "Cauvery": "कावेरी", "Tapti": "ताप्ती",
    "Mahanadi": "महानदी", "Brahmaputra": "ब्रह्मपुत्र", "Sutlej": "सतलुज", "Beas": "ब्यास",
    "Ravi": "रावी", "Chenab": "चिनाब", "Jhelum": "झेलम", "Sone": "सोन", "Kosi": "कोसी",
    "Gandak": "गंडक", "Sabarmati": "साबरमती", "Indus": "सिंधु",
}

PLACES = {
    "Gangotri": "गंगोत्री", "Yamunotri": "यमुनोत्री", "Trimbakeshwar (Nashik)":
    "त्र्यंबकेश्वर (नासिक)", "Amarkantak": "अमरकंटक", "Talakaveri": "तालकावेरी",
    "Mahabaleshwar": "महाबलेश्वर", "Multai": "मुलताई", "Sihawa": "सिहावा",
    "Mansarovar": "मानसरोवर", "Verinag": "वेरीनाग", "Beas Kund": "ब्यास कुंड",
    "Rakshastal": "राक्षसताल", "Chemayungdung": "चेमायुंगडुंग",
}

# every map the gate consults, in one place
ENTITY = {}
for _m in (STATES, CITIES, DANCES, RIVERS, PLACES):
    ENTITY.update(_m)


def register(mapping):
    """Let another verified table contribute its hand-written Hindi to the same gate.

    history_tables keeps its Hindi next to its facts so that ONE review sheet covers both — a
    reviewer ticking "Champaran Satyagraha -> 1917" is also ticking "चम्पारण सत्याग्रह". This is how
    that Hindi reaches `_bilingual_keys`, which is the gate deciding whether a General Studies
    question may print in both languages at all.
    """
    ENTITY.update(mapping)


def hi(text):
    """Hindi for one entity, or None when we have not written it by hand."""
    t = str(text).strip()
    return ENTITY.get(t) or EXTRA_HI.get(t)


def hi_template(tmpl):
    return TEMPLATE.get(tmpl)


def bilingual(tmpl, key, correct, distractors):
    """Everything a bilingual question needs, or None if ANY part is missing.

    All-or-nothing on purpose. A question with a Hindi stem and one English option is worse than
    an English-only question: the English-only one is honestly monolingual, while the half-Hindi
    one looks bilingual and quietly asks a Hindi-medium student to read an option they cannot.
    """
    t = hi_template(tmpl)
    k, c = hi(key), hi(correct)
    ds = [hi(d) for d in distractors]
    if not t or not k or not c or any(d is None for d in ds):
        return None
    return {"tmpl": t, "key": k, "correct": c, "distractors": ds}

# ── Constitution: articles and amendments ───────────────────────────────────────────────────────
# Hand-written like everything above, and with more care than the rest, because a wrong rendering
# here is not a clumsy sentence — it is a wrong constitutional fact that a Hindi-medium candidate
# has no way to catch. Standard legal Hindi as the Constitution's own Hindi text uses it
# (विधि के समक्ष समता, not the loose समानता), so a student reading a bare Act sees the same words.
# Article and amendment NUMBERS stay in Arabic digits, which is how the commission prints them.

ARTICLE_SUBJECT_HI = {
    "equality before the law": "विधि के समक्ष समता",
    "the six fundamental freedoms": "छह मौलिक स्वतंत्रताओं",
    "protection of life and personal liberty": "प्राण एवं दैहिक स्वतंत्रता के संरक्षण",
    "free and compulsory education for children aged 6 to 14":
        "6 से 14 वर्ष के बच्चों की नि:शुल्क एवं अनिवार्य शिक्षा",
    "prohibition of employment of children in factories":
        "कारखानों में बालकों के नियोजन के प्रतिषेध",
    "the right to constitutional remedies": "संवैधानिक उपचारों के अधिकार",
    "organisation of village panchayats": "ग्राम पंचायतों के संगठन",
    "a uniform civil code for citizens": "नागरिकों के लिए समान नागरिक संहिता",
    "the fundamental duties of citizens": "नागरिकों के मूल कर्तव्यों",
    "the pardoning power of the President": "राष्ट्रपति की क्षमादान शक्ति",
    "the definition of a Money Bill": "धन विधेयक की परिभाषा",
    "the annual financial statement, or Union Budget":
        "वार्षिक वित्तीय विवरण (केंद्रीय बजट)",
    "the Comptroller and Auditor General of India":
        "भारत के नियंत्रक एवं महालेखापरीक्षक",
    "the appointment of the Governor of a State": "राज्य के राज्यपाल की नियुक्ति",
    "the Finance Commission": "वित्त आयोग",
    "the Election Commission of India": "भारत निर्वाचन आयोग",
    "the proclamation of a National Emergency": "राष्ट्रीय आपातकाल की उद्घोषणा",
    "President's Rule in a State": "किसी राज्य में राष्ट्रपति शासन",
    "the power of Parliament to amend the Constitution":
        "संविधान में संशोधन करने की संसद की शक्ति",
    # The twelve added from the parsed ToC. Constitution's own Hindi terms throughout — अस्पृश्यता
    # का अंत, लोक नियोजन, दुर्व्यापार, राजभाषा — so a candidate reading the bare Act they are allowed
    # to carry into the hall sees the same words on our paper.
    "prohibition of discrimination on grounds of religion, race, caste, sex or place of birth":
        "धर्म, मूलवंश, जाति, लिंग या जन्मस्थान के आधार पर विभेद के प्रतिषेध",
    "equality of opportunity in matters of public employment":
        "लोक नियोजन के विषय में अवसर की समता",
    "the abolition of untouchability": "अस्पृश्यता के अंत",
    "the abolition of titles": "उपाधियों के अंत",
    "prohibition of traffic in human beings and forced labour":
        "मानव के दुर्व्यापार और बलात् श्रम के प्रतिषेध",
    "freedom of conscience and free profession, practice and propagation of religion":
        "अंतःकरण की तथा धर्म को अबाध रूप से मानने, आचरण करने और प्रचार करने की स्वतंत्रता",
    "separation of the judiciary from the executive":
        "कार्यपालिका से न्यायपालिका के पृथक्करण",
    "a joint sitting of both Houses in certain cases":
        "कुछ दशाओं में दोनों सदनों की संयुक्त बैठक",
    "the establishment and constitution of the Supreme Court":
        "उच्चतम न्यायालय की स्थापना और गठन",
    "Public Service Commissions for the Union and for the States":
        "संघ और राज्यों के लिए लोक सेवा आयोग",
    "the official language of the Union": "संघ की राजभाषा",
    "provisions as to a financial emergency": "वित्तीय आपात के बारे में उपबंधों",
}

# OBLIQUE form (73वें, not 73वाँ). These are only ever used before "संविधान संशोधन ने", and the
# ergative ने takes the oblique — "73वाँ संविधान संशोधन ने" is the kind of error a Hindi reader
# notices in the first line, and the English half gives no hint of it. Same class as the
# मेरा/मेरी slash and the भतीजी/भांजी mix-up caught earlier.
AMENDMENT_HI = {
    "42nd": "42वें", "44th": "44वें", "52nd": "52वें", "61st": "61वें",
    "73rd": "73वें", "74th": "74वें", "86th": "86वें", "101st": "101वें",
}

AMENDMENT_DID_HI = {
    "added the words Socialist, Secular and Integrity to the Preamble":
        "प्रस्तावना में समाजवादी, पंथनिरपेक्ष तथा अखंडता शब्द जोड़े",
    "removed the right to property from the Fundamental Rights":
        "संपत्ति के अधिकार को मौलिक अधिकारों से हटाया",
    "added the Tenth Schedule on defection": "दलबदल से संबंधित दसवीं अनुसूची जोड़ी",
    "lowered the voting age from 21 to 18": "मतदान की आयु 21 से घटाकर 18 वर्ष की",
    "gave constitutional status to Panchayati Raj institutions":
        "पंचायती राज संस्थाओं को संवैधानिक दर्जा दिया",
    "gave constitutional status to urban local bodies":
        "शहरी स्थानीय निकायों को संवैधानिक दर्जा दिया",
    "made education a fundamental right for children aged 6 to 14":
        "6 से 14 वर्ष के बच्चों के लिए शिक्षा को मौलिक अधिकार बनाया",
    "introduced the Goods and Services Tax": "वस्तु एवं सेवा कर (GST) लागू किया",
}

for _m in (ARTICLE_SUBJECT_HI, AMENDMENT_HI, AMENDMENT_DID_HI):
    ENTITY.update(_m)

TEMPLATE.update({
    "Article {k} of the Constitution deals with {v}.":
        "संविधान का अनुच्छेद {k} {v} से संबंधित है।",
    "The {k} Amendment {v}.": "{k} संविधान संशोधन ने {v}।",
})

# Added 2026-08-21. HAND-WRITTEN, like everything else in this file — river ORIGIN places and the
# dance names that had none. Their absence was silently costing coverage rather than correctness:
# the bilingual gate needs the key AND the value, so seven of eleven rivers could never be asked in
# Hindi and the geography topic kept redrawing the same four.
EXTRA_HI = {
    "Gangotri Glacier (Gaumukh)": "गंगोत्री हिमनद (गोमुख)",
    "Talakaveri (Kodagu)": "तालकावेरी (कोडगु)",
    "near Lake Mansarovar (Tibet)": "मानसरोवर झील के निकट (तिब्बत)",
    "Angsi Glacier (Tibet)": "आंगसी हिमनद (तिब्बत)",
    "Aravalli Hills": "अरावली पहाड़ियाँ",
    "Sihawa (Chhattisgarh)": "सिहावा (छत्तीसगढ़)",
    "Multai (Betul, MP)": "मुलताई (बैतूल, मध्य प्रदेश)",
    "Cheraw": "चेरॉ", "Dollu Kunitha": "डोल्लू कुनिथा", "Karma": "करमा",
    "Padayani": "पडयानी", "Nautanki": "नौटंकी",
}

# Added 2026-08-22 with the 14 new rivers. Hand-written, like everything else in this file.
EXTRA_HI.update({
    "Chambal": "चंबल", "Betwa": "बेतवा", "Son": "सोन", "Damodar": "दामोदर",
    "Ghaghara": "घाघरा", "Periyar": "पेरियार", "Tungabhadra": "तुंगभद्रा",
    "Janapav Hills (Mhow)": "जानापाव पहाड़ी (महू)",
    "Vindhya Range (Raisen)": "विंध्य श्रेणी (रायसेन)",
    "Amarkantak Plateau": "अमरकंटक पठार",
    "Chandwa (Latehar)": "चंदवा (लातेहार)",
    "Nhubine Himal Glacier (Nepal)": "न्हुबिने हिमाल हिमनद (नेपाल)",
    "Sun Kosi confluence (Nepal)": "सुन कोसी संगम (नेपाल)",
    "Mapchachungo Glacier (Tibet)": "मापचाचुंगो हिमनद (तिब्बत)",
    "Beas Kund (Rohtang)": "ब्यास कुंड (रोहतांग)",
    "Bara Bhangal (Kangra)": "बड़ा भंगाल (कांगड़ा)",
    "Rakshastal (Tibet)": "राक्षसताल (तिब्बत)",
    "Verinag (Anantnag)": "वेरीनाग (अनंतनाग)",
    "Bara Lacha Pass (Lahaul)": "बारालाचा दर्रा (लाहौल)",
    "Sivagiri Hills (Western Ghats)": "शिवगिरि पहाड़ियाँ (पश्चिमी घाट)",
    "Koodli (Karnataka)": "कूडली (कर्नाटक)",
})
