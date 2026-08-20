#!/usr/bin/env python3
"""Parse article headings from the official Constitution PDF — source-derived, not recalled.

polity_tables.py is hand-written, and hand-written data was measured at 1 wrong in 27 (the 61st
Amendment year). Parsing the Constitution's own table of contents removes the recall step: the
marginal heading beside each article IS the authoritative statement of its subject.

It took six attempts, and every wrong one ran without error. Recorded because each failure is a
different way for a parser to look like it worked:

  1. Presence-only check — confirmed a phrase existed somewhere in 848,000 characters, which says
     nothing about which article it belongs to.
  2. Unbounded parse — swept in the Seventh Schedule's Union/State/Concurrent Lists and the Ninth
     Schedule's protected Acts, which are numbered "N. Text." exactly like articles. It reported
     Article 15 as "The United Provinces Land Acquisition Act, 1948". This is the dangerous
     failure: plausible wrong facts, ready to be cited.
  3. Word-boundary positional check — \bNN\b cannot match in "Right to Equality14.", because there
     is no boundary between a letter and a digit. False alarm on correct data.
  4. PART-anchored — only 2 of 10 PART markers were usable, so one stray number poisoned the
     ascending filter for everything after it.
  5. Bounded at "FIRST SCHEDULE" — whose FIRST occurrence is inside an omitted Part heading,
     "THE STATES IN PART B OF THE FIRST SCHEDULE", cutting the ToC at 19,229 of 36,784 characters
     and silently losing every article above ~250. Low numbers were perfect; high ones absent.
  6. This one: bounded on the END of the article list, "395. Repeals".

Three properties of the real text drive the parse, and none was guessable:
  - a heading runs from one "<number>." to the NEXT, not to the next period — periods live inside
    headings ("etc.")
  - article numbers are glued to the preceding sub-heading: "Right to Equality14.Equality before law"
  - inline sub-headings ("Right to Freedom") trail a heading and must be stripped

THE GATE: the parse must reproduce the 19 already-verified rows before any new row is trusted. It
caught attempts 4 and 5. Two rows fail it by design — Article 19 and 356, where our wording is a
deliberate paraphrase noted in polity_tables — so 17 of 19 is the pass mark, not 19.
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

NUM = re.compile(r"(?<![\d])(\d{1,3}[A-Z]?)\s*\.")
PARAPHRASED = {"19", "356"}          # ours differs from the official heading, deliberately


def headings(segment):
    out, marks = {}, list(NUM.finditer(segment))
    for i, m in enumerate(marks):
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(segment)
        text = segment[m.end():stop].strip().rstrip(".").strip()
        if ". " in text:                       # a short Title Case tail is the next sub-heading
            head, tail = text.rsplit(". ", 1)
            if len(tail.split()) <= 6 and tail[:1].isupper():
                text = head
        if 8 <= len(text) <= 130 and text[:1].isupper():
            out.setdefault(m.group(1), text)
    return out


def parse(pdf_path):
    import pypdf
    flat = re.sub(r"\s+", " ", "\n".join((p.extract_text() or "")
                                         for p in pypdf.PdfReader(pdf_path).pages))
    end = re.search(r"395\s*\.\s*Repeals", flat)
    toc = flat[:end.end() + 20] if end else flat
    rows = {}
    for seg in toc.split("PART "):             # reset the ascending counter at every Part
        last = 0
        for num, head in headings(seg).items():
            n = int(re.match(r"\d+", num).group())
            if n < last or n > 395:
                continue
            last = n
            rows.setdefault(num, head)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="/tmp/coi.pdf")
    ap.add_argument("--out", default=os.path.join(HERE, "drop", "bssc",
                                                  "CONSTITUTION_ARTICLES.json"))
    a = ap.parse_args()
    rows = parse(a.pdf)
    from qbank import polity_tables as P

    def overlaps(x, y):
        wx = set(re.findall(r"[a-z]{5,}", x.lower()))
        wy = set(re.findall(r"[a-z]{5,}", y.lower()))
        return bool(wx & wy)

    miss = [k for k, v in P.ARTICLE_SUBJECT.items()
            if not (rows.get(k) and overlaps(rows[k], v)) and k not in PARAPHRASED]
    print(f"{len(rows)} article headings parsed")
    print(f"self-test: {len(P.ARTICLE_SUBJECT) - len(miss) - len(PARAPHRASED)} of "
          f"{len(P.ARTICLE_SUBJECT) - len(PARAPHRASED)} checkable rows reproduced "
          f"({len(PARAPHRASED)} paraphrased by design, excluded)")
    if miss:
        print(f"  GATE FAILED — not writing. Unreproduced: {miss}")
        raise SystemExit(1)
    json.dump(rows, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  gate passed -> {a.out}")


if __name__ == "__main__":
    main()
