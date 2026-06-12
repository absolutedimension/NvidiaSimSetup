# ADR-001: Use high-stiffness PD controllers for upper body pinning

**Date:** 2026-05-24
**Status:** accepted
**Decider:** Training Agent + Planning Agent
**Workstream:** Lower Body Physics

## Context

The lower body physics prediction system needs to pin the upper body to Quest tracking data
during Isaac Lab simulation. Two approaches exist:

## Decision

Use high-stiffness PD controllers (1000 N·m/rad stiffness, 100 N·m·s/rad damping) on the
upper body joints rather than directly overwriting joint positions via
`write_joint_position_to_sim()`.

## Alternatives considered

1. **Direct position write (`write_joint_position_to_sim`)** — rejected because it bypasses
   PhysX constraint solver. Forcibly setting joint positions mid-step can cause instability,
   especially with contact forces on feet propagating through the articulation chain.

2. **Kinematic body mode** — making upper body kinematic and lower body dynamic. Rejected
   because Isaac Lab's `Articulation` class doesn't cleanly support per-body kinematic mode,
   and it would break the AMP discriminator which expects a single articulation.

## Consequences

- **Positive:** PhysX maintains physical consistency. Forces from lower body (e.g., ground
  reaction) propagate naturally through the spine. No instability.
- **Positive:** Same actuation model as existing AMP humanoid — just different stiffness
  values per joint group.
- **Negative:** Upper body won't track Quest data *exactly* — there will be small tracking
  error proportional to 1/stiffness. At 1000 N·m/rad this should be <1° per joint.
- **Risk:** If external forces are large (e.g., humanoid falling), the PD controllers may
  not be stiff enough to maintain pinning. Mitigation: early termination on large tracking error.

## Related

- Lower body physics skill: `trigunai-lower-body-physics`
- Session log: `lower_body_physics/SESSION_LOWER_BODY.md`
- PhysX OOM constraints: `CLAUDE.md §19.8`
