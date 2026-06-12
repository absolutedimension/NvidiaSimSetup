#!/usr/bin/env python3
"""Mix a focus bed UNDER a video's narration, with sidechain ducking so speech stays clear.
Usage: python3 focus_mix.py <video.mp4> <bed.wav> <out.mp4> [bed_db=-15]"""
import sys, subprocess
vid, bed, out = sys.argv[1], sys.argv[2], sys.argv[3]
bdb = sys.argv[4] if len(sys.argv)>4 else "-20"   # quieter base level
# lower threshold + higher ratio => bed ducks hard whenever the voice is present,
# fast attack so it gets out of the way instantly, gentle release so it breathes back in gaps
fc=(f"[1:a]volume={bdb}dB[bed];"
    f"[0:a]asplit=2[v0][key];"
    f"[bed][key]sidechaincompress=threshold=0.022:ratio=9:attack=5:release=320:makeup=1[duck];"
    f"[v0][duck]amix=inputs=2:duration=first:normalize=0[a]")
r=subprocess.run(["ffmpeg","-y","-i",vid,"-i",bed,"-filter_complex",fc,
    "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",out],
    capture_output=True,text=True)
print("✅ "+out if r.returncode==0 else "ERR\n"+r.stderr[-1200:])
