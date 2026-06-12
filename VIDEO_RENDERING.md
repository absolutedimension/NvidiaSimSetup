# Video Rendering Reference (Master)

> **All skills and agents that produce video MUST read this file.**
> Canonical location: `NvidiaSimSetup/VIDEO_RENDERING.md`
> Last updated: 2026-05-25

---

## TL;DR Decision Table

| Need | Method | Speed | Command |
|---|---|---|---|
| **Fast preview / iteration** | Blender EEVEE | **0.33 s/frame** (18x faster) | `blender45 --background --python render_blender_drone_pov.py -- --engine eevee` |
| **Production quality** | Blender Cycles + OptiX | ~1.5 s/frame (4x faster) | `blender45 --background --python render_blender_drone_pov.py -- --engine cycles --samples 64` |
| **Legacy (DO NOT USE)** | OVRTX API | ~6 s/frame (slow) | `python3 render_drone_demo.py` or `render_combined.py` |

**Default choice: Blender EEVEE.** Use Cycles+OptiX only for final hero renders or when ray-traced reflections/GI matter.

**NEVER use OVRTX for new work** unless you specifically need its material shading pipeline (NVIDIA MDL materials that Blender can't read). OVRTX is 2.5x slower due to HTTP API round-trip overhead.

---

## Method 1: Blender GPU Rendering (PREFERRED)

### Why this is fastest

Blender renders directly on the A10G GPU with zero network overhead. OVRTX requires: base64-encode USD (CPU) -> HTTP POST (network) -> parse USD (CPU) -> render (GPU) -> base64-encode PNG (CPU) -> HTTP response (network) -> decode PNG (CPU). Blender skips all of that.

### Hardware available

| Resource | Value |
|---|---|
| GPU | NVIDIA A10G (24 GB VRAM) |
| Blender | 4.5.5 LTS at `/opt/blender45` (symlink: `blender45`) |
| CUDA | Available (general GPU compute) |
| OptiX | Available (RTX ray tracing + AI denoising) |
| EEVEE Next | Available (realtime rasterizer, GPU-accelerated) |

### Engines comparison

| Engine | Speed (1280x720) | Speed (800x450) | Quality | Best for |
|---|---|---|---|---|
| **EEVEE Next** | **0.33 s/frame** (after shader warmup) | ~0.15 s/frame | Good (rasterizer) | Preview, iteration, most renders |
| **Cycles + OptiX** | ~2-4 s/frame (32 spp) | ~1-2 s/frame | Excellent (path tracing + AI denoise) | Hero renders, reflections, GI |
| **Cycles + OptiX** | ~5-8 s/frame (128 spp) | ~3-5 s/frame | Best | Final product video |

### Master script: `render_blender_drone_pov.py`

Location: `cinematography/render_blender_drone_pov.py` (repo) + `/home/ubuntu/render_blender_drone_pov.py` (EC2)

```bash
# Upload to EC2 if needed
scp -i ~/.ssh/trigunai_key.pem cinematography/render_blender_drone_pov.py ubuntu@$EC2_IP:/home/ubuntu/

# EEVEE fast render (25s video in ~30 min at 1280x720)
blender45 --background --python /home/ubuntu/render_blender_drone_pov.py -- \
  --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
  --trajectory /tmp/cinematographer_v4_trajectory.json \
  --out /home/ubuntu/output.mp4 \
  --engine eevee \
  --width 1280 --height 720 --fps 30

# Cycles RTX ray-traced render (25s video in ~45 min at 1280x720)
blender45 --background --python /home/ubuntu/render_blender_drone_pov.py -- \
  --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
  --trajectory /tmp/cinematographer_v4_trajectory.json \
  --out /home/ubuntu/output_hq.mp4 \
  --engine cycles --samples 64 \
  --width 1280 --height 720 --fps 30

# Quick preview (25s video in ~12 min at 640x360)
blender45 --background --python /home/ubuntu/render_blender_drone_pov.py -- \
  --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
  --trajectory /tmp/cinematographer_v4_trajectory.json \
  --out /home/ubuntu/preview.mp4 \
  --engine eevee \
  --width 640 --height 360 --fps 30
```

### Arguments

| Arg | Default | Description |
|---|---|---|
| `--dancer` | (required) | Dancer USDA with timeSampled animated stick figure |
| `--trajectory` | (required) | Drone trajectory JSON (`{"frames": [{"i", "t", "q"}], "fps": 30}`) |
| `--drone` | None | Optional drone USD/GLB model (creates placeholder cube if absent) |
| `--out` | `/tmp/drone_pov.mp4` | Output MP4 path |
| `--engine` | `eevee` | `eevee` or `cycles` |
| `--width` | 1280 | Render width in pixels |
| `--height` | 720 | Render height in pixels |
| `--fps` | 30 | Frames per second |
| `--samples` | 32 | Cycles samples per pixel (ignored for EEVEE) |
| `--start` | 0 | First frame index |
| `--end` | -1 | Last frame index (-1 = all) |

### Camera behavior

- Camera is **parented to the drone** (rides along with it)
- `TRACK_TO` constraint always aims at the dancer's pelvis
- 24mm focal length (wide angle, cinematic FOV)
- Result: **drone-POV footage** — what the real drone camera would see

### Scene setup (automatic)

- Dancer imported from USDA (stick figure: spheres + cylinders)
- Drone animated along trajectory (position + quaternion keyframes)
- Sun light (key, energy 3.0) + area light (fill, energy 200)
- 30m floor plane with dark material
- Dark blue-black world background

### Output

- PNG frames in `{out_dir}/blender_frames/frame_XXXX.png`
- Final MP4 via ffmpeg (H.264, CRF 18, yuv420p)
- Console output includes timing: `X frames in Ys (Z s/frame)`

---

## Method 2: OVRTX API (LEGACY)

Use only when you need NVIDIA MDL material rendering or when the scene was built specifically for the OVRTX pipeline.

### API contract

```python
# Endpoint
POST http://localhost:8001/render

# Payload
{
    "url": "data:application/octet-stream;base64,{base64_encoded_usda}",
    "force_render": True,
    "render_settings": {
        "camera_paths": ["/World/Camera"],
        "frame_range": {"start": 0, "end": 49},
        "camera_parameters": {"width": 800, "height": 450},
        "sensors": None,
        "apply_background_mask": False
    }
}

# Response structure
body["images"][str(frame_num)]["/World/Camera"]["images"]  # base64 PNG
```

### Critical OVRTX rules

1. **URL field is `url`** (not `usd_url`)
2. **Data URI scheme**: `data:application/octet-stream;base64,{b64}` (not `application/usd`)
3. **Batch max 50 frames** per request (>120 frames timeout at 600s)
4. **Send the FULL USDA once**, vary `frame_range` per batch (do NOT generate per-batch sub-USDs)
5. **Camera must be a UsdGeom.Camera prim path** (not direction shortcuts like `+x`)
6. **Container mounts**: Host `/tmp` -> container `/host_tmp`. USD references must use `/host_tmp/` paths
7. **Cold start**: ~6 min after container restart before `gpu_initialized: true`
8. **After failed renders**: restart container to clear daemon state

### Key scripts (legacy)

| Script | Purpose |
|---|---|
| `render_drone_demo.py` | Single-drone render with OVRTX |
| `render_combined.py` | Dancer + drone combined scene via OVRTX |
| `render_dancer_mp4.py` | Dancer-only orbital camera via OVRTX |
| `render_cinematographer_mp4.py` | Cinematographer trajectory render via OVRTX |

---

## Method 3: ffmpeg Direct Encode (no 3D rendering)

For when you already have frames (from either method above) or need to re-encode:

```bash
# Encode PNGs to MP4
ffmpeg -y -framerate 30 -start_number 0 \
  -i /path/to/frames/frame_%04d.png \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p \
  output.mp4

# Re-encode at different resolution
ffmpeg -y -i input.mp4 -vf scale=1920:1080 -c:v libx264 -crf 18 output_1080p.mp4

# Extract frames from MP4
ffmpeg -i input.mp4 -q:v 2 frames/frame_%04d.jpg

# Extract keyframes for VLM evaluation
ffmpeg -i input.mp4 -vf "select='not(mod(n\,125))'" -vsync vfr keyframe_%02d.jpg
```

---

## Trajectory JSON format (standard)

All rendering scripts consume this format:

```json
{
    "frames": [
        {"i": 0, "t": [x, y, z], "q": [qx, qy, qz, qw]},
        {"i": 1, "t": [x, y, z], "q": [qx, qy, qz, qw]},
        ...
    ],
    "fps": 30
}
```

- `t`: translation in USD Y-up right-hand coords (already remapped from Isaac Sim Z-up)
- `q`: quaternion in `[qx, qy, qz, qw]` order (Isaac convention)
- `i`: frame index (0-based)

### Coordinate remap (Isaac Sim -> USD)

Applied in `export_cinematographer_trajectory.py` BEFORE writing JSON:
- Position: `(x, y, z)_isaac -> (x, z, -y)_usd`
- Quaternion: `(qx, qy, qz, qw)_isaac -> (qx, qz, -qy, qw)_usd`

---

## Dancer USDA format (standard)

Animated stick figure with timeSampled positions:

- 15 spheres (joints): pelvis, torso, head, L/R shoulder/elbow/hand, L/R hip/knee/foot
- 13-14 cylinders (bones): connecting adjacent joints
- All with `xformOp:translate.timeSamples` per frame
- USD Y-up, meters, 30 fps default
- Joint colors: pelvis=red-orange, torso=gold, head=yellow, limbs vary by side

Built by: `cinematography/bake_dancer_usda.py`

---

## Benchmarks (measured on EC2 g5.2xlarge, A10G)

| Scenario | Method | Resolution | Frames | Wall time | Per frame | Speedup vs OVRTX |
|---|---|---|---|---|---|---|
| Drone-only USDA | OVRTX | 800x450 | 750 | 75 min | 6.0 s | 1x |
| Dancer+drone USDA | OVRTX | 800x450 | 750 | 75 min | 6.1 s | 1x |
| Dancer+drone scene | EEVEE | 640x360 | 10 | 27 s | 2.66 s | 2.3x (cold) |
| **Dancer+drone scene** | **EEVEE** | **1280x720** | **750** | **4.2 min** | **0.33 s** | **18x** |
| Dancer+drone scene | Cycles+OptiX 32spp | 1280x720 | (est.) | ~20 min | ~1.5 s | 4x |

**Key insight:** EEVEE's first 10 frames are slow (~2.7s/frame) due to shader compilation.
Once shaders are cached, throughput drops to **0.33 s/frame** — the GPU is doing pure rasterization
with zero HTTP/encoding overhead. This is the production method for all video rendering.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Blender: `usd_open not found` | Wrong operator name in Blender 4.5 | Use `bpy.ops.wm.usd_import()` |
| EEVEE: `BLENDER_EEVEE_NEXT` error | Blender version difference | Fall back to `BLENDER_EEVEE` |
| Cycles: no GPU detected | OptiX not refreshed | Call `prefs.refresh_devices()` + `compute_device_type = 'OPTIX'` |
| OVRTX: `Image is not available` | Referenced USD missing from `/tmp` | Restore: `cp /home/ubuntu/assets/.../ /tmp/` |
| OVRTX: timeout on large batch | >50 frames per request | Reduce batch size to 50 |
| Drone invisible in render | `/tmp/cf2x.usd` wiped on EC2 stop | Copy from EBS: `cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/` |
| Black video from Cycles | No lights in scene | Script auto-adds sun + area light |
| ffmpeg: `start_number` wrong | Blender 1-indexes frames | Use `--start_number 1` |

---

## Adding a new rendering script

When writing a new script that produces video:

1. **Use Blender EEVEE** as default engine (fastest, good quality)
2. **Accept `--engine eevee|cycles`** flag so user can upgrade quality
3. **Accept `--width`, `--height`, `--fps`** for flexibility
4. **Output PNG frames first**, then ffmpeg to MP4 (allows resume on crash)
5. **Print per-frame timing** so user knows ETA
6. **Follow the trajectory JSON contract** above for any drone/camera animation
7. **Set `scene.cycles.device = 'GPU'`** and refresh OptiX devices for Cycles
8. **Set `PYTHONUNBUFFERED=1`** or `python3 -u` when running headless (log buffering)
9. **Use `nohup` + background** for long renders so SSH disconnect doesn't kill it
