# Drone Demo Journey — Phase 2 Handoff (animated GLB from trained policy)

**Date:** 2026-05-18
**From:** Deepak (working in `NvidiaSimSetup/` on Mac)
**For:** the Claude Code agent running in `C:\Users\unity-t4-tesla\GurulokInnerJourney`
**Prerequisites:** Phase 1 handoff (`DRONE_GUROLOK_HANDOFF.md`) is done — `DroneJourney` package exists, static `cf2x.glb` was wired into the journey menu, v64 shipped to alpha, drone visible in VR.

---

## TL;DR

Swap the static `cf2x.glb` for an animated **`cf2x_trained.glb`** that plays a glTF animation of a real trained PPO drone policy. Ship as **v120 to alpha** (the Gurulok build counter is at v107+ in the CLAUDE.md history and v119 shipped the static drone — this is the next sequential build).

### VLM critic verdict on this exact GLB

The trajectory baked into `cf2x_trained.glb` was graded by gpt-4o-mini (via our LiteLLM proxy + the same Material/Physics/Texture agent infrastructure) on 2026-05-18:

```json
{
  "reach": 8,
  "smoothness": 7,
  "stability": 9,
  "efficiency": 8,
  "overall": 8,
  "issues": [],
  "verdict": "ship-it"
}
```

So this is a **green-lit drop** — first ship-it from the Approach A pipeline. Trained for 500 PPO iterations on `Isaac-Quadcopter-Direct-v0`. Animation clip is **7.5 seconds @ 24 fps, 180 frames**.

If Deepak ships a future GLB that scores below `overall: 7` or has any `issues`, treat it as a regression — flag back to him before building.

---

## What you receive

In the same `drone_handoff/` folder alongside this doc:

| File | Size | What |
|---|---|---|
| `cf2x_trained.glb` | 250 KB | Animated GLB — same Crazyflie geometry as Phase 1, with an embedded glTF animation clip on the root node (translate + rotate per frame) |
| `drone_trajectory.json` | 48 KB | Raw trajectory (positions + quaternions per step) — for debugging if the GLB animation doesn't play, or for re-baking with different parameters |
| `drone_trained.mp4` (in parent dir) | 50 KB | Reference render — shows what the animation should look like when played through NVIDIA's OVRTX renderer (third-person fixed camera, 7.5s clip). Use this to sanity-check what you should see in VR. |

The trained model output: drone starts at ~(0, 0, 0.5) in Isaac Sim coords, then makes small position corrections to track a learned goal. **Motion is subtle** (the env's task is "hover near goal", not "fly across the room"), so don't expect dramatic flight — expect a gently drifting + correcting hover. That's what a well-trained PPO policy looks like for this specific task.

---

## What to change in the Unity project

You already have `Assets/_App/DroneJourney/` from Phase 1. Three small additions:

### 1. Drop the new GLB next to the old one

```
Assets/_App/DroneJourney/Models/
├── cf2x.glb              ← Phase 1 (keep — fallback / "static" mode)
└── cf2x_trained.glb      ← Phase 2 (new)
```

### 2. Add an `Animation` component reference to `DroneJourneyController.cs`

Per CLAUDE_FlowArtdance_VR.md PRIMITIVE 3 ("Baked GLB rules") — Unity needs the GLB's NLA-strip animation to play via the `Animation` component. The GLB was exported with `export_animation_mode="NLA_TRACKS", export_nla_strips=True` (verified in `NvidiaSimSetup/webxr-showcase/scripts/usd_to_glb.py`), so Unity's glTFast importer should pick it up automatically — you may not need to do anything manually for the import.

In `DroneJourneyController.cs`, two new fields and a `StartJourney` tweak:

```csharp
[SerializeField] public Animation droneAnimation;   // assigned in setup, may be null
[SerializeField] public bool useTrainedTrajectory = true;  // toggle for v65

public void StartJourney()
{
    // ... existing spawn-position logic ...
    droneRoot.SetActive(true);
    _t = 0f;
    Active = true;

    // NEW: if the trained GLB exposes an Animation clip, play it
    if (droneAnimation != null && droneAnimation.clip != null)
    {
        droneAnimation.wrapMode = WrapMode.Loop;
        droneAnimation.Play();
    }
}

public void EndJourney()
{
    if (droneAnimation != null) droneAnimation.Stop();
    Active = false;
    if (droneRoot != null) droneRoot.SetActive(false);
}
```

In `Update()`, **keep the hover-bob + yaw spin from Phase 1 ONLY if `useTrainedTrajectory == false`** — when the trained animation is playing, the GLB's own animation drives the transform; we shouldn't override it.

```csharp
void Update()
{
    if (!Active || droneRoot == null) return;
    _t += Time.deltaTime;

    if (useTrainedTrajectory && droneAnimation != null && droneAnimation.clip != null)
    {
        return;  // trained animation drives transform; don't override
    }

    // (Phase 1 hover-bob + yaw spin code unchanged)
    float bobY = ...;
    droneRoot.transform.position = _anchorPos + new Vector3(driftX, bobY, 0f);
    droneRoot.transform.rotation = Quaternion.Euler(0f, (_t * yawSpeedDegPerSec) % 360f, 0f);
}
```

### 3. Update `DroneJourneySetup.cs` to spawn the trained GLB

Single string change + `Animation` lookup:

```csharp
// was:
private const string GLB_ASSET_PATH = "Assets/_App/DroneJourney/Models/cf2x.glb";
// now:
private const string GLB_ASSET_PATH = "Assets/_App/DroneJourney/Models/cf2x_trained.glb";

// ... after instantiation:
var drone = (GameObject)PrefabUtility.InstantiatePrefab(droneAsset, root.transform);
drone.name = "CrazyflieDrone";

// Find the Animation component (glTFast adds one if the GLB has anim clips)
var anim = drone.GetComponentInChildren<Animation>();
// Same for Animator (newer glTFast versions sometimes use Animator instead)
var animator = drone.GetComponentInChildren<Animator>();
if (anim == null && animator != null)
{
    Debug.Log("[DroneJourneySetup] GLB came in as Animator, not Animation — adding compatibility layer if needed");
}

// ... attach controller:
ctrl.droneRoot = drone;
ctrl.droneAnimation = anim;
ctrl.useTrainedTrajectory = true;
```

> **Check the actual import result first** by selecting `cf2x_trained.glb` in the Project window. The Inspector should show an embedded animation clip — verify its frame range is **0 → 180** at **24 fps** (so duration ≈ 7.5 s). If only one of `Animation` / `Animator` appears, wire that one. If neither does, the NLA-strip export silently failed — see "If the animation doesn't play" below.

---

## Build + upload

Exactly the same as Phase 1 / CLAUDE_FlowArtdance_VR.md §3:

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
  --notes "v120: Drone Demo Phase 2 — trained PPO trajectory (VLM ship-it 8/10)"
```

---

## What success looks like in Quest 3

Pick "Drone Demo" from the journey menu. The Crazyflie should:
1. Spawn 2 m in front of the user, ~50 cm wide (same as Phase 1)
2. **Play a 7.5-second animation that loops** — subtle position corrections + tiny attitude wobble, characteristic of a trained quadcopter hovering near a goal
3. Loop seamlessly (the WrapMode.Loop above)

Compare against `drone_trained.mp4` to confirm visual fidelity. If you see something dramatically different (e.g. drone sitting motionless while v64's hover-bob runs), the animation didn't import correctly.

---

## If the animation doesn't play

Most likely failure modes (cross-reference CLAUDE_FlowArtdance_VR.md §8):

| Symptom | Cause | Fix |
|---|---|---|
| Drone is static, hover-bob is running | `droneAnimation` field wasn't assigned, or `useTrainedTrajectory == false` | Verify in Inspector on the `DroneJourney` GameObject. Hard-code `useTrainedTrajectory = true` in the controller if needed. |
| Drone is static, no animation on object | NLA strip didn't export. The glTFast importer in Unity may also not find the clip if it's at the root node and the prefab was instanced strangely. | Open `cf2x_trained.glb` in the Project window → Inspector tab → "Animations". If empty, the export failed. Workaround: re-bake via the chain in `NvidiaSimSetup/CLAUDE.md §17.5` and ask Deepak. |
| Drone snaps + jitters | World-space animation conflicts with parent transform applied by `DroneJourneyController.StartJourney()` | The Phase 1 controller writes `droneRoot.transform.position = _anchorPos` then enables. The animation will then animate FROM that anchor + the GLB's first-frame offset. To get the drone hovering at the anchor instead of at `(0,0,0)` in Isaac's coords, either: (a) parent the GLB under an Xform that StartJourney positions, and let the GLB animate within that local space, or (b) zero out the first-frame translation in the GLB and apply only the deltas. Quickest fix: just spawn the drone at `Vector3.zero` and let the animation drive everything; reposition the parent transform only if needed. |
| Animation plays too fast / too slow | glTFast normalized the duration | Set `droneAnimation[clipName].speed = 1.0f` explicitly. The clip was authored at 24 fps. |
| Drone tilts sideways / upside-down | Coordinate-system mismatch (Isaac Sim is Z-up; we remap to Y-up in the bake, but the conversion through Blender might re-apply Y-up). | Open the GLB in any glTF viewer (https://gltf-viewer.donmccurdy.com/) and play the animation. If it looks right there but wrong in Unity, Unity is applying additional axis correction — fix by adding a `Quaternion.AngleAxis(-90, Vector3.right)` to the drone's local rotation at spawn. |

If you can't get past it in ~30 min of debugging, send a screenshot back; we'll regenerate from a different export setting.

---

## What's in this Phase 2 (so you don't over-engineer)

Just swap the GLB + add Animation hookup. Do not:
- Build a city / warehouse around the drone (Phase 3)
- Wire trajectory-selection UI (later)
- Add VR controls for "play / pause / scrub" the animation (later)
- Try to make the drone respond to user input (the policy is fixed in this GLB; "responsive" drone needs realtime inference, which is a totally different pipeline)

Ship v65, confirm it loops correctly in VR, done.

---

## Phase 3 preview (for context, not action)

The current trained policy is `Isaac-Quadcopter-Direct-v0` which is just "hover near a goal pose" — short, subtle motion. Phase 3 trains on `Isaac-TrackPositionNoObstacles-ARL-Robot-1-v0` (a position-tracking env that exists in Isaac Lab 3.0) for longer, then eventually a custom `Isaac-Quadcopter-City-A2B-v0` env we'll fork — that's where you'll see real "fly from A to B" trajectories. Each new policy = new `cf2x_trained_v<N>.glb` shipped through this same pipeline. The Gurulok side won't need to change much; just swap the GLB asset path.

---

## Quick checklist for the picking-up agent

```
□ Read this doc + the Phase 1 doc (DRONE_GUROLOK_HANDOFF.md) + CLAUDE_FlowArtdance_VR.md PRIMITIVE 3
□ Copy cf2x_trained.glb to Assets/_App/DroneJourney/Models/
□ Confirm Unity sees an Animation/Animator on the GLB (Project window → Inspector)
□ Edit DroneJourneyController.cs (add droneAnimation field + Play() + suppress hover-bob)
□ Edit DroneJourneySetup.cs (point GLB_ASSET_PATH to cf2x_trained.glb, wire Animation field)
□ Run "EnergyField → Setup Drone Demo Journey in SampleScene"
□ Verify: SampleScene has DroneJourney root with CrazyflieDrone child carrying the Animation component
□ Build APK via QuestBuildAndUpload.BuildQuestAPK
□ Upload to alpha with notes "v120: Drone Demo Phase 2 — trained PPO trajectory (VLM ship-it 8/10)"
□ Test in Quest 3, compare against drone_trained.mp4 in this folder
□ Confirm with Deepak that the loop plays correctly
```

— end of handoff
