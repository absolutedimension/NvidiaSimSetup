"""
Skybox Environment Renderer — 3D room background from HDRI.

Projects an equirectangular HDRI image as a spherical environment,
with a slowly orbiting camera for parallax depth effect.

Uses ModernGL for GPU-accelerated rendering.

Requires: pip install moderngl numpy Pillow
"""

import os
import math
import subprocess
import numpy as np

SKYBOX_DIR = os.path.join(os.path.dirname(__file__), "..", "skyboxes")

SKYBOX_TEMPLATES = {
    "tech_lab": {
        "name": "Tech Lab",
        "desc": "Dark room, blue monitors, neon accents",
        "hdri": "tech_lab.jpg",
        "camera_speed": 0.3,
        "tint": (0.7, 0.8, 1.0),
    },
    "modern_classroom": {
        "name": "Modern Classroom",
        "desc": "Clean room, whiteboard, warm lighting",
        "hdri": "classroom.jpg",
        "camera_speed": 0.2,
        "tint": (1.0, 0.95, 0.9),
    },
    "cosmic_space": {
        "name": "Cosmic Space",
        "desc": "Stars, galaxies, nebulae",
        "hdri": "cosmic.jpg",
        "camera_speed": 0.1,
        "tint": (0.8, 0.7, 1.0),
    },
    "concert_stage": {
        "name": "Concert Stage",
        "desc": "Arena with spotlights",
        "hdri": "hero_hdri.jpg",
        "camera_speed": 0.25,
        "tint": (1.0, 0.85, 0.7),
    },
    "cozy_studio": {
        "name": "Cozy Studio",
        "desc": "Bookshelf, desk lamp, warm wood",
        "hdri": "intimate_hdri.jpg",
        "camera_speed": 0.15,
        "tint": (1.0, 0.9, 0.8),
    },
    "minimalist_white": {
        "name": "Minimalist White",
        "desc": "Clean infinite white with soft shadows",
        "hdri": None,
        "camera_speed": 0.1,
        "tint": (1.0, 1.0, 1.0),
        "solid_color": (0.95, 0.95, 0.97),
    },
}


def render_skybox_video(
    skybox_name="tech_lab",
    hdri_path=None,
    output_path="/tmp/skybox_bg.mp4",
    duration=30.0,
    fps=30,
    width=1920,
    height=1080,
    camera_speed=None,
    blur_amount=0.3,
):
    """
    Render an HDRI skybox environment as a video with camera orbit.

    For skyboxes without HDRI, generates a gradient/solid background
    with subtle camera movement via color shifting.
    """
    import moderngl
    from PIL import Image

    template = SKYBOX_TEMPLATES.get(skybox_name, SKYBOX_TEMPLATES["tech_lab"])
    if camera_speed is None:
        camera_speed = template.get("camera_speed", 0.2)

    # Try to find HDRI
    if hdri_path is None and template.get("hdri"):
        # Check multiple locations
        candidates = [
            os.path.join(SKYBOX_DIR, template["hdri"]),
            os.path.join("/home/ubuntu/audio_pipeline/voice_library", template["hdri"]),
            os.path.join("/Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/stage_design/hdri", template["hdri"]),
        ]
        for c in candidates:
            if os.path.exists(c):
                hdri_path = c
                break

    total_frames = int(duration * fps)
    tint = template.get("tint", (1.0, 1.0, 1.0))

    if hdri_path and os.path.exists(hdri_path):
        return _render_with_hdri(hdri_path, output_path, total_frames, fps, width, height, camera_speed, tint, blur_amount)
    else:
        return _render_gradient(template, output_path, total_frames, fps, width, height, camera_speed)


def _render_gradient(template, output_path, total_frames, fps, width, height, camera_speed):
    """Render a gradient/solid background with subtle movement."""
    from PIL import Image, ImageDraw

    solid = template.get("solid_color", (0.05, 0.03, 0.08))
    tint = template.get("tint", (1.0, 1.0, 1.0))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", output_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    print(f"Rendering gradient skybox: {total_frames} frames")

    for frame in range(total_frames):
        t = frame / fps
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Subtle color shift over time
        shift = math.sin(t * camera_speed * 0.5) * 0.02
        for y in range(height):
            frac = y / height
            r = int(255 * (solid[0] + shift + frac * 0.02) * tint[0])
            g = int(255 * (solid[1] + shift * 0.5 + frac * 0.01) * tint[1])
            b = int(255 * (solid[2] + shift * 1.5 + frac * 0.03) * tint[2])
            r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        proc.stdin.write(img.tobytes())

        if frame % (fps * 5) == 0:
            print(f"  Frame {frame}/{total_frames}")

    proc.stdin.close()
    proc.wait()
    return {"path": output_path, "duration": total_frames / fps, "frames": total_frames}


def _render_with_hdri(hdri_path, output_path, total_frames, fps, width, height, camera_speed, tint, blur_amount):
    """Render HDRI equirectangular projection with camera orbit."""
    import moderngl
    from PIL import Image

    # Load HDRI
    hdri_img = Image.open(hdri_path).convert("RGB")
    # Downscale for performance (we blur it anyway)
    max_w = 2048
    if hdri_img.width > max_w:
        ratio = max_w / hdri_img.width
        hdri_img = hdri_img.resize((max_w, int(hdri_img.height * ratio)), Image.LANCZOS)

    # Apply blur for depth-of-field effect
    if blur_amount > 0:
        from PIL import ImageFilter
        blur_radius = int(blur_amount * 10)
        hdri_img = hdri_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    hdri_data = np.array(hdri_img).astype(np.float32) / 255.0

    # Create OpenGL context
    ctx = moderngl.create_standalone_context(backend="egl")

    vertex_shader = """
    #version 330
    in vec2 in_vert;
    out vec2 v_uv;
    void main() {
        gl_Position = vec4(in_vert, 0.0, 1.0);
        v_uv = in_vert * 0.5 + 0.5;
    }
    """

    fragment_shader = """
    #version 330
    precision highp float;
    uniform sampler2D u_hdri;
    uniform float u_time;
    uniform float u_camera_speed;
    uniform vec3 u_tint;
    uniform vec2 u_resolution;
    in vec2 v_uv;
    out vec4 fragColor;

    void main() {
        vec2 uv = v_uv;

        // Camera orbit: shift the horizontal lookup
        float orbit = u_time * u_camera_speed * 0.02;
        uv.x = fract(uv.x + orbit);

        // Subtle vertical breathing
        uv.y += sin(u_time * 0.1) * 0.005;

        // Sample HDRI
        vec3 color = texture(u_hdri, uv).rgb;

        // Apply tint
        color *= u_tint;

        // Darken edges (vignette for depth)
        float vignette = 1.0 - 0.3 * length(v_uv - vec2(0.5));
        color *= vignette;

        // Slight desaturation for background feel
        float gray = dot(color, vec3(0.299, 0.587, 0.114));
        color = mix(vec3(gray), color, 0.7);

        fragColor = vec4(color, 1.0);
    }
    """

    prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4"))
    vao = ctx.simple_vertex_array(prog, vbo, "in_vert")

    # Upload HDRI as texture
    tex = ctx.texture((hdri_img.width, hdri_img.height), 3, (hdri_data * 255).astype(np.uint8).tobytes())
    tex.use(0)
    prog["u_hdri"].value = 0

    fbo = ctx.framebuffer(color_attachments=[ctx.texture((width, height), 3)])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", output_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    print(f"Rendering HDRI skybox: {total_frames} frames ({hdri_path})")

    for frame in range(total_frames):
        t = frame / fps

        prog["u_time"].value = t
        prog["u_camera_speed"].value = camera_speed
        prog["u_tint"].value = tint
        prog["u_resolution"].value = (float(width), float(height))

        fbo.use()
        ctx.clear(0.0, 0.0, 0.0)
        vao.render(moderngl.TRIANGLE_STRIP)

        data = fbo.color_attachments[0].read()
        rows = [data[i * width * 3:(i + 1) * width * 3] for i in range(height)]
        flipped = b"".join(reversed(rows))
        proc.stdin.write(flipped)

        if frame % (fps * 5) == 0:
            print(f"  Frame {frame}/{total_frames}")

    proc.stdin.close()
    proc.wait()
    ctx.release()

    print(f"Skybox video saved: {output_path}")
    return {"path": output_path, "duration": total_frames / fps, "frames": total_frames}


def list_skyboxes():
    return SKYBOX_TEMPLATES
