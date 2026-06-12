"""
Isaac-Quadcopter-OSM-City-Vision-v0

Crazyflie drone navigating Manhattan/Times Square (866 OSM-derived
buildings, convex-hull collision) with a forward-facing 84×84 depth
camera. First Tier-2 / Stage A environment with real urban obstacle
collision and real vision sensing — the ground truth the blind OSM
city env was missing.

Architecture
------------
obs  = [lin_vel(3) | ang_vel(3) | grav(3) | goal_b(3) | depth(84×84)]
     = 7068-dimensional flat vector
act  = 4 thrust commands (same as base Quadcopter env)
net  = VisionPolicy/VisionValue from quadcopter_corridor_v1.networks_vision
       (shared-trunk CNN + state MLP, 128-dim feature concat)
algo = skrl PPO (scripts/train_osm_city_vision.py)

Sim2real path
-------------
Depth camera → switch to multi-ranger deck (5 ToF rays) on real Crazyflie
for lowest sim2real gap. Dense depth → RealSense D405 on bigger platform.
"""

import gymnasium as gym

gym.register(
    id="Isaac-Quadcopter-OSM-City-Vision-v0",
    entry_point=f"{__name__}.quadcopter_osm_city_vision_env:QuadcopterOsmCityVisionEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.quadcopter_osm_city_vision_env_cfg:QuadcopterOsmCityVisionEnvCfg",
    },
)
