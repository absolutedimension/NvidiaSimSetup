"""Configuration for the Lower Body Physics AMP environment.

Matches the standard Isaac Lab AMP humanoid env config pattern, with additions
for Quest upper-body pinning and lower-body-only action space.

Deployment: copy to the isaaclab container alongside humanoid_amp_lower_body_env.py
at /workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp_lower_body/
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


# ---------- Paths ----------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# AMP reference motions — sibling directory when deployed under isaaclab_tasks/direct/
_AMP_MOTIONS_DIR = os.path.join(_THIS_DIR, "..", "humanoid_amp", "motions")
if not os.path.isdir(_AMP_MOTIONS_DIR):
    # Fallback: absolute path inside the container
    _AMP_MOTIONS_DIR = (
        "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks"
        "/direct/humanoid_amp/motions"
    )


# ---------- Robot config ----------

# Import the standard humanoid 28-DOF asset config from isaaclab_assets.
# If not available (e.g., running outside the container for linting), define a
# fallback inline.
try:
    from isaaclab_assets.robots.humanoid_28 import HUMANOID_28_CFG as _BASE_HUMANOID_CFG
except ImportError:
    # Inline fallback — matches isaaclab_assets/robots/humanoid_28.py exactly
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
                stiffness=None,  # use values from USD
                damping=None,
            ),
        },
    )


# ---------- Environment config ----------

@configclass
class HumanoidAmpLowerBodyEnvCfg(DirectRLEnvCfg):
    """Pinned-upper-body AMP humanoid environment configuration.

    Upper body (9 bodies, 14 DOFs) pinned to Quest mocap via body-level
    external torques. Lower body (6 bodies, 14 DOFs) controlled by RL policy.
    AMP discriminator on full 15-body state ensures natural motion.
    """

    # --- Timing ---
    episode_length_s: float = 10.0
    decimation: int = 2  # control dt = sim_dt * decimation = 1/60s (matches Quest 60fps)

    # --- Spaces ---
    # Policy observation: 14+14+14+14+1+6+3+3+12 = 81 dims
    #   lower_dof_pos(14) + lower_dof_vel(14) + upper_dof_pos(14) + upper_dof_vel(14)
    #   + root_height(1) + tangent_normal(6) + root_linvel(3) + root_angvel(3)
    #   + key_body_rel_pos(12)
    observation_space: int = 81
    # Actions: 14 lower body DOF position targets
    action_space: int = 14
    state_space: int = 0

    # --- AMP discriminator ---
    # AMP obs: dof_pos(28) + dof_vel(28) + height(1) + tangent_normal(6)
    #          + root_linvel(3) + root_angvel(3) + key_body_rel(12) = 81
    amp_observation_space: int = 81
    num_amp_observations: int = 2  # current frame + 1 history frame

    # Reference motion for AMP discriminator — uses built-in humanoid_dance.npz
    amp_motion_file: str = os.path.join(_AMP_MOTIONS_DIR, "humanoid_dance.npz")

    # --- Quest trajectory ---
    # Upper body trajectory file (from prepare_lb_trajectory.py)
    quest_trajectory_file: str = os.path.join(_THIS_DIR, "lb_trajectory_v1.npz")

    # --- Upper body pinning (body-level external torques) ---
    # NOTE: kp=1000 caused PhysX divergence at step 10-11 (torques too large for
    # small-inertia bodies like hands/forearms → angular accel ~10^5 rad/s² → NaN).
    # Reduced 5× and added per-component clamping in the env.
    upper_body_kp: float = 200.0    # rotational stiffness (N·m/rad)
    upper_body_kd: float = 20.0     # rotational damping (N·m·s/rad)
    max_pinning_torque: float = 50.0  # max torque per axis per body (N·m) — prevents blow-up

    # --- Reference body ---
    reference_body: str = "torso"

    # --- Reward weights ---
    # AMP reward (r_amp, ~0.30 of total) is added externally by the skrl AMP trainer
    # These weights govern the task-specific reward terms:
    reward_upright_weight: float = 0.10     # pelvis up-vector · world Z
    reward_height_weight: float = 0.20      # pelvis Z near target
    reward_foot_contact_weight: float = 0.30  # at least one foot on ground
    reward_energy_weight: float = 0.10      # penalize excessive joint velocities

    # --- Target root height ---
    target_root_height: float = 0.87  # meters (standing humanoid pelvis height)

    # --- Termination ---
    early_termination: bool = True
    termination_height: float = 0.3   # meters — terminate if pelvis drops below this

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

    # --- Debug ---
    debug_vis: bool = False
