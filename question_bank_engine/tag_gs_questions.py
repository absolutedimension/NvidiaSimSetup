#!/usr/bin/env python3
"""Assign chapters to the ingested GS past-paper banks (BPSC TRE / BPSC).

Real PYQs are ingested verbatim and arrive with `chapter = NULL`, so the topic picker had nothing
to offer (it degraded to a single "Full Syllabus (mixed)" entry) and a student could not practise
one topic at a time. This keyword-classifies each banked question into the GS taxonomies added in
`qbank/gs_common.py`.

Deterministic (no LLM, no cost), idempotent, and conservative: a question that matches nothing
keeps `chapter = NULL` rather than being forced into a bucket — the picker simply won't offer it
under a chapter, which is honest. Only ever fills EMPTY chapters; never overwrites an existing tag.

    python3 tag_gs_questions.py --dry-run     # show the distribution it would write
    python3 tag_gs_questions.py               # apply
"""
import argparse
import json
import sqlite3
from collections import Counter

from qbank import syllabus

TARGETS = [("BPSC TRE", "GS Polity"), ("BPSC TRE", "GS History"),
           ("BPSC TRE", "GS Geography"), ("BPSC TRE", "GS Economics"),
           ("BPSC TRE", "General Studies"), ("BPSC", "General Studies")]

# Keyword matching can't catch everything — a History question that just names a person or a
# treaty has no distinctive vocabulary. But a question in a DIMENSION subject is still that
# dimension by construction (it came from a Polity/History/Geography/Economics paper), so park
# the residue in an explicit mixed bucket rather than leaving it chapter-less and therefore
# unreachable from the picker. Honest label, nothing mis-filed into a specific chapter.
FALLBACK = {
    ("BPSC TRE", "GS Polity"): "General Polity (mixed)",
    ("BPSC TRE", "GS History"): "General History (mixed)",
    ("BPSC TRE", "GS Geography"): "General Geography (mixed)",
    ("BPSC TRE", "GS Economics"): "General Economics (mixed)",
    ("BPSC TRE", "General Studies"): "General Studies (mixed)",
    ("BPSC", "General Studies"): "General Studies (mixed)",
}


def classify(text: str, tax: dict):
    """(chapter, concept) by weighted keyword hits; longer keywords score higher (more specific)."""
    t = " " + (text or "").lower() + " "
    best_ch, best_score = None, 0
    for ch, data in tax.items():
        score = sum(t.count(k.lower()) * len(k.split()) for k in data["keywords"])
        if score > best_score:
            best_ch, best_score = ch, score
    if not best_ch:
        return None, None
    best_c, best_cs = None, 0
    for cname, ckw in tax[best_ch].get("concepts", {}).items():
        cs = sum(t.count(k.lower()) for k in ckw)
        if cs > best_cs:
            best_c, best_cs = cname, cs
    return best_ch, best_c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/qbank.sqlite")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    grand = Counter()
    for exam, subject in TARGETS:
        tax = syllabus.get_taxonomy(exam, subject)
        if not tax:
            print(f"!! no taxonomy for ({exam}, {subject}) — skipping"); continue
        rows = con.execute(
            "SELECT id, stem, options FROM questions WHERE exam=? AND subject=? AND verified=1 "
            "AND duplicate_of IS NULL AND (chapter IS NULL OR chapter='')", (exam, subject)).fetchall()
        dist, updates = Counter(), []
        for r in rows:
            text = r["stem"] or ""
            try:                                    # options add signal (names, places, terms)
                text += " " + " ".join(o.get("text", "") for o in json.loads(r["options"] or "[]"))
            except Exception:
                pass
            ch, concept = classify(text, tax)
            if not ch:
                ch, concept = FALLBACK.get((exam, subject)), None
            dist[ch or "(unmatched)"] += 1
            if ch:
                updates.append((ch, concept, r["id"]))
        print(f"\n{exam} / {subject}: {len(rows)} untagged")
        for ch, n in dist.most_common():
            print(f"    {ch:34s} {n}")
        grand[f"{exam}|{subject}"] = len(updates)
        if not args.dry_run and updates:
            con.executemany("UPDATE questions SET chapter=?, concept=COALESCE(concept,?) WHERE id=?", updates)
            con.commit()
    print("\nTOTAL tagged:", sum(grand.values()), "" if not args.dry_run else "(dry-run — nothing written)")


if __name__ == "__main__":
    main()
