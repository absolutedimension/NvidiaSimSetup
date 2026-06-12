#!/usr/bin/env python3
"""
osm_to_usd.py — Pull OpenStreetMap building footprints for a lat/lon/radius
and write a Z-up USD city ready for Isaac Lab drone training.

Each building tagged in OSM becomes a single extruded Mesh prim under
/World/City/Building_<osm_id>. Ground is a square plane under /World/Ground.
A dome light is added under /World/Light.

Output is Z-up, meters-per-unit = 1.0 to match Isaac Lab convention.

Heights come from (in priority): tags["height"] > tags["building:levels"] * 3.5m
> 12 m fallback.

Usage:
  python3 osm_to_usd.py --lat 40.7580 --lon -73.9855 --radius 500 \\
      --name manhattan_times_sq --out /home/ubuntu/assets/cities

Outputs:
  <out>/<name>/city.usd     — the scene
  <out>/<name>/meta.json    — query params, building counts, bbox
"""

import argparse
import json
import math
import sys
from pathlib import Path

import requests
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
EARTH_R_M_PER_DEG = 111320.0
DEFAULT_LEVEL_M = 3.5
DEFAULT_HEIGHT_M = 12.0


def latlon_to_local_xy(lat, lon, lat0, lon0):
    """Equirectangular projection around (lat0, lon0). Accurate enough for ~1km."""
    cos_lat0 = math.cos(math.radians(lat0))
    x = (lon - lon0) * cos_lat0 * EARTH_R_M_PER_DEG
    y = (lat - lat0) * EARTH_R_M_PER_DEG
    return x, y


def signed_area(ring):
    """Shoelace; CCW > 0, CW < 0."""
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return 0.5 * a


def height_from_tags(tags):
    if "height" in tags:
        try:
            return float(str(tags["height"]).split()[0])
        except (ValueError, IndexError):
            pass
    if "building:levels" in tags:
        try:
            return float(tags["building:levels"]) * DEFAULT_LEVEL_M
        except ValueError:
            pass
    return DEFAULT_HEIGHT_M


def fetch_buildings(lat, lon, radius_m):
    """Query Overpass for ways tagged building within a bounding box."""
    dlat = radius_m / EARTH_R_M_PER_DEG
    dlon = radius_m / (EARTH_R_M_PER_DEG * math.cos(math.radians(lat)))
    s, w = lat - dlat, lon - dlon
    n, e = lat + dlat, lon + dlon

    query = f"""
[out:json][timeout:60];
(
  way["building"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;
"""
    print(
        f"[osm] querying Overpass: bbox=({s:.5f},{w:.5f},{n:.5f},{e:.5f})",
        file=sys.stderr,
    )
    headers = {
        # Overpass policy requires a User-Agent that identifies the script + contact.
        "User-Agent": "TrigunAI-NvidiaSimSetup/osm_to_usd (drone-training; deepak@trigunai.com)",
    }
    r = requests.post(
        OVERPASS_URL, data={"data": query}, headers=headers, timeout=120
    )
    r.raise_for_status()
    return r.json(), (s, w, n, e)


def write_city_usd(buildings, out_path, ground_size_m):
    """Write a Z-up USD city with a ground plane and one extruded mesh per building."""
    stage = Usd.Stage.CreateNew(str(out_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Hemispheric light so the city isn't pitch black in viewport/render.
    light = UsdLux.DomeLight.Define(stage, "/World/Light")
    light.CreateIntensityAttr(1500.0)

    # Ground plane (square, side = 2 * ground_size_m)
    ground = UsdGeom.Mesh.Define(stage, "/World/Ground")
    half = ground_size_m
    ground.CreatePointsAttr(
        [
            Gf.Vec3f(-half, -half, 0.0),
            Gf.Vec3f(half, -half, 0.0),
            Gf.Vec3f(half, half, 0.0),
            Gf.Vec3f(-half, half, 0.0),
        ]
    )
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    ground.CreateExtentAttr(
        [Gf.Vec3f(-half, -half, 0.0), Gf.Vec3f(half, half, 0.0)]
    )
    ground.CreateDisplayColorAttr([(0.32, 0.32, 0.34)])

    UsdGeom.Xform.Define(stage, "/World/City")

    n_written = 0
    for b in buildings:
        ring = b["footprint"]
        if len(ring) < 3:
            continue
        if signed_area(ring) < 0:
            ring = list(reversed(ring))

        h = float(b["height_m"])
        n = len(ring)

        points = []
        for x, y in ring:
            points.append(Gf.Vec3f(float(x), float(y), 0.0))
        for x, y in ring:
            points.append(Gf.Vec3f(float(x), float(y), h))

        # 1 bottom n-gon (reversed → outward-down normal) +
        # 1 top n-gon (forward → outward-up normal) +
        # n side quads (CCW from outside)
        face_counts = [n, n] + [4] * n
        face_indices = []
        face_indices += list(range(n - 1, -1, -1))           # bottom
        face_indices += list(range(n, 2 * n))                # top
        for i in range(n):
            i2 = (i + 1) % n
            face_indices += [i, i2, i2 + n, i + n]           # side quad i

        mesh = UsdGeom.Mesh.Define(stage, f"/World/City/Building_{b['id']}")
        mesh.CreatePointsAttr(points)
        mesh.CreateFaceVertexCountsAttr(face_counts)
        mesh.CreateFaceVertexIndicesAttr(face_indices)

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        mesh.CreateExtentAttr(
            [
                Gf.Vec3f(min(xs), min(ys), 0.0),
                Gf.Vec3f(max(xs), max(ys), h),
            ]
        )
        mesh.CreateDisplayColorAttr([(0.70, 0.70, 0.72)])

        n_written += 1

    stage.GetRootLayer().Save()
    return n_written


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lat", type=float, required=True, help="center latitude")
    ap.add_argument("--lon", type=float, required=True, help="center longitude")
    ap.add_argument(
        "--radius",
        type=float,
        default=500.0,
        help="meters from center (default 500 → 1km square)",
    )
    ap.add_argument("--name", required=True, help="city name (output subdir)")
    ap.add_argument(
        "--out",
        default="/home/ubuntu/assets/cities",
        help="output base dir (EBS-persistent)",
    )
    args = ap.parse_args()

    out_dir = Path(args.out) / args.name
    out_dir.mkdir(parents=True, exist_ok=True)

    data, bbox = fetch_buildings(args.lat, args.lon, args.radius)
    nodes = {
        e["id"]: (e["lat"], e["lon"])
        for e in data["elements"]
        if e["type"] == "node"
    }

    buildings = []
    skipped_incomplete = 0
    for e in data["elements"]:
        if e["type"] != "way":
            continue
        node_ids = e.get("nodes", [])
        if len(node_ids) < 4:
            continue
        if node_ids[0] == node_ids[-1]:
            node_ids = node_ids[:-1]
        ring = []
        ok = True
        for nid in node_ids:
            if nid not in nodes:
                ok = False
                break
            lat, lon = nodes[nid]
            x, y = latlon_to_local_xy(lat, lon, args.lat, args.lon)
            ring.append((x, y))
        if not ok or len(ring) < 3:
            skipped_incomplete += 1
            continue
        h = height_from_tags(e.get("tags", {}))
        buildings.append({"id": e["id"], "footprint": ring, "height_m": h})

    print(
        f"[osm] {len(buildings)} buildings extracted "
        f"({skipped_incomplete} skipped as incomplete)",
        file=sys.stderr,
    )

    usd_path = out_dir / "city.usd"
    n_written = write_city_usd(
        buildings, usd_path, ground_size_m=args.radius * 1.1
    )

    heights = [b["height_m"] for b in buildings]
    meta = {
        "name": args.name,
        "center_lat": args.lat,
        "center_lon": args.lon,
        "radius_m": args.radius,
        "bbox": {
            "south": bbox[0],
            "west": bbox[1],
            "north": bbox[2],
            "east": bbox[3],
        },
        "buildings_written": n_written,
        "height_min_m": min(heights) if heights else None,
        "height_max_m": max(heights) if heights else None,
        "height_mean_m": (sum(heights) / len(heights)) if heights else None,
        "usd_path": str(usd_path),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    print(f"[osm] wrote {usd_path} ({n_written} buildings)", file=sys.stderr)
    print(usd_path)


if __name__ == "__main__":
    main()
