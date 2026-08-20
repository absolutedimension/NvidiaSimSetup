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
