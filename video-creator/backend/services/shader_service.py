"""
Shader Renderer Service — GPU-accelerated GLSL shader backgrounds.

Renders audio-reactive shader effects frame-by-frame using ModernGL.
Each frame receives audio analysis data (RMS, FFT, onset detection).

Requires: pip install moderngl numpy librosa

Usage:
    from services.shader_service import render_shader_video
    render_shader_video(
        shader_name="energy_pulse",
        audio_path="/path/to/voice.wav",
        output_path="/path/to/output.mp4",
        duration=30.0,
        fps=30,
    )
"""

import os
import struct
import subprocess
import numpy as np

SHADER_DIR = os.path.join(os.path.dirname(__file__), "..", "shaders")

# Available shader templates
SHADER_TEMPLATES = {
    # === LEARNING SERIES (ultra slow, elegant, education-themed) ===
    "learn_focus": {
        "file": "learn_focus.glsl",
        "name": "Learn Focus",
        "desc": "Deep dark with subtle notebook grid, soft center glow, ultra slow flow",
        "mood": "teaching",
        "colors": "deep navy, barely-there blue",
        "category": "learning",
    },
    "knowledge_flow": {
        "file": "knowledge_flow.glsl",
        "name": "Knowledge Flow",
        "desc": "Vertical data streams rising ultra slowly, floating dots like ideas",
        "mood": "explanation",
        "colors": "deep blue streams, subtle cyan dots",
        "category": "learning",
    },
    "circuit_mind": {
        "file": "circuit_mind.glsl",
        "name": "Circuit Mind",
        "desc": "Ultra subtle circuit board traces with traveling light pulses",
        "mood": "tech_teaching",
        "colors": "deep tech blue, node highlights",
        "category": "learning",
    },
    "deep_ocean": {
        "file": "deep_ocean.glsl",
        "name": "Deep Ocean",
        "desc": "Underwater caustics, gentle light shaft, floating particles",
        "mood": "contemplative",
        "colors": "ocean blue, soft light from above",
        "category": "learning",
    },
    "sacred_geometry": {
        "file": "sacred_geometry.glsl",
        "name": "Sacred Geometry",
        "desc": "Flower of life, concentric circles, radial spokes — all ultra slow",
        "mood": "wisdom",
        "colors": "deep indigo, subtle golden geometry",
        "category": "learning",
    },
    # === ORIGINAL SERIES (faster, more energetic — for trailers/CTAs) ===
    "energy_pulse": {
        "file": "energy_pulse.glsl",
        "name": "Energy Pulse",
        "desc": "Light rings pulsing with speech",
        "mood": "excited",
        "colors": "blue → purple",
        "category": "cinematic",
    },
    "calm_glow": {
        "file": "calm_glow.glsl",
        "name": "Calm Glow",
        "desc": "Soft drifting orbs, gentle color shifts",
        "mood": "calm",
        "colors": "warm purple → cool blue",
        "category": "cinematic",
    },
    "cosmic_drift": {
        "file": "cosmic_drift.glsl",
        "name": "Cosmic Drift",
        "desc": "Stars, nebulae, slow rotation",
        "mood": "inspirational",
        "colors": "deep space purple",
        "category": "cinematic",
    },
    "neon_grid": {
        "file": "neon_grid.glsl",
        "name": "Neon Grid",
        "desc": "Retro-futuristic perspective grid",
        "mood": "tech",
        "colors": "cyan ↔ pink neon",
        "category": "cinematic",
    },
    "warm_bokeh": {
        "file": "warm_bokeh.glsl",
        "name": "Warm Bokeh",
        "desc": "Out-of-focus golden lights",
        "mood": "personal",
        "colors": "amber, gold, soft pink",
        "category": "cinematic",
    },
    "sunlit_leaves": {
        "file": "sunlit_leaves.glsl",
        "name": "Sunlit Leaves",
        "desc": "Sage plaster wall with drifting dappled sunlight and gently swaying "
                "leaf-shadow branches — calm, organic, original (no photos).",
        "mood": "calm",
        "colors": "sage green, warm sunlight",
        "category": "learning",
    },
    # === TRIGUN STUDIO IMPORTS (ported from studio.trigunai.com) ===
    "vocal_melt": {
        "file": "vocal_melt.glsl",
        "name": "Vocal Melt",
        "desc": "Liquid paint that melts and drips with the voice — streaks, pooling, "
                "wet rim-light, chroma split along the melt axis. Premium intro look.",
        "mood": "premium",
        "colors": "cosmic violet, teal highlights",
        "category": "cinematic",
    },
}


def analyze_audio(audio_path, fps=30, duration=None):
    """
    Analyze audio file and extract per-frame features.

    Returns:
        dict with arrays: rms, bass, treble, onset — each length = total_frames
    """
    import librosa

    y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=duration)

    if duration is None:
        duration = len(y) / sr

    total_frames = int(duration * fps)
    hop = int(sr / fps)

    # RMS (volume envelope)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]

    # Spectral features
    S = np.abs(librosa.stft(y, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr)

    # Bass: 20-300 Hz
    bass_mask = (freqs >= 20) & (freqs <= 300)
    bass = np.mean(S[bass_mask, :], axis=0) if bass_mask.any() else np.zeros(S.shape[1])

    # Treble: 2000-8000 Hz
    treble_mask = (freqs >= 2000) & (freqs <= 8000)
    treble = np.mean(S[treble_mask, :], axis=0) if treble_mask.any() else np.zeros(S.shape[1])

    # Onset detection
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, units="frames")
    onset = np.zeros(len(onset_env))
    for f in onset_frames:
        if f < len(onset):
            onset[f] = 1.0

    # Normalize to 0-1
    def norm(x):
        mx = np.max(x) if np.max(x) > 0 else 1.0
        return np.clip(x / mx, 0, 1)

    rms = norm(rms)
    bass = norm(bass)
    treble = norm(treble)

    # Pad/trim all to total_frames
    def pad(x, n):
        if len(x) >= n:
            return x[:n]
        return np.pad(x, (0, n - len(x)), mode="edge")

    return {
        "rms": pad(rms, total_frames).astype(np.float32),
        "bass": pad(bass, total_frames).astype(np.float32),
        "treble": pad(treble, total_frames).astype(np.float32),
        "onset": pad(onset, total_frames).astype(np.float32),
        "duration": duration,
        "total_frames": total_frames,
    }


def render_shader_video(
    shader_name="energy_pulse",
    audio_path=None,
    output_path="/tmp/shader_bg.mp4",
    duration=30.0,
    fps=30,
    width=1920,
    height=1080,
):
    """
    Render a shader to video with audio-reactive uniforms.

    Args:
        shader_name: Key from SHADER_TEMPLATES
        audio_path: Path to voice WAV (for audio analysis). If None, no reactivity.
        output_path: Where to save MP4
        duration: Video duration in seconds
        fps: Frame rate
        width, height: Resolution

    Returns:
        {"path": str, "duration": float, "frames": int}
    """
    import moderngl

    # Load shader
    template = SHADER_TEMPLATES.get(shader_name, SHADER_TEMPLATES["energy_pulse"])
    shader_path = os.path.join(SHADER_DIR, template["file"])
    with open(shader_path) as f:
        fragment_shader = f.read()

    # Analyze audio
    total_frames = int(duration * fps)
    if audio_path and os.path.exists(audio_path):
        audio_data = analyze_audio(audio_path, fps=fps, duration=duration)
        total_frames = audio_data["total_frames"]
        duration = audio_data["duration"]
    else:
        audio_data = {
            "rms": np.full(total_frames, 0.3, dtype=np.float32),
            "bass": np.full(total_frames, 0.2, dtype=np.float32),
            "treble": np.full(total_frames, 0.1, dtype=np.float32),
            "onset": np.zeros(total_frames, dtype=np.float32),
        }

    # Create headless OpenGL context
    ctx = moderngl.create_standalone_context(backend="egl")

    # Vertex shader (fullscreen quad)
    vertex_shader = """
    #version 330
    in vec2 in_vert;
    void main() {
        gl_Position = vec4(in_vert, 0.0, 1.0);
    }
    """

    prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    vertices = np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")
    vbo = ctx.buffer(vertices)
    vao = ctx.simple_vertex_array(prog, vbo, "in_vert")

    # Create framebuffer
    fbo = ctx.framebuffer(
        color_attachments=[ctx.texture((width, height), 3)]
    )

    # Set uniform locations
    uniforms = {}
    for name in ["u_time", "u_resolution", "u_rms", "u_bass", "u_treble", "u_onset"]:
        try:
            uniforms[name] = prog[name]
        except KeyError:
            pass

    # Pipe to ffmpeg
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    print(f"Rendering shader '{shader_name}': {total_frames} frames @ {width}x{height}")

    for frame in range(total_frames):
        t = frame / fps

        # Set uniforms
        if "u_time" in uniforms:
            uniforms["u_time"].value = t
        if "u_resolution" in uniforms:
            uniforms["u_resolution"].value = (float(width), float(height))
        if "u_rms" in uniforms:
            uniforms["u_rms"].value = float(audio_data["rms"][frame])
        if "u_bass" in uniforms:
            uniforms["u_bass"].value = float(audio_data["bass"][frame])
        if "u_treble" in uniforms:
            uniforms["u_treble"].value = float(audio_data["treble"][frame])
        if "u_onset" in uniforms:
            uniforms["u_onset"].value = float(audio_data["onset"][frame])

        # Render
        fbo.use()
        ctx.clear(0.0, 0.0, 0.0)
        vao.render(moderngl.TRIANGLE_STRIP)

        # Read pixels and flip (OpenGL is bottom-up)
        data = fbo.color_attachments[0].read()
        # Flip vertically
        rows = [data[i * width * 3:(i + 1) * width * 3] for i in range(height)]
        flipped = b"".join(reversed(rows))
        ffmpeg_proc.stdin.write(flipped)

        if frame % (fps * 5) == 0:
            print(f"  Frame {frame}/{total_frames} ({frame * 100 // total_frames}%)")

    ffmpeg_proc.stdin.close()
    ffmpeg_proc.wait()
    ctx.release()

    print(f"Shader video saved: {output_path}")
    return {"path": output_path, "duration": duration, "frames": total_frames}


def list_shaders():
    """Return available shader templates."""
    return SHADER_TEMPLATES


if __name__ == "__main__":
    # Quick test
    result = render_shader_video(
        shader_name="energy_pulse",
        duration=10.0,
        fps=30,
        width=960,
        height=540,
        output_path="/tmp/test_shader.mp4",
    )
    print(f"Test: {result}")
