#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/question_bank_engine"))
from qbank import storage, validator
from qbank.models import Question, content_hash

rows = json.load(open("/tmp/tre_social_wave_KEYED.json"))
def norm(c): return "med" if (c or "").lower().startswith("med") else (c or "low").lower()
rows = [r for r in rows if norm(r["confidence"]) in ("high", "med")]

store = storage.Store("data/qbank.sqlite")
batch = []
for r in rows:
    o = r["options"]
    opts = [{"label": l, "text": str(o[l]).strip()} for l in "ABCDE" if o.get(l)]
    batch.append(Question(id=f"bpsctre_soc_{r['gid']:04d}", exam="BPSC TRE", subject="General Studies",
                          stem=r["stem"], qtype="MCQ_single", options=opts, correct_answer=r["answer"],
                          concept=r["concept"], source=f"BPSC TRE {r['edition']} (cross-source keyed)",
                          year=2023, difficulty=3, hash=content_hash(r["stem"])))
validator.validate(batch, llm=None)
nver = sum(1 for q in batch if q.verified)
for q in batch:
    store.upsert(q)
print(f"stored {len(batch)}, verified {nver}")
from collections import Counter
print("dims:", dict(Counter(q.concept for q in batch)))
n = store.con.execute("SELECT COUNT(*) FROM questions WHERE exam='BPSC TRE' AND verified=1 AND duplicate_of IS NULL").fetchone()[0]
print("BPSC TRE verified total now:", n)
# GS-Social dimension depth across the whole bank (BPSC + TRE)
print("=== GS-Social concept depth (all General Studies) ===")
for dim in ["GS: History","GS: Geography","GS: Economics","GS: Polity"]:
    c = store.con.execute("SELECT COUNT(*) FROM questions WHERE subject='General Studies' AND verified=1 AND duplicate_of IS NULL AND concept=?", (dim,)).fetchone()[0]
    print(f"   {dim:16s} {c}")
