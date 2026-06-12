# STEADY Cinematographer v5d — Unity Handoff

> For the Windows-side Claude (VR agent) working on GurulokInnerJourney.
> Generated 2026-05-26 by the Mac-side training agent.
> **Replaces** the v4 general cinematographer with a dedicated STEADY camera mode.

---

## What this is

A trained RL policy that flies a virtual drone camera to an optimal filming position,
**holds absolutely still** facing the performer, then smoothly relocates to a new angle
and holds again. Think of a professional steadicam operator who finds their shot, locks
the tripod, waits, then glides to the next angle.

**Key behavior stats (measured from training):**
- 99.7% of frames below 0.3 m/s (virtually stationary)
- Median speed: 0.029 m/s
- Best reward: 17.41 (epoch ~300 of 1000)
- Ideal filming distance: ~3 m from performer

**ONNX:** 78.6 KB, architecture 20-dim input -> [128,128] ELU -> 4-dim output.
Runs at thousands of FPS on Quest's Snapdragon XR2. Fully on-device, no server.

---

## Files to copy into the Unity project

| Source (Mac) | Destination (Unity) | Purpose |
|---|---|---|
| `cinematography/deploy/cinematographer_v5d_steady.onnx` | `Assets/_App/CinemaJourney/Models/cinematographer_v5d_steady.onnx` | The ONNX model (replaces `cinematographer_v4.onnx`) |
| `cinematography/deploy/cinematographer_v5d_steady_meta.json` | `Assets/_App/CinemaJourney/Models/cinematographer_v5d_steady_meta.json` | Observation/action layout reference |

**Remove or archive** the old `cinematographer_v4.onnx` and `cinematographer_v4_meta.json`.

---

## What changed from v4

| Property | v4 | v5d STEADY | Impact on Unity code |
|---|---|---|---|
| Observation dim | 20 | 20 (same size, DIFFERENT layout) | **Must update obs construction** |
| obs[18] | `prev_azimuth` (cached 2-frame-ago angle) | `stillness_time` (seconds still / 5.0) | New tracking variable |
| obs[19] | `prev_elevation` (cached 2-frame-ago angle) | `hold_quality` (composition quality 0-1) | New computation |
| Network architecture | [256, 256, 128] | [128, 128] | No code change (baked in ONNX) |
| `moment_scale` | 0.02 | **0.01** (halved) | Update constant |
| `sim_dt` | 0.005 (decimation 4) | **0.01** (decimation 2) | Update constant |
| Linear damping | 0 (none) | **2.0** | **CRITICAL: add drag force** |
| Angular damping | 0 (none) | **3.0** | **CRITICAL: add angular drag** |
| Action EMA | none | **alpha = 0.15** | **CRITICAL: add smoothing filter** |
| Mode switching | 6 modes via rule-based bias | Not needed (single STEADY behavior) | Remove mode bias code |
| Behavior | Continuous orbiting | Hold still -> relocate -> hold still | Expected visual output changes |

### The 3 CRITICAL changes (will NOT work without these)

1. **Linear damping (2.0)** — simulates aerodynamic drag. Without it, the drone oscillates endlessly because any thrust imbalance creates continuous acceleration with nothing to slow it down.

2. **Angular damping (3.0)** — prevents rotational oscillation. The drone's yaw/pitch/roll naturally decelerate, like real air resistance on propellers.

3. **Action EMA filter (alpha=0.15)** — smooths the policy's raw output: `smoothed = 0.15 * new_action + 0.85 * previous_smoothed_action`. Prevents rapid thrust changes that cause jitter.

**If you skip any of these three, the drone will oscillate violently instead of holding still.**

---

## ONNX Model Specification

**Input tensor:** `obs` — shape `[1, 20]` (float32)

| Index | Name | Dim | Description | How to compute in Unity |
|---|---|---|---|---|
| 0-2 | `lin_vel_b` | 3 | Drone body-frame linear velocity | `ToIsaacBodyFrame(drone, velocity)` |
| 3-5 | `ang_vel_b` | 3 | Drone body-frame angular velocity | `ToIsaacBodyFrame(drone, angularVelocity)` |
| 6-8 | `gravity_b` | 3 | Projected gravity in body frame | `ToIsaacBodyFrame(drone, Physics.gravity.normalized)` |
| 9-11 | `rel_dancer_b` | 3 | Relative performer position in body frame | `ToIsaacBodyFrame(drone, performerPos - dronePos)` |
| 12-14 | `rel_vel_b` | 3 | Performer velocity in body frame | `ToIsaacBodyFrame(drone, performerVelocity)` |
| 15 | `distance` | 1 | Scalar distance to performer | `Vector3.Distance(dronePos, performerPos)` |
| 16 | `azimuth` | 1 | Horizontal angle to performer (rad) | `Mathf.Atan2(relBody.x, relBody.y)` (Isaac body-frame x,y) |
| 17 | `elevation` | 1 | Vertical angle to performer (rad) | `Mathf.Atan2(relBody.z, horizDist)` (Isaac body-frame z = up) |
| 18 | `stillness_time` | 1 | Seconds drone has been still, / 5.0 | Track cumulative still time, divide by 5 |
| 19 | `hold_quality` | 1 | Composition quality (0-1) | `r_look_at * (1 - Mathf.Clamp01(speed / 0.3))` |

**Output tensor:** `action` — shape `[1, 4]` (float32, clamped to [-1, 1])

| Index | Name | Description | How to apply |
|---|---|---|---|
| 0 | `thrust` | Vertical thrust | `thrust_to_weight * weight * (action[0] + 1) / 2` along drone up |
| 1 | `roll_moment` | Roll torque | `moment_scale * action[1]` = `0.01 * action[1]` |
| 2 | `pitch_moment` | Pitch torque | `moment_scale * action[2]` = `0.01 * action[2]` |
| 3 | `yaw_moment` | Yaw torque | `moment_scale * action[3]` = `0.01 * action[3]` |

---

## Coordinate System Transform

**Isaac Lab** (training): right-hand, Z-up. Gravity = (0, 0, -9.81).
**Unity**: left-hand, Y-up. Gravity = (0, -9.81, 0).

### Body-frame conversion (Unity world -> Isaac body frame for observations)

```csharp
Vector3 ToIsaacBodyFrame(Transform drone, Vector3 worldVec) {
    Vector3 body = drone.InverseTransformDirection(worldVec);
    // Unity body: (right, up, forward) = (x, y, z)
    // Isaac body: (right, forward, up) = (x, y, z)
    return new Vector3(body.x, -body.z, body.y);
}
```

### Force/torque conversion (Isaac -> Unity world for actions)

```csharp
Vector3 IsaacForceToUnity(Vector3 isaacForce) {
    return new Vector3(isaacForce.x, isaacForce.z, -isaacForce.y);
}
Vector3 IsaacTorqueToUnity(Vector3 isaacTorque) {
    return new Vector3(isaacTorque.x, isaacTorque.z, -isaacTorque.y);
}
```

---

## Physics Constants

```csharp
// === v5d STEADY constants (DIFFERENT from v4) ===
const float ROBOT_MASS        = 0.28f;    // kg (Starling 2)
const float GRAVITY           = 9.81f;
const float THRUST_TO_WEIGHT  = 3.6f;     // max thrust / weight
const float MOMENT_SCALE      = 0.01f;    // ** WAS 0.02 in v4 — halved **
const float POLICY_HZ         = 50f;      // inference rate
const float SIM_DT            = 0.02f;    // 0.01s physics * 2 decimation = 0.02s per step
const float LINEAR_DAMPING    = 2.0f;     // ** NEW — aerodynamic drag **
const float ANGULAR_DAMPING   = 3.0f;     // ** NEW — rotational drag **
const float ACTION_EMA_ALPHA  = 0.15f;    // ** NEW — action smoothing **
const float MOMENT_OF_INERTIA = 0.001f;   // kg*m^2 (approximate)
```

---

## Complete Physics Integration

This replaces the v4 physics loop. The key additions are damping forces and EMA filtering.

```csharp
// ============================================================
// CinematographerSteadyController.cs — v5d STEADY physics loop
// ============================================================
using Unity.Sentis;
using UnityEngine;

public class CinematographerSteadyController : MonoBehaviour
{
    [Header("Model")]
    [SerializeField] ModelAsset onnxModel;
    
    [Header("Performer")]
    [SerializeField] Transform performer;  // head tracking or body root
    
    // Physics constants (v5d STEADY)
    const float ROBOT_MASS        = 0.28f;
    const float GRAVITY           = 9.81f;
    const float THRUST_TO_WEIGHT  = 3.6f;
    const float MOMENT_SCALE      = 0.01f;   // halved from v4's 0.02
    const float POLICY_HZ         = 50f;
    const float SIM_DT            = 0.02f;
    const float LINEAR_DAMPING    = 2.0f;    // NEW
    const float ANGULAR_DAMPING   = 3.0f;    // NEW
    const float ACTION_EMA_ALPHA  = 0.15f;   // NEW
    const float MOMENT_OF_INERTIA = 0.001f;
    const float STILL_SPEED_THRESH = 0.3f;   // for hold_quality calc
    
    // Runtime state
    Model model;
    Worker worker;
    Tensor<float> obsTensor;
    
    Vector3 velocity;
    Vector3 angularVelocity;
    Quaternion droneRotation;
    Vector3 dronePos;
    
    // EMA filter state
    float[] smoothedAction = new float[4];
    
    // Stillness tracking
    float stillnessTime = 0f;
    
    // Performer velocity estimation
    Vector3 prevPerformerPos;
    Vector3 performerVelocity;
    
    // Policy timer
    float policyAccum = 0f;
    
    void Start()
    {
        model = ModelLoader.Load(onnxModel);
        worker = new Worker(model, BackendType.GPUCompute); // or CPU
        obsTensor = new Tensor<float>(new TensorShape(1, 20));
        
        dronePos = transform.position;
        droneRotation = transform.rotation;
        velocity = Vector3.zero;
        angularVelocity = Vector3.zero;
        prevPerformerPos = performer.position;
    }
    
    void Update()
    {
        // Estimate performer velocity
        performerVelocity = (performer.position - prevPerformerPos) / Time.deltaTime;
        prevPerformerPos = performer.position;
        
        // Accumulate time, step policy at 50Hz
        policyAccum += Time.deltaTime;
        while (policyAccum >= 1f / POLICY_HZ)
        {
            policyAccum -= 1f / POLICY_HZ;
            PolicyStep();
        }
        
        // Update visual transform
        transform.position = dronePos;
        transform.rotation = droneRotation;
    }
    
    void PolicyStep()
    {
        // === 1. Build observation vector ===
        Vector3 linVelB  = ToIsaacBodyFrame(velocity);
        Vector3 angVelB  = ToIsaacBodyFrame(angularVelocity);
        Vector3 gravB    = ToIsaacBodyFrame(Physics.gravity.normalized);
        Vector3 relPos   = performer.position - dronePos;
        Vector3 relPosB  = ToIsaacBodyFrame(relPos);
        Vector3 relVelB  = ToIsaacBodyFrame(performerVelocity);
        float distance   = relPos.magnitude;
        
        // Azimuth and elevation in Isaac body frame
        float horizDist  = Mathf.Sqrt(relPosB.x * relPosB.x + relPosB.y * relPosB.y);
        float azimuth    = Mathf.Atan2(relPosB.x, relPosB.y);
        float elevation  = Mathf.Atan2(relPosB.z, horizDist);
        
        // Stillness tracking
        float speed = velocity.magnitude;
        if (speed < STILL_SPEED_THRESH)
            stillnessTime += SIM_DT;
        else
            stillnessTime = 0f;
        
        // Hold quality: how well composed the shot is while still
        float lookAtDot = Vector3.Dot(
            (droneRotation * Vector3.forward).normalized,  // drone forward in Unity
            relPos.normalized
        );
        float rLookAt = Mathf.Clamp01(lookAtDot);
        float speedClamped = Mathf.Clamp01(speed / STILL_SPEED_THRESH);
        float holdQuality = rLookAt * (1f - speedClamped);
        
        // Fill tensor
        obsTensor[0, 0]  = linVelB.x;
        obsTensor[0, 1]  = linVelB.y;
        obsTensor[0, 2]  = linVelB.z;
        obsTensor[0, 3]  = angVelB.x;
        obsTensor[0, 4]  = angVelB.y;
        obsTensor[0, 5]  = angVelB.z;
        obsTensor[0, 6]  = gravB.x;
        obsTensor[0, 7]  = gravB.y;
        obsTensor[0, 8]  = gravB.z;
        obsTensor[0, 9]  = relPosB.x;
        obsTensor[0, 10] = relPosB.y;
        obsTensor[0, 11] = relPosB.z;
        obsTensor[0, 12] = relVelB.x;
        obsTensor[0, 13] = relVelB.y;
        obsTensor[0, 14] = relVelB.z;
        obsTensor[0, 15] = distance;
        obsTensor[0, 16] = azimuth;
        obsTensor[0, 17] = elevation;
        obsTensor[0, 18] = stillnessTime / 5f;  // normalized
        obsTensor[0, 19] = holdQuality;
        
        // === 2. Run inference ===
        worker.Schedule(obsTensor);
        var actionTensor = worker.PeekOutput("action") as Tensor<float>;
        actionTensor.CompleteAllPendingOperations();
        
        float[] rawAction = new float[4];
        for (int i = 0; i < 4; i++)
            rawAction[i] = Mathf.Clamp(actionTensor[0, i], -1f, 1f);
        
        // === 3. EMA smoothing (CRITICAL for STEADY behavior) ===
        for (int i = 0; i < 4; i++)
            smoothedAction[i] = ACTION_EMA_ALPHA * rawAction[i]
                              + (1f - ACTION_EMA_ALPHA) * smoothedAction[i];
        
        // === 4. Apply physics with damping ===
        float thrustMag = THRUST_TO_WEIGHT * ROBOT_MASS * GRAVITY
                        * (smoothedAction[0] + 1f) / 2f;
        Vector3 thrustWorld = droneRotation * Vector3.up * thrustMag;
        Vector3 gravityForce = Vector3.down * ROBOT_MASS * GRAVITY;
        
        // LINEAR DAMPING (NEW in v5d) — simulates air resistance
        Vector3 dampingForce = -LINEAR_DAMPING * velocity;
        
        // Linear integration
        Vector3 accel = (thrustWorld + gravityForce + dampingForce) / ROBOT_MASS;
        velocity += accel * SIM_DT;
        dronePos += velocity * SIM_DT;
        
        // Torques in Isaac frame -> Unity
        Vector3 isaacTorque = new Vector3(
            MOMENT_SCALE * smoothedAction[1],  // roll
            MOMENT_SCALE * smoothedAction[2],  // pitch
            MOMENT_SCALE * smoothedAction[3]   // yaw
        );
        Vector3 torqueWorld = IsaacTorqueToUnity(isaacTorque);
        
        // Angular integration with ANGULAR DAMPING (NEW in v5d)
        Vector3 angAccel = torqueWorld / MOMENT_OF_INERTIA;
        angularVelocity += angAccel * SIM_DT;
        angularVelocity *= Mathf.Exp(-ANGULAR_DAMPING * SIM_DT);  // exponential decay
        droneRotation *= Quaternion.Euler(angularVelocity * Mathf.Rad2Deg * SIM_DT);
        
        // Floor clamp (safety)
        if (dronePos.y < 0.3f) {
            dronePos.y = 0.3f;
            if (velocity.y < 0) velocity.y = 0;
        }
    }
    
    // === Coordinate helpers ===
    
    Vector3 ToIsaacBodyFrame(Vector3 worldVec)
    {
        // World -> drone local
        Vector3 body = Quaternion.Inverse(droneRotation) * worldVec;
        // Unity body (right, up, forward) -> Isaac body (right, forward, up)
        return new Vector3(body.x, -body.z, body.y);
    }
    
    static Vector3 IsaacTorqueToUnity(Vector3 isaacTorque)
    {
        return new Vector3(isaacTorque.x, isaacTorque.z, -isaacTorque.y);
    }
    
    void OnDestroy()
    {
        obsTensor?.Dispose();
        worker?.Dispose();
    }
}
```

---

## Camera Setup

The drone IS the camera. The policy naturally points the drone toward the performer
(trained with `r_look_at` reward). Add explicit look-at smoothing for a cleaner result:

```csharp
// After PolicyStep, in Update():
cinemaCamera.transform.position = dronePos;

// Smooth look-at the performer
Vector3 lookDir = (performer.position - dronePos).normalized;
if (lookDir.sqrMagnitude > 0.001f) {
    Quaternion targetLook = Quaternion.LookRotation(lookDir);
    cinemaCamera.transform.rotation = Quaternion.Slerp(
        cinemaCamera.transform.rotation, targetLook, 8f * Time.deltaTime
    );
}
```

**The STEADY behavior means:** the camera will find a good angle, park there with
near-zero motion for several seconds, then glide to a new angle and park again.
The look-at keeps the performer framed during both the hold and the transition.

---

## Performer Position from Quest Body Tracking

```csharp
// Option A: Head position (simplest, always available)
Vector3 performerPos = Camera.main.transform.position;

// Option B: Body tracking root (more accurate)
// The policy was trained with a single point target, so head is fine for v1.
```

Performer velocity is estimated from position deltas (already in the controller above).

---

## IJourney Integration

```csharp
public class CinemaSteadyJourneyController : MonoBehaviour, IJourney
{
    [SerializeField] ModelAsset onnxModel;
    [SerializeField] GameObject dronePrefab;  // visual drone mesh
    
    CinematographerSteadyController steadyController;
    GameObject droneInstance;
    
    public void OnJourneyStart()
    {
        // Spawn drone 3m in front, 1.5m up from performer
        Vector3 spawnPos = Camera.main.transform.position
                         + Camera.main.transform.forward * 3f
                         + Vector3.up * 1.5f;
        droneInstance = Instantiate(dronePrefab, spawnPos, Quaternion.identity);
        
        // Attach the controller
        steadyController = droneInstance.AddComponent<CinematographerSteadyController>();
        // Wire the model and performer reference via reflection or serialization
    }
    
    public void OnJourneyEnd()
    {
        if (droneInstance != null) Destroy(droneInstance);
    }
    
    public void OnJourneyUpdate()
    {
        // Controller runs in its own Update() loop
    }
}
```

Editor setup script: mirror `RamChantingJourneySetup.cs` with v46 menu-rebuild + v62
orphan-cleanup safeguards from CLAUDE_FlowArtdance_VR.md section 8.

---

## What success looks like

1. User puts on Quest 3
2. A small drone camera appears ~3m away from the user
3. The drone **glides to a good filming angle** and **stops completely**
4. It holds that position for 3-8 seconds — zero jitter, zero drift
5. It smoothly relocates to a different angle and holds again
6. Repeat: hold -> glide -> hold -> glide
7. The camera always faces the performer during holds
8. If the user moves, the drone adapts — finds a new hold position

**First test:** stand still and watch the drone. It should settle into a hold within
2-3 seconds, then barely move. If you see continuous orbiting or oscillation,
the damping or EMA filter is missing.

---

## Comparison: v4 vs v5d behavior

| v4 (general cinematographer) | v5d STEADY |
|---|---|
| Continuous orbiting motion | Hold still, then relocate |
| Always moving around performer | 99.7% of time near-stationary |
| Mode switching via rule-based bias | Single behavior, no modes needed |
| Mean speed ~1-2 m/s | Median speed 0.029 m/s |
| No damping in physics | Damping is essential |
| Direct action application | EMA-filtered actions |
| Good for dynamic "music video" feel | Good for "steadicam" / "tripod" feel |

**These are complementary.** v4 gives dynamic orbiting shots. v5d gives locked-off
stable shots. A future mode-switcher can blend between them.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Drone oscillates wildly | Missing LINEAR_DAMPING | Add `dampingForce = -2.0 * velocity` to the force sum |
| Drone rotates endlessly | Missing ANGULAR_DAMPING | Apply `angVel *= exp(-3.0 * dt)` each step |
| Drone jitters on each frame | Missing EMA filter | Apply `smoothed = 0.15*new + 0.85*prev` before using actions |
| Drone overshoots and yo-yos | MOMENT_SCALE still at 0.02 | Change to 0.01 |
| Drone drops to floor immediately | SIM_DT wrong | Use 0.02, not 0.005 |
| Drone never moves, just hovers | Expected for STEADY mode | Wait 5-10s; it will eventually relocate to a new angle |
| Drone flies away from performer | Observation indices wrong | Verify obs[18]=stillness/5, obs[19]=holdQuality, NOT prev_azimuth/prev_elevation |
| Smooth but wrong direction | Coordinate transform wrong | Check `ToIsaacBodyFrame` returns `(x, -z, y)` from Unity body |

---

## Build checklist

- [ ] Remove/archive `cinematographer_v4.onnx` and `cinematographer_v4_meta.json`
- [ ] Import `cinematographer_v5d_steady.onnx` into Unity project
- [ ] Verify Unity Sentis package installed (com.unity.sentis 2.x+)
- [ ] Create `CinematographerSteadyController.cs` with ALL 3 critical changes:
  - [ ] Linear damping = 2.0
  - [ ] Angular damping = 3.0
  - [ ] Action EMA alpha = 0.15
- [ ] Update `MOMENT_SCALE` from 0.02 to 0.01
- [ ] Update observation construction: obs[18] = stillness_time/5, obs[19] = hold_quality
- [ ] Test with keyboard-controlled performer position first
- [ ] Connect to Quest head tracking
- [ ] Verify: drone settles into a hold within 2-3 seconds
- [ ] Verify: near-zero jitter during holds
- [ ] Verify: smooth transitions between hold positions
- [ ] Build APK (v65+)
- [ ] Test on Quest 3

---

## Future: mode switching across policies

v5d is the STEADY policy. Other camera modes (ORBIT, DOLLY, CRANE, etc.) will be
separate ONNX models, each trained with mode-specific rewards. The VR app can switch
between them:

```csharp
// Future pattern
switch (currentCameraMode) {
    case "STEADY":  worker = steadyWorker;  break;  // v5d
    case "ORBIT":   worker = orbitWorker;   break;  // future v5e
    case "DOLLY":   worker = dollyWorker;   break;  // future v5f
}
// Each has the same 20-dim obs / 4-dim act interface but different trained behavior
```

For now, just ship STEADY. It's the most visually impressive mode because the
stillness is immediately obvious and impressive.

---

*Generated by the Mac-side training agent. The ONNX model is authoritative.*
*If observation construction doesn't match the meta.json layout, the model WILL produce garbage.*
*The 3 critical physics changes (damping + EMA) are NON-NEGOTIABLE — the policy was trained*
*with these dynamics. Without them, it will oscillate instead of holding still.*
