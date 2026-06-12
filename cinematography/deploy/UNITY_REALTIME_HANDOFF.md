# Real-Time Cinematographer Drone — Unity Handoff

> For the Windows-side Claude (VR agent) working on GurulokInnerJourney.
> Generated 2026-05-25 by the Mac-side training agent.

---

## What this is

A trained RL policy that flies a virtual drone around a performer cinematically.
The policy was trained for 500 epochs in Isaac Lab on an A10G GPU. It produces
the same camera behavior as the approved 25s and 90s demo videos.

**The ONNX model runs at 50Hz, is 11 KB, and will run at thousands of FPS on
Quest's Snapdragon XR2.** There is no server dependency — inference is fully on-device.

---

## Files to copy into the Unity project

| Source (Mac) | Destination (Unity) | Purpose |
|---|---|---|
| `cinematography/deploy/cinematographer_v4.onnx` | `Assets/_App/CinemaJourney/Models/cinematographer_v4.onnx` | The ONNX model |
| `cinematography/deploy/cinematographer_v4_meta.json` | `Assets/_App/CinemaJourney/Models/cinematographer_v4_meta.json` | Observation/action layout reference |

---

## ONNX Model Specification

**Input tensor:** `observation` — shape `[1, 20]` (float32)

| Index | Name | Dim | Description | How to compute in Unity |
|---|---|---|---|---|
| 0–2 | `lin_vel_b` | 3 | Drone body-frame linear velocity | `drone.InverseTransformDirection(droneRigidbody.velocity)` |
| 3–5 | `ang_vel_b` | 3 | Drone body-frame angular velocity | `drone.InverseTransformDirection(droneRigidbody.angularVelocity)` |
| 6–8 | `gravity_b` | 3 | Projected gravity in body frame | `drone.InverseTransformDirection(Physics.gravity.normalized)` |
| 9–11 | `rel_dancer_b` | 3 | Relative performer position in body frame | `drone.InverseTransformDirection(performerPos - dronePos)` |
| 12–14 | `rel_vel_b` | 3 | Performer velocity in body frame | `drone.InverseTransformDirection(performerVelocity)` |
| 15 | `distance` | 1 | Scalar distance to performer | `Vector3.Distance(dronePos, performerPos)` |
| 16 | `azimuth` | 1 | Horizontal angle to performer (rad) | `Mathf.Atan2(relBody.x, relBody.y)` — see coord note |
| 17 | `elevation` | 1 | Vertical angle to performer (rad) | `Mathf.Atan2(relBody.z, horizDist)` — see coord note |
| 18 | `prev_azimuth` | 1 | Azimuth from 2 frames ago | Cache and delay by 2 steps |
| 19 | `prev_elevation` | 1 | Elevation from 2 frames ago | Cache and delay by 2 steps |

**Output tensor:** `action` — shape `[1, 4]` (float32, clamped to [-1, 1])

| Index | Name | Description | How to apply |
|---|---|---|---|
| 0 | `thrust` | Vertical thrust | Force Z (up in Isaac) = `thrust_to_weight * weight * (action[0] + 1) / 2` |
| 1 | `roll_moment` | Roll torque | Torque X = `moment_scale * action[1]` |
| 2 | `pitch_moment` | Pitch torque | Torque Y = `moment_scale * action[2]` |
| 3 | `yaw_moment` | Yaw torque | Torque Z = `moment_scale * action[3]` |

---

## Coordinate System Transform

**Isaac Lab** (training): right-hand, Z-up. Gravity = (0, 0, -9.81).
**Unity**: left-hand, Y-up. Gravity = (0, -9.81, 0).

### Position mapping: Isaac → Unity
```
unity.x =  isaac.x
unity.y =  isaac.z     // Isaac Z (up) → Unity Y (up)
unity.z = -isaac.y     // Isaac Y (forward) → Unity -Z (forward in LH)
```

### For observation construction (Unity → Isaac body frame):
The observation vector must be in **Isaac conventions** because that's what the
network was trained on. Inside `InverseTransformDirection`, Unity already handles
the body-frame rotation. You only need to remap the world-space axes:

```csharp
Vector3 ToIsaacBodyFrame(Transform drone, Vector3 worldVec) {
    Vector3 body = drone.InverseTransformDirection(worldVec);
    // Unity body: (right, up, forward) = (x, y, z)
    // Isaac body: (right, forward, up) = (x, y, z)
    return new Vector3(body.x, -body.z, body.y);
}
```

### For applying actions (Isaac forces → Unity forces):
```csharp
Vector3 IsaacForceToUnity(Vector3 isaacForce) {
    return new Vector3(isaacForce.x, isaacForce.z, -isaacForce.y);
}
Vector3 IsaacTorqueToUnity(Vector3 isaacTorque) {
    return new Vector3(isaacTorque.x, isaacTorque.z, -isaacTorque.y);
}
```

---

## Physics Constants (from training)

```csharp
const float ROBOT_MASS = 0.28f;           // kg (Starling 2 drone)
const float GRAVITY = 9.81f;
const float THRUST_TO_WEIGHT = 3.6f;      // max thrust / weight ratio
const float MOMENT_SCALE = 0.02f;         // Nm per unit action
const float POLICY_HZ = 50f;              // inference rate
const float SIM_DT = 0.02f;              // 0.005s × 4 decimation = 0.02s per policy step
```

---

## Simplified Physics Integration (no Rigidbody needed)

The policy outputs forces/torques. You don't need Unity's full physics engine.
A simple Euler integrator at 50Hz is sufficient:

```csharp
// Per policy step (every 0.02s = 50Hz):
float thrustMag = THRUST_TO_WEIGHT * ROBOT_MASS * GRAVITY * (action[0] + 1f) / 2f;
Vector3 thrustWorld = drone.up * thrustMag;  // thrust along drone's up axis
Vector3 gravityForce = Vector3.down * ROBOT_MASS * GRAVITY;
Vector3 dragForce = -velocity * DRAG_COEFF;  // tune DRAG_COEFF ~0.3

// Linear integration
Vector3 accel = (thrustWorld + gravityForce + dragForce) / ROBOT_MASS;
velocity += accel * SIM_DT;
dronePos += velocity * SIM_DT;

// Angular integration
Vector3 torqueWorld = IsaacTorqueToUnity(new Vector3(
    MOMENT_SCALE * action[1],
    MOMENT_SCALE * action[2],
    MOMENT_SCALE * action[3]
));
Vector3 angAccel = torqueWorld / MOMENT_OF_INERTIA;  // ~0.001 kg⋅m²
angularVelocity += angAccel * SIM_DT;
angularVelocity *= 0.98f;  // angular drag
droneRotation *= Quaternion.Euler(angularVelocity * Mathf.Rad2Deg * SIM_DT);

// Update transform
transform.position = dronePos;
transform.rotation = droneRotation;
```

**Tuning parameters** (adjust until it looks right):
- `DRAG_COEFF`: start at 0.3, increase for stability
- `MOMENT_OF_INERTIA`: start at 0.001 kg⋅m²
- `angular_drag`: the 0.98 multiplier — lower = more damped rotation

---

## Performer Position from Quest Body Tracking

The policy needs the performer's world position. On Quest:

```csharp
// Option A: Head position (simplest, always available)
Vector3 performerPos = Camera.main.transform.position;

// Option B: Body tracking root (more accurate if body tracking is on)
// Uses OVRBody or the XR Body Tracking subsystem
// Head is fine for v1 — the policy was trained with a single point target
```

The performer's **velocity** is estimated from position deltas:
```csharp
performerVelocity = (performerPos - prevPerformerPos) / Time.fixedDeltaTime;
prevPerformerPos = performerPos;
```

---

## Unity Sentis Setup

1. Install Unity Sentis via Package Manager (com.unity.sentis, version 2.x+)
2. Import the ONNX file — Sentis auto-converts to `.sentis` asset
3. Load and run:

```csharp
using Unity.Sentis;

Model model;
Worker worker;
Tensor<float> obsTensor;

void Start() {
    model = ModelLoader.Load(onnxAsset);
    worker = new Worker(model, BackendType.GPUCompute);  // or CPU
    obsTensor = new Tensor<float>(new TensorShape(1, 20));
}

void FixedUpdate() {  // 50Hz
    // Fill observation (see table above)
    obsTensor[0, 0] = linVelBody.x;
    obsTensor[0, 1] = linVelBody.y;
    // ... etc for all 20 dims
    
    worker.Schedule(obsTensor);
    var actionTensor = worker.PeekOutput("action") as Tensor<float>;
    actionTensor.CompleteAllPendingOperations();
    
    float thrust = actionTensor[0, 0];
    float rollMoment = actionTensor[0, 1];
    float pitchMoment = actionTensor[0, 2];
    float yawMoment = actionTensor[0, 3];
    
    ApplyPhysics(thrust, rollMoment, pitchMoment, yawMoment);
}

void OnDestroy() {
    obsTensor?.Dispose();
    worker?.Dispose();
}
```

---

## Camera Setup

The drone IS the camera. Attach a Camera component to the drone GameObject,
or move the scene camera to the drone's position each frame:

```csharp
// After physics integration:
cinemaCamera.transform.position = dronePos;

// Look at the performer with smoothing
Vector3 lookDir = (performerPos - dronePos).normalized;
Quaternion targetRot = Quaternion.LookRotation(lookDir);
cinemaCamera.transform.rotation = Quaternion.Slerp(
    cinemaCamera.transform.rotation, targetRot, 8f * Time.deltaTime
);
```

**Important:** The policy controls WHERE the camera goes. The look-at is separate —
the policy doesn't output a camera orientation, just position + drone attitude.
In the training env, the "drone forward" naturally points toward the dancer due
to the `r_look_at` reward. In Unity, you should add explicit look-at smoothing
for a cleaner result.

---

## IJourney Integration Pattern

Follow the existing `CosmicJourneyController.cs` / `DroneJourneyController.cs` pattern:

```csharp
public class CinemaJourneyController : MonoBehaviour, IJourney {
    [SerializeField] ModelAsset onnxModel;
    [SerializeField] float dragCoeff = 0.3f;
    [SerializeField] float angularDrag = 0.98f;
    
    // IJourney implementation
    public void OnJourneyStart() { /* load model, init state */ }
    public void OnJourneyEnd() { /* dispose worker, cleanup */ }
    public void OnJourneyUpdate() { /* run policy + physics each frame */ }
}
```

**Editor setup script** (`CinemaJourneySetup.cs`): mirror of `RamChantingJourneySetup.cs`
with v46 menu-rebuild + v62 orphan-cleanup safeguards from CLAUDE_FlowArtdance_VR.md §8.

---

## Mode Switching (future, not in current ONNX)

This policy is a general cinematographer (no mode conditioning). For mode-specific
behavior, add rule-based biases ON TOP of the policy output:

```csharp
switch (currentMode) {
    case Mode.HERO:
        // Bias thrust down (fly lower)
        action[0] -= 0.3f;
        break;
    case Mode.EPIC:
        // Bias thrust up (fly higher)
        action[0] += 0.3f;
        break;
    case Mode.INTIMATE:
        // Scale moments down (less movement)
        action[1] *= 0.5f; action[2] *= 0.5f; action[3] *= 0.5f;
        break;
}
```

A v4 mode-conditioned policy (33D obs with one-hot mode) can replace this later.

---

## What success looks like

1. User puts on Quest 3
2. They see the virtual stage (existing HDRI environment)
3. A small drone camera appears 3m away
4. User moves around → the drone reacts, flies cinematically
5. A picture-in-picture window shows the drone's camera feed (what the audience sees)
6. Director (voice or controller) says "hero" → drone drops low, looking up

**First test:** just the drone moving in response to head tracking. No PiP, no modes.
If the drone smoothly orbits and tracks the user, it's working.

---

## Build checklist

- [ ] Import `cinematographer_v4.onnx` into Unity project
- [ ] Install Unity Sentis package
- [ ] Create `CinemaJourneyController.cs` with policy inference + physics
- [ ] Create `CinemaJourneySetup.cs` editor script
- [ ] Test with keyboard-controlled "performer" position first
- [ ] Connect to Quest head tracking
- [ ] Tune drag/inertia until movement looks smooth
- [ ] Build APK (v65+)
- [ ] Test on Quest 3

---

*Generated by the Mac-side training agent. The ONNX model is authoritative.*
*If observation construction doesn't match the meta.json layout, the model WILL produce garbage.*
