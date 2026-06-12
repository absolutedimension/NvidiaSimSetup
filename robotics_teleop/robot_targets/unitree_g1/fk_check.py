"""Unitree G1 URDF: parse, forward kinematics, top-down visualization sanity check.

Week-2 acceptance criterion (from ROBOTICS_CLAUDE.md §5):
  "Given a joint state vector, compute end-effector positions; visualize in
   matplotlib." No teleop yet — just static FK validation.

Run:
    /usr/bin/python3 fk_check.py
    /usr/bin/python3 fk_check.py --urdf .../g1_23dof.urdf --no-show

Outputs:
    /tmp/g1_fk_rest.png   — front + top views of G1 in rest pose
    /tmp/g1_fk_arms_up.png — same with arms raised
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

import yourdfpy

# Default URDF — relative to this file. Repo was cloned as a sibling of
# unitree_g1/ inside robot_targets/.
HERE = Path(__file__).resolve().parent
DEFAULT_URDF = HERE.parent / "unitree_ros/robots/g1_description/g1_23dof.urdf"


def load_g1(urdf_path: Path) -> yourdfpy.URDF:
    if not urdf_path.exists():
        raise SystemExit(f"URDF not found: {urdf_path}")
    # build_scene_graph=False because we don't need meshes here, only kinematics
    # build_collision_scene_graph=False same
    # mesh_dir hint to find STL files relative to URDF
    # We can disable mesh loading entirely for speed
    urdf = yourdfpy.URDF.load(
        str(urdf_path),
        build_scene_graph=True,   # needed for urdf.get_transform()
        build_collision_scene_graph=False,
        load_meshes=False,
        load_collision_meshes=False,
    )
    return urdf


def summarize(urdf: yourdfpy.URDF) -> None:
    actuated = [j.name for j in urdf.robot.joints if j.type != "fixed"]
    print(f"[g1] base link:     {urdf.base_link}")
    print(f"[g1] total links:   {len(urdf.link_map)}")
    print(f"[g1] total joints:  {len(urdf.robot.joints)}")
    print(f"[g1] actuated DoF:  {len(actuated)}")
    print(f"[g1] actuated joint names:")
    for i, n in enumerate(actuated):
        print(f"     [{i:2d}]  {n}")


def fk_all_link_positions(urdf: yourdfpy.URDF, q: dict) -> dict:
    """Compute world-frame position of every link given joint angles dict."""
    urdf.update_cfg(q)
    out = {}
    for link_name in urdf.link_map:
        T = urdf.get_transform(link_name)   # 4x4 world transform
        out[link_name] = T[:3, 3].copy()
    return out


def make_rest_pose(urdf: yourdfpy.URDF) -> dict:
    return {j.name: 0.0 for j in urdf.robot.joints if j.type != "fixed"}


def make_arms_up_pose(urdf: yourdfpy.URDF) -> dict:
    q = make_rest_pose(urdf)
    # G1 23-DOF shoulder joints — names vary; we set anything containing
    # "shoulder_pitch" to lift the arms forward + slightly up
    for name in list(q.keys()):
        n = name.lower()
        if "shoulder_pitch" in n:
            q[name] = -1.2     # arms swing forward-up
        elif "shoulder_roll" in n:
            q[name] = 0.0
        elif "elbow" in n:
            q[name] = 0.3
    return q


def plot_pose(urdf: yourdfpy.URDF, q: dict, title: str, out_path: str, show: bool) -> None:
    import matplotlib.pyplot as plt

    pts = fk_all_link_positions(urdf, q)
    P = np.array(list(pts.values()))  # (N, 3) XYZ

    # Build bone segments from URDF's parent→child link relationships
    bones = []
    for joint in urdf.robot.joints:
        if joint.parent in pts and joint.child in pts:
            bones.append((pts[joint.parent], pts[joint.child]))

    fig, axes = plt.subplots(1, 2, figsize=(11, 6))
    fig.suptitle(title)

    # FRONT view: X (right) vs Z (up)
    ax = axes[0]
    ax.set_aspect("equal")
    ax.set_xlabel("X (m, right)")
    ax.set_ylabel("Z (m, up)")
    ax.set_title("front view")
    for p0, p1 in bones:
        ax.plot([p0[0], p1[0]], [p0[2], p1[2]], "k-", linewidth=1.2)
    ax.scatter(P[:, 0], P[:, 2], c="b", s=10, zorder=3)
    ax.grid(True, alpha=0.3)

    # TOP view: X vs Y
    ax = axes[1]
    ax.set_aspect("equal")
    ax.set_xlabel("X (m, right)")
    ax.set_ylabel("Y (m, forward)")
    ax.set_title("top view")
    for p0, p1 in bones:
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], "k-", linewidth=1.2)
    ax.scatter(P[:, 0], P[:, 1], c="b", s=10, zorder=3)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    print(f"[g1] saved {out_path}")
    if show:
        plt.show()
    plt.close(fig)


def report_key_links(urdf: yourdfpy.URDF, q: dict, label: str) -> None:
    pts = fk_all_link_positions(urdf, q)
    interesting = []
    for name in pts:
        low = name.lower()
        if any(k in low for k in ["pelvis", "torso", "head",
                                   "left_wrist", "right_wrist",
                                   "left_ankle", "right_ankle",
                                   "left_elbow", "right_elbow"]):
            interesting.append(name)
    if interesting:
        print(f"\n[g1] key link positions ({label}):")
        for name in sorted(interesting):
            p = pts[name]
            print(f"     {name:35s}  ({p[0]:+.3f}, {p[1]:+.3f}, {p[2]:+.3f}) m")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default=str(DEFAULT_URDF))
    ap.add_argument("--no-show", action="store_true",
                    help="Don't pop matplotlib windows; just save PNGs.")
    args = ap.parse_args()

    print(f"[g1] loading URDF: {args.urdf}")
    urdf = load_g1(Path(args.urdf))
    summarize(urdf)

    # Rest pose
    q_rest = make_rest_pose(urdf)
    plot_pose(urdf, q_rest, "G1 — rest pose", "/tmp/g1_fk_rest.png", show=not args.no_show)
    report_key_links(urdf, q_rest, "rest")

    # Arms-up pose — proves FK actually responds to joint changes
    q_arms_up = make_arms_up_pose(urdf)
    plot_pose(urdf, q_arms_up, "G1 — arms up", "/tmp/g1_fk_arms_up.png", show=not args.no_show)
    report_key_links(urdf, q_arms_up, "arms_up")

    # Sanity check: wrist Z should be HIGHER in arms-up than rest
    rest_pts = fk_all_link_positions(urdf, q_rest)
    up_pts   = fk_all_link_positions(urdf, q_arms_up)
    candidates = [n for n in rest_pts if "wrist" in n.lower() or "hand" in n.lower()]
    if candidates:
        wrist = candidates[0]
        dz = up_pts[wrist][2] - rest_pts[wrist][2]
        forward = up_pts[wrist][1] - rest_pts[wrist][1]
        print(f"\n[g1] FK sanity: {wrist} moved Δz={dz:+.3f}m, Δy={forward:+.3f}m between rest and arms-up")
        if abs(dz) < 0.001 and abs(forward) < 0.001:
            print("     ⚠ unexpected: joint changes didn't move wrist — check joint name patterns in make_arms_up_pose()")
        else:
            print("     ✓ FK responds to joint commands")


if __name__ == "__main__":
    main()
