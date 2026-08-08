#!/usr/bin/env python3
"""
store_real_questions.py — Store vision-extracted questions into the qbank as REAL, VERIFIED
questions (generated=0, verified=1). No generative AI, no paraphrase — the stem/options are
exactly what qwen_extract.py transcribed, and the correct_answer comes from the OFFICIAL key.

Generalized from the proven UPSC `store_from_qwen.py`. Parametrised so Class 10/12 PCM +
Commerce (and any board) reuse it unchanged.

Inputs:
  --qdir      dir of <TAG>.json files from qwen_extract.py   (TAG e.g. 2025_QP1, 2024_PHY_SETA)
  --keys      JSON: { "<TAG>": { "<qnum>": "<A|B|C|D or X-to-drop>" }, ... }
              (X = question officially dropped/bonus -> skipped)
  --exam      exam label stored on every row  (e.g. "CBSE Class 12 Physics")
  --map       JSON mapping each TAG -> {"subject": "...", "paper": "...", "year": 2025}
              e.g. '{"2025_PHY_SETA": {"subject":"Physics","paper":"Set A","year":2025}}'
  --id-prefix short slug for ids  (e.g. cbse12phy  ->  cbse12phy_2025_setA_001)
  --difficulty default difficulty band to stamp (3 for UPSC/boards; tune later per tagging)
  --no-key-verified  if a TAG has NO key (latest year not yet released): store verified=0,
                     correct_answer='' so a later official-key or human pass can fill it.

Run ON the serving VM (writes the store-of-record SQLite):
  cd ~/question_bank_engine && PYTHONPATH=$PWD python3 store_real_questions.py \
     --qdir ~/drop/qwen --keys ~/drop/keys.json --exam "CBSE Class 12 Physics" \
     --map ~/drop/tagmap.json --id-prefix cbse12phy
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.expanduser("~/question_bank_engine"))
from qbank.models import Question, content_hash          # noqa: E402
from qbank import storage, validator                     # noqa: E402


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())[:12] or "x"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qdir", required=True)
    ap.add_argument("--keys", default="")
    ap.add_argument("--exam", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--id-prefix", required=True)
    ap.add_argument("--difficulty", type=int, default=3)
    ap.add_argument("--no-key-verified", action="store_true")
    args = ap.parse_args()

    KEYS = json.load(open(os.path.expanduser(args.keys))) if args.keys else {}
    TAGMAP = json.load(open(os.path.expanduser(args.map)))
    store = storage.Store()
    summary = {}

    for jf in sorted(glob.glob(os.path.join(os.path.expanduser(args.qdir), "*.json"))):
        tag = os.path.basename(jf)[:-5]                  # 2025_PHY_SETA
        meta = TAGMAP.get(tag)
        if not meta:
            print(f"!! {tag}: no entry in --map, skipping"); continue
        subject = meta["subject"]; paper = meta.get("paper", ""); year = int(meta.get("year", 0))
        keys = KEYS.get(tag, {})
        data = json.load(open(jf))
        ok = dropped = nokey = bad = 0
        batch = []
        for numstr, q in data.items():
            n = int(q.get("number", numstr))
            stem = (q.get("stem") or "").strip()
            opts_d = q.get("options") or {}
            labels = [l for l in "ABCD" if l in opts_d]
            opts = [{"label": l, "text": str(opts_d.get(l, "")).strip()} for l in labels]
            is_mcq = len(opts) >= 2 and all(o["text"] for o in opts)
            if len(stem) < 15:
                bad += 1; continue
            if keys and is_mcq:
                k = keys.get(str(n))
                if k is None: nokey += 1; continue
                if k == "X": dropped += 1; continue
                ans = k
            else:
                ans = ""                                 # no key OR descriptive question
            qid = f"{args.id_prefix}_{year}_{slug(paper) or 'p'}_{n:03d}"
            qq = Question(id=qid, exam=args.exam, subject=subject, stem=stem,
                          qtype="MCQ_single" if is_mcq else "descriptive",
                          options=opts, correct_answer=ans,
                          source=f"{args.exam} {year} {paper} (official)".strip(),
                          year=year, difficulty=args.difficulty, hash=content_hash(stem))
            batch.append(qq); ok += 1
        # verified=1 ONLY when we have an official key AND it's an auto-checkable MCQ
        if keys and not args.no_key_verified:
            validator.validate(batch, llm=None)          # rule-check -> verified=1 for keyed MCQ
        else:
            for qq in batch:
                qq.verified = False
        for qq in batch:
            store.upsert(qq)
        summary[tag] = {"stored": ok, "dropped": dropped, "no_key": nokey, "bad": bad}
        print(f"{tag}: stored={ok} dropped={dropped} no_key={nokey} bad={bad}", flush=True)

    print("\n=== TOTALS for", args.exam, "===")
    for r in store.con.execute(
            "SELECT subject,year,COUNT(*),SUM(verified) FROM questions WHERE exam=? "
            "GROUP BY subject,year ORDER BY year,subject", (args.exam,)):
        print(f"  {r[0]} {r[1]}: {r[2]} rows, {r[3]} verified")


if __name__ == "__main__":
    main()
