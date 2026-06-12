#!/usr/bin/env python3
"""
city_enrich_textures.py — Use the NVIDIA Content Pipeline's Texture Agent
(:8004) to AI-generate a façade material, then bind it to every building
in an OSM city USD.

Flow:
  1. Build a tiny throwaway sample USD: one 10m cube with a UsdShade.Material
     named "Facade" assigned. The Texture Agent needs *something* with a
     material slot to texture.
  2. POST it to the Texture Agent on :8004 with --prompt.
  3. Poll /pipeline/<id>/status until status='completed'.
  4. Download albedo/normal/roughness PNGs from /artifacts/<id>/textures/.
  5. Write a /World/Looks/CityFacade UsdShade.Material into the city USD
     that reads those PNGs, and MaterialBindingAPI-bind it to every
     /World/City/Building_* mesh.

Usage (run on the EC2 host — the Texture Agent is on localhost):
  python3 city_enrich_textures.py \\
      --city /home/ubuntu/assets/cities/manhattan_times_sq/city.usd \\
      --prompt "weathered Manhattan high-rise façade, mixed glass and concrete, daytime"

The downloaded textures land beside city.usd in <city_dir>/textures/.
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

import requests
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


TEXTURE_AGENT_BASE = "http://localhost:8004"
DEFAULT_PROMPT = (
    "weathered urban building façade, mixed glass and concrete, "
    "daytime, photorealistic, seamless tileable"
)
POLL_S = 5
TIMEOUT_S = 600


def build_sample_usda(out_path: Path):
    """A 1-cube USD with one UsdShade.Material assigned. Texture Agent needs this shape."""
    s = """#usda 1.0
(
    defaultPrim = "Root"
    upAxis = "Y"
    metersPerUnit = 1.0
)

def Xform "Root"
{
    def Cube "Box" (
        prepend apiSchemas = ["MaterialBindingAPI"]
    )
    {
        double size = 10
        rel material:binding = </Root/Looks/Facade>
    }

    def Scope "Looks"
    {
        def Material "Facade"
        {
            token outputs:surface.connect = </Root/Looks/Facade/Shader.outputs:surface>

            def Shader "Shader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.6, 0.6, 0.6)
                float inputs:roughness = 0.7
                float inputs:metallic = 0.0
                token outputs:surface
            }
        }
    }
}
"""
    out_path.write_text(s)


def submit_pipeline(usd_path: Path, prompt: str) -> str:
    """POST USD + prompt → session_id."""
    with open(usd_path, "rb") as fh:
        files = {"usd_file": (usd_path.name, fh, "application/octet-stream")}
        data = {"user_prompt": prompt}
        r = requests.post(
            f"{TEXTURE_AGENT_BASE}/pipeline",
            files=files,
            data=data,
            timeout=60,
        )
    r.raise_for_status()
    body = r.json()
    # Different agent versions return either {session_id: ...} or a wrapper
    sid = body.get("session_id") or body.get("id") or body.get("data", {}).get("session_id")
    if not sid:
        raise RuntimeError(f"no session_id in response: {body}")
    return sid


def poll_until_done(session_id: str) -> dict:
    start = time.time()
    last_status = None
    while time.time() - start < TIMEOUT_S:
        r = requests.get(
            f"{TEXTURE_AGENT_BASE}/pipeline/{session_id}/status", timeout=10
        )
        r.raise_for_status()
        body = r.json()
        status = body.get("status")
        if status != last_status:
            cur = body.get("current_step")
            cur_name = cur.get("name") if isinstance(cur, dict) else cur
            pct = body.get("overall_progress", {}).get("percent")
            print(
                f"[texture] status={status} step={cur_name} pct={pct} "
                f"elapsed={int(time.time() - start)}s",
                file=sys.stderr,
            )
            last_status = status
        if status == "completed":
            return body
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"pipeline {status}: {json.dumps(body, indent=2)}")
        time.sleep(POLL_S)
    raise TimeoutError(f"texture pipeline did not finish in {TIMEOUT_S}s")


def download_textures_zip(session_id: str, out_dir: Path) -> list[Path]:
    """The /artifacts/<sid>/textures endpoint returns a ZIP with all PBR maps.
    Unzip into out_dir, return list of extracted texture paths."""
    import zipfile

    r = requests.get(
        f"{TEXTURE_AGENT_BASE}/artifacts/{session_id}/textures", timeout=120
    )
    r.raise_for_status()
    buf = io.BytesIO(r.content)
    extracted = []
    with zipfile.ZipFile(buf) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # ZIP entries land under "textures/Facade_albedo.png" etc — flatten.
            target = out_dir / Path(info.filename).name
            with zf.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted.append(target)
    return extracted


def pick_pbr_maps(downloaded: list[Path]) -> dict[str, Path]:
    """Match filenames to {albedo, normal, roughness, metallic} slots heuristically."""
    out = {}
    for p in downloaded:
        name = p.name.lower()
        if "albedo" in name or "basecolor" in name or "diffuse" in name:
            out["albedo"] = p
        elif "normal" in name:
            out["normal"] = p
        elif "rough" in name:
            out["roughness"] = p
        elif "metal" in name:
            out["metallic"] = p
        elif "orm" in name:
            out["orm"] = p
    return out


def apply_material_to_city(city_path: Path, maps: dict[str, Path]):
    """Write /World/Looks/CityFacade and bind to every /World/City/Building_*."""
    stage = Usd.Stage.Open(str(city_path))

    looks = UsdGeom.Scope.Define(stage, "/World/Looks")
    mat = UsdShade.Material.Define(stage, "/World/Looks/CityFacade")
    shader = UsdShade.Shader.Define(stage, "/World/Looks/CityFacade/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")

    # Texture coordinate reader (uses st primvar — Mesh doesn't have one yet
    # but UsdPreviewSurface falls back to a planar projection)
    st_reader = UsdShade.Shader.Define(stage, "/World/Looks/CityFacade/PrimvarReader")
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    st_out = st_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

    def make_texture(name: str, png_path: Path, type_: str):
        tx = UsdShade.Shader.Define(stage, f"/World/Looks/CityFacade/{name}")
        tx.CreateIdAttr("UsdUVTexture")
        # Use absolute path so the city.usd works regardless of CWD
        tx.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(str(png_path))
        tx.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(st_out)
        tx.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
        tx.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")
        return tx.CreateOutput(type_, Sdf.ValueTypeNames.Float3 if type_ == "rgb" else Sdf.ValueTypeNames.Float)

    if "albedo" in maps:
        out = make_texture("AlbedoTex", maps["albedo"], "rgb")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(out)
    if "normal" in maps:
        out = make_texture("NormalTex", maps["normal"], "rgb")
        shader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f).ConnectToSource(out)
    if "roughness" in maps:
        out = make_texture("RoughTex", maps["roughness"], "r")
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).ConnectToSource(out)
    if "metallic" in maps:
        out = make_texture("MetalTex", maps["metallic"], "r")
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).ConnectToSource(out)

    mat.CreateSurfaceOutput().ConnectToSource(
        shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)
    )

    # Bind to every Building_*
    bound = 0
    for prim in stage.Traverse():
        if prim.GetPath().pathString.startswith("/World/City/Building_"):
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat)
            bound += 1

    stage.GetRootLayer().Save()
    print(
        f"[material] /World/Looks/CityFacade created; bound to {bound} buildings",
        file=sys.stderr,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--city", required=True, help="city.usd produced by osm_to_usd.py")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, help="user prompt for texture gen")
    ap.add_argument(
        "--keep-sample",
        action="store_true",
        help="keep the throwaway sample USD next to city.usd",
    )
    args = ap.parse_args()

    city_path = Path(args.city)
    city_dir = city_path.parent
    tx_dir = city_dir / "textures"
    tx_dir.mkdir(exist_ok=True)

    sample_path = city_dir / "_sample_facade.usda"
    build_sample_usda(sample_path)
    print(f"[sample] wrote {sample_path}", file=sys.stderr)

    print(f"[texture] submitting with prompt: {args.prompt}", file=sys.stderr)
    sid = submit_pipeline(sample_path, args.prompt)
    print(f"[texture] session_id={sid}", file=sys.stderr)

    poll_until_done(sid)
    downloaded = download_textures_zip(sid, tx_dir)
    print(
        f"[texture] downloaded {len(downloaded)} maps → {tx_dir}: "
        f"{[p.name for p in downloaded]}",
        file=sys.stderr,
    )

    maps = pick_pbr_maps(downloaded)
    print(f"[texture] PBR map mapping: {dict((k, v.name) for k, v in maps.items())}", file=sys.stderr)

    apply_material_to_city(city_path, maps)

    if not args.keep_sample:
        sample_path.unlink(missing_ok=True)

    print(f"[done] {city_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
