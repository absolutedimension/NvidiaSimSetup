---
title: "Module 3 — Hands & Grabbing"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_03_LAB.md — exact Editor + agent steps.
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, you will reach out with your real hands,
  and pick up objects inside your VR room. No controllers needed.
  Your room stops being something you look at, and becomes something you touch.
  This is the moment VR starts to feel real.
on_screen:
  title: Hands & Grabbing
  subtitle: Module 3
  body: Reach out — and pick it up with your real hands
  layout: center
visual: a hand reaches into frame and lifts a glowing stone; ripples spread from the touch
duration_hint_sec: 22

### scene_02_two_ways
narration: |
  On Quest, there are two ways to interact with your world.
  Controllers, the handsets you hold, with buttons and triggers.
  And hand tracking, where the headset sees your bare hands and you grab with your fingers.
  The good news: with the Meta XR SDK, you build once and support both.
  Pick something up with a controller, or with your hand. Same code.
on_screen:
  title: Two Ways to Interact
  bullets: ["Controllers — buttons and triggers",
            "Hand tracking — your bare hands",
            "Meta XR SDK supports both from one setup"]
  layout: bullets
visual: a controller icon and a bare-hand icon both point at the same glowing object
duration_hint_sec: 34

### scene_03_what_is_tracking
narration: |
  So how does hand tracking work?
  The cameras on the front of your Quest watch your hands.
  The Meta XR SDK turns what they see into a hand skeleton, a set of joints and fingers, updated every frame.
  You do not build any of that. It is handed to you, ready to use.
  Your job is just to say which objects can be grabbed, and what happens when they are.
on_screen:
  title: What Hand Tracking Is
  bullets: ["Quest cameras watch your hands",
            "Meta XR SDK builds a live hand skeleton",
            "You don't build tracking — it's handed to you",
            "Your job: which objects grab, and what happens"]
  layout: bullets
visual: a wireframe hand skeleton forms over a real hand outline, joints lighting up
duration_hint_sec: 38

### scene_04_model
narration: |
  Here is the one idea that makes all of this click.
  Interaction has two halves. An interactor, which is the thing that grabs. That is your hand or controller.
  And an interactable, which is the thing that can be grabbed. That is the stone, a lever, a button.
  The Meta XR SDK gives you ready-made building blocks for both.
  Once an object is marked interactable, your hands just work with it.
on_screen:
  title: Interactor + Interactable
  bullets: ["Interactor = the thing that grabs (your hand)",
            "Interactable = the thing grabbed (the stone)",
            "Meta XR gives ready-made blocks for both",
            "Mark an object interactable — hands just work"]
  layout: bullets
visual: a hand labelled "interactor" connects to a stone labelled "interactable" with a glowing link
duration_hint_sec: 38

### scene_05_make_grabbable
narration: |
  Let us extend the stone from the last module.
  In Module 2, your agent made it grabbable with a controller.
  Now we add hand grabbing too. You drop on a hand-grab component, set a grab point,
  and add a collider so your fingers have something solid to catch.
  The lab guide walks every click. After this, you can grab the stone with your hand or your controller.
on_screen:
  title: Make the Stone Hand-Grabbable
  bullets: ["Extend the stone from Module 2",
            "Add a hand-grab component + a grab point",
            "Add a collider so fingers can catch it",
            "Now: grab with hand OR controller"]
  layout: bullets
visual: components drop onto the stone one by one; a hand then closes around it
duration_hint_sec: 38

### scene_06_grab_types
narration: |
  Not every grab is the same, and choosing the right one matters.
  Distance grab lets you pull an object toward you from across the room, like a force pull.
  Hand grab is the close, natural pinch when the object is right in front of you.
  And poke lets you push buttons and panels with a fingertip.
  Use distance grab for far objects, hand grab for held objects, poke for menus.
on_screen:
  title: Choose the Right Grab
  bullets: ["Distance grab — pull from across the room",
            "Hand grab — close, natural pinch",
            "Poke — push buttons with a fingertip",
            "Match the grab type to the object"]
  layout: bullets
visual: three mini-scenes — a far pull, a close pinch, a fingertip poke — cycle
duration_hint_sec: 38

### scene_07_feedback
narration: |
  Here is what separates a cheap VR app from one that feels alive. Feedback.
  When your hand hovers over the stone, it should glow.
  When you grab it, the controller should buzz and a soft sound should play.
  Without feedback, grabbing feels dead, and people are not sure it worked.
  With it, your hands feel connected to the world. Always add feedback.
on_screen:
  title: Feedback Makes It Feel Real
  bullets: ["Hover — the object glows",
            "Grab — haptic buzz + a soft sound",
            "No feedback feels dead and uncertain",
            "Feedback connects your hands to the world"]
  layout: bullets
visual: a stone with no glow looks flat; then glow + a buzz icon + a sound wave make it pop
duration_hint_sec: 38

### scene_08_agent
narration: |
  And this is where your AI coding partner earns its keep.
  You say: make all the objects in my room grabbable with both hand and controller,
  glow when I hover, and play a chime and a haptic buzz when I grab.
  The agent writes the scripts and tells you exactly what to attach.
  You review the code, build to your Quest, and your whole room comes alive. One request.
on_screen:
  title: Let the Agent Wire It
  bullets: ["\"Make every object grabbable — hand + controller\"",
            "\"Glow on hover, chime and buzz on grab\"",
            "Agent writes it, tells you what to attach",
            "Review, build — the room comes alive"]
  layout: bullets
visual: one spoken request flows out to many objects in a room that all light up together
duration_hint_sec: 40

### scene_09_gotchas
narration: |
  Hand tracking has a few traps, and knowing them saves you hours.
  It needs decent light. In a dark room, the cameras lose your hands.
  It only works when your hands are in view of the headset cameras, roughly in front of you.
  And if grabbing feels unreliable, your collider is often too small. Make it match the object.
  When something is off, describe it to the agent and it helps you debug.
on_screen:
  title: Hand-Tracking Gotchas
  bullets: ["Needs decent light — dark rooms lose your hands",
            "Hands must be in the cameras' view",
            "Unreliable grab? Collider is usually too small",
            "Describe the problem to the agent to debug"]
  layout: bullets
visual: a dim room, an out-of-view hand, and a tiny collider each get a fix marker
duration_hint_sec: 38

### scene_10_room_alive
narration: |
  Think about the leap you just made.
  Your room is no longer a picture you stand inside. It is a place you can touch.
  You reach out, and things respond. That is the difference between watching VR and being present in it.
  Every interactive app, every game, every training simulator, is built on exactly what you just learned.
on_screen:
  title: Your Room Is Alive Now
  bullets: ["From a picture you stand in — to a place you touch",
            "You reach out, and things respond",
            "Watching VR vs being present in it",
            "Every interactive app is built on this"]
  layout: bullets
visual: a static room transforms — objects begin to react to a moving hand
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the interaction model and the choices.
  The lab guide beside it has every exact component to add, and the exact prompt to make your room grabbable.
  Watch this once, then open the lab guide and bring your room to life.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (the model + choices)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then make your room grabbable"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 3. Your hands now work inside your VR room, and your objects respond to your touch.
  Next module, we add a user interface. Floating menus and buttons you press with your finger,
  so the user can actually control your app from inside VR.
  Open the lab guide. Let's bring your room to life.
on_screen:
  title: Next — UI & Menus in VR
  subtitle: Module 4
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 3 marked complete, node 4 begins to glow; logo outro
duration_hint_sec: 24
