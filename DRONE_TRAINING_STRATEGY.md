# Drone Training Strategy — From Hover to A→B in a City

> The canonical roadmap for the TrigunAI drone-training pipeline.
> Read top-to-bottom once. Then use it as a checklist.
> Owner: Deepak Rai. Last revised: 2026-05-18, after Phase 1's first ship-it.

---

## 0. North Star

> A trained PPO policy that flies a Crazyflie quadcopter from Point A to Point B inside a city scene with buildings, avoiding collisions, taking a roughly direct path. Visual eval inside our Quest 3 app (GurulokInnerJourney) on every iteration.

Three properties we want at the end:

1. **Reproducible** — anyone can re-run the chain in <1 hour and get an equivalent result
2. **Closed-loop** — VLM critic decides ship-it / needs-more-training / broken; no human in the path until a human picks up the headset
3. **Composable** — each phase adds ONE new capability (longer training, harder env, obstacles, city, etc.) on top of the previous; we never throw a phase away

---

## 1. The Loop (canonical for every phase)

Every phase runs the same five-step loop. The only thing that changes between phases is the **env** and the **reward function**. Everything else is plumbing we already have.

```
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌─────────┐    ┌──────────────┐
│  train   │───►│  export   │───►│   render   │───►│ evaluate│───►│   decide     │
│  (PPO)   │    │trajectory │    │ USD → MP4  │    │  (VLM)  │    │              │
└──────────┘    └───────────┘    └────────────┘    └─────────┘    └──────────────┘
     │                                                                    │
     │                                                                    ▼
     │                                                  ┌──────────────────────────┐
     │                                                  │ ship-it       → next phase│
     │ ◄────────────────────────────────────────────────│ needs-more    → loop with │
                                                        │                  more iters│
                                                        │ broken        → fix env/  │
                                                        │                  reward   │
                                                        └──────────────────────────┘
```

**Already wired** in `webxr-showcase/scripts/`:
- `train.py` (Isaac Lab built-in) — `rl_games` PPO
- `export_drone_trajectory.py` — checkpoint → JSON
- `render_drone_demo.py` — JSON → animated USDA → MP4 (+ optional `--evaluate`)
- `usd_to_glb.py` — animated USDA → Quest-ready GLB (`--animated` for NLA strips)
- `evaluate_drone_trajectory.py` — MP4 → VLM verdict JSON

When all five run cleanly the cost per loop is **~$0.02 cloud + $0.0001 VLM = ~$0.02**.

A complete iteration (train → ship-it verdict OR human-meaningful failure signal) takes **~10 minutes** for short-horizon envs, **~30 min** for long-horizon ones.

### The mandatory pre-flight checklist (every session)

```bash
# 1. Start the AWS box (if stopped) + get its IP
# 2. SSH in
# 3. Start the isaaclab container (it's stopped on every box reboot)
sudo docker start isaaclab

# 4. RESTORE the ephemeral asset (per CLAUDE.md §17.10 Lesson 1)
cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/cf2x.usd
cp /home/ubuntu/assets/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd

# 5. Smoke-test LiteLLM (so the VLM critic doesn't fail mid-loop)
curl -s http://localhost:4000/v1/chat/completions -H "Authorization: Bearer sk-trigunai-master-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"PONG"}],"max_tokens":5}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

If any of those four steps fail, fix that before starting a training run. **The most common failure mode is forgetting step 4 → invisible drones in the render → wrong VLM verdicts.**

---

## 2. The Phases

Each phase has: env, reward intent, deliverable, success bar (VLM verdict threshold), estimated cloud time, and a decision gate.

### ✅ Phase 1 — Hover-near-goal baseline (DONE 2026-05-18)

| | |
|---|---|
| **Env** | `Isaac-Quadcopter-Direct-v0` (bundled, hover near randomized goal) |
| **Reward** | Default (distance to goal + upright bonus) |
| **Reps** | 500 PPO iterations, 4096 envs |
| **Deliverable** | `cf2x_trained.glb` (animated, 7.5 s loop) |
| **Verdict** | ✓ ship-it, overall 8/10 |
| **Cost** | ~$0.40 cloud + $0.0001 VLM (single loop) |
| **What it proved** | The whole pipeline (train + export + bake + render + critic + GLB) is operational. The VLM is calibrated against real flight footage. |

### 🔄 Phase 2 — Better convergence on the same env (next)

| | |
|---|---|
| **Env** | `Isaac-Quadcopter-Direct-v0` (same) |
| **Reward** | Same, but investigate collapse at ep 325 |
| **Hyperparam changes** | Lower `learning_rate` (3e-4 → 1e-4), bump `clip_value` to be less aggressive, possibly raise `entropy_coef` |
| **Reps** | 1500 iterations, with a "no-collapse" sanity check on the reward curve |
| **Deliverable** | `cf2x_trained_v2.glb` |
| **Success bar** | VLM `overall ≥ 9`, `smoothness ≥ 8` (currently 7) |
| **Cost** | ~$1.50 cloud + few cents VLM |
| **Decision gate** | If `overall: 9+` and no `issues` listed → move to Phase 3. If still oscillates, the env's reward might cap us — go straight to Phase 3 which has a richer reward shape. |

### Phase 3 — Position tracking (no obstacles, existing env)

| | |
|---|---|
| **Env** | `Isaac-TrackPositionNoObstacles-ARL-Robot-1-v0` (bundled in Isaac Lab 3.0) |
| **Reward** | Built-in: tracks a moving / further goal, not just "hover here" |
| **Why** | Last bundled env before we fork our own. Trains the drone to actually traverse distances. Tests the VLM critic on a different motion profile (more travel, less hovering). |
| **Reps** | 2000 iterations, 2048 envs (this env is heavier per step) |
| **Deliverable** | `cf2x_trained_track_v1.glb` |
| **Success bar** | VLM `overall ≥ 7`, `reach ≥ 8`, `efficiency ≥ 7` (this env is HARDER, lower bar for "ship-it") |
| **Cost** | ~$2 cloud |
| **Decision gate** | If drone visibly travels distances and looks coordinated → Phase 4. If it stalls or oscillates without reaching, tune VLM prompt to scoring "did it move at all", or extend env's max episode length. |
| **Risk** | The VLM may judge "long traveling flight" differently from "hover" — recalibrate the prompt for this phase. Compare two drops side-by-side. |

### Phase 4 — Custom A→B env, no obstacles (THE pivotal phase)

| | |
|---|---|
| **Env** | NEW: `Isaac-Quadcopter-A2B-v0` (we fork `Quadcopter-Direct-v0`) |
| **Where** | `~/IsaacLab/source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter_a2b/` (new dir, copy from `quadcopter/` and edit) |
| **Reward** |   • `+1.0 × (distance_to_B got smaller this step)` — progress<br>  • `+50` if `distance_to_B < 0.5 m` — arrival bonus<br>  • `+0.5 × upright_alignment` — stability<br>  • `−1e-3 × action_rate²` — smoothness<br>  • `−0.01 × time_step` — efficiency (don't take forever) |
| **Episode** | Spawn at Point A = `(0, 0, 1)` (Isaac-space), goal at B = `(10, 0, 2)`. Max 600 steps (~10s). |
| **Reps** | 3000 iterations, 4096 envs |
| **Deliverable** | `cf2x_trained_a2b_v1.glb` |
| **Success bar** | VLM `verdict: ship-it`, `reach ≥ 8`, `efficiency ≥ 7` |
| **Cost** | ~$5 cloud (longer episodes + more iters) |
| **Critical work** | This is where YOU spend reward-tuning effort. Expect to iterate 5-10x on the reward formula. Each tune = run the canonical loop again. |
| **Decision gate** | If the drone reliably reaches Point B in <10 s and the VLM agrees visually → Phase 5. If it learns "spin in place to maximize upright bonus", fix the reward (cap upright bonus once close to goal). |
| **Risk** | Reward hacking. PPO is brutally honest about gaming whatever score you write. Use the VLM as the catch — if VLM says `verdict: broken` despite high numerical reward, **trust the VLM** and rewrite the reward. |

### Phase 5 — A→B with hand-placed obstacles (still no city)

| | |
|---|---|
| **Env** | `Isaac-Quadcopter-A2B-Obstacle-v0` (fork Phase 4 again) |
| **Scene addition** | 3-5 box "buildings" hand-placed between A and B as `RigidObjectCfg`s. e.g. (3, 0, 2) of size (1, 2, 4), (6, 1, 1.5) of size (1, 1, 3), etc. |
| **Reward addition** | `−1000` for any drone-body collision (huge penalty so the policy treats buildings as hard constraint) |
| **Observation addition** | Add the 5 box positions to the obs vector (or use raycast distances — simpler) |
| **Reps** | 5000 iterations |
| **Deliverable** | `cf2x_trained_obs_v1.glb` |
| **Success bar** | VLM `verdict: ship-it`, no `"collided"` in issues |
| **Cost** | ~$10 cloud |
| **Critical work** | The drone will initially crash CONSTANTLY. PPO learns by failing — first 500 iters will mostly be wrecks. Don't panic. The penalty is doing its job. |
| **Decision gate** | If drone clears the obstacles cleanly and reaches B → Phase 6. If it just refuses to move (negative reward dominates) → increase progress reward weight or shrink obstacles. |
| **Risk** | "Lazy policy" — drone learns to hover at A forever because collision penalty > progress reward. Tune reward magnitudes. |

### Phase 6 — Real Nucleus city + production polish

| | |
|---|---|
| **Env** | `Isaac-Quadcopter-City-v0` (fork Phase 5) |
| **Scene** | A real bundled USD city scene (we'll find one — Demo_City, Grid_City, or pull a Showcases USD over). Drone collides with the actual city geometry, not procedural boxes. |
| **Reward** | Same as Phase 5; collision penalty applies to ALL scene geometry |
| **Observation** | Same as Phase 5 (raycasts); we don't switch to vision yet — keep it state-based for now |
| **Reps** | 10000 iterations + likely a curriculum (start with simple paths, increase complexity) |
| **Deliverable** | `cf2x_trained_city_v1.glb` + a city GLB backdrop for Gurulok scene |
| **Success bar** | VLM `verdict: ship-it`, `overall ≥ 8` |
| **Cost** | ~$25 cloud |
| **Critical work** | Loading a real city into Isaac Sim is its own task. Plan a half-day just for scene authoring. |
| **Decision gate** | The drone flies through a real city scene to Point B in VR. That's it — this is the milestone. |
| **Risk** | Scene size + render perf. Quest 3 has a polygon budget — the city GLB may need decimation via `usd_to_glb.py --decimate 0.3`. |

### Phase 7+ (post-MVP, optional)

- **Vision-based policy** — replace state-based obs with a `TiledCameraCfg` mounted on the drone, CNN encoder, train end-to-end. Avinash's Franka work in CLAUDE.md uses this pattern.
- **Sim-to-real domain randomization** — randomize physics (mass, drag, motor strength) per episode so the policy is robust to a real Crazyflie's dynamics.
- **Multiple goals / waypoints** — Point A → B → C → home.
- **Wind / disturbance** — add per-step random force to the drone body.
- **Real Crazyflie deployment** — Crazyflie 2.X has a Python API and Bitcraze's PyTorch-compatible firmware. We can fly the trained `.pth` on real hardware. Separate project track.

---

## 3. The exact commands per phase

Phases 1-3 use existing envs — pure command substitution. Phases 4-6 require writing a custom env first.

### Phases 1–3 (existing envs)

```bash
# === PRE-FLIGHT (every session) ===
EC2_IP=<current public IP>
ssh -i ~/.ssh/trigunai_key.pem ubuntu@$EC2_IP
sudo docker start isaaclab
cp /home/ubuntu/assets/Crazyflie/cf2x.usd /tmp/cf2x.usd
cp /home/ubuntu/assets/Crazyflie/configuration/cf2x_robot_schema.usd /tmp/cf2x_robot_schema.usd

# === TRAIN === (vary --task per phase, --max_iterations per phase)
sudo docker exec -d isaaclab bash -lc "cd /workspace/isaaclab && \
  rm -f /tmp/drone_train.log && \
  ./isaaclab.sh -p scripts/reinforcement_learning/rl_games/train.py \
    --task <TASK> \
    --viz none \
    --num_envs 4096 \
    --max_iterations <ITERS> \
    > /tmp/drone_train.log 2>&1"

# Wait for the final checkpoint (use Monitor or just sleep)
sudo docker exec isaaclab bash -lc "until find /workspace/isaaclab/logs/rl_games/<TASK-LOWER> \
  -name '*ep_<ITERS>*.pth' 2>/dev/null | head -1 | grep -q .; do sleep 30; done"

# === EXPORT TRAJECTORY ===
CKPT=$(sudo docker exec isaaclab bash -lc "ls /workspace/isaaclab/logs/rl_games/<TASK-LOWER>/<TIMESTAMP>/nn/last_*ep_<ITERS>*.pth | head -1")
sudo docker exec isaaclab bash -lc "cd /workspace/isaaclab && \
  ./isaaclab.sh -p export_drone_trajectory.py \
    --checkpoint $CKPT \
    --steps 180 --fps 24 \
    --out /workspace/isaaclab/exports/drone_trajectory.json"
sudo docker cp isaaclab:/workspace/isaaclab/exports/drone_trajectory.json /tmp/
sudo chown ubuntu:ubuntu /tmp/drone_trajectory.json

# === RENDER + EVALUATE + BAKE GLB ===
python3 /home/ubuntu/render_drone_demo.py \
  --out /home/ubuntu/drone_<phase>.mp4 \
  --trajectory /tmp/drone_trajectory.json --fps 0 \
  --width 800 --height 450 \
  --drone-asset /host_tmp/cf2x.usd --drone-scale 5.0 \
  --keep-usda --evaluate

# Minimal USDA + animated GLB
python3 /home/ubuntu/render_drone_demo.py \
  --out /home/ubuntu/drone_<phase>_minimal.mp4 \
  --trajectory /tmp/drone_trajectory.json --fps 0 \
  --drone-asset /home/ubuntu/cf2x.usd --drone-scale 5.0 \
  --minimal-usda --skip-render --keep-usda
blender45 --background --python /home/ubuntu/usd_to_glb.py -- \
  --input /home/ubuntu/drone_<phase>_minimal.usda \
  --output /home/ubuntu/cf2x_trained_<phase>.glb \
  --animated --max-texture 1024

# === PULL TO MAC ===
scp -i ~/.ssh/trigunai_key.pem \
  ubuntu@$EC2_IP:/home/ubuntu/drone_<phase>.mp4 \
  ubuntu@$EC2_IP:/home/ubuntu/cf2x_trained_<phase>.glb \
  ubuntu@$EC2_IP:/home/ubuntu/drone_<phase>.evaluation.json \
  ~/Documents/NvidiaSimSetup/drone_handoff/

# === DECIDE (read the JSON) ===
cat ~/Documents/NvidiaSimSetup/drone_handoff/drone_<phase>.evaluation.json
# verdict == "ship-it" → ship to Gurulok, move to next phase
# verdict == "needs-more-training" → increase iterations, loop
# verdict == "broken" → fix env / reward / framing, then loop
```

### Phases 4–6 (custom envs) — additional steps

You'll need to author a new `quadcopter_a2b_env.py` (and `_cfg.py`) inside the isaaclab container. Standard Isaac Lab DirectRL env structure. Use `quadcopter_env.py` (the one we already patched in CLAUDE.md §17.6) as the template, copy it, change:

- Spawn position: fixed at `(0, 0, 1)` not randomized
- Goal position: fixed at `(10, 0, 2)` not randomized
- Reward shape: per the table above
- Episode length: 600 steps
- Termination: `distance_to_goal < 0.5` OR `time > 600` OR (Phase 5+) `collided`

Then register the new env in `__init__.py`:
```python
gym.register(id="Isaac-Quadcopter-A2B-v0", entry_point="...", ...)
```

Once registered, training uses the same command — just `--task Isaac-Quadcopter-A2B-v0`. Everything downstream is unchanged.

---

## 4. Decision tree — when to advance, when to retreat

After every loop iteration:

```
        ┌─ verdict ──────────────────────────────────────┐
        │                                                │
   ship-it                  needs-more                 broken
        │                       │                        │
        ▼                       ▼                        ▼
  Move to next            Same env, ×1.5             Read the issues list.
  phase. Save the         iterations. Loop.          Most common:
  GLB as the new          (Cap at 3 attempts          • drone invisible → check
  baseline.               before suspecting             cf2x.usd + auto-frame
                          reward formula.)            • didn't move → policy
                                                         is hovering at A; bump
  If `overall` dropped                                   progress reward weight
  ≥2 from previous                                    • crashed → reduce
  ship-it on the same                                    learning rate or
  env, REGRESSION.                                       penalty magnitude
  Don't ship. Diagnose
  with the grid jpg.
```

**The single most important rule:** trust the VLM verdict over the numerical reward. We proved on the Phase 1 → Phase 2 v3 run that reward can drop 16% while VLM score rises 33%. The reward is what PPO is optimizing; the VLM is what humans care about.

---

## 5. Budget envelope

| Phase | Cloud cost | VLM cost | Wall time | Cumulative |
|---|---|---|---|---|
| 1 (done) | $0.40 | $0.0001 | 30 min | $0.40 |
| 2 | $1.50 | $0.001 | 1 hr | $1.90 |
| 3 | $2.00 | $0.001 | 1.5 hr | $3.90 |
| 4 | $5.00 | $0.005 | 3-4 hr (env auth) | $8.90 |
| 5 | $10.00 | $0.01 | half-day | $18.90 |
| 6 | $25.00 | $0.02 | 1 day | $43.90 |
| **TOTAL to "drone flying in city in VR"** | **~$44** | <$0.05 | ~3 working days | |

Add a 2× buffer for reward-tuning retries → **plan ~$90, ~6 working days end-to-end.**

This is on a SINGLE g5.2xlarge. We're not parallelizing across instances. If we wanted to AB-test 4 reward formulas at once, multiply by 4 in both $ and wall time saved.

---

## 6. Standing risks + mitigations

| Risk | What it looks like | Mitigation |
|---|---|---|
| **Reward hacking** | PPO finds a trick that maxes the reward but doesn't match the intent (e.g., spinning to maximize "upright" bonus while not moving) | VLM is the catch. If VLM says broken/needs-more while reward looks fine, REWRITE the reward — don't ship. |
| **Performance collapse mid-training** | Reward climbs then falls (we saw this in 500-iter Phase 1, peak at ep 100 → collapse at ep 325) | Lower learning rate. Higher PPO clip-fraction stability. Save best-reward checkpoint, not last. |
| **Asset ephemeral wipe** | Box restart → /tmp/cf2x.usd missing → drone invisible → VLM scores blank scene | Documented in NvidiaSimSetup CLAUDE.md §17.10 Lesson 1. Always run the pre-flight `cp` step. |
| **VLM hallucination on missing/off-frame drone** | The VLM gives confident scores when nothing is visible | Documented in CLAUDE.md §17.10 Lesson 3. Visibility-check is now baked into the prompt. |
| **Camera doesn't frame the drone** | The trained policy moves further than the hardcoded camera | Auto-framing already in `render_drone_demo.py`. Verify the grid JPG shows the drone in EVERY one of the 6 keyframes; if not, framing is off. |
| **Sim-to-real gap** | Trained policy looks good in sim, fails on actual Crazyflie hardware | OUT OF SCOPE for Phases 1-6. Reserved for the optional post-MVP track. Mitigation: domain randomization during Phase 6+. |
| **Quest 3 GLB perf** | Drone GLB + city GLB combined exceed Quest 3 polygon budget → frame rate drops | Use `usd_to_glb.py --decimate 0.3 --max-texture 1024`. Profile with Quest 3 dev tools. |
| **Cost overrun** | We trained too long on a stuck reward, burned $50 with nothing to show | Hard rule: every phase has a max-iterations cap. If VLM says broken after the cap, STOP and redesign reward, don't blindly train longer. |
| **Avinash needs the box** | Single g5.2xlarge in us-east-1, shared with Avinash's Mumbai work | Coordinate. Or pay $90 for a second box for a week to parallelize. |

---

## 7. What's done / what's next

✅ **DONE (as of 2026-05-18)**

- Phase 1 baseline (Quadcopter-Direct-v0, 500 iter, ship-it 8/10)
- `cf2x_trained.glb` shipped to `drone_handoff/`
- Gurulok v120 in flight (Phase 2 GLB + handoff doc)
- Full pipeline plumbing (5 scripts, 3 lessons baked into CLAUDE.md)
- VLM critic (Approach A) operational

🔄 **NEXT — immediate (this week)**

- Phase 2: 1500-iter run with lower learning rate, ship-it 9/10 target → `cf2x_trained_v2.glb`
- Side task: verify v120 works in Quest 3 — get the headset feedback before iterating further
- Document the env-authoring template for Phase 4 (so the env code is ready when training time is)

🎯 **MILESTONE — by end of next week**

- Phase 4 complete: custom A→B env, no obstacles, drone reliably reaches Point B
- That's the moment we stop using bundled envs and start owning the env definition
- After that, Phase 5 (obstacles) + Phase 6 (real city) are extensions, not new tracks

🚀 **TARGET — by ship date**

- Phase 6 in Gurulok alpha (v125-ish)
- A user puts on Quest 3, picks "Drone Demo", watches a Crazyflie navigate a real city scene from A to B, in VR
- That's the deliverable. That's the demo.

---

## 8. How to use this doc

- **Starting a new session** — open this, find the current phase, jump to its row in §2, run its commands from §3
- **Stuck mid-phase** — check §4 (decision tree) and §6 (risks)
- **Reviewing progress** — §7 is the live status board. Update it after every ship-it
- **Onboarding a new agent** — give them this doc + the two CLAUDE.md files. That's the full context.

Don't be precious. Iterate fast. Trust the VLM. Ship to alpha frequently.

— Deepak / TrigunAI Innovations
