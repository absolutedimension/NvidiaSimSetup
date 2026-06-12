#!/usr/bin/env python3
"""Transcribe audio via Deepgram Nova-2 with word-level timestamps and speaker diarization.

Usage:
    python3 transcribe_audio.py \
        --audio "/path/to/audiobook.mp3" \
        --out transcript.json

    # With speaker diarization:
    python3 transcribe_audio.py \
        --audio audiobook.mp3 --out transcript.json --diarize

Reads DEEPGRAM_API_KEY from .env file or environment variable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_api_key():
    """Load Deepgram API key from env or .env file."""
    key = os.environ.get("DEEPGRAM_API_KEY")
    if key:
        return key

    # Search for .env in current dir and parent dirs
    for p in [Path(".env"), Path(__file__).parent.parent / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("DEEPGRAM_API_KEY="):
                    return line.split("=", 1)[1].strip()

    print("ERROR: DEEPGRAM_API_KEY not found in environment or .env file", file=sys.stderr)
    sys.exit(1)


def transcribe(audio_path: str, diarize: bool = False, language: str = "en") -> dict:
    """Transcribe audio file via Deepgram Nova-2 REST API."""
    import requests

    api_key = load_api_key()
    url = "https://api.deepgram.com/v1/listen"

    params = {
        "model": "nova-2",
        "language": language,
        "punctuate": "true",
        "paragraphs": "true",
        "smart_format": "true",
        "utterances": "true",
    }
    if diarize:
        params["diarize"] = "true"

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/mpeg",
    }

    file_size = os.path.getsize(audio_path)
    print(f"Uploading {audio_path} ({file_size / 1e6:.1f} MB) to Deepgram...", file=sys.stderr)

    with open(audio_path, "rb") as f:
        resp = requests.post(url, headers=headers, params=params, data=f, timeout=300)

    if resp.status_code != 200:
        print(f"ERROR: Deepgram returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    channel = result["results"]["channels"][0]["alternatives"][0]

    # Extract structured transcript
    transcript = {
        "audio_file": os.path.basename(audio_path),
        "duration": result["metadata"]["duration"],
        "model": result["metadata"]["models"][0] if result.get("metadata", {}).get("models") else "nova-2",
        "full_text": channel["transcript"],
        "words": channel.get("words", []),
        "paragraphs": channel.get("paragraphs", {}),
        "utterances": result.get("results", {}).get("utterances", []),
    }

    # Stats
    n_words = len(transcript["words"])
    dur = transcript["duration"]
    print(f"Transcribed: {n_words} words, {dur:.1f}s duration", file=sys.stderr)

    if diarize and transcript["utterances"]:
        speakers = set()
        for utt in transcript["utterances"]:
            speakers.add(utt.get("speaker", 0))
        print(f"Speakers detected: {len(speakers)}", file=sys.stderr)

    return transcript


def transcript_to_srt(transcript: dict, output_srt: str, max_words: int = 10, max_duration: float = 4.0):
    """Convert word-level transcript to SRT subtitle file."""

    def fmt_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    words = transcript["words"]
    if not words:
        print("WARNING: No words in transcript, cannot generate SRT", file=sys.stderr)
        return

    entries = []
    chunk = []
    chunk_start = None

    for word in words:
        if chunk_start is None:
            chunk_start = word["start"]
        chunk.append(word["word"])

        # Split on: max words, max duration, or sentence-ending punctuation
        is_sentence_end = word["word"].rstrip().endswith((".", "!", "?", "...", "—"))
        is_max_words = len(chunk) >= max_words
        is_max_duration = (word["end"] - chunk_start) >= max_duration

        if is_sentence_end or is_max_words or is_max_duration:
            entries.append({
                "start": chunk_start,
                "end": word["end"],
                "text": " ".join(chunk),
            })
            chunk = []
            chunk_start = None

    # Remaining words
    if chunk:
        entries.append({
            "start": chunk_start,
            "end": words[-1]["end"],
            "text": " ".join(chunk),
        })

    # Write SRT
    with open(output_srt, "w") as f:
        for i, entry in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{fmt_time(entry['start'])} --> {fmt_time(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"Generated {len(entries)} subtitle entries → {output_srt}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio via Deepgram Nova-2")
    parser.add_argument("--audio", required=True, help="Path to audio file (MP3/WAV/M4A)")
    parser.add_argument("--out", required=True, help="Output transcript JSON path")
    parser.add_argument("--srt", default=None, help="Also generate SRT subtitle file")
    parser.add_argument("--diarize", action="store_true", help="Enable speaker diarization")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    args = parser.parse_args()

    transcript = transcribe(args.audio, diarize=args.diarize, language=args.language)

    with open(args.out, "w") as f:
        json.dump(transcript, f, indent=2)
    print(f"Transcript saved → {args.out}", file=sys.stderr)

    if args.srt:
        transcript_to_srt(transcript, args.srt)


if __name__ == "__main__":
    main()
