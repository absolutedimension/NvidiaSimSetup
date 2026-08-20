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
        t = re.sub(r"\\" + k + r"\b", v, t)
    t = re.sub(r"\^\s*\{([^{}]*)\}", r"<sup>\1</sup>", t)
    t = re.sub(r"\^\s*(-?\w)", r"<sup>\1</sup>", t)
    t = re.sub(r"_\s*\{([^{}]*)\}", r"<sub>\1</sub>", t)
    t = re.sub(r"_\s*(\w)", r"<sub>\1</sub>", t)
    t = t.replace("\\%", "%").replace("\\$", "$")
    t = re.sub(r"\\[a-zA-Z]+", "", t)                     # drop anything unrecognised
    return t.replace("{", "").replace("}", "")


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
  | बहुपद | द्विघात | समान्तर\ श्रेणी | त्रिकोणमिति | वृत्त | त्रिज्या | परिधि | क्षेत्रफल
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
_COMPUTER = re.compile(r"MS[- ]?Word|MS[- ]?Excel|PowerPoint|\bkeyboard\b|shortcut|\bsoftware\b"
                       r"|\bhardware\b|\bcomputer\b|Ctrl\s*\+|\bRAM\b|\bCPU\b|operating\s+system"
                       r"|कंप्यूटर|कम्प्यूटर", re.I)

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
    return inter_level_maths_ok(q)
