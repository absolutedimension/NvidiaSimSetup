# Drone Training Pipeline — Where I'm Stuck

**From:** Deepak
**To:** Avinash
**Date:** 2026-05-17
**Re:** Drone-A-to-B Isaac Lab pipeline setup

---

## TL;DR

I followed your direction to set up the drone training pipeline on AWS (Isaac Lab + rl_games PPO, same shape as the Franka work). **Training works perfectly.** But **every Isaac Sim viewport / video render path crashes** on the brand-new EC2 box I built — and on the official NVIDIA Isaac Lab container too. Driver 595 vs Isaac Sim 4.5 hard incompatibility.

While debugging, I logged into our existing `TrigunAI-Omniverse` and found **you've already solved this exact problem** — you built a custom `isaaclab-v2:custom` Docker image based on **Isaac Sim 5.1.0 + Isaac Lab 3.0.0-beta1** (newer than what I was using), plus custom env config + render scripts that use `TiledCameraCfg` (offscreen camera) instead of the broken viewport widget.

**I need you to confirm the pipeline before I copy your approach to my drone box.** Specifics below.

---

## 1. What I set out to do

Per your direction:

- Train a quadcopter policy in Isaac Sim simulation to fly from Point A to Point B in a city scene
- Pipeline shape: cloud AWS GPU → Isaac Lab env → rl_games PPO → headless training → visual eval over NICE DCV
- Drone choice: probably Crazyflie (already wired into `Isaac-Quadcopter-Direct-v0`); confirm with you before first real run
- City scene: bundled Nucleus asset to start; confirm with you

---

## 2. AWS box I built

| Field | Value |
|---|---|
| Name | `TrigunAI-DroneIsaac-v2` |
| Instance ID | `i-01d3700be5abc143a` |
| Type | g5.2xlarge (A10G, 24 GB VRAM, 32 GB RAM) |
| Region | us-east-1 (same as your `TrigunAI-Omniverse`) |
| AMI | NVIDIA GPU Cloud VMI Base 2026.4.1 (`ami-059e868ce2e616dab`) — same AMI as `TrigunAI-Omniverse` |
| Elastic IP | `34.235.182.87` (permanent) |
| Storage | 300 GiB gp3 root + 450 GiB ephemeral NVMe |
| Termination protection | Enabled |
| State | **Currently stopped** (so I'm not burning cloud time while you read this) |

Quota note: us-east-1 G/VT vCPU quota is 8 — so this box and `TrigunAI-Omniverse` can't run at the same time. Quota increase request 8→16 still pending AWS approval.

---

## 3. What works

**Headless PPO training on `Isaac-Quadcopter-Direct-v0` (Crazyflie env):**

- ~370,000 steps/sec on the A10G
- Checkpoint saves to `.pth` correctly
- Validated end-to-end with 20-epoch smoke run, reward curve started moving

Setup that produced this: Native Isaac Lab v2.3.2 + Isaac Sim 4.5 + PyTorch 2.5.1 cu118 in a conda env (Python 3.10), installed via pip from NVIDIA's `pypi.nvidia.com`.

---

## 4. What's broken — the core problem

**Every code path that renders pixels crashes** with the same stack trace:

```
File "/isaac-sim/extscache/omni.kit.widget.viewport-107.0.7/omni/kit/widget/viewport/impl/texture.py",
  line 377 in __enable_hydra_engine
[Warning] [rtx.scenedb.plugin] SceneDbContext: TLAS limit buffer size 7512601600
[Warning] [rtx.scenedb.plugin] SceneDbContext: TLAS limit: valid true, within false
Fatal Python error: Segmentation fault
```

The `rtx.scenedb` plugin can't allocate its top-level acceleration structure on the GPU. This crashes:

- Live viewport (`./isaaclab.sh -s`) → crash
- Headless + `--video` flag → crash
- Tutorial `create_empty.py` → crash
- Same crash inside the **official `nvcr.io/nvidia/isaac-lab:2.0.2` container**
- Same crash inside the **older `nvcr.io/nvidia/isaac-sim:4.2.0` container**

Only difference between native and container is the wrapper — the crash itself happens in NVIDIA's pinned plugin code, which talks to the host kernel's NVIDIA driver. The container can't override the host driver.

**Root cause:** NVIDIA driver 595.58.03 (released April 2026, what AWS now bundles in every NVIDIA AMI) has a hard incompatibility with `omni.kit.widget.viewport-107.0.7` + `rtx.scenedb` from Isaac Sim 4.5 and 4.2. NVIDIA hasn't documented this anywhere I can find.

I disabled ECC on the A10G (`nvidia-smi -e 0` + reboot) on the off chance — no fix.

---

## 5. What I tried before giving up

| Attempt | Result |
|---|---|
| AMI A: AWS Deep Learning Base AMI Ubuntu 24.04 + native Isaac Sim 4.5 | Headless ✅, viewport ❌ crash |
| Disabled ECC, rebooted, retried | Same crash |
| AMI B: NVIDIA GPU Cloud VMI 2026.4.1 (same as your box) + container | Headless ✅, viewport ❌ crash |
| Container: `nvcr.io/nvidia/isaac-lab:2.0.2` | Same crash |
| Container: `nvcr.io/nvidia/isaac-sim:4.2.0` (older, pre-bug) | Same crash |
| Symlinked missing `libnvidia-egl-wayland.so.1.1.13` to fix toolkit/driver mismatch | Container ran, but RTX still crashed |

After 4+ hours and ~$8 of cloud time, headless training works at full speed and **every visual eval path is broken**.

---

## 6. The breakthrough — your existing solution on `TrigunAI-Omniverse`

I started `TrigunAI-Omniverse` to compare drivers (it's the same AMI). Driver is identical (595.58.03, ECC enabled). But in `/home/ubuntu/` I found:

```
~/render_v2_video.py
~/render_v3_video.py
~/render_v4_video.py             ← latest, 194 lines
~/render_wrist_camera_video.py
~/run_franka_play.sh             ← your runner shell script
~/joint_pos_camera_env_cfg.py    ← your custom env with camera
~/camera_tasks_append.py         ← task registration
~/rl_games_camera_ppo_cfg.yaml   ← PPO config
~/franka_lift_camera_best.mp4    ← rendered output (it worked!)
~/franka_lift_camera_v2.mp4
~/franka_v2_front.mp4
~/franka_v2_split.mp4
~/franka_v2_wrist.mp4
~/franka_v2_thirdperson.mp4
~/franka_v2_v4cam.mp4
~/franka_v2_front3q.mp4
~/v2_frames / v3_frames / v4_frames / v4_frames_front / etc.  ← rendered frame dirs
```

Docker images cached on the box:

```
isaaclab-v2:custom                          25.1 GB   ← your custom build
nvcr.io/nvidia/isaac-lab    3.0.0-beta1    22.7 GB
nvcr.io/nvidia/isaac-sim    5.1.0          15.1 GB
```

Docker container `isaaclab` exists but is **Exited (137) 42 hours ago**.

### Reading `run_franka_play.sh`:

```bash
sudo docker exec -it isaaclab bash -lc \
  "cd /workspace/isaaclab && \
   ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/play.py \
   --task Isaac-Lift-Cube-Franka-Camera-Play-v0 \
   --num_envs 1 --enable_cameras --viz kit \
   --checkpoint /workspace/isaaclab/logs/.../franka_lift_camera_v2.pth"
```

### Reading `render_v4_video.py`:

- Uses `from isaaclab.app import AppLauncher`
- `args_cli.headless = True; args_cli.enable_cameras = True` — **headless + offscreen cameras**
- Uses `from isaaclab.sensors import TiledCameraCfg`
- Camera reads frames as tensors, saves via PIL to `--out_dir`
- Then ffmpeg encodes to MP4

**This is the workaround.** `TiledCameraCfg` is an offscreen camera sensor backed by Replicator. It **does not load `omni.kit.widget.viewport`**, so the broken plugin never initializes. You bypass the crash entirely.

I jumped over the fix — I went *backward* to Isaac Sim 4.2 (also broken). The fix is forward, in **Sim 5.1.0 + Lab 3.0.0-beta1**, and your `isaaclab-v2:custom` image presumably layers your custom env on top.

---

## 7. What I'm asking you to confirm

Before I copy your approach to my drone box, please confirm:

1. **Image strategy** — Should I:
   - (a) pull `nvcr.io/nvidia/isaac-lab:3.0.0-beta1` fresh on my drone box and layer my drone env config on top, OR
   - (b) export your `isaaclab-v2:custom` image, transfer it, and use it as the base (faster, but inherits any Franka-specific bits)
   - (c) something else
2. **Pipeline pattern** — Is the pattern below what you actually used? If not, please correct:
   - Train headless without cameras (fast — pure physics)
   - Save `.pth` checkpoint
   - Run play.py with `--enable_cameras` + a custom env that adds `TiledCameraCfg` at a chosen camera angle
   - Replicator captures frames per step → saves PNGs
   - ffmpeg frames → MP4
   - View MP4 in DCV browser (or `scp` it down)
3. **Drone env** — Want me to fork `Isaac-Quadcopter-Direct-v0` into `Isaac-Quadcopter-Camera-Play-v0` (mirroring your Franka-Camera-Play-v0 pattern)? Or do you already have a quadcopter-camera env on `TrigunAI-Omniverse` that I missed?
4. **City scene** — Did you commit to a specific Nucleus USD city scene for the drone task, or is that still open?
5. **Operating mode** — Are you OK with me starting my drone box (us-east-1) to do this, or do you want me to wait for the quota increase 8→16 so we can both run side-by-side? Right now if my box runs, yours can't (and vice versa).

---

## 8. Cost picture (so far)

| Item | Spend |
|---|---|
| Drone box compute (TrigunAI-DroneIsaac-v2, ~4 hrs) | ~$4.80 |
| EBS storage (300 GiB gp3) while stopped | ~$32/month accrual |
| Elastic IP (attached to stopped instance) | ~$3.60/month accrual |
| Container downloads (35 GB pulled, free from NGC) | $0 |
| **Cash burn this session** | ~$5 |

The drone box is currently stopped. I won't restart it until you reply.

---

## 9. What I have ready to go (so this isn't a total restart for you)

On the drone box (which is stopped but everything is on the EBS):

- ✅ Ubuntu 24.04 + NVIDIA driver 595 + CUDA toolkit
- ✅ NICE DCV server installed + configured (port 8443, with the QUIC/UDP rule in the security group)
- ✅ MATE desktop + GDM with Xorg (NOT Wayland — required for DCV+GPU)
- ✅ Miniconda + `isaaclab` env (Python 3.10) + PyTorch 2.5.1 cu118
- ✅ Isaac Sim 4.5.0 (via pip, native) — **don't use this; deprecated by your container**
- ✅ Isaac Lab v2.3.2 — **also deprecated**
- ✅ rl_games installed
- ✅ Headless training validated: 370k FPS PPO on `Isaac-Quadcopter-Direct-v0`
- ✅ Docker + NVIDIA Container Toolkit
- ✅ `nvcr.io/nvidia/isaac-lab:2.0.2` container pulled (~16 GB) — **also deprecated**

What I need to do once you confirm:
1. Pull `nvcr.io/nvidia/isaac-lab:3.0.0-beta1` (or import your custom image)
2. Adapt your render scripts: Franka → Quadcopter
3. Decide drone + scene; first PPO run; visual eval over DCV with MP4

---

## 10. One last note — handoff doc

`drone_training_pipeline_setup.md` (the setup guide you mentioned) — I never received it, or I don't know where it lives. If it's in our shared folder somewhere, please point me to it. If it doesn't exist yet and the working pattern is just "what's on `TrigunAI-Omniverse`", that's fine — I can reverse-engineer it from your scripts. But knowing whether there's a doc avoids me rebuilding what you already wrote down.

---

**Quickest unblock:** a 5-line reply confirming the image choice (3.0.0-beta1 fresh vs. your custom export) and whether to spin up my box now or wait for quota. The rest I can figure out from your scripts.

Thanks — sorry for the saga, but the upside is the drone box is fully provisioned and ready to roll once you nod yes.

— Deepak
