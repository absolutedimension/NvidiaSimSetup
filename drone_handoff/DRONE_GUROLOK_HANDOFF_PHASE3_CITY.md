# Drone Demo Journey — Phase 3 Handoff (animated drone + OSM city, table-top scene)

**Date:** 2026-05-24
**From:** Deepak (working in `NvidiaSimSetup/` on Mac)
**For:** the Claude Code agent running in `C:\Users\unity-t4-tesla\GurulokInnerJourney`
**Prerequisites:**
- Phase 1 (`DRONE_GUROLOK_HANDOFF.md`) shipped — `DroneJourney` package exists, static `cf2x.glb` was wired in, v64 in alpha
- Phase 2 (`DRONE_GUROLOK_HANDOFF_PHASE2.md`) shipped — `cf2x_trained.glb` (hover policy) added, v120 in alpha, animated drone is looping in VR

---

## TL;DR

Drop a **single new GLB — `manhattan_drone_flight.glb` (7.3 MB)** — into the DroneJourney. It contains the AI-generated **Manhattan / Times Square** city (866 OSM-derived buildings, AI-textured façade) **plus** the trained PPO drone playing a 25-second flight clip inside it. **Wrap it in a parent Xform scaled to `0.005` (1300 m → 6.5 m)** so it lands as a table-top "snow-globe" model in front of the user, not as a real-world-sized city the user is standing inside.

Ship as **v121 to alpha**.

This is the first journey where a Gurulok scene asset came **entirely out of the TrigunAI content pipeline** — no manual modelling, no external kit. OSM → USD → AI textures → trained policy → animated GLB. The pipeline is documented in `NvidiaSimSetup/CLAUDE.md §17–§18` (extended with the new OSM city flow added 2026-05-24).

### ⚠️ Honest caveat on the trained policy in this build

**The drone in this GLB crashes into buildings most of the time.** It's a real 500-iter PPO policy on `Isaac-Quadcopter-OSM-City-Direct-v0` — best reward `-25` (negative because each collision costs `-50`). It learned *something* — about 65 % reduction in crash-penalty vs. random baseline at iter 5 — but it is *not* ship-it caliber yet. The animation will show the drone doing a short jittery flight and then its episode ends (where it crashes into a building or simply stops at episode-end).

We're shipping it anyway because:
1. It proves the entire content-pipeline-to-VR loop works end-to-end with a real trained policy on a real city we generated ourselves
2. Every future iteration (longer training, depth-vision Tier 2, etc.) will drop into the *same slot* with no Gurulok-side changes
3. Phase 2's `cf2x_trained.glb` (the calm hover policy, VLM ship-it 8/10) is still in alpha v120 — keep it as the fallback / "polished" mode

Future GLBs from this same env (e.g. `manhattan_drone_flight_v2.glb` after 2000+ iters of training) will be drops-in here — same asset path, same scale wrap, just better-looking flight.

---

## What you receive

In `drone_handoff/`:

| File | Size | What |
|---|---|---|
| **`manhattan_drone_flight.glb`** | **7.3 MB** | The primary deliverable. Manhattan city (textured) + animated trained-policy drone in one GLB. Single glTF animation `Drone_action` on the `Drone` node (translation + rotation + scale F-curves, 600 keyframes @ 24 fps = 25 s loop). Drone is internally scaled 200× so it stays visible after the scene's outer 0.005 down-scale. |
| `manhattan_times_sq.glb` | 7.0 MB | City-only version. **You don't need this for v121** — but useful if a future journey wants a static cityscape without a drone, or if we want to overlay a different animated entity. Keep it staged. |
| `manhattan_drone_trajectory.json` | 118 KB | Raw 600-frame trajectory (Isaac Sim Z-up positions + quaternions, fps=24). Source of truth for re-baking with different scale / coordinate convention if needed. |

The drone trajectory begins at `(0, 0, 30 m)` in Isaac Z-up coords (= origin of city, 30 m altitude) and tries to reach `(100, 0, 30 m)` (100 m east at same altitude). City spans roughly `x = [-665, 632] m`, `y = [-601, 558] m`, `z = [0, 366] m` (tallest building 366 m = real Bank of America Tower).

---

## What to change in the Unity project

You already have `Assets/_App/DroneJourney/` from Phases 1 & 2. The change is **bigger than Phase 2** because we're now also rendering a city — but it's still localized to the `DroneJourney` package.

### 1. Drop the new GLBs next to the existing ones

```
Assets/_App/DroneJourney/Models/
├── cf2x.glb                          ← Phase 1 (static drone, keep)
├── cf2x_trained.glb                  ← Phase 2 (hover policy, keep — fallback)
├── manhattan_drone_flight.glb        ← Phase 3 (NEW, primary)
└── manhattan_times_sq.glb            ← Phase 3 (NEW, optional standalone city)
```

### 2. Edit `DroneJourneyController.cs` — add a "mode" enum

Phase 2 introduced `useTrainedTrajectory: bool`. Promote it to an enum so we can switch between the three deliverables we now have:

```csharp
public enum DroneJourneyMode
{
    StaticDrone,       // Phase 1 — cf2x.glb, hover-bob + yaw via Update()
    TrainedHover,      // Phase 2 — cf2x_trained.glb, plays embedded Animation clip
    ManhattanCityFlight,  // Phase 3 — manhattan_drone_flight.glb, city + drone in one GLB
}

[SerializeField] public DroneJourneyMode mode = DroneJourneyMode.ManhattanCityFlight;
[SerializeField] public Animation droneAnimation;   // set from setup; plays in TrainedHover + ManhattanCityFlight
```

In `StartJourney()`:

```csharp
public void StartJourney()
{
    droneRoot.SetActive(true);
    _t = 0f;
    Active = true;

    if (mode == DroneJourneyMode.TrainedHover || mode == DroneJourneyMode.ManhattanCityFlight)
    {
        if (droneAnimation != null && droneAnimation.clip != null)
        {
            droneAnimation.wrapMode = WrapMode.Loop;
            droneAnimation.Play();
        }
    }
}
```

In `Update()`, only run the Phase 1 hover-bob code when `mode == StaticDrone`:

```csharp
void Update()
{
    if (!Active || droneRoot == null) return;
    _t += Time.deltaTime;
    if (mode != DroneJourneyMode.StaticDrone) return;  // animation drives transform
    // ... existing hover-bob + yaw-spin code unchanged
}
```

### 3. **CRITICAL: scale-down wrapper** in `DroneJourneySetup.cs`

The city is **1300 m wide in real coords** — you can't just instantiate it at scale 1 in front of the user. Wrap it in a parent Xform at `localScale = 0.005f` (a tunable constant — start there) so the city becomes a `~6.5 m` "table-top model" the user sees in front of them, with the drone visible as a moving dot.

```csharp
// In DroneJourneySetup.cs, in the Setup menu method:

private const string GLB_ASSET_PATH_PHASE3 = "Assets/_App/DroneJourney/Models/manhattan_drone_flight.glb";
private const float CITY_TABLE_SCALE = 0.005f;   // 1300 m city → 6.5 m table

// ...

var droneAsset = AssetDatabase.LoadAssetAtPath<GameObject>(GLB_ASSET_PATH_PHASE3);
if (droneAsset == null)
{
    Debug.LogError($"[DroneJourneySetup] missing GLB: {GLB_ASSET_PATH_PHASE3}");
    return;
}

// Outer Xform anchors the table-top in front of the user
var anchor = new GameObject("CityAnchor");
anchor.transform.SetParent(root.transform, worldPositionStays: false);
anchor.transform.localPosition = new Vector3(0f, -0.5f, 1.5f);  // 1.5 m in front, slightly below eye level
anchor.transform.localScale = Vector3.one * CITY_TABLE_SCALE;

var cityDrone = (GameObject)PrefabUtility.InstantiatePrefab(droneAsset, anchor.transform);
cityDrone.name = "ManhattanDroneFlight";

// Find the Animation component the glTFast import added
var anim = cityDrone.GetComponentInChildren<Animation>();
var animator = cityDrone.GetComponentInChildren<Animator>();   // glTFast may use Animator instead
if (anim == null && animator != null)
{
    Debug.Log("[DroneJourneySetup] GLB came in as Animator — wire Animator instead, or convert to legacy Animation");
}

ctrl.droneRoot = cityDrone;
ctrl.droneAnimation = anim;
ctrl.mode = DroneJourneyMode.ManhattanCityFlight;
```

> **Note on the Y offset**: I put it at `y = -0.5 m` (50 cm below eye level) so the user sees the city like a table they're standing in front of. Tune this with the `xrRig` height in your scene — should "look like a model on a coffee table". The `1.5 m` forward distance is a normal arm-reach for VR interactions.

---

## Build + upload

Same as Phase 1 / Phase 2. Bump build notes to v121:

```bash
"/c/Program Files/Unity/Hub/Editor/6000.4.2f1/Editor/Unity.exe" \
  -batchmode -nographics -quit \
  -projectPath "C:\Users\unity-t4-tesla\GurulokInnerJourney" \
  -executeMethod QuestBuildAndUpload.BuildQuestAPK \
  -logFile - 2>&1 | grep -E "(Build succeeded|Build failed|Version code|error CS|APK:)" | head -10

"/c/Users/unity-t4-tesla/Gurulok-EnergyField/Tools/ovr-platform-util.exe" \
  upload-quest-build \
  --app-id 24914535711578182 \
  --app-secret <see CLAUDE_FlowArtdance_VR.md §2> \
  --apk "C:\Users\unity-t4-tesla\GurulokInnerJourney\Builds\GurulokInnerJourney.apk" \
  --channel alpha \
  --notes "v121: Drone Demo Phase 3 — Manhattan OSM city + trained drone (first end-to-end TrigunAI content-pipeline scene)"
```

---

## What success looks like in Quest 3

Pick "Drone Demo" from the journey menu. You should see:

1. A **~6.5 m wide model of Manhattan** appear ~1.5 m in front of you, slightly below eye level (like looking at a tabletop model)
2. Buildings are textured with an AI-generated concrete-and-windows façade (the same texture tiled on all 866 buildings — currently uniform; future iterations will diversify)
3. A small **dark drone** (about the size of a tall building in the model, ~5 cm at table scale) starts at the city center, attempts to fly east, **wobbles and crashes** somewhere mid-traverse
4. The animation **loops** every 25 seconds

What it should NOT look like:
- You inside a 1.3-km city (you forgot the `CITY_TABLE_SCALE` wrap)
- The drone invisible (it spawned outside the camera frustum or scale is wrong)
- Buildings flat-white (texture didn't import — check Project window → `manhattan_drone_flight.glb` → Materials)

A reference video / screenshot of the *web* version (which uses the same GLB) is at https://encouraged-answering-hayes-lying.trycloudflare.com — pick "Manhattan + Trained Drone (ep_475)" (first card). Note that cloudflared quick tunnels expire under load, so the URL may have rotated — Deepak can issue a fresh one with `ssh ubuntu@<ec2-ip> 'nohup cloudflared tunnel --url http://localhost:8080 &'`.

---

## If something doesn't work

| Symptom | Cause | Fix |
|---|---|---|
| User is inside a giant city | Forgot the `CITY_TABLE_SCALE` parent Xform | Verify `anchor.transform.localScale = Vector3.one * 0.005f` is applied BEFORE the GLB is instantiated as its child |
| Drone is invisible | The 200× internal drone scale combined with the 0.005 outer scale = 1× total. That's correct in principle, but the drone's actual size at table scale is `0.10 m × 200 × 0.005 = 0.10 m` — a 10-cm dot. Might be hard to see against the cityscape. | Bump `CITY_TABLE_SCALE` to `0.01` or `0.015` (city = 13–20 m, drone = 20–30 cm). Or alternately re-bake the drone with a bigger `--drone-scale` (Deepak can do this in <1 min). |
| City is textured but appears washed-out / no shadows | glTFast may not auto-apply HDR lighting | Add a `DirectionalLight` to the journey scene, intensity 1.0, rotated like `(50, -30, 0)` |
| Animation plays once and stops | `WrapMode.Loop` wasn't set | Confirm `droneAnimation.wrapMode = WrapMode.Loop` is set BEFORE `Play()` |
| City tilts 90° (on its side) | Z-up → Y-up conversion was applied twice | The GLB was exported with Blender's `export_yup=True`, so Unity should NOT apply additional rotation. If you see tilt, add `cityDrone.transform.localRotation = Quaternion.identity` explicitly, and check that no parent has unintended rotation |
| Materials reference missing texture URI | The GLB embeds 3 PNG textures (albedo, normal, ORM). If they're missing in Unity's Inspector, the export silently dropped them — Deepak should re-bake | Check Project window → `manhattan_drone_flight.glb` → expand → should show 1 material + 3 image entries |
| Build size jumped by 7 MB | Expected — the GLB is 7.3 MB | If this pushes the APK over Meta's size limit, we can decimate buildings via `usd_to_glb.py --decimate 0.5` and re-bake to ~3.5 MB |

If you can't get past it in ~45 min of debugging, send a screenshot + the Unity Console output back to Deepak and we'll iterate. There's no rush — Phase 2's `cf2x_trained.glb` is still in alpha and gives users a working drone experience.

---

## What's in this Phase 3 (don't over-engineer)

Just drop the GLB, wrap in scale, hook the Animation, ship. Do not:
- Add VR controls to scrub through the trajectory (later phase)
- Add a "select city" menu (later phase — we'll have Bangalore, SF SoMa, etc. as separate GLBs)
- Layer multiple drone trajectories on top of each other (later phase — "ghost mode" comparing trained vs. baseline)
- Try to re-train the policy from Unity (the GLB is fixed; new policies = new GLBs)
- Mix the Phase 2 drone with this city (different scales; would need re-baking)

Ship v121, confirm the table-top scene loads + drone animates + loops, done.

---

## Phase 4 preview (for context, not action)

- **More training iterations** → a ship-it caliber Manhattan-flying drone (target: VLM critic returns `verdict: ship-it`)
- **Multiple cities** → swap `--lat / --lon` in `osm_to_usd.py`, get a Bangalore / Tokyo / London variant (each = new GLB through the same `compose_drone_in_city.py` → `usd_to_glb.py --inject-trajectory` chain)
- **In-VR menu** → user picks city + drone variant from a spatial menu inside the journey
- **Live policy inference** → far future, would replace the baked animation with a runtime policy net evaluated on Quest hardware (heavy lift; needs ONNX export + Quest GPU inference)

---

## Quick checklist for the picking-up agent

```
□ Read this doc + Phase 1 + Phase 2 + CLAUDE_FlowArtdance_VR.md PRIMITIVE 3
□ Copy manhattan_drone_flight.glb + manhattan_times_sq.glb to Assets/_App/DroneJourney/Models/
□ Confirm Unity sees 1 animation + textured materials on manhattan_drone_flight.glb in Project Inspector
□ Update DroneJourneyController.cs: add DroneJourneyMode enum, swap useTrainedTrajectory bool for mode field
□ Update DroneJourneySetup.cs: add CityAnchor with localScale 0.005, point GLB_ASSET_PATH_PHASE3 to new GLB, set mode = ManhattanCityFlight
□ Run "EnergyField → Setup Drone Demo Journey in SampleScene"
□ Verify in scene hierarchy: DroneJourney → CityAnchor (scale 0.005) → ManhattanDroneFlight (the GLB with Animation)
□ Build APK via QuestBuildAndUpload.BuildQuestAPK
□ Upload to alpha with notes "v121: Drone Demo Phase 3 — Manhattan OSM city + trained drone"
□ Test in Quest 3 — table-top Manhattan + crashing drone visible
□ Confirm with Deepak that the scene loads + loops correctly
```

— end of handoff
