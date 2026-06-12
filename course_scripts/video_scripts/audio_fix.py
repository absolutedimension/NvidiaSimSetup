"""
Fix the reel audio WITHOUT changing timing (so the lip-sync stays in sync):
  1. mute the F5-TTS 'ghost' tails at each scene boundary (length-preserving)
  2. add an audible, content-selected background music bed with sidechain ducking
  3. mux the new audio into the EXISTING approved video (video copied, no re-render)

Run: /home/ubuntu/audio_pipeline/venv/bin/python /home/ubuntu/reel_build/audio_fix.py
"""
import os, subprocess

WORK = "/home/ubuntu/reel_build"
VIDEO_IN = "/home/ubuntu/module01_reel.mp4"
FULL_VOICE = os.path.join(WORK, "full_voice.wav")
OUT = "/home/ubuntu/module01_reel_music.mp4"
GAP = 1.0
SCENES = ["s1", "s2", "s3", "s4", "s5", "s6"]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0


# ---- content-aware music selection (the "system decides" hook) -------------
MUSIC_LIBRARY = {
    # mood -> track. 'energetic' now uses the ACE-Step content-generated instrumental.
    "energetic": "/home/ubuntu/reel_build/ace_music.wav",
    "calm":      "/home/ubuntu/welcome_voice/bg_ambient.mp3",
    "tech":      "/home/ubuntu/reel_build/ace_music.wav",
}


def detect_mood(text):
    t = text.lower()
    energetic = ["build", "ship", "start", "now", "you can", "let's", "launch", "fast"]
    calm = ["breathe", "relax", "gentle", "calm", "slow", "meditat"]
    e = sum(t.count(w) for w in energetic)
    c = sum(t.count(w) for w in calm)
    return "calm" if c > e else "energetic"


def select_music(content_text):
    mood = detect_mood(content_text)
    track = MUSIC_LIBRARY.get(mood, MUSIC_LIBRARY["energetic"])
    print(f"   music: mood='{mood}' -> {os.path.basename(track)}")
    return track, mood


# ---- boundary mute windows (length-preserving) ----------------------------
durs = [dur(os.path.join(WORK, f"voice_{s}.wav")) for s in SCENES]
mutes = [(0.0, 0.06)]           # tiny head guard
t = 0.0
for i, d in enumerate(durs):
    clip_end = t + d
    if i < len(durs) - 1:
        gap_end = clip_end + GAP
        # mute trailing ghost of this clip + the gap + leading ghost of next
        mutes.append((clip_end - 0.15, gap_end + 0.10))
        t = gap_end
    else:
        t = clip_end
TOTAL = dur(FULL_VOICE)
print(f"   total={TOTAL:.2f}s  mute_windows={len(mutes)}")

# voice clean: chain volume=0 over each mute window
vfilters = ",".join(f"volume=0:enable='between(t,{a:.3f},{b:.3f})'" for a, b in mutes)
voice_clean = os.path.join(WORK, "voice_clean.wav")
subprocess.run(["ffmpeg", "-y", "-i", FULL_VOICE, "-af", vfilters, voice_clean],
               check=True, capture_output=True)

# ---- pick music + build ducked mix ----------------------------------------
content_text = " ".join(open(os.path.join(WORK, "build4.log")).read().splitlines()[:1]) \
    if False else "You can build a real VR app. Without writing code. Start building."
music, mood = select_music(content_text)

final_audio = os.path.join(WORK, "final_audio.wav")
fc = (
    "[0:a]asplit=2[v1][v2];"
    f"[1:a]atrim=0:{TOTAL:.2f},asetpts=N/SR/TB,volume=0.32,"
    "afade=t=in:st=0:d=2,afade=t=out:st=%.2f:d=2[mus];" % max(0, TOTAL - 2) +
    # duck music under the voice; music sits up in the pauses
    "[mus][v2]sidechaincompress=threshold=0.03:ratio=8:attack=12:release=350:makeup=1.5[mducked];"
    "[v1][mducked]amix=inputs=2:duration=first:normalize=0[a]"
)
subprocess.run([
    "ffmpeg", "-y", "-i", voice_clean, "-stream_loop", "-1", "-i", music,
    "-filter_complex", fc, "-map", "[a]", final_audio
], check=True, capture_output=True)

# ---- mux new audio into existing approved video (no re-render) -------------
r = subprocess.run([
    "ffmpeg", "-y", "-i", VIDEO_IN, "-i", final_audio,
    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k", "-shortest", OUT
], capture_output=True, text=True)
if r.returncode != 0:
    print("MUX ERROR:\n", r.stderr[-1500:])
    raise SystemExit(1)
print(f"DONE -> {OUT}  ({dur(OUT):.1f}s, {os.path.getsize(OUT)//1024//1024} MB)")
