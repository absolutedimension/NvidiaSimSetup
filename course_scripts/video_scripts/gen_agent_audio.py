#!/usr/bin/env python3
"""Generate per-scene + full narration for 'What is an AI Agent?' via edge-tts. Runs on EC2."""
import asyncio, subprocess, os, edge_tts

VOICE = "en-GB-SoniaNeural"     # clear modern British FEMALE narrator (podcast host); alt: en-US-AvaMultilingualNeural
RATE  = "-2%"
OUT   = "/home/ubuntu/agent_vid_build"
os.makedirs(OUT, exist_ok=True)

SCENES = [
    ("s01", "What is an A.I. agent? Ask five different people, and you'll get five different answers — and every one of them is true."),
    ("s02", "Ask a six year old. An agent is a helper robot. You give it a job — find my teddy — and it takes one little step at a time until the job is done."),
    ("s03", "Ask a school student. It's an A.I. you give a goal, and it uses tools to reach it. A chatbot tells you the recipe. An agent cooks the meal."),
    ("s04", "Ask a college student. It's a language model running in a loop. It picks a tool, sees what happened, and decides the next step — until the goal is met. You give the goal; it finds the path."),
    ("s05", "Ask a graduate. It's a policy that turns observations into actions. The model is the brain, the tools are its hands, memory is its notebook, and planning ties it all together."),
    ("s06", "Ask an expert. It's an autonomous, goal directed system — but its will is borrowed from the prompt. It performs the shape of wanting, without ever feeling it."),
    ("s07", "Five answers, one skeleton. A goal goes in. It acts in a loop, using tools. It stops when the job is done. That's an agent — and in Module One, you'll build your own."),
]

async def gen(tag, text):
    path = f"{OUT}/{tag}.mp3"
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
    return path

async def main():
    paths = []
    for tag, text in SCENES:
        paths.append(await gen(tag, text))
        print("ok", tag)
    # concat with 0.45s gaps into a full preview
    sil = f"{OUT}/sil.mp3"
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t","0.45",sil],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    listf = f"{OUT}/list.txt"
    with open(listf,"w") as f:
        for i,p in enumerate(paths):
            f.write(f"file '{p}'\n")
            if i < len(paths)-1: f.write(f"file '{sil}'\n")
    full = f"{OUT}/full_preview.mp3"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",listf,"-c","copy",full],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of",
                          "default=nw=1:nk=1",full], capture_output=True, text=True).stdout.strip()
    print(f"FULL -> {full}  ({float(dur):.1f}s)")

asyncio.run(main())
