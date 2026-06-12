"""
Music Generation Service.
Uses ACE-Step for AI background music, with fallback to ambient generation.
"""

import subprocess
import os


def _get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0


def generate_music(prompt, duration=180, output_path="/tmp/music.wav"):
    """
    Generate background music.

    First tries ACE-Step (if installed). Falls back to ambient pink noise generator.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Try ACE-Step
    try:
        return _generate_ace_step(prompt, duration, output_path)
    except Exception as e:
        print(f"ACE-Step not available: {e}. Using ambient fallback.")

    # Fallback: generate ambient pink noise with gentle filter
    return _generate_ambient_fallback(duration, output_path)


def _generate_ace_step(prompt, duration, output_path):
    """Generate music using ACE-Step model."""
    # ACE-Step integration — will be wired when installed
    raise NotImplementedError("ACE-Step not yet installed")


def _generate_ambient_fallback(duration, output_path):
    """Generate soft ambient background using ffmpeg filters."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anoisesrc=d={duration}:c=pink:a=0.015",
        "-af", "lowpass=f=300,highpass=f=50,volume=0.3",
        "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",
        output_path
    ], capture_output=True)

    dur = _get_duration(output_path)
    return {"path": output_path, "duration": dur}
