#!/usr/bin/env python3
import os, json, urllib.parse, urllib.request, time
KEY=os.environ["FSKEY"]; OUT="/home/ubuntu/dj_engine/burmeister/vocals/female2"; os.makedirs(OUT,exist_ok=True)
qs=["female singing phrase ah","indian female singing melody","female vocal melody ah",
    "female melisma vocal","female opera phrase ah","female vocal ah moving","female voice ah phrase",
    "female humming melody","indian classical female alap","female vocalise phrase"]
def api(q):
    p=urllib.parse.urlencode({"query":q,"filter":'license:"Creative Commons 0"',
        "fields":"id,name,duration,previews","page_size":12,"sort":"score","token":KEY})
    try: return json.load(urllib.request.urlopen("https://freesound.org/apiv2/search/text/?"+p,timeout=30))
    except Exception: return {"results":[]}
got=0
for q in qs:
    if got>=12: break
    for r in api(q).get("results",[]):
        if got>=12: break
        d=r.get("duration",0)
        if not (3<=d<=30): continue
        pv=r.get("previews",{}).get("preview-hq-mp3")
        if not pv: continue
        try:
            urllib.request.urlretrieve(pv, f"{OUT}/fm_{r['id']}.mp3"); print(round(d,1), r["name"][:48]); got+=1
        except Exception: pass
    time.sleep(0.3)
print("melodic female:", got)
