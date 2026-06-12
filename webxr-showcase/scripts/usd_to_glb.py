#!/usr/bin/env python3
"""
usd_to_glb.py — Blender headless USD → GLB converter

Runs on the EC2 host. Imports the USD, decimates if requested (for Quest
performance — heavy scenes can crash mobile GPUs), bakes lights, exports
GLB with embedded textures.

Usage (from a shell with blender on PATH):
  blender --background --python usd_to_glb.py -- \
    --input  /tmp/showcases/IsaacWarehouse/IsaacWarehouse.usd \
    --output /var/www/showcase/assets/warehouse.glb \
    --decimate 0.25     # optional: reduce poly count to 25% (Quest-friendly)
    --max-texture 1024  # optional: clamp textures to 1k (Quest VRAM budget)
"""
import argparse
import json
import os
import sys

try:
    import bpy  # type: ignore
except ImportError:
    print("This must run inside blender: blender --background --python usd_to_glb.py -- ...",
          file=sys.stderr)
    sys.exit(1)


def parse_args():
    if "--" not in sys.argv:
        argv = []
    else:
        argv = sys.argv[sys.argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--decimate", type=float, default=None,
                    help="Ratio 0..1 to decimate (e.g. 0.25 = 25%% of faces)")
    ap.add_argument("--max-texture", type=int, default=None,
                    help="Clamp texture dimension (1024 recommended for Quest)")
    ap.add_argument("--animated", action="store_true",
                    help="Push USD actions to NLA strips and export as glTF animations. "
                         "Required for Unity Animated() / glTFast to play the clip.")
    ap.add_argument("--inject-trajectory", default=None,
                    help="Path to a drone trajectory JSON (per-frame t + q in Isaac Z-up). "
                         "After USD import, overrides the static frame-0 pose by writing "
                         "F-curves directly onto the named --drone-object. Required because "
                         "Blender 4.5's USD importer does NOT translate xformOp time samples "
                         "into Blender actions — only a single static pose. Implies --animated.")
    ap.add_argument("--drone-object", default="Drone",
                    help="Name of the imported Empty/Xform to animate (default: Drone)")
    return ap.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_usd(path: str):
    if not os.path.exists(path):
        sys.exit(f"USD not found: {path}")
    print(f"[usd_to_glb] Importing {path}")
    bpy.ops.wm.usd_import(filepath=path)
    n_objs = len(bpy.context.scene.objects)
    print(f"[usd_to_glb] Imported {n_objs} objects")
    if n_objs == 0:
        sys.exit("USD imported zero objects")


def decimate_all(ratio: float):
    print(f"[usd_to_glb] Decimating meshes to {ratio*100:.0f}%")
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mod = obj.modifiers.new(name="trigunai_decimate", type="DECIMATE")
        mod.ratio = ratio
        with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod.name)


def clamp_textures(max_dim: int):
    print(f"[usd_to_glb] Clamping textures to {max_dim}px")
    for img in bpy.data.images:
        if img.size[0] > max_dim or img.size[1] > max_dim:
            scale = max_dim / max(img.size[0], img.size[1])
            img.scale(int(img.size[0] * scale), int(img.size[1] * scale))


def inject_trajectory_animation(trajectory_path: str, drone_name: str):
    """Replace the imported static pose with full per-frame animation.

    Blender 4.5's USD importer reads xformOp:translate.timeSamples /
    xformOp:orient.timeSamples but only materializes the frame-0 value as
    a static transform — no Blender action or F-curves are created. This
    function reads the original trajectory JSON (Isaac Z-up, which matches
    Blender's internal frame) and writes location + rotation_quaternion
    F-curves directly onto the named object, overriding the static pose.
    The glTF exporter with export_yup=True then converts Z-up → Y-up on
    output, so the final GLB animates the drone correctly in WebXR.
    """
    if drone_name not in bpy.data.objects:
        names = sorted(o.name for o in bpy.data.objects)
        sys.exit(f"--drone-object '{drone_name}' not in imported scene. Got: {names}")

    data = json.loads(open(trajectory_path).read())
    frames = data["frames"]
    fps = int(data.get("fps", 24))
    if not frames:
        sys.exit(f"trajectory at {trajectory_path} has no frames")

    obj = bpy.data.objects[drone_name]
    for c in list(obj.constraints):
        if c.type == "TRANSFORM_CACHE":
            print(f"[usd_to_glb] removing Transform Cache constraint '{c.name}' on '{drone_name}' "
                  f"(USD time-sample driver — would override our F-curves on rotation)")
            obj.constraints.remove(c)
    obj.rotation_mode = "QUATERNION"
    obj.animation_data_clear()
    ad = obj.animation_data_create()
    action = bpy.data.actions.new(f"{drone_name}_trajectory")
    ad.action = action

    loc_curves = [action.fcurves.new(data_path="location", index=i) for i in range(3)]
    rot_curves = [action.fcurves.new(data_path="rotation_quaternion", index=i) for i in range(4)]

    for f in frames:
        i = int(f["i"])
        t = f["t"]
        q = f["q"]
        for ax in range(3):
            kf = loc_curves[ax].keyframe_points.insert(frame=i, value=float(t[ax]))
            kf.interpolation = "LINEAR"
        for ax in range(4):
            kf = rot_curves[ax].keyframe_points.insert(frame=i, value=float(q[ax]))
            kf.interpolation = "LINEAR"

    bpy.context.scene.frame_start = int(frames[0]["i"])
    bpy.context.scene.frame_end = int(frames[-1]["i"])
    bpy.context.scene.render.fps = fps
    print(f"[usd_to_glb] Injected {len(frames)} keyframes onto '{drone_name}' "
          f"(frames {frames[0]['i']}..{frames[-1]['i']} @ {fps} fps)")


def push_actions_to_nla():
    """Push every animation action to an NLA strip so the GLB exporter writes
    them as glTF animations. Required for Meta Spatial / Unity glTFast / Three.js
    to actually play the animation — without this, the action is "loose" and
    the exporter drops it.

    Mirrors the rule from GurulokInnerJourney CLAUDE_FlowArtdance_VR.md PRIMITIVE 3:
        "Action must be pushed to NLA strip in Blender NLA Editor (Push Down)"
    """
    pushed = 0
    for obj in bpy.context.scene.objects:
        ad = obj.animation_data
        if ad is None or ad.action is None:
            continue
        # Create an NLA track + strip from the active action
        track = ad.nla_tracks.new()
        track.name = f"{obj.name}_action"
        track.strips.new(name=ad.action.name, start=int(ad.action.frame_range[0]), action=ad.action)
        # Clear the active action so it doesn't double-up with the NLA strip
        ad.action = None
        pushed += 1
    print(f"[usd_to_glb] Pushed {pushed} action(s) to NLA strips")


def export_glb(path: str, animated: bool):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"[usd_to_glb] Exporting {path} (animated={animated})")
    # The animation-mode + nla_strips flags are what makes Unity's Animated()
    # component pick up the clips. For a static asset they're harmless.
    kwargs = dict(
        filepath=path,
        export_format="GLB",
        export_apply=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_animations=animated,
    )
    if animated:
        kwargs.update(
            export_animation_mode="NLA_TRACKS",
            export_nla_strips=True,
            export_frame_range=True,
        )
    bpy.ops.export_scene.gltf(**kwargs)
    size_mb = os.path.getsize(path) / 1e6
    print(f"[usd_to_glb] Wrote {path} ({size_mb:.1f} MB)")


def main():
    args = parse_args()
    clear_scene()
    import_usd(args.input)
    if args.decimate:
        decimate_all(args.decimate)
    if args.max_texture:
        clamp_textures(args.max_texture)
    animated = args.animated or args.inject_trajectory is not None
    if args.inject_trajectory:
        inject_trajectory_animation(args.inject_trajectory, args.drone_object)
    if animated:
        push_actions_to_nla()
    export_glb(args.output, animated=animated)


if __name__ == "__main__":
    main()
