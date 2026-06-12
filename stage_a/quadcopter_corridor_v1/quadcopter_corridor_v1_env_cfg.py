# Stage A — vision-PPO drone navigating a procedural 1-obstacle corridor.
# Fork of QuadcopterEnvCfg with depth camera, collision physics, randomized obstacle.

from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg, ContactSensorCfg
from isaaclab.utils import configclass

from isaaclab_assets import CRAZYFLIE_CFG
from isaaclab_tasks.direct.quadcopter.quadcopter_env_cfg import QuadcopterEnvCfg


DEPTH_H = 84
DEPTH_W = 84
STATE_DIM = 12
OBS_DIM = STATE_DIM + DEPTH_H * DEPTH_W


@configclass
class QuadcopterCorridorV1EnvCfg(QuadcopterEnvCfg):
    episode_length_s = 20.0
    decimation = 2

    # Override the Crazyflie spawn to enable contact sensor reporting on the body.
    # Without activate_contact_sensors=True the USD physics layer doesn't register
    # contact callbacks and ContactSensor fails at init.
    robot: ArticulationCfg = CRAZYFLIE_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        spawn=CRAZYFLIE_CFG.spawn.replace(activate_contact_sensors=True),
    )

    # Vision + real-collision is GPU heavier than the visual-only a2b env.
    # Start at 512; raise to 1024 after smoke passes.
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=512, env_spacing=15.0, replicate_physics=True, clone_in_fabric=True
    )

    # Single flat observation: 12 state + 84*84 depth = 7068 floats.
    # The vision policy splits the trailing 7056 back into (1, 84, 84) and feeds the CNN.
    observation_space = OBS_DIM
    action_space = 4
    state_space = 0

    # Reward scales inherited from Phase 6a's a2b (proven on the long traverse).
    distance_to_goal_reward_scale = 30.0
    lin_vel_reward_scale = -0.02
    ang_vel_reward_scale = -0.005
    progress_reward_scale: float = 5.0

    # NEW Stage A rewards
    collision_penalty: float = -50.0          # one-shot spike on contact
    proximity_penalty_scale: float = 1.0      # multiplied by -1/(min_depth.clamp(0.5)^2)

    # Endpoints (env-local; env_origin added at reset time)
    spawn_pos: tuple[float, float, float] = (0.0, 0.0, 30.0)
    goal_pos:  tuple[float, float, float] = (100.0, 0.0, 30.0)

    # Procedural obstacle — single box randomized per episode per env
    obstacle_x_range: tuple[float, float] = (25.0, 75.0)
    obstacle_y_range: tuple[float, float] = (-5.0, 5.0)
    obstacle_z: float = 30.0
    obstacle_size: tuple[float, float, float] = (5.0, 5.0, 10.0)

    # The obstacle is registered as a kinematic rigid body so it's collidable but
    # we can teleport it on reset without PhysX integrator complaining.
    obstacle: RigidObjectCfg = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Obstacle",
        spawn=sim_utils.CuboidCfg(
            size=obstacle_size,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=True,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=True),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.2, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(50.0, 0.0, obstacle_z)),
    )

    # Forward-facing depth camera, 5cm in front of body, 30m clipping (Stage A horizon).
    camera: CameraCfg = CameraCfg(
        prim_path="/World/envs/env_.*/Robot/body/depth_cam",
        update_period=0.0,                    # every step
        height=DEPTH_H,
        width=DEPTH_W,
        data_types=["distance_to_image_plane"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=15.0,
            focus_distance=400.0,
            clipping_range=(0.05, 30.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.05, 0.0, 0.0),
            rot=(1.0, 0.0, 0.0, 0.0),
            convention="ros",
        ),
    )

    # Contact sensor on drone body — used for collision termination + penalty.
    contact: ContactSensorCfg = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/body",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
    )

    ui_window_class_type = "{DIR}.quadcopter_corridor_v1_env:QuadcopterCorridorV1EnvWindow"
