"""
Video Compositor — Layers all elements into the final frame.

Layer stack (back to front):
  0. Skybox environment (3D room, HDRI, camera orbit)
  1. Shader effects (audio-reactive GLSL, pulsing energy)
  2. Slide content (text, diagrams, screenshots)
  3. Presenter avatar (circular PiP, bottom-right)

Uses ffmpeg filter_complex for compositing.
"""

import subprocess
import os


def _get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0


def composite_scene(
    skybox_path=None,
    shader_path=None,
    slide_path=None,
    voice_path=None,
    presenter_path=None,
    output_path="/tmp/scene.mp4",
    duration=15.0,
    fps=30,
    width=1920,
    height=1080,
):
    """
    Composite all layers for a single scene.

    All video inputs should be same resolution and fps.
    Missing layers are skipped (black background used as base).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    inputs = []
    filter_parts = []
    layer_count = 0

    # Layer 0: Skybox (or black base)
    if skybox_path and os.path.exists(skybox_path):
        inputs.extend(["-i", skybox_path])
        filter_parts.append(f"[{layer_count}:v]setpts=PTS-STARTPTS[skybox]")
        base = "skybox"
        layer_count += 1
    else:
        inputs.extend(["-f", "lavfi", "-i", f"color=c=0x0a0a1a:s={width}x{height}:d={duration}:r={fps}"])
        filter_parts.append(f"[{layer_count}:v]setpts=PTS-STARTPTS[skybox]")
        base = "skybox"
        layer_count += 1

    # Layer 1: Shader effects (overlay with blend)
    if shader_path and os.path.exists(shader_path):
        inputs.extend(["-i", shader_path])
        # Blend shader on top of skybox with "screen" blend mode
        filter_parts.append(
            f"[{layer_count}:v]setpts=PTS-STARTPTS[shader];"
            f"[{base}][shader]blend=all_mode=screen:all_opacity=0.7[shaded]"
        )
        base = "shaded"
        layer_count += 1

    # Layer 2: Slide content (overlay with transparency)
    if slide_path and os.path.exists(slide_path):
        # Slide is a static PNG — loop it for the duration
        inputs.extend(["-loop", "1", "-t", str(duration), "-i", slide_path])
        filter_parts.append(
            f"[{layer_count}:v]scale={width}:{height},format=rgba,"
            f"colorchannelmixer=aa=0.85[slide];"
            f"[{base}][slide]overlay=0:0:format=auto[slided]"
        )
        base = "slided"
        layer_count += 1

    # Layer 3: Presenter avatar (circular PiP, bottom-right)
    if presenter_path and os.path.exists(presenter_path):
        pip_size = 200
        pip_x = width - pip_size - 40
        pip_y = height - pip_size - 40

        inputs.extend(["-loop", "1", "-t", str(duration), "-i", presenter_path])
        filter_parts.append(
            f"[{layer_count}:v]scale={pip_size}:{pip_size},"
            f"format=rgba,"
            # Make circular mask using geq
            f"geq=lum='lum(X,Y)':a='if(gt(({pip_size}/2-X)*({pip_size}/2-X)+({pip_size}/2-Y)*({pip_size}/2-Y),{pip_size*pip_size//4}),0,255)'[pip];"
            f"[{base}][pip]overlay={pip_x}:{pip_y}[piped]"
        )
        base = "piped"
        layer_count += 1

    # Final output label
    filter_parts.append(f"[{base}]format=yuv420p[out]")

    # Build ffmpeg command
    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"] + inputs

    # Add voice audio if available
    audio_input = None
    if voice_path and os.path.exists(voice_path):
        cmd.extend(["-i", voice_path])
        audio_input = layer_count

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[out]",
    ])

    if audio_input is not None:
        cmd.extend(["-map", f"{audio_input}:a", "-c:a", "aac", "-b:a", "128k"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-shortest",
        output_path,
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Compositor error: {result.stderr[-500:]}")
        # Fallback: simpler composite without blend modes
        return _fallback_composite(skybox_path, shader_path, slide_path,
                                    voice_path, output_path, duration, fps, width, height)

    dur = _get_duration(output_path)
    return {"path": output_path, "duration": dur}


def _fallback_composite(skybox_path, shader_path, slide_path, voice_path,
                         output_path, duration, fps, width, height):
    """Simple overlay composite without fancy blend modes."""
    inputs = []
    filter_parts = []
    idx = 0

    # Base: skybox or shader or black
    base_path = skybox_path or shader_path
    if base_path and os.path.exists(base_path):
        inputs.extend(["-i", base_path])
    else:
        inputs.extend(["-f", "lavfi", "-i", f"color=c=0x0a0a1a:s={width}x{height}:d={duration}:r={fps}"])
    base = f"{idx}:v"
    idx += 1

    # Overlay slide
    if slide_path and os.path.exists(slide_path):
        inputs.extend(["-loop", "1", "-t", str(duration), "-i", slide_path])
        filter_parts.append(f"[{base}][{idx}:v]overlay=0:0[out]")
        base = "out"
        idx += 1
    else:
        filter_parts.append(f"[{base}]copy[out]")

    cmd = ["ffmpeg", "-y"] + inputs

    if voice_path and os.path.exists(voice_path):
        cmd.extend(["-i", voice_path])
        audio_idx = idx

    filter_str = ";".join(filter_parts) if filter_parts else f"[0:v]copy[out]"
    cmd.extend(["-filter_complex", filter_str, "-map", "[out]"])

    if voice_path and os.path.exists(voice_path):
        cmd.extend(["-map", f"{audio_idx}:a", "-c:a", "aac", "-b:a", "128k"])

    cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-shortest", output_path])

    subprocess.run(cmd, capture_output=True)
    dur = _get_duration(output_path)
    return {"path": output_path, "duration": dur}


def composite_full_video(
    scenes,
    music_path=None,
    music_volume=0.08,
    output_path="/tmp/final.mp4",
):
    """
    Concatenate all composited scenes and add background music.

    scenes: list of {"video_path": str} from composite_scene results
    """
    build_dir = output_path + "_build"
    os.makedirs(build_dir, exist_ok=True)

    # Concat
    concat_file = os.path.join(build_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for scene in scenes:
            vp = scene.get("video_path") or scene.get("path", "")
            if os.path.exists(vp):
                f.write(f"file '{vp}'\n")

    no_music = os.path.join(build_dir, "no_music.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", no_music
    ], capture_output=True)

    # Add music
    if music_path and os.path.exists(music_path):
        video_dur = _get_duration(no_music)
        subprocess.run([
            "ffmpeg", "-y", "-i", no_music, "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume},afade=in:st=0:d=3,afade=out:st={video_dur-3}:d=3[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            output_path
        ], capture_output=True)
    else:
        os.rename(no_music, output_path)

    dur = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0
    return {"path": output_path, "duration": dur, "size_mb": round(size_mb, 1)}
