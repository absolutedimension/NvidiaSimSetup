#!/usr/bin/env python3
"""Lighting presets for the 6 cinematographer modes.

Each preset defines directed lights (key, fill, rim, etc.) that supplement
the HDRI environment. The HDRI provides ambient + reflected light; these
add shaped, directed character/stage lighting.

Usage:
    from lighting.presets import LIGHT_PRESETS, preset_to_usda, preset_to_blender

    # For USDA (OVRTX pipeline)
    usda_block = preset_to_usda("HERO")

    # For Blender (headless render pipeline)
    preset_to_blender("HERO")  # call inside Blender context
"""
from __future__ import annotations

import math
from typing import Any

LIGHT_PRESETS: dict[str, dict[str, dict[str, Any]]] = {
    "HERO": {
        "key": {
            "type": "spot", "pos": (-1.5, 3.0, 2.0),
            "rot": (-55, -30, 0), "intensity": 50000,
            "color": (1.0, 0.85, 0.7), "cone": 40, "blend": 0.3,
        },
        "rim": {
            "type": "spot", "pos": (1.0, 2.5, -2.0),
            "rot": (-40, 150, 0), "intensity": 35000,
            "color": (0.8, 0.85, 1.0), "cone": 60, "blend": 0.5,
        },
        "fill": {
            "type": "area", "pos": (2.0, 1.5, 1.0),
            "rot": (-20, 60, 0), "intensity": 8000,
            "color": (0.9, 0.88, 0.95), "width": 1.5, "height": 1.0,
        },
    },
    "INTIMATE": {
        "key": {
            "type": "area", "pos": (1.5, 2.0, 1.5),
            "rot": (-35, 45, 0), "intensity": 25000,
            "color": (1.0, 0.9, 0.78), "width": 1.0, "height": 0.8,
        },
        "fill": {
            "type": "area", "pos": (-1.5, 1.5, 1.0),
            "rot": (-25, -45, 0), "intensity": 12000,
            "color": (1.0, 0.92, 0.85), "width": 1.0, "height": 0.8,
        },
        "accent": {
            "type": "point", "pos": (0, 3.0, -1.0),
            "intensity": 5000, "color": (1.0, 0.85, 0.65),
        },
    },
    "EPIC": {
        "key": {
            "type": "sun", "rot": (-30, 45, 0),
            "intensity": 6.0, "color": (1.0, 0.92, 0.8),
        },
        "fill": {
            "type": "area", "pos": (-3.0, 2.0, 2.0),
            "rot": (-20, -45, 0), "intensity": 8000,
            "color": (0.85, 0.9, 1.0), "width": 2.0, "height": 1.5,
        },
    },
    "ENERGY": {
        "key": {
            "type": "spot", "pos": (0, 4.0, 0),
            "rot": (-90, 0, 0), "intensity": 60000,
            "color": (0.7, 0.3, 1.0), "cone": 50, "blend": 0.4,
        },
        "rim_left": {
            "type": "spot", "pos": (-2.5, 1.0, -1.5),
            "rot": (-10, -60, 0), "intensity": 40000,
            "color": (0.2, 0.5, 1.0), "cone": 45, "blend": 0.3,
        },
        "rim_right": {
            "type": "spot", "pos": (2.5, 1.0, -1.5),
            "rot": (-10, 60, 0), "intensity": 40000,
            "color": (1.0, 0.2, 0.5), "cone": 45, "blend": 0.3,
        },
        "floor": {
            "type": "area", "pos": (0, 0.05, 0),
            "rot": (90, 0, 0), "intensity": 15000,
            "color": (0.5, 0.2, 0.8), "width": 3.0, "height": 3.0,
        },
    },
    "SOLITUDE": {
        "key": {
            "type": "spot", "pos": (0, 5.0, 0.5),
            "rot": (-80, 0, 0), "intensity": 30000,
            "color": (1.0, 0.95, 0.9), "cone": 25, "blend": 0.6,
        },
    },
    "BEAUTY": {
        "key": {
            "type": "area", "pos": (0, 3.0, 2.5),
            "rot": (-40, 0, 0), "intensity": 30000,
            "color": (1.0, 0.98, 0.96), "width": 2.0, "height": 1.5,
        },
        "fill_left": {
            "type": "area", "pos": (-2.0, 2.0, 1.0),
            "rot": (-25, -45, 0), "intensity": 15000,
            "color": (1.0, 0.97, 0.95), "width": 1.5, "height": 1.0,
        },
        "fill_right": {
            "type": "area", "pos": (2.0, 2.0, 1.0),
            "rot": (-25, 45, 0), "intensity": 15000,
            "color": (1.0, 0.97, 0.95), "width": 1.5, "height": 1.0,
        },
        "rim": {
            "type": "spot", "pos": (0, 2.5, -2.0),
            "rot": (-30, 180, 0), "intensity": 20000,
            "color": (1.0, 0.95, 0.9), "cone": 50, "blend": 0.5,
        },
    },
}


def preset_to_usda(mode: str) -> str:
    """Return USDA light block for the given mode."""
    preset = LIGHT_PRESETS[mode.upper()]
    blocks = []
    for name, cfg in preset.items():
        light_name = name.title().replace("_", "") + "Light"
        lt = cfg["type"]

        if lt == "sun":
            usd_type = "DistantLight"
        elif lt == "spot":
            usd_type = "SphereLight"
        elif lt in ("area", "rect"):
            usd_type = "RectLight"
        elif lt == "point":
            usd_type = "SphereLight"
        else:
            usd_type = "SphereLight"

        lines = [f'    def {usd_type} "{light_name}"', '    {']
        r, g, b = cfg["color"]
        lines.append(f'        color3f inputs:color = ({r}, {g}, {b})')
        lines.append(f'        float inputs:intensity = {cfg["intensity"]}')

        if lt in ("area", "rect") and "width" in cfg:
            lines.append(f'        float inputs:width = {cfg["width"]}')
            lines.append(f'        float inputs:height = {cfg["height"]}')
        if lt == "spot" and "cone" in cfg:
            lines.append(f'        float inputs:shaping:cone:angle = {cfg["cone"]}')
            lines.append(f'        float inputs:shaping:cone:softness = {cfg.get("blend", 0.25)}')

        if "pos" in cfg:
            px, py, pz = cfg["pos"]
            lines.append(f'        double3 xformOp:translate = ({px}, {py}, {pz})')
        if "rot" in cfg:
            rx, ry, rz = cfg["rot"]
            lines.append(f'        double3 xformOp:rotateXYZ = ({rx}, {ry}, {rz})')

        ops = []
        if "pos" in cfg:
            ops.append('"xformOp:translate"')
        if "rot" in cfg:
            ops.append('"xformOp:rotateXYZ"')
        if ops:
            lines.append(f'        uniform token[] xformOpOrder = [{", ".join(ops)}]')

        lines.append('    }')
        blocks.append('\n'.join(lines))

    return '\n'.join(blocks)


def preset_to_blender(mode: str) -> None:
    """Create Blender lights for the given mode. Must be called inside Blender."""
    import bpy  # type: ignore

    preset = LIGHT_PRESETS[mode.upper()]
    for name, cfg in preset.items():
        light_name = f"Light_{mode}_{name}"
        lt = cfg["type"]

        if lt == "sun":
            bpy_type = "SUN"
        elif lt == "spot":
            bpy_type = "SPOT"
        elif lt in ("area", "rect"):
            bpy_type = "AREA"
        elif lt == "point":
            bpy_type = "POINT"
        else:
            bpy_type = "POINT"

        light_data = bpy.data.lights.new(name=light_name, type=bpy_type)
        light_data.energy = cfg["intensity"]
        light_data.color = cfg["color"]

        if bpy_type == "SPOT" and "cone" in cfg:
            light_data.spot_size = math.radians(cfg["cone"] * 2)
            light_data.spot_blend = cfg.get("blend", 0.25)
        if bpy_type == "AREA" and "width" in cfg:
            light_data.shape = "RECTANGLE"
            light_data.size = cfg["width"]
            light_data.size_y = cfg["height"]

        obj = bpy.data.objects.new(name=light_name, object_data=light_data)
        bpy.context.collection.objects.link(obj)

        if "pos" in cfg:
            obj.location = cfg["pos"]
        if "rot" in cfg:
            obj.rotation_euler = tuple(math.radians(a) for a in cfg["rot"])


def get_hdri_path(mode: str, hdri_dir: str = "stage_design/hdri") -> str:
    """Return the expected HDRI filename for a mode."""
    hdri_map = {
        "HERO": "hero_stage.hdr",
        "INTIMATE": "intimate_studio.hdr",
        "EPIC": "epic_amphitheater.hdr",
        "ENERGY": "energy_festival.hdr",
        "SOLITUDE": "solitude_void.hdr",
        "BEAUTY": "beauty_studio.hdr",
    }
    return f"{hdri_dir}/{hdri_map[mode.upper()]}"


HDRI_PROMPTS = {
    "HERO": "dark dramatic concert stage, single harsh spotlight from below, black void background, theatrical, cinematic, moody, concert photography",
    "INTIMATE": "warm cozy dance studio interior, honey oak wood floor, cream fabric curtains, soft candles along walls, golden hour light, intimate, warm",
    "EPIC": "vast outdoor amphitheater at golden hour, mountain panorama background, stone architecture, epic wide vista, dramatic sky, cinematic landscape",
    "ENERGY": "neon concert festival stage, LED panels purple and blue, laser beams through haze, DJ booth, intense lighting, electronic music festival",
    "SOLITUDE": "infinite black void, single pool of warm light on dark floor, minimalist, lonely, vast empty space, darkness, isolation",
    "BEAUTY": "professional photography studio, white infinity cove, soft diffused lighting, clean elegant space, seamless background, fashion studio",
}

POLYHAVEN_HDRIS = {
    "HERO": "studio_small_08",
    "INTIMATE": "dancing_hall",
    "EPIC": "kloofendal_48d_partly_cloudy",
    "ENERGY": "neon_photostudio",
    "SOLITUDE": "moonless_golf",
    "BEAUTY": "photo_studio_loft_hall",
}
