"""
Blender headless renderer: Drone-POV cinematography video.

Camera rides with the drone, always looking at the dancer.
Uses EEVEE (fast rasterizer) or Cycles+OptiX (RTX ray tracing).

Usage:
  blender45 --background --python render_blender_drone_pov.py -- \
    --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
    --trajectory /tmp/cinematographer_v4_trajectory.json \
    --drone /home/ubuntu/assets/Crazyflie/cf2x.usd \
    --out /home/ubuntu/drone_pov.mp4 \
    --engine eevee \
    --width 1280 --height 720
"""

import bpy
import json
import math
import os
import sys
import subprocess
from pathlib import Path
from mathutils import Vector, Quaternion, Euler

# ── Parse args after "--" ──
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dancer", required=True, help="Dancer USDA file")
parser.add_argument("--trajectory", required=True, help="Drone trajectory JSON")
parser.add_argument("--drone", default=None, help="Drone USD/GLB model (optional)")
parser.add_argument("--out", default="/tmp/drone_pov.mp4", help="Output MP4")
parser.add_argument("--engine", default="eevee", choices=["eevee", "cycles"], help="Render engine")
parser.add_argument("--width", type=int, default=1280)
parser.add_argument("--height", type=int, default=720)
parser.add_argument("--samples", type=int, default=32, help="Cycles samples (ignored for eevee)")
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--end", type=int, default=-1)
args = parser.parse_args(argv)

print(f"=== Blender Drone-POV Renderer ===")
print(f"Engine: {args.engine}, Resolution: {args.width}x{args.height}")

# ── Clean default scene ──
bpy.ops.wm.read_factory_settings(use_empty=True)

# ── Load trajectory ──
with open(args.trajectory) as f:
    traj_data = json.load(f)

frames = traj_data["frames"]
traj_fps = traj_data.get("fps", 30)
total_frames = len(frames)
if args.end < 0:
    args.end = total_frames - 1

print(f"Trajectory: {total_frames} frames @ {traj_fps} fps")

# Isaac Sim coords are already USD-remapped in the trajectory JSON
# t = [x, y, z] in USD Y-up space
# q = [qx, qy, qz, qw] in Isaac convention

# ── Import dancer USDA ──
print(f"Importing dancer: {args.dancer}")
bpy.ops.wm.usd_import(filepath=args.dancer)

# Find the dancer pelvis to track
dancer_pelvis = None
for obj in bpy.data.objects:
    if "pelvis" in obj.name.lower():
        dancer_pelvis = obj
        break

if not dancer_pelvis:
    # Create a tracking target at average dancer position
    print("No pelvis found, creating tracking empty at dancer center")
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(frames[0]["t"][0], frames[0]["t"][2] * 0.15, -frames[0]["t"][1] * 0.15))
    dancer_pelvis = bpy.context.active_object
    dancer_pelvis.name = "DancerTarget"

print(f"Dancer tracking target: {dancer_pelvis.name} at {dancer_pelvis.location}")

# Find dancer center for reference
dancer_center = dancer_pelvis.location.copy()
print(f"Dancer center: {dancer_center}")

# ── Create drone empty (trajectory carrier) ──
bpy.ops.object.empty_add(type='ARROWS', location=(0, 0, 0))
drone_empty = bpy.context.active_object
drone_empty.name = "DroneCarrier"

# ── Import drone model if provided ──
drone_model = None
if args.drone and os.path.exists(args.drone):
    print(f"Importing drone model: {args.drone}")
    # Save current objects to identify new ones
    old_objs = set(bpy.data.objects[:])

    if args.drone.endswith('.glb') or args.drone.endswith('.gltf'):
        bpy.ops.import_scene.gltf(filepath=args.drone)
    elif args.drone.endswith('.usd') or args.drone.endswith('.usda') or args.drone.endswith('.usdc'):
        bpy.ops.wm.usd_import(filepath=args.drone)

    new_objs = [o for o in bpy.data.objects if o not in old_objs]
    if new_objs:
        # Parent all new objects to drone_empty
        for obj in new_objs:
            if obj.parent is None:
                obj.parent = drone_empty
        drone_model = new_objs[0]
        print(f"Drone model loaded: {len(new_objs)} objects")
else:
    # Create a simple drone placeholder (small cube)
    bpy.ops.mesh.primitive_cube_add(size=0.15, location=(0, 0, 0))
    drone_model = bpy.context.active_object
    drone_model.name = "DronePlaceholder"
    drone_model.parent = drone_empty
    # Give it a dark material
    mat = bpy.data.materials.new(name="DroneMat")
    mat.diffuse_color = (0.2, 0.2, 0.2, 1.0)
    drone_model.data.materials.append(mat)

# ── Animate drone along trajectory ──
print("Baking drone trajectory keyframes...")
scene = bpy.context.scene
scene.frame_start = args.start
scene.frame_end = args.end
scene.render.fps = args.fps

for fr in frames[args.start:args.end + 1]:
    frame_idx = fr["i"]
    tx, ty, tz = fr["t"]  # Already in USD Y-up coords
    qx, qy, qz, qw = fr["q"]

    scene.frame_set(frame_idx)

    # Position
    drone_empty.location = Vector((tx, ty, tz))
    drone_empty.keyframe_insert(data_path="location", frame=frame_idx)

    # Rotation (convert from xyzw to Blender's wxyz quaternion)
    drone_empty.rotation_mode = 'QUATERNION'
    drone_empty.rotation_quaternion = Quaternion((qw, qx, qy, qz))
    drone_empty.keyframe_insert(data_path="rotation_quaternion", frame=frame_idx)

print(f"  Keyframed {args.end - args.start + 1} frames")

# ── Create camera (drone POV) ──
bpy.ops.object.camera_add(location=(0, 0, 0))
cam = bpy.context.active_object
cam.name = "DronePOVCamera"

# Camera rides with the drone
cam.parent = drone_empty
# Offset slightly below drone center (camera hangs under the drone)
cam.location = Vector((0, -0.05, 0))

# Camera data settings
cam.data.lens = 24  # Wide angle for cinematic look
cam.data.clip_start = 0.1
cam.data.clip_end = 100

# Add Track To constraint — camera always looks at the dancer
track = cam.constraints.new(type='TRACK_TO')
track.target = dancer_pelvis
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam
print(f"Camera parented to drone, tracking {dancer_pelvis.name}")

# ── Lighting ──
# Key light (sun)
bpy.ops.object.light_add(type='SUN', location=(5, 10, 8))
sun = bpy.context.active_object
sun.name = "KeyLight"
sun.data.energy = 3.0
sun.data.angle = math.radians(10)
sun.rotation_euler = Euler((math.radians(-45), math.radians(15), 0))

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-3, 5, 4))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 200
fill.data.size = 3.0

# ── Floor ──
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "StageFloor"
mat = bpy.data.materials.new(name="FloorMat")
mat.diffuse_color = (0.15, 0.15, 0.18, 1.0)
mat.roughness = 0.8
floor.data.materials.append(mat)

# ── World background ──
world = bpy.data.worlds.new(name="DarkStage")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)  # Dark blue-black
bg.inputs[1].default_value = 1.0
scene.world = world

# ── Render settings ──
scene.render.resolution_x = args.width
scene.render.resolution_y = args.height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

out_dir = Path(args.out).parent / "blender_frames"
out_dir.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(out_dir / "frame_")

if args.engine == "cycles":
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.refresh_devices()
    for device in prefs.devices:
        device.use = True
    scene.cycles.device = 'GPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    print(f"Cycles + OptiX, {args.samples} samples, OptiX denoiser")
else:
    # Try EEVEE Next (4.5+), fall back to legacy EEVEE
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        print("Using EEVEE Next")
    except:
        scene.render.engine = 'BLENDER_EEVEE'
        print("Using EEVEE legacy")
    eevee = scene.eevee
    try:
        eevee.taa_render_samples = 64
    except:
        pass
    try:
        eevee.use_gtao = True
    except:
        pass
    try:
        eevee.use_ssr = True
    except:
        pass
    print(f"EEVEE configured")

# ── Render animation ──
print(f"\nRendering frames {args.start}..{args.end} to {out_dir}/")
print(f"Resolution: {args.width}x{args.height}, FPS: {args.fps}")

import time
t0 = time.time()
bpy.ops.render.render(animation=True)
t1 = time.time()

rendered_count = args.end - args.start + 1
elapsed = t1 - t0
print(f"\n=== Render complete ===")
print(f"  {rendered_count} frames in {elapsed:.1f}s ({elapsed/rendered_count:.2f}s/frame)")

# ── Encode MP4 ──
print(f"\nEncoding MP4: {args.out}")
frame_pattern = str(out_dir / "frame_%04d.png")

# Check actual frame naming
sample_frames = list(out_dir.glob("frame_*.png"))
if sample_frames:
    # Blender names frames like frame_0001.png
    frame_pattern = str(out_dir / "frame_%04d.png")
    start_number = args.start + 1  # Blender 1-indexes by default
else:
    print("WARNING: No rendered frames found!")
    sys.exit(1)

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(args.fps),
    "-start_number", str(start_number),
    "-i", frame_pattern,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    args.out,
]
print(f"  ffmpeg: {' '.join(cmd)}")
subprocess.run(cmd, check=True)

mp4_size = os.path.getsize(args.out)
duration = rendered_count / args.fps
print(f"\nDone: {args.out} ({mp4_size // 1024} KB, {rendered_count} frames @ {args.fps} fps = {duration:.1f}s)")
print(f"Total pipeline time: {elapsed:.1f}s render + encoding")
