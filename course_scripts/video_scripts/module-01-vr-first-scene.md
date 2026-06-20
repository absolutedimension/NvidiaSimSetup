---
title: "Module 1 — Your First VR Scene"
video_type: full_lesson          # faceless-animated concept video; companion lab PDF carries exact Unity clicks
length_target_sec: 420
mode: B                          # motion graphics (rich) — flagship course
voice: { name: male_confident, speed: 0.78 }   # Deepak's first-person voice; override in frontmatter if desired
background_shader: circuit_mind  # tech/coding aesthetic to match the episode look
presenter: none                  # FULLY FACELESS — no talking head, no Unity screen capture
music: ambient_low
aspect: 16:9
# COMPANION DELIVERABLE: course_scripts/labs/MODULE_01_LAB.md — the exact click-by-click
# Unity/Meta-XR setup steps the student follows alongside this video. The video is the MAP;
# the lab guide is the TERRAIN. Ship them together.
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, your first VR scene will be running on your own Quest headset.
  Not a tutorial someone else built. Not a demo. Your scene. Your headset.
  You will put it on, look around, and stand inside a room that you made.
on_screen:
  title: Your First VR Scene
  subtitle: Module 1
  body: Running on YOUR Quest headset
  layout: center
visual: logo top; the word "YOUR" pulses brighter on each repeat; titles fade up over a calm circuit field
duration_hint_sec: 20

### scene_02_what_we_build
narration: |
  Across this whole course, we build one project together. It is called ZenSpace.
  A virtual reality and mixed reality meditation room.
  It is simple enough for a complete beginner, and rich enough to teach every core idea in VR.
  I chose it because it mirrors my own app, EnergyField, which is live in Meta's alpha program.
  So at every step, I can show you how I solved the exact same problem in a real, shipped app.
on_screen:
  title: The Project — ZenSpace
  bullets: ["A VR + MR meditation room", "Beginner-simple, teaches every core idea", "Mirrors my real shipped app, EnergyField"]
  layout: bullets
visual: a soft 3D room outline assembles — floor, four walls, one glowing stone — calm wellness palette
duration_hint_sec: 34

### scene_03_differentiator
narration: |
  Here is what makes this course different from every other VR course.
  You will not type code by hand.
  We use an AI coding agent, Claude Code, to write our scripts.
  You describe what you want in plain English. The agent writes the code. You test it in VR, and you iterate.
  That is how professional developers actually work now.
  So even if you have never written a single line of code, you can build this.
on_screen:
  title: You Won't Type Code by Hand
  bullets: ["Describe what you want — in plain English", "The AI agent writes the C#", "You test in VR, then iterate"]
  layout: bullets
visual: a plain-English sentence flows into a code block, then into a VR object lighting up — a three-stage loop
duration_hint_sec: 34

### scene_04_journey
narration: |
  Here is the journey ahead. Eleven modules.
  Module one, today, we set up our tools and build our first room.
  Module two, we set up our AI coding partner.
  Modules three through eight, we add hands, interface, audio, movement, saving, and multiplayer.
  Module nine is the one that makes your resume different. Mixed reality. Your objects placed in your real room, through Quest passthrough.
  Module ten, we polish for performance. And module eleven, we submit to Meta's Store.
  Almost nobody teaches that last step. We will.
on_screen:
  title: The 11-Module Journey
  bullets: ["1 · Tools + first room", "2 · Your AI coding partner", "3–8 · Hands, UI, audio, movement, multiplayer", "9 · Mixed Reality", "10 · Polish", "11 · Ship to Meta's Store"]
  layout: bullets
visual: a horizontal timeline of 11 nodes lights up left-to-right in sync with narration; node 9 and node 11 flare brightest
duration_hint_sec: 40

### scene_05_dev_loop
narration: |
  Before we build, hold this one picture in your head. The VR development loop.
  You work in Unity on your computer. Unity packages everything into an Android app file, called an A-P-K.
  That file travels down a cable to your Quest, and your app launches inside the headset.
  You change something, you build again, you test in VR. Change, build, test.
  You will repeat this loop hundreds of times. The faster it runs, the faster you create.
on_screen:
  title: The VR Development Loop
  body: Unity → APK → Quest → test → repeat
  layout: diagram
visual: animated three-box diagram — Unity editor, then an APK packet sliding down a cable, then a headset glowing; a circular arrow loops back
duration_hint_sec: 36

### scene_06_anatomy
narration: |
  And here is what a VR scene actually is, underneath. It is simpler than you think.
  A camera rig, which is really you, your head and your hands, tracked in space.
  Some geometry, the floor and the walls, the shapes that make the room.
  Materials, which decide how each surface looks, its color and how it catches light.
  And lights, to make the room feel warm instead of empty.
  That is it. A camera, some shapes, some materials, some lights.
  Every VR app in the world is built from these same few pieces. The big ones just have more of them.
on_screen:
  title: What a VR Scene Really Is
  bullets: ["Camera rig — that's YOU, tracked in space", "Geometry — the floor and walls", "Materials — how surfaces look", "Lights — warmth, not emptiness"]
  layout: bullets
visual: the ZenSpace room rebuilds layer by layer — first a head-and-hands rig, then geometry, then materials wash over, then lights bloom
duration_hint_sec: 40

### scene_07_tools_today
narration: |
  Today you install three things. I will name them now, and the lab guide beside this video has every exact click.
  First, Unity, version six, with Android build support, because Quest runs on Android.
  Second, the Meta XR software development kit, a single free package that gives you hands, controllers, passthrough, everything.
  Third, you switch your project to build for Meta Quest instead of for a PC.
  Follow the lab guide step by step while I explain why each piece matters.
on_screen:
  title: Today You Install Three Things
  bullets: ["Unity 6 + Android Build Support", "Meta XR All-in-One SDK (free)", "Switch the build target to Meta Quest"]
  layout: bullets
visual: three labeled tiles snap into place; a small "→ follow the Lab Guide" tag glows under them
duration_hint_sec: 36

### scene_08_room
narration: |
  Then we build the room itself. A floor, in warm dark wood. Four walls, in soft cream.
  A directional light angled like afternoon sun, and a gentle point light overhead, so the space feels calm, not clinical.
  And one small grey stone, resting in front of where you will stand.
  Later, in module three, we make that stone something you can reach out and grab.
  For now, it is the first object in a world that is yours.
on_screen:
  title: Build the Room
  bullets: ["Warm wood floor", "Soft cream walls", "Sunlight + a warm overhead glow", "One meditation stone"]
  layout: bullets
visual: the room assembles in warm light; the grey stone settles into place and catches a soft highlight
duration_hint_sec: 34

### scene_09_payoff
narration: |
  And then the moment this whole module is for.
  You connect your Quest, you press build and run, and you put on the headset.
  The floor is beneath you. The walls are around you. The stone rests in front of you. The light is warm.
  Look around. You are not watching a VR scene. You are standing inside one. And you made it.
on_screen:
  title: Put On the Headset
  subtitle: You made this
  body: You're not watching a VR scene — you're standing in one
  layout: center
visual: camera pushes from outside the room to a first-person view inside it; warm light fills the frame
duration_hint_sec: 30

### scene_10_credibility
narration: |
  Things will go wrong along the way. A build target missing. A device not found. A black screen on launch.
  I have hit every one of these, in my own work, building a real app.
  So I am not going to hand you the happy path and disappear. I will show you the errors, and exactly how to fix each one.
  That is the difference between reading documentation and learning from someone who shipped.
on_screen:
  title: Every Bug, Every Fix
  bullets: ["I built EnergyField — live in Meta alpha", "I've hit every one of these errors", "You get the fixes, not just the happy path"]
  layout: bullets
visual: three red "error" cards flip over one by one to reveal green "fix" cards
duration_hint_sec: 30

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you what you are building and why each piece matters.
  The lab guide beside it is the terrain. It has every exact click, in order, so you never get lost.
  Watch the video once. Then open the lab guide, put on your headset when it tells you to, and build.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (what + why)", "The Lab Guide = the TERRAIN (every click)", "Watch once, then build along with the guide"]
  layout: split
visual: a folded map graphic and a checklist sit side by side; a pointer moves between them
duration_hint_sec: 26

### scene_12_cta
narration: |
  That is module one. By the end, you will have a working VR development pipeline, and your own room running on your headset.
  Next module, we set up your AI coding partner, so you can build by describing, not by typing.
  Open the lab guide. Let's start.
on_screen:
  title: Next — Your AI Coding Partner
  subtitle: Module 2
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 1 marked complete, node 2 begins to glow; logo outro
duration_hint_sec: 22
