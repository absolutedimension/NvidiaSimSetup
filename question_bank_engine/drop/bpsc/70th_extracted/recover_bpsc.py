#!/usr/bin/env python3
"""
recover_bpsc.py — clean up the two 70th GS extractions before (re)storing:
  1. sanitize HTML artifacts in stems/options (<br>,<p>,<table> match-lists, <sup>/<sub>)
  2. recover options for rows where the vision pass left (A)-(D) inline in the stem
     instead of the options dict (contiguous block in the 04-01-25 extraction)
Writes <name>.fixed.json. Never invents content — options are only pulled verbatim
from markers already present in the stem.
"""
import json, re, sys, os

def sub_sup(t):
    t = re.sub(r"<\s*sup\s*>(.*?)<\s*/\s*sup\s*>", r"^\1", t, flags=re.I|re.S)
    t = re.sub(r"<\s*sub\s*>(.*?)<\s*/\s*sub\s*>", r"_\1", t, flags=re.I|re.S)
    return t

def strip_html(t):
    t = sub_sup(t)
    t = re.sub(r"<\s*br\s*/?\s*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*/?\s*p\s*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*image[^>]*>", "", t, flags=re.I)          # drop figure placeholder text
    # markdown-ish table rows already look like "| a | b |" -> keep as text lines
    t = re.sub(r"<\s*/?\s*(table|tr|thead|tbody)\s*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*/\s*td\s*>", " ", t, flags=re.I)
    t = re.sub(r"<\s*td\s*>", " | ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)                              # any leftover tag
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

OPT = re.compile(r"\(\s*([A-Da-d])\s*\)")

def recover_options(stem):
    """If stem carries a full (A)..(D) block, split it out. Return (new_stem, opts|None)."""
    marks = [(m.start(), m.group(1).upper()) for m in OPT.finditer(stem)]
    # need the four labels A,B,C,D appearing in order at the tail
    want = ["A","B","C","D"]
    pos = {}
    for start,lab in marks:
        if lab in want and lab not in pos:
            pos[lab] = start
    if not all(l in pos for l in want):
        return stem, None
    if not (pos["A"] < pos["B"] < pos["C"] < pos["D"]):
        return stem, None
    # option text = from after "(X)" marker to next marker / end
    bounds = [pos["A"], pos["B"], pos["C"], pos["D"], len(stem)]
    opts = {}
    for i,lab in enumerate(want):
        seg = stem[bounds[i]:bounds[i+1]]
        seg = OPT.sub("", seg, count=1)          # drop the leading (X)
        opts[lab] = strip_html(seg).strip(" .|\n")
    if not all(opts[l] for l in want):
        return stem, None
    new_stem = strip_html(stem[:pos["A"]]).rstrip(" .|\n")
    if len(new_stem) < 15:
        return stem, None
    return new_stem, opts

def main():
    for f in sys.argv[1:]:
        d = json.load(open(f))
        recovered = figs = 0
        for n,q in d.items():
            stem = q.get("stem") or ""
            opts = q.get("options") or {}
            good = [l for l in "ABCD" if l in opts and str(opts.get(l,"")).strip()]
            if re.search(r"<\s*image", stem, re.I):
                q["needs_figure"] = True; figs += 1
            if len(good) < 4:
                ns, ro = recover_options(stem)
                if ro:
                    q["stem"] = ns
                    q["options"] = ro
                    q["raw_options"] = [f"({l}) {ro[l]}" for l in "ABCD"]
                    recovered += 1
                    continue
            # otherwise just sanitize existing content in place
            q["stem"] = strip_html(stem)
            if opts:
                q["options"] = {k: strip_html(str(v)) for k,v in opts.items()}
        out = f.replace(".json",".fixed.json")
        json.dump(d, open(out,"w"), ensure_ascii=False, indent=1)
        still = [int(n) for n,q in d.items()
                 if len([l for l in "ABCD" if l in (q.get("options") or {}) and str((q.get("options") or {}).get(l,"")).strip()])<4]
        print(f"{f}: recovered_options={recovered} figure_flagged={figs} -> {out}")
        print(f"   still <4 options (will store descriptive / delete): {sorted(still)}")

if __name__ == "__main__":
    main()
