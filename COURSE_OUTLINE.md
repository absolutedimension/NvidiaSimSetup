# Course Outline — Build & Ship Your First VR/MR App

> **Full title:** Build & Ship Your First VR/MR App — From Unity Zero to Meta Quest Store
> **Subtitle:** Build a real VR/MR app using AI coding agents + Unity. Submit to Meta. No fluff.
> **Total:** 11 modules · ~14 hours of video · Beginner to Shipped
> **Created:** 6 June 2026 · Day 2 of launch workflow
> **Updated:** 6 June 2026 — added AI coding agent workflow (Module 2) as core differentiator

---

## Design principles

1. **Every module produces something the student can show.** No theory-only modules.
2. **Build ONE app across all 11 modules.** Not 11 separate demos — one growing project.
3. **AI coding agents (Claude Code / Cursor) are the default workflow**, not manual typing.
   Students learn to DESCRIBE what they want, let the agent write the code, understand
   the output, test in VR, and iterate. This is how professional developers work in 2026.
4. **Module 1 = setup. Module 2 = AI agent workflow. Modules 3–8 = build skills.
   Module 9 = MR (the differentiator). Module 10 = polish. Module 11 = ship.**
5. **Each module is 60–90 min of video.** Students can finish one module per day.
6. **Show YOUR app (EnergyField) as reference** throughout — "here's how I solved this
   in my real shipped app."
7. **Students who CAN'T code are welcome.** The AI agent handles the C# — the student
   learns to direct it. Students who CAN code learn to 10x their speed.

---

## The student's project: "ZenSpace"

A VR/MR meditation + focus room app. Why this project:
- Simple enough for a beginner (no complex game logic)
- Rich enough to teach every core VR/MR concept (hands, UI, physics, audio, MR)
- Legitimate app category on Quest Store (wellness is growing)
- Mirrors Deepak's own EnergyField app — teach from REAL experience
- Not a game — appeals to Priya persona ("I want to build apps, not shooters")
- Portfolio-worthy — interviewers find a wellness app more interesting than another shooter

**What ZenSpace does when finished:**
- VR mode: immersive meditation room with ambient sounds, interactive objects (stones,
  candles, a journal), hand tracking, and a breathing guide UI
- MR mode: passthrough — virtual zen objects placed in your REAL room
- Publishable to App Lab with all Meta requirements met

---

## Module 1: Setup — Unity, Quest & Your Dev Environment
**"From zero to headset in 90 minutes"**

| Item | Detail |
|---|---|
| **Duration** | ~90 min |
| **Outcome** | Unity installed, project configured, a simple room running on your Quest headset |
| **YouTube teaser** | Yes — this module IS the free YouTube video |

### What the student learns:
- Install Unity Hub + Unity 6 (LTS) + Android Build Support
- Create a new 3D project
- Install Meta XR SDK via Package Manager
- Configure project settings for Quest (Android platform, Vulkan, texture compression)
- Set up OVR Camera Rig + OVR Manager
- Build the ZenSpace room — a simple floor, 4 walls, soft lighting, skybox
- Connect Quest via USB/Quest Link
- Build & Run → see YOUR scene in VR for the first time

### Key teaching moments:
- "Here's what it looked like the first time I got EnergyField running on Quest" (screenshot)
- Common error: "Build failed — Android SDK not found" → exact fix
- Common error: "Black screen on Quest" → OVR Manager settings fix

### Student can show:
> A VR room running on their Quest. They can put on the headset and look around.

---

## Module 2: Your AI Coding Partner — Building VR with Claude Code
**"You describe it. The AI builds it. You ship it."**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | Student has Claude Code (or Cursor/Copilot) set up, can prompt it to write Unity C# scripts, understands the AI-assisted VR development workflow |

### Why this module exists:
Most VR courses assume you'll manually type every C# script. In 2026, that's like
teaching someone to build a website by hand-writing HTML in Notepad. Professional
developers use AI coding agents. This course teaches the MODERN workflow:

```
You DESCRIBE what you want in plain English
  → AI agent writes the C# script
    → You review and understand the code
      → You test it in VR on your Quest
        → You tell the agent what to fix
          → Iterate until it works
```

**This means: even students with ZERO coding experience can build a real VR app.**
The AI handles the syntax. The student handles the vision, the testing, and the
understanding.

### What the student learns:

**Part A — Setup (20 min):**
- What are AI coding agents? (Claude Code, Cursor, GitHub Copilot — what's different)
- Install Claude Code (terminal-based, works with any editor)
- OR: Install Cursor (VS Code fork with AI built in)
- Connect to your Unity project folder
- The key concept: the agent sees your ENTIRE project — scripts, scenes, prefabs, errors

**Part B — The Core Workflow (30 min):**
- **Prompt 1:** "Create a C# script that makes a cube spin when I look at it in VR"
  - Watch the agent write the script
  - Read through what it wrote — line by line explanation of key concepts
  - Drag the script onto a cube in Unity → Build → Test on Quest
  - It works (or doesn't) → tell the agent what happened → iterate
- **Prompt 2:** "The cube spins too fast and I want it to change color when I grab it"
  - Watch the agent modify the existing script
  - Understand: variables, Update(), GetComponent — taught through the agent's output
- **Prompt 3:** "Add haptic feedback when I grab the cube"
  - The agent knows the Meta XR SDK API — it writes the OVRInput.SetControllerVibration call
  - You didn't need to memorize the API — you described what you wanted

**Part C — Effective Prompting for Unity VR (25 min):**
- **Good prompt:** "Create a grabbable meditation stone using XR Interaction Toolkit.
  When the player picks it up, play a soft chime sound and add slight haptic feedback
  to the controller. Use OVR hand tracking if available, fall back to controllers."
- **Bad prompt:** "Make object grabbable" (too vague — agent doesn't know which toolkit,
  what feedback you want, or which input system)
- **The 5-part VR prompt template:**
  1. What component/behavior do you want?
  2. Which SDK/toolkit should it use? (Meta XR SDK, XR Interaction Toolkit, etc.)
  3. What's the interaction trigger? (grab, gaze, proximity, button press)
  4. What feedback should the user get? (visual, audio, haptic)
  5. Any constraints? (performance, Quest-specific, hand tracking vs controllers)
- **Debugging with the agent:** paste Unity console errors → agent explains + fixes
- **Scene description prompts:** "Look at my current scene hierarchy and suggest what
  scripts I need for a meditation breathing guide with a pulsing sphere"

### Key teaching moments:
- "I built 80% of EnergyField's code using AI agents. Here's my actual prompt history."
- "The agent writes the code. YOUR job is: (a) know what to ask for, (b) understand
  enough to verify it works, (c) test it in VR, (d) describe what's wrong if it isn't."
- "You don't need to memorize C# syntax. You DO need to understand what a MonoBehaviour
  is, what Update() does, and what a coroutine is — because the agent will use them and
  you need to read its output."
- **The 20% you MUST understand** (brief C# survival guide):
  - MonoBehaviour = a script that attaches to a GameObject
  - Start() = runs once when the scene loads
  - Update() = runs every frame (60–90 times per second in VR)
  - public variables = visible in Unity Inspector (drag-and-drop references)
  - GetComponent<T>() = get another component on the same object
  - Coroutines = do something over time (fade, animate, wait)
  - "If you understand these 6 concepts, you can read ANY script the agent writes."

### Student can show:
> They prompted Claude Code to create a spinning, color-changing cube with haptic feedback — and it runs on their Quest. They didn't write a single line manually.

### Tools supported (student picks one):
| Tool | Cost | Best for |
|---|---|---|
| **Claude Code** (recommended) | Free tier available, Pro $20/mo | Terminal users, most capable for large Unity projects |
| **Cursor** | Free tier, Pro $20/mo | VS Code users, visual, good Unity integration |
| **GitHub Copilot** | Free tier, Pro $10/mo | Already using VS Code, lighter assistance |
| **ChatGPT + manual paste** | Free | Budget option — copy prompts, paste code manually |

---

## Module 3: Hands & Controllers — Interacting with the World
**"Touch, grab, throw — making VR feel real"**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | Hand tracking + controller input working, can grab and throw objects |

### What the student learns:
- Enable hand tracking in OVR Manager
- Set up hand models (OVR Hand Prefab) — see your real hands in VR
- Controller tracking — visualize Quest controllers in-scene
- XR Interaction Toolkit: Grab Interactable + Grab Interactor
- Build grabbable objects for ZenSpace: meditation stones, a candle, a journal
- Physics: Rigidbody + colliders so objects feel solid
- Throw mechanics — velocity tracking on release
- Haptic feedback on grab (controller vibration)

### Key teaching moments:
- "Hand tracking vs controllers — when to use which" (design decision, not just code)
- Gotcha: "Objects fly through walls" → continuous collision detection
- Show EnergyField's hand interaction as reference

### Student can show:
> Pick up a meditation stone with their bare hand, throw it, feel the haptic buzz.

---

## Module 4: VR UI — Menus, Buttons, and Panels That Work
**"Building interfaces that don't make people sick"**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | World-space UI with working buttons, a settings panel, and a breathing guide timer |

### What the student learns:
- World-space Canvas (NOT screen overlay — causes VR sickness)
- Curved UI panel placement — comfortable viewing angles and distances
- Laser pointer interaction (ray-based UI input from controllers)
- Poke interaction (finger-based UI input from hand tracking)
- Build ZenSpace UI: main menu, settings panel, session timer
- Build the breathing guide: an animated circle that expands/contracts with a timer
- Toggle switches, sliders (volume, ambient sound level)
- UI audio feedback (click sounds, hover sounds)

### Key teaching moments:
- "Never put UI on a flat screen overlay in VR. Here's why — and what to do instead."
- Font size matters in VR — 24pt minimum, tested at arm's length
- Show how EnergyField handles its journey selection menu

### Student can show:
> A floating menu in their VR room. Tap buttons with their finger. Adjust a slider. Start a breathing session.

---

## Module 5: Environment & Audio — Making VR Feel Like a Place
**"The difference between a demo and an experience"**

| Item | Detail |
|---|---|
| **Duration** | ~60 min |
| **Outcome** | ZenSpace feels like a real place — ambient audio, particle effects, lighting, skybox |

### What the student learns:
- Skybox selection and custom skybox (equirectangular image from Blockade Labs / Poly Haven)
- Lighting setup: baked vs realtime, light probes for Quest performance
- Particle systems: floating dust motes, candle flame, subtle fog
- Spatial audio: AudioSource 3D settings, ambient loops, interaction sounds
- Audio mixer: background vs UI vs interaction channels
- Import free assets: Poly Haven materials, Sketchfab models (CC0)
- Scene composition — where to place objects for VR comfort

### Key teaching moments:
- "Quest has a mobile GPU — here's what you CAN'T do" (no realtime shadows on everything)
- Free asset sources: Poly Haven, Sketchfab, Unity Asset Store freebies
- "How I chose the audio for EnergyField's cosmic journey"

### Student can show:
> Walk into their ZenSpace and it FEELS like a calm meditation room — sounds, particles, warm lighting.

---

## Module 6: Locomotion — Moving Through VR Without Getting Sick
**"Teleport, smooth move, or stay still — and why it matters"**

| Item | Detail |
|---|---|
| **Duration** | ~60 min |
| **Outcome** | Teleportation + smooth locomotion + snap turn + room-scale boundaries |

### What the student learns:
- Teleportation system: aim arc, valid/invalid landing zones, fade transition
- Smooth locomotion: thumbstick movement with vignette comfort overlay
- Snap turn vs smooth turn (comfort options)
- Room-scale: Guardian/boundary system awareness
- NavMesh for valid movement areas
- Build for ZenSpace: teleport between meditation spots, smooth walk around the room
- Player preferences: let the user CHOOSE their comfort mode in settings

### Key teaching moments:
- "Smooth locomotion makes 30% of people sick. Here's how to offer both and let users choose."
- VR comfort rating system (Meta's Comfortable / Moderate / Intense labels)
- How this affects your Store listing

### Student can show:
> Teleport to the candle corner, smooth-walk to the journal, snap-turn to look around. Comfort settings in their menu.

---

## Module 7: Saving Data & Session Logic
**"Your app remembers the user"**

| Item | Detail |
|---|---|
| **Duration** | ~60 min |
| **Outcome** | App saves user preferences and session history. Logic drives a real experience flow. |

### What the student learns:
- PlayerPrefs for simple key-value storage (volume, comfort mode, last session)
- JSON serialization for structured data (session log, user stats)
- File I/O on Quest (Application.persistentDataPath — Android-specific gotchas)
- Build for ZenSpace: save settings across sessions, track "sessions completed" counter,
  show "welcome back" message with last session date
- State machine basics: app states (Menu → Session → Summary → Menu)
- Coroutines for timed sequences (breathing guide, session timer, fade transitions)
- Scene management: loading/unloading scenes for different meditation environments

### Key teaching moments:
- "Your app MUST remember settings. Nobody wants to reconfigure comfort mode every launch."
- Quest file system quirks — where files actually live, what survives app updates
- "How EnergyField tracks journey progress across sessions"

### Student can show:
> Close the app, reopen it, and their settings + session count are preserved. The app greets them by session number.

---

## Module 8: Multiplayer Basics — Sharing VR With Others
**"Two people in the same virtual room"**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | Two Quest headsets can join the same ZenSpace room and see each other |

### What the student learns:
- Photon Fusion (or Normcore) — free tier setup, room creation, joining
- Network object spawning — each player gets a networked avatar
- Simple avatar: floating head + hands (no full body needed)
- Voice chat (Photon Voice or Normcore audio)
- Synchronized objects — both players see the same candle flame, same journal
- Ownership and authority — who controls what
- Build for ZenSpace: "Invite a friend" button, shared meditation session

### Key teaching moments:
- "Multiplayer is optional for App Lab submission — but it 10x's your app's value"
- Free tier limits: Photon's 20 CCU free, Normcore's limits
- "How I would add multiplayer to EnergyField — the architecture I'd use"

### Student can show:
> Two people in the same meditation room, seeing each other's hands, hearing each other's voice.

---

## Module 9: Mixed Reality & Passthrough — VR Meets Your Real Room
**"The skill most senior VR devs don't have yet"**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | ZenSpace works in MR mode — virtual objects placed in the student's real room via passthrough |

### What the student learns:
- Enable passthrough in OVR Manager (Quest 3 / Quest Pro)
- Passthrough layer configuration — full passthrough vs selective
- Scene API: room mesh, walls, floor, furniture detection
- Spatial Anchors: place a virtual object at a real-world position, persist across sessions
- Build for ZenSpace MR mode: virtual candle on your real desk, meditation stones on
  your real floor, breathing guide floating in front of you in your real room
- Toggle VR ↔ MR mode from the settings menu
- Depth occlusion — real objects in front of virtual objects (advanced, brief intro)

### Key teaching moments:
- "MR is where the industry is going. Quest 3, Apple Vision Pro — it's all passthrough."
- "This is the module that makes your resume different from every other VR dev applicant."
- Scene API gotchas: room setup required, what happens when user hasn't set up their room
- Show a live demo of MR in action (screen recording from Quest)

### Student can show:
> Virtual meditation objects placed on their REAL desk and floor, visible through Quest passthrough. Switch between full VR and MR with a toggle.

---

## Module 10: Performance & Polish — Making It Quest-Ready
**"The difference between a prototype and a product"**

| Item | Detail |
|---|---|
| **Duration** | ~60 min |
| **Outcome** | App runs at stable 72fps on Quest, looks polished, handles edge cases |

### What the student learns:
- Unity Profiler on Quest — how to find what's slow
- Draw call batching — static batching, GPU instancing
- Texture compression (ASTC) and atlas optimization
- LOD (Level of Detail) for complex objects
- Shader optimization — use Quest-friendly shaders (Mobile/URP Lit, not Standard)
- Target 72fps (Quest 2) / 90fps (Quest 3) — how to measure and hold it
- App icon and splash screen
- Loading screen (required by Meta VRC guidelines)
- Error handling — what happens when tracking is lost? When battery is low?
- Accessibility: text size, color contrast, comfort options

### Key teaching moments:
- "Meta will REJECT your app if it drops below 72fps. Here's how to guarantee it."
- The VRC checklist — walk through every item your app must pass
- "The 3 bugs that failed my first EnergyField submission and how I fixed them"

### Student can show:
> App runs smooth at 72fps. Has a proper icon, splash screen, loading screen. Handles edge cases gracefully.

---

## Module 11: Ship It — From Build to Meta Store
**"The module nobody else teaches"**

| Item | Detail |
|---|---|
| **Duration** | ~75 min |
| **Outcome** | Student has submitted their app to Meta's App Lab / Horizon Store |

### What the student learns:
- Create a Meta Developer account (if not already done)
- Create an Organization in the Developer Dashboard
- Create a new App — app name, category, comfort rating
- App signing: upload keystore, manage signing keys (CRITICAL — lose this, lose your app)
- Build a release APK (not debug!) from Unity
- Upload APK via Meta Quest Developer Hub (MQDH) or CLI
- Store listing: description, screenshots (required sizes), trailer video, privacy policy
- Privacy policy — yes you need one, here's a template
- Content guidelines — what Meta allows and rejects
- Age rating questionnaire
- Submit for review
- What to expect: review timeline (3–7 business days), common rejection reasons, how to respond
- After approval: sharing your App Lab link, getting your first users

### Key teaching moments:
- "This is where 80% of indie devs give up. The submission process isn't hard — it's just
  undocumented and full of gotchas. I'm walking you through every screen."
- Live walkthrough of the Developer Dashboard (screen recording)
- "My first submission was rejected for [X]. Here's the fix that got it approved."
- Privacy policy template (the student can copy and customize)
- "You now have a shipped VR app. Put this on your resume. Hand interviewers a headset."

### Student can show:
> Their app submitted to Meta. A Store listing with their name on it. A link they can share with anyone.

---

## Module summary table

| # | Module | Duration | Track | Student builds | Key differentiator |
|---|---|---|---|---|---|
| 1 | Setup — Unity, Quest & Dev Environment | 90 min | Setup | Room running on Quest | YouTube teaser — gets students hooked |
| 2 | **AI Coding Partner — Claude Code** | **75 min** | **AI Workflow** | **AI-generated spinning cube with haptics** | **NO other VR course teaches this** |
| 3 | Hands & Controllers | 75 min | Interaction | Grab/throw objects | Hand tracking + AI-prompted scripts |
| 4 | VR UI | 75 min | Interface | Menus + breathing guide | Poke interaction + AI-built UI logic |
| 5 | Environment & Audio | 60 min | Polish | Atmospheric room | Free assets + AI scene composition |
| 6 | Locomotion | 60 min | Movement | Teleport + smooth move | Comfort options as design decision |
| 7 | Saving & Session Logic | 60 min | Logic | Persistent data + state machine | AI writes the serialization code |
| 8 | Multiplayer | 75 min | Network | 2-player shared room | Free tier Photon, AI-prompted networking |
| 9 | **Mixed Reality** | 75 min | **MR** | **Passthrough + spatial anchors** | **Least taught, most in-demand** |
| 10 | Performance & Polish | 60 min | Quality | 72fps, polished UX | VRC checklist + AI-assisted profiling |
| 11 | **Ship It** | 75 min | **Launch** | **Submitted to Meta** | **Nobody else teaches this** |
| | **Total** | **~14 hours** | | | |

---

## AI agent integration across ALL modules

The AI coding agent isn't just Module 2 — it's the workflow for the ENTIRE course.
Every module from 3 onwards follows this pattern:

```
┌─────────────────────────────────────────────────────────────┐
│  EACH MODULE'S AI WORKFLOW:                                 │
│                                                             │
│  1. EXPLAIN the concept (what is hand tracking? what is     │
│     a Rigidbody?) — 10-15 min theory                        │
│                                                             │
│  2. PROMPT the agent — show exact prompt on screen,         │
│     watch it generate the C# script — 5-10 min              │
│                                                             │
│  3. READ the code together — line-by-line explanation of    │
│     what the agent wrote and WHY — 15-20 min                │
│     (this is where real learning happens)                   │
│                                                             │
│  4. TEST in VR — build to Quest, try it — 5-10 min          │
│                                                             │
│  5. ITERATE — "it doesn't feel right / it's broken" →       │
│     tell the agent → watch it fix — 10-15 min               │
│                                                             │
│  6. CHALLENGE — student modifies the prompt to add their    │
│     own twist (different sound, different behavior) — HW    │
└─────────────────────────────────────────────────────────────┘
```

### Example prompts shown in each module:

| Module | Exact prompt shown to student |
|---|---|
| 3 (Hands) | "Create a GrabbableStone.cs script using Meta XR SDK. When the player grabs it with OVR hand tracking, play an AudioClip and trigger 0.3s haptic feedback. If hand tracking isn't available, fall back to controller grab." |
| 4 (UI) | "Build a WorldSpaceMenu.cs with 3 buttons: Start Session, Settings, Quit. Use Unity's Canvas in world space, positioned 1.5m in front of the player at chest height. Add OVR ray interactor support for controllers and poke interaction for hand tracking." |
| 5 (Audio) | "Create an AmbientSoundManager.cs that plays 3 looping AudioClips with spatial audio. Each source should be at a different position in the room. Add a public volume slider that saves to PlayerPrefs." |
| 6 (Locomotion) | "Build a TeleportManager.cs using XR Interaction Toolkit. Show a parabolic aim arc from the right controller thumbstick. Valid landing zones are tagged 'Teleportable'. Add a 0.2s fade-to-black transition. Include a comfort vignette option toggled from settings." |
| 7 (Saving) | "Create a SessionManager.cs that tracks: sessions completed (int), total minutes meditated (float), last session date (string), and user's comfort mode preference (enum). Save to JSON at Application.persistentDataPath. Load on Start(), save on session end." |
| 8 (Multi) | "Set up Photon Fusion networking. Create a NetworkPlayerAvatar.cs that spawns a head + two hand transforms, synced across the network. Add Photon Voice for spatial voice chat. Max 4 players per room." |
| 9 (MR) | "Enable Quest 3 passthrough. Create a SpatialAnchorPlacer.cs that lets the player place a virtual candle on any real-world surface detected by Scene API. The candle should persist across sessions using spatial anchors." |
| 10 (Polish) | "Analyze my project for Quest performance issues. List any scripts using Update() that could be optimized. Check texture sizes and suggest ASTC compression settings. Verify we meet Meta VRC guidelines for 72fps." |

### Why this approach unlocks non-coders:

Traditional VR course: "Type this C# code exactly as shown" → student copies, doesn't understand, can't modify.

Our course: "Tell the agent what you want" → student sees the code generated → instructor explains it → student modifies the prompt → gets a different result → UNDERSTANDS through iteration.

**The student learns C# concepts by READING AI output, not by memorizing syntax.**
This is how humans actually learn languages — immersion + comprehension, not grammar drills.

---

## Udemy section structure

Udemy organizes courses into "Sections" (our modules) and "Lectures" (individual videos).
Each module should be split into 5–8 lectures of 8–15 min each.

**Example for Module 2 (AI Coding Partner):**
1. What are AI coding agents? Claude Code vs Cursor vs Copilot (8 min)
2. Installing Claude Code + connecting to your Unity project (10 min)
3. Your first prompt: spinning cube with haptics (12 min)
4. Reading the code: C# survival guide (MonoBehaviour, Update, variables) (15 min)
5. Prompt engineering for Unity VR: the 5-part template (10 min)
6. Debugging with the agent: paste errors, get fixes (10 min)
7. Challenge: prompt the agent to build YOUR idea (5 min)

**Total lectures across 11 modules:** ~70–80 lectures (Udemy prefers 50+ for "complete" label).

---

## What existing courses DON'T teach (our gap advantage)

| Topic | Top Udemy course teaches it? | Our course? |
|---|---|---|
| Unity setup + first build | ✅ | ✅ |
| **AI coding agent workflow** | ❌ (none) | ✅ Module 2 + every module |
| **Prompting for Unity C#** | ❌ (none) | ✅ Exact prompts per module |
| Controllers + grab | ✅ | ✅ |
| Hand tracking | Partially | ✅ Full |
| VR UI (world-space) | Partially | ✅ + poke interaction |
| Teleportation | ✅ | ✅ + comfort options |
| **Saving data / persistence** | ❌ | ✅ |
| **State machine / app logic** | ❌ | ✅ |
| Multiplayer | Separate course ($) | ✅ Included |
| **MR / Passthrough** | ❌ (separate course) | ✅ Module 9 |
| **Performance profiling** | ❌ | ✅ |
| **VRC checklist** | ❌ | ✅ |
| **Store submission** | ❌ | ✅ Module 11 |
| **"My real app" reference** | ❌ (no instructor has shipped) | ✅ EnergyField |

**We cover 15/15. The top competitor covers 5/15.** That's the gap.
The AI coding agent integration alone makes this the only course of its kind.

---

## Prerequisites (for Udemy listing)

**Required:**
- A Windows PC (Mac works for development but can't build to Quest natively)
- Meta Quest 2, Quest 3, or Quest Pro headset
- USB-C cable (for Quest Link / building)
- No prior Unity or VR experience needed — we start from zero

**Helpful but not required:**
- Basic programming knowledge (any language)
- Basic 3D concepts (what a mesh, texture, material is)

---

## The course title (updated)

**Title:** Build & Ship Your First VR/MR App — AI-Powered Development with Unity & Meta Quest

**Subtitle:** Use AI coding agents (Claude Code) to build a real VR/MR app from scratch. Hand tracking, passthrough MR, multiplayer — and submit it to Meta's Store. No coding experience required.

**Why "AI-Powered" in the title:**
- Immediately differentiates from every other VR course
- Attracts both coders (who want to 10x their speed) and non-coders (who couldn't take traditional courses)
- SEO: "AI" + "VR" + "Meta Quest" captures a search intersection nobody else owns
- Honest: this IS how the app gets built

---

## Next steps

- [ ] Day 3 (Jun 7): Script Module 1 in full — this is the YouTube teaser
- [ ] Day 4 (Jun 8): Script Modules 2-3 (AI workflow + Hands)
- [ ] Day 5 (Jun 9): Script Modules 4-5 (UI + Environment) + YouTube channel setup
- [ ] Day 6 (Jun 10): Script Modules 6-7 (Locomotion + Saving)
- [ ] Day 7 (Jun 11): Script Modules 8-11 (Multiplayer + MR + Polish + Ship) + VR classroom design

---

*Sources:*
- [Meta: Unity Hello World for Quest](https://developers.meta.com/horizon/documentation/unity/unity-tutorial-hello-vr/)
- [Meta: Unity Development Overview](https://developers.meta.com/horizon/documentation/unity/unity-development-overview/)
- [Meta: Submitting Your App](https://developers.meta.com/horizon/resources/publish-submit/)
- [Meta: VRC Guidelines](https://developers.meta.com/horizon/resources/publish-quest-req/)
- [Meta: App Lab Submission Tips](https://developers.meta.com/horizon/blog/how-to-prepare-for-a-successful-app-lab-submission/)
- [Meta: Get Apps Ready for Horizon Store](https://developers.meta.com/horizon/blog/get-apps-ready-app-lab-meta-horizon-store-meta-quest-developers/)
- [Udemy: VR Development Fundamentals](https://www.udemy.com/course/oculus-quest-development-with-unity/)
- [Unity Manual: Meta Quest Workflow](https://docs.unity3d.com/6000.2/Documentation/Manual/xr-meta-quest-develop.html)
