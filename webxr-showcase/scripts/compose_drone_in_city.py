#!/usr/bin/env python3
"""
compose_drone_in_city.py — Build a tiny USDA that references both an OSM
city USD and the Crazyflie drone USD into the same Z-up world, ready for
usd_to_glb.py --inject-trajectory to bake the trained-policy animation
onto the Drone Empty in Blender.

Why a wrapper script (vs. doing this in render_drone_demo.py):
render_drone_demo.py's --minimal-usda only writes the drone half (since
the original Phase-6a pipeline expected Rivermark to be added separately
at view time). We want both in one GLB so the WebXR showcase loads a
single file.

Why --drone-scale: at OSM-city scale (~1300 m wide) a real Crazyflie
(~0.10 m) is invisible after the WebXR auto-fit-to-3m projection.
Default 200× makes the drone appear ~20 m in real coords → ~46 mm after
auto-fit → visible in VR without dominating the city.

Usage:
  python3 compose_drone_in_city.py \\
      --city /home/ubuntu/assets/cities/manhattan_times_sq/city.usd \\
      --drone-asset /home/ubuntu/cf2x.usd \\
      --drone-scale 200 \\
      --out /tmp/manhattan_drone_flight.usda
"""

import argparse
from pxr import Gf, Usd, UsdGeom


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--city", required=True, help="OSM city USD")
    ap.add_argument("--drone-asset", required=True, help="Crazyflie USD")
    ap.add_argument("--drone-scale", type=float, default=200.0,
                    help="Uniform scale on the Drone Xform (default 200 for OSM city visibility)")
    ap.add_argument("--out", required=True, help="Output USDA path")
    args = ap.parse_args()

    stage = Usd.Stage.CreateNew(args.out)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # City — referenced as-is (already Z-up + 1.0 m/u from osm_to_usd.py)
    city = UsdGeom.Xform.Define(stage, "/World/City")
    city.GetPrim().GetReferences().AddReference(args.city)

    # Drone — named "Drone" so usd_to_glb.py --drone-object Drone (default)
    # can find the imported Empty in Blender and inject F-curves onto it.
    drone = UsdGeom.Xform.Define(stage, "/World/Drone")
    drone.GetPrim().GetReferences().AddReference(args.drone_asset)
    if args.drone_scale != 1.0:
        s = float(args.drone_scale)
        drone.AddScaleOp().Set(Gf.Vec3f(s, s, s))

    stage.GetRootLayer().Save()
    print(f"[compose] wrote {args.out} (city={args.city}, drone={args.drone_asset}, scale={args.drone_scale}×)")


if __name__ == "__main__":
    main()
