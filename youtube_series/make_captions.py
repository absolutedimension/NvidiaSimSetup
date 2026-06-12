#!/usr/bin/env python3
"""
Word-synced elegant captions for the episodes.
Word timing via faster-whisper (word_timestamps) on our clean TTS audio -> builds an ASS
where each word APPEARS as it's spoken: current word = gold + glow + pop, already-spoken
words = white, upcoming words = hidden until spoken. Bottom text-safe zone.

Usage:
  python3 make_captions.py --video <in.mp4> --out <out.mp4> [--scene N]
  (N = preview a single scene over its clip; omit = whole episode, offsets applied)
"""
import re, os, sys, argparse, subprocess

GOLD="&H0050C8FF&"; OUT3="&H00120A04&"          # ASS colours are &HBBGGRR
_MODEL=None
def words_from_audio(audio):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL=WhisperModel("base", device="cpu", compute_type="int8")
    segs,_=_MODEL.transcribe(audio, word_timestamps=True, language="en")
    ws=[]
    for s in segs:
        for w in (s.words or []):
            t=w.word.strip()
            if t: ws.append({"t":t,"s":float(w.start),"d":max(0.06,float(w.end-w.start))})
    return ws

def dur(p):
    r=subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0
def at(t):
    h=int(t//3600); m=int((t%3600)//60); s=max(0.0,t)%60
    return f"{h}:{m:02d}:{s:05.2f}"

HEAD=("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
"[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
"Style: Cap,DejaVu Sans,80,&H00FFFFFF,&H000000FF,&H00120A04,&H00000000,-1,0,0,0,100,100,1,0,1,5,3,2,200,200,120,1\n\n"
"[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

def line_text(words, cur, lo, hi):
    parts=[]
    for j in range(lo,hi):
        w=words[j]["t"].replace("{","").replace("}","")
        if j<cur:    parts.append(w)
        elif j==cur: parts.append(f"{{\\c{GOLD}\\3c{OUT3}\\blur13\\bord7\\fscx134\\fscy134\\b1}}{w}{{\\r}}")
        else:        parts.append(f"{{\\alpha&HFF&}}{w}{{\\r}}")
    return " ".join(parts)

def build_ass(scene_words):
    ev=[]; L=4
    for off, ws in scene_words:
        for li in range(0,len(ws),L):
            hi=min(li+L,len(ws))
            for cur in range(li,hi):
                start=off+ws[cur]["s"]
                end=off+(ws[cur+1]["s"] if cur+1<hi else ws[cur]["s"]+ws[cur]["d"]+0.4)
                fade="\\fad(120,0)" if cur==li else ""
                ev.append(f"Dialogue: 0,{at(start)},{at(end)},Cap,,0,0,0,,{{{fade}}}{line_text(ws,cur,li,hi)}")
    return HEAD+"\n".join(ev)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--video",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--scene",type=int,default=0)
    ap.add_argument("--build",default="/home/ubuntu/youtube_series/ep01_build")
    ap.add_argument("--nscenes",type=int,default=10)
    a=ap.parse_args()
    offs=[]; acc=0.0
    for i in range(a.nscenes):
        offs.append(acc); acc+=dur(f"{a.build}/s{i+1:02d}.mp3")
    sw=[]
    for i in range(a.nscenes):
        if a.scene and (i+1)!=a.scene: continue
        ws=words_from_audio(f"{a.build}/s{i+1:02d}.mp3")
        off=0.0 if a.scene else offs[i]
        sw.append((off,ws)); print(f"  s{i+1:02d}: {len(ws)} words",flush=True)
    ass="/tmp/captions.ass"; open(ass,"w").write(build_ass(sw))
    print(">> burning captions",flush=True)
    r=subprocess.run(["ffmpeg","-y","-i",a.video,"-vf",f"ass={ass}","-c:v","libx264","-crf","20",
        "-pix_fmt","yuv420p","-c:a","copy",a.out],capture_output=True,text=True)
    if r.returncode!=0: print("FFMPEG ERR:\n",r.stderr[-1500:]); sys.exit(1)
    print(f"✅ {a.out}",flush=True)

if __name__=="__main__": main()
