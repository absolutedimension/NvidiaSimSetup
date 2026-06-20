#!/usr/bin/env python3
"""
Per-scene F5-TTS voiceover for a course module script (the video-script-writer format).
Reads the YAML voice/speed + each scene's `narration: |` block, generates one MP3 per
scene (sNN.mp3) + a concatenated full preview, into <build_dir>.

Usage (on EC2):
  python3 gen_course_audio.py <module_script.md> <build_dir>
Example:
  python3 gen_course_audio.py agentic_module_01.md /home/ubuntu/agentic_build/m01
"""
import sys, os, re, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.f5tts_service import generate_speech

def parse(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r'voice:\s*\{\s*name:\s*([\w]+)\s*,\s*speed:\s*([\d.]+)', text)
    voice = m.group(1) if m else "male_confident"
    speed = float(m.group(2)) if m else 0.78
    scenes, cur, in_narr, narr = [], None, False, []
    for line in text.splitlines():
        if line.startswith('### '):
            if cur and narr: scenes.append((cur, " ".join(narr).strip()))
            cur, in_narr, narr = line[4:].strip(), False, []
        elif re.match(r'\s*narration:\s*\|', line):
            in_narr, narr = True, []
        elif in_narr:
            # narration block = indented lines; a non-indented key ends it
            if line.strip() and not line.startswith(('  ', '\t')):
                in_narr = False
            elif line.strip():
                narr.append(line.strip())
    if cur and narr: scenes.append((cur, " ".join(narr).strip()))
    return voice, speed, scenes

def main():
    script, build = sys.argv[1], sys.argv[2]
    os.makedirs(build, exist_ok=True)
    voice, speed, scenes = parse(script)
    print(f">> {os.path.basename(script)}: voice={voice} speed={speed} scenes={len(scenes)}")
    mp3s = []
    for i, (sid, narr) in enumerate(scenes, 1):
        wav = f"{build}/s{i:02d}.wav"; mp3 = f"{build}/s{i:02d}.mp3"
        print(f"   [{i:02d}/{len(scenes)}] {sid}  ({len(narr)} chars)")
        generate_speech(narr, tone=voice, speed=speed, output_path=wav)
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame", "-q:a", "2", mp3],
                       check=True, capture_output=True)
        mp3s.append(mp3)
    # full preview with 0.5s gaps
    listf = f"{build}/_concat.txt"
    sil = f"{build}/_sil.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "0.5", "-q:a", "9", sil], check=True, capture_output=True)
    with open(listf, "w") as f:
        for m in mp3s:
            f.write(f"file '{os.path.abspath(m)}'\n")
            f.write(f"file '{os.path.abspath(sil)}'\n")
    full = f"{build}/_full_preview.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-codec:a", "libmp3lame", "-q:a", "2", full], check=True, capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", full], capture_output=True, text=True).stdout.strip()
    print(f">> DONE. {len(mp3s)} scenes. Full preview: {full}  (~{float(dur):.0f}s)")

if __name__ == "__main__":
    main()
