# robotics_teleop — Quest 3 → Robot Teleoperation SDK

**Status:** Active, started 2026-05-21. Read `../ROBOTICS_CLAUDE.md` for the full strategy + roadmap.

This is the **new layer above** the existing Gurulok mocap, Isaac Lab, and AMP work. It bridges Quest VR motion capture into the robotics ML training stack used by humanoid + manipulation labs.

---

## Directory layout

```
robotics_teleop/
├── quest_bridge/        # PC-side receiver for Quest motion stream
│   ├── ws_server.py     # WebSocket receiver
│   ├── schema.py        # Frame schema (84 body + 52 finger + eye gaze)
│   └── viz_live.py      # Real-time matplotlib visualization for sanity check
├── robot_targets/       # URDF-aware retargeting per robot
│   ├── unitree_g1/      # Primary target (Week 2-4)
│   │   ├── urdf/        # URDF + meshes from Unitree's public release
│   │   ├── retarget.py  # Quest skeleton → G1 23-joint commands
│   │   └── fk_check.py  # Forward kinematics sanity test
│   ├── franka_fr3/      # Manipulation arm (later)
│   └── inspire_hand/    # Dex-hand variant
├── datasets/            # LeRobot-compatible recording / playback
│   ├── recorder.py      # Captures episodes to HDF5
│   └── lerobot_export.py
└── docs/
    └── PROTOCOL.md      # WebSocket schema spec for Quest senders
```

---

## Why this is separate from `mocap_handoff/`

`mocap_handoff/` is the data plumbing for the **dance** workstream (paused). Files there:
- `pose_bin_to_amp_motion_v2.py` — Quest binary → AMP-shaped npz (dance training)
- `bake_daphne_animation.py` — npz → animated GLB (dance visualization)
- `add_music_features_to_npz.py` — music-feature augmentation (Phase 3)

The robotics teleop work has **different output targets** (ROS 2 messages, URDFs, LeRobot HDF5) and **different timing requirements** (real-time interactive vs. batch). Kept in a separate directory so neither workstream pollutes the other.

What we **will** reuse: pose binary format knowledge, coord-frame transforms (Unity → Isaac), IK design ideas. But not the actual file targets.

---

## Quick start (once Week 1 is done)

```bash
# 1. Start Quest motion sender (in Gurulok app, "Teleop Mode" toggle)
# 2. Start PC bridge
python3 quest_bridge/ws_server.py --port 9000 --visualize

# 3. (Future) start retargeter to specific robot
python3 robot_targets/unitree_g1/retarget.py \
  --stream tcp://localhost:9000 \
  --output ros2

# 4. (Future) Isaac Lab consumer
ssh ec2 'sudo docker exec isaaclab bash -lc \
  "./isaaclab.sh -p teleop_g1_subscribe.py --listen ros2"'
```

---

## Acceptance criteria for each milestone

See `../ROBOTICS_CLAUDE.md §5` for the 6-week MVP schedule with acceptance criteria.

**Week 1 (current):** WebSocket server receives 60 Hz motion from Quest with <50ms latency. Latency proven via timestamp delta. Live wrist position plotted in real time.
