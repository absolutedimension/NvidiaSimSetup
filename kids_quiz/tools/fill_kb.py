#!/usr/bin/env python3
"""fill_kb.py — add content to a knowledge base WITHOUT ever making it invalid.

The KB engine's guarantee is that a generated question is correct by construction, and
kb_engine._validate() is what enforces it. Hand-editing a KB is where that breaks: adding a
synonym pair whose left value already exists gives a cloze two correct answers, so a child is
marked wrong for a right answer. That happened on the first attempt at hindi_class3.

So every addition goes through here:
  relations  — a pair is added only if its LEFT value is new (a->b must stay a function)
  categories — members deduped; a new category is rejected if its members overlap an existing
               one (odd-one-out picks the odd item from a DISJOINT category)
  groupings  — items deduped within and across bins (an item in two bins has no right answer)
  facts      — deduped by statement

Then it re-validates by loading through kb_engine, and refuses to write if that fails.

    from fill_kb import fill
    fill("hindi_class3", relations={...}, categories=[...], facts=[...])
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import kb_engine as KB                     # noqa: E402

KBDIR = os.path.join(ROOT, "kb")


def _norm(x):
    return str(x).strip().lower()


def fill(name, relations=None, categories=None, groupings=None, facts=None, quiet=False):
    path = os.path.join(KBDIR, name + ".json")
    kb = json.load(open(path, encoding="utf-8"))
    report = {"pairs": 0, "pairs_skipped": 0, "members": 0, "cats": 0, "cats_skipped": 0,
              "facts": 0, "facts_skipped": 0, "rels": 0}

    # ---- relations: extend existing by name, or append whole new ones ----
    for rel in (relations or []):
        cur = next((r for r in kb.get("relations", []) if r["name"] == rel["name"]), None)
        if cur is None:
            seen = set()
            pairs = []
            for a, b in rel.get("pairs", []):
                if _norm(a) in seen:
                    report["pairs_skipped"] += 1
                    continue
                seen.add(_norm(a))
                pairs.append([a, b])
            rel = {**rel, "pairs": pairs}
            kb.setdefault("relations", []).append(rel)
            report["rels"] += 1
            report["pairs"] += len(pairs)
        else:
            seen = {_norm(a) for a, _ in cur["pairs"]}
            for a, b in rel.get("pairs", []):
                if _norm(a) in seen:
                    report["pairs_skipped"] += 1
                    continue
                seen.add(_norm(a))
                cur["pairs"].append([a, b])
                report["pairs"] += 1

    # ---- categories: a new one must not overlap an existing one ----
    for cat in (categories or []):
        cur = next((c for c in kb.get("categories", []) if c["name"] == cat["name"]), None)
        if cur is not None:
            have = {_norm(m) for m in cur["members"]}
            for m in cat.get("members", []):
                if _norm(m) not in have:
                    have.add(_norm(m))
                    cur["members"].append(m)
                    report["members"] += 1
            continue
        others = {_norm(m) for c in kb.get("categories", []) for m in c["members"]}
        members, seen = [], set()
        for m in cat.get("members", []):
            if _norm(m) in seen or _norm(m) in others:
                continue
            seen.add(_norm(m))
            members.append(m)
        if len(members) < 4:            # too thin to draw a 3+1 odd-one-out from
            report["cats_skipped"] += 1
            continue
        kb.setdefault("categories", []).append({**cat, "members": members})
        report["cats"] += 1
        report["members"] += len(members)

    # ---- groupings: an item may belong to exactly one bin ----
    for grp in (groupings or []):
        cur = next((g for g in kb.get("groupings", []) if g["name"] == grp["name"]), None)
        if cur is None:
            bins, used = {}, set()
            for b, items in grp.get("bins", {}).items():
                keep = [i for i in items if _norm(i) not in used and not used.add(_norm(i))]
                bins[b] = keep
            kb.setdefault("groupings", []).append({**grp, "bins": bins})
        else:
            used = {_norm(i) for v in cur["bins"].values() for i in v}
            for b, items in grp.get("bins", {}).items():
                cur["bins"].setdefault(b, [])
                for i in items:
                    if _norm(i) in used:
                        continue
                    used.add(_norm(i))
                    cur["bins"][b].append(i)
                    report["members"] += 1

    # ---- facts ----
    have = {_norm(f["statement"]) for f in kb.get("facts", [])}
    for f in (facts or []):
        if _norm(f["statement"]) in have:
            report["facts_skipped"] += 1
            continue
        have.add(_norm(f["statement"]))
        kb.setdefault("facts", []).append(f)
        report["facts"] += 1

    # ---- write only if it still validates ----
    tmp = path + ".tmp"
    json.dump(kb, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:
        KB.load_kb(tmp)                  # raises on any shape that could emit a wrong question
    except Exception as exc:
        os.remove(tmp)
        raise SystemExit(f"REFUSED to write {name}: {str(exc)[:400]}")
    os.replace(tmp, path)
    if not quiet:
        print(f"  {name:18} +{report['pairs']}p +{report['members']}m +{report['facts']}f "
              f"(skipped {report['pairs_skipped']}p/{report['facts_skipped']}f)")
    return report
