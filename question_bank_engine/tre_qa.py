#!/usr/bin/env python3
"""Reusable QA-classify + batch helper for BPSC TRE keying (see BPSC_TRE_STATUS.md).

extract (extract_tre.py) -> classify each question clean|reextract -> emit keying batches.
'clean' = full stem + readable options, keyable now. 'reextract' = legacy-font-mangled math
symbols or a truncated setup that even the sequential-number parser couldn't recover; those go
to the exact-Q recovery pass instead of being keyed on bad text.
"""
import re, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_tre import extract

GARBLE = re.compile(r'æ|èç|ö|ø÷|Ñ|¶|´|Ã|å|Ð')          # legacy-font math mangling
MATHOP = re.compile(r'[=×÷√]|\^|\bsin\b|\bcos\b|\blog\b')
CONT = ('accordingly', 'therefore', 'then ', 'the value of', 'what is the value',
        'hence', 'the number is', "b's share", 'smallest number', 'select the correct')


def quality(q):
    s = q['stem'].strip()
    opts = [q['options'][k] for k in 'ABC']
    blob = s + ' ' + ' '.join(opts)
    if GARBLE.search(blob):
        return 'reextract'
    if len(s) < 15:
        return 'reextract'
    if s.lower().startswith(CONT) and len(s) < 55:
        return 'reextract'
    if MATHOP.search(' '.join(opts)) and any(len(o.split()) >= 3 for o in opts):
        return 'reextract'
    return 'clean'


def classify(pdf_path):
    qs = extract(pdf_path)
    for i, q in enumerate(qs):
        q['seq'] = i + 1
        q['quality'] = quality(q)
    return qs


if __name__ == "__main__":
    # usage: tre_qa.py <pdf> [pdf...]  -> prints clean/reextract yield per paper
    for p in sys.argv[1:]:
        qs = classify(p)
        clean = sum(1 for q in qs if q['quality'] == 'clean')
        print(f"{clean:3d}/{len(qs):3d} clean  ({len(qs)-clean} reextract)  {os.path.basename(p)}")
