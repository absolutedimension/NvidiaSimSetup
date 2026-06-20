# Module 4 — Lab Guide

**UI & Menus in VR — A Floating Panel You Press With Your Finger**

> Use this alongside the Module 4 video. The video is the map (the UI model + design rules);
> this guide is the terrain (every exact step). By the end, a floating panel with three working
> buttons lives in your room, pressed by your fingertip.
>
> **Time:** ~45 min. **You need:** ZenSpace (Modules 1–3), Claude Code running inside it, your Quest.

---

## Step 0 — Before you start

- [ ] ZenSpace builds to your Quest and hand grabbing from Module 3 works
- [ ] Claude Code running inside the project (`cd ZenSpace` → `claude`)
- [ ] A short ambient `.wav` for the "Calm" button (any soft loop)

---

## Step 1 — Create a world-space canvas

1. In the Hierarchy: **right-click → UI → Canvas.**
2. Select the Canvas. In the Inspector, set **Render Mode → World Space**.
   - *This is the key switch — it turns the canvas from a screen overlay into a real 3D panel.*
3. Set the Canvas **Rect Transform**:
   - Width 600, Height 400 (we'll scale it down next)
   - **Scale** 0.001 on X, Y, Z (UI units are huge; this shrinks it to room scale)
4. Position it about **0.5 m in front** of where the player stands, at **~1.3 m height**, tilted slightly toward the user.

> Let the agent sanity-check: *"Is my world-space canvas sized and placed for comfortable arm's-length use on Quest?"*

---

## Step 2 — Add a background + a button + a label

1. Right-click the Canvas → **UI → Panel** (a translucent dark background).
2. Right-click the Panel → **UI → Button - TextMeshPro** (import TMP Essentials if asked).
3. Make the button **big** — Width ~200, Height ~80. Set its label text.
4. Add a **UI → Text - TextMeshPro** for a title at the top.

---

## Step 3 — Make it pokeable (finger press)

The Meta XR SDK connects your fingertip to Unity UI via poke. Easiest path is Building Blocks:

1. **Meta → Tools → Building Blocks.**
2. Drag in the **"Poke Interaction (UI)"** / **"Pointable Canvas"** block (names vary by SDK version).
3. It adds the components that let a poke interactor drive your Canvas buttons.

> If the block names differ, ask the agent: *"Wire my world-space Canvas so its buttons can be
> pressed by the Meta XR poke interactor (hand + controller). List the exact components to add."*

---

## Step 4 — Make the buttons do things (one request)

Ask the agent:

```
On my world-space Canvas, create three buttons: "Calm", "Energize", "Reset".
- Calm: fade in a soft ambient AudioSource
- Energize: raise the scene's light intensity (Directional + Point light)
- Reset: return the lights and any moved objects to their starting state
Wire each button's onClick to a method in one simple controller script, make the
buttons pokeable with my finger, and tell me exactly what to attach and where to
assign the ambient clip.
```

Review the script it writes (a small `MenuController.cs` with `Calm()`, `Energize()`, `Reset()`),
assign the audio clip where it says, and hook each button's **OnClick** to the matching method.

---

## Step 5 — Test on your Quest

1. Save scene + project → **Build and Run.**
2. Reach out and **poke** each button with your fingertip.
   - Calm → ambience fades in. Energize → room brightens. Reset → back to start.
3. Confirm the panel sits at a comfortable arm's length and the text is readable.

🎉 Your app now has a menu the user controls from inside VR.

---

## Step 6 — Design rules (apply these every time)

| Rule | Why |
|---|---|
| **Big, well-spaced targets** | Fingers are far less precise than a mouse |
| **~Arm's length away** | Closer strains the eyes; farther is unreachable |
| **High contrast, few words** | Reading in VR is harder than on a screen |
| **Fix the panel in the room** | A menu parented to the camera that chases your head is nauseating |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Buttons won't press | Missing the pokeable/pointable-canvas setup (Step 3), or panel too far to reach. |
| Text is blurry | Canvas scale too large or reference resolution too low — shrink the canvas, raise resolution. |
| Menu follows my head | It's parented to the OVRCameraRig — unparent it and place it in the world. |
| Poke goes through the button | The button needs a collider/raycast target from the pointable-canvas block — re-run Step 3. |
| Panel is gigantic or microscopic | World-space canvas Scale should be ~0.001; adjust until it's ~0.4 m wide. |

---

## ✅ Module 4 complete — you now have:

- A world-space canvas floating in your room
- A panel with three big, pokeable buttons
- Calm / Energize / Reset, each changing the room
- The VR UI design rules in your head
- The line crossed from tech demo to controllable app

**Next module:** spatial audio — sound that comes from real places in your room. See you there.
