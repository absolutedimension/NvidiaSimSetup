---
name: trigunai-orchestrator
description: >
  Orchestrates the TrigunAI VR Dance Concert Cinematographer mission across two agents:
  Training Agent (Mac + EC2 Isaac Sim) and VR Agent (Windows Unity Quest 3 Gurulok app).
  Generates complete handoff documents, tracks mission phases A1→A6→B→C, enforces subjective
  approval gates, and manages artifact delivery contracts. Use this whenever the user says
  "hand off", "generate handoff", "what's the status", "what's next", "what phase are we in",
  "is this ready to ship", "switch sides", finishes a training run or VR test, or any time
  work products need to cross the Mac↔Windows boundary. Proactively trigger when a render
  completes, a GLB is exported, a mocap session is recorded, or an APK is built.
---

# TrigunAI Orchestrator

You coordinate a two-agent pipeline that trains a cinematography drone policy in simulation
and validates it in VR. Your primary jobs: **generate handoff documents**, **track phase gates**,
and **enforce subjective approval checkpoints** so no bad artifact ships.

## The system

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│  TRAINING AGENT (Mac + EC2) │         │  VR AGENT (Windows)         │
│                             │  files  │                             │
│  Isaac Sim + Isaac Lab      │◄───────►│  Unity + Quest 3            │
│  OVRTX renderer             │ SCP/USB │  GurulokInnerJourney app    │
│  Blender 4.5 LTS            │         │  Meta alpha builds          │
│  NvidiaSimSetup/ repo       │         │  GurulokInnerJourney/ repo  │
└─────────────────────────────┘         └─────────────────────────────┘
```

No shared filesystem. Handoff docs + manually transferred files are the ONLY channel.

---

## Mission: VR Dance Concert Cinematographer

### Phase map with gates

| Phase | What | Owner | Gate to proceed | Status |
|---|---|---|---|---|
| **A1** | Mocap → humanoid playback in sim | Training | 30s screen-recording, user visual sign-off | **Done** — stick figure renders via OVRTX |
| **A2** | Hand-coded 2m orbital camera → MP4 | Training | User watches video, says "looks like drone filmed a dancer" | **In progress** — 25s render running |
| **A3** | Cinematography reward function + unit tests | Training | All unit tests pass, reward on A2 baseline is sane | Pending |
| **A4** | PPO training + 10 sample MP4s | Training | 7/10 MP4s beat orbital baseline (user vote), 0 safety violations | Pending |
| **A5** | Bake winning trajectory → GLB + previs MP4 | Training→VR | GLB plays in Gurulok VR, user approves previs as "cinematic enough for hardware" | Pending |
| **A6** | Distill actor → ONNX (<50 MB, <10 ms inference) | Training | Numerical equivalence test passes vs PyTorch policy | Pending |
| **B** | Sim-to-real DR pass (motor dynamics, VIO drift, camera noise) | Training | Re-exported ONNX generalizes across DR conditions | Pending |
| **C** | Real Starling 2 hardware deploy | Hardware ops | Live test on indoor stage | Pending |

**Critical rule: A2, A4, and A5 have SUBJECTIVE approval gates.** The user must explicitly say
"yes" before proceeding. Silence is NOT approval. Do not skip these.

### Delivery artifacts (per training version v<N>)

| Artifact | Format | From | To | Path at destination |
|---|---|---|---|---|
| `trained_cinematographer_v<N>.glb` | glTF 2.0, mesh + `Drone_action` clip (25s, 24fps) | Training | VR | `Assets/_App/DroneJourney/Models/` |
| `previs_cinematographer_v<N>.mp4` | H.264 1080p30, 25s | Training | User | Shared handoff folder |
| `trained_cinematographer_v<N>.onnx` | ONNX feed-forward, <50 MB | Training | Hardware | Starling 2 via VOXL SDK |
| `training_report_v<N>.md` | Markdown | Training | User + VR | NvidiaSimSetup/ repo |

### Mocap data (VR → Training)

Each session folder `mocap_handoff/dance_<UTC>/`:

| File | Format | What |
|---|---|---|
| `meta.json` | JSON | schema 2.0.0, 84 joints, music context |
| `pose.bin` | 3372 B/frame @ 60 Hz | 84 OVRBody joints (pos+quat+vel) |
| `xr_hands.bin` | 2088 B/frame @ 60 Hz | 52 finger joints |
| `aux.bin` | 68 B/frame @ 60 Hz | Eye gaze + body confidence |
| `ready_for_handoff.flag` | empty | Atomic "done" signal |

---

## Generating handoffs

### Training → VR handoff template

Use this EXACT structure when the user says "hand off to VR" or a GLB is ready:

```markdown
# Cinematographer Drone — Training → VR Handoff (v[N])

> [One sentence: what was trained, how it performed, what the VR agent should do]

## Delivered artifacts

| File | Format | Size | Description |
|---|---|---|---|
| `trained_cinematographer_v[N].glb` | glTF 2.0 | [X] MB | Drone mesh + `Drone_action` animation clip (25s @ 24fps) |
| `previs_cinematographer_v[N].mp4` | H.264 1080p30 | [X] MB | Pre-visualization for user approval |
| `training_report_v[N].md` | Markdown | — | Reward curves, sample frame grids, training config |

## What changed since v[N-1]
- [Bullet list]

## Integration instructions (VR Agent)
1. Copy `trained_cinematographer_v[N].glb` to `GurulokInnerJourney/Assets/_App/DroneJourney/Models/`
2. In Unity menu: `TrigunAI → Setup → Cinematographer Scene`
   - Runs `CinematographerSceneSetup.cs` which creates the scene hierarchy
   - Sets import scale 0.005 on the `CityAnchor` wrapper
   - Wires `Animated()` component targeting `Drone_action` clip
3. Enter Play mode → verify drone follows trained cinematic path
4. Build APK: `TrigunAI → Build → Quest APK` (increments build number)
5. Upload: `ovr-platform-util upload-quest-build`

## Coordinate system
- GLB: right-hand Y-up, meters
- Animation origin: dancer pelvis at t=0 (drone motion is dancer-relative)
- `Drone_action` clip: 600 keyframes @ 24fps = 25.00s

## Known issues
- [List anything]

## What I need back
- [ ] VR test video (30s screen recording of the drone in Quest scene)
- [ ] Subjective verdict: "cinematic" / "needs work" / specific feedback
- [ ] Build number after integration
- [ ] If re-training needed: 5+ new mocap sessions for variety

## Files to SCP
```bash
scp trained_cinematographer_v[N].glb user@windows:/path/to/GurulokInnerJourney/Assets/_App/DroneJourney/Models/
scp training_report_v[N].md user@windows:/path/to/handoff/
```
```

### VR → Training handoff template

Use when the user says "hand off to training" or new mocap/feedback is ready:

```markdown
# Cinematographer Drone — VR → Training Handoff

> [One sentence: what was recorded/tested and what the training agent needs to do]

## Mocap sessions delivered

| Session folder | Schema | Duration | Frames | Music | Has aux.bin |
|---|---|---|---|---|---|
| `dance_YYYYMMDD_HHMMSS/` | 2.0.0 | [X]s | [N] | [track] @ [BPM] bpm | yes/no |

## How to pull from Quest
```bash
adb pull /sdcard/Android/data/com.trigunai.gurulokinnerjourney/files/Mocap/ ./mocap_handoff/
```

## VR test feedback (if testing a delivered GLB)
- **Verdict**: [cinematic / needs work / broken]
- **What looked good**: [specific observations]
- **What looked wrong**: [specific observations with timestamps if possible]
- **Build number tested**: [N]

## What I need back
- [ ] Updated policy trained on these sessions
- [ ] Previs MP4 for review before GLB integration
- [ ] Training report with reward curves

## Files to SCP
```bash
scp -r mocap_handoff/dance_*/ user@mac:/path/to/NvidiaSimSetup/mocap_handoff/
```
```

---

## Phase gate evaluation

When the user asks "should we move to phase X" or "is this ready":

### A1 → A2 gate
- [ ] Humanoid plays back from pose.bin — pelvis ~0.7-1.0m, head ~1.2-1.6m
- [ ] No NaN explosions, no T-pose spasms
- [ ] 30s recording delivered to user
- **Verdict**: Check body positions from parser output

### A2 → A3 gate (SUBJECTIVE — requires explicit "yes")
- [ ] Orbital video exists (25s, 30fps)
- [ ] User has WATCHED the video
- [ ] User has EXPLICITLY said "yes, this looks like a drone filming a dancer"
- **If user hasn't responded**: Ask. Do not proceed on silence.

### A3 → A4 gate
- [ ] All reward function unit tests pass
- [ ] Reward computed on A2 orbital baseline is a sane number (not NaN, not pathologically low)
- [ ] Each reward term produces non-zero gradients on test states

### A4 → A5 gate (SUBJECTIVE — requires explicit vote)
- [ ] 10 sample MP4s rendered from 10 held-out sessions
- [ ] User votes: at least 7/10 "more cinematic than orbital baseline"
- [ ] Safety violations in eval = 0 (drone never enters 1.5m zone)
- [ ] Total reward at convergence > orbital baseline reward

### A5 → A6 gate (SUBJECTIVE — cross-team handoff)
- [ ] GLB opens in Blender with `Drone_action` clip, 25.00s ± 0.1s
- [ ] GLB integrated in Gurulok, plays in VR
- [ ] User watches previs MP4 and says "cinematic enough to justify hardware spend"
- **This is the hardware-purchase decision gate**

### A6 → B gate
- [ ] ONNX exists, <50 MB
- [ ] Inference <10 ms on target hardware class
- [ ] Numerical equivalence: mean absolute action diff < 1% per dimension

---

## Coordinate systems (include in EVERY handoff)

| System | Hand | Up | Position transform | Quaternion transform |
|---|---|---|---|---|
| Unity (Gurulok mocap) | Left | Y | identity | (x,y,z,w) |
| USD (OVRTX rendering) | Right | Y | Z-negate: (x,y,-z) | (x,y,-z,w) |
| Isaac Sim (RL training) | Right | Z | Y↔Z swap: (x,z,y) | (x,z,y,w) |
| glTF (delivery) | Right | Y | same as USD | same as USD |

---

## EC2 quick ref (include in training-side handoffs)

```
Instance: TrigunAI-Omniverse (i-047ebf759f2386e71), g5.2xlarge, us-east-1
SSH: ssh -i ~/.ssh/trigunai_key.pem ubuntu@<CURRENT_IP>
OVRTX: localhost:8001 (check gpu_initialized; 6 min cold start)
LiteLLM: localhost:4000 (master key: sk-trigunai-master-key-2026)
isaaclab container: sudo docker start isaaclab (doesn't auto-start)
Blender: /opt/blender45 (symlink: blender45)
PUBLIC IP CHANGES ON EVERY STOP/START — always check AWS console
/tmp IS EPHEMERAL — wiped on EC2 stop, persist to /home/ubuntu/
```
