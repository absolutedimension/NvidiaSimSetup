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


def hi(text):
    """Hindi for one entity, or None when we have not written it by hand."""
    return ENTITY.get(str(text).strip())


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
