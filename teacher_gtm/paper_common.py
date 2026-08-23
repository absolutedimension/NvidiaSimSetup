#!/usr/bin/env python3
"""Shared rendering + quality rules for the BSSC/BPSC paper builders.

Both `build_onestep_paper.py` (bilingual, 2022-25 papers) and `build_bssc_150_newstock.py`
(English, 2016-18 papers) hit the same two problems, so the rules live here once:

  1. The extracted questions carry real LaTeX, because that is how formulae were transcribed.
     Printed verbatim a student reads "\\frac{5}{9}" — the first bilingual paper shipped with 56 of
     them. `mathify` turns the handful of constructs these papers actually use into HTML and
     Unicode. There is no network in the headless print, so a JS math renderer is not an option.

  2. A small number of questions are unanswerable no matter what the official key says: an option
     whose text is a bare option LETTER (the extractor swallowed the words and kept the label), or
     two options with identical text. 13 such questions reached the first bilingual paper.
     `servable` drops them; the words are not in the JSON, so they cannot be repaired.
"""
import html
import io
import json
import os
import re

_GREEK = {"pi": "π", "theta": "θ", "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
          "lambda": "λ", "mu": "μ", "omega": "ω", "sigma": "σ", "phi": "φ"}
_OPS = {"times": "×", "div": "÷", "pm": "±", "mp": "∓", "le": "≤", "leq": "≤", "ge": "≥",
        "geq": "≥", "ne": "≠", "neq": "≠", "approx": "≈", "cdot": "·", "infty": "∞",
        "rightarrow": "→", "Rightarrow": "⇒", "circ": "°", "degree": "°"}

# CSS the stacked fractions and radicals need. Both builders paste this into their <style>.
MATH_CSS = """
.fr { display:inline-block; vertical-align:middle; text-align:center; margin:0 2px; }
.fr .nu { display:block; padding:0 3px; border-bottom:1px solid #1a1c24; line-height:1.15; }
.fr .de { display:block; padding:0 3px; line-height:1.15; }
.rad { border-top:1px solid #1a1c24; padding:0 2px; margin-left:1px; }
.rad::before { content:"\\221A"; margin-left:-3px; border-top:0; }
sup, sub { font-size:75%; }
"""


def mathify(t):
    """LaTeX -> HTML/Unicode. Input MUST already be HTML-escaped; output contains tags."""
    t = str(t or "")
    t = t.replace("\\left", "").replace("\\right", "").replace("\\!", "").replace("\\,", " ")
    t = re.sub(r"\$+", "", t)
    for _ in range(3):                                    # nested fractions
        new = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
                     r'<span class="fr"><span class="nu">\1</span>'
                     r'<span class="de">\2</span></span>', t)
        if new == t:
            break
        t = new
    t = re.sub(r"\\d?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1/\2", t)   # anything still nested
    t = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r'<span class="rad">\1</span>', t)
    t = re.sub(r"\\sqrt\s*(\w)", r'<span class="rad">\1</span>', t)
    for k, v in list(_GREEK.items()) + list(_OPS.items()):
        # NOT \b: "\times175" has no word boundary between "times" and "1", so the operator fell
        # through to the catch-all that strips unknown commands — and "164 \times 175" rendered as
        # "164175". A negative lookahead for a letter keeps \timeszone-style names safe.
        t = re.sub(r"\\" + k + r"(?![a-zA-Z])", v, t)
    t = re.sub(r"\^\s*\{([^{}]*)\}", r"<sup>\1</sup>", t)
    # \w matches ONE character, so "3^66" superscripted only the first 6 and printed 3<sup>6</sup>6
    # — a different question from the one the builder computed an answer for, with nothing to see
    # in the HTML but a stray digit. Same family as the `$` and the "______" above: any symbol a
    # stem prints has to be checked through here. A run of DIGITS is taken whole; a letter
    # exponent stays single so "x^2y" still leaves the y on the baseline.
    t = re.sub(r"\^\s*(-?\d+|-?\w)", r"<sup>\1</sup>", t)
    t = re.sub(r"_\s*\{([^{}]*)\}", r"<sub>\1</sub>", t)
    # NOT \w — \w includes the underscore itself, so a fill-in-the-blank "______" was eaten as a
    # run of nested subscripts and printed as "_ _ _ ." A subscript is a letter or a digit; a run
    # of underscores is a blank, and the commission prints exactly that. Same family as the `$`
    # that mathify strips: any symbol a stem prints has to be checked through here first.
    # No \s* either. "______ is the capital of X" put the trailing underscore next to the space
    # before "is", so the blank printed as "_____ i s". A subscript is written tight against its
    # base — H_2, x_1 — and never across a space, so requiring adjacency costs nothing and stops
    # the blank being eaten. (Second fix to this line; the first only excluded the underscore.)
    t = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", t)
    t = t.replace("\\%", "%").replace("\\$", "$")
    t = re.sub(r"\\[a-zA-Z]+", "", t)                     # drop anything unrecognised
    return t.replace("{", "").replace("}", "")


# ── FIGURES ─────────────────────────────────────────────────────────────────────────────────────
# A non-verbal question is a PICTURE, and every path in this file escapes its input — correctly,
# because a stem is untrusted text. So a figure travels as a token, `[[FIG:<key>]]`, which survives
# escaping unchanged, and the SVG is substituted back in afterwards by `place_figures`.
#
# The alternative was an "allow raw HTML" flag threaded through esc(), which would mean every stem
# in the bank is one bad character away from injecting markup into a printed paper. A token that
# only ever resolves against a per-question dictionary cannot do that: an unknown key renders as
# nothing rather than as anything.
FIG_TOKEN = re.compile(r"\[\[FIG:([A-Za-z0-9_-]+)\]\]")


def place_figures(html_text, figures):
    """Replace [[FIG:key]] with figures[key], AFTER escaping. Unknown keys resolve to empty."""
    if not figures:
        return FIG_TOKEN.sub("", html_text)
    return FIG_TOKEN.sub(lambda m: figures.get(m.group(1), ""), html_text)


def esc(t):
    """Escape first, then typeset — the maths becomes tags, everything else stays inert."""
    return mathify(html.escape(str(t or "")))


def options_ok(options):
    """Four distinct, non-degenerate options."""
    texts = [re.sub(r"\s+", " ", str(o.get("text", ""))).strip() for o in options or []]
    if len(texts) != 4:
        return False
    if any(re.fullmatch(r"[A-Ea-e]", t) for t in texts):
        return False
    return len({t.lower() for t in texts}) == 4


# Latin letters sandwiched INSIDE a Devanagari word — "बAREफुट" for "बेयरफुट". The extractor
# half-transliterates a loanword and leaves the English fragment in place. Rohan caught one of
# these by eye in Set 1; a bank-wide sweep found it was the only instance, but the failure mode is
# invisible in the JSON and obvious on the page, so it is gated here permanently rather than left
# to the next reviewer.
_MIXED_SCRIPT = re.compile(r"[\u0900-\u097f][A-Za-z]{2,}[\u0900-\u097f]")


# Characters from scripts that have no business in a Hindi/English exam paper. The OCR emitted
# "किलो그램" — Hangul spliced into the middle of a Hindi word — which the Latin-inside-Devanagari
# check could not see because 그램 is neither Latin nor Devanagari.
# A whole Latin word standing between Hindi words — "गैर-सम Cooperation आंदोलन". The
# Latin-inside-a-WORD check missed this because spaces separate the tokens. Acronyms and units are
# legitimate (BFT, GDP, ICC, km, RNA), so require a lower-case-containing word of 4+ letters.
_LATIN_WORD_IN_HINDI = re.compile(r"[\u0900-\u097f]\s+[A-Za-z]*[a-z]{3,}[A-Za-z]*\s+[\u0900-\u097f]")

# recurring OCR substitutions that leave real Hindi words in place of the right ones
_HINDI_WRONG_WORD = re.compile(r"प्रश्न\s+\d|प्रश्न\s+n\s|प्रश्न\s+पद|अंत\s+संदर्भ")

_FOREIGN_SCRIPT = re.compile(r"[\u1100-\u11ff\u3000-\u303f\u3040-\u30ff\u3130-\u318f"
                             r"\u4e00-\u9fff\uac00-\ud7af\u0600-\u06ff\u0e00-\u0e7f]")

# निम्नलिखित ("the following") is the most common word in an exam paper and the one these scans
# mangle most. A fuzzy match on it was tried and MEASURED NOT TO WORK: the corruptions score 0.30
# to 0.95 similarity while legitimate words score 0.12 to 0.71, so the classes overlap —
# निर्णयात्मक (corruption, 0.38) sits BELOW नियम (a real word, 0.43), and निम्नांकित / निम्नतम are
# real words at 0.70. No threshold separates them. So this is an explicit list of corruptions
# actually observed in these scans; it needs extending when review finds a new one, and that is
# the honest cost of not having a general detector.
_HINDI_CORRUPT = re.compile("|".join([
    "निर्मलिखित", "निर्णयात्मक", "निर्माणबंद", "निर्माणबिंदु", "फिमानलिफ़िकत", "फिनमलिफ़ट",
    "निम्नलिखत", "सूक्ष्मण", "अव्यविक", "उत्प्रदक", "आँटिफिकल", "नैतिकता चक्र", "वित्तीयकारक",
]))


def script_clean(q):
    """True if the Hindi is free of stranded Latin, foreign scripts, and mangled निम्नलिखित."""
    fields = [q.get(f) or "" for f in ("stem", "stem_hi")]
    fields += [o.get("text") or "" for key in ("options", "options_hi") for o in (q.get(key) or [])]
    for t in fields:
        if _MIXED_SCRIPT.search(t) or _FOREIGN_SCRIPT.search(t):
            return False
        if _HINDI_CORRUPT.search(t) or _HINDI_WRONG_WORD.search(t):
            return False
    hi = q.get("stem_hi") or ""
    if _LATIN_WORD_IN_HINDI.search(hi):
        return False
    return True


def servable(q, need_hindi=False):
    """A question we can actually put in front of a student.

    The Hindi options need the SAME check as the English ones, separately. A bilingual question can
    have four fine English options and four identical Hindi ones ('जग + नाश' x4) — the English half
    reads correctly and the Hindi half is unanswerable, and checking only `options` lets it through.
    """
    if not (q.get("stem") and q.get("correct_answer") and options_ok(q.get("options"))):
        return False
    if need_hindi:
        if not q.get("stem_hi"):
            return False
        if not script_clean(q):
            return False
        oh = q.get("options_hi") or []
        if oh and not options_ok(oh):
            return False
    return True


def sig(stem, n=70):
    """Collapse digits so two clones of one template do not both land in the paper."""
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", stem or "")).strip()[:n]


# ── Inter Level (Advt 02/23-A) maths syllabus gate ──────────────────────────────────────────────
# The official prelim syllabus names ONLY arithmetic:
#   संख्या पद्धति · पूर्ण संख्याओं का अभिकलन · दशमलव और भिन्न · संख्याओं के बीच परस्पर संबंध ·
#   मूलभूत अंक गणितीय संक्रियाएँ · प्रतिशत · अनुपात तथा समानुपात · औसत · ब्याज · लाभ और हानि
# It does NOT name algebra, trigonometry, mensuration, coordinate geometry, progressions,
# probability or statistics. Our maths stock comes largely from Advt 0111 (a CLERK exam with a
# wider maths paper), so it carries polynomials, APs, circle geometry and probability — all above
# what an Inter Level candidate is examined on.
#
# The tags cannot do this filtering. Measured: tag.type "arithmetic" includes "Two poles of heights
# 6 m and 11 m stand vertically upright..." (Pythagoras) and tag.type "percentage_profit_loss"
# includes "If the radius of a circle is diminished by 10%, then its area is diminished by"
# (mensuration wearing a percentage costume). So the gate reads the question text.
#
# Deliberately a DENY list, not an allow list: a wrongly-kept question is a syllabus error on a
# student's paper, while a wrongly-dropped one costs nothing — the pool is large.
_ABOVE_SYLLABUS = re.compile(r"""
    polynomial | quadratic | \bzero(e?s)?\ of\b | \broots?\ of\ the\b | factoris | factoriz
  | arithmetic\ progression | geometric\ progression | \bA\.?P\.?\b | \bG\.?P\.?\b
  | common\ difference | \bn-?th\ term\b | \bterms?\ of\ an?\ \w+\ progression
  # trig: a trailing \b fails on "cot12" and "cosθ" (digit/greek are word chars), and a bare
  # "sec" would match "second"/"sector". Require what actually follows a trig function.
  | trigonometr | \b(sin|cos|tan|cot|cosec|sec)\s*(?=[0-9θΘαβAB(^{\\])
  | height\ and\ distance | angle\ of\ (elevation|depression)
  | \bpoles?\b | \btower\b | \bshadow\b | \bladder\b
  | \bcircle | radius | radii | diameter | circumference | \bchord\b | \btangent\b | \barc\b
  | \bsector\b | perimeter | \barea\ of | volume\ of | surface\ area
  | triangle | quadrilateral | parallelogram | rhombus | trapezium | \bpolygon\b
  | cylinder | \bcone\b | \bsphere\b | hemisphere | \bprism\b
  | hypotenuse | pythagoras | \bvertices\b | \bvertex\b | \bdiagonal | \bangle
  | coordinate | co-ordinate | \bdivides\ the\ join\b | \babscissa\b | \bordinate\b
  # algebra: solving equations is not in the named syllabus either
  | system\ of\ equations | linear\ equation | \bequations?\b | \bexpressions?\b
  | समीकरण | व्यंजक
  | probability | \bmedian\b | \bmode\b | central\ tendency | frequency\ distribution
  | standard\ deviation | \bvariance\b | \bhistogram\b | ogive | frequency\ polygon
  | \blocus\b | \bsimilar\ triangles\b | \bcongruen | \bcollinear\b | \bperpendicular\b
  | \bdistribution\b | \\Delta | \bDelta\ [A-Z]{3}\b | \bbisector\b | \bparallel\ to\b
  # Devanagari equivalents
  | बहुपद | द्विघात | समान्तर\ श्रेणी | त्रिकोणमिति | (?<!प्र)वृत्त | त्रिज्या | परिधि | क्षेत्रफल
  | आयतन | त्रिभुज | चतुर्भुज | बेलन | शंकु | गोला | प्रायिकता | माध्यिका | बहुलक | निर्देशांक
""", re.I | re.X)

# Guard: these LOOK like the deny list but are ordinary arithmetic and must survive.
_FALSE_POSITIVE = re.compile(r"perfect\ square|square\ root|cube\ root|squares?\ of\ the\ number"
                             r"|वर्गमूल|घनमूल|पूर्ण\ वर्ग", re.I | re.X)


def inter_level_maths_ok(q):
    """True if a Mathematics question sits inside the Inter Level (02/23-A) syllabus.

    Applies only to Mathematics; every other section passes through untouched.
    """
    if (q.get("tag") or {}).get("section") != "Mathematics":
        return True
    text = " ".join([q.get("stem") or "", q.get("stem_hi") or ""] +
                    [o.get("text", "") for o in (q.get("options") or [])])
    if _FALSE_POSITIVE.search(text) and not _ABOVE_SYLLABUS.search(text):
        return True
    return not _ABOVE_SYLLABUS.search(text)


# Computer/IT knowledge is NOT in the Inter Level prelim syllabus. It appears in the advertisement
# only as a TECHNICAL ELIGIBILITY requirement (Hindi word-processing / typing), tested separately —
# not as a prelim subject. Our stock carries a few from clerk papers that did examine it.
# NOTE the (?-i:...) groups: RAM and CPU must stay CASE-SENSITIVE. Case-insensitively, \bRAM\b
# matches the name "Ram" and silently dropped every question mentioning Ram Mohan Roy — a real
# loss, since the size of this pool is what caps how many unique sets we can build.
_COMPUTER = re.compile(r"MS[- ]?Word|MS[- ]?Excel|PowerPoint|\bkeyboard\b|shortcut|\bsoftware\b"
                       r"|\bhardware\b|\bcomputer\b|Ctrl\s*\+|(?-i:\bRAM\b|\bCPU\b)"
                       r"|operating\s+system|कंप्यूटर|कम्प्यूटर"
                       # the same syllabus point, wider: computing TOPICS, not just software names
                       r"|natural\s+language\s+processing|tokeni[sz]ation|machine\s+learning"
                       r"|\bHTTP\b|\bFTP\b|\bSMTP\b|\bDNS\b|\bURL\b|\bIP\s+address\b"
                       r"|spreadsheet|\bformula\s+in\s+Excel\b", re.I)

# English GRAMMAR/VOCABULARY items. Some papers we source from (the LDC/Welfare paper especially)
# carry a full English section, and those questions get tagged General Studies. The Inter Level
# prelim has NO English section — its three parts are GS, Science+Maths and Mental Ability — so an
# antonym or a modal-verb question does not belong on this paper however good the question is.
_ENGLISH_LANG = re.compile(r"\bantonym\b|\bsynonym\b|one\s+word\s+substitut|\bidiom\b"
                           r"|choose\s+the\s+correct\s+(modal|preposition|article|tense|verb)"
                           r"|fill\s+in\s+the\s+blank.*\b(verb|preposition|article|modal)\b"
                           r"|correct\s+the\s+sentence|active\s+and\s+passive|direct\s+and\s+indirect",
                           re.I)

# "(32) ____ range of flora" — a numbered blank belonging to a comprehension PASSAGE that we do not
# hold. Standing alone on a paper it is unanswerable, whatever the official key says.
_PASSAGE_BLANK = re.compile(r"\(\d{1,3}\)\s*_{2,}")

# "from the following table", "how many triangles are there in the following figure" — the table or
# drawing is not in our JSON, so the question cannot be answered on the page no matter how good the
# transcription is. Rare (2 in 1,018) but fatal to the question.
_NEEDS_FIGURE = re.compile(r"following\s+(table|figure|diagram|graph|chart)|given\s+table"
                           r"|table\s+below|figure\s+below|shown\s+below|as\s+shown"
                           r"|निम्न\s*सारणी|निम्नलिखित\s*सारणी|उपरोक्त\s*सारणी"
                           r"|निम्न\s*चित्र|निम्नलिखित\s*चित्र|दिए\s*गए\s*चित्र|आरेख", re.I)


_NUM = re.compile(r"\d+")

# An Assertion-Reason question whose Assertion and Reason are MISSING — the stem carries only the
# rubric ("a statement of Assertion (A) is followed by a statement of Reason (R), choose the
# correct option") and the four generic options, with nothing to actually judge. Unanswerable.
_AR_RUBRIC = re.compile(r"assertion\s*\(a\)|अभिकथन|असर्शन|आश्वासन\s*\(a\)", re.I)
_AR_CONTENT = re.compile(r"\((?:A|R)\)\s*[:：]|अभिकथन\s*\(A\)\s*[:：]|कारण\s*\(R\)\s*[:：]", re.I)


def numbers_agree(q):
    """The two languages of a bilingual question must contain the SAME numbers.

    Measured on the built papers: 13 questions disagreed. Some are merely incomplete translations
    ("x% of y% of 80 is same as 25% of 900" lost "25% of 900" in Hindi); others change the ANSWER —
    one generated question read "coded by TWICE its position (A=2, B=4)" in English while the Hindi
    said only "according to its alphabet position", so a Hindi-medium student computes a different
    code. Worse, that made two different questions identical in Hindi.
    """
    hi, en = q.get("stem_hi") or "", q.get("stem") or ""
    if not (hi and en):
        return True
    from collections import Counter
    return Counter(_NUM.findall(hi)) == Counter(_NUM.findall(en))


def option_numbers_agree(q):
    """Option i must carry the same numbers in both languages.

    Found by hand: one question printed English options −5/7, 29, 9, −11 beside Hindi options
    −5/7, −42, −14, 28. The keyed letter is the greatest value in the Hindi list and NOT in the
    English one — the same paper gives two different correct answers depending on which half the
    student reads. Comparing option COUNTS, as the earlier check did, cannot see this.
    """
    oe, oh = q.get("options") or [], q.get("options_hi") or []
    if not oh or len(oe) != len(oh):
        return True
    from collections import Counter
    return all(Counter(_NUM.findall(str(a.get("text", "")))) ==
               Counter(_NUM.findall(str(b.get("text", "")))) for a, b in zip(oe, oh))


def assertion_has_content(q):
    text = " ".join([q.get("stem") or "", q.get("stem_hi") or ""])
    if not _AR_RUBRIC.search(text):
        return True
    return bool(_AR_CONTENT.search(text))


_EXCL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "question_bank_engine", "drop", "bssc", "EXCLUSIONS.json")
_EXCL = None


def excluded(q):
    """Questions verified defective by solving them — see drop/bssc/EXCLUSIONS.json.

    These pass every structural gate and are still wrong on the page (a surd comparison with no
    correct option, a telescoping series whose stem lost its denominators, a match-the-columns
    with Column II truncated). Structure cannot catch them; only working the problem can, so the
    result of having worked it is kept.
    """
    global _EXCL
    if _EXCL is None:
        try:
            spec = json.load(io.open(_EXCL_PATH, encoding="utf-8"))
            _EXCL = {(e["source_pdf"], e["number"]) for e in spec.get("excluded", [])}
            # whole papers whose measured defect rate makes every question in them suspect
            _EXCL |= {(e["source_pdf"], None) for e in spec.get("excluded_sources", [])}
        except Exception:
            _EXCL = set()
    return ((q.get("source_pdf"), q.get("number")) in _EXCL
            or (q.get("source_pdf"), None) in _EXCL)


# Heavy LaTeX is where extraction quietly loses structure: nested surds and long fraction chains
# came through looking plausible but semantically wrong. Four of the seven verified-defective
# questions are of this shape, so treat it as a risk marker for an Inter Level paper.
_HEAVY_LATEX = re.compile(r"\\sqrt\{[^{}]*\\sqrt|(?:\\frac.*){3,}|\\ldots|\.\.\.")


def inter_level_ok(q):
    """Everything the BSSC 2nd Inter Level (02/23-A) prelim syllabus allows, and nothing else.

    Three gates, all measured against the official advertisement rather than assumed:
      - maths must be arithmetic (see inter_level_maths_ok)
      - no computer/IT questions — not a prelim subject
      - no passage-fragment blanks, and nothing that points at a table or figure we do not hold —
        both are unanswerable on the page whatever the official key says
    """
    text = " ".join([q.get("stem") or "", q.get("stem_hi") or ""])
    if _COMPUTER.search(text) or _PASSAGE_BLANK.search(text) or _NEEDS_FIGURE.search(text):
        return False
    if q.get("has_figure"):
        return False
    if not (numbers_agree(q) and option_numbers_agree(q) and assertion_has_content(q)):
        return False
    if excluded(q):
        return False
    if (q.get("tag") or {}).get("section") == "Mathematics" and _HEAVY_LATEX.search(q.get("stem") or ""):
        return False
    # A geometry question can be TAGGED General Studies and so never meet the maths gate — one
    # circle/chord assertion-reason question reached Part I that way. Apply the content gate to GS
    # as well. NOT to General Science: physics legitimately talks about angles, circles and volume.
    if (q.get("tag") or {}).get("section") == "General Studies":
        gs_text = " ".join([q.get("stem") or "", q.get("stem_hi") or ""])
        if _ABOVE_SYLLABUS.search(gs_text) or _ENGLISH_LANG.search(gs_text):
            return False
    return inter_level_maths_ok(q)


def analogy_candidates(stem):
    """Every defensible answer to 'a : b :: c : ?', as strings.

    A number analogy is only sound if exactly ONE of its defensible answers appears among the
    options. "5 : 25 :: 4 : ?" is both 4-squared (16) and 4x5 (20); when the paper offers both, a
    student who reasons "x5" is marked wrong for a correct inference. The question is the defect,
    not the student.
    """
    m = re.search(r"(\d+)\s*:\s*(\d+)\s*::\s*(\d+)\s*:\s*\?", stem or "")
    if not m:
        return set()
    a, b, c = (int(x) for x in m.groups())
    out = {str(c + (b - a))}
    if a:
        if b % a == 0:
            out.add(str(c * (b // a)))
        if a * a == b:
            out.add(str(c * c))
        if a ** 3 == b:
            out.add(str(c ** 3))
        # Triangular numbers. "5 : 15 :: 7 : ?" reads as x3 (21) and equally as the sum 1..n
        # (T5=15, so T7=28) — and the paper offered BOTH. Found by a blind solve after the other
        # gates passed it, which is the whole argument for re-solving rather than re-checking.
        if b == a * (a + 1) // 2:
            out.add(str(c * (c + 1) // 2))
        if b == a * a + a:                      # n(n+1), the other common "sum" reading
            out.add(str(c * c + c))
        if b == a * a - a:
            out.add(str(c * c - c))
        if b == 2 * a + 1:                       # rules added to _b_number_analogy
            out.add(str(2 * c + 1))
    return out


_ODD_TESTS = (
    ("perfect square", lambda n: _isqrt(n) ** 2 == n),
    ("prime", lambda n: n > 1 and all(n % d for d in range(2, _isqrt(n) + 1))),
    ("even", lambda n: n % 2 == 0),
    ("perfect cube", lambda n: round(n ** (1 / 3)) ** 3 == n),
    ("multiple of 3", lambda n: n % 3 == 0),
    ("multiple of 5", lambda n: n % 5 == 0),
)


def _isqrt(n):
    import math
    return int(math.isqrt(n)) if n >= 0 else 0


def odd_one_out_ambiguous(q):
    """True when two DIFFERENT numbers are each singled out by a simple rule, and both are offered.

    "99, 16, 49, 121" was keyed 99 as the only non-square — sound. But 16 is the only even number
    in the set, and 16 was also on the option list, so a student who reasons by parity is marked
    wrong for a correct inference. Same defect as an ambiguous analogy, and it took a blind solve
    to see it: the intended rule always looks like the only rule to whoever wrote the question.
    """
    nums = [int(x) for x in re.findall(r"\b(\d+)\b", q.get("stem") or "")]
    nums = [n for n in nums if n > 4]
    if len(nums) != 4 or not re.search(r"odd one out|alike", q.get("stem") or "", re.I):
        return False
    singled = set()
    for _, test in _ODD_TESTS:
        flags = [test(n) for n in nums]
        if flags.count(True) == 3:
            singled.add(nums[flags.index(False)])
        elif flags.count(False) == 3:
            singled.add(nums[flags.index(True)])
    printed = {re.sub(r"\s+", "", str(o.get("text", ""))) for o in q.get("options") or []}
    return len({n for n in singled if str(n) in printed}) > 1


def analogy_ambiguous(q):
    """True if two defensible analogy answers are both on offer."""
    cands = analogy_candidates(q.get("stem"))
    if len(cands) < 2:
        return False
    printed = {re.sub(r"\s+", "", str(o.get("text", ""))) for o in q.get("options") or []}
    return len(cands & printed) > 1
