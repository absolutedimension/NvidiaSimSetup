#!/usr/bin/env python3
"""Verified facts -> (key, value) tables the statement forms can safely falsify.

The statement forms rest on ONE guarantee: a false statement is made by pairing a key with a
DIFFERENT value from the same table. That is only false if the table is a FUNCTION (one correct
value per key) and its values are MUTUALLY EXCLUSIVE for that attribute.

  state -> capital        satisfies both. Bihar has one capital and Patna is nobody else's.
  soil  -> "retains water well"  does NOT. Several soils do, so swapping one in produces a
                                 statement that is accidentally TRUE and keyed as false.

So most verified facts cannot become table rows, and this REJECTS rather than converts them. That
is the right trade: a small table of safely-falsifiable facts beats a large one that quietly
generates true "false" statements — the failure a student would be marked wrong for.

Extraction is by explicit pattern, not by a model. The claims have already passed a three-verifier
support gate; what is needed here is not more judgement but a precise reading of sentence shape,
and a regex can be audited where a model's summary cannot.

Every row keeps the citation the fact arrived with, so a question built from it can still print
"NCERT Class 10, jess304.pdf, para 35 — open it and read".
"""
import argparse
import io
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "drop", "bssc", "GS_FACTS_VERIFIED.jsonl")
OUT = os.path.join(HERE, "drop", "bssc", "GS_TABLES.json")

# Only relations whose value domain is closed and mutually exclusive. Each entry is
# (table name, compiled pattern, key group, value group). Patterns are deliberately strict —
# a missed fact costs coverage, a loose match costs correctness.
PATTERNS = [
    ("capital_of", re.compile(
        r"^(?:The city of )?([A-Z][\w' ]{2,30}?) is the capital (?:city )?of ([A-Z][\w' ]{2,30}?)\.?$"), 2, 1),
    ("article_deals_with", re.compile(
        r"^Article (\d+[A-Z]?) of the (?:Indian )?Constitution (?:deals with|provides for|guarantees|relates to) (.{6,90}?)\.?$"), 1, 2),
    ("amendment_year", re.compile(
        r"^The (\d+(?:st|nd|rd|th)) Amendment (?:Act )?(?:was )?(?:passed|enacted|came into force) in (\d{4})\.?$"), 1, 2),
    ("originates_at", re.compile(
        r"^The (?:river )?([A-Z][\w' ]{2,25}?) (?:river )?originates (?:at|in|from) ([A-Z][\w' ]{2,35}?)\.?$"), 1, 2),
    ("launched_in", re.compile(
        r"^(?:The )?([A-Z][\w' ]{4,45}?) was (?:launched|established|founded|set up) in (\d{4})\.?$"), 1, 2),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    facts = [json.loads(l) for l in io.open(a.src, encoding="utf-8")]
    hits = defaultdict(lambda: defaultdict(list))          # table -> key -> [(value, cite)]
    matched = 0
    for f in facts:
        claim = re.sub(r"\s+", " ", f["claim"]).strip()
        for name, pat, kg, vg in PATTERNS:
            m = pat.match(claim)
            if not m:
                continue
            key, val = m.group(kg).strip(), m.group(vg).strip()
            hits[name][key].append((val, {"title": f.get("title"), "para": f.get("para"),
                                          "claim": claim}))
            matched += 1
            break

    tables, rejected = {}, []
    for name, keys in hits.items():
        # (1) FUNCTION: one key must not carry two different values
        multi = {k for k, vs in keys.items() if len({v for v, _ in vs}) > 1}
        # (2) MUTUAL EXCLUSIVITY: one value must not belong to two keys
        owner = defaultdict(set)
        for k, vs in keys.items():
            for v, _ in vs:
                owner[v].add(k)
        shared = {v for v, ks in owner.items() if len(ks) > 1}
        good = {k: vs[0][0] for k, vs in keys.items()
                if k not in multi and vs[0][0] not in shared}
        for k in multi:
            rejected.append((name, k, "two different values for one key"))
        for k, vs in keys.items():
            if k not in multi and vs[0][0] in shared:
                rejected.append((name, k, f"value '{vs[0][0]}' also belongs to another key"))
        if len(good) >= 4:                # a table with fewer than four rows cannot make options
            tables[name] = {"rows": good,
                            "cites": {k: keys[k][0][1] for k in good}}
        elif good:
            rejected.append((name, f"<whole table: {len(good)} rows>", "fewer than 4 rows"))

    json.dump(tables, io.open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(facts)} verified facts | {matched} matched a safe relation pattern\n")
    for name, t in sorted(tables.items(), key=lambda x: -len(x[1]["rows"])):
        print(f"  KEPT  {name:22s} {len(t['rows']):3d} rows")
        for k, v in list(t["rows"].items())[:2]:
            print(f"          {k}  ->  {v}")
    print()
    for name, k, why in rejected[:8]:
        print(f"  REJECTED {name}: {k} — {why}")
    print(f"\n  {len(rejected)} rejected. A fact that cannot be safely falsified is not a table "
          f"row, however true and however well cited.")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
