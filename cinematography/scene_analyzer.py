#!/usr/bin/env python3
"""Scene Analyzer — LLM reads a transcript and generates a cinematographic scene breakdown.

Takes the Deepgram transcript + music features and uses GPT-4o-mini to:
1. Identify emotional scenes/beats in the dialogue
2. Map each scene to a cinematographic mode (HERO/INTIMATE/EPIC/ENERGY/SOLITUDE/BEAUTY)
3. Generate shot notes for the camera operator
4. Output a mode schedule string for the trajectory exporter

Usage:
    python3 scene_analyzer.py \
        --transcript transcript.json \
        --music-features music_features.json \
        --out scene_breakdown.json \
        --litellm-url http://localhost:4000/v1

    # Or use Azure directly:
    python3 scene_analyzer.py \
        --transcript transcript.json \
        --out scene_breakdown.json \
        --litellm-url https://azure-trigunai-model.openai.azure.com/openai \
        --api-key YOUR_AZURE_KEY

Output includes:
    - scene_breakdown.json (detailed per-scene analysis)
    - mode_schedule string (for --mode-schedule flag in trajectory export)
"""
from __future__ import annotations

import argparse
import json
import sys

import requests

MODE_NAMES = ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"]

DIRECTOR_SYSTEM_PROMPT = """You are an expert film director analyzing a script for a cinematic animation.

You will receive a transcript of dialogue (with word-level timestamps) and optionally music analysis data.
Your job is to break the content into SCENES — each scene gets a cinematographic mode that controls
the camera behavior, lighting, and stage environment.

AVAILABLE CINEMATOGRAPHIC MODES (choose one per scene):

1. **HERO** — Dramatic, powerful. Camera sweeps grandly, center-stage framing.
   Red/gold lighting, concert arena environment.
   USE FOR: climactic moments, powerful statements, key reveals, emotional peaks.

2. **INTIMATE** — Close, personal. Camera moves gently inward, tight framing.
   Warm amber lighting, jazz club environment.
   USE FOR: quiet confessions, tender moments, personal reflections, soft dialogue.

3. **EPIC** — Grand, sweeping. Camera pulls wide, elevated angles.
   Blue/white lasers, stadium environment.
   USE FOR: world-building exposition, grand statements, scope-establishing moments.

4. **ENERGY** — Intense, kinetic. Camera moves fast, dynamic angles.
   Neon pink/cyan strobes, underground rave environment.
   USE FOR: arguments, rapid dialogue, tension, excitement, confrontation.

5. **SOLITUDE** — Isolated, reflective. Camera holds still or pulls away slowly.
   Single ghost light, empty theater environment.
   USE FOR: pauses, silences, loneliness, contemplation, grief, endings.

6. **BEAUTY** — Elegant, flowing. Camera orbits gracefully, smooth arcs.
   Pink/gold diffused light, fashion runway environment.
   USE FOR: descriptions of beauty, love, art, nature, peaceful moments, openings/closings.

RULES:
- Each scene MUST be at least 5 seconds long
- Transition points should land on sentence boundaries (never mid-word)
- Use start_time from the word-level timestamps (be precise to 0.1s)
- Every scene MUST use one of the 6 exact mode names above
- Aim for 8-20 scenes for a typical 5-10 minute piece
- The emotional arc should feel natural — don't switch modes arbitrarily
- If dialogue is neutral/expository, default to BEAUTY or INTIMATE
- Reserve HERO and EPIC for genuinely dramatic/grand moments
- SOLITUDE for genuine pauses or heavy silence
- ENERGY only for high-intensity rapid exchanges

Output STRICT JSON with this schema:
{
  "title": "suggested cinematic title for this piece",
  "emotional_arc": "one sentence describing the overall narrative arc",
  "total_duration": <seconds>,
  "num_scenes": <int>,
  "scenes": [
    {
      "scene_number": 1,
      "start_time": 0.0,
      "end_time": 15.3,
      "duration": 15.3,
      "emotion": "reflective|dramatic|tender|revelatory|intense|graceful|melancholic|joyful|tense|peaceful",
      "mode": "INTIMATE",
      "dialogue_excerpt": "first 15 words of dialogue in this scene...",
      "shot_note": "Slow push-in as narrator sets the scene, warm amber tones"
    }
  ]
}"""


def format_transcript_for_prompt(transcript: dict, max_words: int = 2000) -> str:
    """Format word-level transcript for the LLM prompt."""
    words = transcript.get("words", [])
    if not words:
        # Fallback: use full text with duration
        return f"[0.0s - {transcript.get('duration', 0):.1f}s] {transcript.get('full_text', '')}"

    lines = []
    current_line = []
    line_start = None

    for w in words[:max_words]:
        if line_start is None:
            line_start = w["start"]
        current_line.append(w["word"])

        # Break into ~15-word lines
        if len(current_line) >= 15 or w["word"].rstrip().endswith((".", "!", "?", "...")):
            lines.append(f"[{line_start:.1f}s] {' '.join(current_line)}")
            current_line = []
            line_start = None

    if current_line:
        lines.append(f"[{line_start:.1f}s] {' '.join(current_line)}")

    return "\n".join(lines)


def analyze_scenes(
    transcript: dict,
    music_features: dict | None = None,
    litellm_url: str = "http://localhost:4000/v1",
    api_key: str = "sk-trigunai-master-key-2026",
    model: str = "gpt-4o-mini",
) -> dict:
    """Use LLM to analyze transcript and generate scene breakdown."""

    formatted_transcript = format_transcript_for_prompt(transcript)

    user_content = f"TRANSCRIPT (with timestamps):\n{formatted_transcript}\n\n"
    user_content += f"TOTAL DURATION: {transcript.get('duration', 0):.1f} seconds\n\n"

    if music_features:
        user_content += f"MUSIC ANALYSIS:\n"
        user_content += f"- Tempo: {music_features.get('tempo', 'unknown')} BPM\n"
        user_content += f"- Duration: {music_features.get('duration', 'unknown')}s\n"
        user_content += f"- Segments detected: {music_features.get('num_segments', 'unknown')}\n"

    messages = [
        {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    print(f"Calling {model} for scene analysis...", file=sys.stderr)

    resp = requests.post(
        f"{litellm_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 4000,
        },
        timeout=180,
    )

    if resp.status_code != 200:
        print(f"ERROR: LLM returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    scene_breakdown = json.loads(result["choices"][0]["message"]["content"])

    # Validate modes
    for scene in scene_breakdown.get("scenes", []):
        if scene.get("mode") not in MODE_NAMES:
            print(f"WARNING: Invalid mode '{scene.get('mode')}' in scene {scene.get('scene_number')}, "
                  f"defaulting to BEAUTY", file=sys.stderr)
            scene["mode"] = "BEAUTY"

    n_scenes = len(scene_breakdown.get("scenes", []))
    print(f"Scene breakdown: {n_scenes} scenes, title: '{scene_breakdown.get('title', 'untitled')}'",
          file=sys.stderr)

    return scene_breakdown


def scene_breakdown_to_schedule(scene_breakdown: dict, fps: float = 50.0) -> str:
    """Convert LLM scene breakdown to mode schedule string for trajectory export."""
    parts = []
    for scene in scene_breakdown.get("scenes", []):
        step = int(scene["start_time"] * fps)
        mode = scene["mode"]
        parts.append(f"{step}:{mode}")
    return ",".join(parts)


def main():
    parser = argparse.ArgumentParser(description="LLM Scene Analyzer for cinematographic animation")
    parser.add_argument("--transcript", required=True, help="Deepgram transcript JSON")
    parser.add_argument("--music-features", default=None, help="Music features JSON (optional)")
    parser.add_argument("--out", required=True, help="Output scene breakdown JSON")
    parser.add_argument("--litellm-url", default="http://localhost:4000/v1",
                        help="LiteLLM proxy URL (default: EC2 proxy)")
    parser.add_argument("--api-key", default="sk-trigunai-master-key-2026",
                        help="API key for LiteLLM")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--fps", type=float, default=50.0,
                        help="Simulation FPS for mode schedule (default: 50)")
    args = parser.parse_args()

    with open(args.transcript) as f:
        transcript = json.load(f)

    music_features = None
    if args.music_features:
        with open(args.music_features) as f:
            music_features = json.load(f)

    scene_breakdown = analyze_scenes(
        transcript, music_features,
        litellm_url=args.litellm_url,
        api_key=args.api_key,
        model=args.model,
    )

    # Add mode schedule string
    schedule_str = scene_breakdown_to_schedule(scene_breakdown, fps=args.fps)
    scene_breakdown["mode_schedule"] = schedule_str
    scene_breakdown["fps"] = args.fps

    with open(args.out, "w") as f:
        json.dump(scene_breakdown, f, indent=2)

    # Print the schedule string to stdout (for piping)
    print(schedule_str)

    # Summary
    print(f"\nScene breakdown saved → {args.out}", file=sys.stderr)
    print(f"Mode schedule: {schedule_str}", file=sys.stderr)
    mode_counts = {}
    for scene in scene_breakdown.get("scenes", []):
        m = scene["mode"]
        mode_counts[m] = mode_counts.get(m, 0) + 1
    for mode in MODE_NAMES:
        print(f"  {mode:10s}: {mode_counts.get(mode, 0)} scene(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
