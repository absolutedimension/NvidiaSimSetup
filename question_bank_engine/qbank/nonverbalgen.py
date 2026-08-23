"""COMPUTE-THE-ANSWER non-verbal reasoning — गैर-शाब्दिक (आकृति श्रृंखला).

The last question family the real BSSC papers use that this bank could not generate, and the
reason it could not is that every other builder here produces TEXT. A figure series has to be
DRAWN, and the answer options are pictures rather than words.

THE SAME PRINCIPLE AS THE REST OF THE BANK, applied to a picture. We do not ask a model to draw
an SVG and guess what it means. A figure is a SPEC — a rotation, a mirror flag, a count — and the
SVG is rendered FROM that spec. The next figure in a series is computed from the spec by
arithmetic, then drawn. So the picture is correct because we drew it and the key is correct
because Python computed it, exactly as with quantgen. It is also copyright-clean: these are our
own shapes, not scans of anyone's book.

WHY AN ASYMMETRIC GLYPH. A figure series is only answerable if the reader can tell one rotation
from another, and a shape with rotational symmetry cannot: a square rotated 90 degrees is the same
square, so four of the options would be identical pictures and the question would have no answer.
The glyph below is deliberately asymmetric in BOTH axes — an arrow with a single flag on one side
— so every one of the eight 45-degree positions renders differently, and a mirrored figure is
distinguishable from every rotation of the original. That is a correctness requirement, not a
style choice.

Independent re-derivation: the rotation is written into the rendered SVG as a `data-rot`
attribute, so `test_papers.py` can read the PRINTED figure back, fit the progression itself and
check the key without consulting this module. See solve_figure_series there.
"""
import random

# The drawing area of one cell, in user units. Everything below is expressed in this box so a
# figure can be re-scaled by changing only the viewBox on the way out.
BOX = 100
_CX = _CY = BOX / 2

# One asymmetric glyph, drawn once at 0 degrees and then rotated. Coordinates are deliberate:
# the shaft is off-centre and the flag sits on one side only, so no rotation of the glyph can be
# mistaken for its own mirror image.
_GLYPH = (
    '<line x1="20" y1="50" x2="80" y2="50" />'          # shaft
    '<polygon points="80,50 64,41 64,59" />'            # head
    '<polyline points="34,50 34,26 52,26" />'           # flag, one side only
    '<circle cx="24" cy="50" r="4" />'                  # tail dot
)


def _cell(rot, mirrored=False, dots=0, size=54):
    """One figure as a self-contained SVG.

    `data-rot` and `data-mirror` are written into the markup on purpose: they are what lets an
    independent solver read the printed page back. They are attributes, not visible content, so
    a candidate sees only the picture.
    """
    t = f"rotate({rot % 360} {_CX} {_CY})"
    if mirrored:
        # Reflect in the vertical axis BEFORE rotating, so "mirrored" means the same thing at
        # every angle. Composed the other way round, a mirror of a rotation is a rotation of a
        # mirror by a different angle, and the distractor stops being the mistake it is named for.
        t = f"{t} translate({BOX} 0) scale(-1 1)"
    extra = "".join(
        f'<circle cx="{18 + 12 * i}" cy="88" r="3.4" />' for i in range(dots))
    return (f'<svg class="fig" viewBox="0 0 {BOX} {BOX}" width="{size}" height="{size}" '
            f'data-rot="{rot % 360}" data-mirror="{1 if mirrored else 0}" data-dots="{dots}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="2" y="2" width="{BOX - 4}" height="{BOX - 4}" class="figbox" />'
            f'<g transform="{t}" class="figink">{_GLYPH}</g>{extra}</svg>')


def _spec_eq(a, b):
    """Two figures are the SAME PICTURE when their spec matches. Compared on the spec rather than
    on the rendered string because the string carries a size attribute that varies by position."""
    return (a[0] % 360, a[1], a[2]) == (b[0] % 360, b[1], b[2])


def _b_figure_series(rng, diff):
    """आकृति श्रृंखला — four figures, choose the fifth.

    diff 1  a constant 90-degree turn
    diff 2  a constant 45-degree turn: eight positions instead of four
    diff 3  a turn AND a growing dot count — two rules running at once
    diff 4+ a turn with a mirror on alternate steps

    Distractors are the mistakes a candidate actually makes, in the sense quantgen.mistakes means:
    continuing one step too far, repeating the last figure, turning the wrong way, or mirroring.
    Each is a real reading of the same series, not a nudge of the answer.
    """
    step = {1: 90, 2: 45}.get(diff, rng.choice([45, 90]))
    start = rng.choice([0, 45, 90, 135, 180, 225, 270, 315])
    direction = rng.choice([1, -1])
    grow = diff == 3
    alt_mirror = diff >= 4

    def spec(i):
        return (start + direction * step * i,
                bool(alt_mirror and i % 2),
                (i + 1) if grow else 0)

    shown = [spec(i) for i in range(4)]
    answer = spec(4)

    cands = [
        ("continued the series one step too far", spec(5)),
        ("repeated the last figure instead of continuing", spec(3)),
        ("turned the figure the wrong way", (start - direction * step * 4,
                                             answer[1], answer[2])),
        ("mirrored the correct figure", (answer[0], not answer[1], answer[2])),
        ("kept the count of the last figure", (answer[0], answer[1], max(0, answer[2] - 1))),
        ("turned by one step instead of by the whole series", (shown[3][0] + direction * step * 2,
                                                               answer[1], answer[2])),
    ]
    picked, seen = [], [answer]
    for why, sp in cands:
        if any(_spec_eq(sp, s) for s in seen):
            continue          # a "mistake" that lands on the answer is not a distractor
        seen.append(sp)
        picked.append((why, sp))
        if len(picked) == 3:
            break
    if len(picked) < 3:
        return None           # degenerate draw; the caller asks again

    stem = ("Study the following series of figures and choose the one that comes next.")
    stem_hi = ("निम्नलिखित आकृति-श्रृंखला का अध्ययन कीजिए तथा बताइए कि अगली आकृति कौन-सी होगी।")
    rule = (f"The figure turns {step} degrees "
            + ("clockwise" if direction > 0 else "anticlockwise") + " at each step"
            + (", and gains one dot" if grow else "")
            + (", and is mirrored on alternate steps" if alt_mirror else "") + ".")
    # Built by appending to a list, not with a chain of `+ ... if ... else ""`. Written that way
    # the whole expression binds as `(a + b) if grow else ""`, so on every paper WITHOUT dots the
    # entire Hindi rule was replaced by an empty string and the solution printed as a bare
    # "। अतः पाँचवीं आकृति 45 अंश पर होगी।" — a stray danda and no rule. Three of the four
    # difficulty bands were affected and the English was fine, which is how it stayed invisible.
    _hi = [f"प्रत्येक चरण में आकृति {step} अंश "
           + ("दक्षिणावर्त" if direction > 0 else "वामावर्त") + " घूमती है"]
    if grow:
        _hi.append("तथा प्रत्येक चरण में एक बिंदु बढ़ता है")
    if alt_mirror:
        _hi.append("तथा एकांतर चरणों में इसका दर्पण-प्रतिबिंब बनता है")
    rule_hi = ", ".join(_hi)
    return {
        "stem": stem, "stem_hi": stem_hi,
        "figures": shown, "correct_spec": answer,
        "options": [answer] + [sp for _w, sp in picked],
        "why": ["the correct continuation"] + [w for w, _s in picked],
        "solution": rule + f" The fifth figure is therefore at {answer[0] % 360} degrees.",
        "solution_hi": rule_hi + f"। अतः पाँचवीं आकृति {answer[0] % 360} अंश पर होगी।",
        "concept": "Figure Series",
    }


def render(fig_spec, size=54):
    return _cell(*fig_spec, size=size)


if __name__ == "__main__":
    rng = random.Random(0)
    cells = []
    for d in (1, 2, 3, 4):
        q = _b_figure_series(rng, d)
        seq = "".join(render(f) for f in q["figures"])
        opt = "".join(f'<span style="margin:0 10px">({l}) {render(o, 46)}</span>'
                      for l, o in zip("ABCD", q["options"]))
        cells.append(f"<h3>difficulty {d} — {q['concept']}</h3><p>{q['stem']}</p>"
                     f"<div>{seq}</div><div style='margin-top:8px'>{opt}</div>"
                     f"<p><i>{q['solution']}</i></p>")
    open("/tmp/figpreview.html", "w").write(
        "<style>.fig{border:0}.figbox{fill:none;stroke:#bbb;stroke-width:2}"
        ".figink{fill:none;stroke:#111;stroke-width:5;stroke-linecap:round}"
        ".figink polygon,.figink circle{fill:#111}</style>" + "".join(cells))
    print("wrote /tmp/figpreview.html")
