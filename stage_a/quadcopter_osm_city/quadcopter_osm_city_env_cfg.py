# Quadcopter A->B in OSM-derived city — env config.
# Fork of QuadcopterCityA2BEnvCfg with: real collision (we don't strip the
# city's collision APIs), ContactSensor on drone body, smaller num_envs
# (collision is GPU-heavier than visual-only scenery).

from __future__ import annotations

from isaaclab.assets import ArticulationCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from isaaclab_assets import CRAZYFLIE_CFG
from isaaclab_tasks.direct.quadcopter_city_a2b.quadcopter_city_a2b_env_cfg import (
    QuadcopterCityA2BEnvCfg,
)


@configclass
class QuadcopterOsmCityEnvCfg(QuadcopterCityA2BEnvCfg):
    # OSM city is much smaller (≤900 convex-hull collidables vs Rivermark's
    # 12k+ triangle meshes), but real collision is still heavier than the
    # visual-only Rivermark setup. Start at 256; raise once stable.
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=256, env_spacing=10.0, replicate_physics=True, clone_in_fabric=True
    )

    # Enable contact reporting on the Crazyflie body so ContactSensor can
    # observe collisions with buildings. Without this the USD physics layer
    # doesn't register contact callbacks.
    robot: ArticulationCfg = CRAZYFLIE_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        spawn=CRAZYFLIE_CFG.spawn.replace(activate_contact_sensors=True),
    )

    # Path the env will reference into /World/City. Pre-baked by:
    #   osm_to_usd.py + city_add_colliders.py.
    # Container-internal path; on the host this is /home/ubuntu/assets/cities/...
    city_usd_path: str = "/assets/cities/manhattan_times_sq/city.usd"

    # A → B in env-local coords. z = 30 m sits at Times Sq mean building height,
    # so the drone genuinely has to dodge taller towers. 100 m horizontal traverse
    # matches the proven Phase 6a Rivermark setup so we can compare apples-to-apples.
    spawn_pos: tuple[float, float, float] = (0.0, 0.0, 30.0)
    goal_pos: tuple[float, float, float] = (100.0, 0.0, 30.0)

    # Collision termination + penalty (mirrors corridor-v1)
    collision_penalty: float = -50.0
    terminate_on_collision: bool = True

    # Contact sensor on drone body
    contact: ContactSensorCfg = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/body",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
    )

    # Subclass UI window class
    ui_window_class_type = "{DIR}.quadcopter_osm_city_env:QuadcopterOsmCityEnvWindow"
