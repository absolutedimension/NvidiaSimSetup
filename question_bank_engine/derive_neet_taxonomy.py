#!/usr/bin/env python3
"""Derive NEET Physics/Chemistry taxonomies from the ingested datavorous chapters.

After the datavorous ingest, NEET Physics/Chemistry carry datavorous's own (clean,
NEET-specific) chapter names — which do NOT match the JEE Main taxonomies they were
temporarily reusing. This regenerates dedicated `qbank/neet_physics.py` and
`qbank/neet_chemistry.py` from the DB so /chapters + retrieval line up exactly, and
drops the JEE-Main-inherited chapters that were never in the NEET syllabus.

Keyword signatures are left minimal — the datavorous questions arrive PRE-tagged, so
the offline keyword classifier is not used on them; the chapter LIST is what matters.

    python3 derive_neet_taxonomy.py            # prints the two modules to stdout
    python3 derive_neet_taxonomy.py --write    # writes qbank/neet_{physics,chemistry}.py
"""
import argparse
import os
import re

from qbank.storage import Store

MIN_QS = 8   # ignore a chapter with fewer than this many real questions (noise / mis-tag)


def chapters_for(store, subject, min_qs=MIN_QS):
    rows = store.con.execute(
        "SELECT chapter, COUNT(*) FROM questions "
        "WHERE exam='NEET' AND subject=? AND generated=0 AND duplicate_of IS NULL "
        "AND chapter IS NOT NULL AND chapter!='' GROUP BY chapter ORDER BY 2 DESC",
        (subject,)).fetchall()
    return [(c, n) for c, n in rows if n >= min_qs]


def render_module(var, subject, chapters):
    lines = [f'"""NEET {subject} taxonomy — derived from the datavorous entrance-exam',
             'bank (the dominant NEET source). Chapter names are datavorous\'s own, so the',
             'ingested questions match /chapters exactly. Keyword signatures are minimal',
             'because these questions arrive pre-tagged; the chapter LIST is the point."""',
             '', f'{var} = {{']
    for c, _n in chapters:
        # a couple of distinctive keywords from the chapter title itself
        kw = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", c)
              if w.lower() not in ("and", "the", "with", "from", "properties", "principles")]
        kw = kw[:4]
        cname = c.replace('"', '\\"')
        lines.append(f'    "{cname}": {{"keywords": {kw!r}, "concepts": {{}}}},')
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    store = Store()
    here = os.path.dirname(os.path.abspath(__file__))

    for subject, var, fname in [("Physics", "NEET_PHYSICS", "neet_physics.py"),
                                ("Chemistry", "NEET_CHEMISTRY", "neet_chemistry.py")]:
        chs = chapters_for(store, subject)
        mod = render_module(var, subject, chs)
        total = sum(n for _, n in chs)
        print(f"# {subject}: {len(chs)} chapters, {total} questions")
        if args.write:
            with open(os.path.join(here, "qbank", fname), "w") as f:
                f.write(mod)
            print(f"#   wrote qbank/{fname}")
        else:
            print(mod)


if __name__ == "__main__":
    main()
