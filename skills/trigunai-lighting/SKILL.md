---
name: trigunai-lighting
description: >
  Intelligent lighting system for TrigunAI's cinematographer drone pipeline. Trains RL policies
  to control scene lighting that coordinates with the drone's 6 aesthetic modes (HERO, INTIMATE,
  EPIC, ENERGY, SOLITUDE, BEAUTY). Covers: cinematic lighting presets (Phase L1), RL-optimized
  lighting policy in Isaac Sim (Phase L2), VLM lighting critic (Phase L3), real-world DMX bridge
  (Phase L4). Use when the user mentions "lighting", "lights", "scene lighting", "mood lighting",
  "DMX", "stage lights", "light rig", "3-point lighting", "color temperature", "rim light",
  "key light", "fill light", "light policy", "lighting reward", "cinematic lighting",
  "light presets", "ArtNet", "emotional lighting", "light training", or works on files in
  lighting/ directory. Proactively trigger when a new rendering is produced and lighting looks
  flat or generic, or when mode-switching is discussed without coordinated lighting changes.
---

# TrigunAI Intelligent Lighting Agent

You build an **intelligent lighting system** that coordinates with the cinematographer drone's
6 aesthetic modes. When the director says "hero" — the drone drops low AND the lights shift
to dramatic uplight. One voice command changes both camera and lighting simultaneously.

You operate on a **Mac** (data prep, preset authoring, evaluation scripts) and an **AWS EC2
g5.2xlarge** (Isaac Sim rendering, RL training, OVRTX validation). You are part of the TrigunAI
agent ecosystem alongside the Training Agent, VR Agent, CEO, and Orchestrator.

---

## The problem

The cinematographer drone shoots in 6 aesthetic modes, but lighting is static — flat, uniform,
uninspired. A "HERO" shot with flat lighting doesn't look heroic. An "INTIMATE" shot with
overhead fluorescent doesn't feel intimate. **Lighting is half the emotional signal in
cinematography.** Without intelligent lighting, the 6 modes are doing half the job.

**No existing system combines RL + physically-based rendering + aesthetic scoring for
cinematic scene lighting.** This is a genuine technical gap.

---

## The 6 aesthetic modes (your lighting must serve each)

| Mode | Camera behavior | Lighting intent |
|---|---|---|
| **HERO** | Low-angle power shots, below waist looking up | Dramatic uplighting, hard shadows, strong rim, high contrast (8:1) |
| **INTIMATE** | Close framing, face-focus, eye-level | Soft front fill, warm (3200K), even face lighting, low contrast (2:1) |
| **EPIC** | Wide establishing, bird's-eye moments | Cool wide wash (5600K), rim accents, atmospheric/volumetric |
| **ENERGY** | Fast-paced, beat-synced movement | Multiple colored sources, beat-synced pulses, saturated, high contrast |
| **SOLITUDE** | Isolation framing, large negative space | Single spotlight, tight cone, warm (3500K), 60%+ darkness |
| **BEAUTY** | Balanced composition, rule-of-thirds, orbits | Classic 3-point, golden hour (3500-4500K), soft shadows throughout |

---

## Phase map with gates

| Phase | What you build | Key deliverable | Acceptance gate |
|---|---|---|---|
| **L1** | Cinematic lighting presets per mode | 6 USDA light rigs + renders | Each mode's render looks emotionally distinct (**SUBJECTIVE**) |
| **L2** | RL-optimized lighting policy | Trained policy (.pt) + comparison MP4s | RL-lit renders beat L1 presets on LAION-Aesthetics score AND user preference (**SUBJECTIVE**) |
| **L3** | VLM lighting critic | `evaluate_lighting.py` + calibration data | Critic correctly identifies flat/bad lighting as broken, rates good lighting high |
| **L4** | Real-world DMX bridge | ArtNet sender + venue calibration tool | Light changes visible on real fixtures within 100ms of voice command |

**L1 and L2 have SUBJECTIVE approval gates.** The user/CEO must explicitly approve.

---

## Phase L1 — Cinematic Lighting Presets (no ML, 1-2 weeks)

Encode professional cinematography lighting knowledge as USDA light rigs, one per mode.

### L1.1 — Light rig definitions

Each rig has 3-5 lights. Parameters per light:
- `type`: distant / sphere / rect / disk / dome
- `position`: (x, y, z) in meters, relative to subject center
- `orientation`: aimed at subject (computed from position + target)
- `intensity`: in watts or normalized
- `color_temperature`: in Kelvin (or explicit RGB for ENERGY mode gels)
- `cone_angle`: for spot lights (degrees)
- `softness`: 0.0 (hard point) to 1.0 (large area source)

### L1.2 — The 6 presets (cinematography-grounded)

```
HERO:
  key:  type=spot, pos=(-1.5, 0.3, 2.0), intensity=0.9, color=3800K, cone=40°, softness=0.2
        → Low side key, hard, creates dramatic uplighting on face
  rim:  type=spot, pos=(0.5, 2.5, -1.5), intensity=0.7, color=5600K, cone=60°, softness=0.1
        → High back rim, cool, separates subject from background
  fill: type=rect, pos=(1.5, 1.2, 1.5), intensity=0.1, color=3800K, softness=0.8
        → Minimal fill, maintains contrast ratio ~8:1
  accent: type=spot, pos=(0.0, -0.2, -2.0), intensity=0.3, color=4200K, cone=30°
        → Ground-level backlight for ground plane glow

INTIMATE:
  key:  type=rect, pos=(1.5, 2.0, 1.5), intensity=0.7, color=3200K, softness=0.9
        → Large soft source, 45° above and to the side, wraps around face
  fill: type=rect, pos=(-1.5, 1.5, 1.0), intensity=0.4, color=3400K, softness=0.9
        → Opposite side, 1 stop below key, ratio ~2:1
  back: type=spot, pos=(0.0, 2.0, -1.5), intensity=0.3, color=3500K, cone=50°, softness=0.5
        → Gentle hair/rim light, same warm family
  ambient: type=dome, intensity=0.1, color=3200K
        → Very subtle ambient fill, warm throughout

EPIC:
  wash: type=distant, direction=(0.3, -1.0, 0.2), intensity=0.6, color=5600K
        → Cool daylight directional, wide coverage
  rim_L: type=spot, pos=(-3.0, 2.5, -1.0), intensity=0.5, color=6500K, cone=45°, softness=0.3
        → Cool blue rim, camera-left edge separation
  rim_R: type=spot, pos=(3.0, 2.5, -1.0), intensity=0.5, color=6500K, cone=45°, softness=0.3
        → Matching right rim for symmetry
  atmosphere: type=dome, intensity=0.15, color=5000K
        → Environmental fill, cool neutral
  top: type=spot, pos=(0.0, 5.0, 0.0), intensity=0.3, color=5600K, cone=90°, softness=0.6
        → Top-down for bird's-eye moments

ENERGY:
  color_1: type=spot, pos=(-2.0, 1.5, 1.5), intensity=0.8, color=RGB(255,50,50), cone=35°
        → Red gel, stage-left
  color_2: type=spot, pos=(2.0, 1.5, 1.5), intensity=0.8, color=RGB(50,50,255), cone=35°
        → Blue gel, stage-right
  color_3: type=spot, pos=(0.0, 3.0, -1.0), intensity=0.6, color=RGB(255,100,255), cone=45°
        → Magenta back wash
  strobe: type=spot, pos=(0.0, 2.5, 2.0), intensity=BEAT_SYNCED, color=6500K, cone=60°
        → Beat-synced intensity from music features
  Note: ENERGY mode intensity pulses are driven by music_features[onset] and music_features[rms]
        from the existing music feature pipeline (add_music_features_to_npz.py)

SOLITUDE:
  single: type=spot, pos=(0.0, 3.5, 1.5), intensity=0.9, color=3500K, cone=25°, softness=0.4
        → Single source, tight pool of warm light
  ambient: type=dome, intensity=0.02, color=2800K
        → Barely-there ambient so the rest of the stage is near-black
  Note: This mode intentionally uses minimal lighting. Darkness ratio target: >60%

BEAUTY:
  key:  type=rect, pos=(1.5, 2.0, 1.5), intensity=0.65, color=4000K, softness=0.8
        → Classic 45°/45° key, golden hour warmth
  fill: type=rect, pos=(-1.5, 1.5, 1.0), intensity=0.35, color=4200K, softness=0.9
        → Soft fill, 1 stop below key
  back: type=spot, pos=(0.0, 2.0, -2.0), intensity=0.4, color=4500K, cone=50°, softness=0.5
        → Warm rim/hair separation
  ambient: type=dome, intensity=0.08, color=4000K
        → Golden ambient fill
```

### L1.3 — USDA encoding

Each preset becomes a USDA light block compatible with the existing `render_trained_cinematographer.py`
and `bake_dancer_usda.py` templates. Must match the proven OVRTX-compatible format:

```usda
def SphereLight "KeyLight" {
    float inputs:intensity = 30000
    float inputs:radius = 0.5
    color3f inputs:color = (1.0, 0.85, 0.7)
    float inputs:colorTemperature = 3800
    bool inputs:enableColorTemperature = true
    double3 xformOp:translate = (-1.5, 0.3, 2.0)
    token[] xformOpOrder = ["xformOp:translate"]
}
```

### L1.4 — Integration with existing render pipeline

The render scripts (`render_trained_cinematographer.py`, `render_dancer_mp4.py`) currently
hardcode a basic 3-light setup. Replace with a `get_light_rig(mode: str) -> str` function
that returns the USDA light block for the given mode.

**Critical:** When the mode changes during a trajectory (voice command "switch to hero"),
lights must transition smoothly — not snap-cut. Implement a 1-second linear interpolation
of intensity + color temperature between the old and new preset.

### L1.5 — Validation renders

**Video rendering:** See `VIDEO_RENDERING.md` for the master reference. Use Blender EEVEE (0.33s/frame) instead of OVRTX (6s/frame) — 18x faster.

For each mode, render the same 5s dancer clip with the mode's lighting preset AND with
flat default lighting. Produce a 2×6 comparison grid (flat vs preset, all 6 modes).
This is the L1 gate artifact — CEO reviews and approves.

### Files created (L1)

| File | Purpose | Location |
|---|---|---|
| `lighting/presets.py` | 6 preset definitions (dataclass per mode, USDA generation) | Mac repo |
| `lighting/usda_lights.py` | USDA light block generator (mode → USDA string) | Mac repo |
| `lighting/render_lighting_comparison.py` | Renders 2×6 comparison grid | Deploy to EC2 |
| `lighting/transition.py` | Smooth interpolation between presets | Mac repo |
| `lighting/SESSION_LIGHTING.md` | Session notes for CEO agent | Mac repo |

---

## Phase L2 — RL-Optimized Lighting Policy (4-6 weeks)

Train an RL agent in Isaac Sim that learns to place and adjust lights per mode, using
rendered frame quality as reward.

### L2.1 — Environment: `LightingEnv` (DirectRLEnv)

```
Isaac Lab environment: Isaac-Lighting-Direct-v0

Observation space (52 dims):
├── dancer_pose_relative (15 bodies × 3 = 45)  — from existing pipeline
├── drone_camera_pos_relative (3)               — from cinematographer env
├── current_mode_onehot (6)                     — which aesthetic mode
├── current_light_states_summary (N × params)   — compact state of each light
│   For N=3 lights: 3 × (azimuth, elevation, intensity, color_temp_norm) = 12
│   BUT: keep obs compact. Use relative angles, not absolute positions.
│   Actual: 3 lights × 4 params = 12 → total 52 dims
└── Total: 45 + 3 + 6 + 12 = 66 dims (adjusted from initial estimate)

Action space (18 continuous):
For each of 3 lights (key, fill, back/rim):
├── delta_azimuth     (-10° to +10° per step)
├── delta_elevation   (-10° to +10° per step)
├── delta_intensity   (-0.1 to +0.1, normalized 0-1)
├── delta_color_temp  (-200K to +200K per step, clamped 2500-7000K)
├── delta_cone_angle  (-5° to +5° per step, clamped 10-120°)
└── delta_softness    (-0.1 to +0.1, clamped 0-1)
Total: 3 × 6 = 18

Episode: one full mode sequence (5-10 seconds at 10 Hz lighting rate)
```

### L2.2 — Reward function (8 terms, per-frame from rendered image)

```python
@dataclass
class LightingRewardCfg:
    # --- weights ---
    w_exposure: float = 0.15        # no blown highlights or crushed blacks
    w_face_light: float = 0.20      # subject face must be lit (not silhouetted)
    w_contrast: float = 0.10        # foreground-background luminance separation
    w_shadow_quality: float = 0.10  # mode-dependent: HERO=hard, INTIMATE=soft
    w_color_harmony: float = 0.05   # color temp consistency (except ENERGY)
    w_mood_match: float = 0.20      # per-mode aesthetic prior (see below)
    w_smoothness: float = 0.10      # penalize rapid light changes (no flicker)
    w_aesthetic: float = 0.10       # LAION-Aesthetics score on rendered frame
```

### L2.3 — Per-mode mood_match reward specifications

```python
def r_mood_match(frame, mode, light_states):
    if mode == "HERO":
        # Reward: contrast ratio > 4:1, rim light detected, low key angle
        contrast = compute_contrast_ratio(frame)
        rim = detect_rim_light(frame)  # bright edge on subject outline
        return 0.5 * clip(contrast / 8.0, 0, 1) + 0.5 * rim

    elif mode == "INTIMATE":
        # Reward: face evenly lit, warm color, low contrast
        face_evenness = compute_face_lighting_evenness(frame)
        warm = 1.0 - abs(mean_color_temp(light_states) - 3200) / 2000
        return 0.6 * face_evenness + 0.4 * clip(warm, 0, 1)

    elif mode == "EPIC":
        # Reward: wide coverage, cool tones, edge separation
        coverage = compute_light_coverage(frame)  # % of frame > 10% brightness
        cool = 1.0 - abs(mean_color_temp(light_states) - 5600) / 2000
        return 0.5 * coverage + 0.5 * clip(cool, 0, 1)

    elif mode == "ENERGY":
        # Reward: color variation, beat sync, high saturation
        color_var = compute_color_diversity(frame)  # HSV saturation spread
        beat_sync = music_onset_correlation(light_states.intensity_history)
        return 0.5 * color_var + 0.5 * beat_sync

    elif mode == "SOLITUDE":
        # Reward: darkness ratio > 60%, single dominant source
        darkness = compute_darkness_ratio(frame)  # % of pixels < 10% brightness
        single_source = 1.0 - light_source_spread(light_states)
        return 0.5 * clip(darkness / 0.7, 0, 1) + 0.5 * single_source

    elif mode == "BEAUTY":
        # Reward: golden color temp, 3-point coverage, soft shadows
        golden = 1.0 - abs(mean_color_temp(light_states) - 4000) / 1500
        three_point = detect_three_point_coverage(frame)
        shadow_soft = compute_shadow_softness(frame)
        return 0.33 * clip(golden, 0, 1) + 0.33 * three_point + 0.34 * shadow_soft
```

### L2.4 — Image-based reward computation

**The render-in-the-loop problem:** Computing rewards from rendered frames is expensive
(~0.5-1s per frame on OVRTX). Two strategies:

1. **Proxy rewards (fast, used 90% of steps):** Geometric calculations only — light angles
   relative to subject, intensity ratios, color temperature values. No actual render needed.
   These are the "physics" of lighting — they correlate with visual quality.

2. **Render rewards (slow, used every 10th step):** Actually render the frame via Isaac Sim's
   RTX path tracer. Run LAION-Aesthetics scorer + custom image analysis. These are the
   "ground truth" of visual quality.

Training loop: proxy rewards guide the agent 90% of the time (fast, 50Hz RL rate).
Every 10th step, render + score the frame, and use the render reward to correct the
proxy (reward shaping calibration).

### L2.5 — LAION-Aesthetics integration

```bash
# Install on EC2 (one-time)
pip install --user open_clip_torch
# Download predictor weights
wget https://github.com/christophschuhmann/improved-aesthetic-predictor/raw/main/sac+logos+ava1-l14-linearMSE.pth
```

```python
# In reward computation
import open_clip
model, preprocess, _ = open_clip.create_model_and_transforms('ViT-L-14', pretrained='openai')
# ... encode rendered frame → CLIP embedding → linear aesthetic predictor → score 1-10
```

**Cost:** ~10ms per frame on A10G. Lightweight enough for every-10th-step scoring.

### L2.6 — Joint training with camera policy

The lighting agent sees the camera position as part of its observation. This means lighting
adapts to where the camera is — when the drone moves behind the subject, the lighting
compensates so the subject's face stays lit from the camera's perspective.

**Two training approaches:**

**Option A: Sequential (simpler, recommended for L2).**
1. Train camera policy first (already done — v4 modes checkpoint exists)
2. Freeze camera policy
3. Train lighting policy to optimize for the frozen camera's perspective
4. Result: lighting adapts to the trained camera behavior

**Option B: Joint (harder, for L2+).**
1. Train both policies simultaneously, each receiving the other's state as observation
2. Camera learns "this lighting setup makes my current angle look better"
3. Lighting learns "the camera is moving here, I should prepare"
4. Result: coordinated camera+lighting behavior

Start with Option A. Upgrade to Option B only if customer demos need it.

### L2.7 — Training recipe

```
Hardware: EC2 g5.2xlarge, A10G
Envs: 64 (render-in-loop limits parallelism)
Proxy-only envs: 192 (no render, geometric rewards only)
Total: 256 envs
Iterations: 1000 (proxy-only warm-up) + 500 (with render rewards)
Estimated time: 8-12 hours (most time is rendering)
Estimated cost: ~$10-12
```

### Files created (L2)

| File | Purpose | Location |
|---|---|---|
| `lighting/lighting_env.py` | Isaac Lab DirectRLEnv — lighting agent | Deploy to container |
| `lighting/lighting_env_cfg.py` | Environment config | Deploy to container |
| `lighting/lighting_rewards.py` | 8 reward functions (proxy + render-based) | Mac repo + EC2 |
| `lighting/image_rewards.py` | Image-based reward computation (LAION + custom) | EC2 |
| `lighting/deploy/__init__.py` | Task registration for Isaac-Lighting-Direct-v0 | Deploy to container |
| `lighting/deploy/agents/rl_games_ppo_cfg.yaml` | rl_games PPO config | Deploy to container |
| `lighting/train_lighting.sh` | Training launch script | EC2 |

---

## Phase L3 — VLM Lighting Critic (1 week)

Same pattern as the drone VLM evaluator. Uses the existing LiteLLM proxy (port 4000) and
gpt-4o-mini to grade lighting quality.

### L3.1 — Evaluation script

```python
# evaluate_lighting.py
# Input: rendered frame (PNG or MP4 keyframes)
# Output: JSON with per-dimension scores + verdict

system_prompt = """
You are a professional cinematography lighting director. You are evaluating lighting
for a {mode} shot of a dancer.

**CRITICAL: First verify the scene is actually lit — not pitch black or blown out.**
If the scene appears to have no intentional lighting (flat ambient only), set all
scores to 1 and verdict to "flat-lighting".

Rate each dimension 1-10:
- key_light_placement: Is the main light source positioned correctly for {mode}?
- fill_ratio: Is the shadow-to-light ratio appropriate for {mode}?
- color_temperature: Does the warmth/coolness match {mode}'s emotional intent?
- shadow_quality: Are shadows {hard/soft} as appropriate for {mode}?
- mood_conveyance: Does the lighting actually convey {mode_emotion}?
- overall_cinematic_quality: Would a professional DP approve this lighting?

Per-mode expectations:
  HERO: dramatic contrast, uplighting, strong rim, hard shadows
  INTIMATE: soft wrap, warm, face clearly visible, gentle shadows
  EPIC: cool wide wash, environmental, rim accents
  ENERGY: colorful, high contrast, dynamic feel
  SOLITUDE: single source, mostly dark, isolated pool of light
  BEAUTY: golden warmth, classic 3-point, flattering

Return JSON only: {{scores, issues, verdict}}
verdict: "cinematic" (7+ overall) | "acceptable" (5-6) | "flat-lighting" (<5) | "broken" (1-2)
"""
```

### L3.2 — Calibration

Run the critic on:
1. All 6 L1 presets → should score 6-8 (good presets, not perfect)
2. Flat default lighting → should score 1-3 ("flat-lighting" verdict)
3. L2-trained lighting → should score 7-10 if training worked
4. Intentionally bad lighting (subject silhouetted, blown highlights) → should score 1-2

If the critic doesn't match these expectations, adjust the system prompt.

### Files created (L3)

| File | Purpose | Location |
|---|---|---|
| `lighting/evaluate_lighting.py` | VLM critic for lighting quality | Mac repo + EC2 |
| `lighting/calibration_data/` | Reference renders for critic calibration | Mac repo |

---

## Phase L4 — Real-World DMX Bridge (2-3 weeks)

Map trained lighting policy outputs to real stage lights via ArtNet/DMX512.

### L4.1 — Protocol stack

```
Trained policy (ONNX, runs on companion computer or base station)
  ↓ 10-50 Hz light parameter updates
  ↓
ArtNet sender (Python, UDP packets over WiFi/ethernet)
  ↓ standard ArtNet → DMX protocol
  ↓
ArtNet node ($50-150 hardware, e.g., DMXKing ultraDMX)
  ↓ DMX512 signal (RS-485, 250kbaud)
  ↓
Stage fixtures (moving heads, LED pars, fresnels)
```

### L4.2 — Parameter mapping

```python
# Policy output → DMX channels
def policy_to_dmx(light_params, fixture_profile):
    """Map trained policy's abstract light parameters to physical DMX channels."""
    dmx = {}
    for i, light in enumerate(light_params):
        base_ch = fixture_profile[i].start_channel
        dmx[base_ch + 0] = angle_to_pan(light.azimuth)      # 0-255 (0-540°)
        dmx[base_ch + 1] = angle_to_pan_fine(light.azimuth)  # fine pan
        dmx[base_ch + 2] = angle_to_tilt(light.elevation)    # 0-255 (0-270°)
        dmx[base_ch + 3] = angle_to_tilt_fine(light.elevation)
        dmx[base_ch + 4] = int(light.intensity * 255)        # dimmer
        dmx[base_ch + 5] = temp_to_color_wheel(light.color_temp, fixture_profile[i])
        dmx[base_ch + 6] = int(light.cone_angle / 120 * 255) # zoom
    return dmx
```

### L4.3 — Venue calibration: fly-to-mark for lights

Same principle as the drone boundary setup:

```
Operator points fixture 1 at stage center → presses MARK → system records
  fixture 1 pan/tilt → center = (pan_center, tilt_center)
Operator points fixture 1 at stage left edge → MARK → records left extent
Operator points fixture 1 at stage right edge → MARK → records right extent
System now knows: fixture 1 range, center, and how pan/tilt map to stage positions
Repeat for each fixture

Result: lookup table mapping policy's abstract (azimuth, elevation) to each
        fixture's specific (pan, tilt) range. One-time per venue, ~5 min.
```

### L4.4 — Latency budget

```
Voice command → Whisper STT:       ~200ms
STT → mode switch command:          ~5ms
Mode switch → lighting policy:      ~10ms (ONNX inference)
Policy → ArtNet packet:             ~1ms
ArtNet → DMX → fixture response:   ~50-100ms (moving head motor lag)
                                    ─────────
Total:                              ~300ms
```

300ms is below the threshold for perceptible delay. Director says "hero" → lights shift
before the drone has even started its transition (drone response ~2s).

### Files created (L4)

| File | Purpose | Location |
|---|---|---|
| `lighting/dmx_bridge.py` | ArtNet sender + policy-to-DMX mapping | Base station |
| `lighting/venue_calibration.py` | Fly-to-mark for light fixtures | Base station |
| `lighting/fixture_profiles/` | DMX channel profiles for common fixtures | Mac repo |
| `lighting/artnet_test.py` | Test script: cycle through all 6 modes on real fixtures | Base station |

---

## Reward function details (Phase L2, complete reference)

### r_exposure (weight 0.15)

```python
def r_exposure(frame_rgb):
    """Penalize blown highlights and crushed blacks."""
    luminance = 0.299 * frame_rgb[..., 0] + 0.587 * frame_rgb[..., 1] + 0.114 * frame_rgb[..., 2]
    blown = (luminance > 0.95).float().mean()   # % of pixels > 95% brightness
    crushed = (luminance < 0.05).float().mean()  # % of pixels < 5% brightness
    # Allow some crushed blacks for SOLITUDE mode (handled by mood_match)
    return exp(-10 * max(0, blown - 0.05)) * exp(-5 * max(0, crushed - 0.30))
```

### r_face_light (weight 0.20)

```python
def r_face_light(frame_rgb, subject_head_uv):
    """Subject's face region must be lit, not silhouetted."""
    # Extract 64×64 crop around subject head position (projected to image UV)
    face_crop = extract_crop(frame_rgb, subject_head_uv, size=64)
    face_brightness = face_crop.mean()
    # Face brightness should be > 0.3 (visible) but < 0.9 (not blown)
    return exp(-5 * max(0, 0.3 - face_brightness)) * exp(-5 * max(0, face_brightness - 0.9))
```

### r_contrast (weight 0.10)

```python
def r_contrast(frame_rgb, subject_mask):
    """Foreground-background luminance separation (subject should 'pop')."""
    fg_lum = luminance(frame_rgb * subject_mask).mean()
    bg_lum = luminance(frame_rgb * (1 - subject_mask)).mean()
    separation = abs(fg_lum - bg_lum)
    return clip(separation / 0.3, 0, 1)  # max reward at 30% luminance difference
```

### r_shadow_quality (weight 0.10)

```python
def r_shadow_quality(frame_rgb, mode):
    """Mode-dependent shadow hardness."""
    # Compute shadow edge gradient (Sobel on luminance, in shadow regions)
    shadow_edge_sharpness = compute_shadow_edge_gradient(frame_rgb)
    if mode in ["HERO", "ENERGY"]:
        return clip(shadow_edge_sharpness / 0.5, 0, 1)  # reward HARD shadows
    elif mode in ["INTIMATE", "BEAUTY"]:
        return 1.0 - clip(shadow_edge_sharpness / 0.5, 0, 1)  # reward SOFT shadows
    elif mode == "SOLITUDE":
        return 0.5  # neutral — shadow quality less important than darkness ratio
    elif mode == "EPIC":
        return 0.5 + 0.5 * clip(shadow_edge_sharpness / 0.3, 0, 1)  # slightly hard
```

### r_color_harmony (weight 0.05)

```python
def r_color_harmony(light_states, mode):
    """Color temperature consistency across sources (except ENERGY)."""
    temps = [l.color_temp for l in light_states]
    if mode == "ENERGY":
        # ENERGY rewards color DIVERSITY, not harmony
        return clip(std(temps) / 1500, 0, 1)
    else:
        # Other modes reward consistency within ±500K
        return exp(-0.5 * (std(temps) / 500) ** 2)
```

### r_smoothness (weight 0.10)

```python
def r_smoothness(light_states, prev_light_states):
    """Penalize rapid light changes (flickering is distracting)."""
    delta_intensity = sum(abs(l.intensity - p.intensity) for l, p in zip(light_states, prev_light_states))
    delta_temp = sum(abs(l.color_temp - p.color_temp) for l, p in zip(light_states, prev_light_states)) / 1000
    return exp(-5 * (delta_intensity + delta_temp))
```

### r_aesthetic (weight 0.10)

```python
def r_aesthetic(frame_rgb):
    """LAION-Aesthetics score (pretrained CLIP + linear predictor)."""
    # Only computed every 10th step (render-in-loop)
    embedding = clip_model.encode_image(preprocess(frame_rgb))
    score = aesthetic_predictor(embedding)  # 1-10 scale
    return clip(score / 10, 0, 1)
```

---

## Dependencies on existing systems

| System | What lighting uses from it | Connection point |
|---|---|---|
| **Cinematographer env (v4)** | 6 mode definitions, mode one-hot encoding | `cinematographer_env_cfg_v4.py` |
| **Camera policy (v4 checkpoint)** | Frozen camera trajectory for L2 training | `cinematography/checkpoints/cinematographer_v4_modes_best.pth` |
| **Music features** | Beat/onset/RMS for ENERGY mode beat-sync | `add_music_features_to_npz.py` pipeline |
| **OVRTX renderer** | Renders frames for L2 image-based rewards | Port 8001, same container |
| **LiteLLM proxy** | VLM critic for L3 | Port 4000, gpt-4o-mini |
| **bake_dancer_usda.py** | Light rig injection point for renders | `cinematography/bake_dancer_usda.py` |
| **render_trained_cinematographer.py** | Light rig injection point for MP4 renders | `cinematography/render_trained_cinematographer.py` |
| **Voice command layer (v1 spec)** | Mode switch triggers coordinated light change | Not yet built — lighting agent provides the light-side response |

---

## Data inputs and outputs

### Inputs the lighting system consumes

| Data | Source | Format | Path |
|---|---|---|---|
| Dancer mocap | Quest sessions | .npz (AMP format) | `mocap_handoff/Mocap/` |
| Camera trajectory | Trained drone policy | .json (per-frame pos/quat) | `cinematography/cinematographer_trajectory.json` |
| Music features | `add_music_features_to_npz.py` | 9 floats/frame in .npz | `checkpoints/gurulok_dance_v2_with_music.npz` |
| Mode schedule | Voice commands (runtime) or preset sequence (training) | one-hot vector | Real-time input |

### Outputs the lighting system produces

| Artifact | Consumer | Format | Gate |
|---|---|---|---|
| 6 USDA light rigs | Render pipeline (OVRTX) | USDA string blocks | L1 gate |
| Trained lighting policy | DMX bridge / ONNX export | .pt checkpoint | L2 gate |
| Lit demo MP4s | Customer demos, CEO review | H.264 MP4 | L1/L2 gate |
| Lighting evaluation JSON | CEO, quality tracking | JSON (scores + verdict) | L3 calibration |
| DMX output stream | Real stage fixtures | ArtNet UDP packets | L4 gate |
| ONNX lighting policy | Starling 2 companion / base station | ONNX (<20 MB) | Post-L4 |

---

## Coordinate systems (lighting-specific)

Lights are defined in **USD Y-up right-hand** coordinate system (same as OVRTX rendering):
- +X = stage right
- +Y = up
- +Z = toward audience (front of stage)
- Subject (dancer) at approximately (0, 0, 0) to (0, 1.7, 0) height range

The RL environment uses **Isaac Sim Z-up right-hand** coordinates internally. Convert
light positions when moving between training and rendering:
- Isaac (x, y, z) → USD (x, z, -y)
- Same transform as the camera/drone pipeline (already proven)

---

## Research references used in this design

| Reference | What we use from it |
|---|---|
| LLM-AMMARL (Feb 2026) | Pattern: LLM semantic intent → RL light control |
| LAION-Aesthetics Predictor | Pretrained aesthetic scorer as reward signal |
| Skip-BART (ICLR 2026) | Proof that ML lighting matches human engineers on stage |
| Neurophysiology CCT study (2024) | Empirical color temp → emotion mappings |
| PBDR survey (2025) | Differentiable rendering as alternative to RL for L2+ |
| Neural Gaffer (NeurIPS 2024) | Single-image relighting via diffusion (future reference) |

---

## EC2 quick reference

```
Instance: TrigunAI-Omniverse (i-047ebf759f2386e71), g5.2xlarge, us-east-1
SSH: ssh -i ~/.ssh/trigunai_key.pem ubuntu@<CURRENT_IP>
OVRTX: localhost:8001 (check gpu_initialized; 6 min cold start)
LiteLLM: localhost:4000 (master key: sk-trigunai-master-key-2026)
isaaclab container: sudo docker start isaaclab
Blender: /opt/blender45 (symlink: blender45)
PUBLIC IP CHANGES ON EVERY STOP/START — always check AWS console
/tmp IS EPHEMERAL — wiped on EC2 stop, persist to /home/ubuntu/
LAION-Aesthetics model: install to /home/ubuntu/models/ (EBS persistent)
```

---

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OVRTX render-in-loop too slow for RL | High | L2 training takes days | Proxy rewards for 90% of steps; render only every 10th |
| LAION-Aesthetics doesn't discriminate lighting quality | Medium | L2 reward is noisy | Supplement with geometric proxy rewards; VLM critic (L3) as calibration |
| L1 presets look good enough, L2 doesn't improve | Medium | Wasted 4-6 weeks | Run L1 → customer demo first. Only proceed to L2 if customers want "adaptive" |
| DMX latency too high for real-time | Low | L4 feels sluggish | ArtNet is UDP, <5ms. Fixture motor lag is the bottleneck (~100ms) — acceptable |
| ENERGY mode beat-sync requires music in training | Medium | Can't train without audio | Music features already exist in pipeline; extend to lighting obs space |
| Isaac Sim light API differs from USDA format | Medium | Training/rendering mismatch | Validate: render one frame in Isaac Sim, same frame via OVRTX, compare |

---

## Build sequence recommendation

| Phase | Effort | Prerequisite | Impact on demos |
|---|---|---|---|
| **L1 — Presets** | 1-2 weeks | None | HIGH — immediately improves all demo videos |
| **L3 — VLM critic** | 1 week | L1 (needs renders to evaluate) | Medium — quality assurance |
| **L2 — RL training** | 4-6 weeks | L1 (warm start), L3 (evaluation) | HIGH — adaptive lighting |
| **L4 — DMX bridge** | 2-3 weeks | L2 (trained policy) | HIGH for live demos |

**Recommended order: L1 → L3 → L2 → L4.** Build presets first (demo impact), add critic
(evaluation), then train the RL policy (intelligence), then bridge to real hardware.

---

## Session management

After each work session, update `lighting/SESSION_LIGHTING.md` with:
- What was accomplished (phase progress)
- Bugs found and fixed
- EC2 state (container status, checkpoint paths, what's ephemeral)
- Render comparison results (preset vs flat, RL vs preset)
- Next steps
- Any subjective gate results

---

## Project Hub protocol

At **session start**:
1. Read `project_hub/CEO_BRIEFING.md` for cross-agent context
2. Check `project_hub/feedback/*_to_lighting*.md` for unread messages
3. Check the camera policy's current training state (lighting depends on camera trajectory)
4. Mark any feedback as `Status: acknowledged` after reading

At **session end**:
1. Update your row in `project_hub/CEO_BRIEFING.md` workstream status table
2. Write feedback to `project_hub/feedback/` if you produced deliverables (lit renders, etc.)
3. Update `project_hub/ARTIFACT_REGISTRY.md` with any new files created
4. Update `project_hub/DATA_INVENTORY.md` if you added/moved files on EC2
5. If L1 or L2 gate was reached, add to `project_hub/GATE_LOG.md`
6. Update `lighting/SESSION_LIGHTING.md` with session progress
7. If lighting presets changed, notify the Training Agent (renders need rebuilding)
