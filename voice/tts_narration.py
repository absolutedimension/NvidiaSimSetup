#!/usr/bin/env python3
"""Generate TTS narration via Deepgram Aura API.

Usage:
    python3 tts_narration.py --text "Your script here" --out narration.mp3
    python3 tts_narration.py --script script.txt --out narration.mp3
    python3 tts_narration.py --script script.txt --out narration.mp3 --voice aura-orion-en

Available voices (Deepgram Aura):
    aura-asteria-en   — Female, warm, professional (default)
    aura-luna-en      — Female, soft, friendly
    aura-stella-en    — Female, confident
    aura-athena-en    — Female, authoritative
    aura-hera-en      — Female, mature
    aura-orion-en     — Male, deep, professional
    aura-arcas-en     — Male, warm
    aura-perseus-en   — Male, clear
    aura-angus-en     — Male, friendly
    aura-orpheus-en   — Male, rich

Reads DEEPGRAM_API_KEY from .env file or environment variable.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def load_api_key():
    """Load Deepgram API key from env or .env file."""
    key = os.environ.get("DEEPGRAM_API_KEY")
    if key:
        return key
    for p in [Path(".env"), Path(__file__).parent.parent / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("DEEPGRAM_API_KEY="):
                    return line.split("=", 1)[1].strip()
    print("ERROR: DEEPGRAM_API_KEY not found", file=sys.stderr)
    sys.exit(1)


def generate_tts(text: str, output_path: str, voice: str = "aura-asteria-en"):
    """Generate TTS audio via Deepgram Aura API."""
    import requests

    api_key = load_api_key()
    url = f"https://api.deepgram.com/v1/speak?model={voice}"

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}

    print(f"Generating TTS ({len(text)} chars, voice={voice})...", file=sys.stderr)
    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        print(f"ERROR: Deepgram returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(resp.content)

    size = os.path.getsize(output_path)
    print(f"TTS audio saved: {output_path} ({size / 1024:.1f} KB)", file=sys.stderr)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate TTS via Deepgram Aura")
    parser.add_argument("--text", default=None, help="Text to speak")
    parser.add_argument("--script", default=None, help="Path to text file with script")
    parser.add_argument("--out", required=True, help="Output MP3 path")
    parser.add_argument("--voice", default="aura-asteria-en",
                        help="Deepgram Aura voice model (default: aura-asteria-en)")
    args = parser.parse_args()

    if args.script:
        text = Path(args.script).read_text().strip()
    elif args.text:
        text = args.text
    else:
        print("ERROR: Provide --text or --script", file=sys.stderr)
        sys.exit(1)

    generate_tts(text, args.out, args.voice)


if __name__ == "__main__":
    main()
