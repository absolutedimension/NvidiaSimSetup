#!/usr/bin/env python3
"""
Compose Episode 1 — "AI is the Universal Mind: Attention".
Mode A (timed story slides + reactive circuit_mind shader + per-scene narration).

Runs on EC2 (needs GPU for shader + ffmpeg). Reuses the Video Creator backend.
Output: /home/ubuntu/youtube_series/ep01_attention.mp4
"""
import os, sys, asyncio, subprocess
sys.path.insert(0, "/home/ubuntu/video-creator-backend")
from services.slide_service import render_slide
from services.shader_service import render_shader_video
import edge_tts

VOICE  = "en-IN-PrabhatNeural"     # Indian-English MALE (host = Deepak); swap freely
RATE   = "-4%"                      # slightly slower — contemplative explainer
SHADER = "circuit_mind"
W, H, FPS = 1920, 1080, 30
GAP = 0.45                          # silence between scenes (breathing room)
WORK = "/home/ubuntu/youtube_series/ep01_build"
OUTDIR = "/home/ubuntu/youtube_series"
OUT  = os.path.join(OUTDIR, "ep01_attention.mp4")
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

# (id, narration_for_TTS, slide_kwargs)
SCENES = [
    ("s01",
     "Here is a question I could not stop thinking about. "
     "When you read a sentence, how do you know which words matter? "
     "Take this one. The animal did not cross the street, because it was too tired. "
     "What does the word it point to? "
     "You knew instantly. The animal. Not the street. "
     "Nobody ever taught you that rule. So how did you know? "
     "And here is the stranger part. A machine now knows it too.",
     dict(title='Which word does "it" mean?',
          body='"The animal didn’t cross the street because it was too tired."',
          layout="center", accent_color="blue")),

    ("s02",
     "This one idea, figuring out which words should pay attention to which other words, "
     "is the breakthrough behind almost every AI you have heard of. "
     "Chat G P T. Claude. The whole modern wave of intelligence. "
     "In twenty seventeen, a research paper gave the idea a name. "
     "The title was almost arrogant. Attention is all you need. "
     "And it turned out, they were right.",
     dict(title="Attention Is All You Need", subtitle="2017",
          layout="center", accent_color="blue")),

    ("s03",
     "But before we get to the machine, let me show you something about you. "
     "Imagine a crowded party. A hundred conversations at once. A wall of noise. "
     "And then, across the room, someone says your name. "
     "Instantly, that one voice cuts through everything. "
     "You did not turn up the volume on your name. "
     "You turned down everything else. "
     "That is attention.",
     dict(title="The Cocktail Party", layout="center", accent_color="purple")),

    ("s04",
     "You are doing it right now. "
     "Out of everything hitting your eyes and your ears in this moment, you chose this. "
     "The screen. My voice. "
     "Everything else faded into the background, until I just pointed at it. "
     "Your mind is a spotlight. "
     "And it is always, quietly, choosing what to ignore.",
     dict(title="A spotlight that chooses what to ignore",
          layout="center", accent_color="purple")),

    ("s05",
     "So here is the problem the machine had to solve. "
     "Give it a sentence. To understand any single word, "
     "it has to know which other words give that word its meaning. "
     "In, it was too tired, the word it has to look back and find, animal. "
     "But a machine has no eyes. So how does a machine look?",
     dict(title='How does a machine "look back"?', body="it  →  ?",
          layout="center", accent_color="blue")),

    ("s06",
     "Here is the trick, and it is beautiful. "
     "Every word gets to score every other word. "
     "A number, for how much it should listen to each one. "
     "High score, pay close attention. Low score, ignore. "
     "So it looks across the sentence. It scores animal high. It scores street low. "
     "And it locks on. "
     "The machine is not reading left to right. "
     "Every word is weighing every other word, all at once.",
     dict(title="Every word scores every other word",
          layout="center", accent_color="green")),

    ("s07",
     "And the way it scores is almost human. "
     "Each word quietly asks a question. What am I looking for? "
     "That is called the query. "
     "Every other word answers back. Here is what I am. "
     "That is called the key. "
     "When a question meets a matching answer, attention fires. "
     "It asks, who am I standing for? "
     "Animal answers, a thing that can be tired. "
     "Match. The spotlight snaps into place.",
     dict(title="Query · Key · Value",
          bullet_points=["Query  —  what I'm looking for",
                         "Key  —  what I am",
                         "Value  —  what I give"],
          layout="bullets", accent_color="amber")),

    ("s08",
     "Now multiply this. "
     "Not one sentence. Billions. "
     "Not one spotlight. Millions, running side by side, layer upon layer. "
     "A word attends to words. Those patterns attend to other patterns. "
     "Meaning building on meaning. "
     "Stack it high enough, and something new appears. "
     "The machine begins to seem like it understands. "
     "And all of it, every single layer, is just this one move, repeated. "
     "Deciding what to attend to. Deciding what to ignore.",
     dict(title="One move, repeated billions of times",
          layout="center", accent_color="green")),

    ("s09",
     "Now sit with what just happened. "
     "We were trying to build a better translator. A smarter autocomplete. "
     "And to do it, we had to teach a machine to focus. "
     "To choose what matters, and throw the rest away. "
     "And the moment we did, we had built a mirror. "
     "For the first time, we could see attention itself. Measure it. "
     "Watch a mind decide what to ignore. "
     "We did not just make a tool. "
     "We caught a glimpse of the machinery running quietly inside us.",
     dict(title="We built a tool. We got a mirror.",
          layout="center", accent_color="purple")),

    ("s10",
     "We tend to think intelligence means knowing more. Holding everything. "
     "But the machine learned the opposite lesson. "
     "The same one your mind learned long ago. "
     "So here is what I want you to carry out of this. "
     "Intelligence is not knowing everything. It is knowing what to ignore. "
     "This was the first faculty. Attention. "
     "In this series, we are going to rebuild the whole mind, one piece at a time. "
     "I will see you in the next one.",
     dict(title="Intelligence isn't knowing everything.\nIt's knowing what to ignore.",
          subtitle="AI is the Universal Mind  ·  Ep.1 — Attention",
          layout="center", accent_color="purple")),
]


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


async def tts(text, out_mp3):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(out_mp3)


def make_silence(path, seconds):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=r=24000:cl=mono", "-t", str(seconds),
                    "-q:a", "9", path], capture_output=True)


# 1. per-scene voiceover + measured durations -----------------------------
print(">> generating per-scene voiceover…")
scene_audio, windows, t = [], [], 0.0
sil = os.path.join(WORK, "gap.mp3"); make_silence(sil, GAP)
concat_list = os.path.join(WORK, "concat.txt")
with open(concat_list, "w") as cf:
    for sid, narr, _ in SCENES:
        mp3 = os.path.join(WORK, f"{sid}.mp3")
        asyncio.run(tts(narr, mp3))
        d = dur(mp3)
        windows.append((sid, t, t + d + GAP))     # slide visible through its scene + gap
        t += d + GAP
        cf.write(f"file '{mp3}'\n")
        cf.write(f"file '{sil}'\n")
        print(f"   {sid}: {d:5.1f}s  -> window {windows[-1][1]:.1f}-{windows[-1][2]:.1f}")
TOTAL = t
NARR = os.path.join(WORK, "narration.mp3")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c", "copy", NARR], capture_output=True)
print(f">> total narration = {TOTAL:.1f}s")

# 2. transparent story slides ---------------------------------------------
print(">> rendering slides…")
slide_paths = []
for (sid, _, kw) in SCENES:
    p = os.path.join(WORK, f"slide_{sid}.png")
    render_slide(transparent=True, output_path=p, **kw)
    slide_paths.append(p)

# 3. full-length reactive shader background --------------------------------
print(">> rendering circuit_mind shader background (reactive to narration)…")
bg = os.path.join(WORK, "bg.mp4")
render_shader_video(shader_name=SHADER, audio_path=NARR, output_path=bg,
                    duration=TOTAL, fps=FPS, width=W, height=H)

# 4. composite: shader bg + timed slide overlays + narration ---------------
print(">> compositing…")
inputs = ["-i", bg]
for p in slide_paths:
    inputs += ["-loop", "1", "-t", f"{TOTAL}", "-i", p]
inputs += ["-i", NARR]

fc, last = [], "0:v"
for i, (sid, s, e) in enumerate(windows):
    idx = i + 1
    fin, fout = s, max(s, e - 0.4)
    fc.append(f"[{idx}:v]scale={W}:{H},format=rgba,"
              f"fade=t=in:st={s:.2f}:d=0.4:alpha=1,"
              f"fade=t=out:st={fout:.2f}:d=0.4:alpha=1[sl{i}]")
    out = f"v{i}"
    fc.append(f"[{last}][sl{i}]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[{out}]")
    last = out
filtergraph = ";".join(fc)
aidx = len(slide_paths) + 1

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filtergraph,
    "-map", f"[{last}]", "-map", f"{aidx}:a",
    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERROR:\n", r.stderr[-3000:]); sys.exit(1)

print(f"\n✅ DONE: {OUT}  ({dur(OUT):.1f}s)")
