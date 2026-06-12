#!/usr/bin/env python3
"""
city_add_colliders.py — Add static-collision APIs to an osm_to_usd.py city.

For every prim under /World/City/Building_* and /World/Ground:
  * UsdPhysics.CollisionAPI         (collision enabled)
  * UsdPhysics.MeshCollisionAPI     (approximation = convexHull — drone-friendly)

We intentionally do NOT apply RigidBodyAPI / MassAPI: the city is static
scenery the drone bumps into, not dynamic objects. Per DRONE_CLAUDE.md §4a
gotcha, RigidBodyAPI on city props at scale caused PhysX silent death in
Rivermark; the OSM city avoids that by being static-only from the start.

Convex hull is the right choice for boxy extruded footprints: PhysX has a
fast path for convex-hull-vs-convex-hull collision, and the wrapped hull
is identical to the box for rectangular buildings. For non-rectangular
footprints (L-shapes, courtyards) the hull is slightly more permissive
than the true geometry — fine for drone training where we want the policy
to give buildings a wide berth anyway.

Usage:
  python3 city_add_colliders.py --city /home/ubuntu/assets/cities/manhattan_times_sq/city.usd

Modifies the USD in place. Idempotent — safe to re-run.
"""

import argparse
import sys

from pxr import Usd, UsdGeom, UsdPhysics


def apply_collision(prim, approximation="convexHull"):
    """Apply Collision + MeshCollision APIs idempotently."""
    if not prim.IsA(UsdGeom.Mesh):
        return False
    collision = UsdPhysics.CollisionAPI.Apply(prim)
    collision.CreateCollisionEnabledAttr(True)
    mesh_col = UsdPhysics.MeshCollisionAPI.Apply(prim)
    mesh_col.CreateApproximationAttr(approximation)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--city", required=True, help="path to city.usd from osm_to_usd.py")
    ap.add_argument(
        "--approx",
        default="convexHull",
        choices=["convexHull", "convexDecomposition", "boundingCube", "triangleMesh", "none"],
        help="MeshCollisionAPI approximation; convexHull is fastest for boxy buildings",
    )
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.city)
    if stage is None:
        print(f"[colliders] ERROR: could not open {args.city}", file=sys.stderr)
        sys.exit(1)

    n_buildings = 0
    n_ground = 0
    for prim in stage.Traverse():
        path = prim.GetPath().pathString
        if path.startswith("/World/City/Building_"):
            if apply_collision(prim, approximation=args.approx):
                n_buildings += 1
        elif path == "/World/Ground":
            # Ground is a single quad — boundingCube is cheapest for an infinite-ish floor.
            if apply_collision(prim, approximation="boundingCube"):
                n_ground += 1

    stage.GetRootLayer().Save()
    print(
        f"[colliders] {n_buildings} buildings + {n_ground} ground prims "
        f"got CollisionAPI + MeshCollisionAPI(approx={args.approx})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
