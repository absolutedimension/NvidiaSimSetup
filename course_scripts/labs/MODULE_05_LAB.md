# Module 5 — Lab Guide

**Audio & Ambience — A Living Soundscape in Your VR Room**

> Use this alongside the Module 5 video. The video is the map (the audio layers); this guide is
> the terrain (every exact step). By the end, the stone's chime comes from the stone in 3D space,
> and a soft ambience fills your room.
>
> **Time:** ~40 min. **You need:** ZenSpace (Modules 1–4), Claude Code in the project, your Quest,
> and a few short `.wav` clips (a chime, a soft hum, an ambient loop).

---

## Step 0 — Gather clips

- [ ] A short **chime** `.wav` (grab sound)
- [ ] A short **hum** `.wav` (hover)
- [ ] A **looping ambient** `.wav` (wind / drone / room tone) — freesound.org has free ones
- [ ] Drag all three into your project's `Assets/Audio` folder

---

## Step 1 — Make the stone sound spatial

1. Select the **Stone** in the Hierarchy.
2. **Add Component → Audio Source.**
3. On the Audio Source:
   - Assign **AudioClip** = your chime
   - Uncheck **Play On Awake** (we play it on grab)
   - Set **Spatial Blend** slider all the way to **3D** (1.0) — *this is the key setting*
   - Open **3D Sound Settings**: set a sensible **Max Distance** (e.g. 10) so it fades with distance
4. Now ask the agent to fire it on grab:

```
On my Stone, play its AudioSource when the object is grabbed (hand or controller).
The AudioSource is already set to 3D spatial blend with the chime assigned. Update
the grab script to call audioSource.Play() on grab.
```

---

## Step 2 — Test the spatial chime

1. **Build and Run.** Grab the stone with your **left** hand.
2. You should hear the chime **from your left**, at the stone's position — not centered in your head.
3. Walk toward / away — it should get louder / softer.

> If it sounds the same everywhere, **Spatial Blend is still 2D** — set it to 3D (Step 1).

---

## Step 3 — Add an ambient bed

1. Create an empty GameObject: **right-click Hierarchy → Create Empty**, name it **Ambience**.
2. Add an **Audio Source**:
   - AudioClip = your ambient loop
   - **Loop** = on, **Play On Awake** = on
   - **Spatial Blend** = **2D** (or very low) so it surrounds the user evenly
   - **Volume** low (~0.2–0.3) — it should sit *under* everything
3. Press Play in the Editor — the room should feel fuller immediately.

---

## Step 4 — Add reactive sound (hover + buttons)

Ask the agent:

```
Add reactive audio: a soft hum (2D-ish, quiet) when a hand hovers a grabbable object,
and a gentle click sound on each UI button poke. Reuse the AudioSources where sensible,
keep volumes balanced and gentle, and tell me which clips to assign where.
```

---

## Step 5 — Build the whole soundscape (one request)

```
Give every grabbable object a 3D chime when grabbed, a soft hover hum, a calm ambient
loop that plays under everything, and a gentle click on every UI button. Balance the
volumes so nothing is harsh, keep the ambient bed quiet, and give me one place to tune
the overall mix. Tell me exactly which clips to assign.
```

Review the script, assign clips where it says, then **Build and Run** and listen.

---

## Step 6 — Mixing for comfort

| Layer | Spatial Blend | Volume | Notes |
|---|---|---|---|
| Object sounds (chime) | **3D** | medium | Comes from the object's position |
| Reactive (hover/click) | 2D or low-3D | low–medium | Quick, gentle confirmation |
| Ambient bed | **2D** | **low** (~0.2) | Surrounds evenly, never competes |

Keep the total mix gentle — VR audio sits close to the ears; harsh or loud sounds fatigue fast.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Sound is the same volume everywhere | Spatial Blend still 2D — set the object's AudioSource to **3D**. |
| No sound on grab | Play On Awake is off (correct) but the grab script isn't calling `Play()` — re-run Step 1's prompt. |
| Crackling / distortion | Too many simultaneous sources, or a clip that clips — lower volumes, reduce concurrent sounds. |
| Ambient drowns everything | Ambient volume too high — drop it to ~0.2 and keep it 2D. |
| Chime sounds centered in my head | Spatial Blend not fully 3D, or Max Distance too large — set Blend to 1.0, tune 3D settings. |

---

## ✅ Module 5 complete — you now have:

- A stone whose chime comes from its real position in 3D space
- A soft ambient bed filling the room
- Reactive hover and button sounds
- A balanced, comfortable mix
- The understanding that sound is half of presence

**Next module:** movement — teleport and glide through a space bigger than your room. See you there.
