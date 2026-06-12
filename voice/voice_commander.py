#!/usr/bin/env python3
"""Real-time voice -> mode switching for the cinematographer drone.

Listens to microphone via Deepgram Nova-2 streaming STT, recognizes mode
commands, outputs mode changes to stdout or WebSocket.

For live demo:
    python voice_commander.py --api-key $DEEPGRAM_KEY --output ws://localhost:9000

For recording a command log (offline/demo):
    python voice_commander.py --api-key $DEEPGRAM_KEY --output log --log-file commands.json

Dependencies:
    pip install deepgram-sdk pyaudio
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

MODE_COMMANDS = {
    "hero": {"type": "mode", "value": 0, "mode_name": "HERO"},
    "power": {"type": "mode", "value": 0, "mode_name": "HERO"},
    "intimate": {"type": "mode", "value": 1, "mode_name": "INTIMATE"},
    "close": {"type": "mode", "value": 1, "mode_name": "INTIMATE"},
    "close up": {"type": "mode", "value": 1, "mode_name": "INTIMATE"},
    "epic": {"type": "mode", "value": 2, "mode_name": "EPIC"},
    "wide": {"type": "mode", "value": 2, "mode_name": "EPIC"},
    "go high": {"type": "mode", "value": 2, "mode_name": "EPIC"},
    "energy": {"type": "mode", "value": 3, "mode_name": "ENERGY"},
    "fast": {"type": "mode", "value": 3, "mode_name": "ENERGY"},
    "solitude": {"type": "mode", "value": 4, "mode_name": "SOLITUDE"},
    "isolation": {"type": "mode", "value": 4, "mode_name": "SOLITUDE"},
    "pull back": {"type": "mode", "value": 4, "mode_name": "SOLITUDE"},
    "beauty": {"type": "mode", "value": 5, "mode_name": "BEAUTY"},
    "orbit": {"type": "mode", "value": 5, "mode_name": "BEAUTY"},
    "closer": {"type": "param", "key": "distance", "delta": -0.5},
    "farther": {"type": "param", "key": "distance", "delta": +0.5},
    "higher": {"type": "param", "key": "altitude", "delta": +0.3},
    "lower": {"type": "param", "key": "altitude", "delta": -0.3},
    "faster": {"type": "param", "key": "speed", "delta": +0.2},
    "slower": {"type": "param", "key": "speed", "delta": -0.2},
    "hold": {"type": "control", "action": "pause"},
    "resume": {"type": "control", "action": "play"},
    "stop": {"type": "control", "action": "emergency_stop"},
}

FUZZY_ALIASES = {
    "go hi": "go high",
    "close-up": "close up",
    "closeup": "close up",
    "pullback": "pull back",
    "pull-back": "pull back",
    "go wide": "wide",
}


def match_command(transcript: str) -> dict | None:
    """Match a transcript to a known command. Returns None if no match."""
    text = transcript.strip().lower()
    if text in FUZZY_ALIASES:
        text = FUZZY_ALIASES[text]
    if text in MODE_COMMANDS:
        return {**MODE_COMMANDS[text], "spoken": text}
    for phrase in sorted(MODE_COMMANDS, key=len, reverse=True):
        if phrase in text:
            return {**MODE_COMMANDS[phrase], "spoken": phrase}
    return None


def generate_srt(script_path: str | Path, output_path: str | Path) -> None:
    """Generate an SRT subtitle file from a demo_script.json."""
    with open(script_path) as f:
        script = json.load(f)

    lines = []
    for i, cmd in enumerate(script["commands"], 1):
        t = cmd["time"]
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        start = f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        end_t = t + 2.0
        eh = int(end_t // 3600)
        em = int((end_t % 3600) // 60)
        es = int(end_t % 60)
        ems = int((end_t % 1) * 1000)
        end = f"{eh:02d}:{em:02d}:{es:02d},{ems:03d}"

        display = cmd.get("display", f'"{cmd["spoken"]}"')
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(display)
        lines.append("")

    Path(output_path).write_text("\n".join(lines))


async def run_live(api_key: str, output_mode: str, log_file: str | None = None):
    """Run live voice recognition via Deepgram streaming."""
    try:
        from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
    except ImportError:
        print("ERROR: pip install deepgram-sdk pyaudio", file=sys.stderr)
        sys.exit(1)

    deepgram = DeepgramClient(api_key)
    connection = deepgram.listen.live.v("1")

    command_log = []
    start_time = time.time()

    def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if not transcript.strip():
            return
        cmd = match_command(transcript)
        if cmd:
            elapsed = time.time() - start_time
            entry = {"time": round(elapsed, 2), **cmd}
            command_log.append(entry)
            print(json.dumps(entry), flush=True)

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        interim_results=False,
        utterance_end_ms=1000,
        vad_events=True,
        encoding="linear16",
        sample_rate=16000,
        channels=1,
    )
    await connection.start(options)

    try:
        import pyaudio
    except ImportError:
        print("ERROR: pip install pyaudio", file=sys.stderr)
        sys.exit(1)

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=4096,
    )

    print("Listening... (Ctrl+C to stop)", file=sys.stderr)
    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            await connection.send(data)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        await connection.finish()

    if log_file and command_log:
        Path(log_file).write_text(json.dumps(command_log, indent=2))
        print(f"Saved {len(command_log)} commands to {log_file}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    live_p = sub.add_parser("live", help="Run live voice recognition")
    live_p.add_argument("--api-key", required=True)
    live_p.add_argument("--log-file", default=None)

    srt_p = sub.add_parser("srt", help="Generate SRT from demo_script.json")
    srt_p.add_argument("--script", required=True, type=Path)
    srt_p.add_argument("--out", required=True, type=Path)

    args = ap.parse_args()

    if args.cmd == "live":
        asyncio.run(run_live(args.api_key, "log", args.log_file))
    elif args.cmd == "srt":
        generate_srt(args.script, args.out)
        print(f"Generated SRT: {args.out}")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
