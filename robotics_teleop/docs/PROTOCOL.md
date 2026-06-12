# Quest → PC Teleop Streaming Protocol v1

**Status:** draft. Used as the contract between the Gurulok Quest app (VR coding agent's repo) and this PC bridge.

---

## Transport

- **WebSocket over TCP**, port `9000` by default (configurable).
- Quest app is the **client**; PC bridge is the **server**.
- Quest connects on user-toggling "Teleop Mode" inside the Gurulok app.
- One Quest → one PC. No multi-headset broadcast yet.
- LAN preferred (5GHz WiFi). Over LTE / cell is out of scope.

**Why WebSocket first (instead of UDP):**
- Trivial debug tooling (browser DevTools can connect to it)
- Reliable delivery handles WiFi flickers without us reimplementing TCP
- Acceptable latency on local 5GHz (~10–30 ms typical)
- Easy JSON parsing in MVP; can switch to binary later if needed

**Latency target:** 50 ms end-to-end from Quest sensor read to PC bridge dispatch. Will benchmark Week 1.

---

## Message rate

- **60 Hz** (16.6 ms per frame), matching Quest's body tracking + OVRBody sample rate.
- Quest sender SHOULD drop frames rather than queue if WebSocket backpressure exceeds 2 frames.
- PC bridge SHOULD log frame drops with a counter (visible in `--visualize` mode).

---

## Message schema (one frame per WebSocket message)

JSON, one object per frame:

```json
{
  "v": 1,
  "t_quest_ns": 1716304012345678901,
  "frame": 12342,
  "tracking_quality": 2,
  "body": {
    "joints": [
      [x, y, z, qx, qy, qz, qw],
      ...  // 84 entries total, in OVRBody joint order (see ../mocap_handoff)
    ],
    "valid": [true, true, ..., false, ...]  // 84 bools — false where Quest reports untracked
  },
  "hands": {
    "left_tracked": true,
    "right_tracked": true,
    "joints": [
      [x, y, z, qx, qy, qz, qw],
      ...  // 52 entries total (26 per hand), in XR Hands joint order
    ]
  },
  "gaze": {
    "left":  {"pos": [x, y, z], "dir": [x, y, z], "conf": 0.97},
    "right": {"pos": [x, y, z], "dir": [x, y, z], "conf": 0.94}
  },
  "props": {
    "active_prop": "None",
    "emitters": []
  }
}
```

### Field details

| Field | Type | Notes |
|---|---|---|
| `v` | int | Protocol version. Bump when schema changes break clients. |
| `t_quest_ns` | int | Quest local timestamp in nanoseconds since epoch. Used for latency measurement on PC side. |
| `frame` | int | Monotonic frame counter from Quest. Allows detection of frame drops. |
| `tracking_quality` | int | `0` none, `1` upper-only, `2` upper + IOBT lower, `3` full hardware-tracked. Mirrors v129 `pose.bin` semantics. |
| `body.joints` | array[84] of `[x,y,z,qx,qy,qz,qw]` | Unity LH Y-up world coords. **PC bridge converts to Isaac RH Z-up internally.** |
| `body.valid` | array[84] of bool | False if Quest reports this joint as untracked (e.g. lower body when `tracking_quality==1`) |
| `hands.joints` | array[52] of `[x,y,z,qx,qy,qz,qw]` | XR Hands joint order: 0–25 left, 26–51 right. NaN positions if not tracked. |
| `hands.left_tracked` / `right_tracked` | bool | If false, all 26 joints for that hand are NaN. |
| `gaze` | obj | Optional. Present only if eye-tracking permission granted on Quest 3. |
| `props` | obj | Reserved for Gurulok prop emitters (poi, web weaver). Not used by robotics teleop in v1. |

### Coordinate conventions

- **Quest side (Unity):** left-hand coord, Y-up, units = meters.
- **PC side (Isaac / Pinocchio / mink):** right-hand coord, Z-up, units = meters.
- Conversion is applied **once on PC side**, immediately after WebSocket recv. Quest sends its native frame; PC normalizes.
  - Position: `(x, y, z)_unity → (x, z, y)_isaac`
  - Quaternion `(qx, qy, qz, qw)` order is preserved by component swap: `(qx, qy, qz, qw) → (qx, qz, qy, qw)` (this is the same convention used in the dance `pose_bin_to_amp_motion_v2.py` converter)

---

## Connection lifecycle

```
Quest                       PC Bridge
  │                            │
  │  WS handshake (port 9000)  │
  ├───────────────────────────►│
  │                            │
  │  {"v":1, "frame":0, ...}   │   ← every 16.6 ms
  ├───────────────────────────►│
  │  {"v":1, "frame":1, ...}   │
  ├───────────────────────────►│
  │            ...             │
  │                            │
  │  user toggles teleop off   │
  │      OR Quest sleeps       │
  │                            │
  │  WS close (normal)         │
  ├───────────────────────────►│
  │                            │
```

PC bridge handles WS close cleanly (flush any in-flight retargeted commands, mark session ended in dataset recorder).

---

## Quest-side responsibilities (for the VR coding agent to implement)

1. Add a **"Teleop Mode"** toggle in the Gurulok app settings.
2. When ON, start a WebSocket client connection to the configured PC IP + port.
3. Every body/hand frame from OVRBody / XR Hands, serialize as JSON and `ws.send()`.
4. On user toggle OFF, close the connection cleanly.
5. Surface latency stats in the Gurulok app UI (round-trip ping every 1 s) so user knows if WiFi is bad.

---

## PC-side responsibilities (this repo)

1. WebSocket server listening on configurable port.
2. Parse incoming JSON, validate schema version, convert coord frame.
3. Maintain a **latest-frame buffer** (not a queue) — consumers always get the freshest frame.
4. Optional `--visualize` mode renders the live skeleton in matplotlib for sanity.
5. Optional `--record` mode appends frames to HDF5 in LeRobot-compatible format.
6. Plug-in interface for downstream consumers: ROS 2 publisher, Isaac Lab subscriber, dataset recorder.

---

## Versioning

- v1 (current): JSON, 60 Hz, body + hands + gaze.
- v2 (future): switch to MessagePack/CBOR for size; add joint velocities; add force feedback uplink.
- v3 (future): bidirectional (PC sends haptic targets back to Quest for feedback during teleop).

---

## Open questions to discuss with VR coding agent

1. **Quest IP discovery.** Hardcoded config, mDNS, or QR code pairing? — v1 hardcoded; v2 mDNS.
2. **Multiple PCs receiving the same Quest stream?** Out of scope v1; one Quest one PC.
3. **Bandwidth.** ~84+52 joints × 7 floats × 4 bytes × 60 Hz ≈ 230 KB/s. Trivial for 5GHz WiFi.
4. **Backpressure.** If PC bridge is slow, Quest drops frames silently — this is correct behavior; teleop must not stall the headset.
