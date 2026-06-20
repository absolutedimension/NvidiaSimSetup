---
title: "Module 6 — Movement & Locomotion"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_06_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, you will move through a world far bigger than the room you stand in.
  You will point, and teleport across a space in an instant, without ever feeling sick.
  Your small physical room becomes a doorway into a place with no walls.
  This is how players explore worlds in VR.
on_screen:
  title: Movement & Locomotion
  subtitle: Module 6
  body: Move through a world bigger than your room
  layout: center
visual: a small room outline opens into a vast space; an arc points forward and the view jumps
duration_hint_sec: 22

### scene_02_room_limit
narration: |
  Here is the problem locomotion solves.
  Your real room is small, just a few steps in any direction before you hit a wall.
  But the world you are building can be huge. A gallery, a forest, a whole city.
  Locomotion is how the user crosses that gap, moving through a big virtual world
  while standing safely inside a small real one.
on_screen:
  title: The Room-Scale Limit
  bullets: ["Your real room is only a few steps wide",
            "Your virtual world can be huge",
            "Locomotion bridges that gap",
            "Move a big world from a small real space"]
  layout: bullets
visual: a tiny guardian boundary sits inside a vast virtual landscape
duration_hint_sec: 36

### scene_03_two_styles
narration: |
  There are two main ways to move, and the choice matters more than almost anything for comfort.
  Teleport, where you point at a spot and instantly jump there. It is comfortable for almost everyone.
  And smooth locomotion, where you push a thumbstick and glide, like a first-person game.
  Smooth feels more immersive, but it makes many people motion sick.
  Most VR apps default to teleport, and offer smooth as an option.
on_screen:
  title: Two Ways to Move
  bullets: ["Teleport — point and jump instantly (comfortable)",
            "Smooth — push a stick and glide (immersive)",
            "Smooth can cause motion sickness",
            "Default to teleport, offer smooth as an option"]
  layout: bullets
visual: a teleport arc jump on the left, a smooth glide on the right, side by side
duration_hint_sec: 40

### scene_04_teleport
narration: |
  Let us look at teleport, the comfortable default.
  You hold a button, and a curved ray shoots out with a marker at the end.
  You aim the marker at a spot on the floor, you release, and you are instantly standing there.
  No motion, so no sickness. The Meta XR SDK and the XR Interaction Toolkit both give you
  a ready-made teleport system. You just say which surfaces can be teleported to.
on_screen:
  title: Teleport — The Comfortable Default
  bullets: ["Hold a button — a curved ray with a marker appears",
            "Aim at the floor, release, you're there",
            "No motion means no sickness",
            "Ready-made in Meta XR / XR Interaction Toolkit"]
  layout: bullets
visual: a curved teleport ray lands a marker on the floor; the view snaps to that spot
duration_hint_sec: 40

### scene_05_smooth
narration: |
  Smooth locomotion is the other style.
  You push the thumbstick forward, and you glide through the world continuously, like walking.
  It feels more natural and immersive, and for some games it is the right choice.
  But here is the catch. Your eyes see motion while your body stands still,
  and that mismatch is exactly what makes people feel sick. Use it carefully, and always with comfort options.
on_screen:
  title: Smooth Locomotion
  bullets: ["Push the stick — glide continuously",
            "More natural and immersive",
            "But eyes move while the body stands still",
            "That mismatch causes sickness — use with care"]
  layout: bullets
visual: a thumbstick pushes and the world glides past; a small warning pulse on the horizon
duration_hint_sec: 38

### scene_06_comfort
narration: |
  Comfort is not optional. It is what keeps people in your app instead of taking the headset off.
  A vignette tunnels the edges of your view during movement, which calms the inner ear.
  Snap turn rotates you in fixed steps instead of a dizzy smooth spin.
  And the golden rule: let the user choose. Teleport or smooth, vignette on or off, turn speed.
  Comfort settings are how you keep every kind of player.
on_screen:
  title: Comfort Is Not Optional
  bullets: ["Vignette — tunnel the edges during motion",
            "Snap turn — rotate in fixed steps",
            "Always let the user choose their settings",
            "Comfort is how you keep every player"]
  layout: bullets
visual: a vignette darkens the view edges; a snap-turn rotates the world in clean steps
duration_hint_sec: 40

### scene_07_setup
narration: |
  Setting up teleport is straightforward, and the lab guide has every click.
  You add a locomotion system to your camera rig.
  You mark the floor as a teleport surface, so the user can land there but not on walls or the ceiling.
  And you add a teleport ray to a hand or controller.
  After that, point at the floor, release, and you move.
on_screen:
  title: Setting Up Teleport
  bullets: ["Add a locomotion system to the camera rig",
            "Mark the floor as a teleport surface",
            "Add a teleport ray to a hand / controller",
            "Point at the floor, release, move"]
  layout: bullets
visual: a locomotion system attaches; the floor highlights as teleportable; a ray appears
duration_hint_sec: 38

### scene_08_agent
narration: |
  Let your agent wire the whole movement system.
  You say: add teleport on my right hand that works on any floor surface,
  add snap turning on my left thumbstick, and add a comfort vignette during movement.
  Make teleport the default and keep it comfortable.
  The agent sets up the locomotion system, marks the surfaces, and tells you what to attach.
on_screen:
  title: Let the Agent Wire It
  bullets: ["\"Teleport on the right hand, on any floor\"",
            "\"Snap turn on the left thumbstick\"",
            "\"A comfort vignette during movement\"",
            "Agent sets up locomotion + marks surfaces"]
  layout: bullets
visual: a spoken request produces a teleport ray, a snap-turn indicator, and a vignette
duration_hint_sec: 40

### scene_09_gotchas
narration: |
  A few movement traps to avoid.
  If the user can teleport onto walls or the ceiling, you forgot to limit teleport to the floor surface.
  If they fall through the floor, the floor is missing a collider.
  If smooth movement makes testers queasy, default to teleport and turn comfort options on.
  And if snap turn spins too far, reduce the angle. Small comfortable steps beat fast dizzy ones.
on_screen:
  title: Movement Gotchas
  bullets: ["Teleporting onto walls? Limit it to the floor",
            "Falling through the floor? Add a collider",
            "Testers queasy? Default to teleport + comfort",
            "Snap turn too far? Reduce the angle"]
  layout: bullets
visual: a wall-teleport, a fall-through, and a too-fast spin each get a fix marker
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what movement unlocks.
  Your world is no longer limited to the few square meters of a real room.
  Now it can be a gallery you walk through, a level you explore, a city you wander.
  The user steps through their small room into something vast.
  Movement is what turns a single scene into a world.
on_screen:
  title: What Movement Unlocks
  bullets: ["No longer limited to a few square meters",
            "A gallery, a level, a city to explore",
            "The small room becomes a doorway",
            "Movement turns a scene into a world"]
  layout: bullets
visual: the small room dissolves and a sprawling explorable world opens around the user
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the movement styles and comfort.
  The lab guide beside it has every exact step to set up teleport and snap turn,
  and the prompt to wire a comfortable movement system.
  Watch this once, then open the lab guide and let your user move.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (styles + comfort)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then let your user move"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 6. Your user can now move freely through a world bigger than their room, comfortably.
  Next module, we make your app remember. Saving and persistence,
  so when the user takes off the headset and comes back, their world is exactly as they left it.
  Open the lab guide. Let's get moving.
on_screen:
  title: Next — Saving & Persistence
  subtitle: Module 7
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 6 marked complete, node 7 begins to glow; logo outro
duration_hint_sec: 24
