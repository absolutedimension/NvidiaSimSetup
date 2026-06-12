#!/usr/bin/env python3
"""Create a Starling 2 USD from the Crazyflie template with updated mass/inertia.

Run inside the isaaclab container:
    cd /workspace/isaaclab && ./isaaclab.sh -p /workspace/isaaclab/cinematography/create_starling2_usd.py
"""
import os
import shutil

from pxr import Gf, Usd, UsdPhysics

SRC = "/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/cf2x.usd"
DST_DIR = "/workspace/isaaclab/cinematography"
DST = os.path.join(DST_DIR, "starling2.usd")

os.makedirs(DST_DIR, exist_ok=True)
shutil.copy2(SRC, DST)

src_cfg = "/tmp/Assets/Isaac/6.0/Isaac/Robots/Bitcraze/Crazyflie/configuration"
dst_cfg = os.path.join(DST_DIR, "configuration")
if os.path.isdir(src_cfg) and not os.path.isdir(dst_cfg):
    shutil.copytree(src_cfg, dst_cfg)

stage = Usd.Stage.Open(DST)
body_prim = stage.GetPrimAtPath("/crazyflie/body")

mass_api = UsdPhysics.MassAPI.Get(stage, body_prim.GetPath())
if not mass_api:
    mass_api = UsdPhysics.MassAPI.Apply(body_prim)

# Starling 2: 280g, 132x176mm rectangular frame
m = 0.28
w, d, h = 0.132, 0.176, 0.04
Ixx = (1 / 12) * m * (d**2 + h**2)
Iyy = (1 / 12) * m * (w**2 + h**2)
Izz = (1 / 12) * m * (w**2 + d**2)

mass_api.GetMassAttr().Set(m)
mass_api.GetDiagonalInertiaAttr().Set(Gf.Vec3f(Ixx, Iyy, Izz))

stage.Save()

print(f"Saved Starling 2 USD: {DST}")
print(f"Mass: {m} kg")
print(f"Inertia: Ixx={Ixx:.6f}, Iyy={Iyy:.6f}, Izz={Izz:.6f}")
print(f"Frame: {w*1000:.0f}x{d*1000:.0f}mm, thrust class: ~2.5N/motor")
