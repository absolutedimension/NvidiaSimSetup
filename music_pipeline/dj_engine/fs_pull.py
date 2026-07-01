#!/usr/bin/env python3
"""fs_pull.py — pull CC0 psychedelic loops from Freesound into element buckets.
Token via env FSKEY. Downloads HQ-mp3 previews (public CDN) + writes a manifest.
"""
import os, sys, json, time, urllib.parse, urllib.request, re

KEY=os.environ["FSKEY"]
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/ubuntu/dj_engine/goa-gil/fs_samples"
PER=int(sys.argv[2]) if len(sys.argv)>2 else 6

BUCKETS={
 "kick":   ["psytrance kick","psy kick drum"],
 "bass":   ["psytrance bass loop","psy rolling bass","psytrance bassline"],
 "acid":   ["303 acid loop","acid line loop","acid bass loop"],
 "lead":   ["psytrance lead loop","goa trance lead","acid arp loop","psytrance arp"],
 "drone":  ["psychedelic drone","dark atmosphere drone","psytrance atmosphere"],
 "hats":   ["psytrance hats loop","psytrance percussion loop","psy hihat loop"],
 "fx":     ["psytrance fx riser","uplifter riser","psy whoosh downlifter"],
 "chant":  ["om mantra chant","sanskrit chant","spiritual vocal chant"],
}

def api_search(q):
    p=urllib.parse.urlencode({
        "query":q, "filter":'license:"Creative Commons 0"',
        "fields":"id,name,license,duration,previews,tags,username",
        "page_size":12, "sort":"score", "token":KEY})
    url="https://freesound.org/apiv2/search/text/?"+p
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2)
    return {"results":[]}

def bpm_from_tags(tags):
    for t in tags:
        m=re.match(r"(\d{2,3})bpm$", t) or re.match(r"bpm(\d{2,3})$", t)
        if m:
            b=int(m.group(1))
            if 80<=b<=200: return b
    return None

def dl(url, path):
    try:
        urllib.request.urlretrieve(url, path); return True
    except Exception:
        try:
            urllib.request.urlretrieve(url+"?token="+KEY, path); return True
        except Exception: return False

manifest=[]
for bucket,queries in BUCKETS.items():
    d=f"{OUT}/{bucket}"; os.makedirs(d, exist_ok=True)
    seen=set(); got=0
    for q in queries:
        if got>=PER: break
        res=api_search(q)
        for r in res.get("results",[]):
            if got>=PER: break
            sid=r["id"]
            if sid in seen: continue
            seen.add(sid)
            dur=r.get("duration",0)
            if bucket in ("kick",) and dur>6: continue          # kicks: short
            if bucket in ("bass","acid","lead","hats") and not (1.0<=dur<=40): continue
            if bucket in ("drone","chant") and dur<3: continue
            prev=r.get("previews",{}).get("preview-hq-mp3")
            if not prev: continue
            fn=f"{d}/{bucket}_{sid}.mp3"
            if dl(prev, fn):
                bpm=bpm_from_tags(r.get("tags",[]))
                manifest.append({"bucket":bucket,"id":sid,"name":r["name"],
                    "dur":round(dur,1),"bpm":bpm,"tags":r.get("tags",[])[:8],"file":fn})
                got+=1
        time.sleep(0.4)
    print(f"[{bucket}] {got} files")

json.dump(manifest, open(f"{OUT}/manifest.json","w"), indent=1)
print("TOTAL", len(manifest), "-> ", OUT)
