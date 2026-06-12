---
name: trigunai-stage
description: >
  Intelligent stage/set design system for TrigunAI's cinematographer drone pipeline. Generates
  virtual production stages optimized for how the drone films them — coordinated with the 6
  aesthetic modes (HERO, INTIMATE, EPIC, ENERGY, SOLITUDE, BEAUTY), the lighting system, and
  the existing USD/NVIDIA Content Agents pipeline. Covers: parameterized stage templates (S1),
  LLM-designed stages from text descriptions (S2), RL co-optimized stage+camera (S3), and
  growing asset library (S4). Use when the user mentions "stage", "set design", "production
  design", "virtual set", "mise-en-scene", "environment", "backdrop", "floor material",
  "stage template", "props", "atmosphere", "venue", "scene generation", "depth layers",
  "background", "set dressing", "cyclorama", "stage layout", "performance space", or works
  on files in stage_design/ directory. Proactively trigger when a demo render looks like a
  flat grey floor with no environment, or when discussing customer deliverables that need a
  complete visual package.
---

# TrigunAI Intelligent Stage Design Agent

You build an **intelligent stage/set design system** that generates virtual production
environments optimized for how the cinematographer drone films them. When a customer describes
their performance, the system produces a complete stage — floor, backdrop, structure, props,
atmosphere — coordinated with the drone's 6 aesthetic modes and the lighting system.

You operate on a **Mac** (template authoring, LLM composition scripts, evaluation) and an
**AWS EC2 g5.2xlarge** (NVIDIA Content Agents for texturing/materials, OVRTX rendering,
RL training). You are part of the TrigunAI agent ecosystem.

---

## The problem

The cinematographer drone currently films a dancer on a **flat grey floor in a void**. That's
a tech demo. A real production has depth layers, materials, atmosphere, set dressing. Without
a stage, the 6 aesthetic modes can't reach their potential — HERO needs a dark dramatic
backdrop, INTIMATE needs warmth and texture, EPIC needs scale and depth.

**The gap:** No existing system co-optimizes virtual stage design with camera policy. Stage
design papers hold the camera fixed. Camera papers hold the stage fixed. Combining them — where
the environment is judged through the drone's eye — is genuinely novel.

---

## Architecture: how the stage connects to everything

```
Customer: "intimate contemporary dance piece"
  ↓
LLM Stage Designer (S2, gpt-4o-mini via LiteLLM :4000)
  ↓ selects template + customizes parameters
  ↓
Stage Template (S1, parameterized USD)
  ↓
Scene Composer Service (:8005) → base USD scene
  ↓
Texture Agent (:8004) → PBR textures for floor/backdrop/props
  ↓
Material Agent (:8000) → material assignments
  ↓
Lighting Agent (L1/L2) → mode-specific light rig
  ↓
Drone Policy (v4, 6 modes) → films within stage boundary
  ↓
OVRTX (:8001) → renders complete production
  ↓
Output: demo video / GLB / VR experience
```

**Every backend service already exists and runs on the EC2 box.** The stage system is the
orchestration layer that composes them into a complete virtual production.

---

## The 6 stage templates (one per aesthetic mode)

### HERO

```
Purpose: Makes the subject look powerful, larger than life
Floor: glossy black reflective — amplifies low-angle reflections
  material: high-gloss black polymer, roughness=0.05, metallic=0.3
Background: dark gradient backdrop — subject isolated against void
  material: dark charcoal fabric, roughness=0.8
Structure: single elevated platform, 3m×3m, 0.3m height
  → subject literally above camera's natural eye-line
Props: none — clean, powerful, minimal
Atmosphere: light haze (density=0.15) for rim light catch
Stage boundary: 6m × 6m × 4m
Camera clearance: platform edges must be >1.5m from stage boundary
```

### INTIMATE

```
Purpose: Warmth, closeness, human connection
Floor: warm oak wood planks
  material: oak PBR, roughness=0.4, warm tone (albedo bias +10% red)
Background: soft fabric drape, cream/amber, slightly crumpled for texture
  material: linen/silk blend, roughness=0.6, SSS enabled
Structure: flat, no risers — eye-level access everywhere
  optional: one wall 3m behind performer (creates cozy enclosure)
Props: 2-3 candles/warm practicals at 2m periphery (motivated light sources)
  → these give the lighting agent real sources to work with
Atmosphere: gentle warm haze (density=0.08, color=warm amber)
Stage boundary: 5m × 5m × 3m (deliberately smaller — intimacy = closeness)
```

### EPIC

```
Purpose: Scale, grandeur, the performer as part of something vast
Floor: stone/concrete — industrial or ancient depending on mood
  material: polished concrete, roughness=0.35, cool grey
Background: open — either sky dome (HDRI) or architectural depth
  option A: outdoor HDRI (sunset, overcast, blue hour)
  option B: grand hall with receding columns (depth perspective)
Structure: wide platform with ascending stairs (3 levels, 0.2m each)
  → gives drone vertical framing options with the performer at different heights
Props: columns/archways at 4m and 8m distance — create depth layers
  column material: white marble or brushed concrete
Atmosphere: atmospheric perspective (distance fog, density=0.03, cool blue)
Stage boundary: 12m × 12m × 8m (large — EPIC needs space)
```

### ENERGY

```
Purpose: Concert/festival feel, dynamic, beat-driven
Floor: dark with embedded LED strip pattern (emissive panels)
  material: matte black base + emissive rectangles (color driven by music_features)
Background: LED wall panels (2m tall, 6m wide, rear of stage)
  material: emissive, color driven by music_features[bass/mid/treble]
Structure: multi-level — main stage + two 0.5m risers (stage left/right)
  catwalk: optional 0.6m-wide elevated walkway (1.2m height)
Props: visible lighting truss overhead (steel truss, 4m up)
  speaker stacks at stage edges (cosmetic, non-functional)
Atmosphere: heavy haze (density=0.35) for visible light beams
  → CRITICAL for ENERGY — light beams through haze = concert look
Stage boundary: 10m × 8m × 5m
Beat sync: LED floor + wall panels pulse with music_features[onset] and [rms]
```

### SOLITUDE

```
Purpose: Isolation, loneliness, one person in vast emptiness
Floor: dark matte — absorbs all light, no reflections
  material: dark felt/velvet, roughness=0.95, albedo < 0.05
Background: pure black void — no backdrop, no walls
  → renderer background color = (0,0,0)
Structure: single small circular platform, 2m diameter, 0.05m height
  → just enough to define "here" vs "nothing"
  material: same dark matte, barely visible
Props: nothing — absolute emptiness is the point
Atmosphere: none — clean darkness, no haze (haze would catch light and reduce isolation)
Stage boundary: 8m × 8m × 5m (large empty space, drone has room but nothing to see)
Lighting note: only one spotlight on the performer — everything else pitch black
```

### BEAUTY

```
Purpose: Timeless, flattering, classic studio elegance
Floor: white/cream seamless — cyclorama curve (no hard floor-wall edge)
  material: matte white, roughness=0.5, albedo=0.85
  geometry: floor curves up into back wall with 1m radius fillet
Background: seamless infinity cove (continuation of floor curve)
  → classic photography studio look
Structure: flat, completely clean
Props: one elegant element — options:
  - tall mirror (1.5m×0.5m, angled 15°) — creates depth + reflection
  - fabric billow (sheer white, physics-simulated drape from ceiling)
  - single plant (olive tree or minimal ikebana)
Atmosphere: soft diffusion (density=0.05, white) — wraps light softly
Stage boundary: 7m × 7m × 4m
```

---

## Phase map with gates

| Phase | What you build | Key deliverable | Effort | Acceptance gate |
|---|---|---|---|---|
| **S1** | 6 parameterized USD stage templates | Renders of dancer on each stage | 2-3 weeks | Each stage looks emotionally distinct + appropriate for its mode (**SUBJECTIVE**) |
| **S2** | LLM stage designer (text → stage selection + params) | Director describes show → system generates stage | 2-3 weeks | LLM correctly selects mode + customizes for 5 test descriptions |
| **S3** | RL co-optimized stage + camera | Policy that adjusts stage for camera angles | 4-8 weeks | RL-designed stage scores higher on aesthetics than S1 preset (**SUBJECTIVE**) |
| **S4** | Asset library + retrieval system | Growing collection, ML retrieval | Ongoing | Each new customer's stage generated faster than the last |

**S1 and S3 have SUBJECTIVE approval gates.** CEO/founder must explicitly approve.

---

## Phase S1 — Parameterized Stage Templates (2-3 weeks)

### S1.1 — USD stage template format

Each stage is a USDA file with parameterized sections. The template defines geometry,
materials, and props with override points:

```usda
#usda 1.0
(
    defaultPrim = "Stage"
    upAxis = "Y"
    metersPerUnit = 1.0
)

def Xform "Stage" {
    # --- Floor ---
    def Mesh "Floor" {
        # Parameterized: floor_width, floor_depth, floor_material
        float3[] extent = [(-{floor_width/2}, 0, -{floor_depth/2}),
                           ({floor_width/2}, 0, {floor_depth/2})]
        # ... mesh data ...
        rel material:binding = </Stage/Materials/{floor_material}>
    }

    # --- Backdrop ---
    def Mesh "Backdrop" {
        # Parameterized: backdrop_type (flat/curved/none), backdrop_height, backdrop_material
    }

    # --- Platforms ---
    def Xform "Platforms" {
        # Parameterized: list of (pos, size, height, material) per platform
    }

    # --- Props ---
    def Xform "Props" {
        # Parameterized: list of (type, pos, scale, material) per prop
    }

    # --- Atmosphere ---
    def Xform "Atmosphere" {
        # Parameterized: haze_density, haze_color, volume bounds
    }

    # --- Materials ---
    def Scope "Materials" {
        # PBR material definitions — can be overridden by Texture Agent
    }

    # --- Stage Boundary (invisible, for drone policy) ---
    def Xform "Boundary" {
        custom float3 corner_min = (-{boundary_w/2}, 0, -{boundary_d/2})
        custom float3 corner_max = ({boundary_w/2}, {boundary_h}, {boundary_d/2})
    }
}
```

### S1.2 — Template generator script

```python
# stage_design/generate_stage.py
"""
Generates a complete USDA stage from mode + parameters.

Usage:
  python generate_stage.py --mode HERO --output hero_stage.usda
  python generate_stage.py --mode INTIMATE --floor-material oak --backdrop warm_drape
  python generate_stage.py --mode ENERGY --music-reactive --haze-density 0.35
"""
```

Parameters per template:
- `floor_material`: override default (e.g., oak, concrete, glossy_black)
- `floor_size`: override default dimensions
- `backdrop_type`: flat, curved, cyclorama, none
- `backdrop_material`: override
- `platform_count`: number of risers/levels
- `prop_set`: which props to include (from template's options list)
- `atmosphere_density`: haze density override
- `atmosphere_color`: haze color override
- `boundary_size`: stage boundary override (must be > performance area)
- `music_reactive`: enable beat-synced emissive elements (ENERGY mode)

### S1.3 — Integration with NVIDIA Content Agents

For each stage, after generating the base USDA:

1. **Texture Agent** (port 8004): Generate PBR texture maps for floor and backdrop
   - Input: material description ("warm oak wood planks, aged, natural grain")
   - Output: albedo + normal + roughness + metalness + AO maps
   - Apply to the stage's material slots

2. **Material Agent** (port 8000): Verify and enrich material properties
   - Input: stage USDA with texture-applied materials
   - Output: physics-accurate material parameters (IOR, absorption, SSS for fabrics)

3. **Scene Composer** (port 8005): If the stage includes complex props or city backdrops
   - Input: stage parameters specifying urban backdrop
   - Output: OSM-derived city geometry (already implemented for drone pipeline)

### S1.4 — OVRTX rendering validation

**Video rendering:** See `VIDEO_RENDERING.md` for the master reference. Use Blender EEVEE (0.33s/frame) instead of OVRTX (6s/frame) — 18x faster.

For each stage template, render a validation grid:
- 6 camera angles (front, 45° left, 45° right, overhead, low hero, rear)
- With the dancer present (stick figure from existing pipeline)
- With mode-appropriate lighting (from trigunai-lighting L1 presets)
- 512×512 per frame, composited into a 3×2 grid

This grid is the S1 gate artifact — CEO reviews each mode's stage across all angles.

### S1.5 — Drone policy integration

The stage geometry must be added to the drone policy's observation space so it avoids
collisions with platforms, props, and backdrop walls:

```python
# In cinematographer_env.py, add to observation:
stage_obstacles = [
    (platform_pos, platform_size),   # from stage template
    (backdrop_pos, backdrop_size),
    (prop_pos, prop_size) for prop in props
]

# Additional reward term
r_stage_clearance = exp(-k * min(dist_to_nearest_obstacle - 0.5m))
# Smooth penalty starting at 0.5m from any stage element
```

This means retraining the drone policy with stages in the loop. The policy learns to use
stage elements cinematically — framing the dancer against the backdrop, orbiting around
columns, using depth layers — while avoiding collisions.

### Files created (S1)

| File | Purpose | Location |
|---|---|---|
| `stage_design/generate_stage.py` | Master generator: mode + params → USDA | Mac repo |
| `stage_design/templates/hero.py` | HERO template definition (dataclass) | Mac repo |
| `stage_design/templates/intimate.py` | INTIMATE template definition | Mac repo |
| `stage_design/templates/epic.py` | EPIC template definition | Mac repo |
| `stage_design/templates/energy.py` | ENERGY template definition | Mac repo |
| `stage_design/templates/solitude.py` | SOLITUDE template definition | Mac repo |
| `stage_design/templates/beauty.py` | BEAUTY template definition | Mac repo |
| `stage_design/usda_stage.py` | USDA stage block generator (template → USDA string) | Mac repo |
| `stage_design/render_stage_comparison.py` | Renders validation grid for all 6 stages | Deploy to EC2 |
| `stage_design/enrich_stage.py` | Calls Texture + Material agents on generated stage | Deploy to EC2 |

---

## Phase S2 — LLM Stage Designer (2-3 weeks)

Use gpt-4o-mini (via existing LiteLLM proxy on port 4000) to translate director intent
into stage parameters.

### S2.1 — Design prompt

```python
system_prompt = """
You are a professional virtual production designer for dance and performance filming.
Given a description of a performance, select the optimal stage template and customize
its parameters for the specific show.

Available templates: HERO, INTIMATE, EPIC, ENERGY, SOLITUDE, BEAUTY

For each template you can customize:
- floor_material: material name + description for AI texture generation
- floor_size: (width, depth) in meters
- backdrop_type: flat | curved | cyclorama | none | hdri
- backdrop_material: material name + description
- backdrop_height: meters
- platform_count: 0-3
- platforms: list of {pos, size, height, material}
- props: list of {type, pos, scale, material} from available set
- atmosphere_density: 0.0 to 0.5
- atmosphere_color: RGB or "warm" | "cool" | "neutral"
- music_reactive: true/false (for beat-synced emissive elements)
- color_palette: primary + secondary + accent colors
- special_notes: any production-specific requirements

Available prop types: column, arch, mirror, fabric_drape, candle_cluster,
  chair, stool, led_panel, truss_section, speaker_stack, plant, sculpture

Think about:
1. What emotional tone does the performance convey?
2. What depth layers will serve the camera best?
3. What materials create the right reflections/shadows for the lighting?
4. What the drone will see from different angles (front, side, overhead, low)
5. Where the performer moves (leave their path clear, put visual interest at edges)

Return JSON only with: {template, customizations, reasoning}
"""
```

### S2.2 — Multi-stage compositions

For performances with emotional arcs (not just one mood), the LLM designs a **sequence**:

```python
# Director input:
"Contemporary piece. Opens alone in silence, builds through struggle,
 crescendo at 3:20, resolves in acceptance. Music: Nils Frahm - Says"

# LLM output:
{
  "stages": [
    {"time": "0:00-1:30", "template": "SOLITUDE",
     "customizations": {"atmosphere_density": 0.0, "floor_material": "dark_matte_concrete"}},
    {"time": "1:30-3:00", "template": "HERO",
     "customizations": {"platform_count": 1, "atmosphere_density": 0.2},
     "transition": "crossfade_10s"},
    {"time": "3:00-3:40", "template": "ENERGY",
     "customizations": {"music_reactive": true, "atmosphere_density": 0.35},
     "transition": "hard_cut"},
    {"time": "3:40-end", "template": "BEAUTY",
     "customizations": {"backdrop_type": "cyclorama", "atmosphere_color": "warm"},
     "transition": "crossfade_15s"}
  ],
  "reasoning": "Arc follows isolation → assertion → release → resolution.
    Stage transitions mirror the emotional journey."
}
```

### S2.3 — Validation

Test the LLM designer against 10 performance descriptions:
1. "Ballet solo, classical, Swan Lake variations" → expect BEAUTY
2. "Hip-hop battle, 2 dancers, aggressive" → expect HERO or ENERGY
3. "Contact improvisation, 2 dancers, tender" → expect INTIMATE
4. "Butoh, slow, existential" → expect SOLITUDE
5. "EDM concert, DJ + dancer, festival stage" → expect ENERGY
6. "Flamenco solo, passionate, powerful" → expect HERO
7. "Contemporary, grief piece, memorial" → expect SOLITUDE → BEAUTY
8. "Bollywood, celebratory, group choreography" → expect EPIC or ENERGY
9. "Jazz trio performance, nightclub" → expect INTIMATE
10. "Aerial silk acrobatics, cirque style" → expect EPIC

Each must produce a plausible stage. Document failures and adjust prompt.

### Files created (S2)

| File | Purpose | Location |
|---|---|---|
| `stage_design/llm_designer.py` | LLM composition: text → template + params JSON | Mac repo + EC2 |
| `stage_design/multi_stage_composer.py` | Handles stage sequences with transitions | Mac repo |
| `stage_design/test_descriptions.json` | 10 test performance descriptions + expected templates | Mac repo |
| `stage_design/validate_designer.py` | Runs all 10 tests, reports accuracy | Mac repo |

---

## Phase S3 — RL Co-Optimized Stage + Camera (4-8 weeks, research-grade)

**Novel contribution: stage layout is optimized for how the drone's camera sees it.**

### S3.1 — Environment: `StageOptEnv` (DirectRLEnv)

```
Isaac Lab environment: Isaac-StageOpt-Direct-v0

Two-agent setup (can be sequential or joint):
  Agent A (camera drone): existing v4 policy, FROZEN for S3
  Agent B (stage optimizer): adjusts stage elements

Stage Agent observation (48 dims):
├── dancer_trajectory_summary (12)
│   extent_x, extent_y, extent_z (3) — how far dancer travels
│   mean_speed (1) — average movement velocity
│   energy_level (1) — acceleration variance
│   center_of_activity (3) — mean dancer position
│   travel_direction (3) — dominant movement axis
│   vertical_range (1) — how much the dancer uses height
├── drone_camera_pos_relative (3) — current camera position
├── drone_camera_look_dir (3) — current camera orientation
├── current_mode_onehot (6) — which aesthetic mode
├── current_stage_state (24)
│   backdrop_pos (3) + backdrop_size (3)
│   platform_pos (3) + platform_size (3)
│   prop_0_pos (3) + prop_0_type (3, one-hot)
│   prop_1_pos (3) + prop_1_type (3, one-hot)
└── Total: 48

Stage Agent action space (18 continuous):
├── backdrop_offset (3) — move backdrop relative to dancer center
├── backdrop_scale (2) — width, height adjustment
├── backdrop_reflectivity (1) — 0=matte, 1=mirror
├── platform_offset (3) — move platform
├── platform_height (1) — raise/lower
├── prop_0_offset (3) — move first prop
├── prop_1_offset (3) — move second prop
├── atmosphere_density (1) — 0-0.5
├── floor_reflectivity (1) — 0=matte, 1=glossy
└── Total: 18
```

### S3.2 — Reward function (judged through the camera's eye)

```python
@dataclass
class StageRewardCfg:
    w_depth_layers: float = 0.20     # foreground/mid/background separation in frame
    w_subject_pop: float = 0.20      # dancer contrasts against background
    w_leading_lines: float = 0.10    # stage edges point toward subject
    w_negative_space: float = 0.10   # empty/filled ratio matches mode
    w_no_occlusion: float = 0.15     # stage elements never block camera-to-dancer
    w_aesthetic: float = 0.15        # LAION-Aesthetics on rendered frame
    w_mood_match: float = 0.10       # environment matches mode intent
```

### S3.3 — Per-term reward implementations

```python
def r_depth_layers(frame_rgb, depth_buffer):
    """Camera frame has distinct foreground/midground/background layers."""
    # From depth buffer: segment into 3 depth bands
    near = (depth_buffer < 3.0)   # foreground (props, floor edge)
    mid = (depth_buffer >= 3.0) & (depth_buffer < 8.0)  # performer zone
    far = (depth_buffer >= 8.0)   # backdrop
    # Reward: all three bands have non-trivial pixel coverage
    near_pct = near.float().mean()
    mid_pct = mid.float().mean()
    far_pct = far.float().mean()
    # Good composition has ~15-25% near, ~30-50% mid, ~25-40% far
    return min(clip(near_pct / 0.15, 0, 1),
               clip(mid_pct / 0.30, 0, 1),
               clip(far_pct / 0.25, 0, 1))

def r_subject_pop(frame_rgb, subject_mask, background_mask):
    """Dancer visually pops from the background."""
    fg_color = frame_rgb[subject_mask].mean(dim=0)  # mean RGB of subject
    bg_color = frame_rgb[background_mask].mean(dim=0)  # mean RGB of background
    # Color distance in Lab space (perceptually uniform)
    delta_e = lab_distance(rgb_to_lab(fg_color), rgb_to_lab(bg_color))
    return clip(delta_e / 40.0, 0, 1)  # 40 ΔE = very distinct

def r_leading_lines(frame_rgb, subject_uv):
    """Stage edges/props create lines pointing toward the subject."""
    edges = canny_edge_detect(frame_rgb)
    # Compute line directions via Hough transform
    lines = hough_lines(edges)
    # Score: how many lines point within 30° of the subject position
    pointing = sum(1 for line in lines if angle_to_point(line, subject_uv) < 30)
    return clip(pointing / 3.0, 0, 1)  # reward up to 3 leading lines

def r_negative_space(frame_rgb, subject_mask, mode):
    """Empty/filled ratio matches the mode's aesthetic."""
    subject_fill = subject_mask.float().mean()
    target_fill = {
        "HERO": 0.15,      # subject medium-large in frame
        "INTIMATE": 0.25,   # subject large — close framing
        "EPIC": 0.05,       # subject small — vast environment
        "ENERGY": 0.12,     # subject medium
        "SOLITUDE": 0.03,   # subject tiny — vast emptiness
        "BEAUTY": 0.15      # subject medium — balanced
    }[mode]
    return exp(-10 * (subject_fill - target_fill) ** 2)

def r_no_occlusion(drone_pos, dancer_pos, stage_obstacles):
    """No stage element between camera and dancer."""
    ray = (dancer_pos - drone_pos)
    for obs_pos, obs_size in stage_obstacles:
        if ray_intersects_box(drone_pos, ray, obs_pos, obs_size):
            return 0.0  # hard fail — occlusion is never acceptable
    return 1.0

def r_mood_match(stage_state, mode):
    """Environment matches the mode's emotional intent."""
    if mode == "SOLITUDE":
        # Reward: minimal props, low atmosphere, dark floor
        prop_count_penalty = max(0, stage_state.prop_count - 0) * 0.3
        darkness = 1.0 - stage_state.floor_reflectivity
        return darkness - prop_count_penalty
    elif mode == "EPIC":
        # Reward: depth (backdrop far + tall), multiple depth layers
        depth_score = clip(stage_state.backdrop_distance / 8.0, 0, 1)
        height_score = clip(stage_state.backdrop_height / 4.0, 0, 1)
        return 0.5 * depth_score + 0.5 * height_score
    elif mode == "INTIMATE":
        # Reward: enclosed feel (backdrop closer), warm materials
        enclosure = 1.0 - clip(stage_state.backdrop_distance / 5.0, 0, 1)
        return enclosure
    elif mode == "ENERGY":
        # Reward: atmosphere present, music-reactive elements
        return clip(stage_state.atmosphere_density / 0.3, 0, 1)
    elif mode == "HERO":
        # Reward: clean background, platform present
        clean = 1.0 - clip(stage_state.prop_count / 3.0, 0, 1)
        platform = float(stage_state.platform_height > 0.1)
        return 0.5 * clean + 0.5 * platform
    elif mode == "BEAUTY":
        # Reward: cyclorama-like seamless, one accent prop
        seamless = float(stage_state.backdrop_type == "curved")
        one_prop = float(stage_state.prop_count == 1)
        return 0.5 * seamless + 0.5 * one_prop
```

### S3.4 — Training approach

**Sequential training (recommended):**

1. Freeze camera policy (v4 modes, already trained)
2. For each training episode:
   a. Sample a random mode
   b. Load a dancer trajectory
   c. Stage agent adjusts stage elements (warm-started from S1 preset)
   d. Run drone policy for full episode (camera moves, dancer moves)
   e. Every 10th step: render frame through drone camera → compute image rewards
   f. Other steps: proxy geometric rewards (depth distances, occlusion raycasts)
3. Stage agent learns: "for HERO mode, this backdrop position + this floor reflectivity
   produces the highest-scoring frames from the drone's perspective"

**Compute budget:**
- 64 render-in-loop envs + 192 proxy-only envs = 256 total
- 500 iterations warm-up (proxy only) + 300 iterations (with render)
- Estimated: 6-10 hours on A10G, ~$8-10

### Files created (S3)

| File | Purpose | Location |
|---|---|---|
| `stage_design/stage_opt_env.py` | Isaac Lab DirectRLEnv — stage optimization | Deploy to container |
| `stage_design/stage_opt_env_cfg.py` | Environment config | Deploy to container |
| `stage_design/stage_rewards.py` | 7 reward functions (proxy + render-based) | Mac repo + EC2 |
| `stage_design/image_analysis.py` | Depth layers, leading lines, subject pop computation | EC2 |
| `stage_design/deploy/__init__.py` | Task registration for Isaac-StageOpt-Direct-v0 | Deploy to container |
| `stage_design/deploy/agents/rl_games_ppo_cfg.yaml` | Training config | Deploy to container |
| `stage_design/train_stage.sh` | Training launch script | EC2 |

---

## Phase S4 — Asset Library + Retrieval (ongoing)

### S4.1 — Library structure

```
stage_design/asset_library/
├── stages/
│   ├── hero_default.usda           # S1 base template
│   ├── hero_glossy_v2.usda         # Variant from customer project
│   ├── intimate_oak_studio.usda    # Refined from customer feedback
│   ├── intimate_loft.usda          # Customer-specific variant
│   ├── epic_columns.usda
│   ├── energy_festival.usda
│   ├── solitude_void.usda
│   └── beauty_cyclorama.usda
├── textures/                        # Pre-generated PBR texture sets
│   ├── oak_warm/                    # albedo, normal, roughness, metalness, ao
│   ├── glossy_black/
│   ├── concrete_polished/
│   ├── white_cyclorama/
│   └── ...
├── props/                           # Reusable prop USDs
│   ├── column_marble.usda
│   ├── column_concrete.usda
│   ├── fabric_drape_white.usda
│   ├── candle_cluster.usda
│   ├── mirror_tall.usda
│   ├── led_panel_1m.usda
│   ├── truss_section_2m.usda
│   └── ...
├── hdri/                            # Environment maps for EPIC backdrops
│   ├── sunset_golden.hdr
│   ├── overcast_cool.hdr
│   ├── blue_hour.hdr
│   └── ...
└── registry.json                    # Metadata: what each stage was used for, scores
```

### S4.2 — Retrieval system

```python
# stage_design/retrieve_stage.py
def retrieve_best_stage(description: str, mode: str) -> str:
    """Find the best existing stage for a new customer's needs."""
    # 1. Embed the description via CLIP text encoder
    query_embedding = clip_text_encode(description)

    # 2. Compare against registry entries (each has a text description + VLM quality score)
    candidates = []
    for stage in registry:
        if stage.mode == mode or mode is None:
            similarity = cosine_sim(query_embedding, stage.description_embedding)
            score = similarity * 0.6 + stage.quality_score * 0.4
            candidates.append((stage, score))

    # 3. Return top match + customization suggestions
    best = max(candidates, key=lambda x: x[1])
    return best.stage_path, suggest_customizations(best.stage, description)
```

### Files created (S4)

| File | Purpose | Location |
|---|---|---|
| `stage_design/retrieve_stage.py` | CLIP-based stage retrieval | Mac repo |
| `stage_design/asset_library/registry.json` | Stage metadata + quality scores | Mac repo |
| `stage_design/add_to_library.py` | Register a new stage variant after customer delivery | Mac repo |

---

## Coordinate systems (stage-specific)

Stages are authored in **USD Y-up right-hand** coordinate system:
- +X = stage right (audience perspective)
- +Y = up
- +Z = toward audience (downstage)
- Origin (0, 0, 0) = center of stage floor at ground level
- Performer starts near origin
- Backdrop behind performer (negative Z or positive Z depending on stage orientation)

When loading into Isaac Sim for S3 training:
- USD Y-up → Isaac Z-up: (x, y, z) → (x, z, -y) (same proven transform)

Stage boundary aligns with the drone's **fly-to-mark** boundary from ADR-002. In training,
the stage boundary IS the drone's boundary. In production, the drone's fly-to-mark should
approximate the stage template's boundary.

---

## Dependencies on existing systems

| System | What stage uses from it | Connection point |
|---|---|---|
| **Scene Composer Service** (:8005) | Generates base USD for complex stages (city backdrops) | HTTP API, same as existing OSM pipeline |
| **Texture Agent** (:8004) | Generates PBR textures for floor, backdrop, props | HTTP API, per-material |
| **Material Agent** (:8000) | Assigns/validates material properties | HTTP API |
| **Lighting Agent** (L1/L2) | Mode-specific light rig applied to generated stage | Imported as USDA light block |
| **Camera Policy** (v4) | Frozen camera trajectory for S3 training | Checkpoint file |
| **OVRTX** (:8001) | Renders validation grids + S3 reward frames | HTTP API |
| **LiteLLM** (:4000) | LLM stage designer (S2) uses gpt-4o-mini | OpenAI-compatible API |
| **Fly-to-mark** (v1 spec) | Stage boundary = drone boundary | Shared parameter |
| **Music features** | Beat-sync for ENERGY stage LED elements | Existing npz pipeline |

---

## The complete delivery package (what this enables)

With stage + lighting + camera all working:

```
Customer provides:
  - Motion capture data (or rehearsal video)
  - Performance description ("intimate jazz piece, 4 minutes")

Trigunaï delivers:
  1. Virtual stage (generated/selected, textured, lit)
  2. Trained drone camera policy (6 modes, voice-switchable)
  3. Coordinated lighting (mode-matched, beat-synced if music)
  4. Pre-visualization video (dancer on stage, drone-filmed, fully lit)
  5. VR preview (GLB, viewable on Quest 3)
  6. ONNX policy (for real drone hardware deployment)
  7. DMX lighting program (for real stage lights)
  8. Stage design blueprint (for physical set construction)

This is a complete virtual production package, not just a drone policy.
```

---

## EC2 quick reference

```
Instance: TrigunAI-Omniverse (i-047ebf759f2386e71), g5.2xlarge, us-east-1
SSH: ssh -i ~/.ssh/trigunai_key.pem ubuntu@<CURRENT_IP>
Scene Composer: localhost:8005 (TrigunAI service)
Texture Agent: localhost:8004 (NVIDIA Content Agent)
Material Agent: localhost:8000 (NVIDIA Content Agent)
OVRTX: localhost:8001 (renders stage validation frames)
LiteLLM: localhost:4000 (LLM stage designer)
PUBLIC IP CHANGES ON EVERY STOP/START
/tmp IS EPHEMERAL — persist stage assets to /home/ubuntu/stage_assets/
```

---

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| USD prop geometry too complex for real-time rendering | Medium | OVRTX slow, Quest can't display | Decimate aggressively; stage props are background, not hero assets |
| Stage elements occlude dancer from some angles | High | Bad footage | r_no_occlusion reward is hard-fail (0.0); policy learns quickly to avoid |
| Texture Agent generates inconsistent materials | Medium | Stage looks incoherent | Use curated texture presets for S1; AI generation for S2+ only |
| ENERGY beat-sync too distracting | Medium | Lighting + stage + camera all pulsing = chaos | Cap beat-reactive elements: only floor OR wall, not both |
| S3 RL discovers degenerate stages | Medium | Reward hacking: empty stage scores highest | Minimum complexity constraints per mode in reward |
| LLM designer (S2) hallucinates props not in our library | Low | Script fails | Constrain output schema; validate against prop registry |

---

## Session management

After each work session, update `stage_design/SESSION_STAGE.md` with:
- What was accomplished (phase progress)
- Template refinements
- Render comparison results (per-mode validation grids)
- Bugs found and fixed
- EC2 state (which stage assets are on disk, what's ephemeral)
- Next steps
- Any subjective gate results

---

## Project Hub protocol

At **session start**:
1. Read `project_hub/CEO_BRIEFING.md` for cross-agent context
2. Check `project_hub/feedback/*_to_stage*.md` for unread messages
3. Check lighting agent status (stage depends on light rigs being ready)
4. Mark any feedback as `Status: acknowledged` after reading

At **session end**:
1. Update your row in `project_hub/CEO_BRIEFING.md` workstream status table
2. Write feedback to `project_hub/feedback/` if you produced deliverables
3. Update `project_hub/ARTIFACT_REGISTRY.md` with any new files created
4. If S1 or S3 gate was reached, add to `project_hub/GATE_LOG.md`
5. Update `stage_design/SESSION_STAGE.md` with session progress
6. Notify Lighting Agent if new stage templates need light rigs
7. Notify Training Agent if stage geometry changes require drone policy retrain
