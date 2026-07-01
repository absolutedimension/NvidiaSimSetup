#!/usr/bin/env python3
"""fs_pull_techno.py — pull CC0 hypnotic/dub-techno loops from Freesound into element
buckets for the Burmeister profile. Token via env FSKEY. HQ-mp3 previews + manifest.
"""
import os, sys, json, time, urllib.parse, urllib.request, re
KEY=os.environ["FSKEY"]
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/ubuntu/dj_engine/burmeister/fs_samples"
PER=int(sys.argv[2]) if len(sys.argv)>2 else 6

BUCKETS={
 "kick":  ["dub techno kick","deep techno kick","techno kick drum"],
 "bass":  ["dub techno bass loop","hypnotic techno bassline","rolling sub bass techno","deep techno bass loop"],
 "drone": ["dub techno chord","dub techno stab chord","hypnotic techno drone","deep techno pad"],
 "hats":  ["techno hihat loop","techno hats loop","minimal techno hats"],
 "stab":  ["modular bleep","minimal techno stab","dub techno blip","techno bleep loop"],
 "perc":  ["minimal techno percussion loop","techno rim shaker loop","techno perc loop"],
}

def api_search(q):
    p=urllib.parse.urlencode({"query":q,"filter":'license:"Creative Commons 0"',
        "fields":"id,name,license,duration,previews,tags,username","page_size":12,"sort":"score","token":KEY})
    for _ in range(3):
        try:
            with urllib.request.urlopen("https://freesound.org/apiv2/search/text/?"+p, timeout=30) as r:
                return json.load(r)
        except Exception: time.sleep(2)
    return {"results":[]}

def bpm_from_tags(tags):
    for t in tags:
        m=re.match(r"(\d{2,3})bpm$",t) or re.match(r"bpm(\d{2,3})$",t)
        if m and 80<=int(m.group(1))<=200: return int(m.group(1))
    return None

def dl(url,path):
    try: urllib.request.urlretrieve(url,path); return True
    except Exception:
        try: urllib.request.urlretrieve(url+"?token="+KEY,path); return True
        except Exception: return False

manifest=[]
for bucket,queries in BUCKETS.items():
    d=f"{OUT}/{bucket}"; os.makedirs(d,exist_ok=True); seen=set(); got=0
    for q in queries:
        if got>=PER: break
        for r in api_search(q).get("results",[]):
            if got>=PER: break
            sid=r["id"]
            if sid in seen: continue
            seen.add(sid); dur=r.get("duration",0)
            if bucket=="kick" and dur>6: continue
            if bucket in ("bass","hats","stab","perc") and not (0.8<=dur<=40): continue
            if bucket=="drone" and dur<2: continue
            prev=r.get("previews",{}).get("preview-hq-mp3")
            if not prev: continue
            if dl(prev,f"{d}/{bucket}_{sid}.mp3"):
                manifest.append({"bucket":bucket,"id":sid,"name":r["name"],"dur":round(dur,1),
                    "bpm":bpm_from_tags(r.get("tags",[])),"tags":r.get("tags",[])[:8],"file":f"{d}/{bucket}_{sid}.mp3"})
                got+=1
        time.sleep(0.4)
    print(f"[{bucket}] {got}")
json.dump(manifest,open(f"{OUT}/manifest.json","w"),indent=1)
print("TOTAL",len(manifest),"->",OUT)
