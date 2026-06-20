#!/usr/bin/env python3
"""
GENERIC module compositor (Mode A). Parses on_screen blocks straight from a
production-video script .md, then renders per-scene transparent cards over the
audio-reactive shader, timed to frozen per-scene audio, scene-by-scene -> concat.

Works for any module + either language. English on-screen text comes from the
script; Hindi comes from --onscreen-json (Devanagari + Mukta font override).

Usage (on EC2):
  # English
  python3 compose_module.py --script mod02_script.md --audio-dir mod02_build \
      --out mod02_out --prefix module02
  # Hindi
  python3 compose_module.py --script mod02_script.md --audio-dir mod02_hi_build \
      --out mod02_hi_out --prefix module02_hi --onscreen-json mod02_hi_onscreen.json \
      --font-bold /home/ubuntu/.local/share/fonts/Mukta-ExtraBold.ttf \
      --font-reg  /home/ubuntu/.local/share/fonts/Mukta-Bold.ttf
  # flags: --scene N | --scenes 1,2 | --finalize
"""
import os, sys, re, json, argparse, subprocess
sys.path.append('/home/ubuntu/video-creator-backend')

W, H, FPS = 1920, 1080, 30
MUSIC = "/home/ubuntu/welcome_voice/bg_ambient.mp3"
ACCENTS = {1:"blue",2:"blue",3:"purple",4:"blue",5:"purple",6:"blue",
           7:"amber",8:"amber",9:"green",10:"green",11:"blue",12:"green"}
LAYOUT_MAP = {"diagram":"center", "split":"bullets", "left":"left",
              "center":"center", "bullets":"bullets"}

def parse_frontmatter(txt):
    m = re.search(r'background_shader:\s*(\S+)', txt)
    return (m.group(1) if m else "circuit_mind")

def _field(block, name):
    m = re.search(rf'(?m)^\s*{name}:\s*(.+?)\s*$', block)
    return m.group(1).strip() if m else ""

def parse_scenes(path):
    """Return ordered list of (scene_id, on_screen dict)."""
    txt = open(path).read()
    blocks = re.split(r'(?m)^### (scene_\d+_\w+)\s*$', txt)
    scenes = []
    for i in range(1, len(blocks), 2):
        sid, body = blocks[i], blocks[i+1]
        m = re.search(r'(?ms)^on_screen:\s*\n(.*?)(?=^\w+:|\Z)', body)
        os_block = m.group(1) if m else ""
        bl = re.search(r'(?s)bullets:\s*(\[.*?\])', os_block)
        bullets = json.loads(bl.group(1)) if bl else None
        scenes.append((sid, dict(
            title=_field(os_block, "title"),
            subtitle=_field(os_block, "subtitle"),
            body=_field(os_block, "body"),
            layout=LAYOUT_MAP.get(_field(os_block, "layout") or "center", "center"),
            bullet_points=bullets,
        )))
    return scenes

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                        "-of","csv=p=0",p], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--onscreen-json", default="")
    ap.add_argument("--font-bold", default="")
    ap.add_argument("--font-reg", default="")
    ap.add_argument("--scene", type=int, default=0)
    ap.add_argument("--scenes", type=str, default="")
    ap.add_argument("--finalize", action="store_true")
    a = ap.parse_args()

    import services.slide_service as ss
    if a.font_bold: ss.FONT_BOLD = a.font_bold
    if a.font_reg:  ss.FONT_REG  = a.font_reg
    from services.slide_service import render_slide
    from services.shader_service import render_shader_video

    txt = open(a.script).read()
    shader = parse_frontmatter(txt)
    scenes = parse_scenes(a.script)
    # Hindi (or any) on-screen override keyed by scene_id
    if a.onscreen_json:
        ov = json.load(open(a.onscreen_json))
        for idx,(sid,d) in enumerate(scenes):
            if sid in ov:
                d.update({k:v for k,v in ov[sid].items() if v is not None})
    os.makedirs(a.out, exist_ok=True)

    def build_scene(i):
        n = i + 1
        sid, d = scenes[i]
        audio = f"{a.audio_dir}/s{n:02d}.mp3"
        sec = dur(audio)
        kw = dict(layout=d["layout"], accent_color=ACCENTS.get(n,"blue"),
                  title=d["title"], subtitle=d.get("subtitle",""),
                  body=d.get("body",""), bullet_points=d.get("bullet_points"))
        slide = f"{a.out}/slide{n:02d}.png"; bg = f"{a.out}/bg{n:02d}.mp4"
        clip  = f"{a.out}/scene{n:02d}.mp4"
        render_slide(transparent=True, output_path=slide, **kw)
        render_shader_video(shader_name=shader, audio_path=audio, output_path=bg,
                            duration=sec, fps=FPS, width=W, height=H)
        fo = max(sec - 0.4, 0.1)
        fc = (f"[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1,"
              f"fade=out:st={fo:.2f}:d=0.4:alpha=1[s];"
              f"[0:v][s]overlay=0:0,format=yuv420p[v]")
        subprocess.run(["ffmpeg","-y","-i",bg,"-loop","1","-i",slide,"-i",audio,
                        "-filter_complex",fc,"-map","[v]","-map","2:a","-t",f"{sec:.3f}",
                        "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                        "-c:a","aac","-b:a","192k",clip], check=True, capture_output=True)
        print(f"  scene{n:02d}: {sec:5.1f}s  -> {clip}", flush=True)
        return clip, sec

    if a.scenes:
        for n in [int(x) for x in a.scenes.split(",") if x.strip()]: build_scene(n-1)
        print(">> scenes done", flush=True); return
    if a.scene:
        build_scene(a.scene-1); print(">> single done", flush=True); return

    clips, total = [], 0.0
    for i in range(len(scenes)):
        c, s = (f"{a.out}/scene{i+1:02d}.mp4", dur(f"{a.out}/scene{i+1:02d}.mp4")) if a.finalize else build_scene(i)
        clips.append(c); total += s
    lst = f"{a.out}/concat.txt"
    open(lst,"w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
    nomusic = f"{a.out}/{a.prefix}_nomusic.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k",nomusic], check=True, capture_output=True)
    final = f"{a.out}/{a.prefix}_FINAL.mp4"
    if os.path.exists(MUSIC):
        fo = max(total-3,1)
        mf = (f"[1:a]volume=0.06,afade=in:st=0:d=3,afade=out:st={fo:.2f}:d=3[m];"
              f"[0:a][m]amix=inputs=2:duration=first[aud]")
        subprocess.run(["ffmpeg","-y","-i",nomusic,"-stream_loop","-1","-i",MUSIC,
                        "-filter_complex",mf,"-map","0:v","-map","[aud]",
                        "-c:v","copy","-c:a","aac","-b:a","192k",final],
                       check=True, capture_output=True)
    else:
        os.replace(nomusic, final)
    print(f">> FINAL {total:.1f}s -> {final}", flush=True)

if __name__ == "__main__":
    main()
