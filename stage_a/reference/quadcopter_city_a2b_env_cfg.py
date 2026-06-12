# Quadcopter A->B in Rivermark - env config (fork of QuadcopterEnvCfg)
from __future__ import annotations
from isaaclab.utils import configclass
from isaaclab_tasks.direct.quadcopter.quadcopter_env_cfg import QuadcopterEnvCfg
from isaaclab.scene import InteractiveSceneCfg


@configclass
class QuadcopterCityA2BEnvCfg(QuadcopterEnvCfg):
    # Longer episodes - 100m traverse takes time at Crazyflie's modest top speed
    episode_length_s = 15.0

    # 4096 envs matches the rl_games yaml's expected batch size (4096*24 = 98304,
    # divisible by minibatch_size 24576).
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=4096, env_spacing=2.5, replicate_physics=True, clone_in_fabric=True
    )

    # Reward shape, tuned for 100m horizon (parent's defaults are for ~2m hover)
    distance_to_goal_reward_scale = 30.0    # was 15.0 in parent
    lin_vel_reward_scale = -0.02            # less penalty so drone is willing to MOVE
    ang_vel_reward_scale = -0.005
    # NEW: progress reward (delta-distance per step) - gives PPO a non-saturating
    # gradient signal at any distance. Critical for long traverses.
    progress_reward_scale: float = 5.0

    # NEW fields for City env
    city_usd_path: str = "/assets/Rivermark/rivermark.usd"

    # Point A (spawn) and Point B (goal) in env-local coords (added to env_origin)
    spawn_pos: tuple[float, float, float] = (0.0, 0.0, 30.0)
    goal_pos: tuple[float, float, float]  = (100.0, 0.0, 30.0)

    # Subclass UI window
    ui_window_class_type = "{DIR}.quadcopter_city_a2b_env:QuadcopterCityA2BEnvWindow"
