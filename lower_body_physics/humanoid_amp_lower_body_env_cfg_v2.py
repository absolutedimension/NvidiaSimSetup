"""Configuration V2 for the Lower Body Physics AMP environment.

Changes from V1:
1. Rebalanced reward weights — survival bonus + stronger upright/height
2. Head-below-feet termination (catches flipped humanoid)
3. Curriculum-ready: task/style weights in skrl config, not here
"""
from __future__ import annotations

import os

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

_AMP_MOTIONS_DIR = os.path.join(_THIS_DIR, "..", "humanoid_amp", "motions")
if not os.path.isdir(_AMP_MOTIONS_DIR):
    _AMP_MOTIONS_DIR = (
        "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks"
        "/direct/humanoid_amp/motions"
    )


try:
    from isaaclab_assets.robots.humanoid_28 import HUMANOID_28_CFG as _BASE_HUMANOID_CFG
except ImportError:
    _BASE_HUMANOID_CFG = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=(
                "omniverse://localhost/NVIDIA/Assets/Isaac/6.0"
                "/Isaac/Robots/Classic/Humanoid28/humanoid_28.usd"
            ),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=10.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=4,
                solver_velocity_iteration_count=0,
            ),
            copy_from_source=False,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.87),
            joint_pos={".*": 0.0},
        ),
        actuators={
            "body": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=None,
                damping=None,
            ),
        },
    )


@configclass
class HumanoidAmpLowerBodyEnvCfg(DirectRLEnvCfg):
    """V2 config with survival bonus and curriculum-ready reward weights."""

    # --- Timing ---
    episode_length_s: float = 10.0
    decimation: int = 2

    # --- Spaces ---
    observation_space: int = 81
    action_space: int = 14
    state_space: int = 0

    # --- AMP discriminator ---
    amp_observation_space: int = 81
    num_amp_observations: int = 2
    amp_motion_file: str = os.path.join(_AMP_MOTIONS_DIR, "humanoid_dance.npz")

    # --- Quest trajectory ---
    quest_trajectory_file: str = os.path.join(_THIS_DIR, "lb_trajectory_v1.npz")

    # --- Upper body pinning ---
    upper_body_kp: float = 200.0
    upper_body_kd: float = 20.0
    max_pinning_torque: float = 50.0

    # --- Reference body ---
    reference_body: str = "torso"

    # --- Reward weights (V2: rebalanced for standing) ---
    # Total task reward sums to ~1.0 before AMP weighting
    # The skrl AMP trainer multiplies this by task_reward_weight (e.g. 0.95)
    # and adds style_reward_weight * amp_reward (e.g. 0.05)
    reward_upright_weight: float = 0.25     # was 0.10 — doubled+
    reward_height_weight: float = 0.25      # was 0.20 — slightly up
    reward_foot_contact_weight: float = 0.15  # was 0.30 — reduced
    reward_energy_weight: float = 0.05      # was 0.10 — reduced
    reward_survival_weight: float = 0.20    # NEW — per-step survival bonus
    reward_head_height_weight: float = 0.10  # NEW — head at natural height

    # --- Target root height ---
    target_root_height: float = 0.87

    # --- Termination (V2: stricter) ---
    early_termination: bool = True
    termination_height: float = 0.3
    terminate_head_below_feet: bool = True  # NEW — catches flipped humanoid

    # --- Simulation ---
    sim: SimulationCfg = SimulationCfg(
        dt=1.0 / 120.0,
        render_interval=2,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        ),
    )

    # --- Terrain ---
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="plane",
        collision_group=-1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        ),
        debug_vis=False,
    )

    # --- Scene ---
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=256,
        env_spacing=5.0,
    )

    # --- Robot ---
    robot: ArticulationCfg = _BASE_HUMANOID_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.87),
            joint_pos={".*": 0.0},
        ),
    )

    debug_vis: bool = False
