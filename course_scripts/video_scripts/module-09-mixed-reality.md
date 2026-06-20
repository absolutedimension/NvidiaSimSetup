---
title: "Module 9 — Mixed Reality"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_09_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, your virtual objects will appear in your real room.
  The meditation stone, sitting on your actual desk. A panel floating beside your real window.
  Through Quest's passthrough cameras, the digital and the physical blend into one space.
  This is the feature that makes your resume different. Almost nobody teaches it well.
on_screen:
  title: Mixed Reality
  subtitle: Module 9
  body: Your virtual objects in your real room
  layout: center
visual: a real-room passthrough view with a virtual stone resting on a real desk
duration_hint_sec: 22

### scene_02_vr_vs_mr
narration: |
  First, the difference. In virtual reality, you replace the world. You are fully somewhere else.
  In mixed reality, you keep the real world and add to it.
  You still see your room, your desk, your couch, through the headset's cameras,
  and virtual objects sit inside that real space.
  VR takes you away. MR brings the digital to you. Quest 3 does both.
on_screen:
  title: VR vs Mixed Reality
  bullets: ["VR replaces the world — you're elsewhere",
            "MR keeps the real world and adds to it",
            "You see your real room through the cameras",
            "VR takes you away; MR brings digital to you"]
  layout: bullets
visual: a fully-virtual scene on the left, a real room with added objects on the right
duration_hint_sec: 38

### scene_03_passthrough
narration: |
  The foundation of mixed reality is passthrough.
  Passthrough is the live video feed from the cameras on the front of your Quest,
  showing you your real surroundings inside the headset.
  To build MR, you turn passthrough on, and you make your scene's background transparent,
  so instead of a virtual skybox, you see your actual room behind your virtual objects.
on_screen:
  title: Passthrough — Seeing Your Real Room
  bullets: ["A live video feed from the Quest cameras",
            "Shows your real surroundings in the headset",
            "Turn passthrough on",
            "Make the scene background transparent"]
  layout: bullets
visual: a black VR background dissolves to reveal the real room behind floating objects
duration_hint_sec: 38

### scene_04_anchors
narration: |
  Next, spatial anchors. This is the magic that pins virtual objects to real places.
  You place the stone on your real desk, and you drop a spatial anchor there.
  Quest remembers that exact spot in your room, even after you take the headset off.
  Come back tomorrow, and the stone is still on your desk, in the same place.
  Anchors are how the digital stays put in the physical world.
on_screen:
  title: Spatial Anchors — Pinning to Reality
  bullets: ["Pin a virtual object to a real spot",
            "Drop an anchor where you place it",
            "Quest remembers that exact place",
            "Come back later — it's still there"]
  layout: bullets
visual: a stone is placed on a real desk; a pin marker locks it to that exact spot
duration_hint_sec: 38

### scene_05_scene_understanding
narration: |
  Quest can also understand the shape of your room. This is scene understanding.
  The headset knows where your walls, floor, ceiling, and large furniture are.
  With that, your virtual objects can respect the real world. A ball can bounce off your real floor.
  A panel can avoid your real wall. Digital things can sit on real surfaces.
  Your room becomes the level your app is built on.
on_screen:
  title: Scene Understanding
  bullets: ["Quest knows your walls, floor, furniture",
            "Virtual objects can respect the real world",
            "A ball bounces off your real floor",
            "Your real room becomes the level"]
  layout: bullets
visual: a wireframe maps a real room; a virtual ball bounces off the detected floor
duration_hint_sec: 38

### scene_06_design
narration: |
  Designing for mixed reality is a different mindset.
  You do not control the room, the user does. Their space might be big or tiny, bright or dark, cluttered or bare.
  So you place things relative to what is really there. On a surface, near a wall, within reach.
  And you keep the virtual light, because it has to share the stage with the real world.
  Good MR feels like it belongs in the room it is in.
on_screen:
  title: Designing for Mixed Reality
  bullets: ["You don't control the room — the user does",
            "Every space is different: size, light, clutter",
            "Place things relative to what's really there",
            "Good MR feels like it belongs in the room"]
  layout: bullets
visual: the same virtual object adapts to a small room and a large room sensibly
duration_hint_sec: 38

### scene_07_agent
narration: |
  Let your agent build a mixed reality version of your scene.
  You say: enable passthrough and make the background transparent,
  let me place the stone on a real surface and anchor it there so it persists,
  and use scene understanding so objects rest on my real floor and desk.
  The agent turns on passthrough, wires the anchors, and connects to the room data.
on_screen:
  title: Let the Agent Build It
  bullets: ["\"Enable passthrough, transparent background\"",
            "\"Place + anchor the stone on a real surface\"",
            "\"Use scene data so objects rest on real things\"",
            "Agent wires passthrough + anchors + room data"]
  layout: bullets
visual: a request flips a VR scene into a passthrough MR scene with anchored objects
duration_hint_sec: 40

### scene_08_gotchas
narration: |
  A few mixed reality traps.
  If you still see a virtual background instead of your room, your camera or scene background is not transparent.
  If anchored objects drift, the room was not scanned well. Have the user set up their space first.
  If objects float or sink into furniture, scene understanding is off or the room data is stale.
  And test in different real rooms. What works in yours may break in a messier one.
on_screen:
  title: Mixed Reality Gotchas
  bullets: ["See a virtual background? It's not transparent",
            "Anchors drift? Room wasn't scanned well",
            "Objects float / sink? Scene data off or stale",
            "Test in different real rooms"]
  layout: bullets
visual: an opaque background, a drifting anchor, and a sinking object each get a fix marker
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what mixed reality unlocks.
  A board game on your real coffee table. A fitness coach standing in your living room.
  Furniture you preview in your actual space before you buy. Instructions floating over the real machine you are fixing.
  MR is where VR stops being an escape and becomes a tool for daily life.
  This is the direction the whole industry is heading, and now you can build it.
on_screen:
  title: What Mixed Reality Unlocks
  bullets: ["A board game on your real table",
            "A coach in your living room",
            "Preview furniture in your real space",
            "Where VR becomes a daily-life tool"]
  layout: bullets
visual: a real living room fills with useful MR overlays — game, coach, furniture preview
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the pieces of mixed reality.
  The lab guide beside it has every exact step to enable passthrough, place an anchor,
  and use scene understanding, plus the prompt to make your scene mixed reality.
  Watch this once, then open the lab guide and bring your objects into the real world.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (the MR pieces)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then go mixed reality"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 9, the one that sets your work apart. Your virtual objects now live in the real world.
  Next module, we make everything run smoothly. Polish and performance,
  so your app holds a rock-solid frame rate and feels comfortable, not stuttery.
  Open the lab guide. Let's step into mixed reality.
on_screen:
  title: Next — Polish & Performance
  subtitle: Module 10
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 9 marked complete, node 10 begins to glow; logo outro
duration_hint_sec: 24
