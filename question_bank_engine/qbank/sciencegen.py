"""COMPUTE-THE-ANSWER General Science engine — physics numericals at the 10+2 level.

The fourth sibling of quantgen, reasoninggen and staticgkgen, and it exists because General Science
was the ONE section with no generator at all: the only science content available was static recall
("what does a barometer measure"), so a fully-generated paper could not fill Part II.

Same discipline as quantgen, for the same reason. The answer is computed in Python from the
quantities in the stem, so it cannot be a model misremembering a fact. The distractors are computed
by performing a NAMED mistake — dropping the ½ from ½mv², reading Ohm's law upside down, combining
series resistances as if they were parallel — so a wrong option is one a candidate actually arrives
at, not a number nudged off the right one.

Scope is Advt 02/23(A)'s General Science at 10+2: motion, work-energy-power, current electricity.
Hindi is a second template over the SAME computation, never a translation, so a number cannot drift
between the two languages.
"""
import hashlib
from fractions import Fraction as F

from .models import Question, content_hash

SUBJECT = "General Science"
EXAM = "BSSC"
_ALIASES = {"general science", "science", "physics", "सामान्य विज्ञान"}


def can_generate(exam, subject, chapter=None) -> bool:
    return (subject or "").strip().lower() in _ALIASES


def _n(x):
    x = float(x)
    return str(int(x)) if x.is_integer() else str(round(x, 2))


def mistakes(*pairs):
    return [{"why": w, "text": str(v)} for w, v in pairs if v is not None and str(v).strip()]


def _q(stem, stem_hi, correct, sol, sol_hi, mis, concept):
    return {"stem": stem, "stem_hi": stem_hi, "correct": correct, "solution": sol,
            "solution_hi": sol_hi, "mistakes": mis, "concept": concept}


def _b_motion(rng, diff):
    """diff 1 speed | 2 km/h -> m/s | 3 average speed over equal halves | 4+ s = ut + ½at²"""
    if diff <= 1:
        d, t = rng.choice([60, 90, 120, 150]), rng.choice([2, 3, 4, 5])
        v = F(d, t)
        return _q(f"A body covers {d} m in {t} seconds. What is its speed?",
                  f"एक वस्तु {t} सेकंड में {d} मीटर की दूरी तय करती है। उसकी चाल क्या है ?",
                  _n(v) + " m/s", f"Speed = distance/time = {d}/{t} = {_n(v)} m/s.",
                  f"चाल = दूरी/समय = {d}/{t} = {_n(v)} मी/से।",
                  mistakes(("divided time by distance", _n(F(t, d)) + " m/s"),
                           ("multiplied instead of dividing", _n(d * t) + " m/s"),
                           ("subtracted the two quantities", _n(abs(d - t)) + " m/s")), "Motion")
    if diff == 2:
        k = rng.choice([18, 36, 54, 72, 90])
        ms = F(k * 5, 18)
        return _q(f"Convert a speed of {k} km/h into metres per second.",
                  f"{k} किमी/घंटा की चाल को मीटर प्रति सेकंड में बदलिए।",
                  _n(ms) + " m/s", f"1 km/h = 5/18 m/s, so {k} x 5/18 = {_n(ms)} m/s.",
                  f"1 किमी/घंटा = 5/18 मी/से, अतः {k} x 5/18 = {_n(ms)} मी/से।",
                  mistakes(("multiplied by 18/5 instead of 5/18", _n(F(k * 18, 5)) + " m/s"),
                           ("divided by 10", _n(F(k, 10)) + " m/s"),
                           ("left the value unchanged", _n(k) + " m/s")), "Motion")
    if diff == 3:
        v1, v2 = rng.choice([(40, 60), (30, 60), (20, 80), (45, 90)])
        avg = F(2 * v1 * v2, v1 + v2)
        return _q(f"A car covers the first half of a journey at {v1} km/h and the second half at "
                  f"{v2} km/h. What is its average speed for the whole journey?",
                  f"एक कार यात्रा का पहला आधा भाग {v1} किमी/घंटा तथा दूसरा आधा भाग {v2} किमी/घंटा "
                  f"की चाल से तय करती है। पूरी यात्रा की औसत चाल क्या है ?",
                  _n(avg) + " km/h",
                  f"For equal distances the average is 2 x {v1} x {v2}/({v1}+{v2}) = "
                  f"{_n(avg)} km/h.",
                  f"समान दूरियों के लिए औसत चाल = 2 x {v1} x {v2}/({v1}+{v2}) = {_n(avg)} किमी/घंटा।",
                  mistakes(("took the plain average of the two speeds", _n(F(v1 + v2, 2)) + " km/h"),
                           ("added the two speeds", _n(v1 + v2) + " km/h"),
                           ("used the faster speed alone", _n(v2) + " km/h")), "Motion")
    a, u, t = rng.choice([2, 4, 6]), rng.choice([5, 10, 15]), rng.choice([3, 4, 5])
    s = u * t + F(a * t * t, 2)
    return _q(f"A body starting with a velocity of {u} m/s accelerates uniformly at {a} m/s² "
              f"for {t} seconds. What distance does it cover?",
              f"{u} मी/से के प्रारंभिक वेग से चलती एक वस्तु {t} सेकंड तक {a} मी/से² के एकसमान "
              f"त्वरण से चलती है। वह कितनी दूरी तय करती है ?",
              _n(s) + " m", f"s = ut + ½at² = {u}x{t} + ½x{a}x{t}² = {_n(s)} m.",
              f"s = ut + ½at² = {u}x{t} + ½x{a}x{t}² = {_n(s)} मीटर।",
              mistakes(("dropped the ½ from ½at²", _n(u * t + a * t * t) + " m"),
                       ("used at instead of ½at²", _n(u * t + a * t) + " m"),
                       ("ignored the initial velocity", _n(F(a * t * t, 2)) + " m")), "Motion")


def _b_ohm(rng, diff):
    """diff 1 V=IR | 2 R=V/I | 3 P=VI | 4+ series resistance, then the current"""
    i, r = rng.choice([2, 3, 4, 5]), rng.choice([4, 5, 6, 10, 12])
    v = i * r
    if diff <= 1:
        return _q(f"A current of {i} A flows through a resistance of {r} ohm. What is the "
                  f"potential difference across it?",
                  f"{r} ओम के प्रतिरोध से {i} ऐम्पियर की धारा प्रवाहित होती है। उसके सिरों पर "
                  f"विभवांतर क्या होगा ?",
                  _n(v) + " V", f"V = IR = {i} x {r} = {v} V.", f"V = IR = {i} x {r} = {v} वोल्ट।",
                  mistakes(("divided instead of multiplying", _n(F(r, i)) + " V"),
                           ("added the two quantities", _n(i + r) + " V"),
                           ("divided the other way round", _n(F(i, r)) + " V")),
                  "Current Electricity")
    if diff == 2:
        return _q(f"A potential difference of {v} V drives a current of {i} A through a "
                  f"conductor. What is its resistance?",
                  f"{v} वोल्ट का विभवांतर किसी चालक में {i} ऐम्पियर की धारा प्रवाहित करता है। "
                  f"उसका प्रतिरोध क्या है ?",
                  _n(r) + " ohm", f"R = V/I = {v}/{i} = {r} ohm.", f"R = V/I = {v}/{i} = {r} ओम।",
                  mistakes(("used I/V instead of V/I", _n(F(i, v)) + " ohm"),
                           ("multiplied V by I", _n(v * i) + " ohm"),
                           ("subtracted the two", _n(abs(v - i)) + " ohm")),
                  "Current Electricity")
    if diff == 3:
        p = v * i
        return _q(f"A device draws {i} A at {v} V. What is the power consumed?",
                  f"कोई उपकरण {v} वोल्ट पर {i} ऐम्पियर धारा लेता है। उसमें व्यय शक्ति कितनी है ?",
                  _n(p) + " W", f"P = VI = {v} x {i} = {p} W.", f"P = VI = {v} x {i} = {p} वाट।",
                  mistakes(("used V/I", _n(F(v, i)) + " W"),
                           ("added V and I", _n(v + i) + " W"),
                           ("used I² alone", _n(i * i) + " W")), "Current Electricity")
    r2 = rng.choice([x for x in (4, 5, 6, 10, 12) if x != r])
    tot = r + r2
    cur = F(v, tot)
    return _q(f"Two resistances of {r} ohm and {r2} ohm are connected in SERIES across a {v} V "
              f"supply. What current flows through the circuit?",
              f"{r} ओम तथा {r2} ओम के दो प्रतिरोध {v} वोल्ट की आपूर्ति के साथ श्रेणीक्रम में जोड़े "
              f"गए हैं। परिपथ में कितनी धारा प्रवाहित होगी ?",
              _n(cur) + " A",
              f"In series R = {r} + {r2} = {tot} ohm; I = V/R = {v}/{tot} = {_n(cur)} A.",
              f"श्रेणीक्रम में R = {r} + {r2} = {tot} ओम; I = V/R = {v}/{tot} = {_n(cur)} ऐम्पियर।",
              mistakes(("combined the resistances as if in PARALLEL",
                        _n(F(v, 1) / F(r * r2, r + r2)) + " A"),
                       ("used only the first resistance", _n(F(v, r)) + " A"),
                       ("multiplied V by R instead of dividing", _n(v * tot) + " A")),
              "Current Electricity")


def _b_work(rng, diff):
    """diff 1 W=Fs | 2 P=W/t | 3 KE=½mv² | 4+ PE=mgh"""
    f_, s = rng.choice([10, 20, 25, 50]), rng.choice([4, 6, 8, 10])
    w = f_ * s
    if diff <= 1:
        return _q(f"A force of {f_} N moves a body through {s} m in its own direction. How much "
                  f"work is done?",
                  f"{f_} न्यूटन का बल किसी वस्तु को अपनी ही दिशा में {s} मीटर विस्थापित करता है। "
                  f"कितना कार्य हुआ ?",
                  _n(w) + " J", f"W = F x s = {f_} x {s} = {w} J.",
                  f"कार्य = बल x विस्थापन = {f_} x {s} = {w} जूल।",
                  mistakes(("divided force by distance", _n(F(f_, s)) + " J"),
                           ("added them", _n(f_ + s) + " J"),
                           ("halved the product", _n(F(w, 2)) + " J")), "Work, Energy & Power")
    if diff == 2:
        t = rng.choice([2, 4, 5, 10])
        p = F(w, t)
        return _q(f"A force of {f_} N moves a body {s} m in {t} seconds. What is the power "
                  f"developed?",
                  f"{f_} न्यूटन का बल किसी वस्तु को {t} सेकंड में {s} मीटर विस्थापित करता है। "
                  f"विकसित शक्ति कितनी है ?",
                  _n(p) + " W", f"W = {f_} x {s} = {w} J; P = W/t = {w}/{t} = {_n(p)} W.",
                  f"कार्य = {f_} x {s} = {w} जूल; शक्ति = {w}/{t} = {_n(p)} वाट।",
                  mistakes(("gave the WORK instead of the power", _n(w) + " W"),
                           ("multiplied by the time instead of dividing", _n(w * t) + " W"),
                           ("divided the force by the time", _n(F(f_, t)) + " W")),
                  "Work, Energy & Power")
    m_, v_ = rng.choice([2, 4, 5, 10]), rng.choice([2, 4, 6, 10])
    if diff == 3:
        ke = F(m_ * v_ * v_, 2)
        return _q(f"What is the kinetic energy of a body of mass {m_} kg moving with a velocity "
                  f"of {v_} m/s?",
                  f"{v_} मी/से के वेग से गतिमान {m_} किग्रा द्रव्यमान की वस्तु की गतिज ऊर्जा "
                  f"कितनी है ?",
                  _n(ke) + " J", f"KE = ½mv² = ½ x {m_} x {v_}² = {_n(ke)} J.",
                  f"गतिज ऊर्जा = ½mv² = ½ x {m_} x {v_}² = {_n(ke)} जूल।",
                  mistakes(("used mv instead of ½mv²", _n(m_ * v_) + " J"),
                           ("forgot the ½", _n(m_ * v_ * v_) + " J"),
                           ("used ½mv instead of ½mv²", _n(F(m_ * v_, 2)) + " J")),
                  "Work, Energy & Power")
    h = rng.choice([5, 10, 20])
    pe = m_ * 10 * h
    return _q(f"A body of mass {m_} kg is raised to a height of {h} m. Taking g = 10 m/s², "
              f"what is its potential energy at that height?",
              f"{m_} किग्रा द्रव्यमान की एक वस्तु को {h} मीटर की ऊँचाई तक उठाया जाता है। "
              f"g = 10 मी/से² लेते हुए उस ऊँचाई पर उसकी स्थितिज ऊर्जा कितनी है ?",
              _n(pe) + " J", f"PE = mgh = {m_} x 10 x {h} = {pe} J.",
              f"स्थितिज ऊर्जा = mgh = {m_} x 10 x {h} = {pe} जूल।",
              mistakes(("left out g", _n(m_ * h) + " J"),
                       ("used ½mgh", _n(F(pe, 2)) + " J"),
                       ("added the quantities", _n(m_ + 10 + h) + " J")), "Work, Energy & Power")


_CHAP_BUILDERS = {"Motion": [_b_motion], "Current Electricity": [_b_ohm],
                  "Work, Energy & Power": [_b_work]}

_UNIT_HI = [("km/h", "किमी/घंटा"), ("m/s", "मी/से"), (" ohm", " ओम"), (" V", " वोल्ट"),
            (" W", " वाट"), (" J", " जूल"), (" A", " ऐम्पियर"), (" m", " मीटर")]


def _hi_opt(t):
    for en, hi in _UNIT_HI:
        if t.endswith(en):
            return t[: -len(en)] + hi
    return t


def _mcq(seed, correct, distractors, n=4):
    opts = list(dict.fromkeys([str(correct)] + [str(d) for d in distractors]))[:n]
    if str(correct) not in opts:
        opts[-1] = str(correct)
    # Backstop. Two computed mistakes can coincide, and a three-option question fails the paper's
    # structure check — which is exactly how this was found. Pad on the numeric part, keeping the
    # unit, so the filler still looks like an answer to this question.
    head = str(correct).split(" ", 1)
    unit = " " + head[1] if len(head) > 1 else ""
    try:
        base = float(head[0])
    except ValueError:
        base = None
    k = 1
    while len(opts) < n and base is not None and k < 40:
        for cand in (base + k, base - k, base * (1 + k)):
            if cand <= 0:
                continue
            t = (str(int(cand)) if float(cand).is_integer() else str(round(cand, 2))) + unit
            if t not in opts:
                opts.append(t)
                break
        k += 1
    rot = sum(map(ord, seed)) % max(len(opts), 1)
    opts = opts[rot:] + opts[:rot]
    labels = ["A", "B", "C", "D"][:len(opts)]
    return ([{"label": l, "text": t} for l, t in zip(labels, opts)],
            labels[opts.index(str(correct))])


def _make_question(built, rng, spec):
    stem = built["stem"].strip()
    mis = [m for m in built.get("mistakes", []) if m["text"] != str(built["correct"])]
    options, ans = _mcq(stem, built["correct"], [m["text"] for m in mis])
    q = Question(
        id="gen_sci_" + hashlib.md5(stem.encode()).hexdigest()[:14],
        exam=spec.get("exam") or EXAM, subject=SUBJECT, stem=stem, qtype="MCQ_single",
        options=options, correct_answer=ans, solution=built.get("solution", ""),
        stem_hi=built.get("stem_hi", ""), solution_hi=built.get("solution_hi", ""),
        options_hi=[{"label": o["label"], "text": _hi_opt(o["text"])} for o in options],
        chapter=spec.get("chapter"), concept=built.get("concept"),
        difficulty=spec.get("dmax") or 2, source="sciencegen", generated=True,
        hash=content_hash(stem))
    q.verified = True
    by = {m["text"]: m["why"] for m in mis}
    q.distractor_why = {o["label"]: by[o["text"]] for o in options if o["text"] in by}
    return q
