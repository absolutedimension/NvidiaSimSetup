# MVP Sprint Progress

> Sprint: ADR-003 — 2-Week Complete Demo
> Created: 2026-05-25
> Target completion: 2026-06-08
> Budget: $25

## Status: Day 1-5 scripts built locally — API keys DONE, awaiting EC2 IP only

### Handoff to Executor (2026-05-25)
**What CEO session completed:**
- ✅ A4 gate approved (25s drone-POV video — camera tracks performer, moves cinematically)
- ✅ 6 Blockade Labs HDRIs generated via free web UI (8K equirectangular JPGs) at `stage_design/hdri/`
  - `hero_hdri.jpg` (5.4 MB) — massive concert arena, red/gold pyrotechnics
  - `intimate_hdri.jpg` (5.3 MB) — warm jazz club, amber spotlights
  - `epic_hdri.jpg` (4.8 MB) — Olympic stadium, lasers, LED walls (v2)
  - `energy_hdri.jpg` (4.7 MB) — underground rave, neon strobes
  - `solitude_hdri.jpg` (4.6 MB) — empty theater, ghost light
  - `beauty_hdri.jpg` (5.1 MB) — fashion runway, chandeliers, pink/gold (v2)
- ✅ Deepgram API key obtained ($200 free credit) — saved in `.env`
- ✅ Day 1-5 scripts all built locally (lighting presets, render pipeline, voice commander, mode transitions, trajectory export)
- ✅ Day 9.1 SRT subtitles generated

**Remaining blocker:** EC2 public IP. Once CEO starts the instance and provides IP, executor can run all rendering/testing tasks.

| Day | Task | Status | Output | Notes |
|---|---|---|---|---|
| **Prerequisites** | | | | |
| 0 | Get EC2 public IP | ✅ Done | 18.234.250.128 | Running, confirmed via AWS console |
| 0 | Start EC2 + verify services | ✅ Done | All healthy | OVRTX gpu_initialized=true, all containers Up |
| 0 | Get Blockade Labs API key | ✅ Done | — | Used free tier web UI (5 credits) + 1 extra credit. No API key needed. |
| 0 | Get Deepgram API key | ✅ Done | `.env` | $200 free credit, key saved locally |
| 0 | Verify Daphne GLB on EC2 | ✅ Done | `/home/ubuntu/Daphne_Blender.fbx` | 188 MB FBX uploaded; GLB conversion pending |
| 0 | Verify trajectory JSON on EC2 | ✅ Done | `/home/ubuntu/cinematographer_trajectory.json` | 25s trajectory, 750 frames rendered to drone_pov_25s.mp4 |
| **Day 1 — Stage HDRIs** | | | | |
| 1.1 | Generate 6 HDRIs via Blockade Labs | ✅ Done | `stage_design/hdri/` | 6 × 8K equirectangular JPGs, $0 (free tier) |
| 1.2 | Test: HDRI as OVRTX dome light | ✅ Done (OVRTX fails, Blender works) | test frames | OVRTX can't load HDRI textures; switched to Blender EEVEE for all final renders |
| 1.3 | Modify render script for --hdri flag | ✅ Done | `render_trained_cinematographer.py` | Added --hdri + --lighting-preset flags |
| 1.4 | 🎯 QUALITY GATE: HERO test render | ✅ Approved | `demo_package/screenshots/hero_frame0_quality_gate.png` | "its looking ok" — approved, proceed with Blockade Labs HDRIs |
| **Day 2 — Lighting** | | | | |
| 2.1 | Download 6 Poly Haven lighting HDRIs | ✅ Done | `lighting/hdri/` | 6 × 1K HDRIs, CC0, ~1.5 MB each |
| 2.2 | Create `lighting/presets.py` | ✅ Done | `lighting/presets.py` | 6 modes, USDA + Blender output, HDRI map |
| 2.3 | Create `lighting/usda_lights.py` | ✅ Done | Merged into `presets.py` | `preset_to_usda()` generates USDA blocks |
| 2.4 | Test: lighting preset on HERO stage | ✅ Done | test frame | HERO lighting + HDRI verified in Blender render |
| **Day 3 — Character** | | | | |
| 3.1 | Upload Daphne to EC2 | ✅ Done | `/home/ubuntu/Daphne_Blender.fbx` | 188 MB FBX, rendering directly (no GLB conversion needed) |
| 3.2 | Create `stage_design/render_demo_blender.py` | ✅ Done | `stage_design/render_demo_blender.py` | Blender headless: char + HDRI + lights + camera |
| 3.3 | Test: Daphne + HERO stage + lighting in Blender | ✅ Done | test_daphne_blockade.mp4 | 5s test, camera tracks dancer, HDRI+lights work |
| 3.4 | 🎯 QUALITY GATE: Daphne on stage | ✅ Approved | hero_frame0_quality_gate.png | Combined with QG1 — "its looking ok" |
| **Day 4 — Voice** | | | | |
| 4.1 | Create `voice/voice_commander.py` | ✅ Done | `voice/voice_commander.py` | Deepgram live + SRT generator |
| 4.2 | Create `voice/demo_script.json` | ✅ Done | `voice/demo_script.json` | 11 commands over 90s |
| 4.3 | Test: Deepgram STT recognizes all 15 commands | ⏳ Pending | test log | Blocked on Deepgram key |
| **Day 5 — Mode transitions** | | | | |
| 5.1 | Create `stage_design/render_mode_switching_demo.py` | ✅ Done | `stage_design/render_mode_switching_demo.py` | Dual-HDRI crossfade + keyframed transitions |
| 5.2 | Test: 2-mode transition (BEAUTY → HERO) | ⏳ Pending | test video | Blocked on EC2 + HDRIs |
| 5.3 | 🎯 QUALITY GATE: Mode transition | ⏳ Pending | `demo_test_transition.mp4` | Human approval needed |
| **Day 6 — Full trajectory** | | | | |
| 6.1 | Add --mode-schedule to export script | ✅ Done | `export_cinematographer_trajectory.py` | Parses step:MODE pairs, injects into env |
| 6.2 | Export 90s trajectory with 8 mode switches | ✅ Done | `demo_90s_trajectory.json` | 4500 frames, 8 switches, v4 policy |
| 6.3 | Verify trajectory: correct duration + mode count | ✅ Done | — | 90.0s, 8 modes, positions vary, drone 4.3m from dancer |
| **Day 7-8 — Render all videos** | | | | |
| 7.1 | Render 6 × 25s single-mode videos | ✅ Done | `demo_package/mode_*.mp4` | All 6 modes: 1920x1080 EEVEE 64spp, quality-checked |
| 7.2 | Render 90s multi-mode demo reel | ✅ Done | `demo_package/demo_full_90s.mp4` | 14 MB, 2700 frames, 90s, all 8 mode switches |
| 7.3 | Render before/after comparison | ✅ Done | `demo_package/before_after.mp4` | 1.7 MB, ffmpeg hstack with text overlays |
| 7.4 | 🎯 QUALITY GATE: Full demo reel | 🔄 Awaiting approval | 90s video | **Human approval needed** |
| **Day 9 — Audio + subtitles** | | | | |
| 9.1 | Generate .srt from demo_script.json | ✅ Done | `voice/demo_commands.srt` | 11 subtitle entries |
| 9.2 | Add subtitles to demo reel | ✅ Done | `demo_full_90s_subtitled.mp4` | 16 MB, SRT overlay |
| 9.3 | Add music track (cosmic-hypnotic) | ✅ Done | `demo_full_90s_final.mp4` | 18 MB, AAC 192kbps, fade in/out |
| 9.4 | Extract 6 hero frames for one-pager | ✅ Done | `demo_package/screenshots/` | 6 PNGs extracted from frame 30 of each mode |
| **Day 10 — Package** | | | | |
| 10.1 | Assemble demo_package/ directory | ⏳ Pending | Full directory | |
| 10.2 | Update CAPABILITY_ONE_PAGER.md with screenshots | ⏳ Pending | Updated file | |
| 10.3 | Update CEO_BRIEFING.md with completion | ⏳ Pending | Updated file | |
| 10.4 | Final sprint cost report | ⏳ Pending | — | |

## Cost tracker

| Date | Action | Cost | Cumulative |
|---|---|---|---|
| 2026-05-25 | Local script builds (no EC2/API) | $0.00 | $0.00 |
| 2026-05-25 | 6 Blockade Labs HDRIs (free tier) | $0.00 | $0.00 |
| 2026-05-25 | EC2: 6×25s mode renders (~70 min) | $1.17 | $1.17 |
| 2026-05-25 | EC2: 90s multi-mode render (~53 min) | $0.88 | $2.05 |
| 2026-05-25 | EC2: trajectory export + misc (~15 min) | $0.25 | $2.30 |

## Blockers

- [x] ~~Need Blockade Labs API key~~ — RESOLVED: used free web UI, all 6 HDRIs downloaded
- [x] ~~Need Deepgram API key~~ — RESOLVED: $200 free credit, key in `.env`
- [x] ~~Need EC2 current public IP~~ — RESOLVED: 18.234.250.128, all services healthy

## Quality gates

- [ ] Day 1: HERO HDRI test render — looks like real concert stage?
- [ ] Day 3: Daphne on stage — character looks right with environment + lighting?
- [ ] Day 5: Mode transition — HDRI + lighting switch looks smooth?
- [ ] Day 8: Full 90s demo reel — ready to send to customers?
