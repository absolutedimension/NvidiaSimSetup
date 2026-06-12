#!/usr/bin/env python3
"""Hindi kinetic captions (Mukta line-reveal). Caption TEXT comes from the approved Hindi
script (perfect spelling); whisper supplies only the TIMING.
Usage: python3 make_caps_fx_hi.py <audio.mp3> <scene_video.mp4> <out.mp4>"""
import os, sys, json, subprocess, glob, re

audio, vid, out = sys.argv[1], sys.argv[2], sys.argv[3]
SCRIPT="/home/ubuntu/youtube_series/ep01_hi_build/hindi_script.json"

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

idx=int(re.search(r's(\d+)', os.path.basename(audio)).group(1))      # sNN.mp3 -> N
hi_text=json.load(open(SCRIPT))[idx-1]["hi"]
sw=[w for w in re.split(r'\s+', hi_text.strip()) if w]               # accurate script words
M=len(sw)

# whisper: TIMING only
from faster_whisper import WhisperModel
m=WhisperModel("base",device="cpu",compute_type="int8")
segs,_=m.transcribe(audio,word_timestamps=True,language="hi")
wt=[float(w.start) for s in segs for w in (s.words or []) if w.word.strip()]
if not wt: wt=[0.0, max(0.5,dur(audio)-0.3)]
K=len(wt)
def time_at(j): return wt[min(K-1, round(j*K/max(M,1)))]

# split the SCRIPT into phrases (~4 words or danda/punct), timed from whisper
ph=[]; buf=[]; start_j=0
for j,w in enumerate(sw):
    if not buf: start_j=j
    buf.append(w)
    if len(buf)>=4 or w[-1] in ".?!,;।":
        ph.append({"text":" ".join(buf).rstrip(",;।"),"start":time_at(start_j)}); buf=[]
if buf: ph.append({"text":" ".join(buf),"start":time_at(start_j)})
# enforce monotonic starts
for i in range(1,len(ph)):
    if ph[i]["start"]<=ph[i-1]["start"]: ph[i]["start"]=ph[i-1]["start"]+0.4
json.dump(ph,open("/tmp/cap_phrases.json","w"),ensure_ascii=False)
print(f">> {len(ph)} phrases (script-text, whisper-timed)",flush=True)

D=dur(vid); env=dict(os.environ,SCENE_DUR=f"{D}")
subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent","--disable_caching",
                "-o","CAP","caption_fx_hi.py","Caps"],cwd="/home/ubuntu",env=env,capture_output=True,text=True)
movs=glob.glob("/home/ubuntu/media/videos/caption_fx_hi/**/CAP.mov",recursive=True)
if not movs: print("!! no caption mov"); sys.exit(1)
mov=movs[0]
cp=subprocess.run(["ffmpeg","-y","-i",vid,"-i",mov,"-filter_complex",
    "[1:v]scale=1920:1080[c];[0:v][c]overlay=0:0:format=auto[v]","-map","[v]","-map","0:a",
    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","copy","-shortest",out],capture_output=True,text=True)
if cp.returncode!=0: print("ERR\n",cp.stderr[-1200:]); sys.exit(1)
print(f"✅ {out}",flush=True)
