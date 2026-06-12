#!/usr/bin/env python3
"""Table Read to Cinema — Master orchestrator.

One command to turn a dialogue+music audio file into a complete cinematic animation.

Usage:
    python3 table_read_to_cinema.py \
        --audio "/path/to/audiobook.mp3" \
        --output-dir ./audiobook_cinematic/ \
        --ec2-ip 18.234.250.128 \
        --quality draft

Full pipeline (6 stages):
    1. Transcribe audio (Deepgram Nova-2)
    2. Extract music features (librosa)
    3. LLM scene analysis (GPT-4o-mini)
    4. Export camera trajectory (Isaac Lab on EC2)
    5. Render animation (Blender EEVEE on EC2)
    6. Composite final video (ffmpeg on EC2)

Dependencies:
    Local: python3 with requests, librosa (Python 3.9)
    EC2: isaaclab container, blender45, ffmpeg, HDRIs, character FBX
    API: DEEPGRAM_API_KEY in .env, LiteLLM proxy on EC2:4000
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

PYTHON39 = "/Library/Developer/CommandLineTools/usr/bin/python3"
PROJECT_ROOT = Path(__file__).parent.parent
SSH_KEY = os.path.expanduser("~/.ssh/trigunai_key.pem")

QUALITY_PRESETS = {
    "draft": {"width": 1280, "height": 720, "fps": 24, "samples": 32},
    "standard": {"width": 1920, "height": 1080, "fps": 24, "samples": 64},
    "final": {"width": 1920, "height": 1080, "fps": 30, "samples": 128},
}

EC2_PATHS = {
    "character": "/home/ubuntu/Daphne_Blender.fbx",
    "checkpoint": "/workspace/isaaclab/cinematography/checkpoints/cinematographer_v4_modes_best.pth",
    "hdri_dir": "/home/ubuntu/hdri/",
    "output_dir": "/home/ubuntu/table_read_output/",
    "render_script": "/home/ubuntu/render_demo_blender.py",
    "export_script": "/workspace/isaaclab/cinematography/export_cinematographer_trajectory.py",
}


def log(stage, msg):
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  STAGE {stage}: {msg}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


def run(cmd, check=True, capture=False):
    """Run a local command."""
    print(f"  $ {cmd}", file=sys.stderr)
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: command failed with exit code {result.returncode}", file=sys.stderr)
        if capture:
            print(f"  stdout: {result.stdout}", file=sys.stderr)
            print(f"  stderr: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result


def ssh(ec2_ip, cmd, check=True):
    """Run a command on EC2 via SSH."""
    full = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no ubuntu@{ec2_ip} "{cmd}"'
    return run(full, check=check, capture=True)


def scp_to_ec2(ec2_ip, local_path, remote_path):
    """Upload a file to EC2."""
    run(f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no "{local_path}" ubuntu@{ec2_ip}:{remote_path}')


def scp_from_ec2(ec2_ip, remote_path, local_path):
    """Download a file from EC2."""
    run(f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no ubuntu@{ec2_ip}:{remote_path} "{local_path}"')


# ── Stage 1: Audio Intelligence ───────────────────────────────────────────────

def stage1_transcribe(audio_path, output_dir):
    """Transcribe audio via Deepgram and extract music features."""
    log(1, "AUDIO INTELLIGENCE")

    transcript_json = output_dir / "transcript.json"
    srt_path = output_dir / "subtitles.srt"
    music_json = output_dir / "music_features.json"

    # 1A. Transcribe with Deepgram
    print("  [1A] Transcribing with Deepgram Nova-2...", file=sys.stderr)
    transcribe_script = PROJECT_ROOT / "voice" / "transcribe_audio.py"
    run(f'python3 "{transcribe_script}" '
        f'--audio "{audio_path}" '
        f'--out "{transcript_json}" '
        f'--srt "{srt_path}" '
        f'--diarize')

    # 1B. Extract music features
    print("  [1B] Extracting music features with librosa...", file=sys.stderr)
    music_script = PROJECT_ROOT / "cinematography" / "music_director.py"
    run(f'{PYTHON39} "{music_script}" '
        f'--mp3 "{audio_path}" '
        f'--fps 50 --snap-to-beats '
        f'--json-out "{music_json}"')

    with open(transcript_json) as f:
        transcript = json.load(f)
    with open(music_json) as f:
        music = json.load(f)

    print(f"  Transcript: {len(transcript.get('words', []))} words, "
          f"{transcript.get('duration', 0):.1f}s", file=sys.stderr)
    print(f"  Music: {music.get('tempo', '?')} BPM, "
          f"{music.get('num_segments', '?')} segments", file=sys.stderr)

    return transcript_json, srt_path, music_json


# ── Stage 2: Script Analysis ─────────────────────────────────────────────────

def stage2_analyze(transcript_json, music_json, output_dir, ec2_ip):
    """Use LLM to analyze transcript and generate scene breakdown."""
    log(2, "SCRIPT ANALYSIS (LLM)")

    scene_json = output_dir / "scene_breakdown.json"
    analyzer_script = PROJECT_ROOT / "cinematography" / "scene_analyzer.py"

    # Use EC2's LiteLLM proxy via SSH tunnel, or local if available
    litellm_url = f"http://localhost:4000/v1"

    # Check if LiteLLM is accessible locally (SSH tunnel active)
    try:
        import requests
        resp = requests.get(f"{litellm_url}/../health", timeout=3)
        print("  LiteLLM proxy accessible locally (SSH tunnel active)", file=sys.stderr)
    except Exception:
        print("  LiteLLM not accessible locally. Setting up SSH tunnel...", file=sys.stderr)
        # Start a background SSH tunnel
        tunnel_cmd = (f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no '
                      f'-L 4000:localhost:4000 -N -f ubuntu@{ec2_ip}')
        run(tunnel_cmd, check=False)
        time.sleep(2)

    music_flag = f'--music-features "{music_json}"' if music_json else ""
    run(f'python3 "{analyzer_script}" '
        f'--transcript "{transcript_json}" '
        f'{music_flag} '
        f'--out "{scene_json}" '
        f'--litellm-url {litellm_url}')

    with open(scene_json) as f:
        breakdown = json.load(f)

    print(f"  Title: '{breakdown.get('title', 'untitled')}'", file=sys.stderr)
    print(f"  Scenes: {len(breakdown.get('scenes', []))}", file=sys.stderr)
    print(f"  Arc: {breakdown.get('emotional_arc', 'N/A')}", file=sys.stderr)
    print(f"  Mode schedule: {breakdown.get('mode_schedule', 'N/A')}", file=sys.stderr)

    return scene_json, breakdown.get("mode_schedule", "0:BEAUTY")


# ── Stage 3: Cinematography Planning ─────────────────────────────────────────

def stage3_trajectory(mode_schedule, duration_sec, ec2_ip, output_dir):
    """Export camera trajectory from trained policy on EC2."""
    log(3, "CINEMATOGRAPHY PLANNING (Isaac Lab)")

    steps = int(duration_sec * 50)  # 50 fps policy
    remote_out = f"{EC2_PATHS['output_dir']}trajectory.json"

    # Ensure output dir exists on EC2
    ssh(ec2_ip, f"mkdir -p {EC2_PATHS['output_dir']}")

    # Run trajectory export inside isaaclab container
    print(f"  Exporting {steps} steps ({duration_sec:.0f}s) with mode schedule...", file=sys.stderr)
    cmd = (
        f"sudo docker exec isaaclab bash -lc '"
        f"cd /workspace/isaaclab && "
        f"./isaaclab.sh -p {EC2_PATHS['export_script']} "
        f"--checkpoint {EC2_PATHS['checkpoint']} "
        f"--task Isaac-Cinematographer-Direct-v4 "
        f"--mode-schedule \"{mode_schedule}\" "
        f"--steps {steps} --fps 50 "
        f"--out {remote_out} --headless'"
    )
    ssh(ec2_ip, cmd)

    # Verify
    result = ssh(ec2_ip, f"python3 -c \"import json; d=json.load(open('{remote_out}')); "
                         f"print(f'Frames: {{d[\\\"num_frames\\\"]}}, FPS: {{d[\\\"fps\\\"]}}')\"")
    print(f"  {result.stdout.strip()}", file=sys.stderr)

    return remote_out


# ── Stage 4: Visual Production ───────────────────────────────────────────────

def stage4_render(trajectory_remote, quality, duration_sec, ec2_ip, output_dir):
    """Render animation in Blender EEVEE on EC2."""
    log(4, "VISUAL PRODUCTION (Blender EEVEE)")

    preset = QUALITY_PRESETS[quality]
    remote_mp4 = f"{EC2_PATHS['output_dir']}render.mp4"

    total_frames = int(duration_sec * preset["fps"])
    est_time = total_frames * 0.7 / 60  # ~0.7s per frame estimate
    print(f"  Rendering {total_frames} frames @ {preset['width']}x{preset['height']} "
          f"(est. {est_time:.0f} min)...", file=sys.stderr)

    cmd = (
        f"blender45 --background --python {EC2_PATHS['render_script']} -- "
        f"--character {EC2_PATHS['character']} "
        f"--trajectory {trajectory_remote} "
        f"--hdri-dir {EC2_PATHS['hdri_dir']} "
        f"--lighting-preset AUTO "
        f"--out {remote_mp4} "
        f"--width {preset['width']} --height {preset['height']} "
        f"--fps {preset['fps']} --engine EEVEE "
        f"--samples {preset['samples']}"
    )
    ssh(ec2_ip, cmd)

    # Verify output
    result = ssh(ec2_ip, f"ls -lh {remote_mp4}", check=False)
    print(f"  {result.stdout.strip()}", file=sys.stderr)

    return remote_mp4


# ── Stage 5: Post-Production ─────────────────────────────────────────────────

def stage5_composite(render_remote, audio_path, srt_path, ec2_ip, output_dir):
    """Composite final video with audio + subtitles on EC2."""
    log(5, "POST-PRODUCTION (ffmpeg)")

    remote_audio = f"{EC2_PATHS['output_dir']}audio.mp3"
    remote_srt = f"{EC2_PATHS['output_dir']}subtitles.srt"
    remote_final = f"{EC2_PATHS['output_dir']}final.mp4"
    remote_nosubs = f"{EC2_PATHS['output_dir']}final_nosubs.mp4"

    # Upload audio and SRT to EC2
    scp_to_ec2(ec2_ip, audio_path, remote_audio)
    scp_to_ec2(ec2_ip, str(srt_path), remote_srt)

    # Version without subtitles (clean)
    print("  [5A] Compositing video + audio (clean version)...", file=sys.stderr)
    ssh(ec2_ip, (
        f"ffmpeg -y -i {render_remote} -i {remote_audio} "
        f"-c:v libx264 -crf 20 -preset medium "
        f"-c:a aac -b:a 192k "
        f"-map 0:v -map 1:a -shortest "
        f"{remote_nosubs}"
    ))

    # Version with burned-in subtitles
    print("  [5B] Burning in subtitles...", file=sys.stderr)
    ssh(ec2_ip, (
        f"ffmpeg -y -i {render_remote} -i {remote_audio} "
        f"-vf \"subtitles={remote_srt}:force_style='FontSize=22,PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,Outline=2,Shadow=1'\" "
        f"-c:v libx264 -crf 20 -preset medium "
        f"-c:a aac -b:a 192k "
        f"-map 0:v -map 1:a -shortest "
        f"{remote_final}"
    ))

    return remote_final, remote_nosubs


# ── Stage 6: Quality & Delivery ──────────────────────────────────────────────

def stage6_deliver(remote_final, remote_nosubs, ec2_ip, output_dir, scene_breakdown):
    """Download results, extract thumbnails, generate cost report."""
    log(6, "QUALITY & DELIVERY")

    # Download final videos
    local_final = output_dir / "final_with_subtitles.mp4"
    local_nosubs = output_dir / "final_clean.mp4"

    print("  Downloading final videos...", file=sys.stderr)
    scp_from_ec2(ec2_ip, remote_final, str(local_final))
    scp_from_ec2(ec2_ip, remote_nosubs, str(local_nosubs))

    # Extract hero thumbnails (one per unique mode in the scene breakdown)
    thumbs_dir = output_dir / "thumbnails"
    thumbs_dir.mkdir(exist_ok=True)

    scenes = scene_breakdown.get("scenes", [])
    seen_modes = set()
    for scene in scenes:
        mode = scene["mode"]
        if mode not in seen_modes:
            seen_modes.add(mode)
            # Extract frame at midpoint of this scene
            mid_time = (scene["start_time"] + scene["end_time"]) / 2
            thumb_path = thumbs_dir / f"{mode.lower()}_frame.png"
            run(f'ffmpeg -y -ss {mid_time:.1f} -i "{local_final}" '
                f'-frames:v 1 -q:v 2 "{thumb_path}"', check=False)

    # Cost report
    cost_report = {
        "deepgram_transcription": 0.04,
        "llm_scene_analysis": 0.002,
        "ec2_compute_hours": 0,  # will be filled by caller
        "ec2_cost_per_hour": 1.006,
        "total_api_cost": 0.042,
        "notes": "EC2 compute cost depends on render duration. Draft ~2h, Final ~4h.",
    }
    with open(output_dir / "cost_report.json", "w") as f:
        json.dump(cost_report, f, indent=2)

    # Summary
    print(f"\n  Delivery package at: {output_dir}/", file=sys.stderr)
    print(f"  - final_with_subtitles.mp4", file=sys.stderr)
    print(f"  - final_clean.mp4", file=sys.stderr)
    print(f"  - subtitles.srt", file=sys.stderr)
    print(f"  - scene_breakdown.json", file=sys.stderr)
    print(f"  - thumbnails/ ({len(seen_modes)} mode frames)", file=sys.stderr)
    print(f"  - cost_report.json", file=sys.stderr)

    return local_final


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Table Read to Cinema — one audio file becomes a cinematic animation")
    parser.add_argument("--audio", required=True, help="Input audio file (MP3/WAV)")
    parser.add_argument("--output-dir", required=True, help="Output directory for all artifacts")
    parser.add_argument("--ec2-ip", required=True, help="EC2 public IP address")
    parser.add_argument("--quality", default="draft", choices=["draft", "standard", "final"],
                        help="Render quality preset (default: draft)")
    parser.add_argument("--skip-render", action="store_true",
                        help="Skip stages 4-6 (just do audio analysis + scene breakdown)")
    parser.add_argument("--skip-transcribe", action="store_true",
                        help="Skip stage 1 (reuse existing transcript.json in output-dir)")
    parser.add_argument("--skip-analyze", action="store_true",
                        help="Skip stage 2 (reuse existing scene_breakdown.json)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # Stage 1: Audio Intelligence
    if args.skip_transcribe:
        transcript_json = output_dir / "transcript.json"
        srt_path = output_dir / "subtitles.srt"
        music_json = output_dir / "music_features.json"
        print("  Skipping Stage 1 (using existing files)", file=sys.stderr)
    else:
        transcript_json, srt_path, music_json = stage1_transcribe(args.audio, output_dir)

    # Get duration from transcript
    with open(transcript_json) as f:
        duration_sec = json.load(f).get("duration", 90)

    # Stage 2: Script Analysis
    if args.skip_analyze:
        scene_json = output_dir / "scene_breakdown.json"
        with open(scene_json) as f:
            breakdown = json.load(f)
        mode_schedule = breakdown.get("mode_schedule", "0:BEAUTY")
        print("  Skipping Stage 2 (using existing scene_breakdown.json)", file=sys.stderr)
    else:
        scene_json, mode_schedule = stage2_analyze(
            transcript_json, music_json, output_dir, args.ec2_ip)
        with open(scene_json) as f:
            breakdown = json.load(f)

    print(f"\n  Mode schedule: {mode_schedule}", file=sys.stderr)

    if args.skip_render:
        elapsed = time.time() - start_time
        print(f"\n  Stages 1-2 complete in {elapsed:.0f}s. "
              f"Skipping render (--skip-render).", file=sys.stderr)
        print(f"  Scene breakdown: {scene_json}", file=sys.stderr)
        print(f"  Subtitles: {srt_path}", file=sys.stderr)
        return

    # Stage 3: Trajectory Export
    trajectory_remote = stage3_trajectory(mode_schedule, duration_sec, args.ec2_ip, output_dir)

    # Stage 4: Render
    render_remote = stage4_render(trajectory_remote, args.quality, duration_sec,
                                  args.ec2_ip, output_dir)

    # Stage 5: Composite
    final_remote, nosubs_remote = stage5_composite(
        render_remote, args.audio, srt_path, args.ec2_ip, output_dir)

    # Stage 6: Deliver
    local_final = stage6_deliver(final_remote, nosubs_remote, args.ec2_ip,
                                 output_dir, breakdown)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  COMPLETE — {elapsed/60:.1f} minutes", file=sys.stderr)
    print(f"  Final video: {local_final}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
