# Module 3 — Lab Guide

**Hands & Grabbing — Real Hand Tracking in Your VR Room**

> Use this guide alongside the Module 3 video. The video is the map (the interaction model).
> This guide is the terrain (every exact step). By the end, you grab objects in your room with
> your bare hands or controllers, with glow, sound, and haptics.
>
> **Time:** ~45 min. **You need:** the ZenSpace project (Modules 1–2), Claude Code running inside
> it, and your Quest.

---

## Step 0 — Before you start

- [ ] ZenSpace opens in Unity 6 and still builds to your Quest
- [ ] The grabbable stone from Module 2 works with a controller
- [ ] Claude Code is running inside the ZenSpace folder (`cd ZenSpace` → `claude`)

---

## Step 1 — Turn on hand tracking

1. **Edit → Project Settings → XR Plug-in Management → OpenXR → Android tab.**
2. Under **Features**, enable **Hand Tracking Subsystem** (and confirm **Meta XR Feature** is on).
3. On your **OVRCameraRig**, find the **OVR Manager** component → set **Hand Tracking Support**
   to **Controllers and Hands**.
4. On the headset (once): **Settings → Movement tracking → Hand tracking → On**.

> Tip — let the agent confirm: *"Check my OVRCameraRig is set up for both controllers and hand
> tracking, and tell me anything missing."*

---

## Step 2 — Understand the two halves (interactor + interactable)

You don't need to memorize the API — just hold the model:

- **Interactor** = the thing that grabs → your **hand** or **controller** (already on the OVRCameraRig).
- **Interactable** = the thing that *can* be grabbed → the **stone** (and soon, everything else).

The fastest path is Meta's **Building Blocks**: **Meta → Tools → Building Blocks**. From there you
can drag in ready-made **Hand Grab**, **Distance Grab**, and **Poke** interactors and interactables.

---

## Step 3 — Make the stone hand-grabbable

Ask the agent (it knows your project from Module 2):

```
In my ZenSpace scene, the Sphere "Stone" is already controller-grabbable. Make it
ALSO hand-grabbable using the Meta XR Interaction SDK: add a HandGrabInteractable,
a grab point, and a collider sized to the stone so my fingers can catch it. List
the exact components to add in the Inspector and confirm it still works with controllers.
```

Follow its Editor steps. You'll typically end up with, on the Stone:
- a **Grabbable**
- a **HandGrabInteractable** (+ a child grab-point transform)
- a **Collider** (SphereCollider) matching the stone's size
- a **Rigidbody** (set to **Is Kinematic** if you don't want it to fall)

---

## Step 4 — Add feedback (glow + sound + haptics)

Feedback is what makes it feel real. Ask the agent:

```
Add interaction feedback to the Stone: make it glow (emission) while a hand or
controller is hovering, play a soft chime when grabbed, and trigger a short haptic
buzz on the grabbing controller. Keep it simple and tell me where to assign the
audio clip.
```

Assign a short chime `.wav` where it tells you.

---

## Step 5 — Make the whole room grabbable (one request)

Now scale it. Ask:

```
Apply the same setup to every pickup object in my room (the stones / props): hand +
controller grab, glow on hover, chime + haptic on grab. Give me a single reusable
script or prefab I can drop on any object, and tell me how to apply it to each.
```

Review the script it writes, then apply it per the agent's instructions.

---

## Step 6 — Test on your Quest

1. Save scene + project. **Build and Run.**
2. Put the controllers down and use your **bare hands** — reach out, pinch, lift.
3. Then try **distance grab**: point at a far object and pull.
4. Confirm: glow on hover, chime + buzz on grab.

🎉 Your room is now something you touch, not just look at.

---

## Step 7 — Pick the right grab type

| Grab type | Use it for | Component |
|---|---|---|
| **Hand grab** | Objects right in front of you, natural pinch | HandGrabInteractable |
| **Distance grab** | Objects across the room (force-pull) | DistanceHandGrabInteractable |
| **Poke** | Buttons, panels, menus (Module 4) | PokeInteractable |

Ask the agent to switch a given object to a different grab type whenever it feels wrong.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Hands don't appear | Hand tracking off — Step 1; on headset Settings → Movement tracking → Hand tracking → On. |
| Hands appear but jitter / vanish | Room too dark, or hands outside the cameras' view (keep them in front of you). Add light. |
| Grab won't trigger | Collider too small or missing — make it match the object; confirm a Grabbable + HandGrabInteractable are present. |
| Object falls through the floor | Add a Rigidbody, set **Is Kinematic**, or give the floor a collider. |
| Works with controller, not hand | Missing HandGrabInteractable or no hand grab point — re-run Step 3 and ask the agent to verify. |
| `Oculus.Interaction` type not found | Meta XR SDK not fully imported — redo Module 1 Step 3. |

---

## ✅ Module 3 complete — you now have:

- Hand tracking enabled on your OVRCameraRig
- The interactor + interactable model in your head
- A stone you can grab with hand OR controller, with glow + chime + haptics
- A reusable setup applied across your whole room
- The judgment to pick hand / distance / poke grabs

**Next module:** floating UI and menus you press with your finger. See you there.
