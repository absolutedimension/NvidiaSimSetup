#!/usr/bin/env python3
"""Draw a paper to the SYLLABUS, not to the list of generators we happen to own.

The problem this fixes, measured on the delivered sets:

  MATHS   ब्याज (interest) is ~1% of the real BSSC maths questions and got 32% of ours.
          प्रतिशत (percentage) is 16% of the real questions and got ZERO — even though
          quantgen has had a percentage builder all along. The section drew round-robin
          across whatever builders exist, so 23 builders produced 7 topics and the paper's
          shape was decided by which builder happened to be asked first.

  REASONING The per-concept cap of 4 makes the section even ACROSS CONCEPTS, which is not the
          same as even across the syllabus. खंड (ग) groups our 19 concepts into 12 named
          topics, and four of our concepts sit inside ONE of them — so अंक गणितीय तर्कशक्ति
          got 14 questions against a 6-question target while संबंध अवधारणा got 1 against 4.

  "Balanced" has to have a denominator. This module makes that denominator the commission's
  own topic list (drop/bssc/SYLLABUS_MAP.json), so a section is even against what is actually
  examined rather than against itself.

Nothing here generates or checks a question. It converts shares into whole-question quotas,
maps a drawn question back to its syllabus topic, and prints what the paper covered and what it
could not — because a quota that silently went unfilled reads as "we built to the syllabus" when
we did not, and that is the exact failure this line keeps producing.
"""
import io
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
_MAP_PATH = REPO / "question_bank_engine/drop/bssc/SYLLABUS_MAP.json"
_MAP = None


def load():
    global _MAP
    if _MAP is None:
        _MAP = json.load(io.open(_MAP_PATH, encoding="utf-8"))
    return _MAP


def topics(section):
    """Every named syllabus topic for a section, generatable or not."""
    for khand, spec in load().items():
        if khand.startswith("_"):
            continue
        if spec.get("section") == section:
            return spec["topics"]
    return []


def excluded_builders():
    """Builders deliberately kept off an Inter Level paper — see SYLLABUS_MAP._excluded."""
    return set((load().get("_excluded") or {}).get("builders") or [])


def quotas(section, n):
    """-> {topic_en: count} summing to n, over the topics we can actually generate.

    The shares of the ungeneratable topics are redistributed across the rest rather than left
    as a hole, because a 50-question section must still print 50 questions. What was lost is
    reported separately by `report()` — redistributing quietly is how a gap becomes invisible.
    """
    ts = [t for t in topics(section) if (t.get("builders") or t.get("concepts"))]
    if not ts or n <= 0:
        return {}
    total = sum(t["share"] for t in ts)
    raw = {t["en"]: t["share"] / total * n for t in ts}
    out = {k: int(v) for k, v in raw.items()}
    # hand the rounding remainder to the topics with the largest fractional part, so the quota
    # sums to n exactly and the biggest topics are not the ones that lose a question
    short = n - sum(out.values())
    for k in sorted(raw, key=lambda k: -(raw[k] - int(raw[k])))[:short]:
        out[k] += 1
    return out


def topic_of(section, concept):
    """Which named syllabus topic a drawn question belongs to."""
    for t in topics(section):
        if concept in (t.get("concepts") or []) or concept in (t.get("builders") or []):
            return t["en"]
    return None


def missing(section):
    """Named topics with no generator, and the share of the section they were meant to carry."""
    return [(t["en"], t["hi"], t["share"]) for t in topics(section)
            if not (t.get("builders") or t.get("concepts"))]


def report(section, items, concept_of=lambda q: (q.get("concept") or "?")):
    """Printed lines: what the section drew per syllabus topic, against target, plus the gaps."""
    from collections import Counter
    n = len(items)
    if not n:
        return []
    want = quotas(section, n)
    got = Counter()
    unmapped = 0
    for q in items:
        t = topic_of(section, concept_of(q))
        if t:
            got[t] += 1
        else:
            unmapped += 1
    lines = [f"  syllabus coverage — {section} ({n} questions)"]
    for t in sorted(want, key=lambda k: -want[k]):
        mark = "ok " if got[t] == want[t] else ("+" if got[t] > want[t] else "-")
        lines.append(f"      {mark} {got[t]:2d}/{want[t]:<2d}  {t}")
    if unmapped:
        lines.append(f"      ?  {unmapped:2d}      not mapped to any syllabus topic")
    gaps = missing(section)
    if gaps:
        lines.append("      NOT GENERATABLE (no content yet) — "
                     + "; ".join(f"{en} {int(sh * 100)}%" for en, _hi, sh in gaps))
    return lines
