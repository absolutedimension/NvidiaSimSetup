# Module 1 Script — Your First VR Scene Running on Quest

> **Duration:** ~90 min (split into 8 lectures for Udemy)
> **Also serves as:** YouTube teaser (Lecture 1 + condensed version of Lectures 2-6)
> **Goal:** Student goes from zero to a VR room running on their Quest headset

---

## Lecture 1 [T1] (5 min) — Welcome — What We're Building
**[YOUTUBE HOOK — first 30 seconds are critical]**

### SCREEN: Show finished ZenSpace app running on Quest (screen recording)

> **[DEEPAK, face on camera]**
>
> By the end of today, your first VR scene will be running on your Quest headset.
> Not a tutorial. Not a demo someone else built. YOUR scene, running on YOUR headset.
>
> And by the end of this full course — 11 modules later — you'll have built a complete
> VR and Mixed Reality app, and submitted it to Meta's Store. And here's what makes this
> different from every other VR course out there:
>
> **You won't be typing code by hand.**
>
> We're going to use AI coding agents — Claude Code, specifically — to write our C# scripts.
> You describe what you want in plain English. The AI writes the code. You test it in VR.
> You iterate. That's how professional developers actually work in 2026.
>
> So even if you've never written a line of code — you can build this.

### SCREEN: Show the 11-module journey as a visual timeline

> Here's the journey. Module 1 — that's today — we set up Unity, configure it for Quest,
> and build our first VR room. Module 2, we set up our AI coding partner. Modules 3
> through 8, we add hands, UI, audio, movement, saving, and multiplayer. Module 9 — this
> is the one that makes your resume different — Mixed Reality. Your app objects placed in
> your real room through Quest 3 passthrough. Module 10, we polish for performance. And
> Module 11 — we submit to Meta's Store. Nobody else teaches that last step.
>
> My name is Deepak Kumar. I'm not just teaching this — I built a VR app called EnergyField
> that's currently in Meta's alpha program. I'm going to show you exactly how I did it,
> every step, every bug, every fix.
>
> Let's start.

---

## Lecture 2 [T2] (6 min) — Install Unity Hub & Unity 6 (part 1)
**[SCREEN RECORDING — Mac or Windows desktop]**

### What the student does along with you:

> **Step 1 — Download Unity Hub**
>
> Go to unity.com/download. Download Unity Hub. Install it. Open it.
>
> Unity Hub is just a launcher — it manages your Unity versions and your projects.
> You'll use it every time you start working.

### SCREEN: Unity Hub open, empty

> **Step 2 — Install Unity 6 LTS**
>
> Click "Install Editor" on the left. You'll see several versions.
> Pick **Unity 6 LTS** — the Long Term Support version. This is the stable one.
> Don't pick a tech preview or a beta. LTS means Meta has tested their SDK against it.

### SCREEN: Version selection, highlight Unity 6 LTS

> **Step 3 — Add Android Build Support**
>
> This is where most beginners miss a step and have to reinstall later.
>
> When the module selection screen appears, check these boxes:
> - **Android Build Support** — this is required. Quest runs Android.
> - **Android SDK & NDK Tools** — let Unity install these for you
> - **OpenJDK** — also let Unity handle this
>
> These three together let Unity compile your project into an APK — that's the file
> format Quest apps use. If you skip this, you'll get a "Build target not installed"
> error later and have to come back here anyway.

### SCREEN: Checkboxes highlighted, click Install

> This takes 10-20 minutes depending on your internet. While it installs, let me
> explain what we're building.

### SCREEN: ZenSpace concept art / sketch (simple)

> Our project across all 11 modules is called **ZenSpace** — a VR and MR meditation room.
> It's simple enough for a beginner but rich enough to teach every VR concept you need.
> And it's a legitimate app category on the Quest Store — wellness apps are growing fast.
>
> I chose this because it mirrors my own app, EnergyField. So every module, I can show
> you "here's how I solved this exact problem in my real shipped app."

### ON-SCREEN TEXT: "If Unity is still installing, pause here and come back when it's done."

---

## Lecture 3 [T2] (6 min) — Create Project & Install Meta XR SDK (part 1)

> Unity is installed. Let's create our project.

### SCREEN: Unity Hub → New Project

> **Step 1 — Create a new project**
>
> Click "New Project" in Unity Hub. Choose the **3D (URP)** template.
> URP stands for Universal Render Pipeline — it's optimized for mobile GPUs,
> which is what Quest has. Don't pick the "3D" core template or "HDRP" — those
> are too heavy for Quest.
>
> Name it **ZenSpace**. Pick a folder. Click Create.

### SCREEN: Unity Editor opens with empty URP project

> Unity's open. This is the Editor. Don't be overwhelmed — we'll learn it as we go.
> You need to know four panels right now:
> - **Scene view** — where you build your world (top left)
> - **Game view** — preview of what the player sees (tab next to Scene)
> - **Hierarchy** — list of everything in your scene (left side)
> - **Inspector** — properties of whatever you click on (right side)
>
> That's it. Four panels. Everything else can wait.

### SCREEN: Highlight each panel as you name it

> **Step 2 — Switch to Meta Quest build platform**
>
> Go to File → Build Profiles. Under Platforms, find **Meta Quest**. Click
> "Enable Platform." If it asks you to install the OpenXR package, click Install.
> Then click "Switch Platform."
>
> This tells Unity: "I'm building for Quest, not for PC."
>
> **Common error here:** if you don't see "Meta Quest" in the platform list,
> you're on an older Unity version. You need Unity 6 or later.

### SCREEN: Build Profiles → Meta Quest → Switch Platform

> **Step 3 — Install Meta XR SDK**
>
> Go to Window → Package Manager. In the top-left dropdown, switch to "My Assets."
>
> Now — open your web browser. Go to the Unity Asset Store. Search for
> **"Meta XR All-in-One SDK"** and click "Add to My Assets." It's free.
>
> Come back to Unity's Package Manager, refresh, and you'll see it in My Assets.
> Click "Meta XR All-in-One SDK" → Download → Import.
>
> This single package gives you everything: hand tracking, controllers, passthrough,
> spatial anchors, interaction toolkit — all of it.

### SCREEN: Package Manager → Meta XR All-in-One → Import

> When it finishes importing, Unity will ask about **Hand Skeleton Upgrade**.
> Select "Use OpenXR Hand." This is the modern standard.
>
> **Step 4 — Run the Project Setup Tool**
>
> Go to the top menu → Meta XR Tools → Project Setup Tool.
> You'll see a list of issues with "Fix" buttons. Click **"Fix All"** on both
> the Standalone tab and the Meta tab. Then click **"Apply All."**
>
> This auto-configures about 15 settings that you'd otherwise have to find
> manually in Project Settings. It sets the right color space, texture compression,
> minimum API level, and more.

### SCREEN: Project Setup Tool → Fix All → Apply All

> **Step 5 — Verify OpenXR settings**
>
> Go to Edit → Project Settings → XR Plug-in Management → OpenXR.
> Click the Android tab. Under Feature Groups, make sure **Meta XR** is checked.
> Under Features, make sure these are enabled:
> - Meta XR Feature
> - Meta XR Foveation *(if available)*
>
> You're configured. Let's build the room.

---

## Lecture 4 [T7] (6 min) — Build the ZenSpace Room (part 1)

> Right now your scene has a Main Camera and a Directional Light. We're going
> to replace the camera with Quest's VR camera and build a simple room.

### SCREEN: Hierarchy showing default scene

> **Step 1 — Replace the camera with OVRCameraRig**
>
> Delete the "Main Camera" in the Hierarchy.
>
> Then: right-click in the Hierarchy → search for **OVRCameraRig** (if using
> Meta's Building Blocks, you can drag it from the Building Blocks panel).
> Or go to the Project window, search for "OVRCameraRig" prefab, and drag
> it into the scene.
>
> This prefab is your player's head and hands in VR. It tracks your Quest
> headset position and your controllers/hands automatically.

### SCREEN: OVRCameraRig in Hierarchy, Inspector showing components

> **Step 2 — Create the floor**
>
> Right-click in Hierarchy → 3D Object → Plane.
> This gives you a flat 10m × 10m surface. That's our floor.
>
> In the Inspector, set Position to (0, 0, 0). Reset the scale to (1, 1, 1).
>
> Let's make it look nice. Create a new material: right-click in the Project
> window → Create → Material. Name it "FloorMat." Set the color to a warm
> dark wood tone — something like (0.15, 0.1, 0.08). Set Smoothness to 0.3.
> Drag the material onto the Plane.

### SCREEN: Floor with dark wood material

> **Step 3 — Create the walls**
>
> We'll use 4 Cubes stretched into wall shapes.
>
> Create a Cube (right-click → 3D Object → Cube). In the Inspector:
> - Position: (0, 1.5, 5) — this puts it at the far end
> - Scale: (10, 3, 0.1) — 10m wide, 3m tall, thin
>
> Duplicate it 3 times (Ctrl+D). Adjust positions and rotations:
> - Back wall: Position (0, 1.5, 5), Scale (10, 3, 0.1)
> - Front wall: Position (0, 1.5, -5), Scale (10, 3, 0.1)
> - Left wall: Position (-5, 1.5, 0), Scale (0.1, 3, 10)
> - Right wall: Position (5, 1.5, 0), Scale (0.1, 3, 10)
>
> Create a "WallMat" material — off-white, like (0.85, 0.82, 0.78). Apply to all walls.

### SCREEN: Room taking shape — floor + 4 walls

> **Step 4 — Lighting**
>
> Select the Directional Light in the Hierarchy. In the Inspector:
> - Rotation: (50, -30, 0) — angled warm light
> - Color: warm white (1.0, 0.95, 0.85)
> - Intensity: 1.2
>
> Now add a Point Light inside the room for ambiance:
> Right-click → Light → Point Light
> - Position: (0, 2.5, 0) — ceiling center
> - Color: warm amber (1.0, 0.85, 0.6)
> - Range: 12
> - Intensity: 0.8
>
> The room should now feel warm and inviting, not like a hospital.

### SCREEN: Room with warm lighting — actually looks pleasant

> **Step 5 — Add a simple object**
>
> Let's put something in the room so it doesn't feel empty.
>
> Create a Sphere. Position: (0, 0.5, 2) — in front of where you'll stand.
> Scale: (0.3, 0.3, 0.3) — about the size of a meditation stone.
> Create a material: dark grey, slightly rough. Apply it.
>
> Later in Module 3, we'll make this grabbable. For now, it's just scenery.

### SCREEN: Room with floor, walls, lighting, and a stone sphere

> **Step 6 — Set the player start position**
>
> Select the OVRCameraRig. Set its Position to (0, 0, 0).
> This means the player starts standing at the center of the room.
>
> The camera rig's Y position should be 0 — the OVR tracking system adds
> your actual height automatically. Don't set it to 1.7 or you'll be
> floating above the floor.

### SCREEN: OVRCameraRig at origin

> **Save your scene.** File → Save As → name it "ZenSpaceMain."
> Save your project too: File → Save Project.
>
> The room is built. Let's get it on your Quest.

---

## Lecture 5 [T4] (6 min) — Connect Quest & Build to Headset

> **Step 1 — Enable Developer Mode on your Quest**
>
> If you haven't done this yet:
> - Open the Meta Horizon app on your phone
> - Go to Devices → your Quest → Settings → Developer
> - Toggle on "Developer Mode"
> - Your Quest will restart
>
> This only needs to be done once. Without it, you can't sideload apps.

### ON-SCREEN TEXT: "Already enabled Developer Mode? Skip to Step 2."

> **Step 2 — Connect Quest to your PC**
>
> Plug in your USB-C cable. On the Quest, you'll see a popup:
> "Allow USB debugging?" — check "Always allow from this computer" and click Allow.
>
> In Unity, go to File → Build Profiles. Under "Run Device," you should see
> your Quest listed (something like "Quest 3 - XXXXXX"). Select it.
>
> **Common error:** "No devices found."
> Fix: Make sure USB debugging is allowed. Try a different USB port. Try a
> different cable. Some USB-C cables are charge-only — you need a data cable.

### SCREEN: Build Profiles showing Quest device

> **Step 3 — Build and Run**
>
> Click **"Build and Run."** Unity will ask where to save the APK file.
> Create a folder called "Builds" in your project and save it there.
>
> First build takes 2-5 minutes. Subsequent builds are faster.
>
> While it builds, let me tell you what's happening: Unity is compiling your
> C# scripts, packaging your assets (textures, materials, meshes), converting
> everything to Android format, creating an APK, pushing it to your Quest via
> USB, and launching it.

### SCREEN: Build progress bar

> **Step 4 — Put on your headset**
>
> The app should auto-launch. Put on your Quest.
>
> You should see:
> - The warm wood floor beneath you
> - Cream walls around you
> - A small grey stone sphere in front of you
> - Warm lighting from above
>
> Look around. You're standing in YOUR room. YOU built this.

### ON-SCREEN TEXT: "If you see a black screen, check Lecture 7 (Troubleshooting)."

> **Step 5 — What you should notice**
>
> - Your head movement is tracked — look around, look up, look down
> - If you have Quest 3, notice the passthrough fades in when you leave the
>   Guardian boundary — that's Quest's safety system
> - Your controllers aren't visible yet — we'll add those in Module 3
> - You can't grab the stone yet — that's also Module 3
>
> Right now, this is a static scene. Over the next 10 modules, it becomes
> an interactive VR/MR app that you submit to Meta.

---

## Lecture 6 [T5] (5 min) — Understanding What Just Happened

> Let's pause and understand what we just did, because this is the foundation
> everything else builds on.

### ON-SCREEN DIAGRAM: The VR development loop

```
Unity Editor (PC)          USB Cable           Quest Headset
┌────────────────┐        ┌───────┐          ┌──────────────┐
│ Scene + Scripts │──APK──▶│       │────────▶│ Android OS   │
│ + Assets       │        │       │          │ + VR Runtime │
│                │        │       │          │ + YOUR APP   │
└────────────────┘        └───────┘          └──────────────┘
     You edit here                              You test here
```

> This is the development loop you'll repeat hundreds of times:
> 1. Change something in Unity
> 2. Build to Quest
> 3. Test it in VR
> 4. Go back to Unity and adjust
>
> First build: 2-5 minutes. Incremental builds: 30-60 seconds. The faster
> this loop, the faster you develop. That's why we want it working perfectly.

### ON-SCREEN DIAGRAM: What's in your project

> Let's understand the project structure:
>
> - **OVRCameraRig** — this IS the player. It tracks your headset and hands.
>   Everything in VR is positioned relative to this.
> - **The room** (Plane + 4 Cubes) — static geometry. It doesn't move or do anything.
> - **Materials** — these define how surfaces look: color, roughness, how they
>   reflect light.
> - **Lights** — directional (sun-like) and point (bulb-like). On Quest, you want
>   to bake these for performance — we'll cover that in Module 10.
>
> That's it. A camera, some shapes, some materials, some lights. Every VR app
> in the world is built from these same pieces. Bigger apps just have more of them.

---

## Lecture 7 [T2] (6 min) — Troubleshooting Common Errors

> Things WILL go wrong. Here are the errors I've seen most often — in my own
> work and from other developers.

### Error 1: "Build target Android is not installed"

> You didn't add Android Build Support when installing Unity.
> Fix: Open Unity Hub → Installs → click the gear icon on your Unity version →
> Add Modules → check Android Build Support + SDK + NDK + JDK → Install.
>
> Takes 5 min. You don't lose your project.

### Error 2: "No Android devices found"

> Three possible causes:
> 1. Developer Mode not enabled on Quest → enable it in Meta Horizon app
> 2. USB debugging not allowed → put on Quest, accept the popup
> 3. Bad cable → try a different USB-C cable (must be data, not charge-only)
>
> On Windows, you might also need the Oculus ADB Drivers. Google "Oculus ADB
> Drivers download" and install them.

### Error 3: "Black screen when app launches on Quest"

> Usually means OVRCameraRig isn't configured correctly.
> Check: did you delete the original Main Camera? If both exist, they conflict.
> Check: is the OVRCameraRig's tracking origin set to "Floor Level"?
> Check: in OVR Manager (on the camera rig), is "Target Devices" set to "Quest 3"
> (or Quest 2, matching your headset)?

### Error 4: "App installs but immediately crashes"

> Check Unity Console (Window → Console) for red error messages before building.
> The most common cause: a script has a compile error. Fix all red errors first.
>
> Also check: are you using URP? If you accidentally created a non-URP project,
> some shaders won't compile for Quest.

### Error 5: "Scene is sideways / wrong orientation"

> OVRCameraRig expects Y-up. If your imported assets use Z-up (common from
> Blender), rotate them 90 degrees on the X axis.

> **Pro tip from my experience building EnergyField:** save your scene and project
> BEFORE every build. Unity occasionally corrupts unsaved work during a failed
> build. I learned this the hard way — lost 2 hours of work once.

---

## Lecture 8 [T1] (4 min) — Module 1 Recap + What's Next

> Let's recap what you just did:
>
> ✅ Installed Unity 6 with Android Build Support
> ✅ Created a URP project configured for Meta Quest
> ✅ Installed the Meta XR All-in-One SDK
> ✅ Built a VR room — floor, walls, lighting, a meditation stone
> ✅ Deployed it to your Quest headset
> ✅ Stood inside YOUR VR room for the first time
>
> That's Module 1. You have a working VR development pipeline.
> Everything from here builds on this.

### SCREEN: Preview of Module 2 — Claude Code setup

> **Next module: we set up our AI coding partner.**
>
> Instead of typing C# by hand, you'll describe what you want — "make this
> stone grabbable, play a chime when I pick it up, add haptic feedback" —
> and Claude Code will write the script for you. You review it, test it
> on Quest, iterate.
>
> This is how I built 80% of EnergyField. And it's how you'll build ZenSpace.

### **[YOUTUBE CTA — only for the YouTube version]**

> *This is Module 1 of 11 in my full course: "Build & Ship Your First VR/MR
> App — AI-Powered Development with Unity & Meta Quest."*
>
> *The full course takes you from what you just did all the way to submitting
> your app to Meta's Store — including Mixed Reality, multiplayer, and an
> AI coding workflow that means you don't need to know C#.*
>
> *Link in the description. See you in Module 2.*

---

## Production notes for Deepak

### Recording setup for this module:
- **Face-on-camera segments:** Lectures 1, 6, 8 — well-lit, clean background, energetic
- **Screen recording segments:** Lectures 2, 3, 4, 5, 7 — full screen, cursor visible,
  zoom in on important UI elements
- **Quest footage:** end of Lecture 5 — screen-record from Quest (use Meta Quest Developer
  Hub's casting feature or SideQuest screen mirroring)

### YouTube teaser cut (condensed version):
- Lecture 1 hook (30 sec) → condensed Lectures 2-5 (15 min, sped up boring parts) →
  Lecture 5 "put on headset" moment → Lecture 8 CTA
- Target YouTube length: ~20 min (long enough for watch time, short enough to finish)

### Assets needed before recording:
- [ ] ZenSpace concept sketch / logo (can be simple — Canva)
- [ ] 11-module timeline graphic
- [ ] Development loop diagram
- [ ] EnergyField screenshots (2-3 from your real app)

### Estimated recording time:
- First pass: 2-3 hours (including mistakes and retakes)
- Edit time: 1-2 hours (trim dead air, add zoom-ins, add text overlays)
- Total: ~4 hours for Module 1

---

*Sources:*
- [Meta: Set up Unity for VR Development](https://developers.meta.com/horizon/documentation/unity/unity-project-setup/)
- [Meta: Unity Hello World Tutorial](https://developers.meta.com/horizon/documentation/unity/unity-tutorial-hello-vr/)
- [Meta: Build Configuration Overview](https://developers.meta.com/horizon/documentation/unity/unity-build/)
- [Unity Manual: Meta Quest Build Profile](https://docs.unity3d.com/6000.3/Documentation/Manual/xr-meta-quest-build-profile.html)
- [Meta: XR Plugin Management](https://developers.meta.com/horizon/documentation/unity/unity-xr-plugin/)
- [Zero to Quest Guide](https://guidebook.hdyar.com/xr-dev/virtual-reality/zero-to-quest-meta-xr-sdk/)
