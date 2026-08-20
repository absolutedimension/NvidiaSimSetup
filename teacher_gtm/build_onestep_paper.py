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


def gen_sig(q):
    """Identity of a GENERATED question, independent of the name in the English stem.

    reasoninggen varies the actor ("A boy starts..." / "Sita starts...") while keeping the same
    numbers, and the Hindi template carries no name at all — so two such questions are the SAME
    question with byte-identical Hindi. Keying on the English stem let one through into both sets.
    Signature is therefore the concept, the numbers in the question, and the option set.
    """
    nums = tuple(re.findall(r"\d+", (q.get("stem") or "")))
    opts = tuple(sorted((o.get("text") or "").strip() for o in q.get("options") or []))
    return "|".join([str(q.get("concept") or q.get("qtype") or ""), ",".join(nums), "~".join(opts)])


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
    if re.search(r"Consider the following statements|Match the following", stem):
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


def pick(pool, n, used, tmpl, cap=2, salt="", stripe=None, mix=None):
    """Draw n questions, hardest first.

    `stripe=(i, m)` deals the sorted pool round-robin across m sets and takes lane i. Without it
    the first set built takes every hard question and the second gets the residue: rebuilding for
    difficulty gave Set 1 zero trivial questions and Set 2 thirty-eight of them. The bank simply
    does not hold two sets' worth of hard questions (145 at-level difficulty-2/3 against the 206
    two papers need), so the only honest options are to split them evenly or to ship one strong
    paper. Splitting is what an institute buying a series needs.
    """
    out = []
    pool = sorted(pool, key=lambda q: _order_key(q, salt))
    if stripe:
        i, m = stripe
        pool = [q for k, q in enumerate(pool) if k % m == i] + \
               [q for k, q in enumerate(pool) if k % m != i]   # own lane first, rest as fallback

    def take(candidates, want):
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
            register(q, used, tmpl)
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
    take(pool, n)                       # top up from anywhere the mix could not reach
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
            if g in seen or per_concept.get(q.concept, 0) >= 2:
                continue
            seen.add(g)
            per_concept[q.concept] = per_concept.get(q.concept, 0) + 1
            out.append(row)
        if len(out) >= n:
            break
    print(f"  generated {len(out)} maths question(s) at difficulty {diff}")
    return out


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


def load_generated(n, cap_per_concept=3, exclude=frozenset()):
    """Bilingual reasoning with COMPUTED answers, only used by --structure official3.

    Capped and dealt round-robin BY CONCEPT, not by stem text: three direction questions read
    "facing North, right then left" / "facing East, right then left" / "facing North, left then
    right" — different words, so a stem-signature cap lets all three onto one page, which is
    exactly what happened the first time.
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
    if order:
        cap_per_concept = max(cap_per_concept, -(-n // len(order)))
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
    ap.add_argument("--generate-gs", action="store_true",
                    help="Fill a HARD General Studies shortfall with statement-based and "
                         "match-the-pairs questions built from verified fact tables. This is the "
                         "only way the difficulty mix can be met in GS: the bank holds nothing "
                         "above difficulty 2 in that section.")
    ap.add_argument("--generate-gk", action="store_true",
                    help="Top up a General Studies shortfall from staticgkgen. OFF by default: "
                         "its questions are correct-by-construction but difficulty-1 recall, "
                         "which is the register the institute already rejected.")
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

    try:
        _e, _m, _h = (int(x) for x in a.difficulty_mix.split(":"))
    except ValueError:
        raise SystemExit("--difficulty-mix wants three numbers like 10:60:30")
    if _e + _m + _h != 100:
        raise SystemExit(f"--difficulty-mix must sum to 100, got {_e + _m + _h}")

    def mix_for(want):
        """Turn the requested percentages into per-band counts for a section of `want` questions."""
        hard = round(want * _h / 100)
        med = round(want * _m / 100)
        return {3: hard, 2: med, 1: max(want - hard - med, 0)}

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
            live = {re.sub(r"\s+", " ", (g.get("stem") or "")).strip(): g
                    for g in load_generated(10 ** 6)}
            refreshed = sum(1 for g in full
                            if re.sub(r"\s+", " ", (g.get("stem") or "")).strip() in live)
            full = [live.get(re.sub(r"\s+", " ", (g.get("stem") or "")).strip(), g) for g in full]
            if refreshed:
                print(f"  PIN: refreshed {refreshed}/{len(full)} generated questions from the "
                      f"current pool (corrections propagate; the selection stays pinned)")
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
            if idx == len(SPEC) - 1:
                got = got + pin_gen[:want - len(got)]
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
        pool = [q for s in secs for q in by.get(s, [])]
        last = idx == len(SPEC) - 1
        target = want + carry if last else want
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
                got = got[:max(len(got) - len(fresh), 0)] + fresh
        if a.generate_gk and "General Studies" in secs and len(got) < target:
            fresh = generate_static_gk(target - len(got), gen_taken, a.inter_level)
            gen_taken |= {gen_sig(q) for q in fresh}
            got += fresh
        if a.generate_maths and "Mathematics" in secs:
            want = mix_for(target)
            have3 = sum(1 for q in got if ((q.get("tag") or {}).get("difficulty") or 0) >= 3)
            if want[3] > have3:
                new_qs = generate_maths(want[3] - have3, 4, gen_taken, a.inter_level)
                gen_taken |= {gen_sig(q) for q in new_qs}
                got = got[:max(len(got) - len(new_qs), 0)] + new_qs
        if not last:
            carry += target - len(got)
        elif len(got) < target:
            fresh = load_generated(target - len(got), exclude=gen_taken)
            gen_taken |= {gen_sig(q) for q in fresh}
            got += fresh
        if secs == ["Hindi"] and a.hindi_source == "generated":  # noqa: E501
            got = load_hindi_generated(want)   # (real4 only; Inter Level has no Hindi section)
        paper.append((title, got)); n += len(got)

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
            if a.show_difficulty:
                # The owner said "ye basic ka bhi basic hai" about a whole paper. A badge per
                # question turns that into "question 14 is right, question 61 is too easy" —
                # feedback we can actually build against, and the raw material for calibrating
                # our difficulty tags against a real examiner's judgement.
                dlab = {1: ("सरल", "Easy"), 2: ("मध्यम", "Medium")}.get(
                    (q.get("tag") or {}).get("difficulty") or 0, ("कठिन", "Hard"))
                src = "Acharya" if q.get("_generated") else "आयोग / official"
                block += (f'<span class="dbadge">{dlab[0]} &middot; {dlab[1]}'
                          f'<i>{src}</i></span>')
            if hi_stem:
                block += (f'<div class="hi"><span class="n">{i}.</span> {esc(hi_stem)}</div>'
                          f'<div class="ops">{oh_html}</div>')
            if en_stem:
                lead = "" if hi_stem else f'<span class="n">{i}.</span> '
                block += (f'<div class="en">{lead}{esc(en_stem)}</div>'
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
.ops {{ margin:1px 0 2px 15px; }}
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
.dbadge i {{ font-style:normal; color:#9296a2; display:block; font-size:6.3pt; }}
.foot {{ border-top:1px solid #ddd8c8; margin-top:12px; padding-top:4px; font-size:7.3pt; color:#9296a2; text-align:center; }}
</style></head><body>
{COVER if a.inter_level else ""}
{HEAD}
<div class="meta"><span><b>कुल प्रश्न:</b> {n}</span><span><b>पूर्णांक:</b> {n * 4}</span>
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
    for t, items in paper:
        # Count EVERYTHING on the page, not just the official questions. While the mix could
        # only be met from the bank that distinction did not matter; now that generation can fill
        # a hard shortfall, counting only real questions reports "SHORT: 10 at difficulty 3" on a
        # section that just had 15 hard ones added to it.
        got = Counter(((q.get("tag") or {}).get("difficulty") or 0) for q in items)
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
