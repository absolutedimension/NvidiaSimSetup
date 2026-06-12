"""Quest → PC teleop WebSocket receiver.

Listens on a configurable port. For each connected Quest, receives one JSON
frame per ~16.6 ms, decodes into the Isaac coord frame via schema.decode_frame,
and exposes the latest frame to downstream consumers (retargeter, recorder).

Run:
    python3 ws_server.py --port 9000 [--visualize] [--latency-stats]

Latency-stats mode prints rolling mean/p95 latency every second. Useful for
tuning WiFi position / channel.

Visualize mode pops up a matplotlib window showing live wrist positions —
quick sanity check that the stream is real.
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import json
import signal
import sys
import time
from typing import Optional

try:
    import websockets  # pip install websockets
except ImportError:
    print("ERROR: install websockets — pip install websockets", file=sys.stderr)
    sys.exit(1)

from schema import FrameIsaac, decode_frame, DEFAULT_PORT


class TeleopBridge:
    """Owns the latest frame + latency stats. Consumers poll .latest()."""

    def __init__(self, latency_window: int = 60):
        self._latest: Optional[FrameIsaac] = None
        self._lat_ms = collections.deque(maxlen=latency_window)
        self._frame_count = 0
        self._last_quest_frame: Optional[int] = None
        self._drops = 0
        self._connected = False

    def ingest(self, frame: FrameIsaac) -> None:
        self._latest = frame
        self._lat_ms.append(frame.latency_ms)
        self._frame_count += 1
        if self._last_quest_frame is not None:
            expected = self._last_quest_frame + 1
            if frame.frame > expected:
                self._drops += frame.frame - expected
        self._last_quest_frame = frame.frame

    def latest(self) -> Optional[FrameIsaac]:
        return self._latest

    def stats(self) -> dict:
        lat = list(self._lat_ms)
        if not lat:
            return {"connected": self._connected, "frames": 0}
        lat_sorted = sorted(lat)
        p95 = lat_sorted[int(0.95 * (len(lat_sorted) - 1))]
        return {
            "connected": self._connected,
            "frames": self._frame_count,
            "drops": self._drops,
            "latency_mean_ms": sum(lat) / len(lat),
            "latency_p95_ms": p95,
            "latency_last_ms": lat[-1],
        }


async def handler(ws, bridge: TeleopBridge):
    bridge._connected = True
    print(f"[ws] Quest connected from {ws.remote_address}")
    try:
        async for raw in ws:
            t_pc_recv_ns = time.time_ns()
            try:
                msg = json.loads(raw)
                frame = decode_frame(msg, t_pc_recv_ns)
            except Exception as e:
                print(f"[ws] decode failed: {e}", file=sys.stderr)
                continue
            bridge.ingest(frame)
    except websockets.ConnectionClosed as e:
        print(f"[ws] Quest disconnected: {e}")
    finally:
        bridge._connected = False


async def stats_printer(bridge: TeleopBridge, interval: float = 1.0):
    while True:
        await asyncio.sleep(interval)
        s = bridge.stats()
        if s.get("frames"):
            print(
                f"[stats] frames={s['frames']}  drops={s.get('drops',0)}  "
                f"lat_mean={s['latency_mean_ms']:.1f}ms  "
                f"lat_p95={s['latency_p95_ms']:.1f}ms  "
                f"lat_now={s['latency_last_ms']:.1f}ms"
            )


async def visualizer(bridge: TeleopBridge, interval: float = 0.05):
    """Live wrist + head position plot. Closes on Ctrl-C."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[viz] matplotlib not installed — skipping visualizer", file=sys.stderr)
        return
    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect("equal")
    ax.set_title("Quest teleop — top-down view\n(Isaac X horizontal, Y vertical)")
    head_dot, = ax.plot([], [], "ko", markersize=10, label="head")
    l_wrist_dot, = ax.plot([], [], "bo", markersize=8, label="L wrist")
    r_wrist_dot, = ax.plot([], [], "ro", markersize=8, label="R wrist")
    ax.legend(loc="upper right")

    # OVRBody joint indices (matches v129 spec & mocap_handoff v2 converter)
    IDX_HEAD = 7
    IDX_L_WRIST = 19
    IDX_R_WRIST = 45

    while True:
        await asyncio.sleep(interval)
        f = bridge.latest()
        if f is None:
            continue
        # Isaac frame: X=right, Y=forward, Z=up. Plot X vs Y (top-down).
        h = f.body_pos[IDX_HEAD]
        lw = f.body_pos[IDX_L_WRIST]
        rw = f.body_pos[IDX_R_WRIST]
        head_dot.set_data([h[0]], [h[1]])
        l_wrist_dot.set_data([lw[0]], [lw[1]])
        r_wrist_dot.set_data([rw[0]], [rw[1]])
        fig.canvas.draw_idle()
        fig.canvas.flush_events()


async def amain(args):
    bridge = TeleopBridge()

    print(f"[ws] listening on ws://0.0.0.0:{args.port}  (waiting for Quest)")
    print(f"     PC IP for Quest config: {get_local_ip()}")

    server = await websockets.serve(
        lambda ws: handler(ws, bridge),
        host="0.0.0.0",
        port=args.port,
        ping_interval=20,
        ping_timeout=10,
        max_size=2**20,  # 1 MB per message — generous
    )

    tasks = [server.wait_closed()]
    if args.latency_stats:
        tasks.append(asyncio.create_task(stats_printer(bridge)))
    if args.visualize:
        tasks.append(asyncio.create_task(visualizer(bridge)))

    await asyncio.gather(*tasks)


def get_local_ip() -> str:
    """Best-effort: find LAN IP for displaying to user."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--visualize", action="store_true",
                    help="Open matplotlib window with live wrist + head positions.")
    ap.add_argument("--latency-stats", action="store_true",
                    help="Print rolling latency stats every second.")
    args = ap.parse_args()

    def stop(*_):
        print("\n[ws] shutting down")
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)

    try:
        asyncio.run(amain(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
