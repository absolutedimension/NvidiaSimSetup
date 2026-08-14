import sys, os, json
sys.path.insert(0, os.path.expanduser("~/question_bank_engine"))
from qbank import storage, validator
from qbank.models import Question, content_hash
SUBJ = {"GS: Polity":"GS Polity","GS: History":"GS History","GS: Geography":"GS Geography","GS: Economics":"GS Economics"}
infile, idpref = sys.argv[1], sys.argv[2]
rows = [r for r in json.load(open(infile)) if r["confidence"] in ("high","med")]
store = storage.Store("data/qbank.sqlite")
batch = []
for r in rows:
    o = r["options"]
    opts = [{"label": l, "text": str(o[l]).strip()} for l in "ABCDE" if o.get(l)]
    subj = SUBJ.get(r["concept"], "General Studies")   # dimensions -> dimension subject; else combined GS
    batch.append(Question(id=f"{idpref}_{r['gid']:04d}", exam="BPSC TRE", subject=subj,
                          stem=r["stem"], qtype="MCQ_single", options=opts, correct_answer=r["answer"],
                          concept=r["concept"], source=f"BPSC TRE {r['edition']} (cross-source keyed)",
                          year=2023, difficulty=3, hash=content_hash(r["stem"])))
validator.validate(batch, llm=None)
nver = sum(1 for q in batch if q.verified)
for q in batch: store.upsert(q)
print(f"stored {len(batch)}, verified {nver}")
from collections import Counter
print("into subjects:", dict(Counter(q.subject for q in batch)))
