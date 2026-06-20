#!/usr/bin/env python3
"""Fast standalone renderer for the neon-tunnel-lotus visualizer.
Reuses shader_service.analyze_audio for audio-reactive uniforms, but runs its own
render loop with a NumPy vertical flip (the stock service does a slow per-frame
Python row reversal — fine for 30s clips, far too slow for a 60-min/108k-frame render).
Video only; mux audio afterward with ffmpeg."""
import sys, os, argparse, subprocess, time
import numpy as np
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services import shader_service as ss

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--dur", type=float, default=12.0)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--w", type=int, default=1920)
ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--shader", default="/home/ubuntu/video-creator-backend/shaders/neon_tunnel_lotus.glsl")
a = ap.parse_args()

import moderngl
W, H, FPS = a.w, a.h, a.fps

frag = open(a.shader).read()
audio = ss.analyze_audio(a.audio, fps=FPS, duration=a.dur)
total = audio["total_frames"]
dur = audio["duration"]

ctx = moderngl.create_standalone_context(backend="egl")
vert = "#version 330\nin vec2 in_vert;\nvoid main(){ gl_Position = vec4(in_vert,0.0,1.0); }"
prog = ctx.program(vertex_shader=vert, fragment_shader=frag)
vbo = ctx.buffer(np.array([-1,-1, 1,-1, -1,1, 1,1], dtype="f4"))
vao = ctx.simple_vertex_array(prog, vbo, "in_vert")
fbo = ctx.framebuffer(color_attachments=[ctx.texture((W, H), 3)])

U = {}
for n in ["u_time","u_resolution","u_rms","u_bass","u_treble","u_onset"]:
    try: U[n] = prog[n]
    except KeyError: pass

os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
ff = subprocess.Popen(
    ["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
     "-i","pipe:0","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p", a.out],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

print(f"[viz] {total} frames @ {W}x{H} -> {a.out}", flush=True)
t0 = time.time()
rms, bass, treble, onset = audio["rms"], audio["bass"], audio["treble"], audio["onset"]
for f in range(total):
    if "u_time" in U: U["u_time"].value = f / FPS
    if "u_resolution" in U: U["u_resolution"].value = (float(W), float(H))
    if "u_rms" in U: U["u_rms"].value = float(rms[f])
    if "u_bass" in U: U["u_bass"].value = float(bass[f])
    if "u_treble" in U: U["u_treble"].value = float(treble[f])
    if "u_onset" in U: U["u_onset"].value = float(onset[f])
    fbo.use(); ctx.clear(0,0,0); vao.render(moderngl.TRIANGLE_STRIP)
    arr = np.frombuffer(fbo.color_attachments[0].read(), dtype=np.uint8).reshape(H, W, 3)
    ff.stdin.write(arr[::-1].tobytes())          # fast NumPy vertical flip
    if f % (FPS*60) == 0 and f:
        el = time.time()-t0
        print(f"[viz] {f}/{total} ({f*100//total}%)  {f/el:.1f} fps  ETA {(total-f)/(f/el)/60:.1f} min", flush=True)
ff.stdin.close(); ff.wait(); ctx.release()
print(f"[viz] DONE {a.out} in {(time.time()-t0)/60:.1f} min", flush=True)
