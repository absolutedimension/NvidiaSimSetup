"""
Trigunaï Innovations — Cinematic Demo Video Renderer

Renders a 20-second demo video showing:
- Daphne (CC4 character) dancing on a lit stage
- An autonomous RL-trained drone camera (v5e STEADY policy) filming her
- Cinematic lighting, smooth camera work
- Text overlay for narration cues

Uses Blender 4.5 EEVEE for fast GPU rendering.

Usage:
  blender45 --background --python render_trigunaai_demo.py -- \
    --daphne /home/ubuntu/Daphne_Blender.fbx \
    --dancer /home/ubuntu/dancer_orbital_25s_v2.usda \
    --trajectory /home/ubuntu/steady_v5e_trajectory.json \
    --out /home/ubuntu/trigunaai_demo.mp4 \
    --width 1920 --height 1080 --fps 30
"""

import bpy
import json
import math
import os
import sys
import subprocess
from mathutils import Vector, Quaternion, Euler, Matrix, Color

# ── Parse args ──
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--daphne", required=True, help="Daphne FBX file")
parser.add_argument("--dancer", required=True, help="Dancer stick figure USDA (mocap source)")
parser.add_argument("--trajectory", required=True, help="v5e drone trajectory JSON")
parser.add_argument("--out", default="/home/ubuntu/trigunaai_demo.mp4")
parser.add_argument("--width", type=int, default=1920)
parser.add_argument("--height", type=int, default=1080)
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--duration", type=float, default=20.0, help="Video duration in seconds")
parser.add_argument("--engine", default="eevee", choices=["eevee", "cycles"])
parser.add_argument("--samples", type=int, default=64)
args = parser.parse_args(argv)

total_frames = int(args.duration * args.fps)
print(f"=== Trigunaï Demo Renderer ===")
print(f"Resolution: {args.width}x{args.height}, {args.fps}fps, {args.duration}s = {total_frames} frames")
print(f"Engine: {args.engine}")

# ── Clean scene ──
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = total_frames
scene.render.fps = args.fps


# ═══════════════════════════════════════════════
# SECTION 1: Load Daphne character
# ═══════════════════════════════════════════════
print("Importing Daphne FBX...")
old_objs = set(bpy.data.objects[:])
bpy.ops.import_scene.fbx(filepath=args.daphne, use_anim=False)
daphne_objs = [o for o in bpy.data.objects if o not in old_objs]

# Find the armature
daphne_arm = None
daphne_meshes = []
for obj in daphne_objs:
    if obj.type == 'ARMATURE':
        daphne_arm = obj
    elif obj.type == 'MESH':
        daphne_meshes.append(obj)

if daphne_arm:
    print(f"  Armature: {daphne_arm.name} ({len(daphne_arm.data.bones)} bones)")
    # Position Daphne at stage center
    daphne_arm.location = Vector((0, 0, 0))
    daphne_arm.scale = Vector((0.01, 0.01, 0.01))  # CC4 FBX is in cm
else:
    print("  WARNING: No armature found in Daphne FBX")

# Remove unwanted meshes (jacket, tears, etc) to keep it clean
remove_keywords = ["jacket", "tear", "tongue", "eye_occlusion", "Jacket", "Tear"]
for mesh in daphne_meshes[:]:
    if any(kw.lower() in mesh.name.lower() for kw in remove_keywords):
        bpy.data.objects.remove(mesh, do_unlink=True)
        daphne_meshes.remove(mesh)

print(f"  Kept {len(daphne_meshes)} mesh objects")


# ═══════════════════════════════════════════════
# SECTION 2: Parse mocap from dancer USDA
# ═══════════════════════════════════════════════
print("Parsing dancer mocap from USDA...")
import re

with open(args.dancer) as f:
    usda_text = f.read()

# Extract joint timeSamples for key joints
def extract_translate_samples(usda_text, joint_name):
    """Extract translate.timeSamples for a named Sphere in the USDA."""
    pattern = rf'def Sphere "{joint_name}".*?xformOp:translate\.timeSamples\s*=\s*\{{(.*?)\}}'
    match = re.search(pattern, usda_text, re.DOTALL)
    if not match:
        return {}
    samples = {}
    for line in match.group(1).strip().split('\n'):
        line = line.strip().rstrip(',')
        if ':' in line:
            parts = line.split(':', 1)
            frame_num = int(parts[0].strip())
            coords = parts[1].strip().strip('()')
            x, y, z = [float(v) for v in coords.split(',')]
            samples[frame_num] = (x, y, z)
    return samples

# Key joints from the stick figure
joint_names = ['pelvis', 'torso', 'head', 'left_hand', 'right_hand',
               'left_upper_arm', 'right_upper_arm', 'left_lower_arm', 'right_lower_arm',
               'left_thigh', 'right_thigh', 'left_shin', 'right_shin',
               'left_foot', 'right_foot']

mocap_data = {}
for jname in joint_names:
    samples = extract_translate_samples(usda_text, jname)
    if samples:
        mocap_data[jname] = samples
        print(f"  {jname}: {len(samples)} frames")

# Subsample mocap from 30fps USDA to our render fps (same in this case)
mocap_fps = 30


# ═══════════════════════════════════════════════
# SECTION 3: Animate Daphne from mocap
# ═══════════════════════════════════════════════
print("Animating Daphne from mocap data...")

# CC4 bone name mapping: stick figure joint -> CC4 bone name
JOINT_TO_CC4 = {
    'pelvis': 'CC_Base_Hip',
    'torso': 'CC_Base_Spine02',
    'head': 'CC_Base_Head',
    'left_upper_arm': 'CC_Base_L_Upperarm',
    'right_upper_arm': 'CC_Base_R_Upperarm',
    'left_lower_arm': 'CC_Base_L_Forearm',
    'right_lower_arm': 'CC_Base_R_Forearm',
    'left_hand': 'CC_Base_L_Hand',
    'right_hand': 'CC_Base_R_Hand',
    'left_thigh': 'CC_Base_L_Thigh',
    'right_thigh': 'CC_Base_R_Thigh',
    'left_shin': 'CC_Base_L_Calf',
    'right_shin': 'CC_Base_R_Calf',
    'left_foot': 'CC_Base_L_Foot',
    'right_foot': 'CC_Base_R_Foot',
}

if daphne_arm and 'pelvis' in mocap_data:
    # Get Daphne's rest pelvis position to compute offsets
    pelvis_samples = mocap_data['pelvis']
    first_frame = min(pelvis_samples.keys())
    rest_pelvis = Vector(pelvis_samples[first_frame])

    # Animate Daphne's root (armature) position from pelvis mocap
    # The USDA positions are in Y-up right-hand (already USD convention)
    for frame_num in range(total_frames):
        usda_frame = int(frame_num * (mocap_fps / args.fps))
        usda_frame = min(usda_frame, max(pelvis_samples.keys()))

        if usda_frame in pelvis_samples:
            px, py, pz = pelvis_samples[usda_frame]
            # Offset so Daphne's feet are near Y=0
            # Pelvis is around Y=0.75 in USDA, feet around Y=0
            daphne_arm.location = Vector((px - rest_pelvis[0], 0, pz - rest_pelvis[2]))
            daphne_arm.location *= 1.0  # scale already handled by armature scale
        daphne_arm.keyframe_insert(data_path="location", frame=frame_num + 1)

    print("  Daphne root animated from pelvis mocap")
else:
    print("  Skipping Daphne animation (no armature or mocap)")


# ═══════════════════════════════════════════════
# SECTION 4: Create stick-figure dancer overlay
# ═══════════════════════════════════════════════
print("Creating animated stick figure (mocap visualization)...")

# Create small spheres for joints and animate them
stick_joints = {}
joint_colors = {
    'pelvis': (0.9, 0.3, 0.2),
    'torso': (0.9, 0.5, 0.1),
    'head': (1.0, 0.9, 0.2),
    'left_hand': (0.2, 0.6, 1.0),
    'right_hand': (0.2, 0.6, 1.0),
    'left_upper_arm': (0.3, 0.7, 0.9),
    'right_upper_arm': (0.3, 0.7, 0.9),
    'left_lower_arm': (0.3, 0.7, 0.9),
    'right_lower_arm': (0.3, 0.7, 0.9),
    'left_thigh': (0.2, 0.8, 0.4),
    'right_thigh': (0.2, 0.8, 0.4),
    'left_shin': (0.2, 0.8, 0.4),
    'right_shin': (0.2, 0.8, 0.4),
    'left_foot': (0.1, 0.6, 0.3),
    'right_foot': (0.1, 0.6, 0.3),
}

for jname, samples in mocap_data.items():
    r = 0.03 if 'foot' in jname or 'shin' in jname else 0.04 if 'hand' in jname else 0.05
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0), segments=8, ring_count=6)
    joint_obj = bpy.context.active_object
    joint_obj.name = f"Stick_{jname}"

    # Emissive material
    mat = bpy.data.materials.new(name=f"StickMat_{jname}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    col = joint_colors.get(jname, (0.5, 0.5, 0.5))
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*col, 1.0)
        bsdf.inputs["Emission Color"].default_value = (*col, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 3.0
        bsdf.inputs["Roughness"].default_value = 0.2
    joint_obj.data.materials.append(mat)

    # Keyframe animation
    sorted_frames = sorted(samples.keys())
    for usda_frame in sorted_frames:
        render_frame = int(usda_frame * (args.fps / mocap_fps)) + 1
        if render_frame > total_frames:
            break
        x, y, z = samples[usda_frame]
        joint_obj.location = Vector((x, y, z))
        joint_obj.keyframe_insert(data_path="location", frame=render_frame)

    stick_joints[jname] = joint_obj

print(f"  Created {len(stick_joints)} animated stick joints")

# Create bone connections (cylinders between joints)
bone_pairs = [
    ('pelvis', 'torso'), ('torso', 'head'),
    ('torso', 'left_upper_arm'), ('left_upper_arm', 'left_lower_arm'), ('left_lower_arm', 'left_hand'),
    ('torso', 'right_upper_arm'), ('right_upper_arm', 'right_lower_arm'), ('right_lower_arm', 'right_hand'),
    ('pelvis', 'left_thigh'), ('left_thigh', 'left_shin'), ('left_shin', 'left_foot'),
    ('pelvis', 'right_thigh'), ('right_thigh', 'right_shin'), ('right_shin', 'right_foot'),
]

bone_objects = []
for a, b in bone_pairs:
    if a in stick_joints and b in stick_joints:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=1.0, location=(0, 0, 0))
        bone = bpy.context.active_object
        bone.name = f"Bone_{a}_{b}"
        # Glowing material
        mat = bpy.data.materials.new(name=f"BoneMat_{a}_{b}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.4, 0.6, 1.0, 1.0)
            bsdf.inputs["Emission Color"].default_value = (0.3, 0.5, 1.0, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 2.0
        bone.data.materials.append(mat)

        # Stretch To constraint
        stretch = bone.constraints.new('STRETCH_TO')
        stretch.target = stick_joints[b]
        bone.constraints.new('COPY_LOCATION').target = stick_joints[a]

        bone_objects.append(bone)

print(f"  Created {len(bone_objects)} bone connections")


# ═══════════════════════════════════════════════
# SECTION 5: Drone camera from v5e trajectory
# ═══════════════════════════════════════════════
print("Loading v5e STEADY trajectory...")

with open(args.trajectory) as f:
    traj_data = json.load(f)

traj_frames = traj_data["frames"]
traj_fps = traj_data.get("fps", 50)
print(f"  {len(traj_frames)} frames @ {traj_fps}fps")


def isaac_to_blender(pos):
    """Isaac Z-up (x,y,z) -> Blender Y-up (x,z,-y)"""
    return Vector((pos[0], pos[2], -pos[1]))


# Create drone visual (small blue glowing sphere + ring)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0, 0, 0), segments=16, ring_count=8)
drone_vis = bpy.context.active_object
drone_vis.name = "DroneCamera"
drone_mat = bpy.data.materials.new(name="DroneCameraMat")
drone_mat.use_nodes = True
bsdf = drone_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.5, 1.0, 1.0)
    bsdf.inputs["Emission Color"].default_value = (0.1, 0.5, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 5.0
    bsdf.inputs["Metallic"].default_value = 0.8
drone_vis.data.materials.append(drone_mat)

# Propeller ring
bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.008, location=(0, 0.02, 0))
prop_ring = bpy.context.active_object
prop_ring.name = "PropRing"
prop_ring.parent = drone_vis
prop_mat = bpy.data.materials.new(name="PropMat")
prop_mat.use_nodes = True
bsdf = prop_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Emission Color"].default_value = (0.2, 0.7, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 3.0
prop_ring.data.materials.append(prop_mat)

# Camera lens indicator (small cone)
bpy.ops.mesh.primitive_cone_add(radius1=0.04, depth=0.08, location=(0, 0, 0.1))
lens_cone = bpy.context.active_object
lens_cone.name = "CameraLens"
lens_cone.rotation_euler = Euler((math.radians(90), 0, 0))
lens_cone.parent = drone_vis
lens_mat = bpy.data.materials.new(name="LensMat")
lens_mat.use_nodes = True
bsdf = lens_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
lens_cone.data.materials.append(lens_mat)

# Sightline beam (drone to dancer)
bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=1.0, location=(0, 0, 0))
sightbeam = bpy.context.active_object
sightbeam.name = "SightBeam"
beam_mat = bpy.data.materials.new(name="BeamMat")
beam_mat.use_nodes = True
bsdf = beam_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.8, 1.0, 0.3)
    bsdf.inputs["Emission Color"].default_value = (0.1, 0.8, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.5
    bsdf.inputs["Alpha"].default_value = 0.3
beam_mat.blend_method = 'BLEND' if hasattr(beam_mat, 'blend_method') else None
sightbeam.data.materials.append(beam_mat)

# Animate drone + sightline
print("  Keyframing drone trajectory...")
for render_frame in range(1, total_frames + 1):
    # Map render frame to trajectory frame
    t = (render_frame - 1) / args.fps
    traj_idx = int(t * traj_fps)
    traj_idx = min(traj_idx, len(traj_frames) - 1)

    fr = traj_frames[traj_idx]
    dpos = isaac_to_blender(fr["drone_pos"])
    dapos = isaac_to_blender(fr["dancer_pos"])

    scene.frame_set(render_frame)

    # Drone position
    drone_vis.location = dpos
    drone_vis.keyframe_insert(data_path="location", frame=render_frame)

    # Point drone toward dancer
    look_dir = (dapos - dpos).normalized()
    if look_dir.length > 0.001:
        look_quat = look_dir.to_track_quat('-Z', 'Y')
        drone_vis.rotation_mode = 'QUATERNION'
        drone_vis.rotation_quaternion = look_quat
        drone_vis.keyframe_insert(data_path="rotation_quaternion", frame=render_frame)

    # Sightline beam
    mid = (dpos + dapos) / 2
    diff = dapos - dpos
    dist = diff.length
    sightbeam.location = mid
    sightbeam.scale = (1, 1, dist)
    direction = diff.normalized()
    rot_quat = direction.to_track_quat('Z', 'Y')
    sightbeam.rotation_mode = 'QUATERNION'
    sightbeam.rotation_quaternion = rot_quat
    sightbeam.keyframe_insert(data_path="location", frame=render_frame)
    sightbeam.keyframe_insert(data_path="scale", frame=render_frame)
    sightbeam.keyframe_insert(data_path="rotation_quaternion", frame=render_frame)

print("  Drone trajectory keyframed")


# ═══════════════════════════════════════════════
# SECTION 6: Stage environment
# ═══════════════════════════════════════════════
print("Building stage environment...")

# Reflective stage floor
bpy.ops.mesh.primitive_plane_add(size=25, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "StageFloor"
floor_mat = bpy.data.materials.new(name="StageFloorMat")
floor_mat.use_nodes = True
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.05, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.15  # Slightly reflective
floor.data.materials.append(floor_mat)

# Background wall/curtain
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 6, -8))
bg_wall = bpy.context.active_object
bg_wall.name = "BackdropWall"
bg_wall.rotation_euler = Euler((math.radians(90), 0, 0))
wall_mat = bpy.data.materials.new(name="BackdropMat")
wall_mat.use_nodes = True
bsdf = wall_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.02, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
bg_wall.data.materials.append(wall_mat)


# ═══════════════════════════════════════════════
# SECTION 7: Cinematic lighting
# ═══════════════════════════════════════════════
print("Setting up cinematic lighting...")

# Key light — warm, from upper-right front
bpy.ops.object.light_add(type='AREA', location=(4, 6, 5))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 800
key.data.size = 3.0
key.data.color = (1.0, 0.92, 0.85)  # Warm
key.rotation_euler = Euler((math.radians(-50), math.radians(20), 0))

# Fill light — cool, from left
bpy.ops.object.light_add(type='AREA', location=(-5, 4, 3))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300
fill.data.size = 4.0
fill.data.color = (0.8, 0.85, 1.0)  # Cool blue
fill.rotation_euler = Euler((math.radians(-40), math.radians(-30), 0))

# Rim/back light — strong edge separation
bpy.ops.object.light_add(type='AREA', location=(0, 5, -4))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 600
rim.data.size = 2.0
rim.data.color = (0.7, 0.85, 1.0)  # Cool
rim.rotation_euler = Euler((math.radians(-30), math.radians(180), 0))

# Spot light on dancer (stage spotlight effect)
bpy.ops.object.light_add(type='SPOT', location=(0, 8, 0))
spot = bpy.context.active_object
spot.name = "SpotlightDancer"
spot.data.energy = 2000
spot.data.color = (1.0, 0.95, 0.9)
spot.data.spot_size = math.radians(40)
spot.data.spot_blend = 0.3
spot.rotation_euler = Euler((math.radians(-90), 0, 0))  # Pointing straight down

# Ambient (world)
world = bpy.data.worlds.new("StageWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.01, 1.0)
    bg.inputs["Strength"].default_value = 0.5


# ═══════════════════════════════════════════════
# SECTION 8: Cinematic camera (audience view)
# ═══════════════════════════════════════════════
print("Setting up cinematic camera...")

# Compute scene center from stick figure
all_pelvis = mocap_data.get('pelvis', {})
if all_pelvis:
    avg_x = sum(p[0] for p in all_pelvis.values()) / len(all_pelvis)
    avg_y = sum(p[1] for p in all_pelvis.values()) / len(all_pelvis)
    avg_z = sum(p[2] for p in all_pelvis.values()) / len(all_pelvis)
    dancer_center = Vector((avg_x, avg_y, avg_z))
else:
    dancer_center = Vector((0, 0.8, 0))

print(f"  Dancer center: {dancer_center}")

# Camera tracking target at dancer center
bpy.ops.object.empty_add(type='PLAIN_AXES', location=dancer_center)
cam_target = bpy.context.active_object
cam_target.name = "CamTarget"

# Main camera — slow cinematic orbit
bpy.ops.object.camera_add(location=(5, 3, 4))
cam = bpy.context.active_object
cam.name = "CinemaCamera"
cam.data.lens = 50  # Portrait-ish focal length
cam.data.clip_start = 0.1
cam.data.clip_end = 100
cam.data.dof.use_dof = True
cam.data.dof.focus_object = cam_target
cam.data.dof.aperture_fstop = 2.8  # Shallow DOF for cinematic look

scene.camera = cam

# Smooth camera orbit: start front-right, slowly arc to front-left
# This gives a sense of movement without being distracting
orbit_radius = 7.0
orbit_height = 3.0
start_angle = math.radians(-30)  # Slightly right of center
end_angle = math.radians(30)     # Slightly left

for fi in range(1, total_frames + 1):
    t = (fi - 1) / (total_frames - 1)
    # Ease in/out (smoothstep)
    t_smooth = t * t * (3 - 2 * t)

    angle = start_angle + (end_angle - start_angle) * t_smooth
    cam_x = dancer_center.x + orbit_radius * math.sin(angle)
    cam_z = dancer_center.z + orbit_radius * math.cos(angle)
    cam_y = orbit_height + 0.3 * math.sin(t * math.pi)  # Subtle vertical

    cam.location = Vector((cam_x, cam_y, cam_z))
    cam.keyframe_insert(data_path="location", frame=fi)

# Track camera to dancer center
track = cam.constraints.new(type='TRACK_TO')
track.target = cam_target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

print("  Camera orbit animated")


# ═══════════════════════════════════════════════
# SECTION 9: Render settings
# ═══════════════════════════════════════════════
print("Configuring render settings...")

scene.render.resolution_x = args.width
scene.render.resolution_y = args.height
scene.render.resolution_percentage = 100

if args.engine == "eevee":
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 0, 0) else 'BLENDER_EEVEE'
    # EEVEE quality settings
    if hasattr(scene, 'eevee'):
        eevee = scene.eevee
        if hasattr(eevee, 'use_gtao'):
            eevee.use_gtao = True          # Ambient occlusion
        if hasattr(eevee, 'use_bloom'):
            eevee.use_bloom = True         # Glow on emissive
            eevee.bloom_threshold = 0.8
            eevee.bloom_intensity = 0.3
        if hasattr(eevee, 'use_ssr'):
            eevee.use_ssr = True           # Screen space reflections
        if hasattr(eevee, 'taa_render_samples'):
            eevee.taa_render_samples = args.samples
else:
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = args.samples

# Output to frame sequence
out_dir = os.path.dirname(args.out) or "/tmp"
frame_dir = os.path.join(out_dir, "trigunaai_frames")
os.makedirs(frame_dir, exist_ok=True)

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = os.path.join(frame_dir, "frame_")

# Color management for cinematic look
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium High Contrast'
scene.view_settings.exposure = 0.3


# ═══════════════════════════════════════════════
# SECTION 10: Render
# ═══════════════════════════════════════════════
print(f"Rendering {total_frames} frames to {frame_dir}...")
bpy.ops.render.render(animation=True)

# Encode to MP4
print("Encoding MP4 with ffmpeg...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", str(args.fps),
    "-i", os.path.join(frame_dir, "frame_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "18",        # High quality
    "-preset", "slow",   # Better compression
    "-tune", "film",     # Cinematic tuning
    args.out
]
result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"ffmpeg error: {result.stderr}")
else:
    print(f"Output: {args.out}")
    file_size = os.path.getsize(args.out)
    print(f"Size: {file_size / (1024*1024):.1f} MB")

# Cleanup
import shutil
shutil.rmtree(frame_dir, ignore_errors=True)

print("=== Done! ===")
