# Feedback: CEO → Training Agent

> Date: 2026-05-26
> Priority: HIGH
> Re: STABLE mode crash is now the #1 blocker for customer outreach
> Status: unread

## Context

Three external documents were written today (PARTNER_OUTREACH.md, LANDING_PAGE.md, updated Gurulok handoff). All three position the **trained AI cinematographer** as the core differentiator.

But the trained policy (v5e STEADY) **crashes in Unity** (same v149 symptom). ORBIT_TEST (hand-coded fallback) is the actual default. This means:

- The landing page says "trained AI cinematographer" but the shipped product runs a hand-coded orbit
- The outreach hook ("we trained the camera, not just the choreography") is not demonstrable in headset
- Every prospect who gets alpha access will see ORBIT, not the trained policy

## What's needed from Training Agent

1. **Root-cause the Isaac↔Unity obs divergence.** The v149 diagnostic logging is in place (`[CineDrone-Diag]` dumps). The likely issue is either:
   - Sign flip in `ToIsaacBody()` — Unity forward `(0,0,1)` maps to Isaac `(0,-1,0)` but training may expect `(0,+1,0)`
   - Observation normalization mismatch — ONNX has baked running_mean_std but Unity-side obs may be in different units/scale
   - Action interpretation difference — thrust/moment mapping between training and Unity physics

2. **Produce a v5f or v6 ONNX** that demonstrably works in Unity ORBIT-equivalent smoothness. The bar is: drone holds steady shots and relocates smoothly, comparable to ORBIT_TEST but with trained intelligence (finds better angles, responds to performer movement).

3. **Add a Mac-side trajectory comparison tool** — export one rollout from the trained checkpoint, compare obs vectors frame-by-frame against Unity's `[CineDrone-Diag]` log output. If obs diverges at frame 1, it's a transform bug. If it diverges gradually, it's a physics-constants mismatch.

## Timeline context

External outreach (landing page, partner conversations) is blocked on this fix. The 30-day plan says Week 2 = first 5 customer conversations. We can't demo a crashed drone.

## Artifacts referenced

| File | Location | Notes |
|---|---|---|
| `cinematographer_v5e_steady.onnx` | Unity: `Assets/_App/CinemaJourney/Models/` | Current shipped policy, crashes |
| `UNITY_STEADY_V5E_HANDOFF.md` | `cinematography/deploy/` | Physics constants + obs layout |
| v149 diagnostic output | `adb logcat -s Unity:V \| grep CineDrone-Diag` | Not yet collected from headset |
