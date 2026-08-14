import json, re
from collections import Counter
SP = "/private/tmp/claude-501/-Users-deepakkumarrai-Documents-01-Active-NvidiaSimSetup/0ecd1d51-816c-491a-83b6-1f3c0dac55ea/scratchpad"
rows = json.load(open(f"{SP}/gs_rows.json"))

# word-boundary keyword sets (ordered by priority for tie-breaks)
DIMS = {
    "Polity": r"constitution|article \d|fundamental right|fundamental dut|parliament|lok sabha|"
              r"rajya sabha|president of india|prime minister|governor|supreme court|high court|"
              r"judiciary|amendment|election commission|panchayat|preamble|directive principle|"
              r"attorney general|\bcag\b|vidhan sabha|chief minister|council of ministers|citizenship|"
              r"\bwrit\b|\bveto\b|reorganisation commission|governor general|regulating act|"
              r"government of india act|constituent assembly|fundamental|schedule",
    "History": r"dynasty|empire|emperor|sultan|mughal|maurya|gupta|ashoka|buddha|jain|harappa|"
               r"indus valley|vedic|medieval|ancient|battle of|revolt|rebellion|freedom|"
               r"independence|national movement|swaraj|satyagraha|quit india|non-cooperation|"
               r"civil disobedience|gandhi|viceroy|british rule|east india company|partition|"
               r"treaty of|chola|maratha|peshwa|congress|session|1857|revolutionary|reminiscence|"
               r"poverty and un-british|freedom fighter|kranti",
    "Economics": r"\bgdp\b|\bgnp\b|inflation|fiscal|monetary|budget|\btax\b|\bgst\b|poverty|"
                 r"unemployment|five year plan|planning commission|niti aayog|reserve bank|\brbi\b|"
                 r"repo rate|economic|revenue|subsidy|\bexport|\bimport|balance of payment|"
                 r"per capita|national income|domestic product|banking|sensex|stock exchange|"
                 r"disinvestment|\bfdi\b|cooperative|census|population growth",
    "Geography": r"\briver|mountain|himalaya|plateau|monsoon|climate|\bsoil|\bcrop|mineral|latitude|"
                 r"longitude|\bocean|\blake|\bforest|national park|wildlife|\bplain|\bdesert|\bdelta|"
                 r"tributary|glacier|rainfall|\bpeak|\bstrait|\bcanal|irrigation|biosphere|valley|"
                 r"\bcoast|tropic|equator|volcano|earthquake|\bisland|waterfall|distributar|"
                 r"sanctuary|hills|plateau|tiger reserve",
}
NONGS = {  # not GS-Social — the TRE reasoning/quant/science that leaked into subject=General Studies
    "Reasoning/Quant": r"^if \d|find the (value|missing|number)|next in the series|\bratio\b|"
                       r"simplif|average of|percentage|\* \d|which is the (odd|smallest|largest) number|"
                       r"\d+ \* \d+|compound interest|profit",
    "Science": r"photosynthesis|\batom\b|molecule|\bcell\b|gravity|velocity|vitamin|enzyme|"
               r"chromosome|\bdna\b|chemical reaction|\bacid\b|electron|proton|\bvoltage|\bmagnet|"
               r"\blens\b|compound|respiration|ecosystem|\bforce\b|metal extraction|oxygen|"
               r"\bhormone|bacteria|\bvirus\b|digestion|photoelectric|octane",
}

def classify(stem):
    s = stem.lower()
    # non-GS first (so reasoning/quant/science don't pollute GS-Social)
    for d, pat in NONGS.items():
        if re.search(pat, s):
            return d
    scores = {d: len(re.findall(pat, s)) for d, pat in DIMS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Static-GK/Current-Affairs"
    return best

out = Counter(); tagged = []
for r in rows:
    d = classify(r["stem"]); out[d] += 1
    tagged.append({**r, "dim": d})
json.dump(tagged, open(f"{SP}/gs_tagged2.json", "w"))
print("=== refined distribution (977) ===")
for d, n in out.most_common():
    print(f"  {d:26s} {n}")
social = sum(out[d] for d in ("Polity", "History", "Economics", "Geography"))
print(f"\n  GS-SOCIAL total (Pol+His+Eco+Geo): {social}")
print()
import random; random.seed(9)
by = {}
for t in tagged: by.setdefault(t["dim"], []).append(t)
for d in ("Polity", "History", "Economics", "Geography"):
    print(f"--- {d} ({len(by.get(d,[]))}) ---")
    for t in random.sample(by[d], min(3, len(by[d]))):
        print(f"   {t['stem'][:82]}")
