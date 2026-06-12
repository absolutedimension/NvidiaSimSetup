# Drone Demo Journey — Handoff for the GurulokInnerJourney Agent

**Date:** 2026-05-18
**From:** Deepak (working in `NvidiaSimSetup/` on Mac)
**For:** the Claude Code agent running in `C:\Users\unity-t4-tesla\GurulokInnerJourney`
**Reference:** the project's own `CLAUDE_FlowArtdance_VR.md` is authoritative — this doc only describes the new addition

---

## TL;DR

Add a new **"Drone Demo"** journey to the GurulokInnerJourney Unity app, mirroring the structure of the existing **Ram Chanting** / **Dance** journeys. The journey spawns an NVIDIA Crazyflie 2.X quadcopter in front of the user that hovers + slowly spins so the user can see it from all sides. **Build v64, push to alpha.**

This is **Phase 1 (static)** of a larger pipeline — eventually the drone will be animated by a trained PPO policy's trajectory exported from a separate AWS Isaac Sim setup. Don't worry about that part yet — just ship a static-hover demo first to validate the GLB import, prefab pipeline, menu integration, and the user actually sees the drone in VR.

---

## Why this matters (one paragraph)

A sister project (`NvidiaSimSetup/` on Deepak's Mac) is training a drone-fly-from-A-to-B policy in Isaac Sim on AWS. The original plan used MP4 video over NICE DCV for visual eval, but DCV times out from India to us-east-1 and Isaac Sim's `--video` flag is broken on driver 595. So we pivoted: **GurulokInnerJourney becomes the visual-eval layer.** Step 1 is "drop a static Crazyflie GLB into the existing journey menu and see it in VR." Step 2 (later) wires in trajectory animation from trained policies.

---

## What's already done

| Item | Status |
|---|---|
| Source asset: `cf2x.usd` from NVIDIA Isaac Sim 6.0 (`Isaac/Robots/Bitcraze/Crazyflie/`) | ✅ |
| Converted USD → GLB via Blender 4.5 with `usd_to_glb.py` (4 rotor primitives, glTF 2.0 binary, 250 KB) | ✅ |
| GLB tested rendering successfully via NVIDIA OVRTX renderer (Phase 1/2 of NvidiaSimSetup) | ✅ |
| GLB file ready to transfer: `cf2x.glb` sits alongside this doc | ✅ |

What you do:
1. Transfer the GLB to the Windows machine
2. Create a new journey package mirroring the Ram Chanting pattern
3. Build APK + upload to alpha
4. Confirm the drone appears in VR

---

## File transfer

The GLB (250 KB) is alongside this doc. Deepak will hand you the file via:
- Direct file transfer to the Windows box (USB / OneDrive / scp), OR
- Pulling from the AWS box where it also lives at `ubuntu@<EC2_IP>:/tmp/cf2x.glb` and `ubuntu@<EC2_IP>:/home/ubuntu/assets/Crazyflie/cf2x.glb` (current IP from NvidiaSimSetup/CLAUDE.md), OR
- Re-converting on the Windows machine if Blender 4.5 LTS with USD support is installed there (faster path; the source USD is small and `usd_to_glb.py` is straightforward)

**Where to put it on the Windows machine:**
```
C:\Users\unity-t4-tesla\GurulokInnerJourney\Assets\_App\DroneJourney\Models\cf2x.glb
```

You'll need to create that `DroneJourney/Models/` folder.

---

## What to build

A new journey package at `Assets/_App/DroneJourney/` containing:

```
Assets/_App/DroneJourney/
├── Models/
│   └── cf2x.glb                         ← the asset
├── DroneJourneyController.cs            ← implements IJourney
└── (optional) MandalaDrone_Mat.mat      ← skip for v64 — drone uses its own GLB material
```

And **one new editor setup script** at `Assets/_App/Editor/DroneJourneySetup.cs`.

That's it. No new shaders, no audio (initially), no menu wiring — your existing pattern auto-handles the menu.

---

## Implementation

### 1. `DroneJourneyController.cs`

Implements `IJourney` so the menu auto-discovers it. Simpler than CosmicJourneyController because there's no mandala, no audio coupling, no shader uniform ramp — just spawn a GameObject, hover-animate it on Update, hide on exit.

```csharp
// File: Assets/_App/DroneJourney/DroneJourneyController.cs
using UnityEngine;
using EnergyField.Core.Data; // for IJourney - confirm namespace from existing journeys

namespace EnergyField.App.DroneJourney
{
    public class DroneJourneyController : MonoBehaviour, IJourney
    {
        [SerializeField] public string displayName = "Drone Demo";
        [SerializeField] public GameObject droneRoot;           // the prefab/instance of cf2x.glb
        [SerializeField] public Transform headToFollow;         // XR camera, like other journeys
        [SerializeField] public float spawnOffsetForward = 2.0f;
        [SerializeField] public float spawnOffsetUp = 0.2f;
        [SerializeField] public float hoverBobAmplitude = 0.08f;
        [SerializeField] public float hoverBobSpeed = 2.0f;
        [SerializeField] public float yawSpeedDegPerSec = 30.0f;

        public bool Active { get; private set; }
        public string DisplayName => displayName;

        Vector3 _anchorPos;
        float _t;

        public void StartJourney()
        {
            if (droneRoot == null) return;
            // Anchor in front of the user's head at start, then stay world-fixed (no head follow)
            if (headToFollow != null)
            {
                _anchorPos = headToFollow.position
                           + headToFollow.forward * spawnOffsetForward
                           + Vector3.up * spawnOffsetUp;
            }
            else
            {
                _anchorPos = transform.position;
            }
            droneRoot.transform.position = _anchorPos;
            droneRoot.transform.rotation = Quaternion.identity;
            droneRoot.SetActive(true);
            _t = 0f;
            Active = true;
        }

        public void EndJourney()
        {
            Active = false;
            if (droneRoot != null) droneRoot.SetActive(false);
        }

        void Update()
        {
            if (!Active || droneRoot == null) return;
            _t += Time.deltaTime;
            float bobY = hoverBobAmplitude * Mathf.Sin(_t * hoverBobSpeed);
            float driftX = 0.15f * Mathf.Sin(_t * 0.7f);
            droneRoot.transform.position = _anchorPos + new Vector3(driftX, bobY, 0f);
            droneRoot.transform.rotation = Quaternion.Euler(0f, (_t * yawSpeedDegPerSec) % 360f, 0f);
        }
    }
}
```

> Confirm the `IJourney` namespace from `CosmicJourneyController.cs` before pasting — fix the `using` line to match. The interface contract per CLAUDE_FlowArtdance_VR.md §5: `StartJourney()`, `EndJourney()`, `bool Active`, `string DisplayName`.

### 2. `DroneJourneySetup.cs` (Editor)

Mirror of `RamChantingJourneySetup.cs` but minimal — no audio clip, no shader, just import the GLB and instantiate it. Per CLAUDE_FlowArtdance_VR.md §8 v46 gotcha and §8 v62 gotcha, the script must:
- Delete any prior `DroneJourney` root before re-creating (idempotent)
- Re-run `JourneyMenuSetup.SetupMenu()` at the end (so the menu auto-includes the new journey)
- Clean any orphaned children attached to the XR camera from prior runs (use the `DestroyOrphansByName` helper pattern used in `DanceJourneySetup` v62)

Skeleton:

```csharp
// File: Assets/_App/Editor/DroneJourneySetup.cs
using UnityEngine;
using UnityEditor;
using EnergyField.App.DroneJourney;

public static class DroneJourneySetup
{
    private const string ROOT_NAME = "DroneJourney";
    private const string GLB_ASSET_PATH = "Assets/_App/DroneJourney/Models/cf2x.glb";

    [MenuItem("EnergyField/Setup Drone Demo Journey in SampleScene")]
    public static void Setup()
    {
        // 1. Find XR camera (head-to-follow) — copy the lookup pattern from RamChantingJourneySetup
        var xrCam = GameObject.Find("Main Camera") ?? Camera.main?.gameObject;

        // 2. Delete prior journey root if it exists (idempotent re-run)
        var prior = GameObject.Find(ROOT_NAME);
        if (prior != null) Object.DestroyImmediate(prior);

        // 3. Clean orphaned children on XR camera (mirror DanceJourneySetup v62 cleanup)
        //    Not strictly needed here since DroneJourney doesn't parent anything to camera,
        //    but good hygiene if you later add a fade overlay.

        // 4. Create the journey root
        var root = new GameObject(ROOT_NAME);

        // 5. Instantiate the imported GLB as a child
        var droneAsset = AssetDatabase.LoadAssetAtPath<GameObject>(GLB_ASSET_PATH);
        if (droneAsset == null)
        {
            Debug.LogError($"[DroneJourneySetup] GLB not found at {GLB_ASSET_PATH}. " +
                           "Drop cf2x.glb in that folder and re-run.");
            return;
        }
        var drone = (GameObject)PrefabUtility.InstantiatePrefab(droneAsset, root.transform);
        drone.name = "CrazyflieDrone";

        // 6. Real Crazyflie is ~10 cm — scale up so it reads in VR
        drone.transform.localScale = Vector3.one * 5f;

        // 7. Start invisible — journey controller toggles SetActive
        drone.SetActive(false);

        // 8. Attach controller
        var ctrl = root.AddComponent<DroneJourneyController>();
        ctrl.displayName = "Drone Demo";
        ctrl.droneRoot = drone;
        ctrl.headToFollow = xrCam != null ? xrCam.transform : null;

        // 9. Save scene + auto-rebuild journey menu so the new entry appears
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        JourneyMenuSetup.SetupMenu();  // confirm exact method name from JourneyMenuSetup.cs

        Debug.Log("[DroneJourneySetup] Drone Demo journey wired. Build + upload v64.");
    }
}
```

> Confirm namespaces + the `JourneyMenuSetup` method name from the actual file in the project before pasting. The skeleton above mirrors §4's editor-menu pattern but a few class/method names may differ — fix them.

### 3. Add scene-dirty save guard

If your project pattern requires `EditorSceneManager.SaveScene()` or similar to persist the scene change (some setup scripts in this project do, some don't — check `DanceJourneySetup.cs`), copy that pattern.

---

## Run it

### Via Unity Editor menu (interactive)

`EnergyField → Setup Drone Demo Journey in SampleScene`

### Via batch mode (matches CLAUDE_FlowArtdance_VR.md §4)

```bash
"/c/Program Files/Unity/Hub/Editor/6000.4.2f1/Editor/Unity.exe" \
  -batchmode -nographics -quit \
  -projectPath "C:\Users\unity-t4-tesla\GurulokInnerJourney" \
  -executeMethod DroneJourneySetup.Setup \
  -logFile - 2>&1 | grep -E "(\[DroneJourneySetup\]|\[JourneyMenu\]|error CS|Exception)"
```

---

## Build + upload

Use the exact commands from CLAUDE_FlowArtdance_VR.md §3:

```bash
# Build APK (auto-bumps versionCode ≥ 12, so this lands at v64)
"/c/Program Files/Unity/Hub/Editor/6000.4.2f1/Editor/Unity.exe" \
  -batchmode -nographics -quit \
  -projectPath "C:\Users\unity-t4-tesla\GurulokInnerJourney" \
  -executeMethod QuestBuildAndUpload.BuildQuestAPK \
  -logFile - 2>&1 | grep -E "(Build succeeded|Build failed|Version code|error CS|APK:)" | head -10

# Upload to alpha (credentials are in CLAUDE_FlowArtdance_VR.md §2 — don't paste here)
"/c/Users/unity-t4-tesla/Gurulok-EnergyField/Tools/ovr-platform-util.exe" \
  upload-quest-build \
  --app-id 24914535711578182 \
  --app-secret <see CLAUDE_FlowArtdance_VR.md §2> \
  --apk "C:\Users\unity-t4-tesla\GurulokInnerJourney\Builds\GurulokInnerJourney.apk" \
  --channel alpha \
  --notes "v64: add Drone Demo Journey (static Crazyflie hover)"
```

---

## What success looks like (in Quest 3 ALPHA)

After installing v64:
1. Launch app → base scene loads as normal
2. Open journey menu (press **X** on left controller)
3. New entry **"Drone Demo"** appears alongside Cosmic / 432 Raam Naam / Deep Meditation (Bhairavi) / Dance
4. Pick "Drone Demo" with trigger
5. A Crazyflie quadcopter appears ~2 m in front, ~50 cm wide, gently bobbing + spinning so all 4 rotors visible
6. Press **X** again → menu reappears → press "Return to Base Scene" → drone disappears, base scene restored

---

## Failure modes to watch for (cross-reference CLAUDE_FlowArtdance_VR.md §8)

| Symptom | Likely cause | Fix |
|---|---|---|
| Drone appears as flat white blob | URP unlit material from GLB import not respecting the embedded textures | Right-click `cf2x.glb` → Reimport. Verify the imported materials are URP/Lit not Standard. If still white, manually swap to a URP/Unlit cyan material as a stopgap. |
| Drone doesn't appear at all | `headToFollow` is null at runtime (XR camera lookup happened pre-XR-init) | Mirror `CosmicJourneyController`'s late-bind pattern: cache the XR camera transform in `StartJourney` not `Awake`. |
| "Drone Demo" menu entry not appearing | `JourneyMenuSetup.SetupMenu()` not invoked after spawning, or invoked but failed silently | Re-run the setup script; check the menu's `journeys[]` serialized array in Inspector. |
| Build fails with `error CS0246` for `IJourney` | Wrong namespace `using` in DroneJourneyController.cs | Copy the exact `using` lines from `CosmicJourneyController.cs`. |
| versionCode collision on upload | Forgot to bump | `QuestBuildAndUpload` auto-bumps to ≥ 12; CLAUDE_FlowArtdance_VR.md §8 covers this. |

---

## Standing technical debt this touches

From CLAUDE_FlowArtdance_VR.md §11 "Standing technical debt":
- ✅ The "menu auto-rebuild safeguard for CosmicJourneySetup + RamChantingJourneySetup" doesn't directly apply, but **DroneJourneySetup MUST include the safeguard from day one** (matches the v46 lesson) — already in the skeleton above.

Don't fix unrelated tech debt in v64. Ship the drone, nothing else.

---

## Phase 2 (not yet — just so you know what's coming)

In a future session, the same DroneJourney will receive an animated GLB derived from a trained PPO trajectory. Key facts for that future work:

- Source: trajectory.json (positions + orientations per frame at 24 fps) exported from Isaac Lab `play.py` on AWS
- Bake: `usd_to_glb.py` already sets `export_animations=True` — the source USD gets time-sampled `xformOp:translate` per Avinash's pattern in NvidiaSimSetup
- Per CLAUDE_FlowArtdance_VR.md PRIMITIVE 3, the GLB animation **must be pushed to an NLA strip in Blender** for Unity's `Animated()` to play it — that step lives in `usd_to_glb.py` in NvidiaSimSetup, will be updated before Phase 2

For v64, just ship the static-hover demo.

---

## Quick checklist for the picking-up agent

```
□ Read this entire doc
□ Read CLAUDE_FlowArtdance_VR.md §4 (editor menus), §5 (architecture), §8 (gotchas)
□ Open RamChantingJourneySetup.cs + CosmicJourneyController.cs as templates for code style + namespaces
□ Transfer cf2x.glb to Assets/_App/DroneJourney/Models/
□ Create DroneJourneyController.cs (snippet above, fix namespaces)
□ Create DroneJourneySetup.cs (snippet above, fix method-name + namespaces)
□ Run "EnergyField → Setup Drone Demo Journey in SampleScene"
□ Verify in Editor: SampleScene has a "DroneJourney" root with CrazyflieDrone child, JourneyMenu has new "Drone Demo" entry
□ Run QuestBuildAndUpload.BuildQuestAPK
□ Upload to alpha with notes "v64: add Drone Demo Journey (static Crazyflie hover)"
□ Confirm with Deepak that the drone is visible in VR
```

— end of handoff
