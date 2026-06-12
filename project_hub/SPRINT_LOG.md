# Sprint Execution Log

## [2026-05-25 13:30] Session started
- EC2 IP: UNKNOWN (waiting for human)
- Services: UNCHECKED
- Current task: Day 0 prerequisites + local script builds (Days 2-5)
- Blockers: EC2 IP, Blockade Labs API key

## [2026-05-25 13:30] Local scaffolding
- Created directories: stage_design/hdri/, lighting/hdri/, voice/, demo_package/screenshots/
- Cost: $0
- Duration: instant

## [2026-05-25 13:35] Task 2.2: Created lighting/presets.py
- 6 mode presets (HERO, INTIMATE, EPIC, ENERGY, SOLITUDE, BEAUTY)
- Each preset has key + fill + rim/accent lights with mode-appropriate colors
- Dual output: `preset_to_usda()` for OVRTX pipeline, `preset_to_blender()` for Blender
- Includes HDRI prompt map and Poly Haven HDRI map for reference
- Cost: $0

## [2026-05-25 13:36] Task 4.2: Created voice/demo_script.json
- 11 voice commands over 90 seconds
- Mode sequence: BEAUTY→HERO→INTIMATE→EPIC→ENERGY→SOLITUDE→BEAUTY→HERO
- Includes "closer", "hold", "resume" parameter/control commands
- Cost: $0

## [2026-05-25 13:37] Task 4.1: Created voice/voice_commander.py
- Live Deepgram Nova-2 streaming STT integration
- 23 recognized commands (6 modes × aliases + 6 params + 3 controls)
- Fuzzy alias matching for common misrecognitions
- SRT subtitle generator subcommand (tested: produces valid SRT)
- Cost: $0

## [2026-05-25 13:38] Task 3.2: Created stage_design/render_demo_blender.py
- Blender 4.5 headless render script
- Imports character GLB/FBX, sets HDRI environment, adds preset lighting
- Animates camera along drone trajectory (look-at dancer)
- Renders PNG sequence → ffmpeg → MP4
- Supports both EEVEE (~0.5s/frame) and Cycles (~10s/frame)
- Cost: $0

## [2026-05-25 13:39] Task 5.1: Created stage_design/render_mode_switching_demo.py
- Multi-mode Blender render with dual-HDRI crossfade system
- Parses voice script for mode switches, keyframes mix factor transitions
- 1-second crossfade between HDRI environments at each voice command
- Inherits camera animation from trajectory JSON
- Cost: $0

## [2026-05-25 13:40] Task 1.3: Modified render_trained_cinematographer.py
- Added --hdri flag for DomeLight with HDRI texture
- Added --lighting-preset flag for mode-specific USDA light blocks
- Falls back to original 3-light setup when neither flag is set
- Cost: $0

## [2026-05-25 13:41] Task 6.1: Added --mode-schedule to export_cinematographer_trajectory.py
- Parses "step:MODE" pairs (e.g., "0:BEAUTY,400:HERO,750:INTIMATE")
- Injects mode index into env's _current_mode tensor at specified steps
- Records mode name per frame in trajectory JSON
- Cost: $0

## [2026-05-25 13:42] Task 9.1: Generated voice/demo_commands.srt
- Ran voice_commander.py srt subcommand
- 11 subtitle entries with 2-second display duration each
- Verified: valid SRT format, correct timestamps
- Cost: $0

## [2026-05-25 13:43] Task 2.1: Downloaded 6 Poly Haven HDRIs
- hero_lighting.hdr (studio_small_08) — 1.4 MB
- intimate_lighting.hdr (dancing_hall) — 1.6 MB
- epic_lighting.hdr (kloofendal_48d_partly_cloudy) — 1.6 MB
- energy_lighting.hdr (neon_photostudio) — 1.5 MB
- solitude_lighting.hdr (moonless_golf) — 1.6 MB
- beauty_lighting.hdr (photo_studio_loft_hall) — 1.6 MB
- All validated: #?RADIANCE header confirmed
- Cost: $0

## [2026-05-25 09:10] Session 2 started
- EC2 IP: 18.234.250.128
- Services: all healthy + isaaclab Up
- Current task: Day 7.1 (renders running), Day 6.2 (90s trajectory export)

## [2026-05-25 09:11] Task 7.1 resumed: 6 × 25s single-mode renders
- All 6 modes rendering via nohup on EC2 (Blender EEVEE 1920x1080 64spp)
- HERO: complete (4.1 MB, 750 frames, 25s @ 30fps)
- INTIMATE through BEAUTY: in progress (~15 min each)
- Cost: ~$0.25 (EC2 time)

## [2026-05-25 09:16] Task prep: Uploaded files to EC2
- render_mode_switching_demo.py (fixed HDRI filenames: hero_stage.hdr → hero_hdri.jpg)
- compose_demo.sh (before/after + screenshot extraction)
- demo_script.json + demo_commands.srt (voice script + subtitles)

## [2026-05-25 09:19] Task 6.2: Export 90s trajectory with mode schedule
- Fixed export script to use --task Isaac-Cinematographer-Direct-v4 (v0 had wrong obs/network dims)
- Ran inside isaaclab container: 4500 steps @ 50fps = 90s
- Mode schedule: 0:BEAUTY,400:HERO,1000:INTIMATE,1500:EPIC,2000:ENERGY,2750:SOLITUDE,3250:BEAUTY,3750:HERO
- Output: demo_90s_trajectory.json (1.6 MB, 4500 frames)
- Cost: $0

## [2026-05-25 09:24] Task 6.3: Verify trajectory
- Duration: 90.0s ✓
- Frame count: 4500 ✓
- Mode switches: 8 ✓
- Drone-dancer distance at t=0: 4.34m ✓
- Positions vary across time ✓
- VERIFICATION: PASSED

## [2026-05-25 10:34] Task 7.1 complete: All 6 × 25s single-mode renders
- HERO: 4.1 MB (mean=174.6, std=78.9) ✓
- INTIMATE: 2.9 MB (mean=207.4, std=66.3) ✓
- EPIC: 3.5 MB (mean=206.1, std=51.0) ✓
- ENERGY: 4.8 MB (mean=179.4, std=55.8) ✓
- SOLITUDE: 4.2 MB (mean=83.2, std=84.8) ✓
- BEAUTY: 1.3 MB (mean=224.4, std=55.8) ✓
- All 1920x1080, 25.0s, not black, not white, good pixel variation
- Total render time: ~70 min
- Cost: ~$1.17 (EC2 time)

## [2026-05-25 10:34] Tasks 7.3 + 9.4: Before/after + screenshots
- before_after.mp4: 1.7 MB, hstack with Before/After text overlays
- 6 hero frame PNGs extracted to demo_package/screenshots/
- Cost: $0 (ffmpeg only)

## [2026-05-25 10:35] Task 7.2 started: 90s multi-mode render
- Running via post_render_pipeline.sh Step 3
- 2700 frames at 1920x1080 EEVEE 64spp
- Estimated: ~63 min
- Dual-HDRI crossfade at each voice command timestamp

## [2026-05-25 11:28] Task 7.2 complete: 90s multi-mode render
- demo_full_90s.mp4: 14 MB, 1920x1080, 90.0s @ 30fps, 2700 frames
- All 8 mode switches with dual-HDRI crossfade
- Automated quality checks: 4 keyframes at t=0/30/60/85s all OK (mean 183–224, std 33–97)
- Render time: ~53 min
- Cost: ~$0.88 (EC2 time)

## [2026-05-25 11:29] Tasks 9.2 + 9.3 complete: Subtitles + music
- demo_full_90s_subtitled.mp4: 16 MB (SRT overlay via ffmpeg)
- demo_full_90s_final.mp4: 18 MB (subtitles + cosmic-hypnotic music, AAC 192kbps, fade in/out)
- Audio track: cosmic-hypnotic.mp3, trimmed to 90s with fade
- Cost: $0

## [2026-05-25 11:30] Quality Gate 4 (Day 8): Full demo reel — AWAITING APPROVAL
- Presenting quality_gate_grid.jpg (8 keyframes across all modes)
- Files ready: demo_full_90s_final.mp4 (18 MB, 90s, 1920x1080, music + subtitles)
- HDRI environments visible in HERO, INTIMATE, EPIC, SOLITUDE modes
- BEAUTY mode is bright/washed (expected — fashion runway HDRI)
- Character (Daphne) visible as white/untextured figure throughout
- Camera follows trained cinematographer trajectory with mode-appropriate motion
