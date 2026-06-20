#!/usr/bin/env python3
"""
Hindi build of Course 1 / Module 1 (Mode A). Same pipeline as compose_mod01.py but:
  - per-scene Hindi audio from mod01_hi_build/sNN.mp3 (edge-tts hi-IN-MadhurNeural)
  - Devanagari on-screen text rendered with Mukta (PIL raqm shaping)
  - tech terms kept in Latin (Unity, Quest, Meta XR SDK, APK, C#, ZenSpace, EnergyField...)

Usage (on EC2):
  python3 compose_mod01_hi.py --scene 4      # prototype one scene
  python3 compose_mod01_hi.py --scenes 2,3   # re-render some
  python3 compose_mod01_hi.py --finalize     # concat existing + music
  python3 compose_mod01_hi.py                # full build -> module01_hi_FINAL.mp4
"""
import os, sys, subprocess, argparse
sys.path.append('/home/ubuntu/video-creator-backend')
import services.slide_service as ss
# --- Devanagari fonts (Mukta; raqm shaping auto-on since PIL has libraqm) ---
ss.FONT_BOLD = "/home/ubuntu/.local/share/fonts/Mukta-ExtraBold.ttf"
ss.FONT_REG  = "/home/ubuntu/.local/share/fonts/Mukta-Bold.ttf"
from services.slide_service import render_slide
from services.shader_service import render_shader_video

BUILD = "/home/ubuntu/youtube_series/mod01_hi_build"
OUT   = "/home/ubuntu/youtube_series/mod01_hi_out"
SHADER = "circuit_mind"
MUSIC = "/home/ubuntu/welcome_voice/bg_ambient.mp3"
W, H, FPS = 1920, 1080, 30
PREFIX = "module01_hi"
os.makedirs(OUT, exist_ok=True)

SCENES = [
    dict(layout="center",  accent_color="blue",  title="आपका पहला VR सीन",
         subtitle="मॉड्यूल 1", body="आपके अपने Quest हेडसेट पर"),
    dict(layout="bullets", accent_color="blue",  title="प्रोजेक्ट  —  ZenSpace",
         bullet_points=["एक VR + MR मेडिटेशन रूम",
                        "शुरुआती-आसान, हर ज़रूरी कॉन्सेप्ट सिखाता है",
                        "मेरी असली ऐप EnergyField जैसा"]),
    dict(layout="bullets", accent_color="purple", title="आप कोड हाथ से नहीं लिखेंगे",
         bullet_points=["जो चाहिए वो आसान भाषा में बताइए",
                        "AI एजेंट C# कोड लिखता है",
                        "आप VR में टेस्ट करके सुधारते हैं"]),
    dict(layout="bullets", accent_color="blue",  title="11-मॉड्यूल का सफ़र",
         bullet_points=["1 · टूल्स + पहला रूम",
                        "2 · आपका AI कोडिंग पार्टनर",
                        "3–8 · हाथ, UI, ऑडियो, मूवमेंट, मल्टीप्लेयर",
                        "9 · Mixed Reality",
                        "10 · पॉलिश",
                        "11 · Meta के Store पर पब्लिश"]),
    dict(layout="center",  accent_color="purple", title="VR डेवलपमेंट लूप",
         body="Unity  ·  APK  ·  Quest  ·  टेस्ट  ·  दोहराएँ"),
    dict(layout="bullets", accent_color="blue",  title="VR सीन असल में क्या है",
         bullet_points=["कैमरा रिग — यानी आप, स्पेस में ट्रैक होते हुए",
                        "ज्योमेट्री — फर्श और दीवारें",
                        "मटीरियल — सतहें कैसी दिखती हैं",
                        "लाइट्स — गर्माहट, खालीपन नहीं"]),
    dict(layout="bullets", accent_color="amber", title="आज आप तीन चीज़ें इंस्टॉल करेंगे",
         bullet_points=["Unity 6  +  Android Build Support",
                        "Meta XR All-in-One SDK  (फ्री)",
                        "बिल्ड टारगेट Meta Quest पर सेट करें"]),
    dict(layout="bullets", accent_color="amber", title="रूम बनाइए",
         bullet_points=["गर्म लकड़ी का फर्श",
                        "हल्की क्रीम दीवारें",
                        "धूप + ऊपर से गर्म रोशनी",
                        "एक मेडिटेशन स्टोन"]),
    dict(layout="center",  accent_color="green", title="हेडसेट पहनिए",
         subtitle="ये आपने बनाया है",
         body="आप VR सीन देख नहीं रहे — आप उसके अंदर खड़े हैं"),
    dict(layout="bullets", accent_color="green", title="हर बग, हर फिक्स",
         bullet_points=["मैंने EnergyField बनाई — Meta alpha में लाइव",
                        "मैंने ये सारी errors खुद झेली हैं",
                        "आपको फिक्स मिलेंगे, सिर्फ आसान रास्ता नहीं"]),
    dict(layout="bullets", accent_color="blue",  title="इस मॉड्यूल का उपयोग कैसे करें",
         bullet_points=["यह वीडियो = नक्शा  (क्या + क्यों)",
                        "Lab Guide = रास्ता  (हर क्लिक)",
                        "एक बार देखिए, फिर गाइड के साथ बनाइए"]),
    dict(layout="center",  accent_color="green", title="आगे — आपका AI कोडिंग पार्टनर",
         subtitle="मॉड्यूल 2", body="Lab Guide खोलिए और शुरू करते हैं"),
]

def dur(p):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                        "-of","csv=p=0",p], capture_output=True, text=True)
    return float(r.stdout.strip())

def build_scene(i):
    n = i + 1
    audio = f"{BUILD}/s{n:02d}.mp3"
    d = dur(audio)
    slide = f"{OUT}/slide{n:02d}.png"
    bg    = f"{OUT}/bg{n:02d}.mp4"
    clip  = f"{OUT}/scene{n:02d}.mp4"
    render_slide(transparent=True, output_path=slide, **SCENES[i])
    render_shader_video(shader_name=SHADER, audio_path=audio, output_path=bg,
                        duration=d, fps=FPS, width=W, height=H)
    fo = max(d - 0.4, 0.1)
    fc = (f"[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1,"
          f"fade=out:st={fo:.2f}:d=0.4:alpha=1[s];"
          f"[0:v][s]overlay=0:0,format=yuv420p[v]")
    subprocess.run(["ffmpeg","-y","-i",bg,"-loop","1","-i",slide,"-i",audio,
                    "-filter_complex",fc,"-map","[v]","-map","2:a","-t",f"{d:.3f}",
                    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k",clip], check=True, capture_output=True)
    print(f"  scene{n:02d}: {d:5.1f}s  -> {clip}", flush=True)
    return clip, d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, default=0)
    ap.add_argument("--scenes", type=str, default="")
    ap.add_argument("--finalize", action="store_true")
    a = ap.parse_args()

    if a.scenes:
        for n in [int(x) for x in a.scenes.split(",") if x.strip()]:
            build_scene(n - 1)
        print(">> scenes done", flush=True); return
    if a.scene:
        build_scene(a.scene - 1); print(">> single scene done", flush=True); return

    clips, total = [], 0.0
    for i in range(len(SCENES)):
        if a.finalize:
            c = f"{OUT}/scene{i+1:02d}.mp4"; d = dur(c)
        else:
            c, d = build_scene(i)
        clips.append(c); total += d
    lst = f"{OUT}/concat.txt"
    with open(lst,"w") as f:
        for c in clips: f.write(f"file '{c}'\n")
    nomusic = f"{OUT}/{PREFIX}_nomusic.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                    "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k",nomusic], check=True, capture_output=True)
    final = f"{OUT}/{PREFIX}_FINAL.mp4"
    if os.path.exists(MUSIC):
        fo = max(total - 3, 1)
        mf = (f"[1:a]volume=0.06,afade=in:st=0:d=3,afade=out:st={fo:.2f}:d=3[m];"
              f"[0:a][m]amix=inputs=2:duration=first[a]")
        subprocess.run(["ffmpeg","-y","-i",nomusic,"-stream_loop","-1","-i",MUSIC,
                        "-filter_complex",mf,"-map","0:v","-map","[a]",
                        "-c:v","copy","-c:a","aac","-b:a","192k",final],
                       check=True, capture_output=True)
    else:
        os.replace(nomusic, final)
    print(f">> FINAL {total:.1f}s -> {final}", flush=True)

if __name__ == "__main__":
    main()
