#!/usr/bin/env python3
"""
Render one course module video: transparent slides (from each scene's on_screen)
over the circuit_mind shader, timed to the pre-generated per-scene voice. Uses the
generic render_service assembler. Reliable across a batch — no Hallo presenter.

Usage (on EC2):
  python3 render_course_module.py <module_script.md> <audio_build_dir> <out.mp4>
"""
import sys, os, re, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.slide_service import render_slide
from services.render_service import render_video

ACCENT = "purple"
SHADER = "circuit_mind"
W, H, FPS = 1920, 1080, 30

def parse_scenes(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r'\n###\s+(scene_\w+)\s*\n', text)
    scenes = []
    for i in range(1, len(parts), 2):
        sid, body = parts[i].strip(), parts[i + 1]
        f, in_os = {}, False
        for line in body.splitlines():
            if re.match(r'\s*on_screen:\s*$', line):
                in_os = True; continue
            if in_os:
                if line.strip() and not line.startswith(('  ', '\t')):
                    break
                m = re.match(r'\s+(\w+):\s*(.*)', line)
                if m:
                    f[m.group(1)] = m.group(2).strip()
        scenes.append((sid, f))
    return scenes

def bullets(s):
    return re.findall(r'"([^"]*)"', s) or re.findall(r"'([^']*)'", s) or None

def dur_of(mp3):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", mp3], capture_output=True, text=True).stdout.strip()
    return float(out) if out else 8.0

def main():
    script, audio, out = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
    scenes = parse_scenes(script)
    sdir = os.path.join(audio, "_slides"); os.makedirs(sdir, exist_ok=True)
    proj_scenes = []
    for i, (sid, f) in enumerate(scenes, 1):
        layout = f.get("layout", "center")
        if layout not in ("center", "left", "split", "bullets", "screenshot"):
            layout = "center"
        bp = bullets(f.get("bullets", "")) if "bullets" in f else None
        if bp and layout == "center":
            layout = "bullets"
        slide = f"{sdir}/s{i:02d}.png"
        render_slide(
            title=f.get("title", "").strip('"'),
            body=f.get("body", "").strip('"'),
            subtitle=f.get("subtitle", "").strip('"'),
            bullet_points=bp, layout=layout, accent_color=ACCENT,
            transparent=True, output_path=slide)
        mp3 = f"{audio}/s{i:02d}.mp3"
        d = dur_of(mp3) + 0.4 if os.path.exists(mp3) else 8.0
        proj_scenes.append({"slide_path": slide, "voice_path": mp3 if os.path.exists(mp3) else "", "duration": d})
        print(f"   scene {i:02d} {sid:32s} layout={layout:8s} dur={d:.1f}s")
    music = "/home/ubuntu/welcome_voice/bg_ambient.mp3"
    project = {"scenes": proj_scenes, "background_shader": SHADER,
               "resolution": [W, H], "fps": FPS, "music_volume": 0.06}
    if os.path.exists(music):
        project["music_path"] = music
    print(f">> rendering {len(proj_scenes)} scenes -> {out}")
    render_video(project, out)
    print(f">> DONE -> {out}")

if __name__ == "__main__":
    main()
