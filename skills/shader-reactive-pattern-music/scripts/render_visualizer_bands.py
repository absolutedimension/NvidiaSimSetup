#!/usr/bin/env python3
"""render_visualizer_bands.py — like render_visualizer.py but ALSO computes per-band
energies (u_bands[NB]) so shader regions can dance independently on different beats.
Each band gets a fast-attack / slow-release envelope so hits 'pop' and ring out.
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
ap.add_argument("--shader", required=True)
ap.add_argument("--crf", type=int, default=20)
ap.add_argument("--encoder", default="nvenc", choices=["x264","nvenc"])
ap.add_argument("--nbands", type=int, default=8)
ap.add_argument("--release", type=float, default=0.86, help="per-band decay (higher=longer ring-out)")
ap.add_argument("--bg", default=None, help="background image (melted behind the pattern)")
ap.add_argument("--seed", type=float, default=0.0, help="per-chapter flowering seed")
ap.add_argument("--tint", default="1,1,1", help="per-chapter color tint r,g,b")
ap.add_argument("--foldlo", type=float, default=6.0)
ap.add_argument("--foldhi", type=float, default=12.0)
a = ap.parse_args()

import moderngl, librosa
W, H, FPS, NB = a.w, a.h, a.fps, a.nbands
frag = open(a.shader).read()
audio = ss.analyze_audio(a.audio, fps=FPS, duration=a.dur)
total = audio["total_frames"]; dur = audio["duration"]

# --- per-band energies (the 'beat dance'): 8 log-spaced bands 40 Hz .. 15 kHz ---
print("[viz] analyzing bands...", flush=True)
y, sr = librosa.load(a.audio, sr=22050, mono=True, duration=dur)
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512)).astype(np.float32)
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
stft_t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=512)
vid_t = np.arange(total)/FPS
edges = np.logspace(np.log10(40), np.log10(15000), NB+1)
bands = np.zeros((NB, total), dtype=np.float32)
for i in range(NB):
    m = (freqs >= edges[i]) & (freqs < edges[i+1])
    e = S[m].mean(0) if m.any() else np.zeros(S.shape[1], np.float32)
    e = np.interp(vid_t, stft_t, e).astype(np.float32)
    pk = np.percentile(e, 95) or 1.0
    e = np.clip(e/pk, 0.0, 1.2)
    acc = 0.0                                   # fast attack / slow release -> hits pop and ring out
    for f in range(total):
        acc = e[f] if e[f] > acc else acc*a.release
        bands[i, f] = acc

ctx = moderngl.create_standalone_context(backend="egl")
vert = "#version 330\nin vec2 in_vert;\nvoid main(){ gl_Position = vec4(in_vert,0.0,1.0); }"
prog = ctx.program(vertex_shader=vert, fragment_shader=frag)
vbo = ctx.buffer(np.array([-1,-1, 1,-1, -1,1, 1,1], dtype="f4"))
vao = ctx.simple_vertex_array(prog, vbo, "in_vert")
fbo = ctx.framebuffer(color_attachments=[ctx.texture((W, H), 3)])

U = {}
for n in ["u_time","u_resolution","u_rms","u_bass","u_treble","u_onset","u_bands",
          "u_seed","u_tint","u_foldlo","u_foldn"]:
    try: U[n] = prog[n]
    except KeyError: pass
# per-chapter constants (set once)
if "u_seed"   in U: U["u_seed"].value   = float(a.seed)
if "u_tint"   in U: U["u_tint"].value   = tuple(float(x) for x in a.tint.split(","))
if "u_foldlo" in U: U["u_foldlo"].value = float(a.foldlo)
if "u_foldn"  in U: U["u_foldn"].value  = (a.foldhi - a.foldlo)/2.0 + 0.99

# optional background texture (melted behind the pattern by the shader)
bg_tex = None
if a.bg:
    from PIL import Image
    im = Image.open(a.bg).convert("RGB").resize((1536, 1024))
    bg_tex = ctx.texture(im.size, 3, im.tobytes())
    bg_tex.build_mipmaps(); bg_tex.repeat_x = True; bg_tex.repeat_y = True
    bg_tex.use(0)
    try: prog["u_bg"].value = 0
    except KeyError: pass

os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
if a.encoder == "nvenc":
    vcodec = ["-c:v","h264_nvenc","-preset","p5","-tune","hq","-rc","vbr","-cq",str(a.crf),"-b:v","0"]
else:
    vcodec = ["-c:v","libx264","-preset","veryfast","-crf",str(a.crf)]
ff = subprocess.Popen(
    ["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
     "-i","pipe:0"] + vcodec + ["-pix_fmt","yuv420p", a.out],
    stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

print(f"[viz] {total} frames @ {W}x{H}, {NB} bands -> {a.out}", flush=True)
t0 = time.time()
rms, bass, treble, onset = audio["rms"], audio["bass"], audio["treble"], audio["onset"]
for f in range(total):
    if "u_time" in U: U["u_time"].value = f / FPS
    if "u_resolution" in U: U["u_resolution"].value = (float(W), float(H))
    if "u_rms" in U: U["u_rms"].value = float(rms[f])
    if "u_bass" in U: U["u_bass"].value = float(bass[f])
    if "u_treble" in U: U["u_treble"].value = float(treble[f])
    if "u_onset" in U: U["u_onset"].value = float(onset[f])
    if "u_bands" in U: U["u_bands"].value = tuple(float(bands[i, f]) for i in range(NB))
    fbo.use(); ctx.clear(0,0,0); vao.render(moderngl.TRIANGLE_STRIP)
    arr = np.frombuffer(fbo.color_attachments[0].read(), dtype=np.uint8).reshape(H, W, 3)
    ff.stdin.write(arr[::-1].tobytes())
    if f % (FPS*60) == 0 and f:
        el = time.time()-t0
        print(f"[viz] {f}/{total} ({f*100//total}%)  {f/el:.1f} fps", flush=True)
ff.stdin.close(); ff.wait(); ctx.release()
print(f"[viz] DONE {a.out} in {(time.time()-t0)/60:.1f} min", flush=True)
