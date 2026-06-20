# Module 9 — Lab Guide

**Mixed Reality — Your Virtual Objects in the Real Room**

> Use this alongside the Module 9 video. The video is the map (the MR pieces); this guide is the
> terrain (every exact step). By the end, passthrough shows your real room, the stone sits anchored
> on a real surface, and objects respect your real walls and floor.
>
> **Time:** ~50 min. **You need:** ZenSpace (Modules 1–8), a **Quest 3** (best passthrough), Claude
> Code in the project.

---

## Step 0 — Set up your space on the headset

1. On the Quest: **Settings → Physical space → Space Setup** — scan your room so the headset knows
   your walls, floor, and furniture.
2. This is what scene understanding and anchors rely on. Do it in the room you'll test in.

---

## Step 1 — Enable passthrough

1. On your **OVRCameraRig → OVR Manager**, set **Passthrough Support** to **Supported**.
2. Add the **OVR Passthrough Layer** component (Underlay) to the rig.
3. **Make the background transparent** so you see the real room, not a skybox:
   - Camera **Clear Flags → Solid Color**, color **(0,0,0,0)** (alpha 0)
   - Remove/disable any Skybox or `Environment` background

> Ask the agent: *"Enable Quest passthrough as an underlay and make my camera background fully
> transparent so I see my real room. List every setting to change."*

---

## Step 2 — Confirm you see your room

1. **Build and Run.** You should see your **real room** with your virtual stone + panel floating in it.
2. If you still see a virtual background, the camera background isn't transparent (Step 1) or a skybox is still active.

---

## Step 3 — Anchor an object to a real spot

```
Add spatial anchors so I can place the Stone on a real surface and have it stay there:
when I place/release it, create an OVR Spatial Anchor at that pose and save it; on next
launch, load saved anchors and restore the Stone to its real-world position. Tell me
exactly what to attach.
```

Test: place the stone on your real desk, quit, relaunch → it should reappear on the desk.

---

## Step 4 — Use scene understanding (objects respect the real room)

```
Use Quest Scene/Scene Understanding so my virtual objects respect the real room: let the
stone rest on the real floor or a real table, and stop objects from passing through real
walls. Use the scene's detected planes as colliders. Tell me what to enable.
```

> Requires the room scan from Step 0. The detected walls/floor become invisible colliders.

---

## Step 5 — Build the full MR scene (one request)

```
Convert my ZenSpace scene to mixed reality: passthrough on with a transparent background,
the Stone placeable + anchored to a real surface so it persists, and scene understanding
so objects rest on my real floor/desk and don't pass through real walls. Keep my existing
grab, audio, and menu working. Tell me each component to add and where.
```

Review, **Build and Run**, and place your objects around your real room.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Still see a virtual background | Camera Clear Flags not transparent (alpha 0), or a Skybox/Environment is still active. |
| Passthrough is black | Passthrough Support not "Supported" on OVR Manager, or no OVR Passthrough Layer. |
| Anchored object drifts / wrong spot | Room not scanned well — redo **Space Setup** (Step 0) in the test room. |
| Objects float or sink into furniture | Scene understanding off, or room data stale — re-run Space Setup and enable scene colliders. |
| Works in your room, breaks in another | Always re-scan each new physical space; don't hard-code positions. |

---

## ✅ Module 9 complete — you now have:

- Passthrough showing your real room behind virtual objects
- A transparent background (true mixed reality, not VR)
- Spatial anchors pinning objects to real places that persist
- Scene understanding so objects respect real walls and floors
- The rare, resume-defining MR skill

**Next module:** polish & performance — a rock-solid frame rate and a comfortable app. See you there.
