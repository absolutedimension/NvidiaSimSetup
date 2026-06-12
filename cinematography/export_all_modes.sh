#!/usr/bin/env bash
# Export 6 mode trajectories + render 6 drone-POV videos
# Run on EC2 host (not in container)
set -euo pipefail

CKPT="/workspace/isaaclab/cinematographer_v4_modes_best.pth"
EXPORT_SCRIPT="/workspace/isaaclab/export_cinematographer_trajectory.py"
STEPS=500        # 500 steps @ 50Hz = 10 seconds
FPS=50           # sim FPS (export fps)
RENDER_FPS=30    # output video fps
TASK="Isaac-Cinematographer-Direct-v4"
OUT_DIR="/home/ubuntu/mode_videos"
DANCER_USDA="/home/ubuntu/dancer_orbital_25s_v2.usda"
RENDER_SCRIPT="/home/ubuntu/render_blender_drone_pov.py"

MODES=("HERO" "INTIMATE" "EPIC" "ENERGY" "SOLITUDE" "BEAUTY")

mkdir -p "$OUT_DIR"

echo "=== Exporting 6 mode trajectories ==="
for MODE in "${MODES[@]}"; do
    echo ""
    echo "--- Mode: $MODE ---"
    OUT_JSON="/tmp/traj_${MODE}.json"

    # Skip if already exported
    if [ -f "$OUT_JSON" ] && [ -s "$OUT_JSON" ]; then
        echo "  Already exported: $OUT_JSON ($(wc -c < "$OUT_JSON") bytes)"
        continue
    fi

    sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && \
        ./isaaclab.sh -p $EXPORT_SCRIPT \
            --checkpoint $CKPT \
            --task $TASK \
            --mode-schedule '0:$MODE' \
            --steps $STEPS --fps $FPS \
            --out /workspace/isaaclab/traj_${MODE}.json \
            --headless" 2>&1 | tail -5

    # Copy out of container
    sudo docker cp "isaaclab:/workspace/isaaclab/traj_${MODE}.json" "$OUT_JSON"
    echo "  Exported: $OUT_JSON ($(wc -c < "$OUT_JSON") bytes)"
done

echo ""
echo "=== Converting trajectories to render format ==="
# Convert each trajectory from Isaac Z-up to USD Y-up render format
python3 -u - << 'PYEOF'
import json, os, sys

MODES = ["HERO", "INTIMATE", "EPIC", "ENERGY", "SOLITUDE", "BEAUTY"]
OUT_DIR = "/home/ubuntu/mode_videos"
RENDER_FPS = 30
SIM_FPS = 50

for mode in MODES:
    src = f"/tmp/traj_{mode}.json"
    dst = f"{OUT_DIR}/traj_{mode}_render.json"

    if os.path.exists(dst) and os.path.getsize(dst) > 100:
        print(f"  {mode}: already converted ({os.path.getsize(dst)} bytes)")
        continue

    if not os.path.exists(src):
        print(f"  {mode}: MISSING source {src}")
        continue

    with open(src) as f:
        data = json.load(f)

    frames = data["frames"]
    sim_fps = data.get("fps", SIM_FPS)

    # Subsample from sim_fps to render_fps
    step = max(1, round(sim_fps / RENDER_FPS))

    render_frames = []
    for idx, fr in enumerate(frames):
        if idx % step != 0:
            continue

        # Isaac Sim Z-up → USD Y-up
        # Position: (x, y, z) → (x, z, -y)
        dp = fr["drone_pos"]
        x_usd = dp[0]
        y_usd = dp[2]   # Isaac Z → USD Y
        z_usd = -dp[1]  # Isaac Y → USD -Z

        # Quaternion: (qw, qx, qy, qz)_isaac → (qx, qz, -qy, qw)_render
        dq = fr["drone_quat"]  # [qw, qx, qy, qz] from rl_games
        qw, qx, qy, qz = dq[0], dq[1], dq[2], dq[3]
        # Remap to USD Y-up
        qx_usd = qx
        qy_usd = qz
        qz_usd = -qy
        qw_usd = qw

        render_frames.append({
            "i": len(render_frames),
            "t": [x_usd, y_usd, z_usd],
            "q": [qx_usd, qy_usd, qz_usd, qw_usd],
        })

    out = {"frames": render_frames, "fps": RENDER_FPS}
    with open(dst, "w") as f:
        json.dump(out, f)

    print(f"  {mode}: {len(frames)} sim frames → {len(render_frames)} render frames → {dst}")

PYEOF

echo ""
echo "=== Rendering 6 drone-POV videos with Blender EEVEE ==="
for MODE in "${MODES[@]}"; do
    echo ""
    echo "--- Rendering: $MODE ---"
    TRAJ="$OUT_DIR/traj_${MODE}_render.json"
    MP4="$OUT_DIR/${MODE}_drone_pov.mp4"
    FRAMES_DIR="$OUT_DIR/frames_${MODE}"

    if [ -f "$MP4" ] && [ -s "$MP4" ]; then
        echo "  Already rendered: $MP4 ($(du -h "$MP4" | cut -f1))"
        continue
    fi

    if [ ! -f "$TRAJ" ]; then
        echo "  MISSING trajectory: $TRAJ — skipping"
        continue
    fi

    rm -rf "$FRAMES_DIR"

    PYTHONUNBUFFERED=1 blender45 --background --python "$RENDER_SCRIPT" -- \
        --dancer "$DANCER_USDA" \
        --trajectory "$TRAJ" \
        --out "$MP4" \
        --engine eevee \
        --width 1280 --height 720 \
        --fps "$RENDER_FPS" 2>&1 | grep -E "^(===|Render|Done|Encoding|frames|Importing|Dancer|Camera|Using|EEVEE)" || true

    if [ -f "$MP4" ]; then
        echo "  Done: $MP4 ($(du -h "$MP4" | cut -f1))"
    else
        echo "  FAILED to render $MODE"
    fi
done

echo ""
echo "=== Summary ==="
ls -lh "$OUT_DIR"/*.mp4 2>/dev/null || echo "No videos produced"
echo ""
echo "All 6 mode videos at: $OUT_DIR/"
