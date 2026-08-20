#!/usr/bin/env python3
"""Read the answer key back OUT of a delivered paper, and attach each answer's provenance.

Why this reads the delivered file instead of rebuilding. `--pin` was supposed to make a set
reproducible, and for generated questions it is NOT exact: `gen_sig` deliberately ignores the actor
name ("Neha is the daughter of Sunil" vs "Priya is the mother of Amit"), so it identifies a question
SHAPE, not an instance. Measured: 307 signatures, 31 of which resolve to a different concrete
question when the generator is drawn with a different seed. A pinned rebuild of Set 2 therefore came
back with equivalent-but-different reasoning questions — the paper still 150 questions, still all
correct, but no longer the file Rohan is holding.

For a verification sheet that is worthless if it disagrees with the paper in the reader's hand, the
delivered HTML is the only safe source of truth. It carries everything needed:

    - the question number, stem and options, exactly as printed
    - the printed answer letter, from the paper's own key block
    - whether the question was generated, from the `*` the key prints beside it

Provenance is then recovered by matching each printed stem back to where it came from: the official
question bank (giving advertisement + question number + answer-key page) or the generated pool
(giving the worked solution).

`freeze_generated.py` fixes the underlying pin defect. This script is what makes the two sets
already in the institute's hands checkable.

Usage:
    python3 key_from_delivered.py --html OneStep_BSSC_InterLevel_Set2.html --out Set2_key.json
"""
import argparse
import glob
import html as htmllib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paper_common import esc  # noqa: E402

BSSC = os.path.join(HERE, "..", "question_bank_engine", "drop", "bssc")

Q_BLOCK = re.compile(r'<div class="q">(.*?)</div></div>', re.S)
KEY_ITEM = re.compile(r'<span class="k">(\d+)\.\s*<b>([A-D])</b>(<i>\*</i>)?</span>')
OPT_LABEL = re.compile(r'^\s*<b>\(([A-D])\)</b>(.*)$', re.S)
EN_DIV = re.compile(r'<div class="en">(.*?)</div>', re.S)
TAGS = re.compile(r"<[^>]+>")


def text(s):
    """Printed HTML back to plain text, so it can be compared with the source JSON."""
    return re.sub(r"\s+", " ", htmllib.unescape(TAGS.sub("", s))).strip()


def options(block):
    """Every option in a question block, split on the OPENING tag so nesting cannot truncate it.

    A regex ending at `</span>` stopped at the inner span of a stacked fraction: option (A) 1/20
    came back as "1", and K = ½mv² came back as "K = 1". That fed a wrong answer_text onto the
    verification sheet — the one column a reader compares against the paper. ai_verify_paper.py
    keeps its own copy of this; it has to run alone on the VM.
    """
    out = []
    for chunk in block.split('<span class="op">')[1:]:
        m = OPT_LABEL.match(chunk)
        if m:
            out.append((m.group(1), text(m.group(2))))
    return out


def norm(s):
    """Comparison key: case- and punctuation-insensitive, since the renderer typesets maths."""
    return re.sub(r"[^a-z0-9ऀ-ॿ]+", "", str(s or "").lower())


def as_printed(s):
    """A bank string put through the paper's own typesetting, so both sides normalise the same.

    Without this, '(164 \\times 175) \\times ? = 258300' in the bank never matches the '164 × 175'
    the paper prints, and the question falls through to the option-set fallback — which for a
    plain numeric option set like {6, 9, 12, 15} is ambiguous and correctly refuses to guess.
    """
    return norm(text(esc(s)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--freeze-manifest", default=None,
                    help="Also write the delivered paper's generated questions into this "
                         "manifest as `gen_full`, so --pin reproduces the exact file rather than "
                         "an equivalent one. Needs --set.")
    ap.add_argument("--set", type=int, default=None)
    a = ap.parse_args()
    if a.freeze_manifest and a.set is None:
        raise SystemExit("--freeze-manifest needs --set")

    doc = io.open(a.html, encoding="utf-8").read()
    keys = {int(n): (letter, bool(star)) for n, letter, star in KEY_ITEM.findall(doc)}
    blocks = Q_BLOCK.findall(doc)
    if len(blocks) != len(keys):
        raise SystemExit(f"{len(blocks)} question blocks but {len(keys)} key entries — "
                         f"refusing to guess which is right")

    # Index by English stem, and separately by the exact set of option texts. The renderer
    # typesets a stem (LaTeX -> Unicode) so the stem can stop matching; it never rewrites an
    # option's wording, so the option set is the reliable second key.
    real, gen, real_opts, gen_opts = {}, {}, {}, {}

    def index(q, by_stem, by_opts):
        # Index BOTH language fields. The extraction's language labels are unreliable — measured
        # 59% correct, 12% swapped — so `stem` holds the Hindi on some records and the paper's
        # English half came out of `stem_hi`. Routing by script is what the renderer does; here it
        # is simpler and safer to index both and let the printed text find whichever it matches.
        for s, os_ in ((q.get("stem"), q.get("options")),
                       (q.get("stem_hi"), q.get("options_hi"))):
            if s:
                by_stem[as_printed(s)] = q
            keys = frozenset(as_printed(o.get("text")) for o in os_ or [])
            if len(keys) == 4 and "" not in keys:   # degenerate option sets match everything
                by_opts.setdefault(keys, []).append(q)

    for f in sorted(glob.glob(os.path.join(BSSC, "*_KEYED.json"))):
        for q in json.load(io.open(f, encoding="utf-8")):
            index(q, real, real_opts)
    for q in json.load(io.open(os.path.join(BSSC, "REASONING_GEN.json"), encoding="utf-8")):
        index(q, gen, gen_opts)

    rows, unmatched, gen_full = [], 0, []
    for i, block in enumerate(blocks, 1):
        letter, generated = keys[i]
        # the English half is printed last, so its option block is the final one
        opts = options(block)
        answer_text = next((t for lab, t in reversed(opts) if lab == letter), "")
        en = text(EN_DIV.search(block).group(1)) if EN_DIV.search(block) else ""
        en = re.sub(r"^\d+\.\s*", "", en)
        src = (gen if generated else real).get(norm(en))
        if src is None:
            # The renderer typeset the stem, so it no longer matches. Fall back to the exact
            # four-option set — and only when it identifies ONE record. A looser subset match was
            # tried first and was worse than useless: it silently attributed ten questions to a
            # Hindi paper they had nothing to do with, by matching a record whose options were
            # blank. A wrong citation on a verification sheet is the one defect that would
            # destroy the sheet's whole purpose, so an unmatched row is reported, never guessed.
            hits = (gen_opts if generated else real_opts).get(
                frozenset(norm(t) for _, t in opts), [])
            src = hits[0] if len(hits) == 1 else None
        if src is None:
            unmatched += 1
        elif generated:
            gen_full.append({k: v for k, v in src.items() if not k.startswith("_")})
        rows.append({
            "n": i,
            "answer": letter,
            "answer_text": answer_text,
            "generated": generated,
            "stem": en,
            "solution": (src or {}).get("solution"),
            "source_pdf": None if generated else (src or {}).get("source_pdf"),
            "source_number": None if generated else (src or {}).get("number"),
        })

    json.dump(rows, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_gen = sum(1 for r in rows if r["generated"])
    print(f"{len(rows)} questions read from the delivered paper "
          f"({len(rows) - n_gen} official + {n_gen} generated) -> {a.out}")
    if unmatched:
        print(f"  ⚠ {unmatched} could not be traced back to a source record")
    miss_p = sum(1 for r in rows if not r["generated"] and not r["source_pdf"])
    miss_s = sum(1 for r in rows if r["generated"] and not r["solution"])
    print(f"  provenance missing: {miss_p} official | worked solution missing: {miss_s} generated")

    if a.freeze_manifest:
        if len(gen_full) != n_gen:
            raise SystemExit(f"only traced {len(gen_full)} of {n_gen} generated questions — "
                             f"refusing to freeze a partial set")
        man = json.load(io.open(a.freeze_manifest, encoding="utf-8"))
        man[str(a.set)]["gen_full"] = gen_full
        json.dump(man, io.open(a.freeze_manifest, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  froze {len(gen_full)} generated questions into set {a.set} of "
              f"{os.path.basename(a.freeze_manifest)} — --pin will now reproduce this exact file")


if __name__ == "__main__":
    main()
