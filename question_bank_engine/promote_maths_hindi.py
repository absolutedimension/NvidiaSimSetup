#!/usr/bin/env python3
"""Promote the quarantined Hindi of NEW-STOCK MATHEMATICS questions into servable `stem_hi`.

Background. The 2016-18 papers were extracted with their Hindi held in `stem_hi_unverified`,
because vision mangles Devanagari on those scans — बैकुंठनाथ शुक्ला came back as बंकिमनाथ झा. That
call was right for General Studies, where the content IS proper nouns. It was too broad for
MATHEMATICS, where the content is numbers, symbols and a small stock of standard terms.

Measured before writing this, by reading samples off the page:

    MATHEMATICS   ~90% clean   ("बहुपद 6x²-7x-3 के शून्यक हैं", "आधार त्रिज्या r तथा ऊँचाई h की
                                एक लम्बवृत्तीय बेलन का कुल पृष्ठफल है") — residual errors are
                                single words that do not change the question (प्रथम→प्रश्न पद).
    GENERAL SCIENCE ~50% corrupt (नाइट्रोजन चक्र → "नैतिकता चक्र", नींबू → "निबंध",
                                ऑप्टिकल फाइबर → "आँटिफिकल फाइबर") — NOT promoted.

So this promotes Mathematics only, and only where every one of these holds:

  1. The Hindi stem contains Devanagari at all.
  2. Its DIGITS match the English stem exactly — the strongest automatic evidence we have that the
     transcription tracked the question rather than drifting. This is the check that caught a
     generated question reading "twice its position" in English and plain "position" in Hindi.
  3. The Hindi options pair 1:1 with the English ones and are four distinct values.
  4. No token from _CORRUPT appears — the recurring OCR garbage observed in these scans.
  5. The question is inside the Inter Level arithmetic syllabus, so nothing above-syllabus is
     promoted merely because its Hindi happened to be clean.

Every promoted row is stamped `hindi_status: "promoted_maths_number_verified"`, so a later reader
can tell machine-promoted Hindi from the Hindi the commission actually printed bilingually.

Idempotent. Run after any re-extraction.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "teacher_gtm"))
from paper_common import inter_level_maths_ok, options_ok  # noqa: E402

NUM = re.compile(r"\d+")
DEV = re.compile(r"[ऀ-ॿ]")

# The papers extracted 2026-08-20, whose Hindi sits in the *_unverified fields.
NEW_STOCK = {"GK1.PDF", "GK(3649).PDF", "G.K_and_N.A_M.A.PDF",
             "JE-0411-GK-QB-AND-MA.pdf", "maths.PDF"}

# Recurring OCR garbage seen in these scans. निम्नलिखित ("the following") is the single most
# common word in an exam paper and the one the scanner mangles most often, in several directions.
_CORRUPT = re.compile("|".join([
    "निर्मलिखित", "निर्णयात्मक", "निर्माणबंद", "निर्माणबिंदु", "फिमानलिफ़िकत", "निम्नलिखत",
    "सूक्ष्मण", "अव्यविक", "उत्प्रदक", "आँटिफिकल", "नैतिकता चक्र", "वित्तीयकारक",
]))


def promotable(q):
    if q.get("source_pdf") not in NEW_STOCK:
        return False, "not new stock"
    if (q.get("tag") or {}).get("section") != "Mathematics":
        return False, "not mathematics"
    if q.get("stem_hi"):
        return False, "already has Hindi"
    if not (q.get("correct_answer") and options_ok(q.get("options"))):
        return False, "not servable in English"
    hi = q.get("stem_hi_unverified") or ""
    oh = q.get("options_hi_unverified") or []
    if not (hi and DEV.search(hi)):
        return False, "no Hindi captured"
    if _CORRUPT.search(hi) or any(_CORRUPT.search(str(o.get("text", ""))) for o in oh):
        return False, "known OCR corruption"
    if Counter(NUM.findall(hi)) != Counter(NUM.findall(q.get("stem") or "")):
        return False, "numbers disagree with English"
    if len(oh) != len(q.get("options") or []) or not options_ok(oh):
        return False, "options do not pair"
    if not inter_level_maths_ok(q):
        return False, "above the Inter Level syllabus"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(HERE, "drop", "bssc"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    promoted = 0
    reasons = Counter()
    for path in sorted(glob.glob(os.path.join(a.dir, "*_KEYED.json"))):
        rows = json.load(io.open(path, encoding="utf-8"))
        dirty = False
        for q in rows:
            if q.get("source_pdf") not in NEW_STOCK:
                continue
            ok, why = promotable(q)
            reasons[why] += 1
            if not ok:
                continue
            q["stem_hi"] = q["stem_hi_unverified"]
            q["options_hi"] = q["options_hi_unverified"]
            q["hindi_status"] = "promoted_maths_number_verified"
            promoted += 1
            dirty = True
        if dirty and not a.dry_run:
            json.dump(rows, io.open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"promoted {promoted} Mathematics questions to servable Hindi\n")
    for why, n in reasons.most_common():
        print(f"  {n:4d}  {why}")
    if a.dry_run:
        print("\n  (dry run — nothing written)")


if __name__ == "__main__":
    main()
