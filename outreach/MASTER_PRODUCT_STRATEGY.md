# TrigunAI Cinematographer — Master Product Strategy

> **Master reference for product shaping, marketing, and sales conversations.**
> Covers: what we sell, how we deliver, competitive moat, Made in India positioning,
> pricing, deployment mechanics, and customer targeting.
> Updated: 2026-05-24

---

## 1. WHAT WE SELL

**One sentence:** We train a neural network cinematographer for your specific performance,
and deliver it as a file that runs on your drone.

**What the customer gets:**
- A trained ONNX policy (<5 MB) that controls drone camera positioning in real-time at 50 Hz
- Pre-visualization MP4 to review before hardware deployment
- Optional: VR preview GLB for spatial validation on Quest/Vision Pro

**What we do NOT sell:**
- Drones (hardware is the customer's or a partner's)
- Drone piloting services (though "we film your event" is a valid service tier)
- Generic follow-me or orbit — that's what DJI already does for free

---

## 2. HOW IT'S DIFFERENT FROM EVERYTHING ELSE

### What exists today (commercial)

| Product | What it does | Intelligence |
|---|---|---|
| DJI ActiveTrack / QuickShots | Subject-centering + fixed geometric patterns (orbit, helix, rocket) | Zero — canned spirals, same every time |
| Skydio KeyFrame | Human places 3D waypoints, drone interpolates smooth path + avoids obstacles | Human is the cinematographer, drone just flies safely |
| HOVERAir X1 | Pocketable selfie drone, 5 pre-programmed modes | Same as DJI — fixed patterns |

**All automate "how to fly." None decide "where to be for a cinematic shot."**

### What exists in research (not productized)

| Lab | What they proved | Why it's not a threat |
|---|---|---|
| CMU — Bonatti (2020) | RL policy trained on human aesthetic preferences beats DJI | PhD thesis. Code abandoned 2021. Never commercialized. |
| CineMPC (IEEE 2024) | MPC for camera position + lens params | Not learning-based — can't improve over time |
| DiffusionCinema (Jan 2026) | Text prompt → drone trajectory | One-shot pre-planned path. Not reactive to live motion. |
| ACDC (Sep 2025) | LLM + Bayesian optimization for indoor video tours | Plans single trajectories, not real-time |
| DVGFormer (Dec 2024) | Transformer from 99K YouTube drone videos | Imitation learning — caps at human average |

**No one sells "cinematographer-policy-as-a-service."** This service does not exist.

### Our advantage

| Dimension | DJI / Skydio | Us |
|---|---|---|
| Shot selection | Human decides or fixed patterns | Neural network decides in real-time |
| Subject understanding | Bounding box (2D rectangle) | Full mocap skeleton (84 joints at 60 Hz) |
| Adapts to choreography | No — same orbit for every dance | Yes — trained on YOUR specific routine |
| Improves | No — firmware update only | Yes — retrain with new data |
| Customizable per client | No | Yes — unique policy per performer |

### The analogy that works in sales

> "DJI built a car with great autopilot. We train the race driver.
> Your drone already knows how to fly. We teach it cinematography."

---

## 3. THE LLM/DIFFUSION THREAT

### What's coming (2025-2026 papers)

Research papers show text-to-trajectory: type "orbit slowly from the right, reveal the
background" → AI generates a drone flight path. If DJI puts ChatGPT in their app, casual
users can describe shots in English and get them.

### Why it doesn't kill our wedge

| | LLM trajectory planning | Our RL policy |
|---|---|---|
| When it plans | Before the flight (one-shot) | Every frame, 50 Hz, during flight |
| Adapts if dancer moves? | No — plan is fixed | Yes — continuously reframes |
| Handles 25-min performance? | Impractical — can't describe 25 min in text | Natural — policy runs continuously |
| Knows choreography? | No — only knows what you typed | Yes — trained on actual mocap |
| Unexpected movement? | Breaks | Handles it |

**Their threat:** Commoditizes the LOW end (30-second social media clips on static subjects).
**Our defense:** We own the HIGH end (multi-minute live performances, dynamic improvised movement).

**Future play:** Build a text-to-policy interface ON TOP of our RL system. LLM sets intent
("dramatic low angles, push in on spins"), RL policy executes it reactively. Best of both.

---

## 4. WHAT THE DRONE ALREADY HAS vs. WHAT WE ADD

### Built-in (from Modal AI / any drone manufacturer)

- Flight controller (PX4) — keeps it in the air, stability, motor mixing
- Position hold — hover at a coordinate without drifting
- Obstacle avoidance — cameras detect and avoid walls
- Waypoint navigation — "fly to point A, then B, then C"
- Return-to-home — low battery safety
- Camera — records video, streams feed
- Onboard compute (Snapdragon) — can run ONNX models locally

**The drone already knows HOW to fly.**

### What we add (the cinematographer brain)

The trained policy takes in:
- Dancer position + velocity (from Quest mocap / beacon / camera)
- Current drone-to-dancer angle, distance, elevation
- History of recent angles (for variety optimization)

And outputs:
- Desired thrust + rotation moment (= "go HERE relative to the dancer")

**What the policy learned from our 8 reward terms:**
1. **Framing (20%)** — always keep dancer in camera's field of view
2. **Distance (10%)** — stay 2-4m (too close = dangerous, too far = no detail)
3. **Smoothness (15%)** — dolly-like motion, no jerks
4. **Variety (10%)** — orbit and change angles, don't hover in one spot
5. **Safety (15%)** — NEVER enter 1.5m exclusion zone around dancer
6. **Height variety (5%)** — mix low hero shots with high establishing shots
7. **Look-at (10%)** — camera must always point at dancer
8. **Shot type diversity (15%)** — alternate full-body wide and medium close-up framings

**These are professional cinematography rules encoded as math.** The neural network
satisfies all 8 simultaneously — which takes a human drone operator years of practice.

---

## 5. HOW WE DELIVER THE POLICY (DEPLOYMENT)

### It's NOT embedded firmware coding

The deployment is a ~200-line Python ROS 2 node. Written ONCE, works for every customer.
Only the ONNX file changes per engagement.

### Architecture on the drone

```
TRACKING INPUT ──► YOUR ONNX POLICY ──► PX4 AUTOPILOT ──► MOTORS
"dancer is at      "go to this         handles actual
 x, y, z"          position"           flying
```

### Four delivery tiers

| Tier | What customer gets | Technical skill needed | Price tier |
|---|---|---|---|
| **A: File delivery** | ONNX file + ROS 2 package. Customer SSHs into drone, copies file, runs launch command. | Drone operator with Linux basics | Lowest |
| **B: Docker container** | Pre-built Docker image. Customer runs one command: `voxl-docker pull trigunai/cinematographer:v1` | Minimal — VOXL SDK supports Docker | Medium |
| **C: SD card** | Pre-configured microSD card shipped to customer. Insert → power on → works. | Zero — plug and play | Higher (includes integration) |
| **D: OTA via app (future)** | Customer opens TrigunAI app, taps "Deploy new policy." Downloads over WiFi. Hot-swaps. | Zero — consumer UX | SaaS subscription |

### What we write once (the deployment stack)

| Component | Lines | Language | Effort |
|---|---|---|---|
| ROS 2 cinematographer node | ~200 | Python | 1-2 days |
| ONNX inference wrapper | ~50 | Python | Hours |
| PX4 setpoint publisher | ~100 | Python (MAVSDK) | 1 day |
| Docker packaging | Dockerfile | YAML | Hours |
| **Total one-time work** | **~350 lines** | | **~3-4 days** |

After this, per-customer delivery = swap the ONNX file. That's it.

### Dancer tracking input options

The policy needs to know "where is the dancer?" each frame:

| Method | Accuracy | Cost | Best for |
|---|---|---|---|
| Quest 3 on dancer (WiFi stream) | Best — full skeleton | Dancer wears Quest | Indoor performances, our existing pipeline |
| AprilTag marker | Good — position only | Free (printed paper) | Budget setups, outdoor |
| UWB radio beacon | Good — 10cm | ~$50/tag | Large venues, outdoor |
| Onboard camera + pose estimation | Medium | Free (drone's camera) | Zero extra hardware, but less accurate |
| RTK GPS | Good — 2cm | ~$200/unit | Outdoor only |

For indoor dance: Quest 3 streaming over WiFi is best — and we already have the pipeline.

---

## 6. MADE IN INDIA POSITIONING

### The rules

| What you sell | Can claim "Made in India"? | Why |
|---|---|---|
| ONNX policy (software/IP) | YES | All IP developed in India by Indian company |
| Filming service ("we film your event") | YES | Service rendered by Indian company |
| Bundled product (drone + policy) | NO | Imported hardware fails BIS local content thresholds |

### The right framing

**DO say:** "Indian AI cinematography intelligence — runs on any drone platform"
**DO say:** "AI Developed in India" / "Engineered in India"
**DON'T say:** "Made in India" for a product with imported drone hardware
**DON'T say:** "Made in India drone" — it's not, and claiming it risks legal issues

### Grant/scheme implications

| Scheme | Works for software/service? | Works for hardware product? |
|---|---|---|
| DPIIT Startup Recognition | YES | YES (Indian company either way) |
| SISFS / Bihar grants | YES | Risky — may require local manufacturing |
| Make in India procurement | YES for software | NO — imported hardware fails thresholds |
| NVIDIA Inception | Country doesn't matter | N/A |
| Defense/government contracts | YES for AI layer | NO — need Indian OEM drone partner |

### The strategic play: Partner, don't import

**Don't sell hardware. Sell intelligence.** If a customer needs the full package:

Partner with an Indian drone OEM:
- IdeaForge (listed, defense + enterprise)
- Garuda Aerospace (commercial, large fleet)
- Skylark Drones (mapping/survey, expanding)
- Dhaksha (defense, heavy lift)

They build the drone in India + you provide the AI = "Made in India" end-to-end.
Opens government/defense contracts that neither can win alone.

---

## 7. PRICING MODEL

### Pilot engagement: 5L–15L ($6K–$18K)

**What's included:**
- 3+ motion capture sessions ingested
- Custom policy trained (1-2 weeks)
- Pre-vis MP4 for approval
- ONNX policy + deployment package
- Integration support (remote)

**Why this range:** A skilled drone cinematographer costs $500–2000/day.
A 5L policy pays for itself in 3-5 shooting days.

### Ongoing subscription (future): 1-2L/month

- New policies per new routine/performer
- Policy refinement from production feedback
- Priority support
- OTA deployment via app

### Enterprise / OEM licensing (future)

- Drone manufacturer embeds our AI as a feature
- Per-unit or revenue-share model
- IdeaForge, Garuda, or international OEMs

---

## 8. CUSTOMER TARGETING

### Primary segments (highest willingness to pay)

1. **Professional dance companies** — film rehearsals + performances
2. **Concert / live event producers** — autonomous camera coverage
3. **Music video production** — creative drone shots without a pilot
4. **Sports training facilities** — film athletes with cinematic quality

### Secondary segments (lower price but volume)

5. **Wedding videographers** — premium offering for high-end weddings
6. **Real estate / architecture** — cinematic property tours
7. **Content creators** — YouTube, Instagram, TikTok (if price drops)

### Who to approach first (India)

- Attakkalari Centre for Movement Arts (Bangalore)
- Nrityagram Dance Village (Bangalore)
- National Centre for the Performing Arts (Mumbai)
- Shiamak Davar's Institute (Mumbai/national)
- Terence Lewis Contemporary Dance Company (Mumbai)
- Any Bollywood choreographer's production house
- NH7 Weekender / Ziro Festival / Magnetic Fields (live events)

### Who to approach first (International)

- Alvin Ailey (NYC)
- Royal Ballet (London)
- Cirque du Soleil (Montreal)
- Live Nation / AEG (concert production)
- Major music video production houses

---

## 9. SALES CONVERSATION CHEAT SHEET

### Opening pitch (15 seconds)

> "Your drone already knows how to fly. We teach it cinematography.
> You give us your rehearsal footage, we train an AI that films your
> next performance like a professional — real-time, no pilot needed."

### Common objections

**"DJI already has follow-me mode."**
> DJI follows you in a fixed circle. We create cinematic shot variety —
> low angles, push-ins, crane shots, timed to your choreography.
> Watch this side-by-side. [show A4 drone-POV vs DJI orbit video]

**"Can't I just hire a drone pilot?"**
> You can — at $500-2000/day. Our policy costs 5L once and works forever.
> Plus it reacts in 20 milliseconds. No human pilot has those reflexes.

**"What if the dancer improvises?"**
> That's exactly our advantage. The policy runs at 50 Hz, reacting to your
> dancer's actual movement in real-time. It's not a pre-planned path —
> it adapts frame by frame.

**"Is this safe?"**
> The policy has a hard 1.5m safety zone — it will NEVER fly closer.
> That's enforced at the neural network level AND at the PX4 flight
> controller level. Two independent safety layers.

**"We don't have a drone."**
> We can recommend platforms (Modal AI Starling 2 for indoor, DJI Matrice
> for outdoor). Or we can partner with an Indian drone operator for a
> full-service engagement.

**"Can we see a demo?"**
> Yes — we have a 25s pre-visualization video of the trained policy
> filming a dancer. We can also show it in VR on Quest 3 if you have one.

---

## 10. FILES REFERENCED IN THIS DOCUMENT

| File | What it is |
|---|---|
| `outreach/CAPABILITY_ONE_PAGER.md` | Customer-facing one-pager (send to prospects) |
| `outreach/MASTER_PRODUCT_STRATEGY.md` | This file |
| `cinematography/rewards.py` | The 8 reward terms (source code) |
| `cinematography/cinematographer_env.py` | The RL environment (source code) |
| `cinematography/drone_pov_5s.mp4` | 5s test video (A4 gate, approved) |
| `cinematography/dancer_orbital_25s.mp4` | Orbital baseline (A2, for comparison) |
| `project_hub/CEO_BRIEFING.md` | Current status across all workstreams |
| `project_hub/GATE_LOG.md` | All subjective approval gates |

---

*Master Product Strategy v1.0 | Trigunaï Innovations | 2026-05-24*
*Source of truth for product shaping, marketing positioning, and sales enablement.*
*Update this file when competitive landscape changes or pricing model evolves.*
