#!/usr/bin/env python3
"""
product_hero.py  —  turn product STILLS into ad SCENE CLIPS.

The ad style is built from product hero shots, not shaders/diagrams. This gives the
three motion+layout helpers the producer needs:

  ken_burns(img, dur, out, ...)   still -> smooth push/pan clip (cheap, on-brand motion)
  cutout(img, out)                isolate the product (rembg) onto transparent PNG
  compose_ad_scene(...)           per-scene: 9:16 bg motion + cutout + scrim + caption + audio

Conventions match the engine's reference scripts: ffmpeg on EC2, PIL/numpy, RGBA
overlays via alpha_composite (NOT ImageChops.add — engine §6 gotcha). Render
scene-by-scene then concat (engine §4); never one giant filtergraph.

Deps on EC2:  pip install --break-system-packages pillow numpy rembg  (ffmpeg in AMI)
"""
import os, subprocess, math

W9, H9 = 1080, 1920          # 9:16
W1, H1 = 1080, 1080          # 1:1
SAFE_TOP, SAFE_BOT = 0.12, 0.12   # platform UI eats top/bottom ~12%

def _run(cmd):
    subprocess.run(cmd, check=True)

# ---- 1. KEN-BURNS: still -> motion clip --------------------------------------
def ken_burns(img, dur, out, *, w=W9, h=H9, fps=30, zoom=1.12, direction="in"):
    """
    Smooth zoom/pan over a still. `direction`: in | out | left | right | up | down.
    Uses ffmpeg zoompan. Frame count = dur*fps. Scales source up first so zoompan
    has headroom (zoompan is finicky on small inputs).
    """
    frames = max(2, int(dur * fps))
    # zoom expression
    if direction == "in":
        z = f"zoom+{(zoom-1)/frames:.6f}"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif direction == "out":
        z = f"if(eq(on,0),{zoom},zoom-{(zoom-1)/frames:.6f})"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    else:
        z = f"{zoom}"  # constant zoom, pan instead
        pan = {"left":  ("(iw-iw/zoom)*(1-on/%d)"%frames, "ih/2-(ih/zoom/2)"),
               "right": ("(iw-iw/zoom)*(on/%d)"%frames,   "ih/2-(ih/zoom/2)"),
               "up":    ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/%d)"%frames),
               "down":  ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(on/%d)"%frames)}
        x, y = pan[direction]
    vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
          f"crop={w*2}:{h*2},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps}")
    _run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf,
          "-t", f"{dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), out])
    return out

# ---- 2. CUTOUT: isolate the product ------------------------------------------
def cutout(img, out):
    """Background-remove the product -> transparent PNG (rembg). For float-over-motion."""
    from rembg import remove
    from PIL import Image
    Image.open(img)  # validate
    with open(img, "rb") as f:
        data = remove(f.read())
    with open(out, "wb") as f:
        f.write(data)
    return out

# ---- 3. COMPOSE one ad scene clip --------------------------------------------
def compose_ad_scene(bg_clip, audio, out, *, caption_overlay=None, cutout_png=None,
                     w=W9, h=H9, scrim=0.28, presenter=None):
    """
    One scene = bg motion clip (already 9:16) + optional product cutout (Ken-Burns'd
    separately or static) + text-safe scrim + caption overlay (RGBA from
    kinetic_captions) + this scene's frozen audio (+ optional circular presenter PiP
    for UGC). Duration follows the audio (engine: audio drives timing).

    caption_overlay / cutout_png / presenter are RGBA mp4/png paths (or None).
    """
    inputs = ["-i", bg_clip]
    fc = []
    last = "0:v"
    # scrim: dark gradient bottom-third so captions are legible
    fc.append(f"[{last}]scale={w}:{h},setsar=1[bg]"); last = "bg"
    fc.append(f"color=c=black@{scrim}:s={w}x{int(h*0.42)}[scr0];"
              f"[scr0]format=rgba,fade=t=in:st=0:d=0.01:alpha=1[scr]")
    fc.append(f"[{last}][scr]overlay=0:{int(h*0.58)}[wscrim]"); last = "wscrim"
    idx = 1
    if cutout_png:
        inputs += ["-i", cutout_png]
        fc.append(f"[{idx}:v]scale=-1:{int(h*0.5)}[cut]")
        fc.append(f"[{last}][cut]overlay=(W-w)/2:{int(h*0.18)}[wcut]"); last = "wcut"; idx += 1
    if presenter:  # UGC circular PiP bottom area
        inputs += ["-i", presenter]
        d = int(w*0.34)
        fc.append(f"[{idx}:v]scale={d}:{d},format=rgba,"
                  f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(hypot(X-{d//2},Y-{d//2}),{d//2}),0,255)'[pp]")
        fc.append(f"[{last}][pp]overlay=W-w-40:H-h-{int(h*0.16)}[wpp]"); last = "wpp"; idx += 1
    if caption_overlay:
        inputs += ["-i", caption_overlay]
        fc.append(f"[{last}][{idx}:v]overlay=0:0[wcap]"); last = "wcap"; idx += 1
    fc.append(f"[{last}]format=yuv420p[v]")
    _run(["ffmpeg", "-y", *inputs, "-i", audio,
          "-filter_complex", ";".join(fc),
          "-map", "[v]", "-map", f"{idx}:a", "-shortest",
          "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-b:a", "192k", out])
    return out

# ---- concat scene clips + mix music bed (engine §5 audio recipe, music louder) -
def concat_and_music(scene_clips, music, out, *, music_db=-10):
    """Concat per-scene clips, then duck a music bed under the VO (sidechain)."""
    lst = "/tmp/ad_concat.txt"
    with open(lst, "w") as f:
        for c in scene_clips:
            f.write(f"file '{c}'\n")
    silent = "/tmp/ad_concat_v.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
          "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", silent])
    gain = 10 ** (music_db / 20.0)
    _run(["ffmpeg", "-y", "-i", silent, "-i", music,
          "-filter_complex",
          f"[1:a]volume={gain:.4f},afade=in:0:1,afade=out:st=999:d=2[m];"
          f"[0:a][m]sidechaincompress=threshold=0.03:ratio=8:attack=5:release=300[a]",
          "-map", "0:v", "-map", "[a]", "-shortest",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    return out

if __name__ == "__main__":
    # smoke: still -> 3s push-in clip
    import sys
    if len(sys.argv) >= 3:
        ken_burns(sys.argv[1], 3.0, sys.argv[2])
        print("wrote", sys.argv[2])
    else:
        print("usage: product_hero.py <still.png> <out.mp4>  (smoke-test ken_burns)")
