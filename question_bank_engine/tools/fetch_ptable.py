#!/usr/bin/env python3
"""Derive the element data from PubChem (NIH) instead of typing it.

The measured hand-data error rate on this line is about 1 in 27. A table of 30 element symbols and
atomic numbers typed from memory would therefore be expected to carry an error — and an element
symbol on a Class-10 paper is exactly the kind of thing a teacher spots instantly. So it is not
typed at all: this pulls the authoritative table and writes it to drop/bssc/ELEMENTS.json, which
qbank/science_tables.py reads. The only hand-written part left is WHICH elements a Class-10 student
meets, and that is a curriculum judgement rather than a fact.

    python3 tools/fetch_ptable.py
"""
import io
import json
import os
import urllib.request

URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "drop", "bssc", "ELEMENTS.json")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "trigunai-qbank/1.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
    cols = d["Table"]["Columns"]["Column"]
    i_num, i_sym, i_name = cols.index("AtomicNumber"), cols.index("Symbol"), cols.index("Name")
    rows = {}
    for r in d["Table"]["Row"]:
        c = r["Cell"]
        rows[c[i_name]] = {"symbol": c[i_sym], "atomic_number": int(c[i_num])}
    payload = {"_source": URL, "_note": "Derived, not hand-written. Re-run tools/fetch_ptable.py.",
               "elements": rows}
    json.dump(payload, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} elements -> {os.path.normpath(OUT)}")
    # Internal consistency: atomic numbers must be a bijection onto 1..N and symbols unique.
    nums = sorted(v["atomic_number"] for v in rows.values())
    syms = [v["symbol"] for v in rows.values()]
    assert nums == list(range(1, len(rows) + 1)), "atomic numbers are not 1..N"
    assert len(set(syms)) == len(syms), "duplicate element symbol"
    print("consistency: atomic numbers form 1..N with no gaps; all symbols unique")


if __name__ == "__main__":
    main()
