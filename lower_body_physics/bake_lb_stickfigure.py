#!/usr/bin/env python3
"""Bake LB rollout NPZ into a stick-figure animated GLB.

Usage (on EC2 with Blender 4.5):
    blender45 --background --python bake_lb_stickfigure.py -- \
        --input /home/ubuntu/lb5_rollout.npz \
        --output /home/ubuntu/lb5_stickfigure.glb

Creates a simple stick figure (spheres at joints, cylinders for bones)
with keyframed animation from the rollout data. Coordinate transform:
Isaac Lab Z-up → GLB Y-up (standard glTF/Blender convention).

This is for quick visual assessment of the policy's motion quality.
"""

import argparse
import sys
import math

# Parse args before bpy import (Blender convention)
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser(description="Bake LB rollout to stick figure GLB")
parser.add_argument("--input", required=True, help="Path to rollout .npz")
parser.add_argument("--output", required=True, help="Output .glb path")
parser.add_argument("--fps", type=int, default=60, help="Animation FPS")
parser.add_argument("--scale", type=float, default=1.0, help="Scale factor")
args = parser.parse_args(argv)

import bpy
import numpy as np
from mathutils import Vector, Quaternion


def isaac_to_blender_pos(pos):
    """Body data has Y-up (empirically verified from frame 0 body positions:
    head_Y=1.25, feet_Y=0.1 → Y is height). Blender is Z-up.
    Transform: (x, y, z) → (x, z, y)  i.e. swap Y↔Z.
    Blender's glTF exporter then converts Z-up → Y-up for the viewer.
    """
    return Vector((pos[0], pos[2], pos[1]))


def isaac_to_blender_quat(q):
    """Quaternion wxyz with Y↔Z axis swap.
    (qw, qx, qy, qz) → (qw, qx, qz, qy)
    """
    return Quaternion((q[0], q[1], q[3], q[2]))


# Bone connections for the humanoid skeleton
# (parent_body_idx, child_body_idx) — indices into body_names
BONES = [
    (1, 0),   # pelvis → torso
    (0, 2),   # torso → head
    (0, 3),   # torso → right_upper_arm
    (0, 4),   # torso → left_upper_arm
    (3, 7),   # right_upper_arm → right_lower_arm
    (4, 8),   # left_upper_arm → left_lower_arm
    (7, 11),  # right_lower_arm → right_hand
    (8, 12),  # left_lower_arm → left_hand
    (1, 5),   # pelvis → right_thigh
    (1, 6),   # pelvis → left_thigh
    (5, 9),   # right_thigh → right_shin
    (6, 10),  # left_thigh → left_shin
    (9, 13),  # right_shin → right_foot
    (10, 14), # left_shin → left_foot
]


def main():
    # Load NPZ
    data = np.load(args.input, allow_pickle=True)
    body_pos = data["body_positions"]  # (T, 15, 3)
    body_rot = data["body_rotations"]  # (T, 15, 4) wxyz
    body_names = list(data["body_names"])
    fps = int(data["fps"])
    T, num_bodies, _ = body_pos.shape
    print(f"[bake] Loaded: {T} frames, {num_bodies} bodies, {fps} fps")
    print(f"[bake] Duration: {T/fps:.1f}s")
    print(f"[bake] Bodies: {body_names}")

    # Clear scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Set FPS
    bpy.context.scene.render.fps = fps
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = T

    # Create materials
    mat_joint = bpy.data.materials.new("JointMaterial")
    mat_joint.use_nodes = True
    bsdf = mat_joint.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.2, 0.6, 1.0, 1.0)  # Blue
    bsdf.inputs["Metallic"].default_value = 0.3

    mat_bone = bpy.data.materials.new("BoneMaterial")
    mat_bone.use_nodes = True
    bsdf = mat_bone.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)  # Light gray
    bsdf.inputs["Metallic"].default_value = 0.1

    mat_foot = bpy.data.materials.new("FootMaterial")
    mat_foot.use_nodes = True
    bsdf = mat_foot.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.4, 0.2, 1.0)  # Orange
    bsdf.inputs["Metallic"].default_value = 0.3

    # Center motion: subtract mean XZ position (Y is height in this data)
    mean_x = body_pos[:, 0, 0].mean()  # mean root X
    mean_z = body_pos[:, 0, 2].mean()  # mean root Z (forward axis)
    body_pos[:, :, 0] -= mean_x
    body_pos[:, :, 2] -= mean_z
    print(f"[bake] Centered motion (shifted X={mean_x:.2f}, Z={mean_z:.2f}, Y/height unchanged)")

    # Create joint spheres — large enough to see clearly
    joint_objects = []
    for i, name in enumerate(body_names):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06 * args.scale, segments=12, ring_count=8)
        obj = bpy.context.active_object
        obj.name = f"Joint_{name}"

        # Assign material
        if "foot" in name:
            obj.data.materials.append(mat_foot)
        else:
            obj.data.materials.append(mat_joint)

        joint_objects.append(obj)

    # Create bone cylinders (will be repositioned each frame via empties)
    # For simplicity, use empties parented to joints — bones are just visual
    # We'll keyframe the joint positions and the bones can be derived

    # Keyframe all joint positions
    print(f"[bake] Keyframing {T} frames for {num_bodies} bodies...")
    for frame_idx in range(T):
        bpy.context.scene.frame_set(frame_idx + 1)

        for body_idx in range(num_bodies):
            obj = joint_objects[body_idx]
            pos = body_pos[frame_idx, body_idx]
            rot = body_rot[frame_idx, body_idx]

            # Convert coords
            bl_pos = isaac_to_blender_pos(pos) * args.scale
            bl_rot = isaac_to_blender_quat(rot)

            obj.location = bl_pos
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = bl_rot

            obj.keyframe_insert(data_path="location", frame=frame_idx + 1)
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame_idx + 1)

        if frame_idx % 120 == 0:
            print(f"  Frame {frame_idx}/{T}")

    # Create bone cylinders connecting joints
    # For each bone, create a cylinder that stretches between the two joints
    # We'll use a mesh with two vertices and a skin modifier for clean look
    # Simpler: just use thin cylinders repositioned per frame

    print(f"[bake] Creating {len(BONES)} bones...")
    bone_objects = []
    for parent_idx, child_idx in BONES:
        parent_name = body_names[parent_idx]
        child_name = body_names[child_idx]

        # Create a thin cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025 * args.scale, depth=1.0, vertices=8)
        obj = bpy.context.active_object
        obj.name = f"Bone_{parent_name}_to_{child_name}"
        obj.data.materials.append(mat_bone)
        bone_objects.append((obj, parent_idx, child_idx))

    # Keyframe bone positions and orientations
    print(f"[bake] Keyframing bones...")
    for frame_idx in range(T):
        bpy.context.scene.frame_set(frame_idx + 1)

        for obj, pidx, cidx in bone_objects:
            p1 = isaac_to_blender_pos(body_pos[frame_idx, pidx]) * args.scale
            p2 = isaac_to_blender_pos(body_pos[frame_idx, cidx]) * args.scale

            # Position at midpoint
            mid = (p1 + p2) / 2
            obj.location = mid

            # Orient along bone direction
            direction = p2 - p1
            bone_len = direction.length
            if bone_len < 1e-6:
                bone_len = 0.01

            # Scale Z to match bone length (cylinder default depth=1.0)
            obj.scale = (1.0, 1.0, bone_len)

            # Rotation: align Z-axis with bone direction
            up = Vector((0, 0, 1))
            if direction.normalized().cross(up).length > 1e-6:
                rot = up.rotation_difference(direction.normalized())
                obj.rotation_mode = "QUATERNION"
                obj.rotation_quaternion = rot
            else:
                obj.rotation_mode = "QUATERNION"
                obj.rotation_quaternion = Quaternion((1, 0, 0, 0))

            obj.keyframe_insert(data_path="location", frame=frame_idx + 1)
            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame_idx + 1)
            obj.keyframe_insert(data_path="scale", frame=frame_idx + 1)

        if frame_idx % 120 == 0:
            print(f"  Frame {frame_idx}/{T}")

    # No ground plane — it makes viewers zoom too far out

    # Push all actions to NLA strips (required for GLB animation export)
    print(f"[bake] Pushing actions to NLA strips...")
    for obj in joint_objects + [bo[0] for bo in bone_objects]:
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            track = obj.animation_data.nla_tracks.new()
            track.name = action.name
            strip = track.strips.new(action.name, int(action.frame_range[0]), action)
            obj.animation_data.action = None

    # Export GLB
    print(f"[bake] Exporting {args.output}...")
    bpy.ops.export_scene.gltf(
        filepath=args.output,
        export_format="GLB",
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_nla_strips=True,
        export_apply=False,
    )

    file_size_mb = __import__("os").path.getsize(args.output) / (1024 * 1024)
    print(f"[bake] Done! {args.output} ({file_size_mb:.1f} MB)")
    print(f"  {T} frames @ {fps} fps = {T/fps:.1f}s")
    print(f"  {num_bodies} joint spheres + {len(BONES)} bone cylinders + ground plane")


if __name__ == "__main__":
    main()
