"""Fake-Quest WebSocket client — simulates a Quest sending the teleop stream.

Used to test the PC bridge before the VR coding agent ships the Quest-side
implementation. Generates a synthetic "human waving" motion at 60 Hz.

Run:
    python3 fake_quest_sender.py --host localhost --port 9000
"""
import argparse
import asyncio
import json
import math
import time

try:
    import websockets
except ImportError:
    raise SystemExit("install websockets — pip install websockets")


def synth_frame(frame_idx: int) -> dict:
    """Generate one synthetic Quest frame. Returns dict matching PROTOCOL.md v1."""
    t = frame_idx / 60.0  # seconds since start

    # Simple "human waving" — body upright, right hand sweeping side-to-side
    body_joints = []
    for i in range(84):
        # Rough Y-up Unity positions (meters) — make a stick figure
        if i == 0:    base = [0, 0, 0]            # Root
        elif i == 1:  base = [0, 1.0, 0]          # Hips
        elif i == 7:  base = [0, 1.6, 0]          # Head
        elif i == 19: base = [0.3, 1.4, 0]        # L_Wrist (static)
        elif i == 45:
            # R_Wrist — waving in X direction
            base = [-0.3 + 0.3 * math.sin(t * 2 * math.pi), 1.4 + 0.2 * math.cos(t * 2 * math.pi), 0]
        else:
            base = [0, 1.0, 0]                    # everything else stacked at hip
        body_joints.append([*base, 0.0, 0.0, 0.0, 1.0])  # identity quat

    body_valid = [True] * 70 + [False] * 14   # lower body untracked (matches upper-only Quest mode)

    # Hands — 26 joints each
    hand_joints = []
    for hand_origin_idx in (19, 45):  # left, right wrists
        wrist = body_joints[hand_origin_idx][:3]
        for k in range(26):
            # Just splay fingers out from wrist
            angle = k * 0.2
            base = [wrist[0] + 0.05 * math.cos(angle),
                    wrist[1],
                    wrist[2] + 0.05 * math.sin(angle)]
            hand_joints.append([*base, 0.0, 0.0, 0.0, 1.0])

    return {
        "v": 1,
        "t_quest_ns": time.time_ns(),
        "frame": frame_idx,
        "tracking_quality": 1,
        "body": {"joints": body_joints, "valid": body_valid},
        "hands": {
            "joints": hand_joints,
            "left_tracked": True,
            "right_tracked": True,
        },
        # no gaze, no props
    }


async def run(host: str, port: int, fps: int, duration_s: float):
    uri = f"ws://{host}:{port}"
    print(f"[fake-quest] connecting to {uri}")
    async with websockets.connect(uri) as ws:
        print(f"[fake-quest] connected, streaming synthetic data @ {fps} Hz")
        period = 1.0 / fps
        t_start = time.monotonic()
        frame_idx = 0
        next_send = time.monotonic()
        while True:
            if duration_s > 0 and (time.monotonic() - t_start) > duration_s:
                break
            msg = synth_frame(frame_idx)
            await ws.send(json.dumps(msg))
            frame_idx += 1
            next_send += period
            sleep = next_send - time.monotonic()
            if sleep > 0:
                await asyncio.sleep(sleep)
            else:
                next_send = time.monotonic()
            if frame_idx % 60 == 0:
                print(f"[fake-quest] sent {frame_idx} frames")
        print(f"[fake-quest] done, sent {frame_idx} frames")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--duration", type=float, default=0.0,
                    help="Seconds to run (0 = forever)")
    args = ap.parse_args()
    try:
        asyncio.run(run(args.host, args.port, args.fps, args.duration))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
