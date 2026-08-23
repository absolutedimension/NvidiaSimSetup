#!/usr/bin/env python3
"""Differential tests for the reasoning engines in qbank/reasoninggen.py.

The point of a DIFFERENTIAL test is that the oracle must not share our assumptions. Our own unit
tests are written by the same head that wrote the builders, so they agree with the builders about
whatever the builders get wrong. Each suite here checks one of our engines against an INDEPENDENT
implementation of the same logic:

  A. calendar        _weekday / _leap / _daynum   vs  Python's datetime + calendar (stdlib)
                                                  vs  reasoning-gym `calendar_arithmetic`
  B. syllogism       _syl_follows                 vs  reasoning-gym `syllogism` (is_valid)
  C. blood relations _KIN / _KIN_HI / _INV        vs  a concrete genealogy graph built here

reasoning-gym is OPTIONAL. Suites that need it skip cleanly when it is missing, so this runs in
CI without the extra dependency:

    python3 tools/difftest_reasoning.py                 # all suites, RG ones skipped if absent
    python3 tools/difftest_reasoning.py --suite b       # one suite
    python3 tools/difftest_reasoning.py --n 5000        # more RG samples
    pip install reasoning-gym                           # to enable suites A2 and B

Exit code is non-zero if any suite reports a mismatch, so it can gate a build.
"""
from __future__ import annotations

import argparse
import calendar as _stdcal
import datetime as _dt
import itertools
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qbank import reasoninggen as R  # noqa: E402

try:
    import reasoning_gym as rg
    HAVE_RG = True
except ImportError:
    rg = None
    HAVE_RG = False


class Report:
    """Collects mismatches so every suite runs to completion instead of dying on the first one."""

    def __init__(self, name):
        self.name, self.checked, self.fails = name, 0, []

    def check(self, ok, detail):
        self.checked += 1
        if not ok:
            self.fails.append(detail)

    def show(self, limit=12):
        mark = "PASS" if not self.fails else "FAIL"
        print(f"  [{mark}] {self.name}: {self.checked:,} checked, {len(self.fails)} mismatched")
        for d in self.fails[:limit]:
            print(f"         · {d}")
        if len(self.fails) > limit:
            print(f"         · … and {len(self.fails) - limit} more")
        return not self.fails


# ── A. calendar ───────────────────────────────────────────────────────────────────────────────
# _daynum implements the proleptic Gregorian day count by hand, including the century rule that
# the topic exists to test (1900 not a leap year, 2000 is). stdlib re-implements it independently.

def suite_a1(y_from=1583, y_to=2400):
    rep = Report(f"A1 calendar vs stdlib datetime ({y_from}–{y_to}, every date)")
    for y in range(y_from, y_to + 1):
        if R._leap(y) != _stdcal.isleap(y):
            rep.check(False, f"_leap({y})={R._leap(y)} but calendar.isleap={_stdcal.isleap(y)}")
        for m in range(1, 13):
            for d in range(1, _stdcal.monthrange(y, m)[1] + 1):
                # date.toordinal() counts 1 Jan 0001 as day 1 — the same origin _daynum documents.
                ours_n, theirs_n = R._daynum(y, m, d), _dt.date(y, m, d).toordinal()
                if ours_n != theirs_n:
                    rep.check(False, f"_daynum({y},{m},{d})={ours_n} vs ordinal {theirs_n}")
                    continue
                ours = R._weekday(y, m, d)
                theirs = R._DAYS[(_dt.date(y, m, d).weekday() + 1) % 7]  # Mon=0 -> our Sun-first
                rep.check(ours == theirs, f"_weekday({y},{m},{d})={ours} vs {theirs}")
    return rep


_RG_CAL_ABS = re.compile(r"What day of the week was (\w+) (\d+), (\d+)\?")


def suite_a2(n=2000):
    rep = Report("A2 calendar vs reasoning-gym `calendar_arithmetic`")
    if not HAVE_RG:
        print("  [SKIP] A2 — reasoning-gym not installed")
        return rep
    for x in rg.create_dataset("calendar_arithmetic", size=n, seed=20260822):
        m = _RG_CAL_ABS.search(x["question"])
        if not m:
            continue          # relative-date phrasings; A1 already covers the arithmetic
        mon, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        if mon not in R._MONTHS:
            continue
        ours = R._weekday(year, R._MONTHS.index(mon) + 1, day)
        theirs = str(x["answer"]).strip()
        rep.check(ours.lower() == theirs.lower(),
                  f"{mon} {day}, {year}: ours={ours} rg={theirs}")
    return rep


# ── B. syllogism ──────────────────────────────────────────────────────────────────────────────
# _syl_follows decides validity by countermodel search over occupied Venn cells. reasoning-gym
# ships is_valid from its own generator. Parse its English back into our (kind, x, y) triples.

_PATS = [
    (re.compile(r"^All (.+?) are (.+?)$", re.I), "all"),
    (re.compile(r"^No (.+?) are (.+?)$", re.I), "no"),
    (re.compile(r"^Some (.+?) are not (.+?)$", re.I), "some_not"),
    (re.compile(r"^Some (.+?) are (.+?)$", re.I), "some"),
]


def _parse(sentence):
    """'Some lawyers are not birds' -> ('some_not', 'lawyers', 'birds'). some_not before some."""
    s = sentence.strip().rstrip(".")
    for pat, kind in _PATS:
        m = pat.match(s)
        if m:
            return kind, m.group(1).strip().lower(), m.group(2).strip().lower()
    return None


# Two forms reasoning-gym's `syllogism` generator asserts as valid that are textbook fallacies.
# Confirmed against brute-force enumeration in suite B2 (see REASONING_GYM_AUDIT.md):
#   All X are Y ; Some Y are Z      => Some X are Z          undistributed middle
#   All X are Y ; Some Y are not Z  => Some X are not Z      undistributed middle
# Countermodel for the first: occupy only XY and YZ. Every X is a Y, some Y is a Z, no X is a Z.
# These are counted separately so a known upstream defect does not redden our build, while any
# NEW divergence still fails it.
_RG_KNOWN_BAD = {("all", "some", "some"), ("all", "some_not", "some_not")}


def suite_b(n=3000):
    rep = Report("B syllogism `_syl_follows` vs reasoning-gym `syllogism`")
    if not HAVE_RG:
        print("  [SKIP] B — reasoning-gym not installed")
        return rep
    undecided = 0
    upstream = 0
    for x in rg.create_dataset("syllogism", size=n, seed=20260822):
        md = x["metadata"]
        parsed = [_parse(md[k]) for k in ("premise1", "premise2", "conclusion")]
        if any(p is None for p in parsed):
            continue
        terms = sorted({t for p in parsed for t in p[1:]})
        if len(terms) > 8:
            continue
        idx = {t: i for i, t in enumerate(terms)}
        sts = [(k, idx[a], idx[b]) for k, a, b in parsed[:2]]
        ck, ca, cb = parsed[2]
        got = R._syl_follows(sts, len(terms), (ck, idx[ca], idx[cb]))
        if got is None:
            # our engine says the premises admit no model at all; RG asserts validity anyway
            undecided += 1
            continue
        agree = bool(got) == bool(md["is_valid"])
        if not agree and (parsed[0][0], parsed[1][0], ck) in _RG_KNOWN_BAD:
            upstream += 1                        # known reasoning-gym defect, not ours
            continue
        rep.check(agree,
                  f"[{md.get('type')}] {md['premise1']} / {md['premise2']} => "
                  f"{md['conclusion']} : ours={got} rg={md['is_valid']}")
    if undecided:
        print(f"         (note: {undecided} items where our engine found the premises unsatisfiable)")
    if upstream:
        print(f"         (note: {upstream} known-bad reasoning-gym items excluded — see _RG_KNOWN_BAD)")
    return rep


def _brute_follows(sts, k, concl):
    """Independent validity oracle: enumerate EVERY model and look for a counterexample.

    A model is a set of occupied Venn cells (a cell is a membership pattern over the k terms).
    Our `_syl_follows` avoids this enumeration with a maximal-model argument; this one does the
    dumb exponential thing, so agreement between them is real evidence rather than a shared trick.
    Existential import is assumed on both sides: every term must have at least one member.
    """
    cells = range(1, 1 << k)

    def holds(model, st):
        kind, x, y = st
        if kind == "all":
            return all(not (c >> x & 1) or (c >> y & 1) for c in model)
        if kind == "no":
            return all(not ((c >> x & 1) and (c >> y & 1)) for c in model)
        if kind == "some":
            return any((c >> x & 1) and (c >> y & 1) for c in model)
        return any((c >> x & 1) and not (c >> y & 1) for c in model)

    seen_model = False
    for mask in range(1, 1 << (1 << k) - 1):
        model = [c for i, c in enumerate(cells) if mask >> i & 1]
        if not model:
            continue
        if any(not any(c >> t & 1 for c in model) for t in range(k)):
            continue                                    # a term with no members
        if not all(holds(model, s) for s in sts):
            continue
        seen_model = True
        if not holds(model, concl):
            return False                                # countermodel found
    return True if seen_model else None


def suite_b2():
    """Every 3-term form, our engine vs brute force. No reasoning-gym needed."""
    rep = Report("B2 `_syl_follows` vs brute-force model enumeration (all 3-term forms)")
    kinds = ("all", "no", "some", "some_not")
    pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
    for k1 in kinds:
        for p1 in pairs:
            for k2 in kinds:
                for p2 in pairs:
                    sts = [(k1,) + p1, (k2,) + p2]
                    for kc in kinds:
                        for pc in pairs:
                            concl = (kc,) + pc
                            ours = R._syl_follows(sts, 3, concl)
                            theirs = _brute_follows(sts, 3, concl)
                            rep.check(ours == theirs,
                                      f"{sts} => {concl} : ours={ours} brute={theirs}")
    return rep


# ── C. blood relations ────────────────────────────────────────────────────────────────────────
# _KIN says: A is r1 of B, B is r2 of C  =>  A is _KIN[(r1,r2)] of C. Rather than re-deriving that
# from the same reasoning, build a CONCRETE family and read the answer off the graph.

class Family:
    """A tiny genealogy with explicit father/mother slots.

    Ground truth is the graph, not a lookup table. Assigning a slot that is already filled
    UNIFIES the two people (rewriting every occurrence of the old name), which is what makes
    "A is the father of B, and B is the brother of C" correctly imply that A is C's father too.
    """

    def __init__(self):
        self.sex, self.father, self.mother = {}, {}, {}
        self._n = 0

    def add(self, sex, name=None):
        if name is None:
            self._n += 1
            name = f"_p{self._n}"
        self.sex[name] = sex
        return name

    def _rename(self, old, new):
        for slot in (self.father, self.mother):
            for k, v in list(slot.items()):
                if v == old:
                    slot[k] = new
            if old in slot:
                slot.setdefault(new, slot[old])
                del slot[old]
        self.sex.pop(old, None)

    def _set(self, slot, child, person):
        cur = slot.get(child)
        if cur is not None and cur != person:
            self._rename(cur, person)          # the two names denote the same person
        slot[child] = person

    def set_parent(self, child, person):
        self._set(self.father if self.sex[person] == "M" else self.mother, child, person)

    def ensure_parents(self, child):
        if child not in self.father:
            self.father[child] = self.add("M")
        if child not in self.mother:
            self.mother[child] = self.add("F")

    def parents(self, p):
        return {v for v in (self.father.get(p), self.mother.get(p)) if v}

    def siblings(self, p):
        out = set()
        for q in self.sex:
            if q == p or not self.parents(p):
                continue
            if q != p and self.parents(q) == self.parents(p) and len(self.parents(p)) == 2:
                out.add(q)
        return out

    def children(self, p):
        return {c for c in self.sex if p in self.parents(c)}

    def link(self, x, rel, y):
        """Assert 'X is the <rel> of Y' against the graph."""
        if rel in ("father", "mother"):
            self.ensure_parents(y)
            self.set_parent(y, x)
        elif rel in ("son", "daughter"):
            self.ensure_parents(x)
            self.set_parent(x, y)
        elif rel in ("brother", "sister"):
            self.ensure_parents(y)
            self.father[x], self.mother[x] = self.father[y], self.mother[y]
        else:
            raise ValueError(rel)

    def relation(self, a, c):
        """How is A related to C? Read off the graph."""
        m = self.sex[a] == "M"
        if a in self.parents(c):
            return "father" if m else "mother"
        if c in self.parents(a):
            return "son" if m else "daughter"
        if a in self.siblings(c):
            return "brother" if m else "sister"
        # A is C's grandparent  <=>  A is a parent of one of C's parents
        if any(a in self.parents(p) for p in self.parents(c)):
            return "grandfather" if m else "grandmother"
        # A is C's grandCHILD  <=>  C is a parent of one of A's parents
        if any(c in self.parents(p) for p in self.parents(a)):
            return "grandson" if m else "granddaughter"
        if any(a in self.siblings(p) for p in self.parents(c)):
            return "uncle" if m else "aunt"
        if any(c in self.siblings(p) for p in self.parents(a)):
            return "nephew" if m else "niece"
        return "unrelated"

    def hindi_relation(self, a, c):
        """The Hindi answer names the ROUTE, so it needs the LINKING relative's sex too."""
        rel = self.relation(a, c)
        if rel in ("grandfather", "grandmother"):
            link = next(p for p in self.parents(c) if a in self.parents(p))
            return {("grandfather", "M"): "\u0926\u093e\u0926\u093e", ("grandfather", "F"): "\u0928\u093e\u0928\u093e",
                    ("grandmother", "M"): "\u0926\u093e\u0926\u0940", ("grandmother", "F"): "\u0928\u093e\u0928\u0940"}[(rel, self.sex[link])]
        if rel in ("grandson", "granddaughter"):
            link = next(p for p in self.parents(a) if c in self.parents(p))
            return {("grandson", "M"): "\u092a\u094b\u0924\u093e", ("grandson", "F"): "\u0928\u093e\u0924\u0940",
                    ("granddaughter", "M"): "\u092a\u094b\u0924\u0940", ("granddaughter", "F"): "\u0928\u093e\u0924\u093f\u0928"}[(rel, self.sex[link])]
        if rel in ("uncle", "aunt"):
            link = next(p for p in self.parents(c) if a in self.siblings(p))
            return {("uncle", "M"): "\u091a\u093e\u091a\u093e", ("uncle", "F"): "\u092e\u093e\u092e\u093e",
                    ("aunt", "M"): "\u092c\u0941\u0906", ("aunt", "F"): "\u092e\u094c\u0938\u0940"}[(rel, self.sex[link])]
        if rel in ("nephew", "niece"):
            link = next(p for p in self.parents(a) if c in self.siblings(p))
            return {("nephew", "M"): "\u092d\u0924\u0940\u091c\u093e", ("nephew", "F"): "\u092d\u093e\u0902\u091c\u093e",
                    ("niece", "M"): "\u092d\u0924\u0940\u091c\u0940", ("niece", "F"): "\u092d\u093e\u0902\u091c\u0940"}[(rel, self.sex[link])]
        return None


def _realise(r1, r2):
    """Build a family in which 'A is r1 of B and B is r2 of C' literally holds.

    C's own sex is free and can change the Hindi answer's route, so yield both.
    """
    for sex_c in ("M", "F"):
        f = Family()
        c = f.add(sex_c, "C")
        b = f.add(R._REL_GENDER[r2], "B")
        a = f.add(R._REL_GENDER[r1], "A")
        f.link(b, r2, c)
        f.link(a, r1, b)
        yield f


def suite_c():
    rep_en = Report("C1 blood relations `_KIN` vs concrete genealogy graph")
    rep_hi = Report("C2 blood relations `_KIN_HI` (route-aware) vs graph")
    for (r1, r2), expected in R._KIN.items():
        for f in _realise(r1, r2):
            got = f.relation("A", "C")
            rep_en.check(got == expected,
                         f"A is {r1} of B, B is {r2} of C: table says '{expected}', graph says '{got}'")
            exp_hi = R._KIN_HI.get((r1, r2))
            if exp_hi:
                got_hi = f.hindi_relation("A", "C")
                rep_hi.check(got_hi == exp_hi,
                             f"A is {r1} of B, B is {r2} of C: _KIN_HI says '{exp_hi}', "
                             f"graph says '{got_hi}'")
    rep_inv = Report("C3 `_INV` is a proper involution")
    for k, v in R._INV.items():
        rep_inv.check(R._INV.get(v) == k, f"_INV['{k}']='{v}' but _INV['{v}']={R._INV.get(v)!r}")
    return [rep_en, rep_hi, rep_inv]


# ── driver ────────────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="all", help="a, b, c or all")
    ap.add_argument("--n", type=int, default=3000, help="reasoning-gym samples per RG suite")
    ap.add_argument("--years", default="1583:2400", help="calendar range, FROM:TO")
    a = ap.parse_args()
    y0, y1 = (int(v) for v in a.years.split(":"))

    print(f"differential tests · reasoning-gym {'available' if HAVE_RG else 'NOT installed'}\n")
    reps = []
    if a.suite in ("a", "all"):
        print("Suite A — calendar")
        reps += [suite_a1(y0, y1), suite_a2(a.n)]
    if a.suite in ("b", "all"):
        print("Suite B — syllogism")
        reps += [suite_b(a.n), suite_b2()]
    if a.suite in ("c", "all"):
        print("Suite C — blood relations")
        reps += suite_c()

    print()
    ok = all([r.show() for r in reps])   # list, not genexp: all() must not short-circuit
    print("\n" + ("ALL SUITES AGREE" if ok else "MISMATCHES FOUND — see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
