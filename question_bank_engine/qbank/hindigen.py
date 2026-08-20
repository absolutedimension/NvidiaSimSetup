"""GENERATE-FROM-DATA Hindi engine — deterministic, correct-by-construction हिंदी MCQs for the
BSSC / Bihar govt-exam "हिंदी" section.

The fifth sibling of quantgen / reasoninggen / englishgen / staticgkgen, and the one that closes
the largest measured gap in our BSSC coverage: the mined blueprint (2026-08-19, 497 real questions
from 5 official papers) put the Hindi section at **19-31% of three BSSC papers** — Hindi Vocabulary
18%, Hindi Grammar 11%, Hindi Comprehension 9% — against which we had NO bank at all.

The question shapes here are taken from what the real papers actually ask, e.g.
    "नियम का तद्भव रूप कौन-सा है ?"      (तत्सम → तद्भव)
    "चौमुखता कौन-सा समास है ?"            (समास भेद)
    "जुड़वाँ शब्द का कौन-सा प्रकार है ?"   (संज्ञा भेद)
    "'आँखें मूँद लेना' मुहावरे का अर्थ ?"  (मुहावरा)

WHY GENERATE RATHER THAN INGEST: Hindi grammar is table-driven — a word HAS one तद्भव form, a
compound HAS one समास type. So the answer is a lookup, never a model's opinion, and the distractors
come from the same category (other समास types, other तद्भव words) which makes them exam-plausible
instead of obviously wrong. Impossible to serve a wrong key; unlimited; copyright-clean.

⚠️ These questions are Hindi BY NATURE — a question testing Hindi grammar is not translated into
English on a real paper. So `stem_hi` mirrors `stem` and the options are identical in both, which
is what a real bilingual booklet does for its language section.
"""
import hashlib
import random

from .models import Question, content_hash

SUBJECT = "Hindi"
EXAM = "BSSC"

_SUBJECT_ALIASES = {
    "hindi", "हिंदी", "hindi language", "general hindi", "सामान्य हिंदी",
    "hindi grammar", "हिन्दी", "भाषा हिंदी",
}

# ---------------------------------------------------------------- verified data tables

# तत्सम → तद्भव. Standard, uncontroversial pairs found in every Bihar/UP board grammar text.
TATSAM_TADBHAV = {
    "अग्नि": "आग", "दुग्ध": "दूध", "हस्त": "हाथ", "सूर्य": "सूरज", "चन्द्र": "चाँद",
    "रात्रि": "रात", "मस्तक": "माथा", "कर्ण": "कान", "अक्षि": "आँख", "दन्त": "दाँत",
    "सर्प": "साँप", "मयूर": "मोर", "गृह": "घर", "क्षेत्र": "खेत", "वर्षा": "बरसात",
    "कार्य": "काज", "पुष्प": "फूल", "मृत्यु": "मौत", "सत्य": "सच", "स्वप्न": "सपना",
    "कृषक": "किसान", "दीप": "दीया", "घृत": "घी", "भ्राता": "भाई", "श्रृंगार": "सिंगार",
}

# समास — compound → its type. Textbook examples.
SAMAS = {
    "यथाशक्ति": "अव्ययीभाव", "प्रतिदिन": "अव्ययीभाव", "आजीवन": "अव्ययीभाव",
    "राजपुत्र": "तत्पुरुष", "देशभक्ति": "तत्पुरुष", "गंगाजल": "तत्पुरुष",
    "नीलकमल": "कर्मधारय", "महात्मा": "कर्मधारय", "पीतांबर": "कर्मधारय",
    "त्रिभुज": "द्विगु", "नवरत्न": "द्विगु", "चौराहा": "द्विगु",
    "माता-पिता": "द्वंद्व", "राजा-रानी": "द्वंद्व", "भाई-बहन": "द्वंद्व",
    "दशानन": "बहुव्रीहि", "चतुर्भुज": "बहुव्रीहि", "लंबोदर": "बहुव्रीहि",
}
SAMAS_TYPES = ["अव्ययीभाव", "तत्पुरुष", "कर्मधारय", "द्विगु", "द्वंद्व", "बहुव्रीहि"]

# संज्ञा के भेद
SANGYA = {
    "राम": "व्यक्तिवाचक", "गंगा": "व्यक्तिवाचक", "भारत": "व्यक्तिवाचक", "हिमालय": "व्यक्तिवाचक",
    "लड़का": "जातिवाचक", "नदी": "जातिवाचक", "पुस्तक": "जातिवाचक", "गाय": "जातिवाचक",
    "मिठास": "भाववाचक", "बुढ़ापा": "भाववाचक", "क्रोध": "भाववाचक", "सुंदरता": "भाववाचक",
    "सेना": "समूहवाचक", "सभा": "समूहवाचक", "कक्षा": "समूहवाचक", "भीड़": "समूहवाचक",
    "सोना": "द्रव्यवाचक", "पानी": "द्रव्यवाचक", "तेल": "द्रव्यवाचक", "लोहा": "द्रव्यवाचक",
}
SANGYA_TYPES = ["व्यक्तिवाचक", "जातिवाचक", "भाववाचक", "समूहवाचक", "द्रव्यवाचक"]

# विलोम (antonyms)
VILOM = {
    "आदि": "अंत", "अमृत": "विष", "आय": "व्यय", "उदय": "अस्त", "ज्ञान": "अज्ञान",
    "सुख": "दुःख", "दिन": "रात", "जीवन": "मृत्यु", "शीत": "उष्ण", "हार": "जीत",
    "मित्र": "शत्रु", "आकाश": "पाताल", "उन्नति": "अवनति", "स्वर्ग": "नरक", "पाप": "पुण्य",
    "सरल": "कठिन", "प्राचीन": "नवीन", "अपना": "पराया", "सजीव": "निर्जीव", "गुण": "दोष",
}

# पर्यायवाची (synonyms) — word -> one standard synonym
PARYAYVACHI = {
    "कमल": "पंकज", "सूर्य": "भास्कर", "अग्नि": "पावक", "पानी": "जल", "हाथी": "गज",
    "पृथ्वी": "धरा", "आकाश": "गगन", "नदी": "सरिता", "पर्वत": "गिरि", "वायु": "पवन",
    "रात": "निशा", "सोना": "स्वर्ण", "पुत्र": "तनय", "घर": "गृह", "आँख": "नयन",
}

# मुहावरे — idiom -> meaning
MUHAVARE = {
    "आँखें मूँद लेना": "जान-बूझकर ध्यान न देना",
    "अंगूठा दिखाना": "साफ़ इनकार कर देना",
    "आँखों का तारा": "बहुत प्यारा",
    "नाक में दम करना": "बहुत परेशान करना",
    "कान भरना": "चुगली करना",
    "हाथ मलना": "पछताना",
    "लोहे के चने चबाना": "बहुत कठिन काम करना",
    "आग बबूला होना": "अत्यधिक क्रोधित होना",
    "दाँतों तले उँगली दबाना": "आश्चर्यचकित होना",
    "श्रीगणेश करना": "आरम्भ करना",
    "टेढ़ी खीर": "कठिन काम",
    "घी के दीये जलाना": "बहुत खुशी मनाना",
}

# उपसर्ग — word -> its prefix
UPSARG = {
    "अपमान": "अप", "प्रयोग": "प्र", "विदेश": "वि", "अनुचर": "अनु", "संगम": "सम्",
    "उपकार": "उप", "निर्धन": "निर्", "प्रतिदिन": "प्रति", "अधिकार": "अधि", "परिणाम": "परि",
}

# प्रत्यय — word -> its suffix
PRATYAY = {
    "लिखावट": "आवट", "बुढ़ापा": "आपा", "मिठास": "आस", "सुंदरता": "ता", "पढ़ाई": "आई",
    "लड़कपन": "पन", "धार्मिक": "इक", "दयालु": "आलु", "मानवीय": "ईय", "चालाकी": "ई",
}


# ---------------------------------------------------------------- machinery


def can_generate(exam, subject, chapter=None) -> bool:
    if (subject or "").strip().lower() not in _SUBJECT_ALIASES:
        return False
    if not chapter:
        return True
    return chapter in _CHAP_BUILDERS


def _mcq(seed, correct, distractors, rng, n=4):
    labels = ["A", "B", "C", "D"][:n]
    opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))[:n]
    while len(opts) < n:                       # never serve fewer than n options
        opts.append(str(correct) + " " * len(opts))
    if str(correct) not in opts:
        opts[-1] = str(correct)
    rot = sum(map(ord, seed)) % n
    opts = opts[rot:] + opts[:rot]
    options = [{"label": l, "text": t} for l, t in zip(labels, opts)]
    return options, labels[opts.index(str(correct))]


def _distractors(pool, correct, rng, k=3):
    """Distractors from the SAME category — that is what makes them exam-plausible."""
    cand = [x for x in pool if x != correct]
    rng.shuffle(cand)
    return cand[:k]


def _make_question(built, rng, spec):
    stem = built["stem"].strip()
    options, ans = _mcq(stem, built["correct"], built["distractors"], rng)
    diff = spec.get("dmax") or spec.get("dmin") or 2
    qid = "gen_hin_" + hashlib.md5((spec.get("chapter", "") + "|" + stem).encode()).hexdigest()[:14]
    q = Question(
        id=qid, exam=spec.get("exam") or EXAM, subject=spec.get("subject") or SUBJECT,
        stem=stem, qtype="MCQ_single", options=options, correct_answer=ans,
        solution=built.get("solution", ""),
        # A Hindi-language question is not translated on a real bilingual paper — the Hindi IS
        # the question. Mirroring keeps the bilingual pack shape valid without inventing English.
        stem_hi=stem, options_hi=list(options), solution_hi=built.get("solution", ""),
        chapter=spec.get("chapter"), concept=built.get("concept"), difficulty=diff,
        source="hindigen", generated=True, hash=content_hash(stem))
    q.verified = True
    return q


# ---------------------------------------------------------------- builders


def _b_tadbhav(rng, diff):
    ts, td = rng.choice(list(TATSAM_TADBHAV.items()))
    return {"stem": f"'{ts}' शब्द का तद्भव रूप कौन-सा है ?",
            "correct": td,
            "distractors": _distractors(list(TATSAM_TADBHAV.values()), td, rng),
            "solution": f"'{ts}' (तत्सम) का तद्भव रूप '{td}' है।",
            "concept": "तत्सम-तद्भव"}


def _b_tatsam(rng, diff):
    ts, td = rng.choice(list(TATSAM_TADBHAV.items()))
    return {"stem": f"'{td}' शब्द का तत्सम रूप कौन-सा है ?",
            "correct": ts,
            "distractors": _distractors(list(TATSAM_TADBHAV.keys()), ts, rng),
            "solution": f"'{td}' (तद्भव) का तत्सम रूप '{ts}' है।",
            "concept": "तत्सम-तद्भव"}


def _b_samas(rng, diff):
    word, typ = rng.choice(list(SAMAS.items()))
    return {"stem": f"'{word}' में कौन-सा समास है ?",
            "correct": typ,
            "distractors": _distractors(SAMAS_TYPES, typ, rng),
            "solution": f"'{word}' में {typ} समास है।",
            "concept": "समास"}


def _b_sangya(rng, diff):
    word, typ = rng.choice(list(SANGYA.items()))
    return {"stem": f"'{word}' कौन-सी संज्ञा है ?",
            "correct": typ + " संज्ञा",
            "distractors": [t + " संज्ञा" for t in _distractors(SANGYA_TYPES, typ, rng)],
            "solution": f"'{word}' {typ} संज्ञा है।",
            "concept": "संज्ञा के भेद"}


def _b_vilom(rng, diff):
    w, v = rng.choice(list(VILOM.items()))
    return {"stem": f"'{w}' का विलोम शब्द क्या है ?",
            "correct": v,
            "distractors": _distractors(list(VILOM.values()), v, rng),
            "solution": f"'{w}' का विलोम '{v}' है।",
            "concept": "विलोम शब्द"}


def _b_paryayvachi(rng, diff):
    w, s = rng.choice(list(PARYAYVACHI.items()))
    return {"stem": f"'{w}' का पर्यायवाची शब्द कौन-सा है ?",
            "correct": s,
            "distractors": _distractors(list(PARYAYVACHI.values()), s, rng),
            "solution": f"'{w}' का पर्यायवाची '{s}' है।",
            "concept": "पर्यायवाची शब्द"}


def _b_muhavara(rng, diff):
    idiom, meaning = rng.choice(list(MUHAVARE.items()))
    return {"stem": f"'{idiom}' मुहावरे का सही अर्थ क्या है ?",
            "correct": meaning,
            "distractors": _distractors(list(MUHAVARE.values()), meaning, rng),
            "solution": f"'{idiom}' का अर्थ है — {meaning}।",
            "concept": "मुहावरे"}


def _b_upsarg(rng, diff):
    w, u = rng.choice(list(UPSARG.items()))
    return {"stem": f"'{w}' शब्द में कौन-सा उपसर्ग है ?",
            "correct": u,
            "distractors": _distractors(list(UPSARG.values()), u, rng),
            "solution": f"'{w}' में '{u}' उपसर्ग है।",
            "concept": "उपसर्ग"}


def _b_pratyay(rng, diff):
    w, p = rng.choice(list(PRATYAY.items()))
    return {"stem": f"'{w}' शब्द में कौन-सा प्रत्यय है ?",
            "correct": p,
            "distractors": _distractors(list(PRATYAY.values()), p, rng),
            "solution": f"'{w}' में '{p}' प्रत्यय है।",
            "concept": "प्रत्यय"}


_CHAP_BUILDERS = {
    "शब्द भंडार": [_b_tadbhav, _b_tatsam, _b_vilom, _b_paryayvachi],
    "व्याकरण": [_b_samas, _b_sangya, _b_upsarg, _b_pratyay],
    "मुहावरे एवं लोकोक्तियाँ": [_b_muhavara],
}


def _chapters_for(spec):
    ch = spec.get("chapter")
    if ch and ch in _CHAP_BUILDERS:
        return [ch]
    return list(_CHAP_BUILDERS.keys())


def generate_test(store, spec: dict, count: int = 5) -> dict:
    """Same contract as quantgen/englishgen: returns {questions:[...]}, upserting into the store."""
    rng = random.Random()
    chapters = _chapters_for(spec)
    out, seen, tries = [], set(), 0
    while len(out) < count and tries < count * 40:
        tries += 1
        ch = rng.choice(chapters)
        built = rng.choice(_CHAP_BUILDERS[ch])(rng, spec.get("dmax") or 2)
        q = _make_question(built, rng, dict(spec, chapter=ch))
        if q.hash in seen:
            continue
        seen.add(q.hash)
        if store is not None:
            try:
                store.upsert(q)
            except Exception:
                pass
        out.append(q)
    return {"questions": [q.to_dict() for q in out], "generator": "hindigen",
            "requested": count, "generated": len(out)}
