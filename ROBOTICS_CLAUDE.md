# Robotics Teleoperation B2B — Standalone Session Handoff

**Read this first. This is the active workstream as of 2026-05-21. Self-contained — everything you need is in this file or referenced from it.**

The dance/music project is **paused** (see `CLAUDE.md §19.10`). The drone project is **complete** (see `DRONE_CLAUDE.md`). This is the new main bet.

---

## 1. The 60-second context

**Project goal:** Build a **Quest 3 → robot teleoperation platform** for robotics ML labs and humanoid-robot startups. Capture human demonstration motion via Gurulok Quest app, retarget to specific robot morphologies (Unitree G1, Fourier GR1, Apptronik Apollo, Inspire hand, etc.), output as training data for imitation learning / AMP / GR00T-Mimic.

**Why now:**
- Every major humanoid lab in 2026 is bottlenecked on demonstration data, not algorithms.
- Standard teleop rigs cost $1.5k–50k. Apple Vision Pro setups dominate but are expensive.
- Quest 3 ($499) has the best price/capability ratio: full body + finger tracking + eye gaze + 4MP passthrough.
- We already have the entire Quest → Isaac Lab pipeline from the dance work — pivoting to robotics reuses 70% of the code.
- 200+ robotics labs + 50+ humanoid startups are the addressable market. Each willing to pay $5k–50k/year.

**One-line pitch:** "Quest 3 + our SDK = research-grade teleoperation for 1/10 the cost of Apple Vision Pro setups."

---

## 2. What's already built (reusable from prior work, do NOT redo)

| Asset | Path | Why it transfers to robotics |
|---|---|---|
| Gurulok Quest app | (in VR coding agent's repo) | Captures 84 joints + 52 finger joints + eye gaze in real time |
| `pose_bin_to_amp_motion_v2.py` | `mocap_handoff/` | Quest binary → numpy-friendly motion. Will fork into URDF-target version. |
| `verify_session_v2.py` | `mocap_handoff/` | Session data validator. Reusable for robotics QA. |
| Isaac Lab + AMP infra | EC2 container | Reference simulator for robotics. Same env framework supports manipulation tasks. |
| Daphne CC4 retargeter | `mocap_handoff/bake_daphne_animation.py` | The IK + bone-mapping logic transfers directly to robot retargeting. |
| Drone PPO checkpoint + city training | (in container) | Proof you can train + deploy a 12-DoF system in NVIDIA's sim. Skills transferable. |
| EC2 + Docker setup | `54.84.26.5` (or current IP) | Isaac Sim 6.0 + Isaac Lab 3.0, A10G GPU. Stays the same compute platform. |

---

## 3. Architecture (the new layer to build)

```
┌─────────────────────────────────────────┐
│  Gurulok Quest 3 app (existing)          │
│  Captures: 84 body + 52 finger joints   │
│  Optional: eye gaze, prop emitters      │
└──────────────┬──────────────────────────┘
               │ WebSocket / UDP over WiFi
               │ 60 Hz motion stream
               ▼
┌─────────────────────────────────────────┐
│  PC Bridge (new — Python)                │
│  - Receives motion stream from Quest    │
│  - Real-time retargeter: human → robot  │
│  - URDF-aware IK (Pinocchio / mink)     │
│  - Joint limit + self-collision clamp   │
│  - Publishes ROS 2 topics OR Isaac Lab  │
└──────────────┬──────────────────────────┘
               │
   ┌───────────┼───────────┬───────────┐
   ▼           ▼           ▼           ▼
ROS 2     Isaac Lab    LeRobot HDF5  Real Robot
(rviz,    (sim         (dataset      (eventually)
control)  validation)   recording)
```

The PC Bridge is the new product. The Quest app already exists. The robot interfaces are standard ROS 2 / Isaac Lab / LeRobot. **We build the bridge in the middle.**

---

## 4. Target robot priority (ordered by accessibility + market)

| Robot | DoF | Cost | Why prioritize | NVIDIA support |
|---|---|---|---|---|
| **Unitree G1** (entry humanoid) | 23 + 3-finger gripper | $16k | Cheapest credible humanoid, large community, easy to buy | ✅ Native in Isaac Lab |
| **Unitree G1 + Inspire FTP hands** | 23 + 12/hand | $26k | Adds dexterous fingers — our xr_hands data shines here | ✅ Inspire USD assets in Isaac Sim |
| **Fourier GR1** (29-DoF humanoid) | 44 (with dex hands) | $40k | GR00T-native, NVIDIA partnership angle | ✅ GR00T reference platform |
| **Unitree H1** (full-size humanoid) | 27 | $90k | Stage-presence demos, viral content potential | ✅ |
| **Franka FR3** (research arm) | 7 + gripper | $30k | Bread-and-butter manipulation arm; every lab has one | ✅ Built-in Isaac Lab task templates |
| **Shadow Dexterous Hand** | 24/hand | ~$100k | Only if specializing in dexterous-hand sub-niche | ✅ |
| **Apptronik Apollo** | enterprise humanoid | TBD (pilot pricing) | Enterprise sales path through Mercedes/BMW partnerships | ⚠ Limited public API |
| **Boston Dynamics Atlas / Spot** | enterprise | Not retail | Aspirational, not procurable | ❌ Closed |

**Recommended first target: Unitree G1.** Reasons:
1. Cheapest credible humanoid (can buy one for our own validation)
2. Native NVIDIA Isaac Lab support (USD asset already on EC2)
3. Has community/forum support (mature)
4. Add Inspire hands later as v2 (NVIDIA already ships the combined USD)

**Recommended second target: Franka FR3.** Reasons:
1. Standard research arm — every academic lab has access
2. Smaller scope → faster MVP per robot
3. Manipulation is a separate sub-market from humanoid locomotion

---

## 5. Six-week MVP plan

| Week | Deliverable | Acceptance criteria |
|---|---|---|
| 1 | **Quest → PC motion streaming protocol** (WebSocket or UDP) | Live 60 Hz body + hand data hits a Python script on PC, <50ms latency on local WiFi |
| 2 | **URDF parser + forward kinematics for Unitree G1** | Given a joint state vector, compute end-effector positions; visualize in matplotlib |
| 3 | **IK retargeting: human pose → G1 pose** | Pinocchio + mink (or similar); given a Quest skeleton, output G1 joint angles respecting limits |
| 4 | **Isaac Lab integration** | Stream retargeted G1 commands into Isaac Lab sim; verify G1 in sim mirrors human motion in VR |
| 5 | **LeRobot-compatible dataset recording** | Record episodes to HDF5 in HuggingFace LeRobot format; replay via lerobot CLI |
| 6 | **Beta with 1–2 robotics labs** | Send Quest 3 + SDK to a friendly academic lab; capture 100+ demonstrations; get feedback |

**Tech we already have:** ~70% (Isaac Lab, retargeting logic, mocap parsing, EC2 + GPU)
**Tech we need to build:** ~30% (Quest streaming protocol, URDF IK, ROS 2/LeRobot integration)

---

## 6. EC2 infrastructure (current state)

- **Instance**: `TrigunAI-Omniverse`, us-east-1, g5.2xlarge (A10G 23GB / 31GB RAM / 193GB EBS)
- **Current public IP**: `52.207.20.75` (as of 2026-05-22, changes on stop/start)
- **AMI**: NVIDIA GPU Cloud VM Base 2026.4.1 (`ami-059e868ce2e616dab`)
- **Container**: `isaaclab-v2:custom` (Isaac Sim 6.0 + Isaac Lab 3.0, sleep infinity)
- **Key**: `/tmp/trigunai_key.pem`
- **Services on EC2**: `litellm-proxy` (4000), `ovrtx-rendering-api` (8001), Content Agents, `nginx` (8080), `isaaclab` container (must `docker start` manually)

Robotics teleop runs on the same EC2 (for Isaac Lab sim + training) but **the PC bridge runs on the developer's local Mac**, not on EC2. The Quest streams to local PC for low latency; the PC sends episodes/datasets up to EC2 for batch training.

---

## 7. Resume sequence (do this every session)

```bash
# 1. Start EC2, grab new IP
EC2_IP=<new IP from AWS console>

# 2. Start container (Isaac Sim + Isaac Lab inside)
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP 'sudo docker start isaaclab'

# 3. (Once we have it) start the PC bridge on local Mac
cd /Users/deepakkumarrai/Documents/01_Active/NvidiaSimSetup/robotics_teleop
python3 quest_to_robot_bridge.py --robot unitree_g1 --target sim

# 4. (Optional) cloudflared tunnel for any web UI
ssh -i /tmp/trigunai_key.pem ubuntu@$EC2_IP \
  'pkill cloudflared 2>/dev/null; nohup cloudflared tunnel --url http://localhost:8080 --no-autoupdate > /tmp/tunnel.log 2>&1 &'
```

---

## 8. Skills + reading list to ramp on

**Critical skills (4–6 weeks to ramp):**

| Topic | Resource | Why |
|---|---|---|
| URDF + forward/inverse kinematics | Pinocchio docs; `pin.computeForwardKinematics` examples | Every robot uses URDF; you'll parse/manipulate hundreds |
| mink (or pink) IK library | github.com/kevinzakka/mink | Modern Python IK with QP solvers; standard for retargeting |
| ROS 2 Humble | docs.ros.org/en/humble/Tutorials.html | Standard robotics messaging layer |
| LeRobot framework | github.com/huggingface/lerobot | Emerging open dataset standard for imitation learning |
| Isaac Lab Manipulation envs | `manager_based/manipulation/` in container | Adjacent envs to your existing humanoid_amp work |
| Diffusion Policy | Chi et al. 2023 paper | Current SOTA for robot imitation; needed for credible demos |
| GR00T N1 + Mimic | docs.nvidia.com → GR00T section | NVIDIA's framework; partnership angle |
| Domain randomization (sim-to-real) | Tobin et al. 2017; OpenAI in-hand cube paper | Bridges sim training → real deployment |

**Papers to read (skim ~30 min each):**

1. **Diffusion Policy** (Chi, Feng, Du et al. 2023) — current SOTA for imitation
2. **GR00T N1** (NVIDIA 2024) — humanoid foundation model
3. **Mobile ALOHA** (Stanford 2024) — affordable bimanual teleop reference
4. **OpenVLA** (Stanford 2024) — open vision-language-action model
5. **DexCap** (Stanford 2024) — wearable dexterous-hand capture
6. **HumanPlus** (Stanford 2024) — whole-body humanoid teleop with shadowing
7. **TeleVision** (CMU 2024) — Apple Vision Pro teleop framework (the thing we improve on)
8. **π0** (Physical Intelligence 2024) — generalist robotics model

---

## 9. Hardware to consider adding (in priority order)

| Hardware | Cost | Purpose | When to buy |
|---|---|---|---|
| 3D printer (Bambu A1 mini) | $300 | Custom mounts, fixtures | Week 1 — essential for any real robotics |
| Unitree Go2 quadruped | $1,600 | Cheapest real robot for transfer demos | Week 3–4 (if MVP looks promising) |
| Unitree G1 humanoid | $16,000 | Primary target hardware for sim-to-real | After first paying customer / Q3 2026 |
| Inspire FTP hand (single) | $5,000 | Validate finger transfer on real hardware | After G1 demo lands |
| Quest Pro (in addition to Quest 3) | $1,500 | Face + eye tracking (more obs for some teleop tasks) | Only if customer requests |
| Franka FR3 (used) | $20,000–30,000 | Manipulation arm; standard research platform | If pivoting to manipulation sub-niche |

**Realistic minimum to start (this month):** Bambu printer + nothing else. Software-only MVP is fine for first 6 weeks.

---

## 10. Communities + partnerships to plug into

| Where | Why |
|---|---|
| **NVIDIA Inception** | Free credits + GR00T partner status (you qualify) |
| **HuggingFace LeRobot Discord** | Active robotics community, frequent contributions accepted |
| **ROS Discourse** | Standard robotics community |
| **Twitter: @cremebrule, @gr00t_nvidia, @physical_int, @figure_robot, @1x_tech** | Latest research + product moves |
| **Conferences: RSS, CoRL, ICRA, IROS** | Submission deadlines mostly fall 2026; aim for one paper |
| **Discord: NVIDIA Developer Robotics, ROS, IsaacLab** | Direct line to NVIDIA engineers |
| **Stanford / CMU / MIT robotics labs** | Cold-email PIs once we have a working MVP demo video |

---

## 11. Business angle (the B2B sales motion)

**Customer profile:** robotics research lab (academic or corporate R&D) needing demonstration data for imitation learning. Specifically:

- Humanoid robot startups (Figure, 1X, Apptronik, Sanctuary, Mentee Robotics, ~20 others)
- Dexterous manipulation labs (Shadow, Inspire, Reflex)
- Academic robotics labs (Stanford ROS lab, CMU RI, MIT CSAIL, Berkeley BAIR, ~100 worldwide)
- NVIDIA partner ecosystem (Inception + GR00T launch partners)

**Initial pricing experiments:**
- Open-source SDK (free) → drive adoption + GitHub stars
- Commercial cloud dataset hosting + retargeting credits: $500–5,000/mo per lab
- Enterprise: custom robot URDFs + onboarding services, $20–100k per engagement
- Partnership revenue share: with NVIDIA / robot manufacturers

**First 5 customers (concrete target list):**
1. NVIDIA GR00T team (free / partnership; can intro via Inception)
2. Stanford ALOHA team (academic, has Quest 3s already)
3. HuggingFace LeRobot team (community / open-source partnership)
4. Mentee Robotics or Sanctuary AI (smaller humanoid startup, less locked-in to existing rigs)
5. One academic lab in India (UAlmaCST Bangalore robotics, IIT Delhi) — easier intro path

---

## 12. What this session should NOT touch

- Dance / music / AMP humanoid work — **paused**, lives in `CLAUDE.md §19`
- Daphne CC4 retargeter — frozen; will fork into a robot retargeter, original stays for dance resume
- WebXR dance showcases — stay live, no updates
- Drone pipeline — complete, lives in `DRONE_CLAUDE.md`
- Any `*music*` or `*daphne*` file edits

If a customer asks about consumer dance/VTuber: politely defer ("we built that as a tech demo; now focused on robotics; happy to discuss later").

---

## 13. First concrete deliverable for THIS week

**Build the Quest → PC motion streaming protocol** (Week 1 from §5).

Why first:
- Unblocks every other deliverable downstream
- Tests the most uncertain piece (latency, WiFi reliability)
- Doesn't require a robot — just Quest + Mac
- Aligns with existing Gurulok app team's expertise

**Concrete sub-tasks:**
1. Choose protocol — WebSocket (easy, JSON) vs UDP (lower latency, binary). **Decision: start with WebSocket for dev speed; benchmark UDP if latency >50ms.**
2. Define message schema — frame timestamp + 84 body joints + 52 finger joints + (optional) eye gaze.
3. Implement Quest sender (work with VR coding agent on Gurulok side).
4. Implement Python receiver on Mac (this side).
5. Latency benchmark: target <50ms end-to-end on local 5GHz WiFi.

**Deliverable for end of week:** Mac terminal showing live 60 Hz motion data from Quest user, with timestamps confirming <50ms latency. Plot the wrist position in real time as proof.

---

*Last updated: 2026-05-21 — Pivoted to robotics teleoperation B2B from dance/music. Week 1 deliverable in progress.*
*Owner: TrigunAI Innovations (Deepak + Avinash).*
