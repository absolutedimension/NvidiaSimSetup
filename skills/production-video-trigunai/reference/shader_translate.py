"""
Shader Studio (studio.trigunai.com) GLSL  ->  Video Creator pipeline GLSL.

Studio shaders are authored for browser WebGL (Three.js): GLSL-ES style,
`gl_FragColor`, `texture2D`, and a large custom uniform set (uTime, uRes,
uBass/uMids/uHighs/uBeat, uColA..D, ~14 style-param sliders, uPhoto, ...).

The Video Creator render path (services/shader_service.py, ModernGL desktop
GL 3.3) binds ONLY these 6 uniforms:
    u_time, u_resolution, u_rms, u_bass, u_treble, u_onset

This module rewrites a pasted Studio shader so it compiles and runs in that
path with zero hand-editing:

  * audio / time / resolution uniforms  -> #define onto the 6 bound uniforms
  * unknown float "style" uniforms      -> #define to a sensible constant
                                           (name-heuristic defaults)
  * vecN palette uniforms (uColA..D)     -> #define to constant vec3s
  * sampler uPhoto / uPhotoEnabled       -> photo path disabled (procedural
                                           fallback kept), sampler left dummy
  * gl_FragColor  -> fragColor (declared `out vec4`)
  * texture2D(    -> texture(
  * Shadertoy mainImage(out,in)          -> wrapped in a main()

Public API:
    translate_glsl(src, params=None) -> (translated_src, report_dict)
"""

import re

# ── 6 uniforms the render path actually binds ──
PIPELINE_HEADER = """#version 330
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;
"""

# ── Studio audio/time/res uniform names -> expression over the bound 6 ──
AUDIO_TIME_MAP = {
    "uTime": "u_time",
    "uRes": "u_resolution",
    "iTime": "u_time",
    "iResolution": "vec3(u_resolution, 1.0)",
    "uSubBass": "u_bass",
    "uBass": "u_bass",
    "uMids": "((u_bass + u_treble) * 0.5)",
    "uHighs": "u_treble",
    "uTreble": "u_treble",
    "uBeat": "u_onset",
    "uRMS": "u_rms",
    "uOnset": "u_onset",
    "uFlux": "u_onset",
    "uCentroid": "0.5",
    "uFlatness": "0.5",
    "uZCR": "0.5",
    "uSilence": "0.0",
    "uPhotoEnabled": "0.0",
    "uPhotoBlend": "0.0",
}

# ── default palette (IQ cosine — cosmic violet) for uColA..D if pasted shader uses them ──
PALETTE_DEFAULTS = {
    "uColA": "vec3(0.45, 0.40, 0.55)",
    "uColB": "vec3(0.40, 0.35, 0.45)",
    "uColC": "vec3(1.0, 1.0, 1.0)",
    "uColD": "vec3(0.10, 0.20, 0.45)",
}


def _default_for_param(name: str) -> float:
    """Name-heuristic default for an unknown float style uniform."""
    n = name.lower()
    if "speed" in n:        return 0.5
    if "chroma" in n or "aberr" in n: return 0.3
    if "haze" in n:         return 0.4
    if "saturation" in n:   return 1.1
    if "brightness" in n:   return 1.0
    if "pool" in n:         return 0.5
    if "amount" in n or "strength" in n or "length" in n: return 1.0
    return 1.0


# Matches a whole uniform declaration incl. comma-separated names:
#   uniform float uBass;
#   uniform float uSubBass, uBass, uMids, uHighs, uBeat;
#   uniform float uBands[8];
#   uniform vec3  uColA, uColB, uColC, uColD;
_UNIFORM_RE = re.compile(
    r"^[ \t]*uniform\s+(?P<type>\w+)\s+(?P<names>[^;]+);.*$",
    re.MULTILINE,
)
# One name within a declaration, with optional array suffix.
_NAME_RE = re.compile(r"(?P<name>\w+)\s*(?P<arr>\[\s*\d+\s*\])?")


def translate_glsl(src, params=None):
    """
    Convert a Studio GLSL fragment shader to the pipeline contract.

    params: optional {uniform_name: value} overrides for style params
            (e.g. copied slider state). value may be float or [r,g,b].

    Returns (translated_src, report) where report lists how each uniform
    was handled and any warnings.
    """
    params = params or {}
    report = {"audio": [], "baked": [], "palette": [], "photo": False,
              "warnings": [], "mainimage_wrapped": False}

    defines = []          # lines injected after the pipeline header
    keep_dummy_photo = False

    # 1. Find + strip every uniform declaration; decide how to replace it.
    #    Handles comma-separated names: `uniform float uA, uB, uC;`
    for m in _UNIFORM_RE.finditer(src):
        utype = m.group("type")
        for raw_name in m.group("names").split(","):
          raw_name = raw_name.strip()
          if not raw_name:
              continue
          nm = _NAME_RE.match(raw_name)
          if not nm:
              continue
          name, arr = nm.group("name"), nm.group("arr")

          if name in ("u_time", "u_resolution", "u_rms", "u_bass", "u_treble", "u_onset"):
              continue  # already provided by header; will be stripped below

          if name in AUDIO_TIME_MAP:
              defines.append(f"#define {name} {AUDIO_TIME_MAP[name]}")
              report["audio"].append(name)
          elif name in PALETTE_DEFAULTS:
              val = params.get(name)
              if isinstance(val, (list, tuple)) and len(val) == 3:
                  defines.append(f"#define {name} vec3({val[0]}, {val[1]}, {val[2]})")
              else:
                  defines.append(f"#define {name} {PALETTE_DEFAULTS[name]}")
              report["palette"].append(name)
          elif utype == "sampler2D":
              keep_dummy_photo = True  # leave a dummy decl so dead-branch texture() compiles
              report["photo"] = True
          elif arr:  # array uniform e.g. uBands[8]
              n = int(re.search(r"\d+", arr).group())
              fill = ", ".join(["0.3"] * n)
              defines.append(f"const float {name}[{n}] = float[{n}]({fill});")
              report["baked"].append(f"{name}[{n}]")
          elif utype in ("float", "int"):
              val = params.get(name, _default_for_param(name))
              defines.append(f"#define {name} {float(val)}")
              report["baked"].append(f"{name}={float(val)}")
          elif utype.startswith("vec"):
              val = params.get(name)
              if isinstance(val, (list, tuple)):
                  defines.append(f"#define {name} {utype}({', '.join(str(x) for x in val)})")
              else:
                  defines.append(f"#define {name} {utype}(0.5)")
              report["baked"].append(f"{name}({utype})")
          else:
              report["warnings"].append(f"unhandled uniform {utype} {name} -> baked vec/float(1.0)")
              defines.append(f"#define {name} 1.0")

    body = _UNIFORM_RE.sub("", src)

    # 2. Strip any existing #version / precision lines from the body.
    body = re.sub(r"^\s*#version.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^\s*precision\s+\w+\s+float\s*;.*$", "", body, flags=re.MULTILINE)

    # 3. Token fixes.
    body = body.replace("texture2D(", "texture(")
    body = re.sub(r"\bgl_FragColor\b", "fragColor", body)

    # 4. Shadertoy mainImage(out vec4 X, in vec2 Y) -> main() wrapper.
    mi = re.search(r"void\s+mainImage\s*\(", body)
    has_main = re.search(r"void\s+main\s*\(", body)
    wrapper = ""
    if mi and not has_main:
        wrapper = (
            "\nvoid main() {\n"
            "    vec4 _frag;\n"
            "    mainImage(_frag, gl_FragCoord.xy);\n"
            "    fragColor = _frag;\n"
            "}\n"
        )
        report["mainimage_wrapped"] = True

    photo_decl = "uniform sampler2D uPhoto;\n" if keep_dummy_photo else ""

    out = (
        PIPELINE_HEADER
        + photo_decl
        + "\n".join(defines)
        + "\n\n"
        + body.strip()
        + "\n"
        + wrapper
    )
    return out, report
