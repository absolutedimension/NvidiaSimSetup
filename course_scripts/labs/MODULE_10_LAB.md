# Module 10 — Lab Guide

**Polish & Performance — Smooth, Comfortable, Finished**

> Use this alongside the Module 10 video. The video is the map (what to measure + fix); this guide
> is the terrain (every exact step). By the end, your app holds a steady 72 fps and feels polished.
>
> **Time:** ~50 min. **You need:** ZenSpace (Modules 1–9), Claude Code, your Quest.

---

## Step 0 — Turn on the on-headset stats

1. Connect your Quest; in **Meta Quest Developer Hub (MQDH)**, enable the **Performance / Metrics
   HUD** (or `adb shell setprop debug.oculus.fullRateCapture 1` style overlays).
2. This shows live FPS + GPU/CPU time while you wear the headset — your ground truth.

---

## Step 1 — Profile first (never guess)

1. **Window → Analysis → Profiler.** Build a **Development Build** and connect it to your Quest.
2. Look at the frame: is the tall bar in **Rendering** (graphics-bound) or **Scripts** (CPU-bound)?
3. Note the single biggest cost — that's what you fix first.

> Ask the agent: *"Here's my profiler summary: [paste]. What's my biggest performance cost and the
> highest-impact fix?"*

---

## Step 2 — Reduce draw calls

- **Static batching:** mark non-moving objects (floor, walls) as **Static** (top-right of the Inspector).
- **Share materials:** every unique material = more draw calls. Reuse one material across similar objects.
- **Combine meshes** where it makes sense.

```
Help me reduce draw calls in ZenSpace: mark the room geometry as static, share materials
across the walls/floor, and tell me the before/after draw-call count to check.
```

---

## Step 3 — Shrink textures

1. Select large textures → in the Inspector set **Max Size** to the smallest that still looks good
   (often 1024 or 512 for Quest).
2. Set **Compression** to a mobile-friendly format (ASTC).
3. Disable mipmaps only for UI; keep them for world textures.

---

## Step 4 — Bake the lighting (biggest win for a static scene)

1. Set your room lights' **Mode** to **Baked** (or **Mixed**).
2. Mark static geometry as **Contribute GI / Lightmap Static**.
3. **Window → Rendering → Lighting → Generate Lighting.** Wait for the bake.
4. Result: the room looks lit, but the GPU does almost no lighting work at runtime.

```
Set up baked lighting for my static ZenSpace room: mark the room static, set the lights
to Baked, and generate lightmaps. Keep the warm look from Module 1.
```

---

## Step 5 — Hit and hold 72 fps

1. Build a normal (non-development) build, wear the headset, watch the FPS HUD.
2. Move around, open the menu, grab objects — FPS should stay at **72** with no dips.
3. If it dips, go back to the profiler, find the new biggest cost, fix, repeat.

---

## Step 6 — Add polish

```
Add polish to ZenSpace: a gentle fade from black on startup, smooth transitions when the
Calm/Energize buttons change the room, and make sure every button gives instant visual +
audio feedback. Keep it subtle.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| FPS below 72 / stuttering | Profile to find the bottleneck; usually draw calls, overdraw, or real-time lights. |
| Frame drops only when moving | Too many real-time shadows/lights — bake them. |
| Memory warnings / crashes | Textures too large — shrink Max Size and use ASTC compression. |
| Looks worse after baking | Re-bake at higher lightmap resolution, or use Mixed mode for moving objects. |
| Editor is fine, Quest is slow | Always test ON the headset — the Editor runs on your PC, not the mobile GPU. |

---

## ✅ Module 10 complete — you now have:

- The habit of measuring with the profiler before fixing
- Fewer draw calls via static batching + shared materials
- Right-sized, compressed textures
- Baked lighting for near-free beauty
- A steady 72 fps and polished transitions — a shippable app

**Next module (the last):** ship it — package and submit to the Meta Store. See you there.
