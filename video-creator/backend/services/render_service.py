"""
Final Video Render Service.
Assembles slides + voice + music into a final MP4 using ffmpeg.
"""

import subprocess
import os
import json


def _get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0


def render_video(project, output_path, progress_callback=None):
    """
    Assemble final video from project JSON.

    Project structure:
    {
        "scenes": [
            {
                "id": "scene_01",
                "voice_path": "/path/to/voice.wav",
                "slide_path": "/path/to/slide.png",
                "duration": 15.0
            }, ...
        ],
        "music_path": "/path/to/music.wav",
        "music_volume": 0.08,
        "fps": 30,
        "resolution": [1920, 1080]
    }
    """
    scenes = project.get("scenes", [])
    music_path = project.get("music_path")
    music_volume = project.get("music_volume", 0.08)
    fps = project.get("fps", 30)
    W, H = project.get("resolution", [1920, 1080])

    # Optional audio-reactive shader background (id from shader_service).
    background_shader = project.get("background_shader")
    if background_shader:
        try:
            from services.shader_service import SHADER_TEMPLATES
            if background_shader not in SHADER_TEMPLATES:
                background_shader = None
        except Exception:
            background_shader = None

    build_dir = output_path + "_build"
    os.makedirs(build_dir, exist_ok=True)

    if progress_callback:
        progress_callback(5, "Creating scene clips")

    # Step 1: Create video clip for each scene (slide image + Ken Burns + voice)
    clip_files = []
    for i, scene in enumerate(scenes):
        slide = scene.get("slide_path", "")
        voice = scene.get("voice_path", "")
        dur = scene.get("duration", 10)

        clip_path = os.path.join(build_dir, f"clip_{i:03d}.mp4")

        if background_shader and slide and os.path.exists(slide):
            # Audio-reactive shader background + transparent slide overlaid + voice.
            from services.shader_service import render_shader_video
            shader_bg = os.path.join(build_dir, f"shader_{i:03d}.mp4")
            try:
                render_shader_video(
                    shader_name=background_shader,
                    audio_path=voice if (voice and os.path.exists(voice)) else None,
                    output_path=shader_bg, duration=dur, fps=fps, width=W, height=H,
                )
            except Exception as e:
                print(f"shader render failed ({e}); using opaque slide")
                shader_bg = None

            if shader_bg and os.path.exists(shader_bg):
                fc = (f"[1:v]scale={W}:{H},format=rgba[sl];"
                      f"[0:v][sl]overlay=0:0:format=auto,format=yuv420p[v]")
                cmd = ["ffmpeg", "-y", "-i", shader_bg, "-loop", "1", "-t", str(dur), "-i", slide]
                if voice and os.path.exists(voice):
                    cmd += ["-i", voice, "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
                            "-c:a", "aac", "-b:a", "128k"]
                else:
                    cmd += ["-filter_complex", fc, "-map", "[v]"]
                cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-shortest", clip_path]
                subprocess.run(cmd, capture_output=True)
            else:
                background_shader = None  # disable for remaining scenes; fall through next iters

        if not os.path.exists(clip_path) and slide and os.path.exists(slide):
            # Slide with Ken Burns zoom + voice
            frames = int(dur * fps)
            zp = f"zoompan=z='1+0.0008*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={fps}"

            if voice and os.path.exists(voice):
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", slide,
                    "-i", voice,
                    "-filter_complex", f"[0:v]{zp},format=yuv420p[v]",
                    "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-shortest", clip_path
                ], capture_output=True)
            else:
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", slide,
                    "-vf", f"{zp},format=yuv420p",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-t", str(dur), clip_path
                ], capture_output=True)

        if not os.path.exists(clip_path):
            # Black frame with voice (no slide, or shader+opaque unavailable)
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=0x0a0a1a:s={W}x{H}:d={dur}:r={fps}",
                "-i", voice if voice and os.path.exists(voice) else "",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest", clip_path
            ], capture_output=True)

        if os.path.exists(clip_path):
            clip_files.append(clip_path)

        if progress_callback:
            pct = 10 + int(60 * (i + 1) / len(scenes))
            progress_callback(pct, f"Scene {i+1}/{len(scenes)}")

    if not clip_files:
        return {"error": "No clips generated"}

    # Step 2: Concatenate with crossfade transitions
    if progress_callback:
        progress_callback(70, "Joining scenes with transitions")

    # Simple concat (crossfade is complex; use hard cuts for reliability)
    concat_file = os.path.join(build_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")

    no_music = os.path.join(build_dir, "no_music.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        no_music
    ], capture_output=True)

    # Step 3: Mix with background music
    if progress_callback:
        progress_callback(85, "Adding background music")

    if music_path and os.path.exists(music_path):
        video_dur = _get_duration(no_music)
        subprocess.run([
            "ffmpeg", "-y",
            "-i", no_music, "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume},afade=in:st=0:d=3,afade=out:st={video_dur-3}:d=3[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_path
        ], capture_output=True)
    else:
        # No music — just copy
        os.rename(no_music, output_path)

    if progress_callback:
        progress_callback(100, "Complete")

    duration = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0

    return {"path": output_path, "duration": duration, "size_mb": round(size_mb, 1)}
