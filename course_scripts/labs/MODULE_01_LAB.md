# Module 1 — Lab Guide

**Your First VR Scene Running on Quest**

> Use this guide **alongside the Module 1 video**. The video is the map (what you're
> building and why). This guide is the terrain (every exact click, in order).
> Watch the video once, then work through these steps. Put on your headset when Step 5 says to.
>
> **Goal:** go from zero to your own VR room running on your Quest headset.
> **Time:** ~60–90 min the first time (most of it is downloads installing in the background).
> **You need:** a Windows or Mac computer, a Meta Quest 2 or 3, and a USB-C **data** cable.

---

## Step 0 — Before you start (checklist)

- [ ] A Meta Quest 2 or Quest 3 headset, charged
- [ ] A USB-C cable that carries **data** (not a charge-only cable — this trips people up)
- [ ] The Meta Horizon app installed on your phone, signed into the same account as your headset
- [ ] ~20 GB free disk space on your computer

---

## Step 1 — Install Unity Hub & Unity 6

1. Go to **unity.com/download**. Download **Unity Hub** and install it. Open it.
   - *Unity Hub is just a launcher — it manages your Unity versions and your projects.*
2. In Unity Hub, click **Install Editor** (left side). Pick **Unity 6 LTS**.
   - LTS = Long Term Support, the stable version Meta tests their SDK against.
   - ❌ Don't pick a tech preview or a beta.
3. On the module-selection screen, **check these three boxes** before clicking Install:
   - ☑ **Android Build Support** — required; Quest runs Android
   - ☑ **Android SDK & NDK Tools**
   - ☑ **OpenJDK**
   - *These three let Unity compile your project into an APK (the Quest app format). Skip them and you'll hit "Build target not installed" later and have to come back.*
4. Click **Install**. This takes 10–20 min depending on your internet. Let it run.

> ⚠️ **If you forgot the Android boxes:** Unity Hub → **Installs** → gear icon on your
> version → **Add Modules** → check Android Build Support + SDK + NDK + JDK → Install.
> You won't lose your project.

---

## Step 2 — Create the ZenSpace project

1. Unity Hub → **New Project**.
2. Choose the **3D (URP)** template.
   - URP = Universal Render Pipeline, optimized for mobile GPUs like Quest's.
   - ❌ Don't pick plain "3D" or "HDRP" — too heavy for Quest.
3. Name it **ZenSpace**. Pick a folder. Click **Create**.
4. When the Editor opens, learn just **four panels** for now:
   - **Scene view** — where you build (top-left)
   - **Game view** — preview of what the player sees (tab next to Scene)
   - **Hierarchy** — list of everything in your scene (left)
   - **Inspector** — properties of whatever you click (right)

---

## Step 3 — Switch to Quest + install the Meta XR SDK

1. **Switch build platform:** File → **Build Profiles**. Under Platforms, select
   **Meta Quest** → **Enable Platform** (install OpenXR if prompted) → **Switch Platform**.
   - ⚠️ No "Meta Quest" in the list? You're on an older Unity — you need Unity 6+.
2. **Get the SDK:** open your browser → **Unity Asset Store** → search
   **"Meta XR All-in-One SDK"** → **Add to My Assets** (it's free).
3. Back in Unity: **Window → Package Manager** → top-left dropdown → **My Assets** →
   refresh → select **Meta XR All-in-One SDK** → **Download** → **Import**.
   - *This one package gives you hands, controllers, passthrough, spatial anchors, interaction toolkit — everything.*
4. When prompted about **Hand Skeleton Upgrade**, choose **Use OpenXR Hand**.
5. **Run the Project Setup Tool:** top menu → **Meta XR Tools → Project Setup Tool** →
   click **Fix All** on both the Standalone and Meta tabs → **Apply All**.
   - *This auto-configures ~15 settings (color space, texture compression, min API level) you'd otherwise set by hand.*
6. **Verify OpenXR:** Edit → Project Settings → XR Plug-in Management → OpenXR → **Android tab**.
   Under Feature Groups, **Meta XR** is checked. Under Features: **Meta XR Feature** enabled
   (and **Meta XR Foveation** if available).

---

## Step 4 — Build the room

1. **Replace the camera:** delete **Main Camera** in the Hierarchy. Add **OVRCameraRig**
   (drag the prefab from the Project window, or use Meta's Building Blocks panel).
   - *OVRCameraRig IS the player — it tracks your headset and hands automatically.*
2. **Floor:** right-click Hierarchy → 3D Object → **Plane**. Inspector: Position **(0, 0, 0)**, Scale **(1, 1, 1)**.
   - Create a material: Project window → Create → Material → name **FloorMat** → color a warm dark wood **(0.15, 0.1, 0.08)**, Smoothness **0.3**. Drag it onto the Plane.
3. **Walls:** create a **Cube**, then duplicate (Ctrl/Cmd+D) to make four:
   | Wall | Position | Scale |
   |---|---|---|
   | Back | (0, 1.5, 5) | (10, 3, 0.1) |
   | Front | (0, 1.5, -5) | (10, 3, 0.1) |
   | Left | (-5, 1.5, 0) | (0.1, 3, 10) |
   | Right | (5, 1.5, 0) | (0.1, 3, 10) |
   - Create **WallMat**, off-white **(0.85, 0.82, 0.78)**, apply to all four.
4. **Lighting:**
   - Select the **Directional Light**: Rotation **(50, -30, 0)**, Color warm white **(1.0, 0.95, 0.85)**, Intensity **1.2**.
   - Add a **Point Light** (right-click → Light → Point Light): Position **(0, 2.5, 0)**, Color warm amber **(1.0, 0.85, 0.6)**, Range **12**, Intensity **0.8**.
5. **The stone:** create a **Sphere**, Position **(0, 0.5, 2)**, Scale **(0.3, 0.3, 0.3)**, dark-grey slightly-rough material. *(We make it grabbable in Module 3.)*
6. **Player start:** select **OVRCameraRig**, Position **(0, 0, 0)**.
   - ⚠️ Leave Y at **0** — OVR adds your real height automatically. Set it to 1.7 and you'll float.
7. **Save:** File → Save As → **ZenSpaceMain**. Then File → **Save Project**.

---

## Step 5 — Put it on your Quest 🥽

1. **Enable Developer Mode** (once): Meta Horizon phone app → Devices → your Quest →
   Settings → Developer → toggle **Developer Mode** on. The headset restarts.
2. **Connect:** plug in the USB-C cable. On the Quest, accept **"Allow USB debugging?"** →
   check "Always allow from this computer" → **Allow**.
3. In Unity: File → Build Profiles → under **Run Device**, select your Quest.
   - ⚠️ "No devices found"? See Troubleshooting → Error 2.
4. Click **Build and Run**. Save the APK into a new **Builds** folder. First build: 2–5 min.
5. **Put on the headset.** You should see: the warm wood floor, cream walls, the grey stone,
   warm light from above. **Look around — you're standing in YOUR room.**

> ⚠️ Black screen? See Troubleshooting → Error 3.

---

## Troubleshooting (the 5 you're most likely to hit)

1. **"Build target Android is not installed"** → you skipped Android Build Support. Unity Hub → Installs → gear → Add Modules → Android Build Support + SDK + NDK + JDK.
2. **"No Android devices found"** → (a) Developer Mode off → enable in Horizon app; (b) USB debugging not allowed → accept the headset popup; (c) charge-only cable → use a data cable. On Windows you may also need the **Oculus ADB Drivers**.
3. **Black screen on launch** → check you deleted the original Main Camera (two cameras conflict); OVRCameraRig tracking origin = **Floor Level**; OVR Manager "Target Devices" matches your headset.
4. **Installs but instantly crashes** → open Window → Console, fix all **red** errors before building. Confirm the project is **URP** (non-URP shaders won't compile for Quest).
5. **Scene is sideways** → OVRCameraRig expects **Y-up**. Blender assets are often Z-up — rotate them 90° on X.

> 💡 **Pro tip:** save your scene and project **before every build**. Unity can corrupt
> unsaved work during a failed build. (Learned the hard way — lost 2 hours once.)

---

## ✅ Module 1 complete — you now have:

- Unity 6 with Android Build Support
- A URP project configured for Meta Quest
- The Meta XR All-in-One SDK installed
- A VR room — floor, walls, lighting, a meditation stone
- It deployed and running on YOUR Quest headset

**Next module:** we set up your AI coding partner (Claude Code) so you build by describing,
not by typing. See you there.
