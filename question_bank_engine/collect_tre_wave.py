import json, os
from collections import Counter
SP = "/private/tmp/claude-501/-Users-deepakkumarrai-Documents-01-Active-NvidiaSimSetup/0ecd1d51-816c-491a-83b6-1f3c0dac55ea/scratchpad"
REPO_EXT = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine/drop/bpsc_tre/extracted"
DIMLABEL = {"History": "GS: History", "Geography": "GS: Geography",
            "Economics": "GS: Economics", "Polity": "GS: Polity"}

sel = {q["gid"]: q for q in json.load(open(f"{SP}/social_wave_sel.json"))}
keyed = {}; missing = []
for b in range(1, 17):
    p = f"{SP}/soc_batch_{b}_out.json"
    if not os.path.exists(p):
        missing.append(b); continue
    try:
        for r in json.load(open(p)):
            keyed[r["gid"]] = r
    except Exception as e:
        print("parse err", b, e); missing.append(b)
print("missing batches:", missing or "none", "| keyed:", len(keyed))

final = []
for gid, r in keyed.items():
    q = sel.get(gid)
    if not q:
        continue
    ans = (r.get("answer") or "").upper()
    if ans == "HELD" or ans not in "ABCDE":
        continue
    final.append({"gid": gid, "exam": "BPSC TRE", "edition": q["edition"],
                  "concept": DIMLABEL.get(q["dimhint"], "GS: Static GK / Current Affairs"),
                  "stem": q["stem"],
                  "options": {"A": q["A"], "B": q["B"], "C": q["C"],
                              "D": "More than one of the above", "E": "None of the above"},
                  "answer": ans, "confidence": r.get("confidence", "low"),
                  "sources": r.get("sources", []), "note": r.get("note", "")})
print("keyed (non-HELD):", len(final),
      "| conf", dict(Counter(r["confidence"] for r in final)),
      "| dims", dict(Counter(r["concept"] for r in final)))
out = f"{REPO_EXT}/tre_social_wave_KEYED.json"
json.dump(final, open(out, "w"), ensure_ascii=False, indent=1)
print("wrote", out)
print("high+med store-ready:", sum(1 for r in final if r["confidence"] in ("high", "med")))
