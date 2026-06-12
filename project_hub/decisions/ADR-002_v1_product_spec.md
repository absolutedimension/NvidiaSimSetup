# ADR-002 — v1 Product Spec: Cinematographer Drone

> Date: 2026-05-25
> Status: LOCKED
> Decision by: Deepak (CEO)

## Decision

v1 product = **6 aesthetic modes + real-time voice switching + fly-to-mark boundary setup**

## The 6 modes (trained, operational)

| # | Mode | Behavior |
|---|---|---|
| 1 | HERO | Low-angle power shots, camera below waist looking up |
| 2 | INTIMATE | Close framing, face-focus, eye-level |
| 3 | EPIC | Wide establishing shots, bird's-eye moments |
| 4 | ENERGY | Fast-paced, beat-synced movement |
| 5 | SOLITUDE | Isolation framing, large negative space |
| 6 | BEAUTY | Balanced composition, rule-of-thirds, smooth orbits |

## Voice commands (~15-20 total)

**Mode switches:** "hero" / "intimate" / "epic" / "energy" / "solitude" / "beauty"
**Parameters:** "closer" / "farther" / "higher" / "lower" / "faster" / "slower"
**Control:** "hold" / "resume" / "stop" (emergency hover)

## Boundary: fly-to-mark

No maps. No GPS. No tablet-to-world alignment.

1. Director flies drone to each corner → presses MARK on tablet
2. Director flies to ceiling height → presses CEILING
3. Boundary defined in drone's own coordinate frame
4. Policy treats boundary edges as walls (smooth penalty gradient + hard cutoff)
5. Performer tracked visually by drone camera (no manual marking needed after first ID)

**Setup time: ~90 seconds.**

## Tablet display (live, not a pre-existing map)

Shows drone position within marked boundary, current mode, battery, emergency stop.
Built from drone's own sensor data — no external map source.

## Pre-flight sequence (90s total)

1. Fly-to-mark 4 corners + ceiling → boundary locked
2. Drone identifies performer visually
3. Director selects starting mode via voice or tablet

## Build estimate

| Task | Effort |
|---|---|
| Voice layer (Whisper local STT + command parser) | 3-4 days |
| Fly-to-mark boundary setup (tablet UI + drone recording) | 1 week |
| Boundary integration into policy (obs space + reward) | 3-4 days |
| Mode-transition smoothing | 1 week |
| Visual performer tracking integration | 1 week |
| End-to-end testing | 1 week |
| **Total** | **~5-6 weeks** |

## What this is NOT

- Not autonomous story understanding
- Not free-form natural language (that's Level 2, post-first-customer)
- Not vision-based auto-stage-detection (that's Approach 3, later)
- Not a consumer product — this is a B2B services tool for professional shoots

## Why this spec

Director keeps creative control. Drone provides superhuman execution. 90s setup, then voice-direct.
No competitor offers RL-trained cinematographic modes with real-time voice switching.
