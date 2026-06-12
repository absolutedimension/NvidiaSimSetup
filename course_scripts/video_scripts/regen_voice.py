import sys, os, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.f5tts_service import generate_speech

WORK = "/home/ubuntu/reel_build"
SPEED = 0.45
ATEMPO = 0.82      # extra clean slowdown (no pitch change)
GAP = 1.0
scenes = [
    ("s1", "You can build a real VR app for your Quest headset. Without writing a single line of code."),
    ("s2", "Never written C sharp? It doesn't matter. You describe what you want in plain English."),
    ("s3", "An AI coding agent, Claude Code, writes the script. You test it in VR. You iterate. That's how developers build in 2026."),
    ("s4", "I built a VR app called EnergyField. It's live in Meta's alpha program. I'll show you every step. Every bug. Every fix."),
    ("s5", "By the end, you ship to the Meta Store. And on day one, you're standing inside your own VR room."),
    ("s6", "Start building. Link in the bio."),
]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


sil = os.path.join(WORK, "gap.wav")
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(GAP), sil], capture_output=True)

parts = []
for sid, txt in scenes:
    w = os.path.join(WORK, f"voice_{sid}.wav")
    generate_speech(txt, tone="female_confident", speed=SPEED, output_path=w)
    # apply clean time-stretch (slows delivery, keeps pitch)
    tmp = w + ".st.wav"
    subprocess.run(["ffmpeg", "-y", "-i", w, "-filter:a", "atempo=%s" % ATEMPO, tmp],
                   capture_output=True)
    os.replace(tmp, w)
    print("DUR %s: %.2f" % (sid, dur(w)))
    parts.append(w)

clips = []
for i, w in enumerate(parts):
    clips.append(w)
    if i < len(parts) - 1:
        clips.append(sil)

ins, fc, labels = [], [], []
for i, c in enumerate(clips):
    ins += ["-i", c]
    fc.append("[%d:a]aresample=24000,aformat=channel_layouts=mono[a%d]" % (i, i))
    labels.append("[a%d]" % i)
fc.append("".join(labels) + "concat=n=%d:v=0:a=1[out]" % len(clips))
full = os.path.join(WORK, "full_voice.wav")
subprocess.run(["ffmpeg", "-y"] + ins + ["-filter_complex", ";".join(fc),
               "-map", "[out]", full], check=True, capture_output=True)
print("TOTAL %.2f" % dur(full))
