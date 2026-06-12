"""
F5-TTS Voice Generation Service.
Wraps F5-TTS with the tone-selectable voice library.
"""

import json
import os
import subprocess

VOICE_DIR = "/home/ubuntu/audio_pipeline/voice_library"
VOICE_INDEX = os.path.join(VOICE_DIR, "voice_index.json")

# Lazy-loaded TTS model
_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        from f5_tts.api import F5TTS
        _tts = F5TTS()
    return _tts


def _get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0


def generate_speech(text, tone="female_confident", speed=0.75, output_path="/tmp/voice.wav"):
    """
    Generate speech from text using F5-TTS with tone cloning.

    Args:
        text: The text to speak
        tone: Voice tone key (e.g., "female_confident", "male_excited")
        speed: Speech speed (0.65=very slow, 0.75=learning pace, 0.85=natural, 1.0=fast)
        output_path: Where to save the WAV file

    Returns:
        {"path": str, "duration": float}
    """
    tts = _get_tts()

    # Load voice reference
    with open(VOICE_INDEX) as f:
        voices = json.load(f)

    if tone not in voices:
        tone = "female_confident"

    ref_audio = voices[tone]["reference"]
    ref_meta_path = os.path.join(VOICE_DIR, tone, "metadata.json")
    with open(ref_meta_path) as f:
        ref_meta = json.load(f)
    ref_text = ref_meta["reference_text"]

    # Generate
    wav, sr, _ = tts.infer(
        ref_file=ref_audio,
        ref_text=ref_text,
        gen_text=text,
        seed=-1,
        speed=speed,
    )

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tts.export_wav(wav, output_path, sr)

    duration = _get_duration(output_path)

    return {"path": output_path, "duration": duration}
