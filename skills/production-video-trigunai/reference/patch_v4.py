"""
Patch render_animated_video.py -> render_v4.py:
  * scenes render on a TRANSPARENT scrim (shader shows behind)
  * background = Vocal Melt shader (voice-reactive), composited under the motion graphics
  * Hallo lip-sync clip overlaid for the 0-30s intro (circular, bottom-right)
Keeps every synced scene, timing, and the circular presenter (visible after 30s) intact.
"""
import re

src = open("/home/ubuntu/render_animated_video.py").read()

# 1. Output paths -> v4 (don't clobber v3)
src = src.replace('OUT_DIR = "/home/ubuntu/welcome_v3"', 'OUT_DIR = "/home/ubuntu/welcome_v4"')
src = src.replace('FINAL = "/home/ubuntu/welcome_video_v3.mp4"', 'FINAL = "/home/ubuntu/welcome_video_v4_shader.mp4"')

# 2. Scene canvases -> transparent RGBA (the 8 scene/gap ones; NOT the glow overlay at draw_glow
#    which is Image.new("RGB", (W, H), (0, 0, 0)) and won't match this exact string).
src = src.replace('Image.new("RGB", (W, H))', 'Image.new("RGBA", (W, H), (0, 0, 0, 0))')

# 3. draw_animated_bg: replace the opaque per-line gradient with a transparent scrim.
grad = '''    # Draw gradient (fast — line by line)
    for y in range(H):
        frac = y / H
        r = int(c1[0] + (c2[0] - c1[0]) * frac)
        g = int(c1[1] + (c2[1] - c1[1]) * frac)
        b = int(c1[2] + (c2[2] - c1[2]) * frac)
        draw.line([(0, y), (W, y)], fill=(r, g, b))'''
scrim = '''    # Transparent dark scrim — shader shows through behind, text stays legible
    scrim = Image.new("RGBA", (W, H), (8, 10, 24, 130))
    img.alpha_composite(scrim)
    draw = ImageDraw.Draw(img)'''
assert grad in src, "gradient block not found"
src = src.replace(grad, scrim)

# 3b. draw_glow: blend an RGBA glow via alpha_composite (RGB ImageChops.add breaks on RGBA).
glow_old = '''    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(int(radius * pulse), 0, -3):
        intensity = int(25 * (r / radius) * pulse)
        c = (
            min(255, color[0] * intensity // 255),
            min(255, color[1] * intensity // 255),
            min(255, color[2] * intensity // 255)
        )
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)

    # Blend
    from PIL import ImageChops
    img_data = ImageChops.add(img, overlay)
    img.paste(img_data)'''
glow_new = '''    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(int(radius * pulse), 0, -3):
        intensity = int(25 * (r / radius) * pulse)
        c = (color[0], color[1], color[2], max(0, min(255, intensity)))
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    img.alpha_composite(overlay)'''
assert glow_old in src, "glow block not found"
src = src.replace(glow_old, glow_new)

# 4. Replace the frames->video encode with: render shader bg + composite frames(alpha) + Hallo intro.
encode = '''    # Encode frames to video
    video_only = os.path.join(OUT_DIR, "video_only.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p", video_only
    ], capture_output=True)'''
new_encode = '''    # --- TrigunAI: shader background + composite + Hallo intro ---
    import sys as _sys
    _sys.path.insert(0, "/home/ubuntu/video-creator-backend")
    from services.shader_service import render_shader_video
    shader_bg = os.path.join(OUT_DIR, "shader_bg.mp4")
    render_shader_video("vocal_melt", audio_path="/home/ubuntu/full_voiceover.mp3",
                        output_path=shader_bg, duration=total_duration, fps=FPS, width=W, height=H)
    video_only = os.path.join(OUT_DIR, "video_only.mp4")
    HALLO = "/home/ubuntu/avatar30.mp4"
    psz, pm = 300, 70
    cx, cy = psz // 2, psz // 2
    fc = (
        "[0:v][1:v]overlay=0:0[mg];"
        "[2:v]scale=%d:%d,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(gt(hypot(X-%d,Y-%d),%d),0,255)'[h];"
        "[mg][h]overlay=%d:%d:enable='lt(t,30)',format=yuv420p[v]"
        % (psz, psz, cx, cy, cx, W - psz - pm, H - psz - pm)
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-i", shader_bg,
        "-framerate", str(FPS), "-i", os.path.join(FRAMES_DIR, "frame_%05d.png"),
        "-i", HALLO,
        "-filter_complex", fc, "-map", "[v]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", video_only
    ], capture_output=True)'''
assert encode in src, "encode block not found"
src = src.replace(encode, new_encode)

open("/home/ubuntu/render_v4.py", "w").write(src)
print("render_v4.py written:", len(src), "bytes")
