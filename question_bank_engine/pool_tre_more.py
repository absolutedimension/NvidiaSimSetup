import sys, os, json, re, hashlib, math
sys.path.insert(0, "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine")
from tre_qa import classify
BASE = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine/drop/bpsc_tre/"
SP = "/private/tmp/claude-501/-Users-deepakkumarrai-Documents-01-Active-NvidiaSimSetup/0ecd1d51-816c-491a-83b6-1f3c0dac55ea/scratchpad"
EXT = BASE + "extracted/"

# high-value unkeyed papers: GS-Social + Science-rich, spread across editions/classes
PAPERS = [
    ("TRE1.0", "TRE1.0/General_Studies_Paper_2_1st_Sitting__General_Studies_Paper_2.pdf"),
    ("TRE1.0", "TRE1.0/General_Studies_Paper_2_2nd_Sitting__General_Studies_Paper_2.pdf"),
    ("TRE1.0", "TRE1.0/For_Class_09_10__General_Studies_And_Social_Science.pdf"),
    ("TRE1.0", "TRE1.0/For_Class_11_12__General_Studies_And_Political_Science.pdf"),
    ("TRE2.0", "TRE2.0/For_Class_06_08_Examination_dated_09_12_2023__Language_General_Studies_And_Social_Science.pdf"),
    ("TRE2.0", "TRE2.0/For_Class_06_08_Examination_dated_09_12_2023__Language_General_Studies_And_Mathematics_And_Science.pdf"),
    ("TRE3.0", "TRE3.0/For_Class_06_08_Examination_dated_19_07_2024__Language_General_Studies_And_Social_Science.pdf"),
    ("TRE3.0", "TRE3.0/For_Class_06_08_Examination_dated_19_07_2024__Language_General_Studies_And_Mathematics_And_Science.pdf"),
]

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())[:120]

# dedupe against already-keyed stems (the 3 keyed JSONs)
seen = set()
for f in os.listdir(EXT):
    if f.endswith("_KEYED.json"):
        for r in json.load(open(EXT + f)):
            seen.add(norm(r["stem"]))
print("already-keyed stems:", len(seen))

pool = []
for ed, rel in PAPERS:
    qs = [q for q in classify(BASE + rel) if q["quality"] == "clean"]
    kept = 0
    for q in qs:
        h = norm(q["stem"])
        if h in seen or len(q["stem"]) < 12:
            continue
        seen.add(h)
        pool.append({"edition": ed, "source": os.path.basename(rel), "seq": q["seq"],
                     "stem": q["stem"], "A": q["options"]["A"], "B": q["options"]["B"], "C": q["options"]["C"]})
        kept += 1
    print(f"  {os.path.basename(rel)[:55]:55s} clean={len(qs):3d} new={kept:3d}")

print(f"\nTOTAL new deduped clean questions: {len(pool)}")
# assign global ids, cap, batch
for i, q in enumerate(pool):
    q["gid"] = i + 1
json.dump(pool, open(f"{SP}/tre_more_pool.json", "w"), ensure_ascii=False, indent=1)
N = 10
per = math.ceil(len(pool) / N)
for b in range(N):
    ch = pool[b*per:(b+1)*per]
    if ch:
        recs = [{"gid": q["gid"], "stem": q["stem"], "A": q["A"], "B": q["B"], "C": q["C"]} for q in ch]
        json.dump(recs, open(f"{SP}/more_batch_{b+1}.json", "w"), ensure_ascii=False, indent=1)
print(f"batched into {min(N, math.ceil(len(pool)/per) if per else 0)} files of ~{per}")
