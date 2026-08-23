#!/usr/bin/env python3
"""One Step Education — BSSC practice paper, 150 REAL bilingual questions.

Every question here was printed in an official BSSC paper and carries the commission's own
आदर्श उत्तर. Nothing is generated, nothing is translated: the Hindi is the Hindi the commission
printed, which is why each question shows both languages the way the real booklet does.

Section weights follow the measured blueprint of the five official papers we extracted
(GS ~38-51%, Maths ~20-31%, Hindi ~19-31%), NOT the textbook 50/50/50 — because Reasoning only
yielded 17 real questions and padding it with generated ones would break the "every question is
real" claim that makes this paper worth more than a competitor's mock.

Logo: pass --logo <path.png> to brand it with One Step's own mark; without it the name is set
in type. Never invent a client's logo.
"""
import argparse
import base64
import glob
import hashlib
import html
import io
import json
import os
import pathlib
import random
import re
import subprocess
import sys

REPO = pathlib.Path("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup")
sys.path.insert(0, str(REPO / "teacher_gtm"))
from paper_common import (MATH_CSS, esc, servable, sig, inter_level_ok,  # noqa: E402
                          numbers_agree, analogy_ambiguous, odd_one_out_ambiguous)
LET = ["A", "B", "C", "D", "E"]


_DEV = re.compile(r"[\u0900-\u097f]")


# Every actor name reasoninggen can put in a stem (qbank/reasoninggen.py: _MALE, _FEMALE,
# _SEAT_NAMES and the per-builder choices). Stripped before a question's identity is taken — see
# gen_sig. Keep in step with that module: a name missing here is treated as question CONTENT, which
# splits two copies of one question into two.
_ACTORS = re.compile(
    r"\b(?:Ram|Amit|Vikas|Rohan|Arun|Sunil|Rahul|Sita|Priya|Anjali|Meena|Radha|Neha|Sneha|Ravi)\b"
    r"|\bA man\b|\bA boy\b"
    # The PRONOUN moves with the actor — _b_direction_distance writes "she" for Sita and "he" for
    # everyone else — so leaving it in makes the very pair of questions this function exists to
    # collapse look different. It is part of the name, not part of the question.
    r"|\b(?:he|she|his|her|him)\b", re.I)


def _enumerated(stem):
    """True when the stem itself carries a numbered/lettered LIST of claims.

    Matching the WORDING was wrong in both directions and both were live. Listing the two openings
    that existed at the time missed "Study the following statements". Widening it to "following
    statements" then swept in "Which one of the following statements is correct?" — whose claims
    sit in its OPTIONS, leaving a one-line stem, so every question of that form produced the SAME
    signature and all but the first were discarded as duplicates. Measured: 400 builds, 1 distinct
    signature, and the style fell from 6 questions a paper to 1.

    The property that actually matters is whether the enumerated content is in the stem. Test for
    that, not for the sentence that usually introduces it.
    """
    return len(re.findall(r"(?m)^\s*(?:\d+|[A-D])\.\s", stem or "")) >= 2


def gen_sig(q):
    """Identity of a GENERATED question, independent of the name in the English stem.

    reasoninggen varies the actor ("A boy starts..." / "Sita starts...") while keeping the same
    numbers, and the Hindi template carries no name at all — so two such questions are the SAME
    question with byte-identical Hindi. Keying on the English stem let one through into both sets.
    Signature is therefore the concept, the numbers in the question, and the option set.

    ...which is not enough on its own, and the gap was invisible until a question type without
    numbers arrived. A syllogism carries NO digits and always offers the same four rubric options
    ("Only conclusion I follows", ...), so concept+numbers+options is identical for every syllogism
    ever generated: measured, 240 distinct syllogisms and 240 distinct coded inequalities each
    collapsed to ONE signature, and the dedup would have kept one of each. The same defect was
    already live and unnoticed — Direction–Facing has exactly 1 row in a 1,515-row pool for this
    reason.
    So the stem's WORDS are part of the identity too, with the actor names removed first. That
    keeps the original property exactly (the name-only variants still collapse) while letting
    everything that genuinely differs count as different.
    """
    stem = q.get("stem") or ""
    nums = tuple(re.findall(r"\d+", stem))
    opts = tuple(sorted((o.get("text") or "").strip() for o in q.get("options") or []))
    body = re.sub(r"[^a-z]+", "", _ACTORS.sub("", stem).lower())
    # A statement-based question has NOTHING distinguishing in any of those three fields: the
    # concept is fixed, the only "numbers" are the list markers 1, 2, 3, and the options are the
    # same four strings every time. Forty different questions collapsed to ONE signature, so the
    # dedup discarded thirty-nine of them and the General Studies medium band came back with 1
    # question where 8 were asked. For these, the CLAIMS are the identity.
    #
    # Matched on the SHAPE of the wording, not on a list of stems. It first listed the two openings
    # that existed when it was written, so "Study the following statements" — the count-the-correct
    # -statements form, added later — fell through to the generic branch, where its only digits are
    # the list markers 1, 2, 3 and its options are four fixed rubric strings. That is precisely the
    # collapse this branch exists to prevent, and it went unnoticed because a paper only trips it
    # when two such questions happen to carry no other numbers.
    if _enumerated(stem):
        claims = re.sub(r"(?m)^\s*(?:\d+|[A-D])\.\s*", "", stem)
        claims = re.sub(r"[^a-z0-9\u0900-\u097f]+", "", claims.lower())
        return "|".join([str(q.get("concept") or ""), claims])
    return "|".join([str(q.get("concept") or q.get("qtype") or ""), ",".join(nums),
                     "~".join(opts), body])


def template_sig(q):
    """The SHAPE of a question — its stem with every number replaced by '#'.

    This is deliberately the OPPOSITE of `gen_sig`. gen_sig keeps two questions apart when their
    numbers differ, because they are two different questions to mark. template_sig collapses them
    together, because they are the same question to READ — and reading is what the customer does.

    A delivered paper printed SEVEN CONSECUTIVE questions of the form "(x)^2 + a/b - p% of c".
    gen_sig saw seven distinct questions and was right; every structural check passed. What no
    check measured was that a reader sees one question asked seven times. Part III has had a
    per-concept cap since the owner complained about clustering there; Part II had nothing.
    """
    stem = re.sub(r"<[^>]+>", "", str(q.get("stem") or ""))
    return re.sub(r"\s+", " ", re.sub(r"\d+(?:\.\d+)?", "#", stem)).strip()


def _run_cost(bands):
    """Sum of squared hard-run lengths — one wall of 9 costs far more than three runs of 3."""
    return sum(len(m.group()) ** 2 for m in re.finditer(r"H+", bands))


def break_hard_runs(blocks, limit=4):
    """Cap how many hard questions can appear back to back ANYWHERE in the paper.

    `blocks` are the units a question may move WITHIN — Part I, Part II's science slice, Part II's
    maths slice, Part III — in printed order. The runs are measured across the whole concatenated
    paper, because that is how a candidate reads it, but a swap never crosses a block. The first
    version took whole SECTIONS as the unit and promptly undid a deliberate decision: Part II
    stopped opening with its science block, because a maths question had been swapped in front of
    it. Measuring globally and moving locally is the whole trick.

    Each block is paced independently by `spread_questions`, so a block that ends hard followed by
    one that begins hard produces a run neither block can see. Measured on the first build at 75%
    hard: EIGHT consecutive hard questions across the Part I / Part II boundary — evenly spread
    inside each section, and a wall to a candidate reading straight through, which is the only way
    the paper is ever read.

    A phase offset per block was tried first and made it NINE, because where a boundary lands
    depends on both blocks' band counts and I was guessing. This measures instead: it only ever
    accepts a swap that lowers the sum of squared run lengths, so it cannot oscillate and cannot
    make the paper worse.
    """
    secs = blocks
    off, n = [], 0
    for items in secs:
        off.append(n)
        n += len(items)
    # The band string is carried and mutated rather than rebuilt from the questions for every
    # candidate swap — there are tens of thousands of candidates and rebuilding made the pass the
    # slowest thing in the build.
    b = ["H" if _band(q) == 3 else "-" for items in secs for q in items]

    for _ in range(400):
        s = "".join(b)
        if max((len(m.group()) for m in re.finditer(r"H+", s)), default=0) <= limit:
            break
        best, best_cost = None, _run_cost(s)
        for si, items in enumerate(secs):
            hard = [i for i in range(len(items)) if b[off[si] + i] == "H"]
            soft = [i for i in range(len(items)) if b[off[si] + i] != "H"]
            for i in hard:
                gi = off[si] + i
                for j in soft:
                    gj = off[si] + j
                    b[gi], b[gj] = b[gj], b[gi]
                    c = _run_cost("".join(b))
                    b[gi], b[gj] = b[gj], b[gi]
                    if c < best_cost:
                        best, best_cost = (si, i, j), c
        if not best:
            break                       # nothing left that improves it
        si, i, j = best
        secs[si][i], secs[si][j] = secs[si][j], secs[si][i]
        b[off[si] + i], b[off[si] + j] = b[off[si] + j], b[off[si] + i]
    return blocks


def ask_style(stem):
    """Which of the commission's ASKING styles a question is in — the same buckets the real papers
    were classified into, so target and outcome are measured on one ruler."""
    t = re.sub(r"\s+", " ", str(stem or "").strip())
    low = t.lower()
    if re.search(r"statement", low) and re.search(r"(?:^|\s)(?:\d+|[ivx]+)[.)]\s", t):
        return "statement-list"
    if re.search(r"match|list[- ]?i\b|column", low):
        return "match-list"
    if re.search(r"_{2,}", t):
        return "fill-in-blank"
    if re.search(r"\bnot\b|\bexcept\b|incorrect|mismatch|\bwrong\b|\bodd\b", low):
        return "negative-select"
    if re.search(r"which of the following|which one of the following", low):
        return "which-of-following"
    if re.search(r"^(what|who|when|where|why|how|whom|whose|in which|by whom|name the)\b", low):
        return "direct-wh"
    if re.search(r"\bwhich\b", low):
        return "embedded-which"
    if not t.endswith("?"):
        return "sentence-completion"
    return "other"


def question_topics(q):
    """The SYLLABUS topics a question examines, as (english, hindi) pairs.

    Not the same thing as its concept. The concept is what we built ("Simplification (BODMAS)",
    "Correctly Matched Pair"); the topic is what the commission's own advertisement names
    (पूर्ण संख्याओं का अभिकलन, राजधानी / मुद्रा). Only the second one can show whether a paper
    covers the syllabus, because only the second one has the syllabus as its denominator.

    A General Studies statement question genuinely spans up to THREE topics — it draws a separate
    fact table per statement — so this returns a list, not one value, and the coverage table counts
    every topic a question touches. Pretending such a question has a single topic would report a
    distribution the paper does not have.
    """
    import syllabus_blueprint as SB
    sec = (q.get("tag") or {}).get("section") or ""
    # A REAL question has no `src` and no generator `concept` — it carries the tagger's own topic
    # label ("Current Affairs - National", "Bihar Polity/Schemes"). Those are what bring the
    # topics no generator can make, so without this the whole real half of a paper reported as
    # "अन्य": Part I showed ONE topic on a paper that actually covered twelve.
    keys = list(q.get("src") or []) or [q.get("concept") or "?"]
    # `effective_topic` first: the tagger writes "Other" whenever its GK-oriented taxonomy has no
    # bucket, which on the real MATHS questions is 255 of them. tag_bssc already knows how to
    # derive a usable topic from the question TYPE in that case, and the blueprint mining uses it —
    # the paper simply never did, so 30 of Part II reported as "अन्य".
    tag = q.get("tag") or {}
    rt = tag.get("topic")
    if (not rt or rt == "Other") and tag.get("type"):
        try:
            from qbank_tag_bridge import effective_topic as _et
            rt = _et(tag)
        except Exception:
            try:
                sys.path.insert(0, str(REPO / "question_bank_engine"))
                from tag_bssc import effective_topic as _et
                rt = _et(tag)
            except Exception:
                pass
    if rt and not q.get("src") and not q.get("concept"):
        mapped = (SB.load().get("_real_topic_map") or {}).get(rt)
        if mapped:
            keys = [mapped]
    out = []
    for k in keys:
        for s in (sec, "General Studies", "Mathematics", "Reasoning", "General Science"):
            t = next((t for t in SB.topics(s)
                      if k == t["en"] or k in (t.get("concepts") or [])
                      or k in (t.get("builders") or [])), None)
            if t:
                if (t["en"], t["hi"]) not in out:
                    out.append((t["en"], t["hi"]))
                break
    return out


def short_hi(hi):
    """A syllabus topic short enough for a per-question badge.

    The full names are the commission's own and belong in the coverage table, where there is room
    for them — "भारत का संविधान एवं राज्य व्यवस्था" is right there and unreadable in a 150px badge.
    Cut at the first separator rather than at a character count, so the label always ends on a word.
    """
    s = str(hi).split(" / ")[0].strip()
    for sep in (" एवं ", " तथा "):
        if len(s) > 24 and sep in s:
            s = s.split(sep)[0].strip()
    return s


def coverage_table(items, with_difficulty=True):
    """A topic x difficulty grid for one section, as printable HTML.

    150 badges tell you what each question IS; only a table tells you what the SECTION is. Both of
    the owner's complaints — "only one topic", "style is similar" — are properties of the section,
    invisible while reading any single question, and obvious in three lines of a table. So the
    table carries the two counts that would have caught them: questions per syllabus topic, and
    how many DISTINCT question types the section used.

    Topic counts sum to MORE than the section size when a General Studies statement question draws
    three tables. That is stated in the caption rather than hidden by picking one topic per
    question, because the alternative is a tidy number that is not true.
    """
    from collections import Counter
    per_topic, per_band, types = Counter(), {}, Counter()
    for q in items:
        b = _band(q)
        types[str(q.get("concept") or "?")] += 1
        for _en, hi in question_topics(q) or [("?", "अन्य")]:
            per_topic[hi] += 1
            per_band.setdefault(hi, Counter())[b] += 1
    if not per_topic:
        return ""
    if not with_difficulty:
        body = "".join(f'<tr><td>{esc(hi)}</td><td class="n"><b>{n}</b></td></tr>'
                       for hi, n in per_topic.most_common())
        note = (f"एक प्रश्न एक से अधिक विषय छू सकता है, अतः विषय-योग {sum(per_topic.values())} है। "
                if sum(per_topic.values()) != len(items) else "")
        return (f'<table class="cov"><caption>विषय-वार वितरण / Topic distribution — '
                f'{len(items)} प्रश्न, {len(per_topic)} विषय। {note}'
                f'{len(types)} प्रश्न-प्रकार / question types.</caption>'
                f'<tr><th>विषय / Topic</th><th class="n">प्रश्न</th></tr>{body}</table>')
    rows = ""
    for hi, n in per_topic.most_common():
        c = per_band[hi]
        rows += (f'<tr><td>{esc(hi)}</td><td class="n">{c[1]}</td><td class="n">{c[2]}</td>'
                 f'<td class="n">{c[3]}</td><td class="n"><b>{n}</b></td></tr>')
    tot = Counter(_band(q) for q in items)
    # The band columns count QUESTIONS here but topic TOUCHES above, so the row is labelled for
    # what it is. A total that silently means something different from the column above it is the
    # kind of tidy number this file has been burned by before.
    rows += (f'<tr><th>कुल प्रश्न / Questions</th><th class="n">{tot[1]}</th><th class="n">{tot[2]}</th>'
             f'<th class="n">{tot[3]}</th><th class="n">{len(items)}</th></tr>')
    top = types.most_common(1)[0]
    return (f'<table class="cov"><caption>विषय-वार एवं कठिनाई-वार वितरण / Topic &amp; difficulty '
            f'spread — {len(types)} distinct question types, most-used {top[1]}&times; '
            f'({esc(top[0])}). एक प्रश्न एक से अधिक विषय छू सकता है, अतः विषय-योग '
            f'{sum(per_topic.values())} है।</caption>'
            f'<tr><th>विषय / Topic</th><th class="n">सरल</th><th class="n">मध्यम</th>'
            f'<th class="n">कठिन</th><th class="n">कुल</th></tr>{rows}</table>')


def _band(q):
    """1 easy / 2 medium / 3 hard — the three bands the difficulty badge prints."""
    d = (q.get("tag") or {}).get("difficulty") or q.get("difficulty") or 2
    try:
        d = int(d)
    except (TypeError, ValueError):
        d = 2
    return 3 if d >= 3 else (1 if d <= 1 else 2)


def spread_questions(items, rng, phase=0.5):
    """Order a section on three axes at once: DIFFICULTY, CONCEPT and SHAPE.

    Difficulty is the primary one, and it is here because of the survey. Asked "where should the
    hard questions sit", the answer was **"spread evenly through the paper"** — and the builder did
    no difficulty ordering whatsoever, so where a hard question landed was a side effect of the
    draw. At 75% hard that matters more, not less: the fifteen easy questions are the only places a
    weaker student gets a foothold, and all fifteen arriving together is a different paper from
    fifteen spaced through the section.

    So at each slot, take the band that is furthest BEHIND an even spacing — the k-th question of a
    band belongs at (k + ½)·N/n_band — then inside that band prefer a concept that is not the one
    just printed, and among those a question whose shape is not the one just printed.

    Concept and shape are the other two axes, and they are here because clustering has levels and
    fixing one moves the problem up. Spreading by shape alone was tried first and the rebuilt page
    came back with ten consecutive computation questions — ten genuinely different shapes, which a
    reader still experiences as "ten sums in a row". That is the owner's "it contains only one
    topic" complaint one level above where it was first found.

    All three are the standard greedy spread: optimal whenever a conflict-free ordering exists, and
    degrading to "as separated as possible" when one does not — which is what a section with a
    dominant concept, or with 75% of its questions in one band, actually needs.

    `phase` shifts where a band's first and last questions fall inside the block. Sections are
    paced INDEPENDENTLY, so with the same phase every block ends hard and the next begins hard: the
    first build put EIGHT consecutive hard questions across the Part I/Part II boundary, evenly
    spread within each section and a wall to anyone reading straight through. Alternating the phase
    between blocks makes them meet on an easier question.
    """
    from collections import Counter, defaultdict
    buckets = defaultdict(list)
    for q in items:
        # The spread key is the style AND the fact table it drew from. Style alone was enough
        # while each style had one look; once "Sentence Completion" became 38% of Part I it
        # covered "छऊ नृत्य है —", "गरबा नृत्य है —" and "संविधान का अनुच्छेद 356 संबंधित है —"
        # alike, and the page came back with three dance completions in four questions. What a
        # reader experiences as "the same question again" is the table plus the phrasing.
        key = str(q.get("concept") or "?") + "|" + ",".join(q.get("src") or [])
        buckets[(_band(q), key)].append(q)

    for key, qs in list(buckets.items()):                  # shapes round-robin inside each bucket
        shapes = defaultdict(list)
        for q in qs:
            shapes[template_sig(q)].append(q)
        for v in shapes.values():
            rng.shuffle(v)
        order, dealt = sorted(shapes, key=lambda s: (-len(shapes[s]), s)), []
        while any(shapes[s] for s in order):
            for s in order:
                if shapes[s]:
                    dealt.append(shapes[s].pop())
        buckets[key] = dealt

    n = len(items)
    total = Counter(_band(q) for q in items)
    taken, out, prev_c, prev_s = Counter(), [], None, None
    for i in range(n):
        avail = [b for b in total if taken[b] < total[b]]
        # how far past its even-spacing slot this band's next question already is
        # JITTER, and it is not decoration. Perfectly even spacing over regular band counts IS a
        # cycle: Part I came out 20 easy / 20 medium / 10 hard and the printed difficulty string had
        # an EXACT period of 5 — M-E-H-M-E repeating for all fifty questions — while the statement
        # style landed on questions 3, 8, 13, 18, 23, 28, every fifth one without a single miss.
        # The institute's owner spotted it by eye: "ye machine se bana lag raha hai", and a student
        # who notices can predict whether question 33 is hard before reading it.
        #
        # Half a slot of seeded noise swaps neighbours that were already near-tied, so the spacing
        # stays even ON AVERAGE and stops being predictable. Seeded, so a rebuild reproduces, and
        # break_hard_runs still caps any run the jitter lengthens.
        # Prefer a band that can still offer something OTHER than what was just printed. The
        # jitter can otherwise land on a band whose only remaining bucket is the previous one,
        # forcing an adjacent repeat that the concept filter below is then powerless to avoid —
        # measured at 4 such pairs, against 0 before the jitter was added.
        free = [b for b in avail
                if any(c != prev_c for (bb, c) in buckets if bb == b and buckets[(bb, c)])]
        b = max(free or avail,
                key=lambda b: (i - (taken[b] + phase) * n / total[b] + rng.uniform(-.5, .5),
                               -total[b], b))
        cs = [c for (bb, c) in buckets if bb == b and buckets[(bb, c)]]
        pick = [c for c in cs if c != prev_c] or cs
        pick = [c for c in pick if template_sig(buckets[(b, c)][0]) != prev_s] or pick
        # Ties on "most remaining" used to fall to alphabetical order, which is another fixed
        # cycle. Break them randomly instead.
        c = max(pick, key=lambda c: (len(buckets[(b, c)]), rng.random()))
        q = buckets[(b, c)].pop(0)
        out.append(q)
        taken[b] += 1
        prev_c, prev_s = c, template_sig(q)
    return out


def qid(q):
    """Identity of a real question: its number within its source booklet."""
    return [q.get("number"), q.get("source_pdf")]


def load_manifest(path):
    try:
        return json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return {}


def taken_by_other_sets(manifest, this_set):
    """Everything the OTHER sets already used — so rebuilding set N never fights itself."""
    real, gen = set(), set()
    for k, v in manifest.items():
        if str(k) == str(this_set):
            continue
        real |= {tuple(x) for x in v.get("real", [])}
        gen |= set(v.get("gen", []))          # signatures, see gen_sig
    return real, gen


def load(inter_level=False, exclude=frozenset()):
    qs = []
    for f in glob.glob(str(REPO / "question_bank_engine/drop/bssc/*_KEYED.json")):
        for q in json.load(io.open(f, encoding="utf-8")):
            # servable() also drops the questions whose options are unusable — a bare option
            # LETTER as the text, or two identical options. 21 of these 497 are in that state and
            # 13 of them reached the first build of this paper.
            if not (q.get("tag") and servable(q, need_hindi=True)):
                continue
            if tuple(qid(q)) in exclude:
                continue
            # Advt 02/23(A) names an arithmetic-only maths syllabus. Our maths stock comes mostly
            # from Advt 0111, a CLERK exam whose paper ranged wider, so it carries polynomials,
            # APs, circle geometry, trigonometry and probability — above what an Inter Level
            # candidate is examined on. 34% of the maths pool is dropped here.
            if inter_level:
                if not inter_level_ok(q):
                    continue
                # Require a TRUE bilingual pair — Devanagari in one stem field and Latin in the
                # other. Where the extractor lost the English and left Hindi in BOTH fields, the
                # Hindi is an unverified machine translation with nothing to check it against, and
                # it shows: one such question printed a "climate change" stem over 1919 dates
                # (the real question was Jallianwala Bagh). 170 GS and 119 Science+Maths true pairs
                # remain, comfortably more than the 50 + 50 the paper needs.
                a, b = (q.get("stem_hi") or ""), (q.get("stem") or "")
                if bool(_DEV.search(a)) == bool(_DEV.search(b)):
                    continue
            qs.append(q)
    return qs


# Exams for posts BELOW Inter Level. Office Attendant (Advt 02/22) is a Class-10 post and
# "10th Level" is exactly what it says, so their questions are pitched under a 10+2 candidate.
# They are not banned — the bank is too small for that — but they sort last.
_BELOW_LEVEL = {"Qn_SET_A.pdf", "3102059_10_I.pdf"}


def _order_key(q, salt):
    """Deterministic per-set ordering, hardest first.

    random.shuffle() re-orders the WHOLE list whenever the pool changes, so excluding a single bad
    question silently rebuilt the entire paper and threw away the question-by-question checking.
    Hashing each question independently means removing one leaves every other in place.

    The hash used to be the WHOLE key, which meant difficulty played no part in what got picked —
    and it showed. One Step's owner read the first two sets and said "ye basic ka bhi basic hai".
    He was right: 28 of Set 1's 106 official questions were tagged difficulty 1 ("which instrument
    measures the growth of a plant"), and a third came from exams for Class-10 posts. Nothing chose
    that; the hash did. So sort by difficulty first, then by exam level, and let the hash break ties
    — which keeps the draw deterministic and keeps the removal of one question from disturbing the
    rest.
    """
    import hashlib
    d = (q.get("tag") or {}).get("difficulty") or 0
    below = 1 if q.get("source_pdf") in _BELOW_LEVEL else 0
    h = hashlib.sha1(f"{salt}|{q.get('source_pdf')}|{q.get('number')}".encode()).hexdigest()
    return (-d, below, h)


def _numkey(q):
    """Identity of a question by its COMPUTATION rather than its wording.

    "If 3889 + 12.952 - ? = 3854.002" and "Find the value of X in 3889 + 12.952 - X = 3854.002"
    came from two different source papers, had different option sets, and both landed on one
    paper. Text signatures cannot see that; the numbers plus the answer can.
    """
    stem = q.get("stem") or ""
    # A statement-based or match-the-pairs question is ENUMERATED, not computed: its "1. 2. 3."
    # and "A. B. C. D." are list markers, so two entirely different statement questions with the
    # same answer looked like the same computation and the uniqueness check failed on them. The
    # numeric key exists for arithmetic; strip the enumeration before applying it.
    if _enumerated(stem):
        stem = re.sub(r"(?m)^\s*(?:\d+|[A-D])\.\s*", "", stem)
    nums = tuple(sorted(re.findall(r"\d+\.?\d*", stem)))
    ans = next((o["text"] for o in q.get("options") or []
                if o["label"] == q.get("correct_answer")), "")
    return ("num", nums, re.sub(r"\s+", "", str(ans))), len(nums)


def register(q, used, tmpl):
    """Record a question as taken. Anything that lands on the paper must go through here.

    Pin mode originally did not: pinned questions bypassed pick(), so `used`/`tmpl` were empty
    and a top-up draw re-selected the very pair the numeric check above exists to prevent. A
    dedup table only works if everything on the page is in it.
    """
    used.add((q.get("number"), q.get("source_pdf")))
    k = sig(q.get("stem") or "")
    tmpl[k] = tmpl.get(k, 0) + 1
    nkey, n = _numkey(q)
    if n >= 2:
        tmpl[nkey] = 1


def pick(pool, n, used, tmpl, cap=2, salt="", stripe=None, mix=None, topic_quota=None):
    """Draw n questions, hardest first.

    `stripe=(i, m)` deals the sorted pool round-robin across m sets and takes lane i. Without it
    the first set built takes every hard question and the second gets the residue: rebuilding for
    difficulty gave Set 1 zero trivial questions and Set 2 thirty-eight of them. The bank simply
    does not hold two sets' worth of hard questions (145 at-level difficulty-2/3 against the 206
    two papers need), so the only honest options are to split them evenly or to ship one strong
    paper. Splitting is what an institute buying a series needs.
    """
    out = []
    # `topic_quota` caps how many questions each SYLLABUS topic may contribute. Without it this
    # function sorted by difficulty and took whatever the bank happened to hold, so a paper drawn
    # entirely from real questions reflected the BANK's topic mix rather than the commission's:
    # measured, Constitution 15 and Current Affairs 15 against syllabus targets of 7 and 2.5,
    # while Geography got 2 against 5. The generated draw has honoured the syllabus for a while;
    # the real draw never did.
    from collections import Counter as _Counter
    got_topic = _Counter()

    def _topic(q):
        tp = question_topics(q)
        return tp[0][0] if tp else None

    out = []
    pool = sorted(pool, key=lambda q: _order_key(q, salt))
    if stripe:
        i, m = stripe
        pool = [q for k, q in enumerate(pool) if k % m == i] + \
               [q for k, q in enumerate(pool) if k % m != i]   # own lane first, rest as fallback

    def take(candidates, want, respect_topics=True):
        for q in candidates:
            if len(out) >= want:
                break
            if (q.get("number"), q.get("source_pdf")) in used:
                continue
            if tmpl.get(sig(q["stem"]), 0) >= cap:
                continue
            nkey, nn = _numkey(q)
            if nn >= 2 and tmpl.get(nkey):
                continue
            t = _topic(q) if topic_quota else None
            if topic_quota and respect_topics and t and got_topic[t] >= topic_quota.get(t, 0):
                continue
            register(q, used, tmpl)
            if t:
                got_topic[t] += 1
            out.append(q)

    if mix:
        # Fill each difficulty band to its quota, easiest band LAST so that when a band runs dry
        # the shortfall is made up from harder stock rather than trivia. A real paper is not
        # uniformly hard: an all-difficulty-3 paper has no entry point and every candidate stalls
        # on question 1. The mix is what makes a paper feel like an exam rather than a gauntlet.
        running = 0
        for band in sorted(mix, reverse=True):
            running += mix[band]
            take([q for q in pool if ((q.get("tag") or {}).get("difficulty") or 0) == band],
                 running)
    # Top up IGNORING the topic quota. A quota that leaves the section short is worse than one
    # slightly exceeded — the paper must still print 50 questions.
    take(pool, n, respect_topics=False)
    return out


def generate_maths(n, diff, exclude_sigs, bilingual):
    """Fill a maths shortfall from quantgen, at a REQUESTED difficulty.

    This is the only way the difficulty mix can actually be met. The bank holds 145 at-level
    difficulty-2 questions and essentially no difficulty-3 arithmetic, so asking a real-question
    draw for 15 hard questions per section will always come back short — quantgen can produce them
    without limit, with the answer COMPUTED rather than recalled and every distractor derived from
    a named mistake.

    The gate: quantgen has no Hindi at all (zero stem_hi across 23 builders). Dropping English-only
    questions into a bilingual paper would silently break the one promise the paper makes to a
    Hindi-medium student, so a bilingual paper refuses them and says why rather than shipping a
    half-translated section. Hindi templates over the same computation are the fix — the answer is
    computed, so a number cannot drift between the two languages the way a translation can.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    try:
        from qbank import quantgen
    except Exception as e:
        print(f"  quantgen unavailable ({e}) — maths shortfall not filled")
        return []
    rng = random.Random(20260820 + diff)
    out, seen, per_concept = [], set(exclude_sigs), {}
    # Round-robin the builders rather than choosing at random. A random choice returned four
    # questions from the SAME builder on the first run — four ages problems in one section, which
    # reads as padding however hard each one is.
    builders = [b for bs in quantgen._CHAP_BUILDERS.values() for b in bs]
    rng.shuffle(builders)
    for pass_no in range(60):
        for build in builders:
            if len(out) >= n:
                break
            q = quantgen._make_question(build(rng, diff), rng, {"chapter": "Arithmetic"})
            # A bilingual paper takes only the builders that have Hindi. Not all 23 do, and a
            # half-Hindi section would break the one promise the paper makes to a Hindi-medium
            # student — so the filter is per QUESTION, not a blanket refusal.
            if bilingual and not q.stem_hi:
                continue
            row = {"stem": q.stem, "stem_hi": q.stem_hi, "options": q.options,
                   "options_hi": q.options_hi, "correct_answer": q.correct_answer,
                   "solution": q.solution, "solution_hi": q.solution_hi,
                   "concept": q.concept, "_generated": True,
                   "tag": {"section": "Mathematics", "difficulty": diff},
                   "source_pdf": "quantgen", "number": None}
            # The syllabus gate belongs to the Inter Level paper, not to every paper.
            if bilingual and not inter_level_ok(row):
                continue
            g = gen_sig(row)
            if g in seen or per_concept.get(q.concept, 0) >= 4:   # 2 was throttling the hard shortfall
                continue
            seen.add(g)
            per_concept[q.concept] = per_concept.get(q.concept, 0) + 1
            out.append(row)
        if len(out) >= n:
            break
    print(f"  generated {len(out)} maths question(s) at difficulty {diff}")
    return out


def _swap_in(got, fresh):
    """Put `fresh` on the paper by dropping REAL questions, never previously-added generated ones.

    Both top-ups used to trim the tail of the section — and after the first one ran, that tail WAS
    the questions it had just added. The maths block silently deleted all five General Science
    questions the science block had put there, while the build log cheerfully reported both.
    """
    keep, drop = [], len(fresh)
    for q in reversed(got):
        if drop and not q.get("_generated"):
            drop -= 1
            continue
        keep.append(q)
    return list(reversed(keep)) + fresh


def generate_science(n, exclude_sigs):
    """Computed physics numericals — the only non-recall science content we have.

    General Science was the last section with no generator at all, so a fully-generated Part II
    was impossible. sciencegen computes the answer from the quantities in the stem, so it is as
    trustworthy as quantgen and unlimited in the same way.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    try:
        from qbank import sciencegen
    except Exception as e:
        print(f"  sciencegen unavailable ({e})")
        return []
    rng = random.Random(20260821)
    builders = [b for bs in sciencegen._CHAP_BUILDERS.values() for b in bs]
    out, seen = [], set(exclude_sigs)
    for _ in range(60):
        for bld in builders:
            if len(out) >= n:
                break
            sq = sciencegen._make_question(bld(rng, 4), rng,
                                           {"chapter": "General Science", "dmax": 3})
            row = {"stem": sq.stem, "stem_hi": sq.stem_hi, "options": sq.options,
                   "options_hi": sq.options_hi, "correct_answer": sq.correct_answer,
                   "solution": sq.solution, "solution_hi": sq.solution_hi,
                   "concept": sq.concept, "_generated": True, "source_pdf": "sciencegen",
                   "number": None,
                   "tag": {"section": "General Science", "difficulty": 3}}
            if gen_sig(row) in seen:
                continue
            seen.add(gen_sig(row))
            out.append(row)
        if len(out) >= n:
            break
    print(f"  generated {len(out)} General Science question(s) at difficulty 3")
    return out


def generate_whole_section(secs, want, mix, gen_taken, bilingual, salt=0):
    """Build an ENTIRE section from generators, at the requested easy/medium/hard split.

    The top-up paths only ever filled a HARD shortfall, so the easy and medium bands still came
    from the bank and 41 of 150 questions stayed official. This fills every band from a generator,
    which is what "all generated" actually requires.

    Every answer here is computed in Python or looked up in a verified fact table. The computed
    ones cannot be wrong unless the arithmetic is; the table-derived ones are correct relative to
    125 hand-written entries, which is a far smaller and more auditable surface than a scanned
    answer key — but it is not the same kind of zero, and the section note on the page says the
    questions are Acharya-built rather than past-paper.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    out = []
    rng = random.Random(20260822 + salt)
    if "General Studies" in secs:
        out += generate_gs_section(want, mix, gen_taken, bilingual, rng)
    elif "Mathematics" in secs:
        out += generate_maths_section(want, mix, gen_taken, bilingual, rng)
    else:
        # Part III. Do NOT deal the whole pool and then filter by difficulty here — that is the
        # exact shape of the bug that put 16 Blood Relations questions in one section. The band
        # filter belongs inside the deal; see load_generated.
        out += generate_reasoning_section(want, mix, gen_taken)
    # A section short of `want` prints a 147-question paper. Top up from whatever band still has
    # stock rather than shipping a paper that fails its own structure check.
    if len(out) < want:
        for d in (3, 2, 1):
            if len(out) >= want:
                break
            # Top up from the SECTION'S OWN generators. The first version sent maths questions
            # into General Studies, which both mis-sectioned them and duplicated Part II's draw —
            # three identical computations appeared on one paper.
            if "General Studies" in secs:
                extra = generate_static_gk(want - len(out), gen_taken, bilingual)
            elif "Mathematics" in secs:
                extra = generate_maths(want - len(out), d, gen_taken, bilingual)
            else:
                # Backstop only — generate_reasoning_section already relaxes its own cap rather
                # than return short. Keep it capped anyway, so a shortfall here cannot undo the
                # spread the section just spent eleven relaxation steps protecting.
                extra = generate_reasoning_section(want - len(out), {3: want - len(out)},
                                                   gen_taken, cap=REASONING_CONCEPT_CAP)
            for q in extra:
                gen_taken.add(gen_sig(q))
                q.setdefault("tag", {})["section"] = list(secs)[0]
            out += extra
        # A top-up appends whatever it can find, AFTER the section has already been spread — so
        # two questions of one shape can land next to each other at the join. Re-spread Part II
        # here rather than trusting that the top-up never fires. Split on source rather than on
        # the tag, because the loop above overwrites the tag with `list(secs)[0]`.
        if "Mathematics" in secs:
            sci = [q for q in out if q.get("source_pdf") in ("sciencegen", "science_tables")]
            mat = [q for q in out if q.get("source_pdf") not in ("sciencegen", "science_tables")]
            out = spread_questions(sci, rng) + spread_questions(mat, rng)
    return out[:want]


def science_fact_tables():
    """Chemistry and biology fact tables for Part II, each behind its OWN gate.

    Two subjects, two levels of evidence, so two flags. Chemistry's element data is derived from
    PubChem rather than typed and its compound formulae are checked against PubChem's own answer
    (sabotage-tested on eleven corrupted rows, all caught) — a machine can earn that. Biology has
    no comparable source, so it waits for a person, exactly like history. Lumping them under one
    flag would either hold back verified facts or ship unverified ones.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    from qbank import science_tables, staticgk_hi
    t = {}
    if science_tables.CHEM_REVIEWED:
        staticgk_hi.register(science_tables.HI)
        t.update({n: getattr(science_tables, n) for n in
                  ("ELEMENT_SYMBOL", "ELEMENT_ATOMIC_NUMBER", "COMPOUND_FORMULA")})
    if science_tables.BIO_REVIEWED:
        staticgk_hi.register(science_tables.HI)
        t.update({n: getattr(science_tables, n) for n in
                  ("VITAMIN_DEFICIENCY", "VITAMIN_CHEMICAL_NAME", "HORMONE_GLAND",
                   "DISEASE_PATHOGEN")})
    if not t:
        print("  note: chemistry/biology tables are BUILT but NOT ENABLED "
              "(CHEM_REVIEWED / BIO_REVIEWED are False) — see drop/bssc/SCIENCE_REVIEW.md")
    return t


def gs_tables():
    """The verified fact tables every General Studies form draws on."""
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    from qbank import staticgkgen, polity_tables
    t = {n: getattr(staticgkgen, n) for n in ("STATE_CAPITAL", "DANCE_STATE", "RIVER_ORIGIN")}
    # The Constitution tables are what makes a statement question hard rather than a capital in a
    # harder wrapper — and they are what the advertisement's syllabus actually names.
    t["ARTICLE_SUBJECT"] = polity_tables.ARTICLE_SUBJECT
    t["AMENDMENT_DID"] = polity_tables.AMENDMENT_DID
    # 58 more articles + the Part IX/IX-A Panchayat articles, both parsed from the same official
    # PDF. Articles are the only GS sub-topic that reliably produces a HARD question, so this is
    # the cheapest hardness we have. GATED: the Hindi is hand-written.
    from qbank import polity_extra
    if polity_extra.REVIEWED:
        from qbank import staticgk_hi as _sh
        _sh.register(polity_extra.HI)
        t["ARTICLE_SUBJECT"] = dict(t["ARTICLE_SUBJECT"], **polity_extra.ARTICLE_SUBJECT_EXTRA)
        t["PANCHAYAT_ARTICLE"] = polity_extra.PANCHAYAT_ARTICLE
    else:
        print(f"  note: {len(polity_extra.ARTICLE_SUBJECT_EXTRA)} extra Constitution articles + "
              f"{len(polity_extra.PANCHAYAT_ARTICLE)} Panchayat articles BUILT but NOT REVIEWED "
              f"(see drop/bssc/POLITY_EXTRA_REVIEW.md)")
    # History and the freedom movement — 18% of Part I by the blueprint, and previously zero.
    # GATED: these facts do not reach a paper until a person has read drop/bssc/HISTORY_REVIEW.md
    # and set REVIEWED = True. Two automated verifiers were written for that table and both were
    # measured unreliable, so the gate is a human one on purpose. See history_tables.
    from qbank import history_tables, staticgk_hi
    if history_tables.REVIEWED:
        staticgk_hi.register(history_tables.HI)
        for name in ("MOVEMENT_YEAR", "FOUNDED_YEAR", "MOVEMENT_LEADER",
                     "MOVEMENT_AGAINST", "BIHAR_FREEDOM"):
            t[name] = getattr(history_tables, name)
    else:
        print("  note: history/freedom-movement tables are BUILT but NOT REVIEWED — "
              "39 facts held back from the paper (see drop/bssc/HISTORY_REVIEW.md)")
    # बिहार. The advertisement names Bihar as its own emphasis and the delivered paper carried
    # THREE Bihar questions in 150, all of them "Patna is the capital of which state?". Same human
    # gate as history, and for a stronger reason: these are the rows a Patna institute owner checks
    # first, so a hand-written slip here costs the account rather than a mark.
    # Current affairs is 8.2% of the real GS papers and we had zero. It is NOT a fact table —
    # each row is a standalone question — so it is not added to `t`; the GS draw calls
    # current_affairs.build() directly. Reported on every build either way, because a
    # current-affairs table that has gone stale looks identical to one that is simply absent.
    # आर्थिक परिदृश्य / खेल / भारतीय कृषि — 16% of Part I between them, and all three sat at
    # zero because the topics had no content at all, not because a gate was holding them. Same
    # human gate as history and Bihar: these are hand-written rows, and the measured error rate on
    # hand data in this repo is ~1 in 27. Each module names its own review sheet.
    for _mod, _label, _sheet in (
            ("economy_tables", "economy / five-year-plan", "ECONOMY_REVIEW.md"),
            ("agri_tables", "agriculture", "AGRICULTURE_REVIEW.md"),
            ("sports_tables", "sports", "SPORTS_REVIEW.md")):
        _m = __import__(f"qbank.{_mod}", fromlist=["x"])
        if _m.REVIEWED:
            staticgk_hi.register(_m.HI)
            t.update(_m._ALL)
        else:
            print(f"  note: {_label} tables are BUILT but NOT REVIEWED — "
                  f"{sum(len(x) for x in _m._ALL.values())} facts held back "
                  f"(see drop/bssc/{_sheet})")
    from qbank import current_affairs
    print("  note: " + current_affairs.status())
    from qbank import bihar_tables
    if bihar_tables.REVIEWED:
        staticgk_hi.register(bihar_tables.HI)
        for name in ("BIHAR_SITE_DISTRICT", "BIHAR_GI_PRODUCT",
                     "BIHAR_FREEDOM_ROLE", "BIHAR_FOLK_REGION"):
            t[name] = getattr(bihar_tables, name)
    else:
        n = sum(len(x) for x in bihar_tables._TABLES.values())
        print(f"  note: BIHAR tables are BUILT but NOT REVIEWED — {n} facts held back "
              f"(see drop/bssc/BIHAR_REVIEW.md, then set bihar_tables.REVIEWED)")
    return t


# No GS style may take more than this share of the section. The delivered paper ran one opening
# line ("Consider the following statements") 35 times out of 50 and the institute's owner said so:
# "question is good but style is similar". Ten is a fifth of the section.
# A ceiling, not a target. It was 10 of 50 when the section round-robinned across six forms we
# happened to own; now the weighted slot list IS the quota and the commission's own largest style
# is 36% of its paper, so a cap of 10 would fight the very distribution we are copying. Kept only
# to stop a runaway if the weighting is ever mis-specified.
GS_STYLE_CAP = 24

# The commission's measured share of the reverse-lookup style ("Agartala is the capital of which
# state?"). Raising it is the ONLY lever that makes General Studies harder without faking a
# difficulty label, because `rev` is the only asking style that can reach difficulty 3 — it scores
# +1 for running the table backwards and +1 again when the distractors are measurably confusable.
#
# It is a DELIBERATE TRADE and the build prints it. At 14.3 the paper matches the real exam's
# style distribution; above that it is progressively less like a real BSSC paper and progressively
# harder. There is no setting that is both.
GS_REV_SHARE_DEFAULT = 14.3
GS_REV_SHARE = GS_REV_SHARE_DEFAULT


def _gs_row(b, d):
    # 🔴 ROTATE THE ANSWER OUT OF SLOT A.
    # Written without this, the correct option was simply placed first and the key hardcoded to
    # "A". Measured on a DELIVERED paper: 46 of Part I's 50 answers were (A), so a candidate who
    # marked A all the way down Part I scored 184 of 200 without reading a single question.
    # Every check passed — the key letter was present among the options, and every independent
    # solver agreed with it — because not one of them looked at the DISTRIBUTION of key letters.
    # quantgen and reasoninggen rotate inside their own _mcq, which is why Parts II and III were
    # evenly spread and this stayed invisible.
    # Keyed on the stem so it is deterministic: a pinned rebuild reproduces the same paper.
    texts = [b["correct"]] + list(b["distractors"])[:3]
    # Hash the ANSWER as well as the stem. Keyed on the stem alone this was still lopsided —
    # B took 23 of 50 — because the pair and statement forms print ONE fixed stem
    # ("Which of the following pairs is correctly matched?") for every question they build, so
    # every question of that style hashed to the same rotation. The answer text is what actually
    # varies question to question.
    seed = (b["stem"] or "") + "|" + str(b["correct"])
    rot = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16) % len(texts)
    texts = texts[-rot:] + texts[:-rot] if rot else texts
    opts = [{"label": l, "text": t} for l, t in zip("ABCD", texts)]
    hm = b.get("hi_opts") or {}
    return {"stem": b["stem"], "stem_hi": b["stem_hi"], "options": opts,
            "options_hi": [{"label": o["label"], "text": hm.get(o["text"], o["text"])}
                           for o in opts],
            "correct_answer": "ABCD"[rot], "solution": b["solution"],
            "solution_hi": b.get("solution_hi", ""), "concept": b["concept"],
            "src": list(b.get("src") or []), "fact": b.get("fact"),
            "_generated": True, "source_pdf": "staticgk_forms", "number": None,
            # A builder that KNOWS what its question demands overrides the band that asked for
            # it. Stamping the loop variable is how a capital-city recall printed "कठिन / Hard".
            "tag": {"section": "General Studies", "difficulty": b.get("difficulty") or d}}


# How many questions of one SHAPE Part II may print. Part III's per-concept cap is 4 of 50; a
# shape is narrower than a concept, so this is tighter. It is relaxed a step at a time, loudly,
# if the generators cannot fill the section under it.
MATHS_TEMPLATE_CAP = 2


def generate_maths_section(want, mix, gen_taken, bilingual, rng):
    """Part II, drawn to the SYLLABUS quotas instead of round-robin across every quantgen builder.

    What the old draw produced, measured on the delivered sets: ब्याज (interest) took 32% of the
    maths questions and प्रतिशत (percentage) took ZERO — while 330 real BSSC maths questions put
    percentage at 16% and interest near 1%. quantgen owned 23 builders and the paper used 7. None
    of that was a content gap; the section simply asked whichever builder came first in a
    round-robin and had no idea what the syllabus wanted.

    Science shares Part II, so it takes its own slice first — otherwise a maths quota that fills
    completely leaves no room for it, which is how the science block used to be silently deleted.
    """
    from collections import Counter
    import syllabus_blueprint as SB
    from qbank import quantgen, sciencegen
    sci_want = max(1, round(want * 0.25))               # ~1 in 4 of Part II is General Science
    out = []
    # One shared ceiling on how often any one SHAPE may appear in Part II, spent across the science
    # slice and the maths slice alike. `cap` is a list so the top-up loop can relax it — a short
    # section is a worse outcome than a slightly repetitive one, and relaxing loudly beats
    # returning 46 questions quietly.
    tmpl, cap = Counter(), [MATHS_TEMPLATE_CAP]

    def take(row):
        """Accept a drawn row, or reject it as a duplicate question or an over-used shape."""
        if gen_sig(row) in gen_taken:
            return False
        t = template_sig(row)
        if tmpl[t] >= cap[0]:
            return False
        gen_taken.add(gen_sig(row))
        tmpl[t] += 1
        return True

    # ---- General Science slice, drawn to the blueprint's subject quotas
    # Physics comes from sciencegen (computed numericals); chemistry from the verified fact tables
    # through the same statement/pair FORMS General Studies uses, so a chemistry question is as
    # hard as a GS one rather than bare recall. Biology joins here the moment BIO_REVIEWED flips.
    sci_quota = SB.quotas("General Science", sci_want)
    fact_tables = science_fact_tables()
    sci_builders = [b for bs in sciencegen._CHAP_BUILDERS.values() for b in bs]
    for subject, n_want in sorted(sci_quota.items(), key=lambda kv: -kv[1]):
        got_s = 0
        if subject == "Physics":
            # Fill the subject's whole quota, spending the hard band first. The earlier
            # per-band target was computed against a share rather than a running total, so a band
            # that came up short was never made good and physics landed at 6 of 7.
            for d, upto in ((3, 0.7), (2, 0.9), (1, 1.0)):
                for _ in range(200):
                    if got_s >= round(n_want * upto):
                        break
                    sq = sciencegen._make_question(rng.choice(sci_builders)(rng, d), rng,
                                                   {"chapter": "General Science", "dmax": d})
                    row = {"stem": sq.stem, "stem_hi": sq.stem_hi, "options": sq.options,
                           "options_hi": sq.options_hi, "correct_answer": sq.correct_answer,
                           "solution": sq.solution, "solution_hi": sq.solution_hi,
                           "concept": sq.concept, "_generated": True,
                           "source_pdf": "sciencegen", "number": None,
                           "tag": {"section": "General Science", "difficulty": d}}
                    if not take(row):
                        continue
                    out.append(row); got_s += 1
        elif fact_tables:
            from qbank import staticgk_forms as SF
            forms = [SF.b_multi_statement(fact_tables), SF.b_correct_pair(fact_tables),
                     SF.b_count_statements(fact_tables), SF.b_which_statement(fact_tables)]
            for _ in range(400):
                if got_s >= n_want:
                    break
                b = forms[got_s % len(forms)](rng, 3)
                if not b or (bilingual and not b.get("stem_hi")):
                    continue
                row = _gs_row(b, 3)
                # The FORM name is not the subject. Tag the subject explicitly, or the syllabus
                # report cannot tell a chemistry question from a capitals one.
                row["concept"] = subject
                row["src"] = [subject]          # keep the tag on the SUBJECT, as the map keys it
                row["tag"]["section"] = "General Science"
                row["source_pdf"] = "science_tables"
                if not take(row):
                    continue
                out.append(row); got_s += 1
        if got_s < n_want:
            print(f"  note: General Science drew {got_s} of {n_want} for {subject}")

    # ---- Mathematics, to the blueprint
    maths_want = want - len(out)
    quota = SB.quotas("Mathematics", maths_want)
    banned = SB.excluded_builders()
    by_name = {b.__name__: b for bs in quantgen._CHAP_BUILDERS.values() for b in bs}
    got, made = Counter(), Counter()

    def draw(topic, d):
        """One bilingual, in-syllabus maths question for this topic at difficulty d, or None."""
        names = [n for n in _builders_for("Mathematics", topic)
                 if n in by_name and n not in banned]
        if not names:
            return None
        for _ in range(60):
            try:
                q = quantgen._make_question(by_name[rng.choice(names)](rng, d), rng,
                                            {"chapter": "Arithmetic"})
            except Exception:
                continue
            row = {"stem": q.stem, "stem_hi": q.stem_hi, "options": q.options,
                   "options_hi": q.options_hi, "correct_answer": q.correct_answer,
                   "solution": q.solution, "solution_hi": q.solution_hi,
                   "concept": q.concept, "_generated": True,
                   "tag": {"section": "Mathematics", "difficulty": d},
                   "source_pdf": "quantgen", "number": None}
            if bilingual and (not q.stem_hi or not inter_level_ok(row)):
                continue
            if not take(row):
                continue
            return row
        return None

    # Fill each topic to its quota, spending the difficulty bands in the requested proportions.
    # A builder may only have Hindi at SOME difficulties — quantgen's simplify and average carry it
    # at band 1 only — so a band that cannot be filled falls back to one that can, and the row is
    # tagged with the difficulty it was ACTUALLY built at. Tagging it with the difficulty we asked
    # for would put a made-up number in the mix report, which is the failure this file keeps
    # finding in its own checks.
    for topic in sorted(quota, key=lambda t: -quota[t]):
        band = {3: int(round(quota[topic] * mix[3] / want)),
                2: int(round(quota[topic] * mix[2] / want))}
        band[1] = max(0, quota[topic] - band[3] - band[2])
        for d in (3, 2, 1):
            for _ in range(band[d]):
                if got[topic] >= quota[topic]:
                    break
                row = draw(topic, d) or draw(topic, 2) or draw(topic, 1) or draw(topic, 4)
                if row:
                    out.append(row); got[topic] += 1; made[topic] += 1

    # Anything the quotas could not reach is topped up ROUND-ROBIN across the topics that still
    # have room. The first version sorted by "most room" and then looped without re-checking the
    # quota, so it emptied the whole shortfall into one topic — percentage came out at 20 against
    # a target of 10, which is the same over-concentration this blueprint exists to prevent.
    guard = 0
    while len(out) < want and guard < 400:
        guard += 1
        room = [t for t in quota if got[t] < quota[t]] or list(quota)
        progress = False
        for topic in room:
            if len(out) >= want:
                break
            row = draw(topic, 3) or draw(topic, 2) or draw(topic, 1)
            if row:
                out.append(row); got[topic] += 1; progress = True
        if not progress:
            # Nothing left within the current shape ceiling. Raise it by one and say so, rather
            # than either printing a short section or repeating a shape silently — the two
            # failure modes this file keeps rediscovering.
            if cap[0] < 4:
                cap[0] += 1
                print(f"  note: no shapes left under a cap of {cap[0] - 1} per template — "
                      f"relaxing Part II to {cap[0]}")
                continue
            break
    if len(out) < want:
        print(f"  note: Part II is {want - len(out)} short of the blueprint — no bilingual "
              f"generator could fill the remaining quota")
    maths_only = [q for q in out if q["tag"]["section"] == "Mathematics"]
    for line in SB.report("Mathematics", maths_only):
        print(line)
    print(f"      (+ {len(out) - len(maths_only)} General Science questions in Part II)")

    # Print the shape spread on EVERY build. Nothing ever said what had been drawn, which is the
    # only reason seven identical templates in a row survived two deliveries.
    spread = Counter(template_sig(q) for q in out)
    worst = spread.most_common(3)
    print(f"      shapes — {len(spread)} distinct templates in {len(out)} questions, "
          f"most-repeated {worst[0][1] if worst else 0}x")
    for s, c in worst:
        if c > 1:
            print(f"        {c}x  {s[:78]}")

    # Science first, then maths — the section is named "सामान्य विज्ञान एवं गणित" and a candidate
    # expects the two subjects in blocks. Spread WITHIN each block, so no two questions of the same
    # shape are ever adjacent.
    sci = spread_questions([q for q in out if q["tag"]["section"] != "Mathematics"], rng)
    mat = spread_questions(maths_only, rng)
    return (sci + mat)[:want]


def _builders_for(section, topic_en):
    import syllabus_blueprint as SB
    for t in SB.topics(section):
        if t["en"] == topic_en:
            return list(t.get("builders") or [])
    return []


def generate_gs_section(want, mix, gen_taken, bilingual, rng):
    """Part I, dealt ROUND-ROBIN ACROSS STYLES rather than filled one style at a time.

    The old version fed a quota to each builder in turn: match-pairs got a fifth of the hard band
    and multi-statement got the other four fifths, so 28 of 35 hard questions were one form — and
    because b_two_statement opens with the same sentence, 35 of the 50 printed questions began with
    the identical words. The facts were all different and the paper still read as one question
    asked fifty times.

    Dealing across the styles is the same fix Part III needed, for the same reason: a section that
    fills its quota one source at a time will always be dominated by whichever source is asked
    first. The style spread is printed on every build, because this went unnoticed for two
    deliveries purely because nothing ever said what had been drawn.
    """
    from collections import Counter
    from qbank import staticgk_forms as SF
    import syllabus_blueprint as SB
    tables = gs_tables()
    # Which fact tables serve each SYLLABUS topic. The forms choose a table for themselves when
    # handed the whole dict, so the section spread across STYLES perfectly and across TOPICS not at
    # all — measured on a tagged build, राजधानी took 27 of 50 while the blueprint asks for ~10.
    # Handing a builder only the target topic's tables is what makes the topic quota real, and it
    # is the same fix Part II's maths draw needed for the same reason.
    topic_tables = {}
    for t in SB.topics("General Studies"):
        names = [c for c in (t.get("concepts") or []) if c in tables]
        if names:
            topic_tables[t["en"]] = names
    quota = {k: v for k, v in SB.quotas("General Studies", want).items() if k in topic_tables}
    # ── THE COMMISSION'S OWN ASKING MIX ────────────────────────────────────────────────────────
    # Weights are the MEASURED shares of 552 official General Studies questions (see the
    # qbank/gs_ask docstring), renormalised after dropping "word problem", which a fact table
    # cannot produce and which Parts II and III already carry.
    #
    # What this replaces: six statement/match/pair forms in a flat round-robin, which put 44% of
    # the section in match-list and 30% in statement-list — 74% in two styles that are 2.7% of the
    # real exam, and NONE in the commission's largest style. Every "spread" report was green,
    # because they measured the spread across the styles we happened to own.
    from qbank import gs_ask as GA

    def _ask(style):
        def factory(tbls):
            def build(rng, diff):
                names = [n for n in tbls if style in (GA.ASK.get(n) or {})]
                return GA.build(tbls, rng.choice(names), style, rng, diff) if names else None
            return build
        return factory

    def _neg():
        def factory(tbls):
            def build(rng, diff):
                return GA.build_neg_statement(tbls, rng, diff)
            return build
        return factory

    def _odd():
        def factory(tbls):
            def build(rng, diff):
                names = list(tbls)
                return GA.build_odd(tbls, rng.choice(names), rng, diff) if names else None
            return build
        return factory

    # Factory, the classifier bucket it is MEANT to land in, and the commission's measured share
    # of that bucket (renormalised over the styles a fact table can produce). Selection below is
    # driven by the DEFICIT against these shares, measured on the questions actually produced.
    #
    # Fixed weights were tried first and could not hold the distribution, because a weight is an
    # intention and the output is what matters: b_wrong_pair had a perfectly good yield (220 of
    # 300) and still produced 0-1 questions a paper, because 3 slots out of 100 over a 38-question
    # draw is one question. Meanwhile _ask("wh") was WORDED as an embedded-which and quietly
    # spent the direct-wh budget on the wrong bucket. Counting the outcome fixes both.
    # comp yields exactly what rev takes, so the other styles keep their measured shares and the
    # trade is visible in one place instead of being smeared across the table.
    _rev = float(GS_REV_SHARE)
    _comp = max(4.0, 36.2 - (_rev - GS_REV_SHARE_DEFAULT))
    if abs(_rev - GS_REV_SHARE_DEFAULT) > 0.01:
        print(f"  note: GS reverse-lookup share raised {GS_REV_SHARE_DEFAULT}% -> {_rev}% "
              f"(sentence-completion {36.2}% -> {_comp:.1f}%) — HARDER than the real exam's "
              f"style mix, on purpose")
    spec = [(_ask("comp"), "sentence-completion", _comp),
            (_ask("wh"), "direct-wh", 16.7),
            (_ask("rev"), "embedded-which", _rev),
            (SF.b_which_statement, "which-of-following", 9.2),
            # Split across two negative forms: the odd-one-out can only build where three keys
            # share a value (Kerala's dances, and nothing else in our tables), so on its own it
            # capped the bucket at one question however the weight was set.
            (_neg(), "negative-select", 3.6),
            (_odd(), "negative-select", 1.5),
            # ⚠️ The bucket is the one the CLASSIFIER puts the output in, not the one the builder
            # is named after. "Which of the following pairs is NOT correctly matched?" contains
            # "matched", so it scores as match-list — and labelling it negative-select here left
            # that bucket permanently unfilled, so its deficit never closed and the selector chose
            # it ELEVEN times against a target of two. Exactly the intention-vs-outcome trap this
            # selector exists to avoid, reproduced inside its own configuration.
            (SF.b_wrong_pair, "match-list", 1.0),
            (SF.b_correct_pair, "match-list", 0.9),
            (SF.b_match_pairs, "match-list", 0.6),
            (_ask("blank"), "fill-in-blank", 1.3)]
    # ── THE DIFFICULTY MIX HAS TO REACH THE STYLE MIX ──────────────────────────────────────────
    # Measured on a built paper, style and difficulty are almost perfectly correlated, because
    # `gs_ask.difficulty_of` scores what a form actually DEMANDS:
    #
    #   Sentence Completion  36.2%  ->  21 questions, 0 hard      forward lookup: caps at 2
    #   Direct Question      16.7%  ->  10 questions, 0 hard      forward lookup: caps at 2
    #   Fill in the Blank     1.3%  ->   1 question,  0 hard      forward lookup: caps at 2
    #   Reverse / statement / pair   ->  18 questions, ALL hard
    #
    # So 54% of the style budget was spent on forms that structurally cannot produce a hard
    # question, and `--difficulty-mix 15:15:70` came out 0/32/18. The build has been reporting
    # that as "SHORT: 17 at difficulty 3" as though the bank were thin. It is not thin — the
    # request never reached the thing that decides.
    #
    # The mix is the request, so it steers the styles: share moves from the difficulty-capped
    # forms to the hard-capable ones until they hold the requested hard fraction. That makes the
    # paper deliberately UNLIKE the commission's measured asking mix, which is the right trade for
    # a practice paper — the institute asked for hard questions, not for a style replica — but it
    # is a real deviation and it is printed, the same way GS_REV_SHARE prints its own.
    _HARD_CAPABLE = {"embedded-which", "which-of-following", "negative-select", "match-list"}
    # `mix` is the caller's mix_for(want) — {1: easy, 2: medium, 3: hard} as whole questions.
    _mix_want = mix if want else None
    if _mix_want:
        _target = _mix_want[3] / max(1, want)                    # requested HARD fraction
        _tot = sum(sh for _f, _s, sh in spec)
        _hard = sum(sh for _f, s2, sh in spec if s2 in _HARD_CAPABLE)
        _have = _hard / _tot
        if _target > _have + 0.01:
            # Scale the hard-capable group up to the target and the rest down to fill the
            # remainder, both proportionally, so the mix WITHIN each group is untouched.
            _up = (_target * _tot) / _hard
            _down = ((1 - _target) * _tot) / (_tot - _hard)
            spec = [(f, s2, sh * (_up if s2 in _HARD_CAPABLE else _down)) for f, s2, sh in spec]
            print(f"  note: GS style mix re-weighted for a {_mix_want[1]}:{_mix_want[2]}:"
                  f"{_mix_want[3]} (easy:medium:hard) paper — hard-capable forms {_have:.0%} -> {_target:.0%} of the "
                  f"draw. DELIBERATELY unlike the real exam's style mix; a forward lookup cannot "
                  f"be a hard question however it is worded.")
    total_share = sum(sh for _f, _s, sh in spec)
    out, used, by_topic, facts_used = [], Counter(), Counter(), set()

    def next_topic():
        """The syllabus topic furthest below its quota — ties broken deterministically."""
        return max(quota, key=lambda t: (quota[t] - by_topic[t], t)) if quota else None

    by_style, by_band = Counter(), Counter()

    def next_factory(n_target, blocked):
        """The style furthest BELOW the commission's share of it, measured on what we have built.

        `blocked` holds the factories that already failed this round. Without it the selector
        re-picked the same failing style on every slot — its deficit cannot close if it never
        produces anything — so a round burned all its slots on one dead builder and the section
        fell ten questions short, to be topped up by an UNSTEERED recall generator that pushed
        direct-wh from 17% to 30%. A style that cannot build has to yield its turn.
        """
        live = [fs for fs in spec if id(fs[0]) not in blocked] or spec
        return max(live, key=lambda fs: (fs[2] / total_share * n_target - by_style[fs[1]],
                                         -spec.index(fs)))

    # One pass to fill the section. There is no longer a per-BAND loop: difficulty is now derived
    # from the question (gs_ask.difficulty_of), not requested, so asking for "a hard one" and
    # stamping the answer would be the very thing that printed कठिन on "The capital of Rajasthan
    # is". Every draw asks for the hardest form of its style — the tightest distractors available —
    # and the difficulty that comes out is reported rather than chosen.
    for d, factories, n in ((3, spec, want),):
        got, rounds = 0, 0
        while got < n and rounds < 400:
            rounds += 1
            progress = False
            blocked = set()
            for _slot in range(len(spec)):
                if got >= n:
                    break
                _fs = next_factory(n, blocked)
                factory, _bucket = _fs[0], _fs[1]
                # WHICH DIFFICULTY TO ASK THIS DRAW FOR.
                # The band loop was removed once difficulty became derived rather than requested,
                # and the easy band went to zero with it — every draw asked for the tightest
                # distractors available, so nothing easy was ever built. A paper of 50 questions
                # with no entry point is not what "15:15:70" asked for either.
                # Asking is not stamping: `_options` uses this to choose how CONFUSABLE the
                # distractors are, and `difficulty_of` still reports what actually came out. The
                # statement and pair forms are left alone at 3 — they carry no honest difficulty
                # of their own, so a low `d` would be stamped straight onto a three-statement
                # question, which is the decorative-badge bug in reverse.
                if _bucket in _HARD_CAPABLE:
                    ask_d = 3
                elif by_band[1] < (mix or {}).get(1, 0):
                    ask_d = 1
                else:
                    # Not 2. `_options` treats `diff` as how hard to try for CONFUSABLE
                    # distractors, and asking for 2 still returned loose ones often enough that
                    # the easy band overshot 8 -> 15 while medium starved at 2. A forward lookup
                    # cannot exceed difficulty 2 whatever it is handed, so asking for the tightest
                    # options available is what reliably LANDS it at 2.
                    ask_d = 3
                topic = next_topic()
                sub = {k: tables[k] for k in topic_tables[topic]} if topic else tables
                # Restricting to one topic's tables starves some styles: a "which pair is NOT
                # correctly matched" needs four rows whose values are all distinct, and one small
                # table cannot always supply them. Steering the topic that way took two styles from
                # six questions each down to ONE — trading the owner's "style is similar"
                # complaint for his "only one topic" complaint. So the restriction is a PREFERENCE:
                # if a style cannot build within the target topic, it builds from everything and
                # the topic it actually produced is what gets counted.
                placed = False
                for build in (factory(sub), factory(tables)):
                    for _ in range(25):                 # a style may need a few tries to land
                        b = build(rng, ask_d)
                        if not b or (bilingual and not b.get("stem_hi")):
                            continue
                        if used[b["concept"]] >= GS_STYLE_CAP:
                            break
                        row = _gs_row(b, ask_d)
                        if gen_sig(row) in gen_taken:
                            continue
                        if row.get("fact") and row["fact"] in facts_used:
                            continue      # same table row, different phrasing — one question
                        gen_taken.add(gen_sig(row))
                        if row.get("fact"):
                            facts_used.add(row["fact"])
                        used[b["concept"]] += 1
                        # Count the topic the question ACTUALLY covers, not the one that was asked
                        # for — the fallback above can return a different one, and a quota fed by
                        # intentions rather than outcomes reports a spread the paper does not have.
                        for en, _hi in question_topics(row):
                            if en in quota:
                                by_topic[en] += 1
                                break
                        by_style[ask_style(row["stem"])] += 1
                        by_band[(row["tag"] or {}).get("difficulty") or ask_d] += 1
                        out.append(row); got += 1; progress = placed = True
                        break
                    if placed:
                        break
                if not placed:
                    blocked.add(id(factory))
            if not progress:
                break
        if got < n:
            print(f"  note: General Studies drew {got} of {n} at difficulty {d} "
                  f"under a {GS_STYLE_CAP}/style cap")
    out += generate_static_gk(want - len(out), gen_taken, bilingual)
    spread = Counter(q.get("concept") or "?" for q in out)
    print(f"  Part I style spread: {len(out)} questions over {len(spread)} styles, "
          f"most-used {max(spread.values(), default=0)} — "
          + ", ".join(f"{k} {v}" for k, v in spread.most_common()))
    for line in SB.report("General Studies", out,
                          concept_of=lambda q: (q.get("src") or [q.get("concept") or "?"])[0]):
        print(line)
    return out[:want]


def generate_gs_forms(n, exclude_sigs, bilingual):
    """Fill a General Studies HARD shortfall with statement-based and match-the-pairs questions.

    This is the only way the difficulty mix can be met in GS. After every gate the bank holds 132
    General Studies questions and ZERO above difficulty 2, so asking a real-question draw for 15
    hard ones per section will always come back short — which the build report has been saying out
    loud since the mix was wired.

    Unlike --generate-gk, these are NOT recall. The fact is the same; the FORM does the work, and
    the profile shows it: 31.4 words per stem against 29.7 for the hardest real GS we hold. Every
    statement is a (key, value) pair from a verified table, and every false one pairs a key with a
    different value from the SAME table — false by our own data rather than by a model's opinion.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    try:
        from qbank import staticgkgen, staticgk_forms
    except Exception as e:
        print(f"  GS form generation unavailable ({e})")
        return []
    tables = {t: getattr(staticgkgen, t)
              for t in ("STATE_CAPITAL", "DANCE_STATE", "RIVER_ORIGIN")}
    builders = [staticgk_forms.b_multi_statement(tables), staticgk_forms.b_match_pairs(tables)]
    rng = random.Random(20260820)
    out, seen = [], set(exclude_sigs)
    for _ in range(200):
        for build in builders:
            if len(out) >= n:
                break
            try:
                b = build(rng, 3)
            except Exception:
                continue
            if bilingual and not b.get("stem_hi"):
                continue
            opts = [{"label": l, "text": t} for l, t in
                    zip("ABCD", [b["correct"]] + list(b["distractors"])[:3])]
            hi_map = b.get("hi_opts") or {}
            row = {"stem": b["stem"], "stem_hi": b["stem_hi"], "options": opts,
                   "options_hi": [{"label": o["label"], "text": hi_map.get(o["text"], o["text"])}
                                  for o in opts],
                   "correct_answer": "A", "solution": b["solution"],
                   "solution_hi": b.get("solution_hi", ""), "concept": b["concept"],
                   "src": list(b.get("src") or []),
                   "_generated": True,
                   "tag": {"section": "General Studies", "difficulty": 3},
                   "source_pdf": "staticgk_forms", "number": None}
            g = gen_sig(row)
            if g in seen:
                continue
            seen.add(g)
            out.append(row)
        if len(out) >= n:
            break
    print(f"  generated {len(out)} GS question(s) at difficulty 3 "
          f"(statement-based / match-the-pairs)")
    return out


def generate_static_gk(n, exclude_sigs, bilingual):
    """Fill a General Studies shortfall from staticgkgen — correct-by-construction, not recall.

    OFF BY DEFAULT, and the reason matters. staticgkgen answers a fact by looking it up in a
    verified table, so it can never serve a wrong key — but what it produces is "What is the
    capital of Chhattisgarh?", which is difficulty-1 recall. That is the same register as the
    "Who is the Speaker?" questions One Step's owner read and called "basic ka bhi basic". Adding
    them would make the paper WORSE by the standard he actually gave us, so the paper only draws
    them when explicitly asked.

    What makes this data useful for a hard paper is not more recall questions over it — it is
    re-forming these verified facts into multi-statement, assertion-reason and match-the-pairs
    questions, where the false statements are DERIVED from the same tables rather than asserted.
    That is the next build, and this engine is its data layer.
    """
    sys.path.insert(0, str(REPO / "question_bank_engine"))
    try:
        from qbank import staticgkgen
    except Exception as e:
        print(f"  staticgkgen unavailable ({e})")
        return []
    rng = random.Random(20260820)
    out, seen = [], set(exclude_sigs)
    builders = [b for bs in staticgkgen._CHAP_BUILDERS.values() for b in bs]
    rng.shuffle(builders)
    for _ in range(80):
        for build in builders:
            if len(out) >= n:
                break
            try:
                b = build(rng, 2)
            except Exception:
                continue
            if bilingual and not b.get("stem_hi"):
                continue          # staticgk_hi gates all-or-nothing; never half-Hindi
            q = staticgkgen._make_question(b, rng, {"chapter": "Static GK"})
            row = {"stem": q.stem, "stem_hi": q.stem_hi, "options": q.options,
                   "options_hi": q.options_hi, "correct_answer": q.correct_answer,
                   "solution": q.solution, "solution_hi": q.solution_hi,
                   "concept": q.concept, "_generated": True,
                   "tag": {"section": "General Studies", "difficulty": 1},
                   "source_pdf": "staticgkgen", "number": None}
            g = gen_sig(row)
            if g in seen:
                continue
            seen.add(g)
            out.append(row)
        if len(out) >= n:
            break
    print(f"  generated {len(out)} Static GK question(s) — NOTE: difficulty 1, factual recall")
    return out


def load_hindi_generated(n, cap_per_concept=6, exclude=frozenset()):
    """The Hindi Language section, from `hindigen` rather than from the real papers.

    This is a deliberate downgrade of the "every question is real" claim, made after rendering the
    real Hindi section and reading it. Hindi-LANGUAGE questions are the worst case for OCR: the
    question is ABOUT the Devanagari word, so a misread destroys it outright, and unlike a GS
    question there is no English twin to fall back on. What the real section actually printed:

        फिल्म में प्रायोगिक संधारण बताइए ?        (A) मिट्टी (B) मानव (C) इमारत (D) संपत्ति
        विशेषण शब्द को परिभाषित करें              (A) रेल (B) भेद (C) पटना (D) सड़क
        'मैं में दो जोड़ना' मुहावरा का क्या अर्थ होगा ?  (A) मैं में दो जोड़ना ...

    Roughly half the section read like that. `hindigen` is standard textbook grammar with correct
    answers ('लोहे के चने चबाना' -> 'बहुत कठिन काम करना'), so the section is right even though it is
    not a past question. Pass --hindi-source real to print the original anyway.

    Still open: a native Hindi reader has not reviewed hindigen's tables (skill §11 item 2).
    """
    p = REPO / "question_bank_engine/drop/bssc/HINDI_GEN.json"
    if not p.exists():
        return []
    buckets = {}
    for q in json.load(io.open(p, encoding="utf-8")):
        if not (q.get("stem") and q.get("correct_answer") and len(q.get("options") or []) == 4):
            continue
        if gen_sig(q) in exclude:
            continue
        if not numbers_agree(q):
            continue      # Hindi template dropped the rule ("twice its position") — see numbers_agree
        if analogy_ambiguous(q) or odd_one_out_ambiguous(q):
            continue      # two defensible answers both on offer — see the two _ambiguous gates
        q["_generated"] = True
        # The pool carries `difficulty` at the top level but no tag.difficulty, so the mix report
        # counted every generated reasoning question as difficulty 0 and printed a shortfall on a
        # section that was full. Mirror it into the tag the report actually reads.
        q.setdefault("tag", {})
        q["tag"].setdefault("section", "Reasoning")
        q["tag"].setdefault("difficulty", q.get("difficulty") or 2)
        buckets.setdefault(q.get("concept") or "?", []).append(q)
    for b in buckets.values():
        random.shuffle(b)
        # ...then hardest first WITHIN each concept. The round-robin deal keeps the section varied;
        # this makes it also honour the difficulty request, which it ignored entirely before —
        # Part III drew 29 easy questions from a pool holding 343 hard ones.
        b.sort(key=lambda q: -(q.get("difficulty") or (q.get("tag") or {}).get("difficulty") or 0))
    order = sorted(buckets, key=lambda k: -len(buckets[k]))
    # Deal round-robin so the section stays varied. The cap is a PREFERENCE, not a wall: once
    # every concept has contributed cap_per_concept, keep dealing rather than return a short
    # section — a 146-question paper is a worse outcome than a slightly uneven one.
    out, rnd, deepest = [], 0, max((len(v) for v in buckets.values()), default=0)
    while len(out) < n and rnd < deepest:
        for k in order:
            if len(out) >= n:
                break
            if len(buckets[k]) > rnd:
                out.append(buckets[k][rnd])
        rnd += 1
        if rnd == cap_per_concept and len(out) < n:
            print(f"  note: reasoning spread exceeded {cap_per_concept}/concept to fill the section")
    return out[:n]


def load_generated(n, cap_per_concept=6, exclude=frozenset(), difficulty=None,
                   concept_used=None, hard_cap=None, only_concepts=None):
    """Bilingual reasoning with COMPUTED answers, only used by --structure official3.

    Capped and dealt round-robin BY CONCEPT, not by stem text: three direction questions read
    "facing North, right then left" / "facing East, right then left" / "facing North, left then
    right" — different words, so a stem-signature cap lets all three onto one page, which is
    exactly what happened the first time.

    `difficulty` FILTERS BEFORE THE DEAL, and that argument is the whole fix for the clustering One
    Step's owner complained about. The caller used to deal the entire pool round-robin and only
    then keep the rows of the band it wanted — but each concept's bucket is sorted hardest-first,
    so the early rounds are all hard rows and a band's questions only surface once a concept has
    run out of harder stock. The shallowest concept therefore reaches its medium and easy rows
    first and supplies almost the whole band on its own. Measured on the delivered papers: Set 1's
    medium band came back 6 Blood Relations out of 7 and its easy band 7 out of 8, which is how one
    concept took 16 of 50 questions while every round-robin in this file looked correct.

    `concept_used` (a Counter shared across the three band calls) plus `hard_cap` enforce a real
    ceiling per concept for the section as a whole. Passing the counter between calls is what makes
    it a section-level cap rather than three independent per-band ones that can each spend 4.
    """
    p = REPO / "question_bank_engine/drop/bssc/REASONING_GEN.json"
    if not p.exists():
        return []
    buckets = {}
    for q in json.load(io.open(p, encoding="utf-8")):
        if not (q.get("stem") and q.get("correct_answer") and len(q.get("options") or []) == 4):
            continue
        if gen_sig(q) in exclude:
            continue
        if difficulty is not None:
            d = q.get("difficulty") or (q.get("tag") or {}).get("difficulty") or 0
            if (d < 3) if difficulty >= 3 else (d != difficulty):
                continue
        # Restrict to the concepts that belong to one SYLLABUS topic. Like the difficulty filter
        # above, this has to happen BEFORE the round-robin deal — filtering a dealt list is what
        # produced the clustering this file has already been fixed for once.
        if only_concepts and (q.get("concept") or "?") not in only_concepts:
            continue
        if not numbers_agree(q):
            continue      # Hindi template dropped the rule ("twice its position") — see numbers_agree
        if analogy_ambiguous(q) or odd_one_out_ambiguous(q):
            continue      # two defensible answers both on offer — see the two _ambiguous gates
        q["_generated"] = True
        # The pool carries `difficulty` at the top level but no tag.difficulty, so the mix report
        # counted every generated reasoning question as difficulty 0 and printed a shortfall on a
        # section that was full. Mirror it into the tag the report actually reads.
        q.setdefault("tag", {})
        q["tag"].setdefault("section", "Reasoning")
        q["tag"].setdefault("difficulty", q.get("difficulty") or 2)
        buckets.setdefault(q.get("concept") or "?", []).append(q)
    for b in buckets.values():
        random.shuffle(b)
        # ...then hardest first WITHIN each concept. The round-robin deal keeps the section varied;
        # this makes it also honour the difficulty request, which it ignored entirely before —
        # Part III drew 29 easy questions from a pool holding 343 hard ones.
        b.sort(key=lambda q: -(q.get("difficulty") or (q.get("tag") or {}).get("difficulty") or 0))
    for k in list(buckets):                    # drop same-question-different-name clones
        seen, uniq = set(), []
        for q in buckets[k]:
            g = gen_sig(q)
            if g in seen:
                continue
            seen.add(g); uniq.append(q)
        buckets[k] = uniq
    order = sorted(buckets, key=lambda k: -len(buckets[k]))
    # Raise the per-concept cap only as far as the request forces. With 11 concepts a cap of 3
    # tops out at 33, so a 35-question Part III silently came back short — the paper printed 148.
    if order and hard_cap is None:
        cap_per_concept = max(cap_per_concept, -(-n // len(order)))
    # Deal round-robin so the section stays varied. The soft cap is a PREFERENCE, not a wall: once
    # every concept has contributed cap_per_concept, keep dealing rather than return a short
    # section — a 146-question paper is a worse outcome than a slightly uneven one. `hard_cap` IS
    # a wall, and the caller relaxes it a step at a time if the section cannot be filled.
    out, rnd, deepest = [], 0, max((len(v) for v in buckets.values()), default=0)
    while len(out) < n and rnd < deepest:
        progress = False
        for k in order:
            if len(out) >= n:
                break
            if hard_cap is not None and concept_used is not None and concept_used[k] >= hard_cap:
                continue
            if len(buckets[k]) > rnd:
                out.append(buckets[k][rnd])
                progress = True
                if concept_used is not None:
                    concept_used[k] += 1
        rnd += 1
        if not progress:
            break                       # every remaining concept is at its cap — let the caller
            #                             decide whether to relax it rather than spin to `deepest`
        if hard_cap is None and rnd == cap_per_concept and len(out) < n:
            print(f"  note: reasoning spread exceeded {cap_per_concept}/concept to fill the section")
    return out[:n]


# One concept took 16 of Part III's 50 questions in the paper One Step read, and the owner's words
# were "it contains only one topic". Four is about a tenth of the section and matches what a real
# BSSC Part III looks like across concepts.
REASONING_CONCEPT_CAP = 4


def generate_reasoning_section(want, mix, gen_taken, cap=REASONING_CONCEPT_CAP):
    """Part III, drawn to the SYLLABUS topic quotas with the per-concept cap kept inside each.

    The cap alone made the section even across our 19 CONCEPTS, which is not the same thing as
    even across खंड (ग)'s 12 named TOPICS — four of our concepts sit inside अंक गणितीय तर्कशक्ति,
    so at 4 apiece that one topic took 14 questions against a 6-question target while संबंध
    अवधारणा took 1 against 4. Quotas come first now; the cap still stops any single concept
    dominating the topic it belongs to.
    """
    from collections import Counter
    import syllabus_blueprint as SB
    want_by_topic = SB.quotas("Reasoning", want)
    if not want_by_topic:
        return _generate_reasoning_flat(want, mix, gen_taken, cap)
    used, out = Counter(), []
    # Deal band by band inside each topic, so the difficulty mix survives the topic quotas.
    for d in (3, 2, 1):
        band = mix.get(d, 0)
        if band <= 0:
            continue
        share = {t: max(1, round(band * want_by_topic[t] / want)) for t in want_by_topic}
        for topic in sorted(share, key=lambda t: -want_by_topic[t]):
            got_t = sum(1 for q in out if SB.topic_of("Reasoning", q.get("concept")) == topic)
            need = min(share[topic], want_by_topic[topic] - got_t, want - len(out))
            if need <= 0:
                continue
            picked = load_generated(need, exclude=gen_taken, difficulty=d,
                                    concept_used=used, hard_cap=cap,
                                    only_concepts=_concepts_for("Reasoning", topic))
            gen_taken.update(gen_sig(q) for q in picked)
            out += picked
    # Top up anything the quotas could not reach rather than print a short section, then say so.
    if len(out) < want:
        short = want - len(out)
        for step in range(8):
            extra = load_generated(want - len(out), exclude=gen_taken,
                                   concept_used=used, hard_cap=cap + step)
            gen_taken.update(gen_sig(q) for q in extra)
            out += extra
            if len(out) >= want:
                break
        print(f"  note: Part III topped up {short} question(s) outside the syllabus quotas")
    for line in SB.report("Reasoning", out[:want]):
        print(line)
    return out[:want]


def _concepts_for(section, topic_en):
    import syllabus_blueprint as SB
    for t in SB.topics(section):
        if t["en"] == topic_en:
            return set(t.get("concepts") or [])
    return set()


def _generate_reasoning_flat(want, mix, gen_taken, cap=REASONING_CONCEPT_CAP):
    """Part III, drawn to the difficulty mix AND to a per-concept ceiling for the whole section.

    The cap is shared across the three band draws through one Counter, so a concept cannot spend
    its allowance three times over. It is relaxed one step at a time if the pool genuinely cannot
    fill the section — an uneven paper beats a 147-question paper — and the relaxation is PRINTED,
    because a cap that quietly gives up is the same as no cap at all.

    The spread is printed on every build. The clustering that produced this function was invisible
    for two deliveries precisely because nothing ever stated what the section had actually drawn.
    """
    from collections import Counter
    used, out = Counter(), []
    for step in range(12):
        for d in (3, 2, 1):
            if len(out) >= want:
                break
            short = min(mix.get(d, 0), want - len(out)) if step == 0 else want - len(out)
            if short <= 0:
                continue
            got = load_generated(short, exclude=gen_taken, difficulty=d,
                                 concept_used=used, hard_cap=cap + step)
            gen_taken.update(gen_sig(q) for q in got)
            out += got
        if len(out) >= want:
            break
        if step == 0 or len(out) < want:
            print(f"  note: Part III could not fill at {cap + step}/concept "
                  f"({len(out)} of {want}) — relaxing the cap to {cap + step + 1}")
    spread = Counter(q.get("concept") or "?" for q in out)
    print(f"  Part III spread: {len(out)} questions over {len(spread)} concepts, "
          f"most-used {max(spread.values(), default=0)} — "
          + ", ".join(f"{k} {v}" for k, v in spread.most_common()))
    return out[:want]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logo", default=None, help="path to the institute's logo PNG")
    ap.add_argument("--out", default=str(REPO / "teacher_gtm/OneStep_BSSC_150.pdf"))
    ap.add_argument("--structure", choices=["real4", "official3"], default="real4",
                    help="real4 = 100%% real, 4 parts shaped to what the papers actually contain "
                         "(GS/Sci+Maths/Hindi/Reasoning). official3 = the commission's 3x50 "
                         "layout, which needs ~35 GENERATED reasoning questions to fill Part III.")
    ap.add_argument("--set", type=int, default=1,
                    help="Which set of the series to build. Sets never share a question: every "
                         "question a set uses is recorded in the manifest, and later sets exclude "
                         "everything the other sets already took.")
    ap.add_argument("--manifest", default=str(REPO / "teacher_gtm/InterLevel_sets_used.json"),
                    help="Ledger of which questions each set has consumed.")
    ap.add_argument("--pin", action="store_true",
                    help="Rebuild EXACTLY the questions the manifest already records for this set, "
                         "instead of drawing fresh. Once a set has been fact-checked question by "
                         "question, any redraw silently swaps in unverified ones — removing three "
                         "questions reshuffled the whole paper and quietly changed Parts I and II. "
                         "Pinning is what makes 'this set is verified' stay true.")
    ap.add_argument("--inter-level", action="store_true",
                    help="Build for BSSC 2nd Inter Level (Advt 02/23-A). Forces the commission's "
                         "OWN three-section prelim structure — GS / Science+Maths / Mental Ability, "
                         "with NO Hindi Language section, because the official syllabus does not "
                         "have one — and drops maths that is above the Inter Level syllabus.")
    ap.add_argument("--hindi-source", choices=["generated", "real"], default="generated",
                    help="Which Hindi Language section to print. DEFAULT IS 'generated' because "
                         "the REAL Hindi-language questions in these papers are badly OCR-corrupted "
                         "- see the note in load_hindi_generated().")
    ap.add_argument("--all-generated", action="store_true",
                    help="Build every question from the generators — no official past-paper "
                         "questions at all. Every answer is then computed in Python or looked up "
                         "in a verified fact table.")
    ap.add_argument("--generate-gs", action="store_true",
                    help="Fill a HARD General Studies shortfall with statement-based and "
                         "match-the-pairs questions built from verified fact tables. This is the "
                         "only way the difficulty mix can be met in GS: the bank holds nothing "
                         "above difficulty 2 in that section.")
    ap.add_argument("--generate-gk", action="store_true",
                    help="Top up a General Studies shortfall from staticgkgen. OFF by default: "
                         "its questions are correct-by-construction but difficulty-1 recall, "
                         "which is the register the institute already rejected.")
    ap.add_argument("--gs-rev-share", type=float, default=None,
                    help="percentage of General Studies asked as reverse-lookup. The commission's "
                         "measured share is 14.3; raising it is the only honest way to make GS "
                         "harder, and it makes the paper less like a real one.")
    ap.add_argument("--show-topic", action="store_true",
                    help="print the SYLLABUS TOPIC and question type on each question, and a "
                         "topic-distribution table under each section header — without the "
                         "difficulty badge. For a student copy: a candidate who reads 'कठिन' "
                         "before answering has been primed, but knowing the topic helps review.")
    ap.add_argument("--show-difficulty", action="store_true",
                    help="Print a difficulty badge (सरल / मध्यम / कठिन) beside every question. "
                         "This is for a REVIEW copy sent to the institute, not for students: it "
                         "turns 'the paper is too basic' into per-question feedback we can act "
                         "on, and it primes a student who sees it before answering.")
    ap.add_argument("--generate-maths", action="store_true",
                    help="Fill any HARD maths shortfall from quantgen instead of leaving the "
                         "section short. Refused on a bilingual paper until quantgen has Hindi.")
    ap.add_argument("--difficulty-mix", default="10:60:30",
                    help="Share of EASY:MEDIUM:HARD questions to aim for, as percentages of each "
                         "section — difficulty 1 : difficulty 2 : difficulty 3+. Default 10:60:30. "
                         "Pure hardest-first ('0:0:100') makes a paper with no entry point; the "
                         "bank also cannot supply it. Whatever a band cannot fill is taken from "
                         "the next band DOWN in easiness, and the shortfall is reported.")
    ap.add_argument("--sets", type=int, default=2,
                    help="How many sets this series will have. The hard questions are dealt "
                         "round-robin across that many lanes so every set gets an equal share, "
                         "instead of the first one built taking them all.")
    ap.add_argument("--key-json", default=None,
                    help="Also write the answer key, numbered exactly as printed, with each "
                         "answer's provenance. build_verification_sheet.py consumes this so the "
                         "sheet and the paper cannot disagree about what question 47 is.")
    a = ap.parse_args()
    if a.gs_rev_share is not None:
        globals()["GS_REV_SHARE"] = a.gs_rev_share

    try:
        _e, _m, _h = (int(x) for x in a.difficulty_mix.split(":"))
    except ValueError:
        raise SystemExit("--difficulty-mix wants three numbers like 10:60:30")
    if _e + _m + _h != 100:
        raise SystemExit(f"--difficulty-mix must sum to 100, got {_e + _m + _h}")

    _mix_call = {"n": 0}

    def mix_for(want):
        """The requested PERCENTAGES as whole-question counts for a section of `want` questions.

        15% of a 50-question section is 7.5 questions, which cannot be printed. Rounding the same
        way in every section compounds that half three times over, and the paper came out 14/16/70
        against a requested 15/15/70. So the spare question alternates between the easy and medium
        bands from one section to the next, and the paper-wide totals land as close to the request
        as whole questions allow.
        """
        hard = round(want * _h / 100)
        rest = want - hard
        exact_e = want * _e / 100
        lo = int(exact_e)
        easy = (lo + 1) if (_mix_call["n"] % 2 == 0 and exact_e != lo) else lo
        _mix_call["n"] += 1
        easy = max(0, min(easy, rest))
        return {3: hard, 2: rest - easy, 1: easy}

    random.seed(20260820 + a.set * 1009)
    manifest = load_manifest(a.manifest)
    used_real, used_gen = taken_by_other_sets(manifest, a.set)
    if used_real or used_gen:
        print(f"  excluding {len(used_real)} real + {len(used_gen)} generated questions "
              f"already used by other sets")
    qs = load(inter_level=a.inter_level, exclude=used_real)
    by = {}
    for q in qs:
        by.setdefault(q["tag"]["section"], []).append(q)

    used, tmpl = set(), {}
    if a.inter_level:
        a.structure = "official3"
    if a.structure == "real4":
        # The shape the PAPERS actually have. These five are 10th/8th-level and clerk-grade exams,
        # and the measured blueprints put Hindi at 19-31% of three of them and Reasoning at 0%.
        # A 4-part paper is therefore closer to what these candidates sat than the 3x50 template,
        # and — the reason it was chosen — it can be filled ENTIRELY with real questions.
        SPEC = [
            ("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", ["General Studies"], 50),
            ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (General Science & Mathematics)",
             ["Mathematics", "General Science"], 50),
            ("भाग–III / PART–III : हिंदी भाषा (Hindi Language)", ["Hindi"], 33),
            ("भाग–IV / PART–IV : सामान्य बुद्धि परीक्षण (Reasoning)", ["Reasoning", "English"], 17),
        ]
    else:
        # The commission's printed CGL / Inter-Level layout. Only 15 real bilingual reasoning
        # questions exist, so Part III is topped up from `reasoninggen` — computed answers, and
        # bilingual, so the paper stays bilingual throughout. This trades the "every question is
        # real" claim for the official shape; that is why it is not the default.
        # खंड (ग) मानसिक क्षमता जाँच lists ONLY reasoning shapes — सादृश्य, समानता एवं भिन्नता,
        # स्थान कल्पना, समस्या समाधान, विश्लेषण, दृश्य स्मृति, विभेद, अवलोकन, संबंध अवधारणा,
        # अंक गणितीय तर्कशक्ति, अंक गणितीय संख्या श्रृंखला, कूट लेखन एवं कूट व्याख्या. English
        # grammar/vocabulary is NOT among them, so it is excluded for an Inter Level paper even
        # though we hold 16 such real questions.
        third = ["Reasoning"] if a.inter_level else ["Reasoning", "English"]
        SPEC = [
            ("भाग–I / PART–I : सामान्य अध्ययन (General Studies)", ["General Studies"], 50),
            ("भाग–II / PART–II : सामान्य विज्ञान एवं गणित (General Science & Mathematics)",
             ["Mathematics", "General Science"], 50),
            ("भाग–III / PART–III : मानसिक क्षमता जाँच (Mental Ability / Reasoning)", third, 50),
        ]

    # Generated top-up belongs ONLY in the reasoning part. Topping up Science+Maths with it put a
    # number analogy into Part II — wrong section — and, because each part called the generator
    # independently, the same question could be dealt twice ("3 : 9 :: 11 : ?" appeared as both
    # Q100 and Q127). Any shortfall in an earlier part is carried into the reasoning part instead,
    # so every question stays in its right section and the paper still totals 150. The
    # advertisement names the three sections without fixing a per-section count, so 47/53 is as
    # faithful as 50/50.
    if a.pin and str(a.set) in manifest:
        want_real = [tuple(x) for x in manifest[str(a.set)]["real"]]
        want_gen = list(manifest[str(a.set)]["gen"])   # ORDER matters: a pinned rebuild must
        #                                                    reproduce the paper, not just its contents
        by_id = {}
        for q in qs:
            by_id[tuple(qid(q))] = q
        missing = [r for r in want_real if tuple(r) not in by_id]
        if missing:
            print(f"  PIN: {len(missing)} pinned questions are no longer eligible "
                  f"(newly excluded?) — {missing[:5]}")
        pinned_real = [by_id[tuple(r)] for r in want_real if tuple(r) in by_id]
        # Prefer the FULL generated questions if the manifest carries them. Restoring a generated
        # question by signature is not exact: gen_sig deliberately ignores the actor name, so it
        # identifies a question SHAPE. Measured across two draws of the same pool, 31 of 307
        # signatures resolved to a DIFFERENT concrete question — which is how a pinned rebuild of
        # Set 2 came back with the same 150 shapes but different names and letters, no longer the
        # file the institute was holding. `freeze_generated.py` writes gen_full; the signature path
        # below is the fallback for manifests written before it existed.
        full = manifest[str(a.set)].get("gen_full")
        if full:
            # Re-gate on the way back in. gen_full bypasses load_generated, so a question pinned
            # before a gate existed would sail past it forever — which is exactly what happened
            # when a blind solve found "5 : 15 :: 7 : ?" answerable as both 21 (x3) and 28
            # (triangular), with both printed. A pin must preserve the paper, not its defects.
            # Refresh each pinned question from the CURRENT pool, matched on its English stem.
            # gen_full stores a copy, so a correction to the generated bank never reached a pinned
            # paper: the Hindi kinship fix landed in REASONING_GEN.json and the paper went on
            # printing पोती for a daughter's daughter. A pin should fix WHICH questions the paper
            # asks, not freeze a stale copy of their text.
            # Refresh ONLY where the stem identifies exactly one pool row. `load_generated`
            # shuffles, so a last-wins dict silently picked either of two rows sharing a stem, and
            # a pinned rebuild came back with one distractor changed from OTTER to TREAT — same
            # question, same key, not the file the institute is holding, and the line below still
            # said "exact". Where the pool is ambiguous the frozen copy wins and the count says so.
            by_stem = {}
            for g in load_generated(10 ** 6):
                by_stem.setdefault(re.sub(r"\s+", " ", (g.get("stem") or "")).strip(), []).append(g)

            def _key(g):
                return re.sub(r"\s+", " ", (g.get("stem") or "")).strip()
            refreshed = sum(1 for g in full if len(by_stem.get(_key(g), ())) == 1)
            ambiguous = sum(1 for g in full if len(by_stem.get(_key(g), ())) > 1)
            full = [by_stem[_key(g)][0] if len(by_stem.get(_key(g), ())) == 1 else g for g in full]
            if refreshed or ambiguous:
                print(f"  PIN: refreshed {refreshed}/{len(full)} generated questions from the "
                      f"current pool (corrections propagate; the selection stays pinned)"
                      + (f"; kept {ambiguous} frozen copy(ies) whose stem matches more than one "
                         f"pool row" if ambiguous else ""))
            pinned_gen = [dict(g, _generated=True) for g in full
                          if numbers_agree(g) and not analogy_ambiguous(g)
                          and not odd_one_out_ambiguous(g)]
            if len(pinned_gen) < len(full):
                print(f"  PIN: dropped {len(full) - len(pinned_gen)} pinned generated question(s) "
                      f"that no longer pass the gates")
            print(f"  PIN: rebuilding the recorded set — {len(pinned_real)} real + "
                  f"{len(pinned_gen)} generated (exact, from gen_full)")
        else:
            gen_by_sig = {gen_sig(g): g for g in load_generated(10 ** 6)}
            pinned_gen = [gen_by_sig[sg] for sg in want_gen if sg in gen_by_sig]
            print(f"  PIN: rebuilding the recorded set — {len(pinned_real)} real + "
                  f"{len(pinned_gen)} generated (BY SIGNATURE — not exact; run "
                  f"freeze_generated.py to pin the actual questions)")

    paper, n, carry = [], 0, 0
    gen_taken = set(used_gen)
    pin_pool = list(pinned_real) if (a.pin and str(a.set) in manifest) else None
    pin_gen = list(pinned_gen) if (a.pin and str(a.set) in manifest) else None
    if pin_pool is not None:
        # Seed the dedup tables with everything already pinned, so a top-up draw cannot re-select
        # a question the paper is about to print anyway. Without this, replacing four excluded
        # questions in Set 2 reintroduced a duplicate pair and a repeated odd-one-out.
        for q in pin_pool:
            register(q, used, tmpl)
        gen_taken |= {gen_sig(q) for q in pin_gen}
    for idx, (title, secs, want) in enumerate(SPEC):
        if pin_pool is not None:
            got = [q for q in pin_pool if q["tag"]["section"] in secs][:want]
            for q in got:
                pin_pool.remove(q)
            # Route the pinned GENERATED questions by their own section tag, exactly like the real
            # ones. They used to be handed to the last section only, which was harmless when a
            # paper was mostly real questions with a generated tail — and silently catastrophic
            # once papers went 100% generated on 2026-08-20: Parts I and II matched nothing, so a
            # pinned rebuild drew 100 FRESH questions while the log said "exact, from gen_full".
            # A pin that replaces two thirds of the paper is worse than one that refuses, because
            # the line above it says the opposite.
            if len(got) < want:
                take = [q for q in pin_gen
                        if (q.get("tag") or {}).get("section") in secs][:want - len(got)]
                for q in take:
                    pin_gen.remove(q)
                got += take
            if idx == len(SPEC) - 1 and len(got) < want:
                got = got + pin_gen[:want - len(got)]        # mop up anything unrouted
            # Top up whatever the exclusions took out. Without this a pinned rebuild after an
            # exclusion silently prints a short paper — the section just ends early, and nothing
            # says so. Replacements are drawn the normal way and are NOT covered by the earlier
            # verification, so they have to go back through the checks.
            if len(got) < want:
                short = want - len(got)
                pool = [q for s in secs for q in by.get(s, []) if q not in got]
                fresh = pick(pool, short, used, tmpl, salt="shared",
                             stripe=((a.set - 1) % a.sets, a.sets), mix=mix_for(short))
                if idx == len(SPEC) - 1 and len(fresh) < short:
                    more = load_generated(short - len(fresh), exclude=gen_taken)
                    gen_taken |= {gen_sig(q) for q in more}
                    fresh += more
                print(f"  PIN: topped up {len(fresh)} replacement(s) in {title[:34]} "
                      f"— RE-VERIFY these")
                got += fresh
            paper.append((title, got)); n += len(got)
            continue
        if a.all_generated:
            got = generate_whole_section(secs, want, mix_for(want), gen_taken, a.inter_level, idx)
            paper.append((title, got)); n += len(got)
            continue
        pool = [q for s in secs for q in by.get(s, [])]
        last = idx == len(SPEC) - 1
        target = want + carry if last else want
        # NOTE: a syllabus topic quota was tried on this REAL draw and measured WORSE — Part I
        # fell from 7 topics to 5 and 23 questions landed in "अन्य", because capping the topics
        # the tagger CAN label just pushes the draw into the ones it cannot. The quota belongs on
        # the generated draw, where every question's topic is known by construction.
        got = pick(pool, target, used, tmpl, salt="shared",
                   stripe=((a.set - 1) % a.sets, a.sets), mix=mix_for(target))
        # A maths section that came back short of HARD questions can be topped up by generation —
        # the bank has no difficulty-3 arithmetic to give, and that is the whole reason the mix
        # could not be met.
        if a.generate_gs and "General Studies" in secs:
            want = mix_for(target)
            have3 = sum(1 for q in got if ((q.get("tag") or {}).get("difficulty") or 0) >= 3)
            if want[3] > have3:
                fresh = generate_gs_forms(want[3] - have3, gen_taken, a.inter_level)
                gen_taken |= {gen_sig(q) for q in fresh}
                got = _swap_in(got, fresh)
        if a.generate_gk and "General Studies" in secs and len(got) < target:
            fresh = generate_static_gk(target - len(got), gen_taken, a.inter_level)
            gen_taken |= {gen_sig(q) for q in fresh}
            got += fresh
        if a.generate_maths and "Mathematics" in secs:
            want = mix_for(target)
            have3 = sum(1 for q in got if ((q.get("tag") or {}).get("difficulty") or 0) >= 3)
            # Part II is Science AND Maths, so split the hard shortfall between the two rather
            # than letting whichever runs second overwrite the first.
            if want[3] > have3:
                short = want[3] - have3
                sci = generate_science(short // 3 or 1, gen_taken)
                gen_taken |= {gen_sig(q) for q in sci}
                got = _swap_in(got, sci)
                have3 += len(sci)
            if want[3] > have3:
                new_qs = generate_maths(want[3] - have3, 4, gen_taken, a.inter_level)
                gen_taken |= {gen_sig(q) for q in new_qs}
                got = _swap_in(got, new_qs)
        if not last:
            carry += target - len(got)
        elif len(got) < target:
            fresh = load_generated(target - len(got), exclude=gen_taken)
            gen_taken |= {gen_sig(q) for q in fresh}
            got += fresh
        if secs == ["Hindi"] and a.hindi_source == "generated":  # noqa: E501
            got = load_hindi_generated(want)   # (real4 only; Inter Level has no Hindi section)
        paper.append((title, got)); n += len(got)

    # Survey q8 — "Where should the hard questions sit?" -> "Spread evenly through the paper".
    # Applied to EVERY section here rather than inside one generator, because until now only Part
    # II was ordered at all and the answer is about the whole paper. Deterministic in the set
    # number, so a pinned rebuild still reproduces its file exactly (gotcha #18).
    _ord = random.Random(20260822 + a.set)
    _SCI = {"sciencegen", "science_tables"}

    # A pinned rebuild must NOT be re-ordered. The manifest records the paper as PRINTED, so the
    # order it restores is already final — running the spread over it again would deal an
    # already-dealt section and hand back the same 150 questions in a different order, which is
    # gotcha #18 all over again in a new place.
    _pinned = bool(a.pin and str(a.set) in manifest)
    blocks, owner = [], []
    for si, (_t, items) in enumerate(paper if not _pinned else []):
        # Part II keeps science and maths as blocks — the section is named "सामान्य विज्ञान एवं
        # गणित" and a candidate expects the two subjects in order — so each is paced separately
        # and no later pass may move a question from one into the other.
        if any(q.get("source_pdf") in _SCI for q in items):
            parts = [[q for q in items if q.get("source_pdf") in _SCI],
                     [q for q in items if q.get("source_pdf") not in _SCI]]
        else:
            parts = [items]
        for p in parts:
            blocks.append(spread_questions(p, _ord))
            owner.append(si)

    if not _pinned:
        break_hard_runs(blocks)
        merged = {}
        for si, blk in zip(owner, blocks):
            merged.setdefault(si, []).extend(blk)
        paper = [(t, merged[si]) for si, (t, _items) in enumerate(paper)]
    for t, items in paper:
        pos = [str(i + 1) for i, q in enumerate(items) if _band(q) <= 2]
        print(f"  order — {t[:34]:34s} easy/medium at {', '.join(pos) or '(none)'}")

    logo_html, logo_b64, logo_ext = "", "", "png"
    if a.logo and os.path.exists(a.logo):
        logo_b64 = base64.b64encode(open(a.logo, "rb").read()).decode()
        logo_ext = "png" if a.logo.lower().endswith("png") else "jpeg"
        logo_html = f'<img class="logo" src="data:image/{logo_ext};base64,{logo_b64}">'

    # The vision extraction was not consistent about WHICH field held which language: measured
    # across 497 pairs, only 59% were correct, 12% arrived swapped and 27% held Hindi in both.
    # Rendering by field name therefore printed some questions twice and some back-to-front.
    # Route by SCRIPT instead — Devanagari is Hindi, full stop — and print a language only once.
    DEV = re.compile(r"[\u0900-\u097f]")
    # "A 30 (B) 35 (C) 38 (D) 40" — an option list sitting in a stem field.
    OPTLIST = re.compile(r"\(?[Aa]\)?\s.{0,40}?\([Bb]\).{0,40}?\([Cc]\)")

    def split_lang(a, b):
        """(hindi, english) from two texts whose labels we do not trust."""
        a, b = (a or "").strip(), (b or "").strip()
        da, db = bool(DEV.search(a)), bool(DEV.search(b))
        if da and not db:
            return a, b
        if db and not da:
            return b, a
        if da and db:
            return (a if len(a) >= len(b) else b), ""      # both Hindi -> show once
        return "", (a if len(a) >= len(b) else b)          # both English -> show once

    n_gen = sum(1 for _, items in paper for q in items if q.get("_generated"))
    qh, keys, keyrows, i = [], [], [], 0
    for title, items in paper:
        g = sum(1 for q in items if q.get("_generated"))
        note = ('<div class="pnote">इस भाग के सभी प्रश्न BSSC की आधिकारिक विगत परीक्षाओं से '
                '&middot; उत्तर आयोग की आदर्श उत्तर कुंजी से।</div>') if not g else (
               f'<div class="pnote">इस भाग के {g} प्रश्न Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं '
               f'(मानक व्याकरण पर आधारित) &middot; ये विगत परीक्षा के प्रश्न नहीं हैं।</div>')
        qh.append(f'<h2 class="sec">{html.escape(title)}</h2>{note}')
        # Only on a review copy. A student who sees the spread before answering learns nothing
        # useful from it, and it is the reviewer — not the candidate — who is being asked whether
        # the distribution is right.
        if a.show_difficulty or a.show_topic:
            qh.append(coverage_table(items, with_difficulty=a.show_difficulty))
        for q in items:
            i += 1
            # Some stems in the 8th-Level paper are not stems at all — the extractor put the OPTION
            # LIST in the field ("A 30 (B) 35 (C) 38 (D) 40"). Printed, that is a junk line above
            # the real options. Blank it and let the other language carry the question.
            hi_raw, en_raw = q.get("stem_hi"), q.get("stem")
            if OPTLIST.search(hi_raw or ""):
                hi_raw = ""
            if OPTLIST.search(en_raw or ""):
                en_raw = ""
            hi_stem, en_stem = split_lang(hi_raw, en_raw)
            oh_l, oe_l = [], []
            for oa, ob in zip(q.get("options_hi") or q["options"], q["options"]):
                h, e = split_lang(oa.get("text"), ob.get("text"))
                # A language-NEUTRAL option ("5", "12.5%") belongs to both halves. split_lang hands
                # it to English alone, which is right for a stem and wrong here: a question whose
                # options are two numbers and two Hindi phrases rendered a two-option Hindi block,
                # tripped the short-block fallback below, and printed the ENGLISH options to a
                # Hindi reader even though the bank held the Hindi. 5 reads as 5 in both scripts.
                if not h and e and not DEV.search(str(oa.get("text") or "")):
                    h = e
                oh_l.append((oa["label"], h)); oe_l.append((ob["label"], e))
            def render(pairs):
                return "".join(f'<span class="op"><b>({lb})</b> {esc(t)}</span>'
                               for lb, t in pairs if str(t).strip())
            oh_html, oe_html = render(oh_l), render(oe_l)
            # A language can lose SOME options, not just all of them: when split_lang routes option
            # (A) and (C) one way and (B) and (D) the other, one block prints two options and the
            # question is unanswerable. Only a FULL set is acceptable, so fall back whenever the
            # rendered count is short.
            want = len(q["options"])
            if oh_html.count("<span class=\"op\">") < want:
                oh_html = oe_html if oe_html.count("<span class=\"op\">") == want else ""
            if oe_html.count("<span class=\"op\">") < want:
                oe_html = oh_html if oh_html.count("<span class=\"op\">") == want else ""
            # When the options are language-NEUTRAL (numbers, formulae, single letters) split_lang
            # hands both copies to the English side, so a Hindi-only question rendered its options
            # block EMPTY and never rendered an English block — 26 of 470 questions showed a stem
            # with no options at all. Numbers read the same in both scripts, so reuse them.
            if not oh_html:
                oh_html = oe_html
            if not oe_html:
                oe_html = oh_html
            if not oh_html and not oe_html:      # nothing renderable at all — skip the question
                i -= 1
                continue
            block = f'<div class="q">'
            if a.show_difficulty or a.show_topic:
                # The owner said "ye basic ka bhi basic hai" about a whole paper. A badge per
                # question turns that into "question 14 is right, question 61 is too easy" —
                # feedback we can actually build against, and the raw material for calibrating
                # our difficulty tags against a real examiner's judgement.
                dlab = {1: ("सरल", "Easy"), 2: ("मध्यम", "Medium")}.get(
                    (q.get("tag") or {}).get("difficulty") or 0, ("कठिन", "Hard"))
                dpart = f'{dlab[0]} &middot; {dlab[1]}' if a.show_difficulty else ""
                # The badge carries the difficulty and nothing else. It named the source too,
                # which put our brand on every question of a paper that goes out under the
                # institute's own logo — and the source is not what the reviewer is being asked
                # to judge.
                # Three fields, and each one earns its place by catching a defect the other two
                # cannot see. TOPIC is the commission's own vocabulary and is the only thing that
                # shows syllabus coverage. TYPE is what the owner was describing when he said the
                # reasoning was "only one topic" and the GS "style is similar" — a section can be
                # perfectly spread across topics and still ask one question type forty times.
                # DIFFICULTY is what he has been asked to calibrate.
                tp = question_topics(q)
                tlab = " · ".join(short_hi(h) for _e, h in tp[:2]) + (" आदि" if len(tp) > 2 else "")
                # An unmapped topic printed an EMPTY badge box, which reads as a rendering fault.
                # Static GK genuinely spans the syllabus and has no single home; say so instead.
                if not tlab.strip():
                    tlab = "सामान्य ज्ञान"
                block += (f'<span class="dbadge">{dpart}'
                          + (f'<i>{esc(tlab)}</i>' if tlab else "")
                          + (f'<i class="ty">{esc(str(q.get("concept") or ""))}</i>')
                          + '</span>')
            # The list forms build their items on separate LINES, and HTML collapses those to
            # spaces — so a four-row match-the-pairs printed as one unbroken paragraph
            # ("A. 368 — freedom of conscience ... B. 24 — the Finance Commission C. 17 — ...").
            # The question was answerable and genuinely hard to read, which is a bad combination on
            # a paper whose whole purpose is to have its difficulty judged.
            lines = lambda t: t.replace("\n", "<br>")
            if hi_stem:
                block += (f'<div class="hi"><span class="n">{i}.</span> {lines(esc(hi_stem))}</div>'
                          f'<div class="ops">{oh_html}</div>')
            if en_stem:
                lead = "" if hi_stem else f'<span class="n">{i}.</span> '
                block += (f'<div class="en">{lead}{lines(esc(en_stem))}</div>'
                          f'<div class="ops">{oe_html}</div>')
            qh.append(block + "</div>")
            keys.append(f'<span class="k">{i}. <b>{q["correct_answer"]}</b>'
                        f'{"<i>*</i>" if q.get("_generated") else ""}</span>')
            # Same place, same `i`, so the verification sheet can never number a row differently
            # from the printed paper. It must be here and not re-derived elsewhere: this loop can
            # skip a question that has nothing renderable (see `i -= 1` above), and any second
            # implementation of the ordering would drift silently past that point.
            keyrows.append({
                "n": i,
                "answer": q["correct_answer"],
                "answer_text": next((o["text"] for o in q.get("options") or []
                                     if o["label"] == q["correct_answer"]), ""),
                "generated": bool(q.get("_generated")),
                "solution": q.get("solution"),
                "source_pdf": q.get("source_pdf"),
                "source_number": q.get("number"),
            })

    TITLE_LINE = ("बिहार कर्मचारी चयन आयोग &mdash; द्वितीय इंटर स्तरीय संयुक्त प्रतियोगिता परीक्षा "
                  "(वि0सं0&ndash;02/23-A) &mdash; अभ्यास प्रश्न-पत्र" if a.inter_level
                  else "बिहार कर्मचारी चयन आयोग (BSSC) &mdash; अभ्यास प्रश्न-पत्र")
    PATTERN_NOTE = ("<br>5. यह प्रश्न-पत्र आयोग द्वारा वि0सं0&ndash;02/23(A) में प्रकाशित "
                    "<b>प्रारंभिक परीक्षा की योजना</b> के अनुरूप है &mdash; 150 प्रश्न, "
                    "प्रत्येक सही उत्तर 4 अंक, प्रत्येक गलत उत्तर &ndash;1, कुल 600 अंक, समय 2 घंटा 15 मिनट, "
                    "तीन खण्ड। गणित के प्रश्न आयोग के <b>अंकगणित-आधारित</b> पाठ्यक्रम तक सीमित रखे गए हैं।"
                    if a.inter_level else "")
    # Cover page: the officially released syllabus, so the institute can see exactly what the
    # paper was built against. Every figure here comes from Advt 02/23(A) and its corrigenda —
    # see teacher_gtm/BSSC_INTER_LEVEL_FACTSHEET.md for the document-by-document sourcing.
    COVER = f"""<div class="cover">
  <div class="lh">{logo_html}<div>
    <div class="co">ONE STEP EDUCATION</div><div class="sub2">PATNA</div>
    <div class="sub">बिहार कर्मचारी चयन आयोग &mdash; <b>द्वितीय इंटर स्तरीय संयुक्त प्रतियोगिता परीक्षा</b></div>
    <div class="sub">विज्ञापन संख्या <b>02/23 (A)</b> &middot; कुल रिक्तियाँ <b>25,311</b></div>
    <div class="setno">अभ्यास प्रश्न-पत्र &mdash; <b>सेट {a.set}</b> / PRACTICE PAPER &mdash; <b>SET {a.set}</b></div>
  </div></div><div class="rule"></div>

  <div class="claim">यह अभ्यास प्रश्न-पत्र बिहार कर्मचारी चयन आयोग द्वारा विज्ञापन संख्या&ndash;02/23(A) में
  <b>आधिकारिक रूप से प्रकाशित पाठ्यक्रम एवं परीक्षा-योजना</b> के आधार पर तैयार किया गया है।<br>
  <span class="en2">This practice paper has been prepared strictly on the syllabus and examination
  scheme officially published by the Bihar Staff Selection Commission in Advertisement No. 02/23 (A).</span></div>

  <h2 class="sec">प्रारंभिक परीक्षा की योजना / EXAMINATION SCHEME</h2>
  <table class="tb">
    <tr><td>परीक्षा की प्रकृति</td><td>वस्तुनिष्ठ (बहुविकल्पीय)</td></tr>
    <tr><td>कुल प्रश्न</td><td><b>150</b></td></tr>
    <tr><td>अंक</td><td>प्रत्येक सही उत्तर <b>+4</b> &middot; कुल <b>600 अंक</b></td></tr>
    <tr><td>ऋणात्मक अंकन</td><td>प्रत्येक गलत उत्तर पर <b>&ndash;1 अंक</b></td></tr>
    <tr><td>अवधि</td><td><b>2 घंटा 15 मिनट</b></td></tr>
    <tr><td>विकल्प</td><td>4</td></tr>
    <tr><td>माध्यम</td><td>हिन्दी एवं अंग्रेज़ी &mdash; <b>भिन्नता होने पर अंग्रेज़ी प्रश्न मान्य</b></td></tr>
    <tr><td>चयन</td><td>प्रारंभिक परीक्षा से कोटिवार रिक्तियों के <b>5 गुना</b> अभ्यर्थी मुख्य परीक्षा हेतु</td></tr>
  </table>

  <div class="callout"><b>⭐ यह परीक्षा &ldquo;पुस्तक सहित&rdquo; ली जाती है</b> (परीक्षा संचालन नियमावली&ndash;2010, कंडिका&ndash;12)।
  अभ्यर्थी <b>तीन पुस्तकें</b> ले जा सकते हैं &mdash; सामान्य अध्ययन, गणित एवं सामान्य विज्ञान हेतु एक-एक।
  केवल <b>NCERT / B.S.E.B. / I.C.S.E. एवं अन्य बोर्ड की पाठ्य-पुस्तकें</b> मान्य हैं। गाइड, फोटोकॉपी,
  हस्तलिखित कागज़, नोट्स एवं इलेक्ट्रॉनिक उपकरण <b>पूर्णतः वर्जित</b> हैं। पुस्तक पर केवल अपना नाम एवं
  रौल नंबर लिखें &mdash; इसके अतिरिक्त कुछ भी लिखा मिलने पर अभ्यर्थिता रद्द।</div>

  <h2 class="sec">आधिकारिक पाठ्यक्रम / OFFICIAL SYLLABUS</h2>
  <div class="syl"><b>खंड (क) &mdash; सामान्य अध्ययन</b><br>
  अभ्यर्थी के आस-पास के वातावरण की सामान्य जानकारी तथा समाज में उसके अनुप्रयोग की जाँच। बिहार, भारत एवं
  उसके पड़ोसी देशों पर विशेष बल।<br>
  <i>(i) सम-सामयिक विषय:</i> वैज्ञानिक प्रगति · राष्ट्रीय/अंतर्राष्ट्रीय पुरस्कार · भारतीय भाषाएँ · पुस्तक · लिपि ·
  राजधानी · मुद्रा · खेल-खिलाड़ी · महत्वपूर्ण घटनाएँ<br>
  <i>(ii) भारत और उसके पड़ोसी देश:</i> पड़ोसी देशों का इतिहास · भारत का इतिहास · संस्कृति · भूगोल · आर्थिक परिदृश्य ·
  स्वतंत्रता आन्दोलन · भारतीय कृषि एवं प्राकृतिक संसाधन · भारत का संविधान एवं राज्य व्यवस्था · राजनीतिक प्रणाली ·
  पंचायती राज · सामुदायिक विकास · पंचवर्षीय योजना · <b>राष्ट्रीय आन्दोलन में बिहार का योगदान</b></div>

  <div class="syl"><b>खंड (ख) &mdash; सामान्य विज्ञान एवं गणित</b> <span class="lvl">(मैट्रिक स्तर)</span><br>
  <i>(i) सामान्य विज्ञान:</i> भौतिक शास्त्र · रसायन शास्त्र · जीव विज्ञान · भूगोल<br>
  <i>(ii) गणित:</i> संख्या पद्धति · पूर्ण संख्याओं का अभिकलन · दशमलव और भिन्न · संख्याओं के बीच परस्पर संबंध ·
  मूलभूत अंक गणितीय संक्रियाएँ · प्रतिशत · अनुपात तथा समानुपात · औसत · ब्याज · लाभ और हानि</div>

  <div class="syl"><b>खंड (ग) &mdash; मानसिक क्षमता जाँच</b> <span class="lvl">(शाब्दिक एवं गैर-शाब्दिक)</span><br>
  सादृश्य · समानता एवं भिन्नता · स्थान कल्पना · समस्या समाधान · विश्लेषण · दृश्य स्मृति · विभेद · अवलोकन ·
  संबंध अवधारणा · अंक गणितीय तर्कशक्ति · अंक गणितीय संख्या श्रृंखला · कूट लेखन एवं कूट व्याख्या</div>

  <h2 class="sec">न्यूनतम अर्हतांक / QUALIFYING MARKS</h2>
  <table class="tb">
    <tr><td>सामान्य वर्ग</td><td>40%</td><td>अनुसूचित जाति / जनजाति</td><td>32%</td></tr>
    <tr><td>पिछड़ा वर्ग</td><td>36.5%</td><td>महिला (सभी वर्ग)</td><td>32%</td></tr>
    <tr><td>अत्यंत पिछड़ा वर्ग</td><td>34%</td><td>दिव्यांग (सभी वर्ग)</td><td>32%</td></tr>
  </table>

  <div class="src">स्रोत: आयोग का विज्ञापन 02/23(A) दिनांक 27.09.2025 एवं शुद्धि पत्र दिनांक 13.02.2026
  (bssc.bihar.gov.in)। संकलन: Acharya &mdash; TrigunAI Innovations Pvt Ltd</div>
</div>"""

    HEAD = f"""<div class="lh">{logo_html}<div>
<div class="co">ONE STEP EDUCATION</div><div class="sub2">PATNA</div>
<div class="sub">{TITLE_LINE}</div>
<div class="sub"><b>{"सेट " + str(a.set) + " · " if a.inter_level else ""}</b>आदर्श उत्तर कुंजी सहित</div>
</div></div><div class="rule"></div>"""

    # position:fixed repeats on every printed page in Chrome, which is what makes this a
    # per-page watermark rather than a one-off image on page 1. Built by token replacement, not
    # %-formatting: the CSS is full of "%" units.
    WATERMARK_CSS = ""
    if logo_b64:
        WATERMARK_CSS = """
body::before {
  content:""; position:fixed; top:50%; left:50%;
  transform:translate(-50%,-50%) rotate(-28deg);
  width:74%; height:74%;
  background:url(data:image/__EXT__;base64,__B64__) center center / contain no-repeat;
  opacity:.055; z-index:0; pointer-events:none;
}
.cover, .q, h2.sec, .meta, .inst, .keys, .lh, .foot, .pnote, .claim,
table.tb, .callout, .syl { position:relative; z-index:1; }
""".replace("__EXT__", logo_ext).replace("__B64__", logo_b64)

    HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:12mm 11mm 12mm 11mm; }}
body {{ font-family:'Helvetica Neue',Arial,sans-serif; color:#1a1c24; font-size:9pt; line-height:1.34; margin:0; }}
.lh {{ display:flex; align-items:center; gap:14px; }} .logo {{ width:74px; height:auto; }}
.co {{ font-size:16pt; font-weight:800; letter-spacing:.6px; color:#12141c; }}
.sub2 {{ font-size:9pt; letter-spacing:3px; color:#8a6d1a; font-weight:700; margin-top:-2px; }}
.sub {{ font-size:8pt; color:#5a5f6e; margin-top:2px; }}
.rule {{ height:3px; background:linear-gradient(90deg,#c9a227,#8a6d1a 55%,#c9a227); margin:8px 0 10px; border-radius:2px; }}
.meta {{ display:flex; justify-content:space-between; font-size:8.4pt; color:#4a4f5e;
        border:1px solid #e0dccc; background:#faf8f1; border-radius:4px; padding:7px 10px; margin-bottom:8px; }}
.inst {{ font-size:8.2pt; border:1px solid #e0dccc; border-radius:4px; padding:8px 10px; margin-bottom:11px; }}
.inst b {{ color:#8a6d1a; }}
.pnote {{ font-size:7.4pt; color:#8d8676; margin:0 0 7px 10px; page-break-after:avoid; }}
h2.sec {{ font-size:10.5pt; color:#8a6d1a; border-left:3px solid #c9a227; padding-left:7px;
         margin:14px 0 3px; page-break-after:avoid; }}
.q {{ margin:0 0 9px; page-break-inside:avoid; }}
.q .n {{ font-weight:800; margin-right:3px; }}
.hi {{ font-weight:500; }}
.en {{ color:#3a3f4e; margin-top:2px; }}
.ops {{ margin:1px 0 2px 15px; clear:right; }}
.op {{ display:inline-block; min-width:47%; padding-right:6px; vertical-align:top; }}
{MATH_CSS}
.keyhead {{ page-break-before:always; }}
.keys {{ display:flex; flex-wrap:wrap; gap:3px 14px; font-size:9pt; }} .k {{ min-width:54px; }}
.cover {{ page-break-after:always; }}
.claim {{ border:1px solid #c9a227; background:#fdfaf0; border-radius:5px; padding:9px 11px;
         font-size:9pt; margin:10px 0 12px; }}
.claim .en2 {{ color:#5a5f6e; font-size:8.2pt; }}
table.tb {{ width:100%; border-collapse:collapse; font-size:8.6pt; margin-bottom:11px; }}
table.tb td {{ border:1px solid #e0dccc; padding:5px 8px; }}
table.tb tr td:nth-child(odd) {{ background:#faf8f1; width:26%; color:#5a5f6e; }}
.callout {{ border-left:3px solid #c9a227; background:#fbf7ea; padding:9px 11px; font-size:8.5pt;
           border-radius:0 4px 4px 0; margin:4px 0 13px; }}
.syl {{ font-size:8.5pt; border:1px solid #eee8d8; border-radius:4px; padding:8px 10px; margin-bottom:8px; }}
.syl i {{ color:#8a6d1a; font-style:normal; font-weight:600; }}
.syl .lvl {{ color:#8d8676; font-size:7.6pt; }}
.setno {{ display:inline-block; margin-top:5px; font-size:8.4pt; color:#8a6d1a;
          border:1px solid #c9a227; border-radius:3px; padding:2px 9px; background:#fdfaf0; }}
.src {{ font-size:7.4pt; color:#9296a2; margin-top:10px; }}
{WATERMARK_CSS}
.dbadge {{ float:right; font-size:7pt; color:#8a6d1a; border:1px solid #e0dccc;
          border-radius:3px; padding:1px 6px; background:#faf8f1; margin-left:6px; }}
.dbadge {{ text-align:right; max-width:150px; }}
.dbadge i {{ font-style:normal; color:#7b8394; display:block; font-size:6.3pt; line-height:1.25; }}
.dbadge i.ty {{ color:#a9adb8; font-size:6pt; }}
.cov {{ width:100%; border-collapse:collapse; font-size:7.2pt; margin:6px 0 14px 0; }}
.cov th, .cov td {{ border:1px solid #e0dccc; padding:2px 5px; text-align:left; }}
.cov th {{ background:#faf8f1; color:#8a6d1a; font-weight:600; }}
.cov td.n {{ text-align:center; width:34px; }}
.cov caption {{ text-align:left; font-size:7.6pt; color:#8a6d1a; padding-bottom:3px; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:12px; padding-top:4px; font-size:7.3pt; color:#9296a2; text-align:center; }}
</style></head><body>
{COVER if a.inter_level else ""}
{HEAD}
<div class="meta" data-mix="{a.difficulty_mix}"><span><b>कुल प्रश्न:</b> {n}</span><span><b>पूर्णांक:</b> {n * 4}</span>
<span><b>समय:</b> 2 घंटे 15 मिनट</span><span><b>नाम:</b> ____________</span>
<span><b>अनुक्रमांक:</b> ________</span></div>
<div class="inst">
<b>निर्देश / INSTRUCTIONS</b><br>
1. सभी प्रश्न वस्तुनिष्ठ हैं। प्रत्येक प्रश्न <b>हिंदी एवं अंग्रेज़ी</b> दोनों में दिया गया है &mdash; किसी एक भाषा में पढ़कर उत्तर दें।<br>
2. प्रत्येक <b>सही उत्तर के लिए 4 अंक</b>; प्रत्येक <b>गलत उत्तर के लिए 1 अंक</b> काटा जाएगा।<br>
3. दिए गए विकल्पों में से <b>केवल एक</b> सही है। उत्तर OMR पत्रक पर काले/नीले बॉलपॉइंट पेन से भरें।<br>
4. जिन भागों में <b>*</b> चिह्नित प्रश्न हैं वे Acharya द्वारा निर्मित अभ्यास-प्रश्न हैं; शेष सभी
   प्रश्न BSSC की <b>आधिकारिक विगत परीक्षाओं</b> से हैं और उत्तर आयोग की <b>आदर्श उत्तर कुंजी</b> से।{PATTERN_NOTE}
</div>
{''.join(qh)}
<div class="keyhead">{HEAD}<h2 class="sec">उत्तर कुंजी / ANSWER KEY</h2>
<div class="keys">{''.join(keys)}</div>
<div class="foot">* = Acharya द्वारा निर्मित अभ्यास-प्रश्न &middot; शेष सभी आयोग की आदर्श उत्तर कुंजी से।<br>
शिक्षक हेतु &mdash; विद्यार्थियों को देने से पूर्व यह पृष्ठ अलग कर लें।</div></div>
<div class="foot">One Step Education, Patna &middot; संकलन: Acharya (TrigunAI Innovations Pvt Ltd)</div>
</body></html>"""

    # follow --out; this was hardcoded, so building a second paper silently overwrote
    # the first one's HTML while its PDF sat elsewhere.
    if a.key_json:   # before the render — the key does not depend on Chrome, and Chrome is slow
        json.dump(keyrows, io.open(a.key_json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    out_html = pathlib.Path(str(a.out).replace(".pdf", ".html")).resolve()
    out_html.write_text(HTML, encoding="utf-8")
    pdf = pathlib.Path(a.out).resolve()
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", out_html.as_uri()], capture_output=True, timeout=300)
    # Record what this set consumed, so the next set can avoid all of it.
    manifest[str(a.set)] = {
        "real": [qid(q) for _, items in paper for q in items if not q.get("_generated")],
        "gen": [gen_sig(q) for _, items in paper for q in items if q.get("_generated")],
        # The generated questions in full, because a signature only pins the SHAPE (see the
        # pin branch above). This is what makes --pin actually reproduce the delivered file.
        "gen_full": [{k: v for k, v in q.items() if not k.startswith("_")}
                     for _, items in paper for q in items if q.get("_generated")],
        "out": os.path.basename(str(a.out)),
    }
    json.dump(manifest, io.open(a.manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # Report the mix ACHIEVED against the mix asked for. A quota that quietly went unfilled is
    # worse than no quota: it reads as "we built to a spec" when the bank could not supply it, and
    # that is exactly the gap the owner spotted the first time.
    from collections import Counter
    # mix_for alternates the spare question, so it is STATEFUL — calling it again for the report
    # advanced the counter and printed each section's target out of phase with the one it was
    # actually built to, inventing a "SHORT" on sections that were exactly right.
    _mix_call["n"] = 0
    for t, items in paper:
        # Count EVERYTHING on the page, not just the official questions. While the mix could
        # only be met from the bank that distinction did not matter; now that generation can fill
        # a hard shortfall, counting only real questions reports "SHORT: 10 at difficulty 3" on a
        # section that just had 15 hard ones added to it.
        # Bin 3-and-above together. The report used to key on the EXACT difficulty, so the seven
        # difficulty-4 maths questions just added to Part II vanished from the "hard" column and
        # the section still read SHORT. The mix asks for easy/medium/hard, not for a 3 exactly.
        got = Counter(min(((q.get("tag") or {}).get("difficulty") or 0), 3) for q in items)
        n_gen_here = sum(1 for q in items if q.get("_generated"))
        n_real = sum(got.values())
        if n_real:
            want = mix_for(n_real)
            shortfall = {b: want[b] - got.get(b, 0) for b in (3, 2) if want[b] > got.get(b, 0)}
            note = (f"  asked {want[1]}/{want[2]}/{want[3]}, got "
                    f"{got.get(1, 0)}/{got.get(2, 0)}/{got.get(3, 0)} (easy/med/hard)"
                    f"  [{n_real - n_gen_here} official + {n_gen_here} generated]")
            if shortfall:
                note += ("  SHORT: " +
                         ", ".join(f"{v} at difficulty {b}" for b, v in shortfall.items()))
            print(f"  {t[:52]:54s} {len(items):3d}\n{note}")
        else:
            print(f"  {t[:52]:54s} {len(items):3d}")
    print(f"\n{n} bilingual questions | {n - n_gen} REAL official + {n_gen} generated "
          f"| logo: {'yes' if logo_html else 'TEXT ONLY'} | {pdf}")


if __name__ == "__main__":
    main()
