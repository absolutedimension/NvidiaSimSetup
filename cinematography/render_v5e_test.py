"""
Quick Blender render for v5e STEADY cinematographer trajectory.
Renders a bird's-eye + side view of drone (blue sphere) tracking dancer (green sphere).

Usage:
  blender45 --background --python render_v5e_test.py -- \
    --trajectory /home/ubuntu/steady_v5e_trajectory.json \
    --out /home/ubuntu/v5e_steady_test.mp4 \
    --fps 30 --width 960 --height 540
"""

import bpy
import json
import math
import os
import sys
import subprocess
from mathutils import Vector, Quaternion, Euler, Matrix

argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--trajectory", required=True)
parser.add_argument("--out", default="/tmp/v5e_test.mp4")
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--width", type=int, default=960)
parser.add_argument("--height", type=int, default=540)
parser.add_argument("--subsample", type=int, default=2,
                    help="Take every Nth frame from trajectory (50fps traj -> 25fps video at subsample=2)")
args = parser.parse_args(argv)

# ── Load trajectory ──
with open(args.trajectory) as f:
    traj_data = json.load(f)

all_frames = traj_data["frames"]
traj_fps = traj_data.get("fps", 50)
coord_sys = traj_data.get("coordinate_system", "isaac_sim_z_up")

# Subsample frames
frames = all_frames[::args.subsample]
num_frames = len(frames)
print(f"Loaded {len(all_frames)} frames, subsampled to {num_frames} @ ~{traj_fps/args.subsample:.0f}fps")


def isaac_to_blender_pos(pos):
    """Isaac Sim Z-up (x,y,z) -> Blender Y-up (x,z,-y)"""
    x, y, z = pos
    return Vector((x, -y, z))


def isaac_to_blender_quat(q):
    """Isaac Sim quat [qx,qy,qz,qw] -> Blender Quaternion (w,x,z,-y)"""
    qx, qy, qz, qw = q
    return Quaternion((qw, qx, -qy, qz))


# ── Clean scene ──
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ── Materials ──
def make_mat(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.4
    return mat

drone_mat = make_mat("DroneMat", (0.1, 0.4, 0.9, 1.0))      # Blue
dancer_mat = make_mat("DancerMat", (0.1, 0.8, 0.3, 1.0))     # Green
trail_mat = make_mat("TrailMat", (0.3, 0.5, 1.0, 0.3))       # Light blue
floor_mat = make_mat("FloorMat", (0.12, 0.12, 0.15, 1.0))    # Dark grey
glow_mat = make_mat("GlowMat", (1.0, 0.9, 0.2, 1.0))        # Yellow for "hold" indicator

# ── Drone sphere ──
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, 0), segments=16, ring_count=8)
drone_obj = bpy.context.active_object
drone_obj.name = "Drone"
drone_obj.data.materials.append(drone_mat)

# Direction indicator (small cone pointing forward from drone)
bpy.ops.mesh.primitive_cone_add(radius1=0.06, depth=0.15, location=(0, 0, 0))
cone = bpy.context.active_object
cone.name = "DroneDir"
cone.rotation_euler = Euler((math.radians(90), 0, 0))
cone.parent = drone_obj
cone.data.materials.append(drone_mat)

# ── Dancer sphere ──
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0), segments=16, ring_count=8)
dancer_obj = bpy.context.active_object
dancer_obj.name = "Dancer"
dancer_obj.data.materials.append(dancer_mat)

# ── Hold quality indicator (ring around drone, scales with hold_quality) ──
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.02, location=(0, 0, 0))
hold_ring = bpy.context.active_object
hold_ring.name = "HoldRing"
hold_ring.data.materials.append(glow_mat)
hold_ring.parent = drone_obj

# ── Floor ──
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# ── Trail curve (shows drone path) ──
curve_data = bpy.data.curves.new(name="TrailCurve", type='CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.015
spline = curve_data.splines.new('NURBS')
# Pre-allocate points (subsample for trail to keep it manageable)
trail_step = max(1, num_frames // 200)
trail_positions = [isaac_to_blender_pos(frames[i]["drone_pos"]) for i in range(0, num_frames, trail_step)]
spline.points.add(len(trail_positions) - 1)
for i, pos in enumerate(trail_positions):
    spline.points[i].co = (pos.x, pos.y, pos.z, 1.0)
trail_obj = bpy.data.objects.new("Trail", curve_data)
bpy.context.collection.objects.link(trail_obj)
trail_obj.data.materials.append(trail_mat)

# ── Sightline (dashed line drone -> dancer) ──
# We'll use a simple cylinder scaled per frame
bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=1.0, location=(0, 0, 0))
sightline = bpy.context.active_object
sightline.name = "Sightline"
sight_mat = make_mat("SightMat", (1.0, 1.0, 1.0, 0.3))
sightline.data.materials.append(sight_mat)

# ── Lighting ──
# Key light
bpy.ops.object.light_add(type='SUN', location=(5, 8, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.angle = math.radians(15)
sun.rotation_euler = Euler((math.radians(-40), math.radians(10), 0))

# Fill light
bpy.ops.object.light_add(type='AREA', location=(-4, 5, 6))
fill = bpy.context.active_object
fill.data.energy = 150
fill.data.size = 4.0

# Ambient (world)
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.3

# ── Camera ──
# Compute scene center and extent from trajectory
all_drone_pos = [isaac_to_blender_pos(f["drone_pos"]) for f in frames]
all_dancer_pos = [isaac_to_blender_pos(f["dancer_pos"]) for f in frames]
all_pos = all_drone_pos + all_dancer_pos

cx = sum(p.x for p in all_pos) / len(all_pos)
cy = sum(p.y for p in all_pos) / len(all_pos)
cz = sum(p.z for p in all_pos) / len(all_pos)

span_x = max(p.x for p in all_pos) - min(p.x for p in all_pos)
span_y = max(p.y for p in all_pos) - min(p.y for p in all_pos)
span_z = max(p.z for p in all_pos) - min(p.z for p in all_pos)
span = max(span_x, span_y, span_z, 3.0)

# Elevated side view — slightly above and to the side
cam_dist = span * 1.8
cam_x = cx + cam_dist * 0.6
cam_y = cy - cam_dist * 0.8
cam_z = cz + cam_dist * 0.5

bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
cam = bpy.context.active_object
cam.name = "MainCamera"
cam.data.lens = 35
cam.data.clip_start = 0.1
cam.data.clip_end = 200

# Point camera at scene center
track = cam.constraints.new(type='TRACK_TO')
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(cx, cy, cz))
target = bpy.context.active_object
target.name = "CamTarget"
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam
print(f"Camera at ({cam_x:.1f}, {cam_y:.1f}, {cam_z:.1f}), looking at ({cx:.1f}, {cy:.1f}, {cz:.1f}), span={span:.1f}")

# ── Render settings ──
scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 0, 0) else 'BLENDER_EEVEE'
scene.render.resolution_x = args.width
scene.render.resolution_y = args.height
scene.render.fps = args.fps
scene.frame_start = 0
scene.frame_end = num_frames - 1

# Output to image sequence first, then ffmpeg
out_dir = os.path.dirname(args.out) or "/tmp"
frame_dir = os.path.join(out_dir, "v5e_frames")
os.makedirs(frame_dir, exist_ok=True)

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(frame_dir, "frame_")

# ── Keyframe animation ──
print(f"Keyframing {num_frames} frames...")

for fi, fr in enumerate(frames):
    scene.frame_set(fi)

    # Drone position
    dpos = isaac_to_blender_pos(fr["drone_pos"])
    drone_obj.location = dpos
    drone_obj.keyframe_insert(data_path="location", frame=fi)

    # Drone rotation
    dquat = isaac_to_blender_quat(fr["drone_quat"])
    drone_obj.rotation_mode = 'QUATERNION'
    drone_obj.rotation_quaternion = dquat
    drone_obj.keyframe_insert(data_path="rotation_quaternion", frame=fi)

    # Dancer position
    dapos = isaac_to_blender_pos(fr["dancer_pos"])
    dancer_obj.location = dapos
    dancer_obj.keyframe_insert(data_path="location", frame=fi)

    # Sightline: cylinder from drone to dancer
    midpoint = (dpos + dapos) / 2
    diff = dapos - dpos
    dist = diff.length
    sightline.location = midpoint
    sightline.scale = (1, 1, dist)
    # Orient cylinder along the line between drone and dancer
    direction = diff.normalized()
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.999:
        up = Vector((1, 0, 0))
    rot_quat = direction.to_track_quat('Z', 'Y')
    sightline.rotation_mode = 'QUATERNION'
    sightline.rotation_quaternion = rot_quat
    sightline.keyframe_insert(data_path="location", frame=fi)
    sightline.keyframe_insert(data_path="scale", frame=fi)
    sightline.keyframe_insert(data_path="rotation_quaternion", frame=fi)

    # Hold quality ring scale
    hq = fr.get("hold_quality", 0)
    ring_scale = 0.5 + hq * 1.5  # Scale 0.5 -> 2.0 based on hold quality
    hold_ring.scale = (ring_scale, ring_scale, ring_scale)
    hold_ring.keyframe_insert(data_path="scale", frame=fi)

print("Keyframing done.")

# ── Render ──
print(f"Rendering {num_frames} frames to {frame_dir}...")
bpy.ops.render.render(animation=True)

# ── Encode to MP4 ──
print(f"Encoding MP4...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", str(args.fps),
    "-i", os.path.join(frame_dir, "frame_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "20",
    "-preset", "fast",
    args.out
]
subprocess.run(ffmpeg_cmd, check=True)
print(f"Output: {args.out}")

# Cleanup frames
import shutil
shutil.rmtree(frame_dir, ignore_errors=True)
print("Done!")
