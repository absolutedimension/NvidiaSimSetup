# STEADY Cinematographer v5e — Training to VR Handoff

> For the Windows-side Claude (VR agent) working on GurulokInnerJourney.
> Generated 2026-05-26 by the Mac-side training agent.
> **Replaces v5d STEADY.** Same observation/action interface, same physics constants.
> Drop-in ONNX swap with smoother transitions and stable training.

---

## What this is

A trained RL policy that flies a virtual drone camera to an optimal filming position,
**holds absolutely still** facing the performer, then smoothly relocates to a new angle
and holds again. v5e fixes v5d's training collapse and adds 3 new reward terms for
smoother transitions between hold positions.

**Key behavior stats (measured from trajectory export):**
- 93.0% of frames below 0.3 m/s (near-stationary)
- 80.4% of frames below 0.05 m/s (essentially frozen)
- Median speed: 0.021 m/s
- Best reward: 11.43 (epoch 1900 of 2000) — stable, no collapse
- Ideal filming distance: ~3 m from performer

**ONNX:** 78.6 KB, architecture 20-dim input -> [128, 128] ELU -> 4-dim output.
Runs at thousands of FPS on Quest's Snapdragon XR2. Fully on-device, no server.

---

## Delivered artifacts

| File | Format | Size | Description |
|---|---|---|---|
| `cinematographer_v5e_steady.onnx` | ONNX | 79 KB | Drop-in replacement for v5d ONNX |
| `cinematographer_v5e_steady_meta.json` | JSON | 3 KB | Obs/action layout + physics constants |
| `v5e_steady_test.mp4` | H.264 960x540 25fps | 285 KB | 25s pre-visualization (drone=blue, dancer=green, sightline=white) |
| `steady_v5e_trajectory.json` | JSON | 500 KB | 1250 frames @ 50fps raw trajectory |

---

## What changed from v5d

| Property | v5d | v5e | Impact on Unity code |
|---|---|---|---|
| Observation dim | 20 | 20 (identical) | **None** |
| Action dim | 4 | 4 (identical) | **None** |
| Physics constants | all same | all same | **None** |
| Network architecture | [128, 128] ELU | [128, 128] ELU (identical) | **None** |
| ONNX size | 78.6 KB | 78.6 KB | **None** |
| Training stability | Collapsed at ep ~300 (17.41 -> 0.107) | Stable through 2000 epochs | N/A |
| Active reward terms | 3 (stillness, look_at, distance) | 6 (+hold_bonus, action_smooth, jerk_penalty) | N/A |
| Transition smoothness | Abrupt angle changes | Jerk-minimized, buttery transitions | Visible improvement |
| Stillness (< 0.3 m/s) | 99.7% | 93.0% (trades some stillness for smoother relocations) | N/A |
| Median speed | 0.029 m/s | 0.021 m/s (actually slower median) | N/A |

### Summary: this is a pure ONNX file swap

**No C# code changes needed.** The observation layout, action layout, physics constants,
coordinate transforms, and ONNX I/O shapes are all identical to v5d. If v5d is already
integrated, just replace the `.onnx` file and the `.meta.json` file.

---

## Files to copy into the Unity project

| Source (Mac/handoff) | Destination (Unity) | Purpose |
|---|---|---|
| `cinematographer_v5e_steady.onnx` | `Assets/_App/CinemaJourney/Models/cinematographer_v5e_steady.onnx` | The ONNX model (replaces v5d) |
| `cinematographer_v5e_steady_meta.json` | `Assets/_App/CinemaJourney/Models/cinematographer_v5e_steady_meta.json` | Reference for obs/act layout |

**Remove or archive** the old `cinematographer_v5d_steady.onnx` and `cinematographer_v5d_steady_meta.json`.

---

## If v5d was ALREADY integrated (fastest path)

1. Swap the ONNX file: replace `cinematographer_v5d_steady.onnx` with `cinematographer_v5e_steady.onnx`
2. Update the `ModelAsset` reference in `CinematographerSteadyController` inspector to point at the new file
3. That's it. Build and test.

---

## If starting fresh (full integration from scratch)

### ONNX Model Specification

**Input tensor:** `obs` -- shape `[1, 20]` (float32)

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

**Output tensor:** `action` -- shape `[1, 4]` (float32, clamped to [-1, 1])

| Index | Name | Description | How to apply |
|---|---|---|---|
| 0 | `thrust` | Vertical thrust | `thrust_to_weight * weight * (action[0] + 1) / 2` along drone up |
| 1 | `roll_moment` | Roll torque | `0.01 * action[1]` |
| 2 | `pitch_moment` | Pitch torque | `0.01 * action[2]` |
| 3 | `yaw_moment` | Yaw torque | `0.01 * action[3]` |

### Coordinate System Transform

**Isaac Lab** (training): right-hand, Z-up. Gravity = (0, 0, -9.81).
**Unity**: left-hand, Y-up. Gravity = (0, -9.81, 0).

```csharp
Vector3 ToIsaacBodyFrame(Vector3 worldVec) {
    Vector3 body = Quaternion.Inverse(droneRotation) * worldVec;
    // Unity body: (right, up, forward) = (x, y, z)
    // Isaac body: (right, forward, up) = (x, y, z)
    return new Vector3(body.x, -body.z, body.y);
}

Vector3 IsaacTorqueToUnity(Vector3 isaacTorque) {
    return new Vector3(isaacTorque.x, isaacTorque.z, -isaacTorque.y);
}
```

### Physics Constants

```csharp
const float ROBOT_MASS        = 0.28f;    // kg (Starling 2)
const float GRAVITY           = 9.81f;
const float THRUST_TO_WEIGHT  = 3.6f;
const float MOMENT_SCALE      = 0.01f;    // HALF of v4's 0.02
const float POLICY_HZ         = 50f;      // inference rate
const float SIM_DT            = 0.02f;    // 0.01s physics * 2 decimation
const float LINEAR_DAMPING    = 2.0f;     // aerodynamic drag
const float ANGULAR_DAMPING   = 3.0f;     // rotational drag
const float ACTION_EMA_ALPHA  = 0.15f;    // action smoothing filter
const float MOMENT_OF_INERTIA = 0.001f;   // kg*m^2 (approximate)
```

### 3 CRITICAL physics additions (vs v4)

1. **Linear damping (2.0)** -- simulates aerodynamic drag. Without it, drone oscillates.
2. **Angular damping (3.0)** -- prevents rotational oscillation.
3. **Action EMA filter (alpha=0.15)** -- `smoothed = 0.15 * new + 0.85 * prev`. Prevents jitter.

**If you skip any of these three, the drone will oscillate violently instead of holding still.**

### Complete C# Controller

```csharp
// ============================================================
// CinematographerSteadyController.cs -- v5e STEADY physics loop
// Drop-in replacement for v5d controller (identical interface)
// ============================================================
using Unity.Sentis;
using UnityEngine;

public class CinematographerSteadyController : MonoBehaviour
{
    [Header("Model")]
    [SerializeField] ModelAsset onnxModel;
    
    [Header("Performer")]
    [SerializeField] Transform performer;

    // Physics constants (v5e STEADY -- same as v5d)
    const float ROBOT_MASS        = 0.28f;
    const float GRAVITY           = 9.81f;
    const float THRUST_TO_WEIGHT  = 3.6f;
    const float MOMENT_SCALE      = 0.01f;
    const float POLICY_HZ         = 50f;
    const float SIM_DT            = 0.02f;
    const float LINEAR_DAMPING    = 2.0f;
    const float ANGULAR_DAMPING   = 3.0f;
    const float ACTION_EMA_ALPHA  = 0.15f;
    const float MOMENT_OF_INERTIA = 0.001f;
    const float STILL_SPEED_THRESH = 0.3f;

    // Runtime state
    Model model;
    Worker worker;
    Tensor<float> obsTensor;
    
    Vector3 velocity;
    Vector3 angularVelocity;
    Quaternion droneRotation;
    Vector3 dronePos;
    
    float[] smoothedAction = new float[4];
    float stillnessTime = 0f;
    
    Vector3 prevPerformerPos;
    Vector3 performerVelocity;
    float policyAccum = 0f;

    void Start()
    {
        model = ModelLoader.Load(onnxModel);
        worker = new Worker(model, BackendType.GPUCompute);
        obsTensor = new Tensor<float>(new TensorShape(1, 20));
        
        dronePos = transform.position;
        droneRotation = transform.rotation;
        velocity = Vector3.zero;
        angularVelocity = Vector3.zero;
        prevPerformerPos = performer.position;
    }

    void Update()
    {
        performerVelocity = (performer.position - prevPerformerPos) / Time.deltaTime;
        prevPerformerPos = performer.position;
        
        policyAccum += Time.deltaTime;
        while (policyAccum >= 1f / POLICY_HZ)
        {
            policyAccum -= 1f / POLICY_HZ;
            PolicyStep();
        }
        
        transform.position = dronePos;
        transform.rotation = droneRotation;
    }

    void PolicyStep()
    {
        // 1. Build observation vector
        Vector3 linVelB  = ToIsaacBodyFrame(velocity);
        Vector3 angVelB  = ToIsaacBodyFrame(angularVelocity);
        Vector3 gravB    = ToIsaacBodyFrame(Physics.gravity.normalized);
        Vector3 relPos   = performer.position - dronePos;
        Vector3 relPosB  = ToIsaacBodyFrame(relPos);
        Vector3 relVelB  = ToIsaacBodyFrame(performerVelocity);
        float distance   = relPos.magnitude;
        
        float horizDist  = Mathf.Sqrt(relPosB.x * relPosB.x + relPosB.y * relPosB.y);
        float azimuth    = Mathf.Atan2(relPosB.x, relPosB.y);
        float elevation  = Mathf.Atan2(relPosB.z, horizDist);
        
        float speed = velocity.magnitude;
        if (speed < STILL_SPEED_THRESH)
            stillnessTime += SIM_DT;
        else
            stillnessTime = 0f;
        
        float lookAtDot = Vector3.Dot(
            (droneRotation * Vector3.forward).normalized,
            relPos.normalized
        );
        float rLookAt = Mathf.Clamp01(lookAtDot);
        float speedClamped = Mathf.Clamp01(speed / STILL_SPEED_THRESH);
        float holdQuality = rLookAt * (1f - speedClamped);
        
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
        obsTensor[0, 18] = stillnessTime / 5f;
        obsTensor[0, 19] = holdQuality;
        
        // 2. Run inference
        worker.Schedule(obsTensor);
        var actionTensor = worker.PeekOutput("action") as Tensor<float>;
        actionTensor.CompleteAllPendingOperations();
        
        float[] rawAction = new float[4];
        for (int i = 0; i < 4; i++)
            rawAction[i] = Mathf.Clamp(actionTensor[0, i], -1f, 1f);
        
        // 3. EMA smoothing (CRITICAL)
        for (int i = 0; i < 4; i++)
            smoothedAction[i] = ACTION_EMA_ALPHA * rawAction[i]
                              + (1f - ACTION_EMA_ALPHA) * smoothedAction[i];
        
        // 4. Apply physics with damping
        float thrustMag = THRUST_TO_WEIGHT * ROBOT_MASS * GRAVITY
                        * (smoothedAction[0] + 1f) / 2f;
        Vector3 thrustWorld = droneRotation * Vector3.up * thrustMag;
        Vector3 gravityForce = Vector3.down * ROBOT_MASS * GRAVITY;
        Vector3 dampingForce = -LINEAR_DAMPING * velocity;
        
        Vector3 accel = (thrustWorld + gravityForce + dampingForce) / ROBOT_MASS;
        velocity += accel * SIM_DT;
        dronePos += velocity * SIM_DT;
        
        Vector3 isaacTorque = new Vector3(
            MOMENT_SCALE * smoothedAction[1],
            MOMENT_SCALE * smoothedAction[2],
            MOMENT_SCALE * smoothedAction[3]
        );
        Vector3 torqueWorld = IsaacTorqueToUnity(isaacTorque);
        
        Vector3 angAccel = torqueWorld / MOMENT_OF_INERTIA;
        angularVelocity += angAccel * SIM_DT;
        angularVelocity *= Mathf.Exp(-ANGULAR_DAMPING * SIM_DT);
        droneRotation *= Quaternion.Euler(angularVelocity * Mathf.Rad2Deg * SIM_DT);
        
        if (dronePos.y < 0.3f) {
            dronePos.y = 0.3f;
            if (velocity.y < 0) velocity.y = 0;
        }
    }

    Vector3 ToIsaacBodyFrame(Vector3 worldVec)
    {
        Vector3 body = Quaternion.Inverse(droneRotation) * worldVec;
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

### Camera Setup

The drone IS the camera. Add smooth look-at for clean framing:

```csharp
// After PolicyStep, in Update():
cinemaCamera.transform.position = dronePos;

Vector3 lookDir = (performer.position - dronePos).normalized;
if (lookDir.sqrMagnitude > 0.001f) {
    Quaternion targetLook = Quaternion.LookRotation(lookDir);
    cinemaCamera.transform.rotation = Quaternion.Slerp(
        cinemaCamera.transform.rotation, targetLook, 8f * Time.deltaTime
    );
}
```

### IJourney Integration

```csharp
public class CinemaSteadyJourneyController : MonoBehaviour, IJourney
{
    [SerializeField] ModelAsset onnxModel;
    [SerializeField] GameObject dronePrefab;
    
    CinematographerSteadyController steadyController;
    GameObject droneInstance;
    
    public void OnJourneyStart()
    {
        Vector3 spawnPos = Camera.main.transform.position
                         + Camera.main.transform.forward * 3f
                         + Vector3.up * 1.5f;
        droneInstance = Instantiate(dronePrefab, spawnPos, Quaternion.identity);
        steadyController = droneInstance.AddComponent<CinematographerSteadyController>();
    }
    
    public void OnJourneyEnd()
    {
        if (droneInstance != null) Destroy(droneInstance);
    }
    
    public void OnJourneyUpdate() { }
}
```

---

## What success looks like

1. User puts on Quest 3
2. A small drone camera appears ~3m away from the user
3. The drone **glides to a good filming angle** and **stops completely**
4. It holds that position for 3-8 seconds -- zero jitter, zero drift
5. It **smoothly** relocates to a different angle and holds again (smoother than v5d)
6. Repeat: hold -> glide -> hold -> glide
7. The camera always faces the performer during both holds and transitions
8. If the user moves, the drone adapts

**v5e improvement you should notice:** transitions between hold positions are visibly
smoother and more "cinematic" than v5d. No abrupt direction changes, no jerk.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Drone oscillates wildly | Missing LINEAR_DAMPING | Add `dampingForce = -2.0 * velocity` |
| Drone rotates endlessly | Missing ANGULAR_DAMPING | Apply `angVel *= exp(-3.0 * dt)` |
| Drone jitters each frame | Missing EMA filter | `smoothed = 0.15*new + 0.85*prev` |
| Drone overshoots | MOMENT_SCALE still at 0.02 | Change to 0.01 |
| Drone drops to floor | SIM_DT wrong | Use 0.02, not 0.005 |
| Drone never moves | Expected STEADY behavior | Wait 5-10s, it will relocate |
| Drone flies away | Obs indices wrong | Verify obs[18]=stillness/5, obs[19]=holdQuality |
| Wrong direction | Coord transform wrong | `ToIsaacBodyFrame` must return `(x, -z, y)` |

---

## Build checklist

- [ ] Copy `cinematographer_v5e_steady.onnx` to Unity project (replace v5d)
- [ ] Copy `cinematographer_v5e_steady_meta.json` alongside it
- [ ] Update ModelAsset reference in inspector to new ONNX
- [ ] If fresh integration: create `CinematographerSteadyController.cs` with ALL 3 critical physics:
  - [ ] Linear damping = 2.0
  - [ ] Angular damping = 3.0
  - [ ] Action EMA alpha = 0.15
- [ ] Test in editor: drone settles into hold within 2-3 seconds
- [ ] Verify: transitions between holds are smooth (no abrupt jerks)
- [ ] Build APK
- [ ] Test on Quest 3

---

## What I need back

- [ ] VR test video (30s screen recording of the drone in Quest scene)
- [ ] Subjective verdict: "cinematic" / "needs work" / specific feedback on transition quality
- [ ] Build number after integration
- [ ] Comparison impression vs v5d if you saw both: are transitions smoother?

---

## Future: mode switching

v5e is the STEADY policy. Other modes (ORBIT, DOLLY, CRANE) will be separate ONNX files
with the same 20-dim / 4-dim interface. The VR app can hot-swap:

```csharp
switch (currentCameraMode) {
    case "STEADY":  worker = steadyWorker;  break;  // v5e (this file)
    case "ORBIT":   worker = orbitWorker;   break;  // future
    case "DOLLY":   worker = dollyWorker;   break;  // future
}
```

---

*Generated by the Mac-side training agent, 2026-05-26.*
*The ONNX model is authoritative. If observation construction doesn't match the meta.json, the model WILL produce garbage.*
*The 3 critical physics changes (damping + EMA) are NON-NEGOTIABLE.*
