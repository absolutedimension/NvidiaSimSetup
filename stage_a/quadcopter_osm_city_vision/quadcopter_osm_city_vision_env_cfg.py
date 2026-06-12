# Stage A — Crazyflie vision-PPO over the Manhattan OSM city.
#
# Merges the collision-physics approach of quadcopter_osm_city_env_cfg
# (keep building colliders, terminate on contact) with the depth-camera
# observation space of quadcopter_corridor_v1_env_cfg (84×84 pinhole,
# proximity penalty). The result is the first env where the drone SEES
# what it bumps into — a prerequisite for real hardware deployment.
#
# Inherits from QuadcopterEnvCfg (the base, not city_a2b) so we control
# the full scene: no Rivermark, no API stripping, just city USD + sensors.

from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg, ContactSensorCfg
from isaaclab.utils import configclass

from isaaclab_assets import CRAZYFLIE_CFG
from isaaclab_tasks.direct.quadcopter.quadcopter_env_cfg import QuadcopterEnvCfg


# Observation layout constants — must match the VisionPolicy/VisionValue
# trunk in quadcopter_corridor_v1/networks_vision.py exactly.
DEPTH_H = 84
DEPTH_W = 84
STATE_DIM = 12                          # lin_vel(3) + ang_vel(3) + grav(3) + goal_b(3)
OBS_DIM = STATE_DIM + DEPTH_H * DEPTH_W  # 12 + 7056 = 7068


@configclass
class QuadcopterOsmCityVisionEnvCfg(QuadcopterEnvCfg):
    """Config for vision-PPO in the Manhattan OSM city (866-building, real collision)."""

    # Longer episode: city traverse at ~3-5 m/s takes ~20 s; give 30 s margin.
    episode_length_s: float = 30.0
    decimation: int = 2

    # ---- observation / action layout ----
    # 7068-d flat vector: the VisionPolicy CNN splits the trailing 7056 back
    # into (1, 84, 84) for the depth branch.
    observation_space: int = OBS_DIM
    action_space: int = 4
    state_space: int = 0

    # ---- reward scales (from proven Phase 6a / corridor-v1 values) ----
    distance_to_goal_reward_scale: float = 30.0
    lin_vel_reward_scale: float = -0.02
    ang_vel_reward_scale: float = -0.005
    progress_reward_scale: float = 5.0

    # Hard collision penalty — building contact triggers instant -50 + episode end.
    collision_penalty: float = -50.0
    terminate_on_collision: bool = True

    # Soft proximity penalty: -1/(min_depth² * scale) per step.
    # Encourages the drone to keep at least 1–2 m clearance from buildings.
    proximity_penalty_scale: float = 1.0

    # ---- A → B trajectory (env-local coords; env_origin added at reset) ----
    # Spawn at city centre, 30 m altitude (near top of average Times Sq building).
    # Goal = 100 m east, same altitude (matches Phase 6a Rivermark traverse length).
    spawn_pos: tuple[float, float, float] = (0.0, 0.0, 30.0)
    goal_pos: tuple[float, float, float] = (100.0, 0.0, 30.0)

    # ---- OSM city ----
    # Container path: /assets/ is bind-mounted from host /home/ubuntu/assets/
    city_usd_path: str = "/assets/cities/manhattan_times_sq/city.usd"

    # ---- sensors ----
    # Enable contact reporting on drone body so ContactSensor fires on building hits.
    robot: ArticulationCfg = CRAZYFLIE_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        spawn=CRAZYFLIE_CFG.spawn.replace(activate_contact_sensors=True),
    )

    # RTX scenedb ceiling confirmed on A10G (driver 595, Isaac Sim 6.0.0-rc.22):
    #   16 envs  → OK (smoke test passes)
    #   64 envs  → OK (20% GPU, 7.8 GB VRAM, stable training confirmed)
    #   128 envs → HANG: rtx.scenedb.plugin RangeAllocator grows to 1M-slot cap
    #              then fails to allocate ProjectedAreaCullingData::PerViewState.
    #              Process freezes; GPU stays at 1% utilization forever.
    # Use 64 as the safe ceiling for this driver/sim combination.
    # Future: upgrade to Isaac Sim 6.1+ or Avinash's custom image may raise the cap.
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=64, env_spacing=10.0, replicate_physics=True, clone_in_fabric=True
    )

    # Forward-facing 84×84 depth camera on the drone body.
    # 30 m clip = max useful horizon for city navigation at this scale.
    camera: CameraCfg = CameraCfg(
        prim_path="/World/envs/env_.*/Robot/body/depth_cam",
        update_period=0.0,        # every physics step
        height=DEPTH_H,
        width=DEPTH_W,
        data_types=["distance_to_image_plane"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=15.0,
            focus_distance=400.0,
            clipping_range=(0.05, 30.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.05, 0.0, 0.0),    # 5 cm in front of body origin
            rot=(1.0, 0.0, 0.0, 0.0),
            convention="ros",
        ),
    )

    # Contact sensor — watches drone body for non-zero contact forces.
    contact: ContactSensorCfg = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/body",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
    )
