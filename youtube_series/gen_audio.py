#!/usr/bin/env python3
"""
Stage-1 audio generator for the staged video pipeline.
Parses an episode script (.md) → per-scene narration → per-scene MP3 + concatenated
full narration. Run on EC2 (edge-tts needs network). The per-scene MP3s are the FROZEN
timing source for the later visual render.

Usage: python3 gen_audio.py <script.md> <out_dir> [voice] [rate]
  e.g. python3 gen_audio.py EP02_learning_loop_script.md /home/ubuntu/youtube_series/ep02_build
"""
import os, sys, re, asyncio, subprocess
import edge_tts

SCRIPT = sys.argv[1]
OUT    = sys.argv[2]
VOICE  = sys.argv[3] if len(sys.argv) > 3 else "en-IN-PrabhatNeural"   # male Indian-English (Ep1 voice)
RATE   = sys.argv[4] if len(sys.argv) > 4 else "-4%"
GAP    = 0.45
os.makedirs(OUT, exist_ok=True)

def parse_scenes(path):
    """Return [(scene_id, narration_text), ...] in order."""
    txt = open(path).read()
    # split on scene headers
    blocks = re.split(r'(?m)^### (scene_\d+_\w+)\s*$', txt)
    scenes = []
    # blocks = [pre, id1, body1, id2, body2, ...]
    for i in range(1, len(blocks), 2):
        sid = blocks[i]; body = blocks[i+1]
        m = re.search(r'(?ms)^narration:\s*\|\s*\n(.*?)(?=^\w+:|\Z)', body)
        if not m:
            continue
        raw = m.group(1)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        narration = " ".join(lines)
        scenes.append((sid, narration))
    return scenes

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

async def tts(text, out): await edge_tts.Communicate(text, VOICE, rate=RATE).save(out)

def silence(path, secs):
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t",str(secs),
                    "-q:a","9",path], capture_output=True)

scenes = parse_scenes(SCRIPT)
print(f">> {len(scenes)} scenes parsed from {os.path.basename(SCRIPT)}", flush=True)
sil = os.path.join(OUT, "gap.mp3"); silence(sil, GAP)
concat = os.path.join(OUT, "concat.txt")
total = 0.0
with open(concat, "w") as cf:
    for i, (sid, narr) in enumerate(scenes, 1):
        mp3 = os.path.join(OUT, f"s{i:02d}.mp3")
        asyncio.run(tts(narr, mp3))
        d = dur(mp3); total += d + GAP
        cf.write(f"file '{mp3}'\nfile '{sil}'\n")
        print(f"   s{i:02d} ({sid}): {d:5.1f}s", flush=True)
full = os.path.join(OUT, "full_narration.mp3")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",full],
               capture_output=True)
print(f">> full narration = {total:.1f}s  -> {full}", flush=True)
