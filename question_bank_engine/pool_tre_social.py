import sys, os, json, re, math
sys.path.insert(0, "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine")
from tre_qa import classify
BASE = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine/drop/bpsc_tre/"
SP = "/private/tmp/claude-501/-Users-deepakkumarrai-Documents-01-Active-NvidiaSimSetup/0ecd1d51-816c-491a-83b6-1f3c0dac55ea/scratchpad"
EXT = BASE + "extracted/"

# pure GS-Social dimension papers (Part-II = History / Geography / Economics / PolSci / Sociology)
# + combined Social Science 09-10, across editions. dim = the paper's Part-II subject (bias tag).
PAPERS = [
    ("TRE1.0", "History",   "TRE1.0/For_Class_11_12__General_Studies_And_History.pdf"),
    ("TRE2.0", "History",   "TRE2.0/For_Class_11_12_Examination_dated_15_12_2023__Language_General_Studies_And_History.pdf"),
    ("TRE3.0", "History",   "TRE3.0/For_Class_11_12_Examination_dated_22_07_2024_1st_Sitting__Language_General_Studies_And_History.pdf"),
    ("TRE1.0", "Geography", "TRE1.0/For_Class_11_12__General_Studies_And_Geography.pdf"),
    ("TRE2.0", "Geography", "TRE2.0/For_Class_11_12_Examination_dated_15_12_2023__Language_General_Studies_And_Geography.pdf"),
    ("TRE3.0", "Geography", "TRE3.0/For_Class_11_12_Examination_dated_22_07_2024_1st_Sitting__Language_General_Studies_And_Geography.pdf"),
    ("TRE1.0", "Economics", "TRE1.0/For_Class_11_12__General_Studies_And_Economics.pdf"),
    ("TRE2.0", "Economics", "TRE2.0/For_Class_11_12_Examination_dated_15_12_2023__Language_General_Studies_And_Economics.pdf"),
    ("TRE3.0", "Economics", "TRE3.0/For_Class_11_12_Examination_dated_22_07_2024_1st_Sitting__Language_General_Studies_And_Economics.pdf"),
    ("TRE2.0", "Polity",    "TRE2.0/For_Class_11_12_Examination_dated_15_12_2023__Language_General_Studies_And_Political_Science.pdf"),
    ("TRE3.0", "Polity",    "TRE3.0/For_Class_11_12_Examination_dated_22_07_2024_1st_Sitting__Language_General_Studies_And_Political_Science.pdf"),
    ("TRE1.0", "Sociology", "TRE1.0/For_Class_11_12__General_Studies_And_Sociology.pdf"),
    ("TRE2.0", "SocialSci", "TRE2.0/For_Class_09_10_Examination_dated_08_12_2023__Language_General_Studies_And_Social_Science.pdf"),
    ("TRE3.0", "SocialSci", "TRE3.0/For_Class_09_10_Examination_dated_21_07_2024__Language_General_Studies_And_Social_Science.pdf"),
]

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())[:120]

seen = set()
for f in os.listdir(EXT):
    if f.endswith("_KEYED.json"):
        for r in json.load(open(EXT + f)):
            seen.add(norm(r["stem"]))
print("already-keyed stems:", len(seen))

pool = []
for ed, dimhint, rel in PAPERS:
    if not os.path.exists(BASE + rel):
        print("  MISSING", rel); continue
    qs = [q for q in classify(BASE + rel) if q["quality"] == "clean"]
    kept = 0
    for q in qs:
        h = norm(q["stem"])
        if h in seen or len(q["stem"]) < 12:
            continue
        seen.add(h)
        pool.append({"edition": ed, "dimhint": dimhint, "source": os.path.basename(rel), "seq": q["seq"],
                     "stem": q["stem"], "A": q["options"]["A"], "B": q["options"]["B"], "C": q["options"]["C"]})
        kept += 1
    print(f"  {dimhint:10s} {ed} clean={len(qs):3d} new={kept:3d}  {os.path.basename(rel)[:40]}")

for i, q in enumerate(pool):
    q["gid"] = 1000 + i + 1        # distinct gid range from wave1
print(f"\nTOTAL new deduped: {len(pool)}")
from collections import Counter
print("by dim-hint:", dict(Counter(q["dimhint"] for q in pool)))
json.dump(pool, open(f"{SP}/social_pool.json", "w"), ensure_ascii=False, indent=1)
