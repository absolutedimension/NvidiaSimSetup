#!/usr/bin/env python3
"""Phrase-level kinetic captions (Poppins line-reveal) over a scene clip.
Usage: python3 make_caps_fx.py <audio.mp3> <scene_video.mp4> <out.mp4>"""
import os, sys, json, subprocess, glob

audio, vid, out = sys.argv[1], sys.argv[2], sys.argv[3]

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

from faster_whisper import WhisperModel
m=WhisperModel("base",device="cpu",compute_type="int8")
segs,_=m.transcribe(audio,word_timestamps=True,language="en")
words=[{"t":w.word.strip(),"s":float(w.start),"e":float(w.end)} for s in segs for w in (s.words or []) if w.word.strip()]

# group into short phrases: break on punctuation or every 4 words
ph=[]; cur=[]
for w in words:
    cur.append(w)
    if len(cur)>=4 or w["t"][-1] in ".?!,;":
        ph.append({"text":" ".join(x["t"] for x in cur).rstrip(",;"),"start":cur[0]["s"],"end":cur[-1]["e"]}); cur=[]
if cur: ph.append({"text":" ".join(x["t"] for x in cur),"start":cur[0]["s"],"end":cur[-1]["e"]})
json.dump(ph,open("/tmp/cap_phrases.json","w"))
print(f">> {len(ph)} phrases",flush=True)

D=dur(vid)
env=dict(os.environ,SCENE_DUR=f"{D}")
subprocess.run(["python3","-m","manim","-r","1920,1080","--fps","30","--transparent","--disable_caching",
                "-o","CAP","caption_fx.py","Caps"],cwd="/home/ubuntu",env=env,capture_output=True,text=True)
movs=glob.glob("/home/ubuntu/media/videos/caption_fx/**/CAP.mov",recursive=True)
if not movs: print("!! no caption mov"); sys.exit(1)
mov=movs[0]
cp=subprocess.run(["ffmpeg","-y","-i",vid,"-i",mov,"-filter_complex",
    "[1:v]scale=1920:1080[c];[0:v][c]overlay=0:0:format=auto[v]","-map","[v]","-map","0:a",
    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-c:a","copy","-shortest",out],capture_output=True,text=True)
if cp.returncode!=0: print("ERR\n",cp.stderr[-1200:]); sys.exit(1)
print(f"✅ {out}",flush=True)
