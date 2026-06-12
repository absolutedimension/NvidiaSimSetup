#!/usr/bin/env python3
"""
test_rewards.py — Unit tests for cinematography reward function.

A3 gate requirement: all tests pass + reward on A2 baseline is sane.

Run:
    cd cinematography && python3 -m pytest test_rewards.py -v
    # or without pytest:
    python3 test_rewards.py
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from rewards import (
    CinematographyRewardCfg,
    classify_shot_type,
    compute_azimuth_elevation,
    compute_total_reward,
    compute_vertical_coverage,
    reward_distance,
    reward_framing,
    reward_height_variety,
    reward_look_at,
    reward_safety,
    reward_shot_type_diversity,
    reward_smoothness,
    reward_variety,
    score_orbital_baseline,
)


class TestRewardFraming(unittest.TestCase):
    """Framing reward: dancer should be centered in camera view."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_perfect_framing(self):
        """Camera pointing directly at dancer → reward ~1.0."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[0.0, 0.0, -1.0]])  # pointing at dancer
        r = reward_framing(drone, dancer, forward, self.cfg)
        self.assertGreater(float(r[0]), 0.95)

    def test_looking_away(self):
        """Camera pointing opposite direction → reward near 0."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[0.0, 0.0, 1.0]])  # pointing away
        r = reward_framing(drone, dancer, forward, self.cfg)
        self.assertLess(float(r[0]), 0.1)

    def test_slight_offset(self):
        """15° offset → reward ~0.24 (at tolerance boundary)."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        # 15° offset in X
        angle = math.radians(15)
        forward = np.array([[math.sin(angle), 0.0, -math.cos(angle)]])
        r = reward_framing(drone, dancer, forward, self.cfg)
        self.assertGreater(float(r[0]), 0.15)
        self.assertLess(float(r[0]), 0.40)

    def test_nonzero_gradient(self):
        """Reward changes with small angular perturbation (non-zero gradient)."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        fwd1 = np.array([[0.0, 0.0, -1.0]])
        fwd2 = np.array([[0.05, 0.0, -1.0]])
        r1 = float(reward_framing(drone, dancer, fwd1, self.cfg)[0])
        r2 = float(reward_framing(drone, dancer, fwd2, self.cfg)[0])
        self.assertNotAlmostEqual(r1, r2, places=3)


class TestRewardDistance(unittest.TestCase):
    """Distance reward: stay in the 2-4m sweet spot."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_ideal_distance(self):
        """At exactly ideal distance → reward ~1.0."""
        drone = np.array([[0.0, 1.0, self.cfg.dist_ideal_m]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_distance(drone, dancer, self.cfg)
        self.assertGreater(float(r[0]), 0.95)

    def test_too_close(self):
        """At 1m (inside safety) → reward low."""
        drone = np.array([[0.0, 1.0, 1.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_distance(drone, dancer, self.cfg)
        self.assertLess(float(r[0]), 0.5)

    def test_too_far(self):
        """At 10m → reward low."""
        drone = np.array([[0.0, 1.0, 10.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_distance(drone, dancer, self.cfg)
        self.assertLess(float(r[0]), 0.3)

    def test_symmetric(self):
        """Reward should be same at ideal+1m and ideal-1m."""
        d_over = np.array([[0.0, 1.0, self.cfg.dist_ideal_m + 1.0]])
        d_under = np.array([[0.0, 1.0, self.cfg.dist_ideal_m - 1.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r_over = float(reward_distance(d_over, dancer, self.cfg)[0])
        r_under = float(reward_distance(d_under, dancer, self.cfg)[0])
        self.assertAlmostEqual(r_over, r_under, places=2)


class TestRewardSmoothness(unittest.TestCase):
    """Smoothness reward: penalize jerk."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_zero_jerk(self):
        """Constant acceleration → zero jerk → reward ~1.0."""
        accel = np.array([[0.1, 0.0, 0.0]])
        r = reward_smoothness(accel, accel, dt=1/30, cfg=self.cfg)
        self.assertGreater(float(r[0]), 0.95)

    def test_high_jerk(self):
        """Sudden large acceleration change → low reward."""
        a1 = np.array([[0.0, 0.0, 0.0]])
        a2 = np.array([[20.0, 20.0, 20.0]])
        r = reward_smoothness(a2, a1, dt=1/30, cfg=self.cfg)
        self.assertLess(float(r[0]), 0.1)

    def test_nonzero_gradient(self):
        """Small jerk difference produces different rewards."""
        a0 = np.array([[0.0, 0.0, 0.0]])
        a1 = np.array([[0.01, 0.0, 0.0]])
        a2 = np.array([[0.1, 0.0, 0.0]])
        r1 = float(reward_smoothness(a1, a0, dt=1/30, cfg=self.cfg)[0])
        r2 = float(reward_smoothness(a2, a0, dt=1/30, cfg=self.cfg)[0])
        self.assertGreater(r1, r2)


class TestRewardSafety(unittest.TestCase):
    """Safety: hard penalty inside exclusion zone."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_outside_safe(self):
        """At 3m → no penalty."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_safety(drone, dancer, self.cfg)
        self.assertEqual(float(r[0]), 0.0)

    def test_inside_penalty(self):
        """At 1m → full penalty."""
        drone = np.array([[0.0, 1.0, 1.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_safety(drone, dancer, self.cfg)
        self.assertLess(float(r[0]), 0.0)
        self.assertAlmostEqual(float(r[0]), self.cfg.safety_penalty)

    def test_on_boundary(self):
        """At exactly 1.5m → no penalty (boundary is exclusive)."""
        drone = np.array([[0.0, 1.0, 1.5]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        r = reward_safety(drone, dancer, self.cfg)
        self.assertEqual(float(r[0]), 0.0)


class TestRewardVariety(unittest.TestCase):
    """Shot variety: reward diverse azimuth angles."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_full_orbit_high_variety(self):
        """360° orbit → high variety reward."""
        angles = np.linspace(0, 2 * math.pi, 150)[None, :]
        r = reward_variety(angles, self.cfg)
        self.assertGreater(float(r[0]), 0.7)

    def test_static_no_variety(self):
        """Fixed angle → zero variety."""
        angles = np.full((1, 150), 0.5)
        r = reward_variety(angles, self.cfg)
        self.assertLess(float(r[0]), 0.05)

    def test_partial_orbit(self):
        """90° sweep → moderate variety."""
        angles = np.linspace(0, math.pi / 2, 150)[None, :]
        r = reward_variety(angles, self.cfg)
        self.assertGreater(float(r[0]), 0.2)
        self.assertLess(float(r[0]), 0.9)


class TestRewardHeightVariety(unittest.TestCase):
    """Height variety: reward mixing low/eye/high shots."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_varied_heights(self):
        """Range from -20° to +45° → high reward."""
        elevations = np.linspace(
            math.radians(-20), math.radians(45), 150
        )[None, :]
        r = reward_height_variety(elevations, self.cfg)
        self.assertGreater(float(r[0]), 0.9)

    def test_flat_height(self):
        """All at same elevation → zero reward."""
        elevations = np.full((1, 150), math.radians(10))
        r = reward_height_variety(elevations, self.cfg)
        self.assertLess(float(r[0]), 0.05)


class TestRewardLookAt(unittest.TestCase):
    """Look-at: camera yaw should track dancer horizontally."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_looking_at_dancer(self):
        """Camera forward aimed at dancer → high reward."""
        drone = np.array([[3.0, 1.5, 0.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[-1.0, -0.1, 0.0]])
        r = reward_look_at(drone, dancer, forward, self.cfg)
        self.assertGreater(float(r[0]), 0.85)

    def test_looking_perpendicular(self):
        """Camera forward perpendicular to dancer → low reward."""
        drone = np.array([[3.0, 1.5, 0.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[0.0, 0.0, 1.0]])  # perpendicular
        r = reward_look_at(drone, dancer, forward, self.cfg)
        self.assertLess(float(r[0]), 0.15)


class TestComputeAzimuthElevation(unittest.TestCase):
    """Utility: azimuth + elevation computation."""

    def test_drone_on_positive_z(self):
        """Drone at +Z from dancer → azimuth ~0."""
        drone = np.array([[0.0, 1.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        az, el = compute_azimuth_elevation(drone, dancer)
        self.assertAlmostEqual(float(az[0]), 0.0, places=2)

    def test_drone_above(self):
        """Drone above dancer → positive elevation."""
        drone = np.array([[0.0, 3.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        az, el = compute_azimuth_elevation(drone, dancer)
        self.assertGreater(float(el[0]), 0.0)

    def test_drone_below(self):
        """Drone below dancer → negative elevation."""
        drone = np.array([[0.0, 0.0, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        _, el = compute_azimuth_elevation(drone, dancer)
        self.assertLess(float(el[0]), 0.0)


class TestShotTypeDiversity(unittest.TestCase):
    """Shot type diversity: reward mixing full/half/close-up shots."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_vertical_coverage_at_3m(self):
        """At 3m with 35mm lens → coverage ≈ 2m (full body)."""
        coverage = compute_vertical_coverage(np.array([3.0]), self.cfg)
        self.assertGreater(float(coverage[0]), 1.5)
        self.assertLess(float(coverage[0]), 2.5)

    def test_vertical_coverage_at_2m(self):
        """At 2m → coverage ≈ 1.4m (half body / waist up)."""
        coverage = compute_vertical_coverage(np.array([2.0]), self.cfg)
        self.assertGreater(float(coverage[0]), 1.0)
        self.assertLess(float(coverage[0]), 1.6)

    def test_classify_full_body(self):
        """Distance 3.5m → full body shot (type 2)."""
        shot = classify_shot_type(np.array([3.5]), self.cfg)
        self.assertEqual(float(shot[0]), 2.0)

    def test_classify_half_body(self):
        """Distance 2.0m → half body shot (type 1)."""
        shot = classify_shot_type(np.array([2.0]), self.cfg)
        self.assertEqual(float(shot[0]), 1.0)

    def test_mixed_shots_high_diversity(self):
        """Window with both full body (4m) and half body (2m) → high reward."""
        # Alternate between 2m and 4m every 30 frames
        dist_hist = np.zeros((1, 150))
        for i in range(150):
            dist_hist[0, i] = 2.0 if (i // 30) % 2 == 0 else 4.0
        r = reward_shot_type_diversity(dist_hist, self.cfg)
        self.assertGreater(float(r[0]), 0.5)

    def test_fixed_distance_low_diversity(self):
        """Always at same distance → only one shot type → low reward."""
        dist_hist = np.full((1, 150), 3.0)
        r = reward_shot_type_diversity(dist_hist, self.cfg)
        self.assertLess(float(r[0]), 0.25)

    def test_all_three_types(self):
        """Window with close + half + full → highest reward."""
        dist_hist = np.zeros((1, 150))
        dist_hist[0, :50] = 1.0    # close-up (coverage < 0.8m)
        dist_hist[0, 50:100] = 2.0  # half body
        dist_hist[0, 100:] = 4.0    # full body
        r = reward_shot_type_diversity(dist_hist, self.cfg)
        self.assertGreater(float(r[0]), 0.7)


class TestCompositeReward(unittest.TestCase):
    """Total reward: weighted sum is sane."""

    def setUp(self):
        self.cfg = CinematographyRewardCfg()

    def test_ideal_state(self):
        """Perfect position + framing → total reward > 0.5."""
        drone = np.array([[0.0, 1.3, 3.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[0.0, -0.1, -1.0]])
        accel = np.array([[0.0, 0.0, 0.0]])
        az_hist = np.linspace(0, 2 * math.pi, 150)[None, :]
        el_hist = np.linspace(-0.3, 0.7, 150)[None, :]
        dist_hist = np.linspace(2.0, 4.0, 150)[None, :]  # varies full→half body

        total, comps = compute_total_reward(
            drone, dancer, forward, accel, accel,
            az_hist, el_hist, dist_hist, dt=1/30, cfg=self.cfg,
        )
        self.assertGreater(float(total[0]), 0.5)
        for k, v in comps.items():
            if k != "safety":
                self.assertGreater(float(v[0]), 0.0,
                                   f"{k} should produce positive reward")

    def test_terrible_state(self):
        """Inside safety zone + looking away → total reward very negative."""
        drone = np.array([[0.0, 1.0, 0.5]])  # inside 1.5m zone
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[0.0, 0.0, 1.0]])  # looking away
        accel = np.array([[10.0, 10.0, 10.0]])
        prev_accel = np.array([[0.0, 0.0, 0.0]])
        az_hist = np.full((1, 150), 0.5)
        el_hist = np.full((1, 150), 0.1)
        dist_hist = np.full((1, 150), 0.5)

        total, comps = compute_total_reward(
            drone, dancer, forward, accel, prev_accel,
            az_hist, el_hist, dist_hist, dt=1/30, cfg=self.cfg,
        )
        self.assertLess(float(total[0]), 0.0)

    def test_not_nan(self):
        """No NaN in any reward component."""
        drone = np.array([[2.0, 1.5, 2.0]])
        dancer = np.array([[0.0, 1.0, 0.0]])
        forward = np.array([[-0.5, -0.1, -0.5]])
        accel = np.array([[0.1, 0.05, -0.1]])
        prev_accel = np.array([[0.08, 0.04, -0.09]])
        az_hist = np.linspace(0, 1, 50)[None, :]
        el_hist = np.linspace(0, 0.5, 50)[None, :]
        dist_hist = np.linspace(2.5, 3.5, 50)[None, :]

        total, comps = compute_total_reward(
            drone, dancer, forward, accel, prev_accel,
            az_hist, el_hist, dist_hist, dt=1/30, cfg=self.cfg,
        )
        self.assertFalse(np.isnan(float(total[0])))
        for k, v in comps.items():
            self.assertFalse(np.isnan(float(v[0])), f"{k} is NaN")


class TestOrbitalBaseline(unittest.TestCase):
    """Score the A2 orbital trajectory against the reward function."""

    def test_baseline_is_sane(self):
        """Orbital baseline should produce a positive, non-NaN total reward."""
        # Simulate a dancer standing roughly still for 5 seconds
        T = 150  # 5s at 30fps
        dancer_pos = np.zeros((T, 3))
        dancer_pos[:, 1] = 1.0  # chest at Y=1m
        # Add slight sway
        dancer_pos[:, 0] = 0.1 * np.sin(np.linspace(0, 2 * math.pi, T))

        result = score_orbital_baseline(dancer_pos, orbit_radius=2.0, fps=30)

        self.assertFalse(math.isnan(result["total_mean"]))
        self.assertGreater(result["total_mean"], 0.0,
                           "Orbital baseline should get positive reward")
        self.assertEqual(result["safety_mean"], 0.0,
                         "Orbital at 2m should never violate 1.5m safety zone")
        self.assertGreater(result["framing_mean"], 0.5,
                           "Orbital camera points at dancer → framing > 0.5")
        self.assertGreater(result["distance_mean"], 0.3,
                           "2m orbit is close to 3m ideal → distance > 0.3")

        print("\n=== Orbital Baseline Scores ===")
        for k, v in sorted(result.items()):
            print(f"  {k}: {v:.4f}")

    def test_baseline_with_real_mocap(self):
        """If mocap data exists, score the real A2 trajectory."""
        session_path = Path(__file__).parent.parent / "mocap_handoff" / "Mocap" / "dance_20260519_213931"
        if not session_path.exists():
            # Try EC2-style flat path
            session_path = Path("/home/ubuntu/mocap_session")
        if not session_path.exists():
            self.skipTest("No mocap session available locally")

        from parse_pose_bin import load_session, unity_to_usd_pos, BODY_NAMES

        session = load_session(session_path)
        # Subsample to 30fps, 25s
        step = max(1, round(session.fps / 30))
        max_frames = int(25 * session.fps)
        indices = np.arange(0, min(session.num_frames, max_frames), step)
        positions = session.body_positions[indices]  # (T, 15, 3)
        positions_usd = unity_to_usd_pos(positions)

        pelvis_idx = BODY_NAMES.index("pelvis")
        torso_idx = BODY_NAMES.index("torso")
        dancer_chest = (positions_usd[:, pelvis_idx] + positions_usd[:, torso_idx]) * 0.5

        result = score_orbital_baseline(dancer_chest, orbit_radius=2.0, fps=30)

        self.assertFalse(math.isnan(result["total_mean"]))
        self.assertGreater(result["total_mean"], 0.0)

        print("\n=== Real Mocap Orbital Baseline ===")
        for k, v in sorted(result.items()):
            print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
