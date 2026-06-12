#!/usr/bin/env python3
"""Music Director — analyzes an MP3 and generates a cinematographer mode schedule.

The MP3 becomes the director: energy, beats, and spectral features drive which
of the 6 aesthetic modes the camera should use at each moment.

Usage (standalone — generates mode schedule string):
    /Library/Developer/CommandLineTools/usr/bin/python3 music_director.py \
        --mp3 ~/Downloads/cosmic-hypnotic.mp3 \
        --duration 90 --fps 50

    Output: 0:INTIMATE,350:HERO,900:ENERGY,1600:EPIC,2800:SOLITUDE,3500:BEAUTY,...

Usage (with trajectory export — pipe into --mode-schedule):
    SCHEDULE=$(/Library/Developer/CommandLineTools/usr/bin/python3 music_director.py \
        --mp3 ~/Downloads/cosmic-hypnotic.mp3 --duration 90 --fps 50)
    # Then pass $SCHEDULE to export_cinematographer_trajectory.py --mode-schedule

Can also output a detailed JSON timeline for visualization/debugging:
    python3 music_director.py --mp3 track.mp3 --duration 90 --fps 50 --json-out timeline.json

Dependencies: librosa, numpy, soundfile (all in Python 3.9 site-packages)
"""
from __future__ import annotations

import argparse
import json
import sys

import librosa
import numpy as np


# ── Mode definitions ──────────────────────────────────────────────────────────
# Each mode has a "profile" — the ideal audio characteristics that trigger it.
# We score each analysis window against all 6 profiles and pick the best match.

MODE_NAMES = ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"]

MODE_PROFILES = {
    # (energy_range, spectral_centroid_range, beat_density_range, onset_density_range)
    # energy: 0-1 normalized RMS
    # spectral_centroid: 0-1 normalized
    # beat_density: beats per second in window
    # onset_density: onsets per second in window
    "HERO": {
        "energy": (0.55, 1.0),      # high energy — peak moments
        "spectral": (0.3, 0.7),     # mid-range spectrum — full band
        "beat_density": (1.5, 4.0), # driving beat
        "onset_density": (2.0, 8.0),# lots happening
        "description": "Peak dramatic moments, big drops, choruses",
    },
    "INTIMATE": {
        "energy": (0.0, 0.30),      # quiet
        "spectral": (0.1, 0.45),    # warm, low-mid
        "beat_density": (0.0, 1.5), # gentle or no beat
        "onset_density": (0.0, 3.0),# sparse
        "description": "Quiet intros, breakdowns, acoustic passages",
    },
    "EPIC": {
        "energy": (0.45, 0.85),     # sustained high energy
        "spectral": (0.4, 1.0),     # bright, expansive
        "beat_density": (1.0, 3.0), # steady powerful beat
        "onset_density": (3.0, 10.0),# dense but controlled
        "description": "Crescendos, builds, anthemic sections",
    },
    "ENERGY": {
        "energy": (0.50, 1.0),      # high energy
        "spectral": (0.0, 0.4),     # bass-heavy
        "beat_density": (2.0, 6.0), # fast beat
        "onset_density": (4.0, 15.0),# very dense
        "description": "Drops, bass-heavy sections, rapid percussion",
    },
    "SOLITUDE": {
        "energy": (0.0, 0.25),      # very quiet
        "spectral": (0.0, 0.35),    # dark, low
        "beat_density": (0.0, 0.8), # minimal or no beat
        "onset_density": (0.0, 1.5),# very sparse
        "description": "Silence, sparse ambience, fadeouts",
    },
    "BEAUTY": {
        "energy": (0.20, 0.55),     # moderate
        "spectral": (0.35, 0.75),   # balanced, pleasant
        "beat_density": (0.5, 2.5), # gentle groove
        "onset_density": (1.0, 5.0),# moderate activity
        "description": "Melodic passages, flowing mid-sections, harmonic richness",
    },
}


def score_mode(energy, spectral, beat_dens, onset_dens, profile):
    """Score how well audio features match a mode profile. Lower = better match."""
    def range_dist(val, lo, hi):
        if lo <= val <= hi:
            return 0.0
        return min(abs(val - lo), abs(val - hi))

    return (
        range_dist(energy, *profile["energy"]) * 2.0 +       # energy matters most
        range_dist(spectral, *profile["spectral"]) * 1.0 +
        range_dist(beat_dens, *profile["beat_density"]) * 0.8 +
        range_dist(onset_dens, *profile["onset_density"]) * 0.3
    )


def analyze_music(mp3_path, duration=None, sr=22050):
    """Extract audio features from an MP3 file.

    Returns:
        y: audio signal
        sr: sample rate
        features: dict with per-frame arrays (energy, spectral_centroid, beats, onsets)
    """
    print(f"Loading {mp3_path}...", file=sys.stderr)
    y, sr = librosa.load(mp3_path, sr=sr, duration=duration, mono=True)
    total_duration = len(y) / sr
    print(f"  Duration: {total_duration:.1f}s, SR: {sr}", file=sys.stderr)

    # RMS energy (per hop)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]

    # Spectral centroid (brightness)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]

    # Beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)

    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=512)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)

    # Normalize to 0-1
    rms_norm = rms / (rms.max() + 1e-8)
    cent_norm = cent / (cent.max() + 1e-8)

    # Frame times
    frame_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)

    if hasattr(tempo, '__len__'):
        tempo_val = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo_val = float(tempo)
    print(f"  Tempo: {tempo_val:.1f} BPM, Beats: {len(beat_times)}, Onsets: {len(onset_times)}", file=sys.stderr)

    return {
        "y": y,
        "sr": sr,
        "duration": total_duration,
        "tempo": tempo_val,
        "rms": rms_norm,
        "spectral_centroid": cent_norm,
        "beat_times": beat_times,
        "onset_times": onset_times,
        "frame_times": frame_times,
    }


def generate_mode_schedule(features, window_sec=5.0, min_segment_sec=3.0, fps=50):
    """Generate a mode schedule from audio features.

    Args:
        features: output of analyze_music()
        window_sec: analysis window size in seconds
        min_segment_sec: minimum duration before allowing a mode switch
        fps: simulation FPS (for converting time → frame steps)

    Returns:
        schedule: list of (step, mode_name) tuples
        segments: detailed segment info for JSON output
    """
    duration = features["duration"]
    rms = features["rms"]
    cent = features["spectral_centroid"]
    beat_times = features["beat_times"]
    onset_times = features["onset_times"]
    frame_times = features["frame_times"]

    # Slide a window across the track and score each position
    hop = window_sec / 2  # 50% overlap
    segments = []
    t = 0.0

    while t < duration - 0.5:
        win_end = min(t + window_sec, duration)

        # Get frames in this window
        mask = (frame_times >= t) & (frame_times < win_end)
        if not mask.any():
            t += hop
            continue

        # Average energy and spectral centroid in window
        avg_energy = float(rms[mask].mean())
        avg_spectral = float(cent[mask].mean())

        # Beat density (beats per second in window)
        beats_in_win = np.sum((beat_times >= t) & (beat_times < win_end))
        beat_dens = beats_in_win / (win_end - t)

        # Onset density
        onsets_in_win = np.sum((onset_times >= t) & (onset_times < win_end))
        onset_dens = onsets_in_win / (win_end - t)

        # Score all 6 modes
        scores = {}
        for mode_name in MODE_NAMES:
            scores[mode_name] = score_mode(
                avg_energy, avg_spectral, beat_dens, onset_dens,
                MODE_PROFILES[mode_name]
            )

        best_mode = min(scores, key=scores.get)

        segments.append({
            "time": round(t, 2),
            "step": int(t * fps),
            "mode": best_mode,
            "energy": round(avg_energy, 3),
            "spectral": round(avg_spectral, 3),
            "beat_density": round(beat_dens, 2),
            "onset_density": round(onset_dens, 2),
            "scores": {k: round(v, 3) for k, v in scores.items()},
        })

        t += hop

    # Merge consecutive segments with the same mode + enforce minimum duration
    merged = []
    for seg in segments:
        if not merged or merged[-1]["mode"] != seg["mode"]:
            # Check minimum segment duration
            if merged and (seg["time"] - merged[-1]["time"]) < min_segment_sec:
                # Too short — keep previous mode, skip this change
                continue
            merged.append(seg)

    # Convert to schedule format
    schedule = [(seg["step"], seg["mode"]) for seg in merged]

    print(f"\nMode schedule ({len(schedule)} segments):", file=sys.stderr)
    for i, (step, mode) in enumerate(schedule):
        t = step / fps
        end_t = schedule[i + 1][0] / fps if i + 1 < len(schedule) else duration
        print(f"  {t:6.1f}s → {end_t:6.1f}s  [{step:5d}] {mode:10s} ({end_t - t:.1f}s)",
              file=sys.stderr)

    return schedule, merged


def schedule_to_string(schedule):
    """Convert [(step, mode), ...] to '0:INTIMATE,350:HERO,...' format."""
    return ",".join(f"{step}:{mode}" for step, mode in schedule)


def main():
    parser = argparse.ArgumentParser(description="Music Director — MP3 → cinematographer mode schedule")
    parser.add_argument("--mp3", required=True, help="Path to MP3 file")
    parser.add_argument("--duration", type=float, default=None,
                        help="Max duration in seconds (default: full track)")
    parser.add_argument("--fps", type=float, default=50.0,
                        help="Simulation FPS for step calculation (default: 50)")
    parser.add_argument("--window", type=float, default=5.0,
                        help="Analysis window size in seconds (default: 5.0)")
    parser.add_argument("--min-segment", type=float, default=3.0,
                        help="Minimum segment duration before mode switch (default: 3.0)")
    parser.add_argument("--json-out", default=None,
                        help="Optional: save detailed timeline as JSON")
    parser.add_argument("--snap-to-beats", action="store_true",
                        help="Snap mode switches to nearest beat (more musical)")
    parser.add_argument("--force-diversity", action="store_true",
                        help="Ensure all 6 modes appear at least once (for demos)")
    args = parser.parse_args()

    features = analyze_music(args.mp3, duration=args.duration)
    schedule, segments = generate_mode_schedule(
        features,
        window_sec=args.window,
        min_segment_sec=args.min_segment,
        fps=args.fps,
    )

    # Force diversity — ensure all 6 modes appear at least once (for demos)
    if args.force_diversity:
        used_modes = {mode for _, mode in schedule}
        missing = [m for m in MODE_NAMES if m not in used_modes]
        if missing:
            print(f"\n--force-diversity: injecting missing modes: {missing}", file=sys.stderr)
            # Replace some middle segments with missing modes, keeping first and last
            replaceable = list(range(1, len(schedule) - 1))
            np.random.seed(42)
            np.random.shuffle(replaceable)
            for i, mode in enumerate(missing):
                if i < len(replaceable):
                    idx = replaceable[i]
                    old_mode = schedule[idx][1]
                    schedule[idx] = (schedule[idx][0], mode)
                    print(f"  Replaced segment {idx} ({old_mode} → {mode}) at step {schedule[idx][0]}",
                          file=sys.stderr)
                else:
                    # Not enough segments — split the longest one
                    durations = []
                    for j in range(len(schedule)):
                        end = schedule[j + 1][0] if j + 1 < len(schedule) else int(features["duration"] * args.fps)
                        durations.append(end - schedule[j][0])
                    longest = int(np.argmax(durations))
                    mid_step = schedule[longest][0] + durations[longest] // 2
                    schedule.insert(longest + 1, (mid_step, mode))
                    print(f"  Split segment {longest} and inserted {mode} at step {mid_step}",
                          file=sys.stderr)

    # Snap to nearest beat if requested
    if args.snap_to_beats and len(features["beat_times"]) > 0:
        beat_steps = (features["beat_times"] * args.fps).astype(int)
        snapped = []
        for step, mode in schedule:
            if len(beat_steps) > 0:
                nearest_idx = np.argmin(np.abs(beat_steps - step))
                snapped_step = int(beat_steps[nearest_idx])
                # Only snap if within 1 second
                if abs(snapped_step - step) < args.fps:
                    step = snapped_step
            snapped.append((step, mode))
        schedule = snapped
        print(f"\nSnapped {len(schedule)} transitions to nearest beats", file=sys.stderr)

    # Output the schedule string to stdout (for piping to export script)
    schedule_str = schedule_to_string(schedule)
    print(schedule_str)

    # Optional JSON output with full details
    if args.json_out:
        timeline = {
            "mp3": args.mp3,
            "duration": features["duration"],
            "tempo": features["tempo"],
            "fps": args.fps,
            "num_segments": len(schedule),
            "schedule_string": schedule_str,
            "schedule": [{"step": s, "time": round(s / args.fps, 2), "mode": m}
                         for s, m in schedule],
            "analysis_windows": segments,
        }
        with open(args.json_out, "w") as f:
            json.dump(timeline, f, indent=2)
        print(f"\nDetailed timeline saved to {args.json_out}", file=sys.stderr)

    # Summary stats
    print(f"\nSummary:", file=sys.stderr)
    print(f"  Track: {features['duration']:.1f}s @ {features['tempo']:.0f} BPM", file=sys.stderr)
    print(f"  Segments: {len(schedule)}", file=sys.stderr)
    mode_counts = {}
    for _, mode in schedule:
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    for mode in MODE_NAMES:
        count = mode_counts.get(mode, 0)
        print(f"    {mode:10s}: {count} segment(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
