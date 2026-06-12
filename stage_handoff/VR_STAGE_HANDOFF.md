# Neon Psychedelic Stage — VR Handoff

> For the GurulokInnerJourney Unity/Quest 3 agent.
> Created: 2026-05-29 by the Stage Design agent.

---

## What this is

A procedurally-built neon psychedelic dance stage, exported as a GLB for use in the GurulokInnerJourney Quest 3 app. The scene is designed as a backdrop for live performer recording — the user dances in VR wearing a Quest 3, and the stage surrounds them.

## Files

| File | Path | Size | Description |
|---|---|---|---|
| **GLB (Quest-ready)** | `stage_design/neon_stage_v17.glb` | 5.5 MB | Static scene geometry with simplified materials, Draco-compressed, floor texture baked at frame 100 |
| **Blend source** | EC2: `/home/ubuntu/neon_stage_v17.blend` | ~80 MB | Full procedural scene with animated shaders (Blender 4.5 EEVEE) |
| **Build script** | `stage_design/build_neon_stage.py` | ~60 KB | Procedural scene builder — regenerate from scratch |
| **Export script** | `stage_design/export_stage_to_glb.py` | ~8 KB | Blend → GLB converter with material baking |
| **Demo clip** | `stage_design/neon_v17_clip.mp4` | 7.5 MB | 5s animation preview |

## Scene contents (16 elements)

| Element | Object count | What it is |
|---|---|---|
| Psychedelic floor | 1 plane | 30m dark mirror with Voronoi+Noise+Wave ring patterns, baked to 1024² emission texture |
| Fire columns | 6 cones | Tall thin cones at r=5m circle, amber-red gradient with noise flicker |
| Floating geometry | 10 shapes | Tori/icospheres with glass+emission, animated hue rotation + sine bob |
| Neon ring arcs | 3 curves | Thin bezier circles with rainbow emission, rotating |
| Accent lights | 3 spots | Cyan/magenta/warm — **removed in GLB** (lights don't export to glTF) |
| Moonlight | 1 area light | **Removed in GLB** — Unity must add its own directional light |
| Atmosphere fog | world volume | **Not in GLB** — add Unity fog/post-processing |
| Rising particles | 200 spheres | Small emissive motes with rise animation (keyframed Z) |
| God rays | 3 spotlights | **Removed in GLB** — recreate with Unity volumetric light |
| Moon + halo | 2 spheres | Emissive sphere at (3, -8, 14) with radial-falloff glow halo |
| Light curtain | 1 curved mesh | 160° arc wall (r=7, h=12) with rainbow strand UV shader — baked to solid colors |
| Ground glow | 50 spheres | Flat emissive floor dots in 6 neon colors |
| Psychedelic trees | 4 trees | Dark trunks with purple glow veins + ~220 emissive leaf particles + 60 fallen leaves |
| Glowing stones | 35 pebbles | Glass+emission hybrid with Fresnel glow, mixed with dark matte stones |
| Waterfall | 1 mesh | Curved plane at (0, -6.5, 0-8) with flowing neon shader — baked to solid |
| Test camera | — | **Removed in GLB** — Quest provides the camera |

## What transfers vs. what's lost

### Transfers to GLB
- All geometry positions and shapes
- Basic emission colors on all materials
- Baked floor texture (psychedelic pattern snapshot at frame 100)
- Object hierarchy and names

### Lost in GLB (must be recreated in Unity)
- **Animated shaders** — floor color cycling, fire flicker, hue rotation, rainbow scrolling
- **Volumetric fog and god rays** — no equivalent in glTF
- **Bloom** — post-processing, must be added via Unity's URP/post-processing stack
- **Particle rise animation** — keyframed Z positions exist but may not play without Unity's `Animated()` component
- **Ring rotation animation** — same as above
- **Glass material translucency** — glTF's transmission extension may partially work

## Integration into GurulokInnerJourney

### Step 1: Drop the GLB

```
Assets/_App/NeonStage/Models/neon_stage_v17.glb
```

### Step 2: Write `NeonStageJourneyController.cs`

Implements `IJourney` (mirror of `CosmicJourneyController`). Key points:
- Load the GLB at runtime via `com.atteneder.gltfast`
- Place it at world origin — the stage is centered at (0,0,0)
- The performer (user) stands at center, surrounded by the stage
- Scale: 1:1 (Blender meters = Unity meters)
- Add a directional light to replace the removed moonlight (color: `#D9E6FF`, intensity 0.5, rotation 45° from above-behind)

### Step 3: Add Unity-side effects

Priority order for recreating the lost effects:

1. **Bloom post-processing** — URP Post Processing Volume, bloom threshold 0.3, intensity 1.5
2. **Fog** — Global fog or linear fog, dark blue-black (#020208), density low
3. **Skybox** — Solid dark color or gradient (very dark blue-black)
4. **Floor animation** (optional) — UV scroll shader on the floor material to animate the baked texture
5. **Volumetric light** (optional) — Spot light with volumetric rendering for god ray effect
6. **Particle system** (optional) — Replace the 200 static mote spheres with a Unity ParticleSystem for proper rising effect

### Step 4: Build + Upload

Per the standard Gurulok build pipeline:
```
QuestBuildAndUpload.BuildQuestAPK → ovr-platform-util upload-quest-build
```

## Scene layout (top-down coordinates, Y-up in Unity)

```
        Moon (3, 14, -8)
             •

    ┌─── Light Curtain arc (r=7, 190°-350°) ───┐
    │                                             │
    │   Tree(-6.5,-2)    Waterfall(0,-6.5)   Tree(7,-3) │
    │        🌳              |||              🌳        │
    │                                                   │
    │     🔥    🔥    ⭕    🔥    🔥                  │
    │                 USER                              │
    │     🔥    CENTER(0,0)   🔥                       │
    │          [r=5 circle]                             │
    │   Tree(-7.5,2)              Tree(6,3.5)          │
    │        🌳                      🌳                │
    │                                                   │
    └───────────────────────────────────────────────────┘
              ●●● scattered stones + ground glow ●●●
```

Coordinate note: Blender is Z-up, Unity is Y-up. The GLB exporter handles the conversion. In Unity: Y is up, the floor is at Y=0, trees grow in +Y.

## Regenerating from scratch

If you need a different frame bake or different parameters:

```bash
# On EC2 (3.91.18.30):

# 1. Rebuild scene with different settings
blender45 --background --python /home/ubuntu/build_neon_stage.py -- \
    --save /home/ubuntu/neon_stage_v17.blend \
    --floor-size 30 --stage-radius 5 --fire-count 6

# 2. Export to GLB at a different frame
blender45 --background --python /home/ubuntu/export_stage_to_glb.py -- \
    --blend /home/ubuntu/neon_stage_v17.blend \
    --out /home/ubuntu/neon_stage_v17.glb \
    --frame 150 --texture-size 1024 --decimate 0.5
```

## Performance notes for Quest

- GLB is 5.5 MB — well within Quest memory budget
- ~600 objects total (most are tiny sphere particles/leaves)
- Floor is a single plane — negligible draw calls
- Recommend disabling shadows on mobile (emissive scene doesn't need them)
- If frame rate drops: disable fog, reduce particle count, or use LOD groups for distant trees

---

*Handoff created 2026-05-29 by Stage Design agent. Scene: v17 psychedelic overhaul.*
