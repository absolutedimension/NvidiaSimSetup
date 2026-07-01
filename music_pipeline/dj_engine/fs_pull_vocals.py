#!/usr/bin/env python3
"""Pull CC0 Indian-style wordless vocals: female 'aaaa' + deep male 'aaa' drone."""
import os, sys, json, time, urllib.parse, urllib.request
KEY=os.environ["FSKEY"]
OUT="/home/ubuntu/dj_engine/burmeister/vocals"; os.makedirs(OUT,exist_ok=True)
PER=10
BUCKETS={
 "female":   ["indian female vocal","female alap","female aah vocal ethereal","raga female voice",
              "indian classical female voice","female vocalise ah","female voice ah drone"],
 "male_deep":["deep male vocal ah","male aah drone","throat singing","deep male chant","tibetan chant",
              "male vocalise deep","om male voice deep","baritone male ah"],
}
def api(q):
    p=urllib.parse.urlencode({"query":q,"filter":'license:"Creative Commons 0"',
      "fields":"id,name,license,duration,previews,tags","page_size":15,"sort":"score","token":KEY})
    for _ in range(3):
        try:
            with urllib.request.urlopen("https://freesound.org/apiv2/search/text/?"+p,timeout=30) as r:
                return json.load(r)
        except Exception: time.sleep(2)
    return {"results":[]}
def dl(u,p):
    try: urllib.request.urlretrieve(u,p); return True
    except Exception:
        try: urllib.request.urlretrieve(u+"?token="+KEY,p); return True
        except Exception: return False
man=[]
for b,qs in BUCKETS.items():
    d=f"{OUT}/{b}"; os.makedirs(d,exist_ok=True); seen=set(); got=0
    for q in qs:
        if got>=PER: break
        for r in api(q).get("results",[]):
            if got>=PER: break
            sid=r["id"]
            if sid in seen: continue
            seen.add(sid); dur=r.get("duration",0)
            if not (2.0<=dur<=45): continue
            prev=r.get("previews",{}).get("preview-hq-mp3")
            if not prev: continue
            if dl(prev,f"{d}/{b}_{sid}.mp3"):
                man.append({"bucket":b,"id":sid,"name":r["name"],"dur":round(dur,1),"file":f"{d}/{b}_{sid}.mp3"}); got+=1
        time.sleep(0.4)
    print(f"[{b}] {got}")
json.dump(man,open(f"{OUT}/manifest.json","w"),indent=1)
print("TOTAL",len(man),"->",OUT)
