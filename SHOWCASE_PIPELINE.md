# Showcase Pipeline — Rendered MP4 of Phase 6a Drone in Rivermark

> Self-contained doc. A fresh session can execute this without reading anything else in the repo.
> Goal: produce a high-quality MP4 of the trained PPO drone flying through Rivermark city, viewable in Quest browser as a 2D video.

**Owner:** TrigunRoboticsLab
**Status:** Pipeline validated; one chase-camera fix needed to land the final render.
**Last updated:** 2026-05-23

---

## 1. Why this exists

The Phase 6a checkpoint trains a Crazyflie to fly A→B in NVIDIA Rivermark city. The trajectory is exported as `cf2x_city_a2b_v7.glb` (264 KB animated GLB) and the city is decimated to `rivermark_lite.glb` (640 MB GLB). For showcase use:

- **What we want**: a polished MP4 of drone-flying-through-Rivermark, hostable, viewable in Quest browser
- **What we tried tonight that didn't work**: NVIDIA Omniverse Kit + RTX headless rendering (NVIDIA gates this behind Omniverse Enterprise), LÖVR + CloudXR (Vulkan headless wall), Isaac Lab CloudXR teleoperation (live-control only, needs display)
- **What works**: **Blender 4.5 Eevee Next, headless on us-east-1 g5.2xlarge A10G.** Validated 2026-05-23 — 5 smoke frames at 1280×720, ~12 GB RAM steady, no crashes.

Live VR streaming is blocked behind NVIDIA Enterprise gates we don't have. **Rendered MP4 is the realistic showcase artifact** until Omniverse Enterprise lands.

---

## 2. State of us-east-1 (`TrigunAI-Omniverse`)

Everything you need is already on EBS. Survives stop/start. As of 2026-05-23:

| Asset | Path |
|---|---|
| Blender 4.5.5 LTS | `/opt/blender45/blender` |
| Decimated Rivermark | `/var/www/showcase/assets/rivermark_lite.glb` (640 MB, 7.25M tris) |
| Animated drone GLB | `/var/www/showcase/assets/cf2x_city_a2b_v7.glb` (264 KB, 360 frames @ 24 fps) |
| Crazyflie source USD | `/home/ubuntu/cf2x.usd` |
| Existing render script (needs chase-cam fix) | `/home/ubuntu/blender_render.py` |
| Smoke render output (proof of concept) | `/home/ubuntu/render_out_useast/frame_{0,60,180,270,359}.png` |

Container `isaaclab-v2:custom` does NOT need to be running for the render pipeline (Blender is on the host).

**To resume work**: start the EC2 instance from the AWS console (Instance ID `i-047ebf759f2386e71`), get the new public IP, SSH in. No additional setup required.

---

## 3. The one open issue: chase camera

The current `blender_render.py` uses a **static** camera at `(-30, -120, 80)` looking at the trajectory midpoint `(60, 2.5, 24)`. With the drone scaled 25× to its Isaac native size (~25 cm fuselage × 5× embedded scale = ~1.25 m wide), at the ~150 m camera distance, the drone is **3–5 pixels** in the 1280×720 frame. You can't see it. The smoke render shows the city correctly but the drone is invisible.

**Fix**: replace the static camera with a Track-To constraint that follows the Drone empty, OR position the camera closer + use a Damped Track for a chase-cam feel.

Two camera options, pick one:

### Option A — Static "third-person follow" (simpler)
Camera ~15 m behind and ~5 m above the drone, Track-To constraint pointed at Drone empty.

```python
# at the bottom of blender_render.py, replacing the existing camera block:
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 35
cam_data.clip_end = 5000.0
cam_obj = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Parent camera to drone with an offset so it follows
cam_obj.parent = drone
cam_obj.location = (-15.0, 0.0, 5.0)   # 15 m behind (-X), 5 m above (+Z) in drone local

# Track-To constraint pointed at drone empty itself
track = cam_obj.constraints.new("TRACK_TO")
track.target = drone
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
```

This gives a steady third-person chase shot. The drone always centered, city moving past behind it.

### Option B — Cinematic orbit (more impressive but slower to set up)
Camera dollies along a curve while looking at the drone. Better for marketing reel.
Use a Bezier curve, parent camera to a constraint that lerps along the curve.

**Recommend Option A** for the first MP4. Once that ships, iterate.

---

## 4. Execution recipe

Resumes from a fresh us-east-1 instance start.

### 4.1 Verify state (1 min)

```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
ls -la /opt/blender45/blender                                           # Blender 4.5
ls -la /var/www/showcase/assets/{rivermark_lite,cf2x_city_a2b_v7}.glb   # both GLBs
ls -la /home/ubuntu/blender_render.py                                   # the script
'
```

If anything's missing → see §6 recovery.

### 4.2 Patch in the chase camera (1 min)

Edit `/home/ubuntu/blender_render.py` — find the `# ─── camera ───` section, replace with Option A from §3 above. Or scp a fresh version up from your Mac.

### 4.3 Smoke test (3-5 min)

```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
rm -rf /home/ubuntu/render_out_useast
/opt/blender45/blender --background --python /home/ubuntu/blender_render.py -- smoke 2>&1 | tail -20
ls -la /home/ubuntu/render_out_useast/
'
```

Pull frame 0 and frame 180 to your Mac:
```bash
scp -i /tmp/trigunai_key.pem ubuntu@<NEW_IP>:/home/ubuntu/render_out_useast/frame_{0000,0180}.png /tmp/
```

Open them. **Drone should be clearly visible** in the center of frame at both timesteps, with different city geometry passing behind. If drone is still invisible, camera offset is wrong — adjust `(-15, 0, 5)` to closer / different angle.

### 4.4 Full render (30-60 min)

```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
rm -rf /home/ubuntu/render_out_useast
nohup /opt/blender45/blender --background --python /home/ubuntu/blender_render.py > /home/ubuntu/render.log 2>&1 &
echo "PID: $!"
'
```

Render runs in background. Monitor progress:
```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
ls /home/ubuntu/render_out_useast/ | wc -l   # frames written so far
tail -5 /home/ubuntu/render.log               # latest progress
free -h | head -2                             # memory sanity
'
```

Eevee Next on A10G renders 1280×720 at 64 TAA samples in ~5-10 s/frame. **360 frames ≈ 30-60 min wall time.**

### 4.5 Encode MP4 (1 min)

```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
cd /home/ubuntu/render_out_useast
ffmpeg -y -framerate 24 -i frame_%04d.png \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" \
  /home/ubuntu/drone_in_rivermark.mp4
ls -la /home/ubuntu/drone_in_rivermark.mp4
'
```

CRF 18 = visually lossless for our purposes. Expect ~20-50 MB MP4.

### 4.6 Host + share (1 min)

```bash
ssh -i /tmp/trigunai_key.pem ubuntu@<NEW_IP> '
sudo cp /home/ubuntu/drone_in_rivermark.mp4 /var/www/showcase/assets/drone_in_rivermark.mp4
sudo chmod 644 /var/www/showcase/assets/drone_in_rivermark.mp4
# start cloudflared tunnel for public URL
pkill cloudflared 2>/dev/null
nohup cloudflared tunnel --url http://localhost:8080 --no-autoupdate > /tmp/tunnel.log 2>&1 &
sleep 8
grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/tunnel.log | head -1
'
```

The printed URL + `/assets/drone_in_rivermark.mp4` is your demo link. View in any browser, Quest browser, share on social.

### 4.7 Pull MP4 to Mac (for backup / further editing)

```bash
scp -i /tmp/trigunai_key.pem ubuntu@<NEW_IP>:/home/ubuntu/drone_in_rivermark.mp4 ~/Downloads/
```

### 4.8 Stop EC2 to halt spend

After the MP4 is hosted + downloaded, stop the instance from the AWS console. The MP4 stays at `/var/www/showcase/assets/` on EBS; nginx still serves it whenever the instance is up.

---

## 5. Quality tuning (later iterations)

What to bump if the first MP4 isn't impressive enough:

| Setting | Current | Bump to | Cost |
|---|---|---|---|
| Resolution | 1280×720 | 1920×1080 | ~2× render time |
| TAA samples (Eevee anti-aliasing) | 64 | 128 | +30% render time |
| Sky / ambient lighting | flat ambient | HDRI environment (download from polyhaven.com) | +5 min setup, marginal render cost |
| Sun shadows | disabled | enabled, soft shadows, 512 resolution | +20% render time |
| Bloom | off | on (Eevee Next has good bloom) | negligible |
| Volumetric atmosphere | off | thin volumetric for city haze | +10% render time |

If you want path-traced quality (true RTX-style realism), switch to Cycles + OptiX — but Cycles will OOM with the full rivermark_lite.glb (Phase 2 testing on Mumbai box confirmed this on g5.2xlarge). Would need:
- Further decimate Rivermark to ~500 K tris (another 30-60 min Blender prep job, similar to how the 7.25M version was made)
- Or upsize the EC2 instance to g5.4xlarge or g5.8xlarge for more RAM

**Don't pursue Cycles for the first MP4** — Eevee at 1080p with HDRI looks great and ships tonight.

---

## 6. Recovery — if EBS state is gone

If the persistent assets aren't on us-east-1 (instance was terminated, EBS deleted), rebuild:

| Lost | How to recreate |
|---|---|
| Blender 4.5 | `wget https://download.blender.org/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz`, extract to `/opt/blender45/`, `sudo chmod -R a+rx /opt/blender45` |
| `rivermark_lite.glb` | Re-run the Phase 2 decimation pipeline (see `DRONE_CLAUDE.md` §13 / the chat log of 2026-05-22). Or scp from local: `/Users/deepakkumarrai/Downloads/rivermark_lite.glb` |
| `cf2x_city_a2b_v7.glb` | Re-bake via `webxr-showcase/scripts/usd_to_glb.py --inject-trajectory` (see `DRONE_CLAUDE.md` §3). Or scp from local: `/Users/deepakkumarrai/Downloads/cf2x_city_a2b_v7.glb` |
| `blender_render.py` | Recreate from §3 of this doc + the Eevee-Next config template in `DRONE_CLAUDE.md` §13 |

---

## 7. Acceptance criteria

The showcase MP4 is "done" when:

- ✅ Drone is clearly visible at every timestep (no <5px renders)
- ✅ The city geometry is visible behind/around the drone (not just floating in void)
- ✅ Camera motion is smooth (no abrupt cuts, no jitter)
- ✅ Animation plays the full 360 frames (15 s @ 24 fps)
- ✅ No render artifacts (missing textures, NaN pixels, freeze frames)
- ✅ MP4 plays cleanly in Chrome, Safari, Quest browser
- ✅ File size ≤100 MB (for easy sharing / embedding)

---

## 8. Where the MP4 goes next (out of scope for this doc)

Once the MP4 is shipped, downstream use cases:

- **TrigunRoboticsLab landing page** (per the agent prompt in earlier work): embed as the drone project's hero clip
- **Demo reel for investors / press**: 15 s is the right length for short attention spans
- **Social media (LinkedIn / X)**: clip + caption explaining the trained policy
- **Conference talks**: project on screen during robotics-RL talks
- **Quest 3 native experience (separate from this MP4)**: see the Unity project work tracked in `CLAUDE (2).md` (the GurulokInnerJourney handoff) for the standalone APK path

The MP4 itself is the artifact; how it's used is product/marketing work, not pipeline engineering.

---

*This doc is the explicit "produce an MP4 demo" runbook. Hand to anyone — they can execute end-to-end in 1-2 hours from a stopped us-east-1 instance.*

*Companion docs: `DRONE_CLAUDE.md` (overall drone-work session entry), `DRONE_TIER2_ROADMAP.md` (next training workstream, vision-RL with collision avoidance).*
