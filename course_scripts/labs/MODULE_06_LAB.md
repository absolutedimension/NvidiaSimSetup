# Module 6 — Lab Guide

**Movement & Locomotion — Teleport, Snap Turn & Comfort**

> Use this alongside the Module 6 video. The video is the map (movement styles + comfort); this
> guide is the terrain (every exact step). By the end, you teleport across a space bigger than your
> room, snap-turn, and move comfortably.
>
> **Time:** ~40 min. **You need:** ZenSpace (Modules 1–5), Claude Code in the project, your Quest.

---

## Step 0 — Before you start

- [ ] ZenSpace builds to your Quest
- [ ] Your floor (Plane) has a collider (it does by default)
- [ ] Claude Code running inside the project

---

## Step 1 — Add a locomotion system

The fastest path on Quest is Meta's **Building Blocks**:

1. **Meta → Tools → Building Blocks.**
2. Drag in the **"Locomotor"** / **"Player Controller"** block (it adds teleport + turn support to your rig).
   - *Alternatively, the Unity XR Interaction Toolkit ships a `Locomotion System` + `Teleportation Provider` + `Snap Turn Provider`.*

> Let the agent confirm: *"Confirm my OVRCameraRig has a locomotion system that supports teleport
> and snap turn, and list anything missing."*

---

## Step 2 — Mark the floor as teleportable

1. Select your **floor Plane**.
2. Add a **Teleportation Area** component (XRI) — *or* the Meta teleport-surface component from Building Blocks.
3. **Important:** add this ONLY to the floor, not the walls or ceiling, so users can't teleport up a wall.

---

## Step 3 — Add the teleport ray to a hand

1. On the right-hand controller / hand interactor, add a **teleport ray interactor** (Building Blocks adds this, or XRI's ray interactor set to teleport mode).
2. Set it to activate on a button hold (e.g. grip or A) or a thumbstick push-forward.

Test in the Editor (or build): hold the button, aim the arc at the floor, release → you jump there.

---

## Step 4 — Add snap turn

1. On the **left** thumbstick, add a **Snap Turn Provider** (XRI) or enable snap turn in the Building Blocks locomotor.
2. Set the turn angle to **30° or 45°** (comfortable steps).
3. Flick the stick left/right → the view rotates in clean steps, no dizzy spin.

---

## Step 5 — Add a comfort vignette

Ask the agent:

```
Add a comfort vignette that tunnels the edges of the view while the player is moving
(teleport dash or smooth glide) and fades away when still. Keep it subtle. Tell me
what to attach to the camera rig.
```

---

## Step 6 — Wire the whole movement system (one request)

```
Set up movement on my OVRCameraRig: teleport on the right hand that only lands on the
floor surface, snap turn (45 degrees) on the left thumbstick, and a subtle comfort
vignette during movement. Make teleport the default. Tell me exactly which components
to add and to which objects.
```

Review the setup, then **Build and Run** and move around.

---

## Step 7 — (Optional) offer smooth locomotion as a toggle

Some users prefer smooth. Add it as an **option**, never the forced default:

```
Add optional smooth locomotion on the left thumbstick that the user can enable from
the menu. Keep teleport as the default. When smooth is on, keep the comfort vignette
active.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Can teleport onto walls / ceiling | Teleportation Area is on the wrong objects — put it ONLY on the floor. |
| Fall through the floor on teleport | Floor missing a collider — add a Mesh/Box Collider to the floor. |
| Testers feel sick | Default to teleport, keep the vignette on, avoid forced smooth movement. |
| Snap turn spins too far / too fast | Lower the turn angle to 30–45°. |
| Teleport ray doesn't appear | Ray interactor not in teleport mode, or no activation button bound — re-check Step 3. |

---

## ✅ Module 6 complete — you now have:

- A locomotion system on your camera rig
- Floor-only teleport with an aiming arc
- Snap turn on the left stick
- A comfort vignette during movement
- The judgment to default to comfort and offer options

**Next module:** saving & persistence — your app remembers state between sessions. See you there.
