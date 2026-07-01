#!/usr/bin/env python3
"""
TrigunAI RTX Variant Studio — render proxy
==========================================

A browser-drivable, variant-aware RTX studio on top of the existing OVRTX
single-frame renderer (localhost:8001). Mirrors NVIDIA's "OVRTX Variant Studio":
pick a USD showcase asset, flip its authored variant sets (carpaint colour,
wheels, decals, lights…), choose a camera angle + quality, and get a photoreal
RTX frame back.

   browser ──{asset, variants, camera, quality}──> THIS PROXY ──/render──> OVRTX
           <─────────── data:image/png ───────────            <── images[0] ──

How variants work: the asset (e.g. NVIDIA's Koenigsegg Ragnarok) ships authored
`UsdVariantSets`. We scan them with pxr, and on render we compose the chosen
selections in a tiny overlay layer (built with the Sdf API) that *references* the
asset by a URL OVRTX can resolve (public S3 / `/host_tmp`). OVRTX renders the
composed result with full RTX + MDL materials.

Run ON the EC2 box (OVRTX on localhost:8001):
    pip install --break-system-packages fastapi "uvicorn[standard]" requests
    python3 render_proxy.py            # serves 0.0.0.0:8010
"""
from __future__ import annotations

import base64
import math
import os
import time
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pxr import Usd, UsdGeom, Gf, Sdf

OVRTX_URL = os.environ.get("OVRTX_URL", "http://localhost:8001")
PORT = int(os.environ.get("PORT", "8010"))
S3 = "https://omniverse-content-production.s3.us-west-2.amazonaws.com"

# ── asset registry ───────────────────────────────────────────────────────────
# scan_path: a local USD pxr can open (to scan variants/cameras/bbox)
# render_ref: the URL/path OVRTX references at render time (S3 https or /host_tmp)
# frame_prim/frame_extra: prims used to auto-frame (excludes the HDRI environment)
# add_lights: inject a dome+key light (for assets with no authored lighting)
ASSETS: dict[str, dict] = {
    "ragnarok": {
        "label": "Koenigsegg Ragnarok",
        "scan_path": "/home/ubuntu/showcase_assets/Ragnarok/Koenigsegg_Ragnarok.usd",
        "render_ref": f"{S3}/Samples/Showcases/2023_2_1/Ragnarok/Koenigsegg_Ragnarok.usd",
        "frame_prim": "/World/Koenigsegg_Ragnarok",
        "frame_extra": ["/World/Tires"],
        "add_lights": False,
        "hero": {"az": 40, "el": 8, "focal": 35},
    },
    "cf2x": {
        "label": "Crazyflie 2X (drone)",
        "scan_path": "/tmp/viewer_assets/cf2x.usd",
        "render_ref": "/host_tmp/viewer_assets/cf2x.usd",
        "frame_prim": None,
        "frame_extra": [],
        "add_lights": True,
        "hero": {"az": 50, "el": 22, "focal": 24},
    },
}

app = FastAPI(title="TrigunAI RTX Variant Studio", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_scan_cache: dict[str, dict] = {}


# ── camera math ──────────────────────────────────────────────────────────────
def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def look_at(eye, target, up=(0.0, 1.0, 0.0)) -> Gf.Matrix4d:
    z = _norm([eye[i] - target[i] for i in range(3)])
    x = _norm(_cross(up, z))
    y = _cross(z, x)
    return Gf.Matrix4d(x[0], x[1], x[2], 0, y[0], y[1], y[2], 0,
                       z[0], z[1], z[2], 0, eye[0], eye[1], eye[2], 1)


def orbit_eye(target, az_deg, el_deg, dist):
    az, el = math.radians(az_deg), math.radians(max(-89.0, min(89.0, el_deg)))
    d = (math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az))
    return [target[i] + dist * d[i] for i in range(3)]


# ── scan: variant sets, cameras, framing ─────────────────────────────────────
def scan_asset(asset_id: str) -> dict:
    if asset_id in _scan_cache:
        return _scan_cache[asset_id]
    cfg = ASSETS[asset_id]
    path = cfg["scan_path"]
    if not Path(path).exists():
        raise HTTPException(404, f"scan source missing for {asset_id}: {path}")
    stage = Usd.Stage.Open(path)
    if not stage:
        raise HTTPException(500, f"could not open {path}")
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                              [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])

    variant_sets, cameras = [], []
    for prim in stage.Traverse():
        vs = prim.GetVariantSets()
        for name in vs.GetNames():
            vset = vs.GetVariantSet(name)
            variant_sets.append({
                "id": f"{prim.GetPath()}::{name}",
                "prim": str(prim.GetPath()),
                "set": name,
                "current": vset.GetVariantSelection(),
                "options": list(vset.GetVariantNames()),
            })
        if prim.IsA(UsdGeom.Camera):
            cameras.append(str(prim.GetPath()))

    # framing: bbox of the vehicle (frame_prim + extras), or whole stage
    rng = Gf.Range3d()
    targets = ([cfg["frame_prim"]] if cfg["frame_prim"] else []) + cfg["frame_extra"]
    if not targets:
        targets = [str(c.GetPath()) for c in stage.GetPseudoRoot().GetChildren()]
    center_prim = cfg["frame_prim"]
    for p in targets:
        prim = stage.GetPrimAtPath(p)
        if prim and prim.IsValid():
            b = cache.ComputeWorldBound(prim).ComputeAlignedRange()
            if not b.IsEmpty():
                rng = Gf.Range3d.GetUnion(rng, b)
    if rng.IsEmpty():
        rng = cache.ComputeWorldBound(stage.GetPseudoRoot()).ComputeAlignedRange()
    mn, mx = rng.GetMin(), rng.GetMax()
    size = max(mx[i] - mn[i] for i in range(3)) or 1.0
    # centre on the body prim if available (more stable than the union centre)
    cb = rng
    if center_prim:
        bp = stage.GetPrimAtPath(center_prim)
        if bp and bp.IsValid():
            bb = cache.ComputeWorldBound(bp).ComputeAlignedRange()
            if not bb.IsEmpty():
                cb = bb
    cmn, cmx = cb.GetMin(), cb.GetMax()
    center = [(cmn[i] + cmx[i]) / 2.0 for i in range(3)]

    out = {
        "id": asset_id, "label": cfg["label"],
        "variant_sets": variant_sets, "cameras": cameras,
        "center": [round(c, 4) for c in center],
        "size": round(size, 4),
        "suggest_dist": round(size * 1.6, 4),
        "hero": cfg["hero"],
        "has_variants": bool(variant_sets),
    }
    _scan_cache[asset_id] = out
    return out


# ── build the overlay wrapper + render ───────────────────────────────────────
def build_wrapper(asset_id: str, variants: dict, matrix: Gf.Matrix4d,
                  focal: float, add_lights: bool) -> str:
    cfg = ASSETS[asset_id]
    layer = Sdf.Layer.CreateAnonymous(".usda")
    world = Sdf.PrimSpec(layer, "World", Sdf.SpecifierDef, "Xform")
    layer.defaultPrim = "World"
    world.referenceList.prependedItems.append(Sdf.Reference(cfg["render_ref"]))

    # author each variant selection as a nested `over`
    def ensure_over(prim_path: str) -> Sdf.PrimSpec:
        parent = world
        for name in prim_path.split("/")[2:]:           # skip '' and 'World'
            parent = parent.nameChildren.get(name) or \
                Sdf.PrimSpec(parent, name, Sdf.SpecifierOver)
        return parent

    for vid, value in variants.items():
        if "::" not in vid or not value:
            continue
        prim_path, set_name = vid.split("::", 1)
        ensure_over(prim_path).variantSelections[set_name] = value

    # camera
    cam = Sdf.PrimSpec(world, "ViewCam", Sdf.SpecifierDef, "Camera")
    a = Sdf.AttributeSpec(cam, "xformOp:transform", Sdf.ValueTypeNames.Matrix4d)
    a.default = matrix
    o = Sdf.AttributeSpec(cam, "xformOpOrder", Sdf.ValueTypeNames.TokenArray)
    o.default = ["xformOp:transform"]
    fl = Sdf.AttributeSpec(cam, "focalLength", Sdf.ValueTypeNames.Float)
    fl.default = float(focal)
    crv = Sdf.AttributeSpec(cam, "clippingRange", Sdf.ValueTypeNames.Float2)
    crv.default = Gf.Vec2f(0.05, 1e7)

    if add_lights:
        dome = Sdf.PrimSpec(world, "Dome", Sdf.SpecifierDef, "DomeLight")
        Sdf.AttributeSpec(dome, "inputs:intensity", Sdf.ValueTypeNames.Float).default = 1000.0
        key = Sdf.PrimSpec(world, "Key", Sdf.SpecifierDef, "DistantLight")
        Sdf.AttributeSpec(key, "inputs:intensity", Sdf.ValueTypeNames.Float).default = 3000.0
        kr = Sdf.AttributeSpec(key, "xformOp:rotateXYZ", Sdf.ValueTypeNames.Float3)
        kr.default = Gf.Vec3f(-50, 25, 0)
        Sdf.AttributeSpec(key, "xformOpOrder", Sdf.ValueTypeNames.TokenArray).default = ["xformOp:rotateXYZ"]

    return layer.ExportToString()


def ovrtx_render(usda: str, width: int, height: int, samples: int | None,
                 timeout: float = 600.0) -> str:
    data = "data:application/octet-stream;base64," + base64.b64encode(usda.encode()).decode()
    rs = {
        "camera_paths": ["/World/ViewCam"],
        "frame_range": {"start": 0, "end": 0},
        "camera_parameters": {"width": width, "height": height},
        "sensors": None,
        "apply_background_mask": False,
    }
    if samples:
        rs["samples"] = int(samples)          # honoured if OVRTX supports it
    payload = {"url": data, "force_render": True, "render_settings": rs}
    try:
        r = requests.post(f"{OVRTX_URL.rstrip('/')}/render", json=payload, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(502, f"OVRTX unreachable: {e}")
    body = r.json()
    if body.get("status") != "success":
        raise HTTPException(502, f"OVRTX render failed: {body.get('error')}")
    frame = body.get("images", {}).get("0")
    if not frame:
        raise HTTPException(502, "OVRTX returned no frame")
    _cam, sensor = next(iter(frame.items()))
    return next(iter(sensor.values()))


# ── API ──────────────────────────────────────────────────────────────────────
class RenderReq(BaseModel):
    asset: str = "ragnarok"
    variants: dict[str, str] = {}
    az: float | None = None
    el: float | None = None
    dist: float | None = None
    focal: float | None = None
    width: int = 1280
    height: int = 720
    samples: int | None = None


@app.get("/")
def root():
    # Friendly landing for the bare API host — the actual UI is the studio page.
    return {
        "service": "TrigunAI RTX Variant Studio — render proxy",
        "ok": True,
        "studio_ui": "https://studio.trigunai.com/rtx",
        "endpoints": ["/viewer/health", "/viewer/assets",
                      "/viewer/scan?asset=ragnarok", "/viewer/render (POST)"],
    }


@app.get("/viewer/health")
def health():
    try:
        ok = requests.get(f"{OVRTX_URL.rstrip('/')}/health", timeout=5).ok
    except requests.RequestException:
        ok = False
    return {"proxy": "up", "ovrtx": ok}


@app.get("/viewer/assets")
def list_assets():
    out = []
    for aid, cfg in ASSETS.items():
        out.append({"id": aid, "label": cfg["label"],
                    "available": Path(cfg["scan_path"]).exists()})
    return {"assets": out}


@app.get("/viewer/scan")
def scan(asset: str):
    if asset not in ASSETS:
        raise HTTPException(404, f"unknown asset {asset}")
    return scan_asset(asset)


@app.post("/viewer/render")
def render(req: RenderReq):
    if req.asset not in ASSETS:
        raise HTTPException(404, f"unknown asset {req.asset}")
    info = scan_asset(req.asset)
    cfg = ASSETS[req.asset]
    hero = info["hero"]
    az = hero["az"] if req.az is None else req.az
    el = hero["el"] if req.el is None else req.el
    dist = info["suggest_dist"] if req.dist is None else req.dist
    focal = hero["focal"] if req.focal is None else req.focal
    target = info["center"]

    eye = orbit_eye(target, az, el, dist)
    matrix = look_at(eye, target)
    usda = build_wrapper(req.asset, req.variants, matrix, focal, cfg["add_lights"])

    t0 = time.time()
    b64 = ovrtx_render(usda, req.width, req.height, req.samples)
    ms = int((time.time() - t0) * 1000)
    return {"png": f"data:image/png;base64,{b64}", "render_ms": ms,
            "camera": {"az": az, "el": el, "dist": round(dist, 3), "focal": focal}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("render_proxy:app", host="0.0.0.0", port=PORT)
