#!/usr/bin/env python3
"""
rewards.py — Cinematography reward function for autonomous drone filming.

Pure-math reward terms that encode professional cinematography principles.
No Isaac Sim dependency — works with numpy for local testing, or torch
tensors inside the Isaac Lab env (all ops are element-wise and work on both).

Reward terms:
  1. framing    — keep dancer centered in camera frustum
  2. distance   — stay in the sweet spot (2–4m)
  3. smoothness — penalize jerky acceleration (jerk = da/dt)
  4. variety    — reward changing azimuth angle over time
  5. safety     — hard penalty inside 1.5m exclusion zone
  6. height     — reward elevation angle variety (low/eye/high shots)
  7. look_at    — reward camera orientation actually pointing at dancer

Each function returns a per-env scalar reward. The composite function
weights and sums them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Union

import numpy as np

Array = Union[np.ndarray, "torch.Tensor"]


@dataclass
class CinematographyRewardCfg:
    """Weights and parameters for each reward term."""

    # --- weights v2 (framing-dominant: "always see the dancer" = 55%) ---
    w_framing: float = 0.35
    w_distance: float = 0.10
    w_smoothness: float = 0.10
    w_variety: float = 0.05
    w_safety: float = 0.10
    w_height: float = 0.03
    w_look_at: float = 0.20
    w_shot_type: float = 0.07       # shot type diversity (full/medium/close)

    # --- framing ---
    framing_tolerance_rad: float = math.radians(15)

    # --- distance ---
    # Wider range now: allows close-ups (2m) through wide shots (5m)
    dist_ideal_m: float = 3.0
    dist_margin_m: float = 2.0      # wider margin to allow both close and far
    dist_min_m: float = 1.5         # hard lower bound (safety zone)
    dist_max_m: float = 6.0         # beyond this, too far to film

    # --- smoothness ---
    jerk_scale: float = 10.0        # tanh normalization for jerk magnitude (m/s³)

    # --- variety ---
    variety_window: int = 150       # frames (~5s at 30fps) to measure angle spread
    variety_target_std_rad: float = math.radians(30)  # target std dev of azimuth

    # --- safety ---
    safety_radius_m: float = 1.5
    safety_penalty: float = -10.0   # one-shot penalty per step inside zone

    # --- height ---
    height_min_angle_rad: float = math.radians(-20)   # low angle (hero shot)
    height_max_angle_rad: float = math.radians(45)     # high angle (establishing)
    height_ideal_range_rad: float = math.radians(50)   # reward for using this range

    # --- look_at ---
    look_at_tolerance_rad: float = math.radians(10)

    # --- shot type diversity ---
    # Shot types based on how much of the dancer's body the camera sees.
    # Computed from distance + vertical FOV (35mm lens, 24mm sensor height).
    # full body: camera sees ≥1.5m of dancer height (d ≥ 2.2m)
    # medium/half body: camera sees 0.8–1.5m (d ≈ 1.5–2.2m)
    # close-up: camera sees <0.8m (d < 1.5m — but this is in safety zone)
    # So practically: full body at 3-5m, half body at 2-3m
    shot_type_window: int = 150     # frames to measure shot type spread
    focal_length_mm: float = 35.0
    sensor_height_mm: float = 24.0

    # --- v3: front arc (no going behind performer) ---
    front_arc_penalty: float = -5.0   # penalty per step when behind performer
    front_arc_half_angle_rad: float = math.radians(90)  # 180° total arc

    # --- v3: hold-when-good (pause on beautiful frames) ---
    hold_framing_threshold: float = 0.7    # framing score above this = "good frame"
    hold_velocity_scale: float = 2.0       # m/s — lower velocity when holding = higher reward
    w_hold_beauty: float = 0.10

    # --- v3: zoom dynamics (push-in / pull-out) ---
    zoom_window: int = 90           # 3s at 30fps — look for distance changes
    zoom_ideal_changes: int = 2     # want ~2 push-in/pull-out cycles per window
    w_zoom: float = 0.08

    # --- v3: pacing (alternate movement and stillness) ---
    pacing_window: int = 150        # 5s window
    pacing_move_threshold: float = 0.3  # m/s — above = "moving", below = "holding"
    pacing_ideal_ratio: float = 0.5     # want ~50% moving, 50% holding
    w_pacing: float = 0.07


def _tanh_reward(error: Array, scale: float) -> Array:
    """1 - tanh(|error| / scale). Returns 1.0 at error=0, ~0.24 at error=scale."""
    abs_err = np.abs(error) if isinstance(error, np.ndarray) else error.abs()
    return 1.0 - np.tanh(abs_err / scale) if isinstance(error, np.ndarray) else 1.0 - (abs_err / scale).tanh()


def _norm(v: Array, axis: int = -1) -> Array:
    if isinstance(v, np.ndarray):
        return np.linalg.norm(v, axis=axis)
    return v.norm(dim=axis)


def _clamp(x: Array, lo: float, hi: float) -> Array:
    if isinstance(x, np.ndarray):
        return np.clip(x, lo, hi)
    return x.clamp(lo, hi)


# ---------------------------------------------------------------------------
# Individual reward terms
# ---------------------------------------------------------------------------

def reward_framing(
    drone_pos: Array,
    dancer_pos: Array,
    drone_forward: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for keeping the dancer centered in the camera's view.

    Computes the angle between the camera's forward vector and the
    direction toward the dancer. Reward peaks when dancer is on-axis.
    """
    to_dancer = dancer_pos - drone_pos
    to_dancer_norm = to_dancer / (_norm(to_dancer, axis=-1)[..., None] + 1e-8)
    drone_fwd_norm = drone_forward / (_norm(drone_forward, axis=-1)[..., None] + 1e-8)

    # dot product → cos(angle)
    if isinstance(to_dancer_norm, np.ndarray):
        cos_angle = np.sum(to_dancer_norm * drone_fwd_norm, axis=-1)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
    else:
        cos_angle = (to_dancer_norm * drone_fwd_norm).sum(dim=-1)
        cos_angle = cos_angle.clamp(-1.0, 1.0)
        angle = cos_angle.acos()

    return _tanh_reward(angle, cfg.framing_tolerance_rad)


def reward_distance(
    drone_pos: Array,
    dancer_pos: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for maintaining ideal filming distance."""
    dist = _norm(drone_pos - dancer_pos, axis=-1)
    error = dist - cfg.dist_ideal_m
    return _tanh_reward(error, cfg.dist_margin_m)


def reward_smoothness(
    accel_current: Array,
    accel_previous: Array,
    dt: float,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Penalize jerk (rate of change of acceleration).

    Jerk = (a_t - a_{t-1}) / dt. Lower jerk = smoother camera motion.
    """
    jerk = (accel_current - accel_previous) / dt
    jerk_mag = _norm(jerk, axis=-1)
    return _tanh_reward(jerk_mag, cfg.jerk_scale)


def reward_variety(
    azimuth_history: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for shot angle variety over a time window.

    Measures the standard deviation of the drone's azimuth angle relative
    to the dancer over the last `variety_window` frames. Higher spread =
    more dynamic camera work.

    azimuth_history: (num_envs, window) in radians
    """
    if isinstance(azimuth_history, np.ndarray):
        # Handle wraparound by using circular std
        sin_mean = np.mean(np.sin(azimuth_history), axis=-1)
        cos_mean = np.mean(np.cos(azimuth_history), axis=-1)
        R = np.sqrt(sin_mean**2 + cos_mean**2)
        circular_std = np.sqrt(-2.0 * np.log(np.clip(R, 1e-8, 1.0)))
    else:
        sin_mean = azimuth_history.sin().mean(dim=-1)
        cos_mean = azimuth_history.cos().mean(dim=-1)
        R = (sin_mean**2 + cos_mean**2).sqrt()
        circular_std = (-2.0 * R.clamp(1e-8, 1.0).log()).sqrt()

    return _clamp(circular_std / cfg.variety_target_std_rad, 0.0, 1.0)


def reward_safety(
    drone_pos: Array,
    dancer_pos: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Hard penalty for violating the safety exclusion zone."""
    dist = _norm(drone_pos - dancer_pos, axis=-1)
    if isinstance(dist, np.ndarray):
        violation = (dist < cfg.safety_radius_m).astype(float)
    else:
        violation = (dist < cfg.safety_radius_m).float()
    return violation * cfg.safety_penalty


def reward_height_variety(
    elevation_history: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for using a range of elevation angles (low/eye/high shots).

    elevation_history: (num_envs, window) in radians, negative = below dancer,
    positive = above.
    """
    if isinstance(elevation_history, np.ndarray):
        el_range = np.max(elevation_history, axis=-1) - np.min(elevation_history, axis=-1)
    else:
        el_range = elevation_history.max(dim=-1).values - elevation_history.min(dim=-1).values
    return _clamp(el_range / cfg.height_ideal_range_rad, 0.0, 1.0)


def reward_look_at(
    drone_pos: Array,
    dancer_pos: Array,
    drone_forward: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for camera orientation actually pointing at the dancer.

    Similar to framing but specifically rewards the horizontal aim —
    the camera yaw should track the dancer even when doing height changes.
    """
    to_dancer = dancer_pos - drone_pos
    # Project to horizontal plane (XZ in Y-up, or XY in Z-up)
    if isinstance(to_dancer, np.ndarray):
        to_dancer_horiz = to_dancer.copy()
    else:
        to_dancer_horiz = to_dancer.clone()
    to_dancer_horiz[..., 1] = 0  # zero out Y (up axis in USD) or Z (up in Isaac)
    to_dancer_horiz = to_dancer_horiz / (_norm(to_dancer_horiz, axis=-1)[..., None] + 1e-8)

    if isinstance(drone_forward, np.ndarray):
        fwd_horiz = drone_forward.copy()
    else:
        fwd_horiz = drone_forward.clone()
    fwd_horiz[..., 1] = 0
    fwd_horiz = fwd_horiz / (_norm(fwd_horiz, axis=-1)[..., None] + 1e-8)

    if isinstance(to_dancer_horiz, np.ndarray):
        cos_angle = np.sum(to_dancer_horiz * fwd_horiz, axis=-1)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
    else:
        cos_angle = (to_dancer_horiz * fwd_horiz).sum(dim=-1)
        cos_angle = cos_angle.clamp(-1.0, 1.0)
        angle = cos_angle.acos()

    return _tanh_reward(angle, cfg.look_at_tolerance_rad)


def compute_vertical_coverage(
    distance: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Compute how much vertical height (meters) the camera sees at given distance.

    Based on pinhole camera model: coverage = 2 * d * tan(vfov/2)
    where vfov = 2 * atan(sensor_height / (2 * focal_length)).
    """
    half_vfov = math.atan(cfg.sensor_height_mm / (2 * cfg.focal_length_mm))
    if isinstance(distance, np.ndarray):
        return 2.0 * distance * math.tan(half_vfov)
    return 2.0 * distance * math.tan(half_vfov)


def classify_shot_type(
    distance: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Classify each frame as a shot type based on vertical body coverage.

    Returns: 0 = close-up (<0.8m coverage), 1 = half body (0.8–1.5m),
             2 = full body (≥1.5m).
    """
    coverage = compute_vertical_coverage(distance, cfg)
    if isinstance(coverage, np.ndarray):
        shot = np.zeros_like(coverage)
        shot[coverage >= 0.8] = 1.0
        shot[coverage >= 1.5] = 2.0
    else:
        shot = (coverage >= 0.8).float() + (coverage >= 1.5).float()
    return shot


def reward_shot_type_diversity(
    distance_history: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward for mixing between full-body and half-body shots over time.

    A professional cinematographer alternates between wide establishing shots
    (full body), medium shots (waist up), and tighter framings. This reward
    measures how many distinct shot types appear in the recent window.

    distance_history: (num_envs, window) — distance to dancer per frame.
    """
    # Classify each frame in the window
    shot_types = classify_shot_type(distance_history, cfg)  # 0, 1, or 2

    if isinstance(shot_types, np.ndarray):
        has_close = np.any(shot_types == 0, axis=-1).astype(float)
        has_half = np.any(shot_types == 1, axis=-1).astype(float)
        has_full = np.any(shot_types == 2, axis=-1).astype(float)
        num_types = has_close + has_half + has_full

        # Also reward transitions between types (not just presence)
        transitions = np.sum(np.abs(np.diff(shot_types, axis=-1)) > 0, axis=-1)
        transition_bonus = np.clip(transitions / 5.0, 0.0, 1.0)  # up to 5 transitions
    else:
        has_close = (shot_types == 0).any(dim=-1).float()
        has_half = (shot_types == 1).any(dim=-1).float()
        has_full = (shot_types == 2).any(dim=-1).float()
        num_types = has_close + has_half + has_full

        transitions = (shot_types[:, 1:] - shot_types[:, :-1]).abs().gt(0).sum(dim=-1)
        transition_bonus = (transitions / 5.0).clamp(0.0, 1.0)

    # 1 type = 0.33, 2 types = 0.67, 3 types = 1.0, plus transition bonus
    type_score = num_types / 3.0
    return 0.6 * type_score + 0.4 * transition_bonus


# ---------------------------------------------------------------------------
# v3 reward terms: front-arc, hold-beauty, zoom, pacing
# ---------------------------------------------------------------------------

def reward_front_arc(
    drone_pos: Array,
    dancer_pos: Array,
    performer_facing: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Penalize drone when it's behind the performer.

    performer_facing: (num_envs, 3) — unit vector pointing where performer faces.
    Drone must be in the 180° arc in FRONT of the performer.
    """
    to_drone = drone_pos - dancer_pos
    # Project to horizontal plane
    if isinstance(to_drone, np.ndarray):
        to_drone_horiz = to_drone.copy()
        facing_horiz = performer_facing.copy()
    else:
        to_drone_horiz = to_drone.clone()
        facing_horiz = performer_facing.clone()

    # Zero out vertical component (Z in Isaac Z-up, Y in USD Y-up)
    to_drone_horiz[..., -1] = 0  # last axis = up
    facing_horiz[..., -1] = 0

    to_drone_horiz = to_drone_horiz / (_norm(to_drone_horiz, axis=-1)[..., None] + 1e-8)
    facing_horiz = facing_horiz / (_norm(facing_horiz, axis=-1)[..., None] + 1e-8)

    # dot product: positive = drone is in front, negative = behind
    if isinstance(to_drone_horiz, np.ndarray):
        cos_angle = np.sum(to_drone_horiz * facing_horiz, axis=-1)
    else:
        cos_angle = (to_drone_horiz * facing_horiz).sum(dim=-1)

    # In front: cos > 0 → reward 1.0; behind: cos < 0 → penalty
    if isinstance(cos_angle, np.ndarray):
        behind = (cos_angle < 0).astype(float)
    else:
        behind = (cos_angle < 0).float()

    return behind * cfg.front_arc_penalty


def reward_hold_when_good(
    drone_vel: Array,
    framing_score: Array,
    look_at_score: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward holding still when the frame is good.

    A real cinematographer FINDS a beautiful angle, then HOLDS it.
    If framing + look_at are both high, reward low velocity.
    """
    # Is this a "good frame"?
    frame_quality = framing_score * look_at_score  # 0 to 1
    is_good_frame = _clamp(frame_quality / cfg.hold_framing_threshold, 0.0, 1.0)

    # How still is the drone?
    speed = _norm(drone_vel, axis=-1)
    stillness = 1.0 - (speed / cfg.hold_velocity_scale).tanh() if isinstance(speed, np.ndarray) \
        else 1.0 - (speed / cfg.hold_velocity_scale).tanh()

    # Reward stillness only when frame is good
    return is_good_frame * stillness


def reward_zoom_dynamics(
    distance_history: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward intentional push-in / pull-out distance changes.

    A cinematographer zooms in to capture detail, holds, then pulls out
    for context. Reward deliberate distance transitions (not jittery noise).

    distance_history: (num_envs, window) — distance to dancer per frame.
    """
    if isinstance(distance_history, np.ndarray):
        # Smooth the distance to ignore noise
        kernel_size = 10
        if distance_history.shape[-1] < kernel_size:
            return np.zeros(distance_history.shape[0])
        # Simple moving average
        cumsum = np.cumsum(distance_history, axis=-1)
        smoothed = (cumsum[..., kernel_size:] - cumsum[..., :-kernel_size]) / kernel_size
        # Count significant direction changes (push-in → pull-out or vice versa)
        diff = np.diff(smoothed, axis=-1)
        sign_changes = np.sum(np.abs(np.diff(np.sign(diff), axis=-1)) > 0, axis=-1)
        # Reward having ~2 zoom cycles per window (not too many = jittery, not too few = static)
        zoom_score = 1.0 - np.abs(sign_changes - cfg.zoom_ideal_changes * 2) / (cfg.zoom_ideal_changes * 2 + 1)
        return np.clip(zoom_score, 0.0, 1.0)
    else:
        kernel_size = 10
        if distance_history.shape[-1] < kernel_size:
            return torch.zeros(distance_history.shape[0], device=distance_history.device)
        # Moving average via unfold
        smoothed = distance_history.unfold(-1, kernel_size, 1).mean(dim=-1)
        diff = smoothed[:, 1:] - smoothed[:, :-1]
        sign_changes = (diff[:, 1:].sign() - diff[:, :-1].sign()).abs().gt(0).sum(dim=-1).float()
        zoom_score = 1.0 - (sign_changes - cfg.zoom_ideal_changes * 2).abs() / (cfg.zoom_ideal_changes * 2 + 1)
        return zoom_score.clamp(0.0, 1.0)


def reward_pacing(
    velocity_history: Array,
    cfg: CinematographyRewardCfg,
) -> Array:
    """Reward alternating between movement and stillness.

    A great cinematographer isn't always moving OR always still — they
    alternate. Move to find a new angle, then hold. Move again, hold again.

    velocity_history: (num_envs, window) — speed magnitude per frame.
    """
    threshold = cfg.pacing_move_threshold
    if isinstance(velocity_history, np.ndarray):
        is_moving = (velocity_history > threshold).astype(float)
        move_ratio = np.mean(is_moving, axis=-1)
        # Count transitions between moving and holding
        transitions = np.sum(np.abs(np.diff(is_moving, axis=-1)) > 0, axis=-1)
        transition_score = np.clip(transitions / 6.0, 0.0, 1.0)  # want ~6 transitions in 5s
    else:
        is_moving = (velocity_history > threshold).float()
        move_ratio = is_moving.mean(dim=-1)
        transitions = (is_moving[:, 1:] - is_moving[:, :-1]).abs().sum(dim=-1)
        transition_score = (transitions / 6.0).clamp(0.0, 1.0)

    # Reward being near 50/50 split
    ratio_score = 1.0 - abs(move_ratio - cfg.pacing_ideal_ratio) * 2 if isinstance(move_ratio, np.ndarray) \
        else 1.0 - (move_ratio - cfg.pacing_ideal_ratio).abs() * 2
    ratio_score = _clamp(ratio_score, 0.0, 1.0)

    # Combine: 60% pacing ratio, 40% transition frequency
    return 0.6 * ratio_score + 0.4 * transition_score


# ---------------------------------------------------------------------------
# Utility: compute azimuth + elevation from relative position
# ---------------------------------------------------------------------------

def compute_azimuth_elevation(
    drone_pos: Array, dancer_pos: Array
) -> tuple[Array, Array]:
    """Return (azimuth, elevation) in radians of the drone relative to dancer.

    Azimuth: angle in XZ plane, 0 = +Z, positive = clockwise.
    Elevation: angle above horizontal, positive = drone above dancer.
    """
    rel = drone_pos - dancer_pos
    if isinstance(rel, np.ndarray):
        azimuth = np.arctan2(rel[..., 0], rel[..., 2])
        horiz = np.sqrt(rel[..., 0]**2 + rel[..., 2]**2)
        elevation = np.arctan2(rel[..., 1], horiz)
    else:
        azimuth = rel[..., 0].atan2(rel[..., 2])
        horiz = (rel[..., 0]**2 + rel[..., 2]**2).sqrt()
        elevation = rel[..., 1].atan2(horiz)
    return azimuth, elevation


# ---------------------------------------------------------------------------
# Composite reward
# ---------------------------------------------------------------------------

def compute_total_reward(
    drone_pos: Array,
    dancer_pos: Array,
    drone_forward: Array,
    accel_current: Array,
    accel_previous: Array,
    azimuth_history: Array,
    elevation_history: Array,
    distance_history: Array,
    dt: float,
    cfg: CinematographyRewardCfg | None = None,
) -> tuple[Array, dict[str, Array]]:
    """Compute weighted sum of all reward terms.

    Returns (total_reward, component_dict) for logging.
    """
    if cfg is None:
        cfg = CinematographyRewardCfg()

    r_frame = reward_framing(drone_pos, dancer_pos, drone_forward, cfg)
    r_dist = reward_distance(drone_pos, dancer_pos, cfg)
    r_smooth = reward_smoothness(accel_current, accel_previous, dt, cfg)
    r_variety = reward_variety(azimuth_history, cfg)
    r_safe = reward_safety(drone_pos, dancer_pos, cfg)
    r_height = reward_height_variety(elevation_history, cfg)
    r_look = reward_look_at(drone_pos, dancer_pos, drone_forward, cfg)
    r_shot = reward_shot_type_diversity(distance_history, cfg)

    total = (
        cfg.w_framing * r_frame
        + cfg.w_distance * r_dist
        + cfg.w_smoothness * r_smooth
        + cfg.w_variety * r_variety
        + cfg.w_safety * r_safe
        + cfg.w_height * r_height
        + cfg.w_look_at * r_look
        + cfg.w_shot_type * r_shot
    )

    components = {
        "framing": r_frame,
        "distance": r_dist,
        "smoothness": r_smooth,
        "variety": r_variety,
        "safety": r_safe,
        "height_variety": r_height,
        "look_at": r_look,
        "shot_type_diversity": r_shot,
    }
    return total, components


# ---------------------------------------------------------------------------
# Orbital baseline scorer — compute reward on the A2 orbital trajectory
# ---------------------------------------------------------------------------

def score_orbital_baseline(
    dancer_positions: np.ndarray,
    orbit_radius: float = 2.0,
    orbit_height_offset: float = 0.3,
    fps: int = 30,
    cfg: CinematographyRewardCfg | None = None,
) -> dict:
    """Score the A2 orbital baseline trajectory against the reward function.

    dancer_positions: (T, 3) dancer chest positions in USD coords (Y-up).
    Returns dict with per-term means and total mean reward.
    """
    if cfg is None:
        cfg = CinematographyRewardCfg()

    T = dancer_positions.shape[0]
    dt = 1.0 / fps

    # Reconstruct orbital camera trajectory
    drone_positions = np.zeros_like(dancer_positions)
    drone_forwards = np.zeros_like(dancer_positions)
    for f in range(T):
        angle = 2 * math.pi * f / T
        center = dancer_positions[f]
        drone_positions[f, 0] = center[0] + orbit_radius * math.sin(angle)
        drone_positions[f, 1] = center[1] + orbit_height_offset
        drone_positions[f, 2] = center[2] + orbit_radius * math.cos(angle)
        # Forward = toward dancer
        fwd = center - drone_positions[f]
        fwd_len = np.linalg.norm(fwd)
        drone_forwards[f] = fwd / (fwd_len + 1e-8)

    # Compute accelerations (finite differences)
    vel = np.gradient(drone_positions, dt, axis=0)
    accel = np.gradient(vel, dt, axis=0)

    # Compute azimuth/elevation/distance histories
    azimuths, elevations = compute_azimuth_elevation(drone_positions, dancer_positions)
    distances = np.linalg.norm(drone_positions - dancer_positions, axis=-1)

    # Score each frame
    total_rewards = []
    all_components = {k: [] for k in [
        "framing", "distance", "smoothness", "variety", "height_variety",
        "safety", "look_at", "shot_type_diversity"
    ]}

    window = cfg.variety_window
    for f in range(1, T):
        az_start = max(0, f - window)
        az_hist = azimuths[az_start:f+1][None, :]  # (1, window)
        el_hist = elevations[az_start:f+1][None, :]
        dist_hist = distances[az_start:f+1][None, :]

        total, comps = compute_total_reward(
            drone_pos=drone_positions[f:f+1],
            dancer_pos=dancer_positions[f:f+1],
            drone_forward=drone_forwards[f:f+1],
            accel_current=accel[f:f+1],
            accel_previous=accel[f-1:f],
            azimuth_history=az_hist,
            elevation_history=el_hist,
            distance_history=dist_hist,
            dt=dt,
            cfg=cfg,
        )
        total_rewards.append(float(total[0]))
        for k, v in comps.items():
            all_components[k].append(float(v[0]))

    result = {"total_mean": float(np.mean(total_rewards))}
    for k, v in all_components.items():
        result[f"{k}_mean"] = float(np.mean(v))
    return result
