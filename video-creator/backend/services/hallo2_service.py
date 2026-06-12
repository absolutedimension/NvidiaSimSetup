"""
Hallo2 Avatar Service.
Generates talking head video from image + audio.
"""

import subprocess
import os
import yaml
import shutil


HALLO2_DIR = "/home/ubuntu/hallo2"
HALLO2_VENV = "/home/ubuntu/hallo2/venv/bin/python3"


def generate_avatar(image_path, audio_path, output_path):
    """
    Generate a talking avatar video using Hallo2.

    Args:
        image_path: Path to presenter image (PNG/JPG)
        audio_path: Path to voice audio (WAV, 16kHz mono)
        output_path: Where to save the output MP4
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Ensure audio is 16kHz mono WAV
    wav_path = output_path + "_audio.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-ar", "16000", "-ac", "1", wav_path
    ], capture_output=True)

    # Create temporary config
    config_path = os.path.join(HALLO2_DIR, "configs/inference/_temp.yaml")
    save_path = os.path.dirname(output_path)

    # Read base config
    base_config = os.path.join(HALLO2_DIR, "configs/inference/long.yaml")
    with open(base_config) as f:
        config = yaml.safe_load(f)

    # Update paths
    config["source_image"] = image_path
    config["driving_audio"] = wav_path
    config["save_path"] = save_path

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Run Hallo2
    result = subprocess.run(
        [HALLO2_VENV, "scripts/inference_long.py", "--config", config_path],
        cwd=HALLO2_DIR,
        capture_output=True, text=True,
        timeout=1800,  # 30 min max
    )

    # Find output video
    avatar_name = os.path.splitext(os.path.basename(image_path))[0]
    seg_video_dir = os.path.join(save_path, avatar_name, "seg_video")

    if os.path.exists(seg_video_dir):
        # Concatenate segment videos
        segments = sorted([
            os.path.join(seg_video_dir, f)
            for f in os.listdir(seg_video_dir)
            if f.endswith(".mp4")
        ])

        if segments:
            concat_file = os.path.join(save_path, "concat.txt")
            with open(concat_file, "w") as f:
                for seg in segments:
                    f.write(f"file '{seg}'\n")

            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ], capture_output=True)

    # Get duration
    dur = 0
    if os.path.exists(output_path):
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", output_path],
            capture_output=True, text=True
        )
        dur = float(r.stdout.strip()) if r.stdout.strip() else 0

    # Cleanup temp config
    if os.path.exists(config_path):
        os.remove(config_path)

    return {"path": output_path, "duration": dur}
