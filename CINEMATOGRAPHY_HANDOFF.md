# Cinematography Drone — Training Pipeline Handoff

> Train an autonomous cinematography drone policy in Isaac Sim that films a human dancer on an indoor stage from compositionally good angles, then deploy to Modal AI Starling 2 hardware (Snapdragon 865, VOXL SDK, onboard ONNX inference).

---

## Mission

A PPO-trained drone policy that produces cinematic footage of a dancing subject. The dancer is driven by real Quest 3 mocap recordings (Gurulok `pose.bin`, 84 joints at 60 Hz). The trained policy ships two ways: (1) baked-to-GLB for VR validation in the Gurulok Quest 3 app (reusing the v139 pipeline), and (2) distilled to ONNX for onboard inference on Modal AI Starling 2.

**This is a fresh pipeline.** Does not extend the prior Crazyflie navigation work.

---

## Phase A — Sim-only proof (current)

| Step | Description | Status |
|---|---|---|
| A1 | Mocap playback — drive humanoid from pose.bin in sim | in progress |
| A2 | Orbital camera baseline — 2 m orbit around pelvis, render 25s MP4 | in progress |
| A3 | Cinematography reward function (framing, smoothness, variety, safety, gaze, beat) | pending |
| A4 | Train PPO with 6-DOF velocity actions | pending |
| A5 | Export trained trajectory to GLB for VR validation | pending |
| A6 | Distill to ONNX for Starling 2 | pending |

## Phase B — Sim-to-real prep (domain randomization, motor dynamics, VIO noise)

## Phase C — Real hardware deployment (only after A5 video passes user review)

---

## Canonical mocap session

Working canonical: `mocap_handoff/Mocap/dance_20260519_213931/`
- Schema 2.0.0 (84 joints)
- 110.8 s / 3984 frames @ 60 Hz
- Has `aux.bin` (eye gaze) + `xr_hands.bin` (finger tracking)
- Music: cosmic-hypnotic, BPM 110

---

## Key files

| File | Purpose |
|---|---|
| `cinematography/parse_pose_bin.py` | Reads pose.bin + aux.bin, returns joint arrays in Unity or Isaac coords |
| `cinematography/bake_dancer_usda.py` | Bakes dancer body prims + orbital camera to animated USDA |
| `cinematography/render_dancer_mp4.py` | Renders USDA via OVRTX to MP4 (reuses render_drone_demo.py patterns) |
| `cinematography/README.md` | Ongoing technical notes |

---

## Infrastructure reused (do NOT duplicate)

- OVRTX renderer on EC2 port 8001
- `isaaclab` container (Isaac Sim 6.0.0-rc.22 + Isaac Lab 3.0)
- Blender 4.5 LTS at `/opt/blender45`
- LiteLLM proxy on port 4000 (for VLM critic, later)
- v139 GLB bake pipeline for VR validation

---

## Coordinate systems

- **Gurulok mocap (Unity):** left-hand, Y-up. Quaternions `(qx, qy, qz, qw)`.
- **Isaac Sim / USD:** right-hand, Z-up. Transform: `pos (x,y,z) → (x,z,y)`, `quat (qx,qy,qz,qw) → (qx,qz,qy,qw)`.
- **USD for OVRTX rendering:** Y-up by convention. Positions stay in Unity frame for USDA baking (Y-up is native USD).

---

*Created: 2026-05-24. Owner: TrigunAI Innovations.*
