"""Isaac Lab env config for the cinematography drone (Starling 2)."""
from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass


STARLING2_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path="/workspace/isaaclab/cinematography/starling2.usd",
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            max_depenetration_velocity=10.0,
            enable_gyroscopic_forces=True,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=0,
            sleep_threshold=0.005,
            stabilization_threshold=0.001,
        ),
        copy_from_source=False,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 1.5),  # start at ~1.5m height (above dancer chest)
        joint_pos={".*": 0.0},
        joint_vel={
            "m1_joint": 200.0,
            "m2_joint": -200.0,
            "m3_joint": 200.0,
            "m4_joint": -200.0,
        },
    ),
    actuators={
        "dummy": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            stiffness=0.0,
            damping=0.0,
        ),
    },
)


@configclass
class CinematographerEnvCfg(DirectRLEnvCfg):
    # Observation: [lin_vel_b(3), ang_vel_b(3), gravity_b(3), rel_dancer_b(3),
    #               dancer_vel_b(3), distance(1), azimuth(1), elevation(1),
    #               prev_azimuth(1), prev_elevation(1)]
    # = 20 dims
    episode_length_s = 25.0
    decimation = 2
    action_space = 4
    observation_space = 20
    state_space = 0
    debug_vis = False

    sim: SimulationCfg = SimulationCfg(
        dt=1 / 100,
        render_interval=decimation,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        ),
    )

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

    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=1024, env_spacing=4.0, replicate_physics=True, clone_in_fabric=True
    )

    robot: ArticulationCfg = STARLING2_CFG.replace(prim_path="/World/envs/env_.*/Robot")

    # Starling 2: 280g, ~2.5N per motor = ~10N total, weight = 0.28*9.81 = 2.75N
    # thrust_to_weight = max_thrust / weight ≈ 10/2.75 ≈ 3.6
    thrust_to_weight = 3.6
    moment_scale = 0.02  # larger than Crazyflie due to bigger frame

    # Dancer trajectory
    mocap_npz_path: str = "/workspace/isaaclab/cinematography/dancer_trajectory.npz"

    # Reward weights
    reward_scale: float = 1.0
