"""Get humanoid rest-pose by instantiating the env directly.

Run inside isaaclab container:
  ./isaaclab.sh -p get_rest_pose.py --headless
"""
import numpy as np
import sys

from isaacsim import SimulationApp
app = SimulationApp({"headless": True})

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
import torch
import warp as wp

# Use a simple scene setup — spawn humanoid directly (not via env)
sim_cfg = sim_utils.SimulationCfg(dt=1.0/120.0, render_interval=1)
sim = sim_utils.SimulationContext(sim_cfg)

spawn_ground_plane("/World/ground", GroundPlaneCfg())

# Load the humanoid config from AMP task
sys.path.insert(0, "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/direct/humanoid_amp")
from humanoid_amp_env_cfg import HumanoidAmpEnvCfg

amp_cfg = HumanoidAmpEnvCfg()
robot_cfg = amp_cfg.robot

# Override the prim path to a non-regex path
robot_cfg.prim_path = "/World/Robot"

robot = Articulation(robot_cfg)

# Play the sim
sim.reset()
robot.reset()

# Step to let physics settle
for _ in range(10):
    sim.step()
    robot.update(sim.cfg.dt)

joint_names = list(robot.data.joint_names)
body_names = list(robot.data.body_names)

# Read current state (should be near rest pose since default joint pos is applied)
jp = wp.to_torch(robot.data.joint_pos)[0].cpu().numpy()
default_jp = wp.to_torch(robot.data.default_joint_pos)[0].cpu().numpy()
bq = wp.to_torch(robot.data.body_quat_w)[0].cpu().numpy()   # (N_bodies, 4) wxyz
bp = wp.to_torch(robot.data.body_pos_w)[0].cpu().numpy()

# Also set DOFs explicitly to zero and read again
zero_pos = torch.zeros(1, len(joint_names), device=robot.device)
zero_vel = torch.zeros(1, len(joint_names), device=robot.device)
env_ids = torch.tensor([0], device=robot.device)
robot.write_joint_position_to_sim_index(position=zero_pos, env_ids=env_ids)
robot.write_joint_velocity_to_sim_index(velocity=zero_vel, env_ids=env_ids)

for _ in range(5):
    sim.step()
    robot.update(sim.cfg.dt)

bq_zero = wp.to_torch(robot.data.body_quat_w)[0].cpu().numpy()
bp_zero = wp.to_torch(robot.data.body_pos_w)[0].cpu().numpy()
jp_zero = wp.to_torch(robot.data.joint_pos)[0].cpu().numpy()

print("=" * 60)
print("HUMANOID REST-POSE EXTRACTION")
print("=" * 60)
print(f"Joint names ({len(joint_names)}):", joint_names)
print(f"Body names ({len(body_names)}):", body_names)
print(f"Default joint pos: {np.array2string(default_jp, precision=6, separator=', ')}")
print(f"Joint pos after zero write: {np.array2string(jp_zero, precision=6, separator=', ')}")
print()
print("Body poses at DOF=0 (rest pose):")
for i, name in enumerate(body_names):
    q = bq_zero[i]  # wxyz
    q_xyzw = np.array([q[1], q[2], q[3], q[0]])  # xyzw for our npz format
    print(f"  {i:2d} {name:>15s}: wxyz=[{q[0]:.6f},{q[1]:.6f},{q[2]:.6f},{q[3]:.6f}]  xyzw=[{q_xyzw[0]:.6f},{q_xyzw[1]:.6f},{q_xyzw[2]:.6f},{q_xyzw[3]:.6f}]  pos={bp_zero[i].round(4)}")

np.savez("/tmp/humanoid_rest_state.npz",
         joint_names=np.array(joint_names),
         body_names=np.array(body_names),
         default_joint_pos=default_jp,
         rest_body_quat_wxyz=bq_zero,
         rest_body_quat_xyzw=np.stack([bq_zero[:, 1], bq_zero[:, 2], bq_zero[:, 3], bq_zero[:, 0]], axis=-1),
         rest_body_pos=bp_zero)
print("\nSaved /tmp/humanoid_rest_state.npz")

app.close()
