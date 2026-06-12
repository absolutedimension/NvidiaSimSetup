# ADR-003 — MVP Sprint Plan: 2-Week Complete Demo

> Date: 2026-05-25
> Status: LOCKED
> Decision by: Deepak (CEO)

## Goal

Assemble a complete, customer-showable demo in 2 weeks by plugging in best-in-market
services for every non-core layer, instead of building from scratch.

**What "complete demo" means:** A 90-second video showing a real-looking character
dancing on a beautiful mode-appropriate stage, filmed by the trained drone, with
cinematic lighting, with voice commands switching modes mid-flight. Plus a side-by-side
"before/after" (grey void vs full production) to show the value.

---

## What already works (no build needed)

| Asset | Status | Path |
|---|---|---|
| Camera policy v4 (6 modes, PPO trained) | ✅ | `cinematography/checkpoints/cinematographer_v4_modes_best.pth` |
| Trajectory export script | ✅ | `cinematography/export_cinematographer_trajectory.py` |
| USDA scene builder | ✅ | `cinematography/render_trained_cinematographer.py` |
| Orbital baseline builder | ✅ | `cinematography/bake_dancer_usda.py` |
| OVRTX renderer | ✅ | EC2 port 8001 |
| Texture Agent | ✅ | EC2 port 8004 |
| Material Agent | ✅ | EC2 port 8000 |
| Scene Composer | ✅ | EC2 port 8005 |
| LiteLLM proxy (gpt-4o-mini) | ✅ | EC2 port 4000 |
| VLM critic | ✅ | `evaluate_drone_trajectory.py` pattern |
| 25s drone-POV video (stick figure, grey floor) | ✅ | `cinematography/drone_pov_25s.mp4` |
| 25s orbital baseline | ✅ | `cinematography/dancer_orbital_25s.mp4` |
| Daphne CC4 retargeter | ✅ | `mocap_handoff/bake_daphne_animation.py` |
| Mocap data (9 sessions, cosmic-hypnotic) | ✅ | Local backups + EC2 EBS |

## What needs building (the 2-week sprint)

---

## WEEK 1: Assets + Integration (build the pieces)

### Day 1 — Stage environments via HDRIs

**Task:** Generate 6 environment HDRIs (one per mode) and integrate into the render pipeline.

**Service: Blockade Labs Skybox AI**
- API: `https://backend.blockadelabs.com/api/v1/skybox`
- Cost: $0.30/skybox on free tier, or free trial credits
- Output: 4096×2048 equirectangular HDRI per prompt

**6 prompts to generate:**

```
HERO:     "dark dramatic concert stage, single harsh spotlight from below,
           black void background, theatrical, cinematic, moody, concert photography"

INTIMATE: "warm cozy dance studio interior, honey oak wood floor, cream fabric
           curtains, soft candles along walls, golden hour light, intimate, warm"

EPIC:     "vast outdoor amphitheater at golden hour, mountain panorama background,
           stone architecture, epic wide vista, dramatic sky, cinematic landscape"

ENERGY:   "neon concert festival stage, LED panels purple and blue, laser beams
           through haze, DJ booth, intense lighting, electronic music festival"

SOLITUDE: "infinite black void, single pool of warm light on dark floor,
           minimalist, lonely, vast empty space, darkness, isolation"

BEAUTY:   "professional photography studio, white infinity cove, soft diffused
           lighting, clean elegant space, seamless background, fashion studio"
```

**Integration point:** Modify `render_trained_cinematographer.py` to accept a `--hdri` flag:

```python
# In build_usda(), replace the current hardcoded lights section with:
def get_environment_block(mode, hdri_path=None):
    if hdri_path:
        return f'''
    def DomeLight "Environment"
    {{
        asset inputs:texture:file = @{hdri_path}@
        float inputs:intensity = 1.0
        token inputs:textureFormat = "latlong"
    }}'''
    else:
        return get_default_lights()  # current 3-light setup as fallback
```

**Deliverable:** 6 HDRI files in `stage_design/hdri/`, render script modified.

**Verification:** Render one 5s test clip with HERO HDRI. Compare against grey-floor version.
If OVRTX doesn't support HDRI dome lights via data URI, fallback plan: use the HDRIs in
Blender (which definitely supports them) and render there instead of OVRTX.

---

### Day 2 — Lighting presets (Poly Haven + Blender)

**Task:** Download 6 professional lighting HDRIs and create matching USDA light rigs.

**Service: Poly Haven (polyhaven.com)**
- Cost: $0 (CC0 license, no attribution required)
- Format: .hdr or .exr, 1K-8K resolution

**6 downloads:**

| Mode | Poly Haven HDRI | Why |
|---|---|---|
| HERO | `studio_small_08` (dark dramatic) | Strong directional key, dark background |
| INTIMATE | `dancing_hall` or `studio_small_09` | Warm, enclosed, soft |
| EPIC | `kloofendal_48d_partly_cloudy` | Outdoor, golden hour, vast |
| ENERGY | `neon_photostudio` | Colorful, high contrast |
| SOLITUDE | `moonless_golf` (dark night) | Near-black, minimal light |
| BEAUTY | `photo_studio_loft_hall` | Clean, balanced, studio |

**Plus: 6 USDA light rigs** as supplements (HDRIs provide ambient, these add directed key/fill):

```python
# lighting/presets.py
LIGHT_PRESETS = {
    "HERO": {
        "key":  {"type": "spot", "pos": (-1.5, 0.3, 2.0), "intensity": 50000,
                 "color": (1.0, 0.85, 0.7), "cone": 40},
        "rim":  {"type": "spot", "pos": (0.5, 2.5, -1.5), "intensity": 35000,
                 "color": (0.8, 0.85, 1.0), "cone": 60},
    },
    "INTIMATE": {
        "key":  {"type": "rect", "pos": (1.5, 2.0, 1.5), "intensity": 25000,
                 "color": (1.0, 0.9, 0.8), "width": 1.0, "height": 0.8},
        "fill": {"type": "rect", "pos": (-1.5, 1.5, 1.0), "intensity": 12000,
                 "color": (1.0, 0.92, 0.85), "width": 1.0, "height": 0.8},
    },
    # ... etc for all 6 modes
}

def preset_to_usda(mode: str) -> str:
    """Return USDA light block for the given mode."""
    preset = LIGHT_PRESETS[mode]
    blocks = []
    for name, cfg in preset.items():
        blocks.append(f'''
    def {"SphereLight" if cfg["type"] == "spot" else "RectLight"} "{name.title()}Light"
    {{
        float inputs:intensity = {cfg["intensity"]}
        color3f inputs:color = {cfg["color"]}
        double3 xformOp:translate = {cfg["pos"]}
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }}''')
    return "\n".join(blocks)
```

**Deliverable:** `lighting/presets.py` with all 6 rigs + 6 HDRI files downloaded.

---

### Day 3 — Replace stick figure with Daphne (or Mixamo character)

**Task:** Swap the orange-sphere stick figure for a real human character in renders.

**Option A: Daphne (already have her)**
- `mocap_handoff/bake_daphne_animation.py` already works
- 14 MB GLB, fully rigged, mocap-retargeted
- Problem: need to convert GLB → USD for OVRTX rendering (or render in Blender)

**Option B: Mixamo (backup, free)**
- mixamo.com → pick character → download FBX → Blender retarget → export
- More variety of characters available

**The fast path:**
Use **Blender as the renderer** instead of OVRTX for the final demo videos. Blender:
- Supports HDRI environments natively (Cycles/EEVEE)
- Supports GLB/FBX characters natively
- Supports USD import (we installed Blender 4.5 LTS for exactly this)
- Already on EC2 at `/opt/blender45`

This means: OVRTX renders the quick test clips (fast, API-based). Blender renders the
final demo videos (beautiful, supports full materials + HDRIs + characters).

**Blender render script (new):**

```python
# stage_design/render_demo_blender.py
"""
Render the complete demo in Blender: character + stage HDRI + lighting + drone camera path.

Usage:
    blender45 --background --python render_demo_blender.py -- \
        --character /home/ubuntu/daphne.glb \
        --trajectory /home/ubuntu/cinematographer_trajectory.json \
        --hdri /home/ubuntu/hdri/hero.hdr \
        --lighting-preset HERO \
        --out /home/ubuntu/demo_hero_25s.mp4 \
        --width 1920 --height 1080 --fps 30 --engine EEVEE
```

Script workflow:
1. Import character GLB (Daphne or Mixamo)
2. Apply dancer trajectory as keyframes on character armature
3. Set world HDRI from --hdri flag
4. Add USDA-equivalent lights from --lighting-preset
5. Create camera and animate it along drone trajectory
6. Render to PNG sequence → ffmpeg → MP4

**EEVEE vs Cycles:**
- EEVEE: ~0.5s/frame on A10G, 750 frames × 0.5s = ~6 min per 25s video. Use this.
- Cycles: ~10s/frame, 2+ hours per video. Too slow for iteration.

**Deliverable:** `stage_design/render_demo_blender.py` script, first test render of
Daphne on HERO stage.

---

### Day 4 — Voice command integration

**Task:** Wire Deepgram STT to mode switching.

**Service: Deepgram Nova-2**
- API: `wss://api.deepgram.com/v1/listen`
- Latency: ~200ms (streaming mode)
- Cost: $0.0043/min, $200 free credit on signup
- Accuracy: best-in-class for short commands

**Script: `voice/voice_commander.py`**

```python
#!/usr/bin/env python3
"""Real-time voice → mode switching for the cinematographer drone.

Listens to microphone, recognizes mode commands, outputs mode changes
to stdout (for piping to the policy runner) or WebSocket (for live demo).

Usage:
    python voice_commander.py --api-key $DEEPGRAM_KEY --output ws://localhost:9000
    # Or for demo recording:
    python voice_commander.py --api-key $DEEPGRAM_KEY --output log --log-file commands.json
"""
import asyncio
import json
import sys
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

MODE_COMMANDS = {
    # Mode switches
    "hero": {"type": "mode", "value": 0},
    "power": {"type": "mode", "value": 0},
    "intimate": {"type": "mode", "value": 1},
    "close": {"type": "mode", "value": 1},
    "close up": {"type": "mode", "value": 1},
    "epic": {"type": "mode", "value": 2},
    "wide": {"type": "mode", "value": 2},
    "go high": {"type": "mode", "value": 2},
    "energy": {"type": "mode", "value": 3},
    "fast": {"type": "mode", "value": 3},
    "solitude": {"type": "mode", "value": 4},
    "isolation": {"type": "mode", "value": 4},
    "pull back": {"type": "mode", "value": 4},
    "beauty": {"type": "mode", "value": 5},
    "orbit": {"type": "mode", "value": 5},
    # Parameter adjustments
    "closer": {"type": "param", "key": "distance", "delta": -0.5},
    "farther": {"type": "param", "key": "distance", "delta": +0.5},
    "higher": {"type": "param", "key": "altitude", "delta": +0.3},
    "lower": {"type": "param", "key": "altitude", "delta": -0.3},
    "faster": {"type": "param", "key": "speed", "delta": +0.2},
    "slower": {"type": "param", "key": "speed", "delta": -0.2},
    "hold": {"type": "control", "action": "pause"},
    "resume": {"type": "control", "action": "play"},
    "stop": {"type": "control", "action": "emergency_stop"},
}

# Fuzzy matching: Deepgram sometimes returns "go high" as "go hi"
FUZZY_ALIASES = {
    "go hi": "go high",
    "close-up": "close up",
    "pullback": "pull back",
}
```

**For the demo video (simulated voice):**
Don't need a live microphone. Pre-record voice commands with timestamps:

```json
// voice/demo_script.json
{
  "commands": [
    {"time": 0.0,  "spoken": "beauty",    "mode": "BEAUTY"},
    {"time": 8.0,  "spoken": "hero",      "mode": "HERO"},
    {"time": 15.0, "spoken": "closer",    "param": "distance-"},
    {"time": 20.0, "spoken": "intimate",  "mode": "INTIMATE"},
    {"time": 30.0, "spoken": "epic",      "mode": "EPIC"},
    {"time": 40.0, "spoken": "energy",    "mode": "ENERGY"},
    {"time": 55.0, "spoken": "solitude",  "mode": "SOLITUDE"},
    {"time": 65.0, "spoken": "beauty",    "mode": "BEAUTY"},
    {"time": 75.0, "spoken": "hold",      "control": "pause"},
    {"time": 80.0, "spoken": "resume",    "control": "play"}
  ]
}
```

The render script reads this JSON, switches HDRI + lighting preset at each command timestamp,
adds a voice-command subtitle overlay via ffmpeg. Demo shows: voice text appears on screen →
environment + lighting instantly changes.

**Deliverable:** `voice/voice_commander.py` + `voice/demo_script.json` + demo script integration.

---

### Day 5 — Mode-transition rendering

**Task:** Build the render pipeline that switches stage + lighting mid-video when modes change.

**Script: `stage_design/render_mode_switching_demo.py`**

This is the key script that ties everything together:

```python
"""Render a complete multi-mode demo video.

Reads:
  1. Drone trajectory (from trained policy)
  2. Dancer trajectory (from mocap)
  3. Voice command script (mode switches with timestamps)
  4. 6 HDRIs (one per mode)
  5. 6 lighting presets

Outputs:
  MP4 with mode-appropriate environments, smooth transitions on voice commands,
  subtitle overlay showing commands.

Uses Blender EEVEE for rendering (supports HDRIs + real characters + fast).
"""
```

For mode transitions: 1-second crossfade between HDRIs. Blender supports animated
world shader mixing — interpolate between old HDRI and new HDRI over 30 frames.

**Deliverable:** Multi-mode render script, first test of a 2-mode transition.

---

## WEEK 2: Render + Polish + Package

### Day 6 — Full 6-mode trajectory export

**Task:** Export a 90-second trajectory that cycles through all 6 modes.

On EC2, run the trained v4 policy with mode switches injected at timestamps matching
the demo script:

```bash
ssh -i $PEM ubuntu@$EC2_IP 'sudo docker exec isaaclab bash -lc "
  cd /workspace/isaaclab &&
  ./isaaclab.sh -p /workspace/isaaclab/cinematography/export_cinematographer_trajectory.py \
    --checkpoint /workspace/isaaclab/cinematography/cinematographer_v4_modes_best.pth \
    --steps 4500 --fps 50 \
    --mode-schedule 0:BEAUTY,400:HERO,750:INTIMATE,1100:EPIC,1600:ENERGY,2200:SOLITUDE,2800:BEAUTY,3500:HERO \
    --out /workspace/isaaclab/exports/demo_90s_trajectory.json"'
```

If the export script doesn't support `--mode-schedule` yet, add it — it's a simple
modification: at each step, check if step >= next_switch_step, if so update the mode
one-hot in the observation.

**Deliverable:** 90-second, 6-mode trajectory JSON on EC2.

---

### Day 7-8 — Render the full demo

**Task:** Render all video assets on EC2 via Blender EEVEE.

**Renders needed:**

| Video | Duration | Content | Est. render time |
|---|---|---|---|
| `demo_hero_25s.mp4` | 25s | Daphne on HERO stage, drone-POV | ~6 min |
| `demo_intimate_25s.mp4` | 25s | Daphne on INTIMATE stage | ~6 min |
| `demo_epic_25s.mp4` | 25s | Daphne on EPIC stage | ~6 min |
| `demo_energy_25s.mp4` | 25s | Daphne on ENERGY stage | ~6 min |
| `demo_solitude_25s.mp4` | 25s | Daphne on SOLITUDE stage | ~6 min |
| `demo_beauty_25s.mp4` | 25s | Daphne on BEAUTY stage | ~6 min |
| **`demo_full_90s.mp4`** | 90s | **Multi-mode with voice switches** | ~18 min |
| `demo_comparison.mp4` | 30s | Split-screen: grey void vs full production | ~12 min |

Total render time: ~1 hour on A10G with EEVEE. Can nohup and walk away.

**Resolution:** 1920×1080 for demo reel, 1280×720 for quick iterations.

---

### Day 9 — Subtitle overlay + audio mix

**Task:** Add voice command overlay and music to the videos.

**ffmpeg commands:**

```bash
# Add voice command subtitles
ffmpeg -i demo_full_90s.mp4 \
  -vf "subtitles=voice_commands.srt:force_style='FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2'" \
  -c:a copy demo_full_90s_subtitled.mp4

# Add music track (cosmic-hypnotic, already have it)
ffmpeg -i demo_full_90s_subtitled.mp4 \
  -i cosmic-hypnotic.mp3 \
  -map 0:v -map 1:a -c:v copy -c:a aac -shortest \
  demo_full_90s_final.mp4

# Create split-screen comparison
ffmpeg \
  -i cinematography/drone_pov_25s.mp4 \
  -i demo_hero_25s.mp4 \
  -filter_complex "[0:v]scale=960:540[left];[1:v]scale=960:540[right];[left][right]hstack=inputs=2;drawtext=text='Before':x=200:y=20:fontsize=36:fontcolor=white,drawtext=text='After':x=1160:y=20:fontsize=36:fontcolor=white" \
  demo_before_after.mp4
```

**Voice command .srt file** (generated from demo_script.json):

```srt
1
00:00:00,000 --> 00:00:02,000
🎙️ "Beauty"

2
00:00:08,000 --> 00:00:10,000
🎙️ "Hero"

3
00:00:15,000 --> 00:00:17,000
🎙️ "Closer"
```

**Deliverable:** Final videos with subtitles + music.

---

### Day 10 — Package + one-pager update

**Task:** Create the demo package ready for customer outreach.

**Demo reel (90 seconds):**

```
0:00-0:05  Title card: "TrigunAI Autonomous Cinematography"
0:05-0:10  Before: grey void, stick figure (current state)
0:10-0:15  After: full production (same trajectory, beautiful)
0:15-0:30  HERO mode — dramatic low angles, character on dark stage
0:30-0:40  Voice: "intimate" — smooth transition to warm studio
0:40-0:50  INTIMATE mode — close framing, soft lighting
0:50-1:00  Voice: "epic" — transition to outdoor amphitheater
1:00-1:10  EPIC — wide shots, golden hour, vast scale
1:10-1:20  Voice: "energy" — transition to neon concert stage
1:20-1:30  End card: "6 modes. Voice-directed. Your mocap → our drone."
           Contact: deepak@trigunai.com
```

**Deliverables directory:**

```
demo_package/
├── demo_reel_90s.mp4              # The main show
├── demo_before_after.mp4          # Split-screen comparison
├── mode_hero_25s.mp4              # Individual mode showcase
├── mode_intimate_25s.mp4
├── mode_epic_25s.mp4
├── mode_energy_25s.mp4
├── mode_solitude_25s.mp4
├── mode_beauty_25s.mp4
├── CAPABILITY_ONE_PAGER.pdf       # Updated with screenshots
├── screenshots/
│   ├── hero_frame.png
│   ├── intimate_frame.png
│   ├── epic_frame.png
│   ├── energy_frame.png
│   ├── solitude_frame.png
│   └── beauty_frame.png
└── README.md                      # What's in this package
```

---

## Total cost estimate

| Item | Cost |
|---|---|
| Blockade Labs (6 skyboxes) | ~$2 |
| Poly Haven HDRIs (6) | $0 |
| Deepgram (testing voice commands) | ~$1 |
| EC2 compute (~15 hours for rendering + iterations) | ~$15 |
| Mixamo character (if not using Daphne) | $0 |
| **Total** | **~$18** |

## EC2 compute breakdown

| Task | Hours | Cost |
|---|---|---|
| Day 6: trajectory export (2 runs × 10 min) | 0.5h | $0.50 |
| Day 7-8: Blender EEVEE renders (8 videos × 6-18 min) | 2h | $2.00 |
| Day 7-8: iteration renders (re-renders, tests) | 4h | $4.00 |
| Day 1-5: OVRTX test renders, asset prep | 4h | $4.00 |
| Buffer for debugging | 4h | $4.00 |
| **Total** | **~15h** | **~$15** |

---

## Risk mitigation

| Risk | Likelihood | Mitigation |
|---|---|---|
| OVRTX doesn't support HDRI dome lights | Medium | Use Blender EEVEE for final renders (definitely supports HDRIs) |
| Blockade Labs HDRIs look AI-generated | Low | Supplement with Poly Haven real HDRIs; use Blockade for concept, Poly Haven for quality |
| Daphne character looks weird with HDRI lighting | Medium | Test Day 3; fallback to Mixamo character or back to stick figure with HDRIs |
| 90s trajectory export needs mode-schedule support | High | Build it Day 6; it's a small modification to existing export script |
| Blender EEVEE quality not cinematic enough | Low | Switch to Cycles for hero shots only (render overnight); EEVEE for iteration |
| Voice demo feels fake (pre-recorded, not live) | Medium | It IS pre-recorded for the video demo. Note: "live demo available on request" |

---

## Success criteria

The demo is "done" when:
1. ✅ 90-second reel shows all 6 modes with real character + real stages + real lighting
2. ✅ Voice commands are visible on screen and environments change in response
3. ✅ Before/after comparison is dramatic (grey void → full production)
4. ✅ Music is synced to the performance
5. ✅ CEO watches the reel and would send it to a customer without embarrassment
6. ✅ One-pager updated with screenshots from the demo

---

## What this does NOT include (deliberately)

- No live voice integration (pre-recorded for demo video — live comes when a customer asks)
- No DMX hardware (demo is all simulation — real fixtures when a customer has a venue)
- No RL-trained lighting (presets are fine for demo — RL comes when presets aren't enough)
- No procedural stage generation (HDRI + Poly Haven is fine — procedural comes later)
- No ONNX export (drone hardware deployment is post-first-customer)
- No fly-to-mark UI (demo is in simulation — tablet UI when there's a real drone)
