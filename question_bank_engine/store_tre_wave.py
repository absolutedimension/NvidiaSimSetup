#!/usr/bin/env python3
"""Store wave-1 more-TRE keyed questions into the live bank (exam=BPSC TRE, General Studies),
tagged with a GS dimension concept. High+med confidence only."""
import sys, os, json, re
sys.path.insert(0, os.path.expanduser("~/question_bank_engine"))
from qbank import storage, validator
from qbank.models import Question, content_hash

# --- lightweight dimension classifier (same rules as classify_gs_social) ---
DIMS = {
    "GS: Polity": r"constitution|article \d|fundamental right|fundamental dut|parliament|lok sabha|rajya sabha|president of india|prime minister|governor|supreme court|high court|judiciary|amendment|election commission|panchayat|preamble|directive principle|citizenship|\bwrit\b|reorganisation commission|governor general|regulating act|government of india act|constituent assembly|schedule",
    "GS: History": r"dynasty|empire|emperor|sultan|mughal|maurya|gupta|ashoka|buddha|jain|harappa|indus valley|vedic|medieval|ancient|battle of|revolt|rebellion|freedom|independence|national movement|swaraj|satyagraha|quit india|non-cooperation|civil disobedience|gandhi|viceroy|british rule|east india company|partition|treaty of|chola|maratha|peshwa|congress|session|1857|champaran|home rule",
    "GS: Economics": r"\bgdp\b|inflation|fiscal|monetary|budget|\btax\b|\bgst\b|poverty|unemployment|five year plan|niti aayog|reserve bank|\brbi\b|economic|revenue|subsidy|\bexport|\bimport|per capita|national income|domestic product|banking|census|literacy rate|population",
    "GS: Geography": r"\briver|mountain|himalaya|plateau|monsoon|climate|\bsoil|\bcrop|mineral|\bocean|\blake|\bforest|national park|\bplain|\bdesert|\bdelta|tributary|glacier|rainfall|\bpeak|\bstrait|\bcanal|valley|\bcoast|tropic|volcano|earthquake|\bisland|waterfall|zone|jhum",
}
NONGS = {"Reasoning/Quant": r"^if \d|find the (value|missing|number)|next in the series|\bratio\b|simplif|average of|percentage|\* \d|\d+ \* \d+|compound interest|profit|\bcm\b|\bsquare",
         "GS: General Science": r"photosynthesis|\batom\b|molecule|\bcell\b|gravity|velocity|vitamin|enzyme|chromosome|\bdna\b|chemical|\bacid\b|electron|\bvoltage|\bmagnet|\blens\b|respiration|ecosystem|\bforce\b|oxygen|\bhormone|bacteria|\bvirus\b"}

def dim(stem):
    s = stem.lower()
    for d, p in NONGS.items():
        if re.search(p, s):
            return d
    sc = {d: len(re.findall(p, s)) for d, p in DIMS.items()}
    b = max(sc, key=sc.get)
    return b if sc[b] else "GS: Static GK / Current Affairs"

SP = "/tmp"
rows = [r for r in json.load(open(f"{SP}/tre_more_wave1_KEYED.json")) if r["confidence"] in ("high", "med")]
db = "data/qbank.sqlite"
store = storage.Store(db)
batch = []
for r in rows:
    o = r["options"]
    opts = [{"label": l, "text": str(o[l]).strip()} for l in "ABCDE" if o.get(l)]
    qid = f"bpsctre_w1_{r['gid']:04d}"
    batch.append(Question(id=qid, exam="BPSC TRE", subject="General Studies",
                          stem=r["stem"], qtype="MCQ_single", options=opts,
                          correct_answer=r["answer"], concept=dim(r["stem"]),
                          source=f"BPSC TRE {r['edition']} (cross-source keyed)",
                          year=2023, difficulty=3, hash=content_hash(r["stem"])))
validator.validate(batch, llm=None)
nver = sum(1 for q in batch if q.verified)
for q in batch:
    store.upsert(q)
print(f"stored {len(batch)}, verified {nver}")
from collections import Counter
c = Counter(q.concept for q in batch)
print("dimension tags:", dict(c))
# report new BPSC TRE total
n = store.con.execute("SELECT COUNT(*) FROM questions WHERE exam='BPSC TRE' AND verified=1 AND duplicate_of IS NULL").fetchone()[0]
print("BPSC TRE verified total now:", n)
