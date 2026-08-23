#!/usr/bin/env python3
"""build_chapter_map.py — map each OFFICIAL syllabus chapter to the KB themes that can answer it.

WHY
---
The picker offers real syllabus chapters ("Poonam's Day Out", "Water O' Water!") because the
curriculum cells are transcribed from the official books (each cell carries its source URL and a
verified_on date). The knowledge bases, however, tag facts THEMATICALLY ("Plants", "Water",
"Animals") — deliberately, because one KB serves CBSE, ICSE and Bihar Board, whose chapter names
differ. Only 2 of 24 chapter names happened to match a theme string, so picking a chapter silently
served the general pool.

This builds the missing layer: per board+class+subject, official chapter -> [KB themes].

HOW
---
Each chapter is scored against each theme by vocabulary overlap:
  chapter text = chapter name + its official subtopics
  theme text   = theme name + the names/labels/members/statements of every KB entry tagged with it
A theme is accepted for a chapter when it clears MIN_SCORE and is close to that chapter's best
theme. Chapters that clear nothing are written with an EMPTY theme list on purpose — serving
"mixed practice" and saying so is honest; quietly serving off-topic questions is not.

    python3 kids_quiz/tools/build_chapter_map.py            # write the maps
    python3 kids_quiz/tools/build_chapter_map.py --show cbse_class3_evs   # inspect one

Output: kids_quiz/chapter_map/<board>_class<N>_<subject>.json  (copy into lms/app/kidsengine/)
Hand-edit any mapping that looks wrong — this file is data, and the tool never overwrites a
chapter whose entry carries "locked": true.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # kids_quiz/
sys.path.insert(0, ROOT)
import kb_engine as KB                            # noqa: E402
import worksheet_engine as WE                     # noqa: E402

CURDIR = os.path.join(ROOT, "curriculum")
OUTDIR = os.path.join(ROOT, "chapter_map")
SUBJECT_KB = {"EVS": "evs", "English": "english", "GK": "gk", "Hindi": "hindi"}

MIN_SCORE = 0.10          # below this, a theme is not credibly about the chapter
NEAR_BEST = 0.55          # keep themes scoring at least this fraction of the chapter's best

STOP = set("""a an the and or of in on at to for with from is are was were be being been this that these
those it its his her their our your my we you they he she i as by if then than so such into over under
about above below up down out off again more most some any all each few other own same too very can will
just not no nor only which who whom what when where why how do does did doing done make makes making use
uses using used around near far new old big small good great day days life live living things thing""".split())


def norm(s):
    """words → lowercase, punctuation-free, crudely singularised, stopwords dropped."""
    words = re.findall(r"[^\W\d_]+", str(s).lower(), flags=re.UNICODE)
    out = set()
    for w in words:
        if len(w) < 3 or w in STOP:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("es") and not w.endswith("ses"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def theme_vocab(kb):
    """theme -> the set of words that theme actually talks about (its own entries' vocabulary)."""
    vocab = {}

    def add(theme, *chunks):
        v = vocab.setdefault(str(theme or "").strip() or "General", set())
        v |= norm(theme)
        for c in chunks:
            v |= norm(c)

    for c in kb.get("categories", []):
        add(c.get("chapter"), c.get("name"), c.get("label"), " ".join(map(str, c.get("members", []))))
    for g in kb.get("groupings", []):
        members = " ".join(" ".join(map(str, v)) for v in (g.get("bins") or {}).values())
        add(g.get("chapter"), g.get("name"), " ".join((g.get("bins") or {}).keys()), members)
    for r in kb.get("relations", []):
        pairs = " ".join(f"{a} {b}" for a, b in (r.get("pairs") or []))
        add(r.get("chapter"), r.get("name"), r.get("a_label"), r.get("b_label"), pairs)
    for f in kb.get("facts", []):
        add(f.get("chapter"), f.get("statement"))
    return vocab


def idf(vocab):
    """How INFORMATIVE each word is: a word that appears under many themes ("water" shows up in
    Animals, Plants and Water alike) says little about which theme a chapter belongs to. Without
    this, the largest theme simply wins — 'Different kinds of food' was matching Animals purely
    because Animals has the biggest vocabulary."""
    import math
    df = {}
    for words in vocab.values():
        for w in words:
            df[w] = df.get(w, 0) + 1
    n = max(1, len(vocab))
    return {w: math.log(1 + n / c) for w, c in df.items()}


def score(chapter_words, theme_words, weights):
    """Share of the CHAPTER's meaning this theme can cover, weighted by how discriminating each
    shared word is."""
    if not chapter_words or not theme_words:
        return 0.0
    total = sum(weights.get(w, 1.0) for w in chapter_words)
    if not total:
        return 0.0
    return sum(weights.get(w, 1.0) for w in (chapter_words & theme_words)) / total


def build_cell(board, cls, subject, existing=None):
    cell = WE.load_cell(board, cls, subject)
    stem = SUBJECT_KB.get(subject)
    if not cell or not stem:
        return None
    try:
        kb = KB.load_kb(f"{stem}_class{cls}")
    except Exception:
        return None
    vocab = theme_vocab(kb)
    weights = idf(vocab)
    keep = (existing or {}).get("map", {})
    out = {}
    for ch in cell.get("chapters", []):
        cid = ch.get("id") or re.sub(r"\W+", "_", str(ch.get("name", "")).lower()).strip("_")
        if keep.get(cid, {}).get("locked"):
            out[cid] = keep[cid]                        # hand-corrected → never overwrite
            continue
        # name + official subtopics, plus (for Hindi-medium books) the translated title and its
        # concept words — without those, a Devanagari chapter name shares no vocabulary with an
        # English KB theme and every Bihar chapter scored zero.
        words = (norm(ch.get("name", ""))
                 | norm(" ".join(ch.get("subtopics", []) or []))
                 | norm(ch.get("title_en", ""))
                 | norm(" ".join(ch.get("concepts_en", []) or [])))
        scored = sorted(((score(words, tv, weights), t) for t, tv in vocab.items()), reverse=True)
        best = scored[0][0] if scored else 0.0
        themes = [t for sc, t in scored if sc >= MIN_SCORE and sc >= best * NEAR_BEST]
        conf = "high" if best >= 0.25 else ("low" if best >= MIN_SCORE else "none")

        # A chapter that NAMES its concepts outranks any amount of vocabulary overlap. "Different
        # kinds of food" was matching Animals because the word "food" appears in Animals entries
        # (cow → grass), which is lexically true and semantically wrong. When the concepts name a
        # theme, take exactly those; when they name none, a lexical guess has not earned
        # confidence, so cap it — the server then serves it as "partial", never as the chapter.
        concepts = norm(" ".join(ch.get("concepts_en", []) or []))
        if concepts:
            direct = [t for t in vocab if norm(t) & concepts]
            if direct:
                themes, conf = direct, "high"
            else:
                conf = min(conf, "low", key=lambda c: {"high": 2, "low": 1, "none": 0}[c])

        out[cid] = {"name": ch.get("name", ""), "themes": themes,
                    "score": round(best, 3), "confidence": conf}
    matched = sum(1 for v in out.values() if v["themes"])
    return {"board": board, "class": cls, "subject": subject,
            "source": cell.get("source", {}),
            "generated_by": "kids_quiz/tools/build_chapter_map.py",
            "chapters": len(out), "mapped": matched, "map": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", default="", help="print one cell's map instead of writing")
    a = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    boards = [("CBSE", "cbse"), ("ICSE", "icse"), ("Bihar Board", "biharboard")]
    rows = []
    for board, slug in boards:
        for cls in range(1, 6):
            for subject in SUBJECT_KB:
                path = os.path.join(OUTDIR, f"{slug}_class{cls}_{subject.lower()}.json")
                existing = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None
                data = build_cell(board, cls, subject, existing)
                if not data:
                    continue
                if a.show and a.show in os.path.basename(path):
                    print(json.dumps(data, ensure_ascii=False, indent=1))
                    return 0
                if not a.show:
                    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                rows.append((os.path.basename(path)[:-5], data["mapped"], data["chapters"]))
    if a.show:
        print(f"no cell matching {a.show!r}")
        return 1
    tot_m = sum(r[1] for r in rows); tot_c = sum(r[2] for r in rows)
    print(f"{'cell':34} {'mapped':>7} {'chapters':>9}")
    for n, m, c in rows:
        flag = "" if m == c else "   <- some chapters fall back to mixed"
        print(f"{n:34} {m:>7} {c:>9}{flag}")
    print(f"\n{len(rows)} cells · {tot_m}/{tot_c} chapters mapped ({100*tot_m//max(1,tot_c)}%)")
    print(f"written to {OUTDIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
