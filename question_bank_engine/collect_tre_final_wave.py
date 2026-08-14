# collect a final wave: args = prefix nbatches sel_json out_name
import json, os, re, sys
from collections import Counter
SP = "/private/tmp/claude-501/-Users-deepakkumarrai-Documents-01-Active-NvidiaSimSetup/0ecd1d51-816c-491a-83b6-1f3c0dac55ea/scratchpad"
REPO_EXT = "/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/question_bank_engine/drop/bpsc_tre/extracted"
prefix, nb, sel_json, out_name = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]

# per-question dimension classifier (for mixed Sociology/SocialSci/GS-Paper-2)
DIMS = {"GS: Polity": r"constitution|article \d|fundamental right|parliament|lok sabha|rajya sabha|president|governor|supreme court|judiciary|amendment|election commission|panchayat|directive principle|citizenship|writ|sovereign|democracy|state|rights|caste|society|social",
        "GS: History": r"dynasty|empire|emperor|sultan|mughal|maurya|gupta|ashoka|buddha|jain|harappa|vedic|medieval|ancient|battle|revolt|freedom|independence|movement|gandhi|british|partition|treaty|chola|maratha|congress|1857|civilization",
        "GS: Economics": r"gdp|inflation|fiscal|monetary|budget|tax|gst|poverty|unemployment|plan|niti aayog|reserve bank|rbi|economic|revenue|export|import|banking|income|market|capital|demand|supply|price|cost",
        "GS: Geography": r"river|mountain|himalaya|plateau|monsoon|climate|soil|crop|mineral|ocean|lake|forest|park|plain|desert|delta|glacier|rainfall|peak|volcano|island|latitude|zone|region"}
def dim_of(stem, hint):
    m = {"History":"GS: History","Geography":"GS: Geography","Economics":"GS: Economics","Polity":"GS: Polity"}
    if hint in m: return m[hint]
    s = stem.lower()
    sc = {d: len(re.findall(p, s)) for d, p in DIMS.items()}
    b = max(sc, key=sc.get)
    return b if sc[b] else "GS: Static GK / Current Affairs"

sel = {q["gid"]: q for q in json.load(open(f"{SP}/{sel_json}"))}
keyed = {}; missing = []
for b in range(1, nb+1):
    p = f"{SP}/{prefix}_batch_{b}_out.json"
    if not os.path.exists(p): missing.append(b); continue
    try:
        for r in json.load(open(p)): keyed[r["gid"]] = r
    except Exception as e: print("parse", b, e); missing.append(b)
def norm(c): return "med" if (c or "").lower().startswith("med") else (c or "low").lower()
final = []
for gid, r in keyed.items():
    q = sel.get(gid)
    if not q: continue
    ans = (r.get("answer") or "").upper()
    if ans == "HELD" or ans not in "ABCDE": continue
    final.append({"gid": gid, "exam": "BPSC TRE", "edition": q["edition"],
                  "concept": dim_of(q["stem"], q.get("dim") or q.get("dimhint","")),
                  "stem": q["stem"], "options": {"A": q["A"],"B": q["B"],"C": q["C"],"D":"More than one of the above","E":"None of the above"},
                  "answer": ans, "confidence": norm(r.get("confidence","low")), "sources": r.get("sources",[]), "note": r.get("note","")})
print("missing:", missing or "none", "| keyed:", len(keyed), "| non-HELD:", len(final))
print("conf", dict(Counter(r["confidence"] for r in final)), "| dims", dict(Counter(r["concept"] for r in final)))
json.dump(final, open(f"{REPO_EXT}/{out_name}","w"), ensure_ascii=False, indent=1)
print("high+med:", sum(1 for r in final if r["confidence"] in ("high","med")), "->", out_name)
