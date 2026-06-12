# Cinematography Techniques — Reward Function Catalog

> **Master reference for encoding professional cinematography into RL reward terms.**
> Each technique has: what it is, when to use it, measurable properties, and reward formulation.
>
> This is TrigunAI's core IP — the translation layer between film art and math.
> 134 techniques across 10 categories, sourced from StudioBinder, MasterClass, DroneFilmGuide,
> NoFilmSchool, academic papers (CineMPC, DVGFormer, VERTIGO, GenDoP), and filmmaker breakdowns.
> Updated: 2026-05-24 v2.0

---

## Current system (v3 baseline — 12 reward terms)

| # | Reward term | Weight | What it teaches | Status |
|---|---|---|---|---|
| 1 | `r_framing` | 25% | Keep dancer in camera FOV (currently center-biased — WRONG) | v1 |
| 2 | `r_look_at` | 15% | Camera orientation points at dancer | v1 |
| 3 | `r_front_arc` | 10% | Stay in front 180° arc, never behind | v3 |
| 4 | `r_hold_beauty` | 10% | Find good frame, pause on it | v3 |
| 5 | `r_zoom` | 8% | Push-in / pull-out dynamics | v3 |
| 6 | `r_pacing` | 7% | Alternate movement and stillness | v3 |
| 7 | `r_shot_type` | 5% | Mix full-body / half-body framings | v1 |
| 8 | `r_distance` | 5% | Stay in filmable range (2–4 m) | v1 |
| 9 | `r_smoothness` | 5% | Smooth motion, no jerks | v1 |
| 10 | `r_safety` | 5% | Never enter 1.5 m exclusion zone | v1 |
| 11 | `r_variety` | 3% | Change azimuth angle over time | v1 |
| 12 | `r_height` | 2% | Use range of elevation angles | v1 |
| — | `framing_gate` | multiplier | If dancer >60° off-camera, all rewards ×0.30 | v2 |

---

## CATEGORY 1 — CAMERA MOVEMENTS (37 techniques)

### 1.1 Translational Movements

| # | Technique | Description | When to use | Measurable properties | Our status |
|---|---|---|---|---|---|
| 1 | **Dolly In / Push In** | Move toward subject along optical axis | Build intimacy, focus attention, amplify emotion | `Δdist < 0`; velocity 0.1–0.5 m/s; parallax shift between layers | Partial (`r_zoom` v3) — needs intentional-approach detection |
| 2 | **Dolly Out / Pull Back** | Retreat from subject along optical axis | Reveal context, emotional distance, isolation, end-of-scene | `Δdist > 0`; smooth deceleration at end | Partial (`r_zoom` v3) |
| 3 | **Truck Left / Right** | Lateral translation perpendicular to optical axis | Follow lateral action, reveal adjacent space, parallax | `vel_lateral ≠ 0`, `vel_forward ≈ 0`; subject stays in composition bounds | NOT IMPL |
| 4 | **Pedestal Up / Down (Boom)** | Vertical translation, horizontal aim constant | Change power dynamic, reveal vertical extent | `vel_vertical ≠ 0`; altitude changes monotonically; pitch ≈ constant | Partial (`r_height`) |
| 5 | **Crane Shot** | Multi-axis simultaneous (up + forward + lateral) | Grand establishing, following action across vertical planes | `|v_x|, |v_y|, |v_z| > 0`; smooth polynomial trajectory; jerk < threshold | NOT IMPL |
| 6 | **Tracking (Follow)** | Move with subject from behind, consistent framing | Show journey, pursuit; keep subject centered while environment passes | `dist ≈ const`; `screen_pos ≈ center`; camera vel ≈ subject vel | NOT IMPL — **HIGH priority** |
| 7 | **Tracking (Lead)** | Move ahead of subject, facing them | Show face/expression during motion; anticipation of destination | Camera vel > subject vel initially; subject faces camera; subject in lower third | NOT IMPL |
| 8 | **Tracking (Parallel / Side)** | Move alongside at constant lateral offset | Profile during motion, sense of pace, companionship | `lateral_offset ≈ const`; camera heading ∥ subject heading | NOT IMPL |
| 9 | **Approach Shot** | Advance toward stationary subject from far | Build anticipation before a reveal, sense of arrival | `dist` monotonically decreasing from >20 m to 3–5 m; constant velocity | NOT IMPL |

### 1.2 Rotational Movements

| # | Technique | Description | When to use | Measurable properties | Our status |
|---|---|---|---|---|---|
| 10 | **Pan Left / Right** | Yaw rotation, body stays put | Scan landscape, follow lateral motion, reveal horizontal extent | `ω_yaw ≠ 0`; pos fixed; 5–30°/s cinematic | NOT IMPL (no yaw-only action) |
| 11 | **Tilt Up / Down** | Pitch rotation, body stays put | Reveal vertical extent; tilt up = awe, tilt down = vulnerability | `ω_pitch ≠ 0`; pos fixed; 5–20°/s typical | NOT IMPL |
| 12 | **Dutch / Canted Angle** | Roll so horizon is deliberately tilted | Unease, disorientation, tension, stylistic emphasis | `roll ≠ 0`; typically 15–45°; static or dynamic | NOT IMPL (no roll control) |
| 13 | **Whip Pan / Swish Pan** | Extremely fast horizontal rotation with motion blur | Scene transition, inject energy, passage of time, comedic timing | `ω_yaw > 200°/s`; full motion blur; duration < 0.5 s | NOT IMPL |

### 1.3 Compound Movements

| # | Technique | Description | When to use | Measurable properties | Our status |
|---|---|---|---|---|---|
| 14 | **Orbit / Arc** | Circle around subject, always facing them | Hero moment, 360° reveal, dramatic emphasis, time-freeze | `ω_azimuth ≈ const`; `dist ≈ const`; subject at frame center | Partial (`r_variety`) — needs orbit-quality sub-reward |
| 15 | **Helix / Spiral** | Orbit + simultaneous vertical ascent/descent | Grand reveal, escalating drama, epic establishing | Orbit + `v_z ≠ 0`; helical path `r ≈ const, θ = ωt, z = v_z·t` | NOT IMPL |
| 16 | **Reveal Shot** | Start aimed away from subject, then move/tilt to show them | Surprise, suspense payoff, dramatic introduction | `subject_visibility: 0 → 1` over time; initial frames empty, final frames centered | NOT IMPL — conflicts with framing gate |
| 17 | **Fly-Over** | Pass over subject front-to-behind with downward tilt | Establish geography, show scale, transition | `alt > subject_height`; forward vel + pitch tilts down to track | NOT IMPL |
| 18 | **Fly-Through** | Pass through narrow space (doorway, gap) | Immersion, transition between spaces, FPV energy | Clearance < 1 m; vel 2–8 m/s; tight collision avoidance | NOT IMPL |
| 19 | **Dolly Zoom / Vertigo Shot** | Dolly backward + zoom in (subject same size, background warps) | Disorientation, realization, psychological shift | `dist` changes inversely with `focal_length`; `subject_size ≈ const`; background scale changes | NOT IMPL (no zoom control) |
| 20 | **Cable Cam** | Move along straight/curved path between two points | Smooth terrain traversal, controlled lateral movement | Position follows defined spline; vel ≈ const; gimbal compensates | NOT IMPL |
| 21 | **Steadicam / Gimbal Follow** | Stabilized follow, organic feel | Intimate corridors, organic movement | Micro-jitter removed (jerk < threshold); macro-path follows subject; dist 1–3 m; slight natural sway < 0.5 Hz | NOT IMPL |
| 22 | **Long Take / Oner** | Single uninterrupted extended shot | Build tension through continuous time, showcase choreography | Duration > 30 s (often > 60 s); continuous recomposition; no cuts | Partially inherent (our episodes ARE continuous shots) |

### 1.4 Drone-Specific Movements

| # | Technique | Description | When to use | Measurable properties | Our status |
|---|---|---|---|---|---|
| 23 | **Dronie** | Fly backward + ascend while locked on subject | Selfie-reveal establishing shot, social media signature | `v_back > 0`, `v_up > 0`; pitch auto-adjusts; subject size decreases | NOT IMPL |
| 24 | **Rocket** | Ascend straight up, camera pointing down | Reveal from intimate to god's-eye view | `v_z > 0` (2–5 m/s); `pitch = -90°`; `(x,y)` constant | NOT IMPL |
| 25 | **Boomerang** | Oval flight path, ascending outbound, descending return | Dynamic reveal + return, subject as center of world | Elliptical trajectory; alt = f(phase); returns to start | NOT IMPL |
| 26 | **Asteroid** | Fly up+back, panorama at peak, simulate descent from space | Epic reveal with tiny-planet aesthetic | Ascent: `v_back, v_up > 0`; panoramic capture at peak; reverse playback | NOT IMPL |
| 27 | **Hyperlapse** | Long-exposure time-lapse with camera position changing | Show passage of time with spatial movement | Position changes > 0.5 m between frames; time compressed 10–100× | N/A (post-processing) |
| 28 | **Point of Interest (POI)** | GPS-locked orbit at constant radius + altitude | Showcase building, monument, scene center | Same as Orbit but GPS-locked; `radius_error < 0.5 m` | Covered by orbit |
| 29 | **Top-Down / Bird's Eye** | Directly overhead, pitch −90°, straight down | Formations, patterns, dance choreography from above | `pitch = -90°`; `alt > 10 m`; yaw determines frame orientation | NOT IMPL — **HIGH priority** |
| 30 | **Low-Altitude Hero** | Near-ground level (0.5–2 m), fast forward flight | Energy, speed, FPV-style, "in the action" | `alt < 2 m`; `v_forward > 3 m/s`; ground fills bottom 30–50% | NOT IMPL — **HIGH priority** |
| 31 | **Altitude Transition** | Smooth height change during continuous shot | Transition between intimate and establishing | `dz/dt` changes; often + pitch change; alt range 2–50 m | Partial (`r_height`) |
| 32 | **Proximity Pass** | Fly very close (< 3 m) past subject at speed | Visceral energy, dramatic emphasis, demonstrate scale | `min_dist < 3 m`; `vel > 2 m/s` at closest; subject passes through frame rapidly | NOT IMPL — conflicts with safety |
| 33 | **Knap-of-the-Hill Reveal** | Fly low toward ridge, crest it to reveal landscape | Surprise reveal, dramatic geography | Subject visibility jumps 0 → 1 as camera crests | NOT IMPL |
| 34 | **Power Dive** | Dive from altitude at high speed | Extreme energy, attack-angle drama, FPV signature | `v_z < 0` (> 5 m/s); `pitch < -45°`; pull-up at bottom | NOT IMPL |
| 35 | **Power Loop** | Full vertical circle | Acrobatic energy, extreme spectacle | 360° pitch rotation; radius 5–15 m | NOT IMPL |
| 36 | **Split-S** | Half-roll then downward half-loop to reverse direction | Quick direction change with dive; action energy | Roll 180° then pitch 180°; exits opposite dir at lower alt | NOT IMPL |
| 37 | **Parallax Slide** | Lateral movement with foreground object creating depth separation | Cinematic depth, 3D feel, visual richness | `vel_lateral > 0`; foreground within 2–5 m moves faster than background; depth ratio > 3:1 | NOT IMPL |

---

## CATEGORY 2 — SHOT TYPES BY FRAMING (13 types)

> Source: StudioBinder shot guide + Video 1 breakdown (establishing → high angle)

| # | Shot type | What's in frame | Distance (person) | Emotional register | Measurable: `subject_height_ratio` (% of frame) | Our status |
|---|---|---|---|---|---|---|
| 38 | **Extreme Wide (EWS)** | Tiny in vast environment | > 50 m | Isolation, epic scale | < 5% | NOT IMPL |
| 39 | **Wide / Long (WS)** | Full body + significant environment | 10–30 m | Context, relationship to space | 10–25% | Partial (`r_shot_type` classifies "full body") |
| 40 | **Establishing Shot** | Location dominates, subject tiny/absent | > 30 m | Set geography, time, context | Subject < 10%; environment dominant | NOT IMPL |
| 41 | **Full Shot (FS)** | Head to toes, minimal environment | 5–10 m | Action, body language | 50–70% | Partial (`r_shot_type`) |
| 42 | **Cowboy Shot** | Mid-thigh up (shows holster/hands) | 3–6 m | Action + expression; originated in Westerns | 60–80% | NOT IMPL |
| 43 | **Medium (MS)** | Waist up | 2–4 m | Balanced: body language + expression, dialogue | 70–85% | Partial (`r_shot_type` "half body") |
| 44 | **Medium Close-Up (MCU)** | Chest/shoulders up | 1.5–3 m | Emphasis, mild intimacy | 80–90% | NOT IMPL |
| 45 | **Close-Up (CU)** | Face fills frame (chin to above head) | 0.5–1.5 m | Emotion, reaction, empathy trigger | 85–100% | NOT IMPL — safety zone conflicts |
| 46 | **Choker** | Forehead to chin only | 0.3–0.8 m | Intense emotion, pressure | ~100% (tight crop) | NOT IMPL |
| 47 | **Extreme Close-Up (ECU)** | Single feature (eyes, hands) | < 0.3 m | Maximum intensity, psychological depth | > 100% (extends beyond frame) | NOT IMPL |
| 48 | **Two Shot** | Two subjects in frame | Varies | Relationship, comparison | Both 40–60% height | N/A (single-subject env) |
| 49 | **Over-the-Shoulder (OTS)** | Subject past another's shoulder | 1–3 m | Conversation perspective, depth | Background subject 40–60%; shoulder 20–30% | N/A |
| 50 | **POV (Point of View)** | First-person view of what character sees | Varies | Character perspective, immersion | Camera at subject eye height, facing subject's gaze direction | NOT IMPL |

---

## CATEGORY 3 — CAMERA ANGLES (10 types)

> Source: StudioBinder + Video 1 (low angle = power/dominance, high angle = vulnerability)

| # | Angle | Description | Emotional effect | Measurable | Our status |
|---|---|---|---|---|---|
| 51 | **Eye Level** | Camera at subject's eye height | Neutral, equality, realism | pitch = 0° (relative to subject) | Implicit — no specific reward |
| 52 | **Low Angle** | Below subject, looking up | Power, dominance, heroism | pitch > +10°; camera height < subject waist | NOT IMPL — **HIGH** (`r_hero_shot`) |
| 53 | **High Angle** | Above subject, looking down | Vulnerability, weakness, overview | pitch < −10°; camera > subject head | Partial (`r_height`) |
| 54 | **Bird's Eye / Overhead** | Directly above, straight down | God-view, pattern reveal, formations | pitch = −90°; alt > 10 m | NOT IMPL — **HIGH** (`r_topdown`) |
| 55 | **Worm's Eye** | On ground, looking straight up | Extreme power/scale, otherworldly | pitch > +60°; camera < 0.3 m | NOT IMPL |
| 56 | **Dutch / Canted** | Rolled off horizontal | Unease, madness, disorientation, tension | roll = 15–45° off horizontal | NOT IMPL (no roll action) |
| 57 | **Shoulder Level** | At shoulder height | Subtle authority to subject | Camera 0.1–0.3 m below eye level | NOT IMPL |
| 58 | **Hip Level** | At waist/hip height | Cowboy/action framing, dynamic | Camera ≈ 1 m height | NOT IMPL |
| 59 | **Knee Level** | At knee height | Ground-level drama | Camera ≈ 0.5 m; pitch slightly up | NOT IMPL |
| 60 | **Ground Level** | On ground plane | Intimate, unique perspective | Camera < 0.15 m | NOT IMPL |

---

## CATEGORY 4 — COMPOSITION RULES (15 rules)

> Source: StudioBinder + NoFilmSchool + Video 2 (focal points, rule of thirds, golden triangle, leading lines, headroom/lead room, balance, symmetry, frame-within-frame, depth, color/contrast)

| # | Rule | Description | Measurable property | Our status |
|---|---|---|---|---|
| 61 | **Rule of Thirds** | Subject at intersection of 3×3 grid lines | `subject_pos` within ε of (⅓,⅓), (⅔,⅓), (⅓,⅔), or (⅔,⅔) in screen coords | **NOT IMPL — CRITICAL #1 fix** (current `r_framing` rewards center = WRONG) |
| 62 | **Center / Symmetry** | Subject dead center, bilateral symmetry | `|subj_x − 0.5| < ε`; `symmetry_score = corr(left_half, mirror(right_half))` | Accidentally what `r_framing` does now — keep as 20% variant |
| 63 | **Golden Ratio / Fibonacci** | Subject at φ-ratio point (0.382 or 0.618) | `subject_pos` near (0.382, 0.382) or (0.618, 0.618) | NOT IMPL |
| 64 | **Golden Triangle** | Diagonal corner-to-corner + perpendicular lines from other corners | Subject at intersection of diagonal and perpendicular | NOT IMPL |
| 65 | **Headroom** | Space between head top and frame top | `headroom = head_screen_y / frame_height`; ideal 5–15% MCU, 15–35% MS | NOT IMPL — **HIGH** |
| 66 | **Lead Room / Nose Room** | More space in direction subject faces/moves | `space_ahead / space_behind > 1.5`; ⅔ frame in movement direction | NOT IMPL — **HIGH** |
| 67 | **Leading Lines** | Visual lines in scene converge toward subject | Lines in frame point toward subject pos (Hough transform) | NOT IMPL (needs scene geometry) |
| 68 | **Focal Point** | Single dominant point of interest, minimize distractions | Subject is brightest/sharpest element; low clutter | Implicit via `r_look_at` |
| 69 | **Negative Space** | Large empty area contrasting with subject | `neg_space = 1 − subject_area/frame_area > 0.7`; isolation, breathing room | NOT IMPL |
| 70 | **Balance / Visual Weight** | Elements distributed so frame feels even (or deliberately uneven) | `center_of_visual_mass` near frame center for balance; skewed for tension | NOT IMPL |
| 71 | **Depth Layering** | Foreground + midground + background all populated | `num_depth_layers ≥ 3`; objects at d₁ < d₂ < d₃ where d₂/d₁ > 2 | NOT IMPL (needs scene elements) |
| 72 | **Foreground Interest** | Object in near foreground adds depth | Foreground element 1–3 m from camera; subject 3–10 m | NOT IMPL |
| 73 | **Frame Within Frame** | Architectural elements create secondary frame around subject | Subject bounded by foreground on 2+ sides; depth layers | NOT IMPL |
| 74 | **Diagonal Dominance** | Major elements along diagonal for dynamic energy | Dominant line at 30–60° from horizontal | NOT IMPL |
| 75 | **Horizon Placement** | Horizon at ⅓ or ⅔, not center | `horizon_y / frame_height` near 0.33 or 0.67 | NOT IMPL |

---

## CATEGORY 5 — TEMPORAL / PACING (12 techniques)

| # | Technique | Description | When to use | Measurable | Our status |
|---|---|---|---|---|---|
| 76 | **Beat Sync** | Movement/transition lands on music beat | Music videos, dance, concerts | `|t_move − t_beat| < 50 ms`; correlate vel peaks with beat onsets | **NOT IMPL — CRITICAL #2** |
| 77 | **Anticipation** | Camera begins moving before the action it follows | Professional tracking; "camera knows what's coming" | Camera vel leads subject vel by 0.1–0.3 s; `cross_corr offset < 0` | NOT IMPL — **HIGH** |
| 78 | **Hold / Linger** | Reach position and pause, let moment breathe | After reveal, emotional peak, let audience absorb | `vel < ε` for `duration > 1.5 s`; subject properly composed during hold | ✅ DONE (`r_hold_beauty` v3) |
| 79 | **Rhythmic Cutting / Visual Tempo** | Shot durations create rhythm (4-beat, 2-beat, 1-beat) | Match musical structure; build/release tension | `shot_duration_sequence` follows progression; avg cut length ∝ BPM | NOT IMPL |
| 80 | **Accelerating Pace** | Shots get shorter toward climax | Build tension, urgency | `shot_duration[i+1] < shot_duration[i]`; ratio 0.6–0.8× | NOT IMPL |
| 81 | **Decelerating Pace** | Shots get longer after climax | Release, resolution, breathing room | `shot_duration[i+1] > shot_duration[i]` | NOT IMPL |
| 82 | **Speed Ramp** | Velocity changes dramatically within single shot | Emphasize a moment; music energy shifts | `|d(vel)/dt|` has large spike; vel ratio peak/trough > 3:1 | NOT IMPL |
| 83 | **Slow-Motion Equivalent** | Camera slows dramatically at closest approach | Emphasize subject detail during proximity pass | `vel(t_closest) < 0.3 × vel(t_approach)` | NOT IMPL |
| 84 | **Pause-and-Release** | Movement pauses briefly then accelerates in new direction | Punctuation of movement phrases; energy reset | `vel = 0` for 0.3–0.8 s then `accel > threshold` | Partial (`r_pacing` v3) |
| 85 | **Continuous Recomposition** | Smooth shift between composition rules in unbroken shot | Long takes, complex choreography | Composition target changes (thirds-left → center → thirds-right) smoothly | NOT IMPL |
| 86 | **Downbeat Emphasis** | Largest movement lands on beat 1 of bar | Music video, concert, dance | `max(|accel|)` per bar occurs at beat 1 ±100 ms | NOT IMPL |
| 87 | **Upbeat Anticipation** | Movement begins on beat 4 / "and", arrives on beat 1 | Musical phrasing in camera work | Movement initiation on beat 3.5–4; arrival on beat 1 of next bar | NOT IMPL |

---

## CATEGORY 6 — DEPTH OF FIELD / FOCUS (5 techniques)

> Note: Most DOF techniques require variable-aperture or variable-focus lens control. Our drone sim has a fixed virtual camera. These become relevant when we add camera parameter actions.

| # | Technique | Description | Measurable | Our status |
|---|---|---|---|---|
| 88 | **Shallow DOF** | Subject sharp, background blurred | Aperture wide (f/1.4–2.8); circle of confusion in BG > threshold | N/A (fixed camera) |
| 89 | **Deep Focus** | Everything from FG to BG sharp | Aperture narrow (f/8–16); all layers in focus | N/A |
| 90 | **Rack Focus / Pull Focus** | Focus shifts from one plane to another mid-shot | `focus_dist` changes from d₁ to d₂; transition 0.5–2 s | N/A |
| 91 | **Split Diopter** | Two focal planes simultaneously sharp | FG and BG sharp; middle blurred | N/A |
| 92 | **Follow Focus** | Focus tracks moving subject continuously | `focus_dist(t) = dist_to_subject(t)` | N/A |

---

## CATEGORY 7 — EMOTIONAL / NARRATIVE (13 techniques)

> Source: StudioBinder psychology of cinematography + Video 2 composition-emotion mapping

| # | Technique | Description | When to use | Measurable camera properties | Our status |
|---|---|---|---|---|---|
| 93 | **Tension Build** | Slow push-in + narrowing composition + decreasing headroom | Before dramatic moment | `Δdist ≈ -0.05…-0.2 m/s`; headroom ↓; neg space ↓ | NOT IMPL |
| 94 | **Isolation** | Wide/EW shot, subject tiny, vast negative space | Abandonment, solitude, insignificance | `subject_ratio < 0.1`; `neg_space > 0.9`; subject near center | NOT IMPL |
| 95 | **Power Shot** | Low angle + push-in + subject fills upper frame | Hero entrance, dominance, authority | Camera < subject waist; pitch > +10°; subject fills upper 60% | NOT IMPL → part of `r_hero_shot` |
| 96 | **Vulnerability** | High angle + wide lens + subject small | Defeat, helplessness, being watched | Camera > head + 2 m; pitch < −20°; `subject_ratio < 0.3` | NOT IMPL |
| 97 | **Reveal** | Hidden info shown through camera movement | Surprise, discovery, plot twist | `key_element_visibility: 0 → 1` via camera motion | NOT IMPL |
| 98 | **Concealment** | Camera deliberately avoids showing something | Suspense, mystery, withhold info | Key element not in frustum or occluded | NOT IMPL |
| 99 | **Intimacy / Empathy** | CU, eye-level, shallow DOF, still or gentle movement | Emotional connection to character | `dist < 1.5 m`; pitch ≈ 0; vel < 0.1 m/s; face > 30% of frame | NOT IMPL |
| 100 | **Epic / Scale** | Extreme wide, high altitude, slow movement | Awe, grandeur, establishing world | `alt > 20 m`; FOV > 60°; vel < 1 m/s; landscape > 80% | NOT IMPL |
| 101 | **Chaos / Energy** | Fast movement, whip pans, dutch angles, rapid alt changes | Action, panic, excitement, FPV | `ω > 90°/s`; jerk > threshold; roll ≠ 0; rapid vel changes | NOT IMPL |
| 102 | **Serenity / Calm** | Slow, smooth, level; wide; minimal rotation | Peace, beauty, meditation | vel < 0.5 m/s; ω < 5°/s; jerk ≈ 0; roll = 0 | NOT IMPL |
| 103 | **Claustrophobia** | Tight framing, no headroom, no lead room | Entrapment, pressure | headroom < 3%; lead_room_ratio < 0.5; obstacles on 3+ sides | NOT IMPL |
| 104 | **Freedom / Liberation** | Wide, ascending, opening from tight to wide | Breaking free, triumph | alt ↑; dist ↑; neg_space ↑; tight → open | NOT IMPL |
| 105 | **Suspense Crawl** | Ultra-slow push-in from behind/above | Horror, thriller, being watched | vel < 0.05 m/s; approach from behind; subject facing away; dur > 10 s | NOT IMPL |

---

## CATEGORY 8 — DANCE / PERFORMANCE-SPECIFIC (9 techniques)

| # | Technique | Description | When to use | Measurable | Our status |
|---|---|---|---|---|---|
| 106 | **Overhead Formation** | Bird's eye above dancers showing geometric patterns | Group choreography, synchronized dance | pitch = −90°; alt set so all dancers fit; coverage > 60% | NOT IMPL |
| 107 | **Ground-Level Sweep** | Floor level sweeping past/through feet and legs | Energy, intimate with footwork | alt < 0.5 m; vel > 1 m/s; lateral or forward | NOT IMPL |
| 108 | **Rise-and-Reveal** | Start ground-level close, rise up+back to reveal full scene | Open performance, intimate → epic | alt: 1 m → 15 m+; dist ↑; continuous shot | NOT IMPL |
| 109 | **Synchronized Orbit** | Orbit in sync with performer's spin | Enhance spinning, visual harmony | `cam_ω = dancer_rotation_speed`; `relative_facing ≈ const` | NOT IMPL |
| 110 | **Beat-Matched Altitude Pulse** | Altitude oscillates with beats | Add visual rhythm to aerial shots | `alt(t)` correlates with `beat_amplitude(t)`; oscillation 0.5–2 m | NOT IMPL |
| 111 | **Dancer-Facing Track** | Track laterally, always facing dancer's front | Show expressions + body movement during traveling choreo | `subject_facing_camera = true`; cam moves ∥ dancer path | NOT IMPL |
| 112 | **Body-Part Isolation** | Tight on hands, feet, torso, or face for specific choreo | Highlight technique, artistry, detail | ROI = body_part; body_part fills > 50% of frame | NOT IMPL |
| 113 | **Counter-Motion** | Camera moves opposite to dancer's direction | Dynamic contrast, sense of speed | `cam_vel_dir ≈ −subj_vel_dir`; relative vel > individual | NOT IMPL |
| 114 | **Breath Shot / Musical Pause** | Camera holds still during musical rest | Emphasize stillness, contrast with preceding motion | vel = 0 during `audio_rms < threshold`; dur matches rest | NOT IMPL |

---

## CATEGORY 9 — SMOOTHNESS / MOTION QUALITY METRICS (9 metrics)

> Not "techniques" but **quality constraints** that are reward components across ALL techniques.

| # | Metric | Description | Formulation | Our status |
|---|---|---|---|---|
| 115 | **Jerk Minimization** | Rate of change of acceleration should be low | `J = ∫|d³pos/dt³|² dt`; professional cinema jerk < 0.5 m/s³ | ✅ Partial (`r_smoothness` v1) |
| 116 | **Snap Minimization** | Fourth derivative for ultra-smooth motion | `S = ∫|d⁴pos/dt⁴|² dt` | NOT IMPL |
| 117 | **Angular Jerk** | Rotational smoothness (pan/tilt/roll) | `J_ω = ∫|d³orient/dt³|² dt`; whip pans deliberately violate this | NOT IMPL |
| 118 | **Velocity Consistency** | Speed shouldn't oscillate without purpose | `var(|vel|) / mean(|vel|)` < threshold during steady-state | NOT IMPL |
| 119 | **Gimbal Horizon Lock** | Roll = 0 unless Dutch angle intentional | `|roll| < 1°` during standard shots | NOT IMPL |
| 120 | **Subject Tracking Error** | How well camera keeps subject at intended screen pos | `RMS(screen_pos − target_pos)` < threshold | Partial (`r_framing` + `r_look_at`) |
| 121 | **Occlusion Avoidance** | Subject not blocked by obstacles | `subject_visible_fraction > 0.95`; raycast checks | N/A (open env) |
| 122 | **Collision Avoidance** | Camera doesn't collide with environment | `min_dist_obstacle > safety_margin` (0.5–2 m) | ✅ (`r_safety` v1) |
| 123 | **Frame Stability** | Horizon stays level unless intentional | `roll_variance < 0.5°²` over 2 s windows | NOT IMPL |

---

## CATEGORY 10 — ACADEMIC PAPERS & SYSTEMS (11 references)

| # | Paper / System | Year | Key contribution | Relevance to our RL rewards |
|---|---|---|---|---|
| 124 | **CineMPC** (Pueyo et al.) | 2024 | First drone cinematography with intrinsic camera params (zoom, focus, DOF) in MPC. Cost functions encode rule-of-thirds, framing, DOF. | Mathematical cost functions for composition → reward terms. arXiv:2401.05272 |
| 125 | **DVGFormer** | 2024 | Auto-regressive transformer on DroneMotion-99k dataset of real drone footage. Learns orbits, dives, proximity from data. | Learning from demonstration; camera trajectories + patches as supervision. arXiv:2412.09620 |
| 126 | **VERTIGO** | 2025 | Direct Preference Optimization on Unity-rendered previews scored by VLM. First preference-based post-training for camera generators. | VLM scoring as reward signal; preference model on ranked trajectories. arXiv:2604.02467 |
| 127 | **GenDoP** | 2025 | Decoder-only Transformer for camera trajectories; DataDoP dataset of 29K real shots with captions + depth. ICCV 2025. | Architecture + dataset design for learning from real cinematography. arXiv:2504.07083 |
| 128 | **Camera Trajectory Survey** | 2025 | First survey covering rule-based, optimization, ML, and hybrid methods + eval metrics. | Definitive reference for method taxonomy and evaluation. arXiv:2506.00974 |
| 129 | **Min-Jerk Trajectories** (Galvane et al.) | 2018 | Polynomial trajectories minimizing jerk with cinematographic constraints. | Jerk/snap as differentiable reward terms. |
| 130 | **Multi-UAV Optimal Trajectories** (Alcantara et al.) | 2020 | Multi-drone trajectory optimization with framing + collision + smoothness. | Multi-agent RL formulation. arXiv:2009.04234 |
| 131 | **Automated Cinematography Planning** | 2024 | Real-time motion planning: framing objectives → robot trajectories + gimbal control. | Online planning → RL: framing objective = reward, dynamics = env. arXiv:2409.00864 |
| 132 | **RL of Dolly-In** | 2025 | RL-trained dolly-in policy. Reward = centering error + vel smoothness + subject size. First RL for a named shot. | Direct precedent for our approach. arXiv:2509.00564 |
| 133 | **Synchronized Drone Filming RL** (Springer) | 2020 | Multi-drone RL with role assignment (lead, follow, wide). | Multi-agent RL with role-conditioned rewards. |
| 134 | **Flying on Tap Shoes** (Tandfonline) | 2023 | Aerial filming for dance. Camera-dancer relationship study. | Domain-specific: how to frame dancers, angles per choreographic element. |

---

## COMPOSITE REWARD ARCHITECTURE (synthesis)

```
R_total = w₁·R_composition + w₂·R_framing_size + w₃·R_smoothness + w₄·R_technique + w₅·R_music + w₆·R_safety

Where:
├── R_composition = rule-of-thirds + headroom + lead room + depth layering
├── R_framing_size = subject size matches target shot type (CU, MS, WS)
│                    + angle matches target (low, high, eye-level)
├── R_smoothness = jerk penalty + angular jerk + velocity consistency + horizon stability
├── R_technique = technique-specific (orbit: constant radius + ω;
│                 reveal: visibility 0→1; tracking: Δdist ≈ 0, centered)
├── R_music = beat sync (vel peaks ∝ beat onsets) + tempo matching
│            (vel ∝ musical energy) + phrase structure
└── R_safety = collision penalty + occlusion penalty + altitude floor + geofence
```

Each technique from this catalog maps to a specific configuration of these components with technique-specific weights and targets.

---

## IMPLEMENTATION ROADMAP

### Phase v4 (next training cycle) — 5 new rewards

| # | Technique | Reward name | Source § | Impact |
|---|---|---|---|---|
| 1 | Rule of Thirds (61) | `r_thirds` | Replace `r_framing` center-bias | **CRITICAL** |
| 2 | Beat-Sync (76) | `r_beat_sync` | New — needs music features in env | **CRITICAL** |
| 3 | Tracking/Follow (6) | `r_tracking` | New — match dancer vel when moving | HIGH |
| 4 | Top-Down moments (29, 54) | `r_topdown` | New — brief bird's-eye phases | HIGH |
| 5 | Low-Angle Hero (30, 52) | `r_hero_shot` | New — brief below-eye-level phases | HIGH |

### Phase v5 — 4 more rewards

| # | Technique | Reward name | Source § | Impact |
|---|---|---|---|---|
| 6 | Anticipation (77) | `r_anticipation` | Camera leads dancer by 0.1–0.3 s | HIGH |
| 7 | Emotional Arc (D5 in v1) | `r_emotional_arc` | Distance ∝ 1/music_rms | HIGH |
| 8 | Lead Room (66) | `r_lead_room` | ⅔ frame ahead of movement | HIGH |
| 9 | Headroom (65) | `r_headroom` | 5–15% head-to-top | MEDIUM |

### Phase v6 — Eureka-style automated discovery

Use LLM to generate new reward candidates, train on each, VLM grades the output,
evolve the best. This is where we discover techniques no human cinematographer has named.
Reference: VERTIGO paper (126) shows VLM-scored DPO already works for camera quality.

---

## TECHNIQUE DISCOVERY METHODS

### Method 1: Watch and learn
1. Download 20 professional drone dance videos from Vimeo
2. Frame-by-frame: extract camera position/angle/distance via structure-from-motion
3. Cluster trajectories — each cluster = a technique
4. Name it, measure it, write a reward

### Method 2: VLM critic feedback loop
1. Train policy → render 10 test videos → feed to GPT-4V
2. "Compare to professional drone dance footage. What's missing?"
3. VLM says: "Camera never holds on face during spins"
4. Write: `r_spin_closeup` — detect dancer ω > threshold, reward closer distance
5. Retrain. Repeat.

### Method 3: Eureka (automated reward evolution)
1. LLM generates 16 candidate reward functions (Python code)
2. Train policy with each (100 epochs, ~2 min each = 32 min total)
3. Render test video from each → VLM ranks all 16
4. LLM takes top 4, mutates, generates 16 new candidates
5. Repeat 5 generations → best reward wins
6. May discover novel techniques no human has named

---

## KEY INSIGHTS

**#1 — We currently train to CENTER the subject. This is WRONG.**
Professional cinematography uses rule-of-thirds: subject at ⅓ intersection, not dead center.
Video 2 confirms: "the four intersecting points... are fantastic areas to place your subject."
Fixing this single issue = biggest visual improvement. Center framing should be a 20% variant
(for authority/power shots), not the default.

**#2 — Beat-sync is the second biggest win.**
Dance footage where camera movements don't align with beats looks amateur regardless of
everything else. Musical phrasing in camera work (upbeat anticipation → downbeat emphasis)
separates pro from amateur.

**#3 — Headroom + lead room = instant polish.**
Video 2: "placing your subject's eyes on the upper horizontal line of rule-of-thirds will
almost always give you perfect headroom and lead room." These three rules (thirds + headroom
+ lead room) are a triplet — implement together.

**#4 — Emotional intent drives shot choice, not random variety.**
Low angle = power. High angle = vulnerability. Wide + negative space = isolation.
Close-up = empathy. The policy should learn WHEN to use each, not just cycle through randomly.
This requires music energy or choreographic phase as input.

**#5 — Depth is king in 2D.**
Video 2: "we're representing 3D space in a 2D medium — the best way is depth."
Foreground interest, depth layering, parallax from drone lateral movement.
Even without scene objects, the drone can create parallax between dancer and background
by strategic lateral movement during orbits.

---

*Cinematography Techniques Catalog v2.0 | TrigunAI Innovations | 2026-05-24*
*Sources: StudioBinder (shot guide, camera movements, composition, angles, Roger Deakins analysis),*
*MasterClass, DroneFilmGuide, NoFilmSchool, DocFilmAcademy, Video 1 (shot types breakdown),*
*Video 2 (7 composition techniques), CineMPC, DVGFormer, VERTIGO, GenDoP, Camera Trajectory Survey,*
*RL of Dolly-In, Flying on Tap Shoes, DJI QuickShots, FPV Tricktionary, Rotor Riot.*
