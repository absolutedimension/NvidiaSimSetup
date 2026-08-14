#!/usr/bin/env python3
"""Load cross-source-keyed BPSC TRE questions (drop/bpsc_tre/extracted/*_KEYED.json) into a
question bank as REAL verified 5-option (A-E) questions (generated=0).

Serving discipline (see BPSC_TRE_STATUS.md / TRE_KEYED_SUMMARY.md):
  * Only rows with status=="keyed" are loaded. --min-confidence gates high vs high+med.
  * Options are the full A-E set (D="More than one of the above", E="None of the above").
  * correct_answer = the keyed letter; validator (now A-E aware) sets verified=1.
  * DEFAULT target is a LOCAL TEST DB. Writing the live bank requires --db <path> explicitly,
    and per project guardrails must be preceded by a DB backup + an official-key spot-check on
    flagged medium-confidence discrepancies. This script never touches Gurukul on its own.
"""
import argparse, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qbank import storage, validator
from qbank.models import Question, content_hash

BOILER = {"D": "More than one of the above", "E": "None of the above"}


def load_file(path, min_conf):
    rows = json.load(open(path))
    keep = []
    conf_rank = {"high": 2, "med": 1, "low": 0}
    floor = conf_rank[min_conf]
    for r in rows:
        if r.get("status") != "keyed":
            continue
        if conf_rank.get(r.get("confidence", "low"), 0) < floor:
            continue
        keep.append(r)
    return rows, keep


def to_question(r, id_prefix):
    o = r["options"]
    opts = [{"label": l, "text": str(o[l]).strip()} for l in "ABCDE" if l in o and str(o[l]).strip()]
    qid = f"{id_prefix}_{r['edition'].replace('.', '')}_{r['seq']:03d}"
    subj = r.get("paper", r.get("edition", "General Studies"))
    return Question(
        id=qid, exam=r["exam"], subject="General Studies",
        stem=r["stem"], qtype="MCQ_single", options=opts,
        correct_answer=r["answer"],
        source=f"{r['exam']} {r['edition']} {r.get('paper','')} (cross-source keyed)".strip(),
        year=2023, difficulty=3, hash=content_hash(r["stem"]),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="*_KEYED.json files")
    ap.add_argument("--db", default=None, help="target sqlite (default: a local test db)")
    ap.add_argument("--min-confidence", choices=["high", "med", "low"], default="med")
    ap.add_argument("--id-prefix", default="bpsctre")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db = args.db or "/tmp/tre_test_bank.sqlite"
    live = args.db is not None
    print(f"target DB: {db}  ({'LIVE — ensure backup+spot-check' if live else 'local test'})")
    store = storage.Store(db) if not args.dry_run else None

    total_keyed = total_stored = total_verified = 0
    for pat in args.files:
        for path in sorted(glob.glob(pat)):
            allrows, keep = load_file(path, args.min_confidence)
            batch = [to_question(r, args.id_prefix) for r in keep]
            if not args.dry_run:
                validator.validate(batch, llm=None)          # A-E aware -> verified=1
                for qq in batch:
                    store.upsert(qq)
            nver = sum(1 for qq in batch if qq.verified)
            total_keyed += len(keep); total_stored += len(batch); total_verified += nver
            print(f"  {os.path.basename(path):40s} keyed={len(keep):3d}  stored={len(batch):3d}  verified={nver:3d}")
    print(f"\nTOTAL  keyed_selected={total_keyed}  stored={total_stored}  verified={total_verified}"
          + ("  (dry-run)" if args.dry_run else ""))
    if not args.dry_run:
        print("stats:", store.stats())


if __name__ == "__main__":
    main()
