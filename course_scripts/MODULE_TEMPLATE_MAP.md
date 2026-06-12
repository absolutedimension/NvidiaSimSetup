# Module → Template Map (pre-computed recommendations)

> Use this as a cheat sheet when scripting each module.
> Each row = one ~3-6 min section. Copy the sections into your module script and fill in content.

---

## Module 2: AI Coding Partner — Claude Code (~75 min, 12 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why AI coding changes everything | Motivation — hook them on the workflow |
| 2 | T3 | 5 | The AI-assisted development loop | Draw the 6-step cycle: describe→generate→read→test→iterate→ship |
| 3 | T2 | 6 | Install Claude Code (or Cursor) | Procedural — terminal/VS Code setup |
| 4 | T2 | 6 | Connect to your Unity project | Procedural — open project, show agent sees files |
| 5 | T2 | 6 | Prompt 1: spinning cube that responds to gaze | Live demo — type prompt, watch agent write code |
| 6 | T3 | 4 | Reading C# the agent wrote — the 6 concepts you need | Tablet annotation — MonoBehaviour, Start, Update, etc. |
| 7 | T4 | 5 | Build to Quest and test the spinning cube | Physical demo — put on headset, see it work |
| 8 | T2 | 6 | Prompt 2: add color change + grab | Iterate — modify existing script via agent |
| 9 | T2 | 6 | Prompt 3: add haptic feedback | Show agent knows Meta XR SDK API |
| 10 | T3 | 5 | The 5-part VR prompt template | Draw the template structure, examples |
| 11 | T2 | 5 | Debugging with the agent — paste Unity errors | Procedural — show error→fix flow |
| 12 | T1 | 3 | Recap + "you didn't write a single line" | Forward-looking, Module 3 preview |

**Mix: T1 10% · T2 48% · T3 23% · T4 8%**

---

## Module 3: Hands & Controllers (~75 min, 12 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why touch is what makes VR feel real | Motivation |
| 2 | T3 | 5 | Hand tracking vs controllers — when to use which | Concept — draw comparison table |
| 3 | T2 | 6 | Enable hand tracking in OVR Manager | Procedural — Unity Inspector settings |
| 4 | T4 | 5 | See your real hands in VR | Physical demo — hands in headset |
| 5 | T2 | 6 | Set up controller tracking + hand models | Procedural — prefabs and config |
| 6 | T2 | 6 | XR Grab Interactable: make the stone grabbable | AI prompt → code → attach to object |
| 7 | T4 | 5 | Grab the stone with your bare hand | Physical demo — the payoff moment |
| 8 | T2 | 5 | Add Rigidbody + colliders for physics | Procedural — mass, gravity, collision |
| 9 | T3 | 4 | Why objects fly through walls (and the fix) | Concept — continuous collision detection |
| 10 | T2 | 6 | Throw mechanics — velocity tracking on release | AI prompt → code |
| 11 | T4 | 5 | Throw the stone across the room | Physical demo — Quest mirror + hands |
| 12 | T1 | 3 | Recap: you built VR touch interaction | Forward-looking |

**Mix: T1 8% · T2 42% · T3 18% · T4 24%**

---

## Module 4: VR UI (~75 min, 12 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why screen UI makes people sick in VR | Motivation — frames the problem |
| 2 | T3 | 5 | World-space Canvas: how VR UI works | Draw the spatial UI model vs screen overlay |
| 3 | T2 | 6 | Create a world-space Canvas + first button | Procedural — Unity Canvas setup |
| 4 | T3 | 4 | Comfortable viewing: distance, angle, font size | Draw comfort zone diagram |
| 5 | T2 | 6 | Laser pointer input from controllers | Procedural — ray interactor setup |
| 6 | T2 | 6 | Poke input from hand tracking (finger tap) | Procedural — poke interactor setup |
| 7 | T4 | 5 | Test both input methods on Quest | Physical demo — tap button with finger |
| 8 | T2 | 6 | Build the ZenSpace main menu panel | AI prompt → full menu UI |
| 9 | T2 | 6 | Build the breathing guide (animated circle + timer) | AI prompt → animation code |
| 10 | T2 | 5 | Toggle switches and sliders (volume, settings) | Procedural — UI components |
| 11 | T2 | 5 | UI audio feedback (click/hover sounds) | Procedural — AudioSource on buttons |
| 12 | T1 | 3 | Recap: spatial UI that feels native | Forward-looking |

**Mix: T1 8% · T2 56% · T3 13% · T4 7%**

---

## Module 5: Environment & Audio (~60 min, 10 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | The difference between a demo and an experience | Motivation |
| 2 | T3 | 5 | Lighting on mobile GPU — what you can and can't do | Draw baked vs realtime comparison |
| 3 | T2 | 6 | Skybox from Blockade Labs (free AI-generated) | Procedural — import equirect, apply |
| 4 | T2 | 6 | Baked lighting + light probes for Quest | Procedural — Unity Lightmapper |
| 5 | T2 | 6 | Particle systems: dust motes, candle flame | Procedural — particle settings |
| 6 | T3 | 4 | Spatial audio: how 3D sound works in VR | Draw audio source/listener model |
| 7 | T2 | 6 | Audio setup: ambient loops + interaction sounds | Procedural — AudioSource, mixer |
| 8 | T2 | 6 | Import free assets (Poly Haven, Sketchfab) | Procedural — download, import, apply |
| 9 | T4 | 5 | Walk through the finished room on Quest | Physical demo — the "wow" moment |
| 10 | T1 | 3 | Recap: your room feels like a real place | Forward-looking |

**Mix: T1 10% · T2 53% · T3 15% · T4 8%**

---

## Module 6: Locomotion (~60 min, 10 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why movement in VR can make you sick | Motivation + safety context |
| 2 | T3 | 5 | Three movement systems and who they're for | Draw teleport/smooth/roomscale comparison |
| 3 | T2 | 6 | Teleportation: aim arc + valid zones + fade | Procedural — XRI teleport setup |
| 4 | T2 | 6 | Smooth locomotion with comfort vignette | Procedural — thumbstick + vignette |
| 5 | T2 | 5 | Snap turn vs smooth turn | Procedural — both options |
| 6 | T2 | 6 | NavMesh: where the player CAN and CAN'T go | Procedural — bake NavMesh |
| 7 | T4 | 5 | Test all three modes on Quest | Physical demo — teleport, walk, turn |
| 8 | T2 | 6 | Settings menu: let user choose comfort mode | AI prompt → preference saving |
| 9 | T3 | 4 | Meta comfort ratings and what they mean for your listing | Draw the rating tiers |
| 10 | T1 | 3 | Recap: user-controlled comfort | Forward-looking |

**Mix: T1 10% · T2 50% · T3 15% · T4 8%**

---

## Module 7: Saving & Session Logic (~60 min, 10 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why your app must remember the user | Motivation |
| 2 | T5 | 5 | App states: Menu → Session → Summary → Menu | Diagram — state machine flow |
| 3 | T2 | 6 | PlayerPrefs: save volume and comfort mode | Procedural — simple key-value |
| 4 | T2 | 6 | JSON serialization: save session history | AI prompt → serialization code |
| 5 | T3 | 4 | File I/O on Quest (Android gotchas) | Draw file system paths |
| 6 | T2 | 6 | Build "welcome back" with session count | Procedural — read saved data on Start |
| 7 | T2 | 6 | State machine: timed meditation session flow | AI prompt → coroutine chain |
| 8 | T2 | 6 | Scene management: loading different environments | Procedural — SceneManager API |
| 9 | T4 | 5 | Test: close app, reopen, settings persist | Physical demo — the proof |
| 10 | T1 | 3 | Recap: your app is persistent | Forward-looking |

**Mix: T1 10% · T2 53% · T3 7% · T4 8% · T5 8%**

---

## Module 8: Multiplayer (~75 min, 12 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 3 | Why multiplayer transforms a solo app | Motivation |
| 2 | T5 | 5 | Network architecture: client-server vs P2P | Diagram — Photon topology |
| 3 | T2 | 6 | Photon Fusion free tier setup | Procedural — account, SDK, app ID |
| 4 | T2 | 6 | Room creation and joining logic | AI prompt → lobby code |
| 5 | T2 | 6 | Networked avatar: floating head + hands | Procedural — spawn prefab |
| 6 | T3 | 4 | Ownership and authority — who controls what | Draw ownership model |
| 7 | T2 | 6 | Synchronized objects (candle, journal) | AI prompt → network sync code |
| 8 | T2 | 6 | Voice chat with Photon Voice | Procedural — audio setup |
| 9 | T2 | 6 | "Invite a friend" button in UI | Procedural — room code sharing |
| 10 | T4 | 5 | Test with two headsets (or Quest + Link) | Physical demo — two people in room |
| 11 | T3 | 4 | Free tier limits and what to watch for | Draw pricing tiers |
| 12 | T1 | 3 | Recap: shared VR space | Forward-looking |

**Mix: T1 8% · T2 55% · T3 12% · T4 7% · T5 7%**

---

## Module 9: Mixed Reality & Passthrough (~75 min, 12 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 4 | MR is where the industry is going — and nobody teaches it | Motivation — the career differentiator |
| 2 | T3 | 5 | How passthrough works (Quest 3 cameras → reconstruction) | Draw the camera/reconstruction pipeline |
| 3 | T2 | 6 | Enable passthrough in OVR Manager | Procedural — config settings |
| 4 | T4 | 5 | First passthrough: see your real room through Quest | Physical demo — the wow moment |
| 5 | T3 | 5 | Scene API: room mesh, walls, floor, furniture | Draw the scene understanding model |
| 6 | T2 | 6 | Room setup and Scene API integration | Procedural — request scene data |
| 7 | T2 | 6 | Place virtual candle on your real desk | AI prompt → spatial anchor code |
| 8 | T2 | 6 | Persist anchors across sessions | Procedural — anchor persistence |
| 9 | T4 | 6 | Full MR demo: virtual objects in your real room | Physical demo — the portfolio shot |
| 10 | T2 | 5 | VR ↔ MR toggle in settings menu | Procedural — mode switching |
| 11 | T3 | 4 | Depth occlusion (brief intro — real objects in front) | Draw the occlusion model |
| 12 | T1 | 3 | Recap: your resume now says "MR developer" | Forward-looking |

**Mix: T1 9% · T2 39% · T3 19% · T4 22%**

---

## Module 10: Performance & Polish (~60 min, 10 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 4 | The 3 bugs that failed my first EnergyField submission | Personal story — stakes are real |
| 2 | T2 | 6 | Unity Profiler on Quest — find what's slow | Procedural — profiler walkthrough |
| 3 | T3 | 5 | Draw call budget: what Quest can handle | Draw the GPU pipeline bottleneck |
| 4 | T2 | 6 | Batching, instancing, texture compression (ASTC) | Procedural — apply optimizations |
| 5 | T2 | 6 | LOD setup + Quest-friendly shaders | Procedural — LOD groups, shader swap |
| 6 | T2 | 5 | App icon, splash screen, loading screen | Procedural — required Meta assets |
| 7 | T5 | 5 | The VRC checklist walkthrough | Diagram — checklist as visual flow |
| 8 | T2 | 5 | Error handling: tracking lost, battery low | Procedural — edge case scripts |
| 9 | T4 | 5 | Performance test: hold 72fps on Quest | Physical demo — profiler + headset |
| 10 | T1 | 3 | Recap: your app is submission-ready | Forward-looking |

**Mix: T1 12% · T2 52% · T3 8% · T4 8% · T5 8%**

---

## Module 11: Ship It — Meta Store Submission (~75 min, 13 sections)

| # | Tag | Min | Title | Why this template |
|---|-----|-----|-------|-------------------|
| 1 | T1 | 4 | This is where 80% of indie devs give up | Motivation — you won't |
| 2 | T2 | 6 | Create Meta Developer account + Organization | Procedural — browser walkthrough |
| 3 | T2 | 6 | Create new App in Developer Dashboard | Procedural — app name, category |
| 4 | T3 | 4 | App signing: keystores and why you MUST NOT lose them | Draw the signing flow |
| 5 | T2 | 6 | Build release APK from Unity | Procedural — build settings |
| 6 | T2 | 6 | Upload APK via MQDH | Procedural — upload flow |
| 7 | T2 | 6 | Store listing: description, screenshots, trailer | Procedural — fill out every field |
| 8 | T2 | 5 | Privacy policy (template provided) | Procedural — edit template, host it |
| 9 | T2 | 5 | Content guidelines + age rating questionnaire | Procedural — walkthrough |
| 10 | T2 | 5 | Submit for review | Procedural — the button click |
| 11 | T3 | 4 | Common rejection reasons and how to respond | Draw the review cycle |
| 12 | T1 | 5 | You shipped a VR app — what's next? | Closing — career paths, next course |
| 13 | T1 | 3 | Course outro + call to action | Final sign-off |

**Mix: T1 16% · T2 60% · T3 11%**

---

## Full Course Template Distribution

| Template | Total min | % of course | Production hrs (est.) |
|----------|-----------|-------------|----------------------|
| T1 Talking Head | ~105 min | 13% | 10-17 hrs |
| T2 Screen Recording | ~380 min | 47% | 32-48 hrs |
| T3 Tablet Annotation | ~125 min | 15% | 8-13 hrs |
| T4 Live Demo + PiP | ~105 min | 13% | 13-21 hrs |
| T5 Diagram Walkthrough | ~30 min | 4% | 3-4 hrs |
| T6 Motion Graphics | ~0 min | 0% | 0 hrs |
| T7 Workshop | ~55 min | 7% | 7 hrs |
| **TOTAL** | **~800 min (~13.3 hrs)** | **100%** | **73-110 hrs** |

**At 6 productive hours/day: 12-18 working days of recording + editing.**
**Add 5-7 days for scripting = 17-25 total working days.**
**You have 40 days. This fits — but only if you start scripting NOW.**
