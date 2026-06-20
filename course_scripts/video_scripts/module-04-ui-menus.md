---
title: "Module 4 — UI & Menus in VR"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_04_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, a menu will float in your room,
  and you will press its buttons with your finger.
  This is how the people who use your app actually control it from inside VR.
  Start a sound. Change the lighting. Reset the scene. All from a panel in mid-air.
on_screen:
  title: UI & Menus in VR
  subtitle: Module 4
  body: A floating panel you press with your finger
  layout: center
visual: a glowing UI panel fades in mid-air; a fingertip presses a button and it lights up
duration_hint_sec: 22

### scene_02_why_different
narration: |
  User interface in VR is different from anything you have built before.
  There is no mouse. There is no flat screen in front of you.
  Your menu lives in 3D space, floating in the room, and the user reaches out and touches it.
  A button is not something you click. It is something you push, with your actual finger.
  Once you see UI as a physical object in the room, it all makes sense.
on_screen:
  title: VR UI Is Different
  bullets: ["No mouse, no flat 2D screen",
            "The menu floats in 3D space",
            "A button is pushed — with your finger",
            "Think of UI as a physical object in the room"]
  layout: bullets
visual: a 2D phone menu tilts back into 3D space and becomes a floating panel
duration_hint_sec: 36

### scene_03_world_canvas
narration: |
  The core building block is the world-space canvas.
  In Unity, a canvas is where your buttons and text live.
  Normally it is stuck to the screen. In VR, you set it to world space,
  and now it is a real panel you can place anywhere in the room, like a floating tablet.
  Everything you put on it, buttons, labels, sliders, becomes part of your 3D world.
on_screen:
  title: The World-Space Canvas
  bullets: ["A canvas holds your buttons and text",
            "Set it to World Space — not screen",
            "Now it's a real panel in the room",
            "Like a floating tablet you can place anywhere"]
  layout: bullets
visual: a flat canvas detaches from the screen edge and floats into the room as a panel
duration_hint_sec: 36

### scene_04_poke
narration: |
  How do you press a button that is floating in the air?
  With poke, the same idea from the last module.
  Your fingertip becomes the cursor. You reach out and push the button inward, and it presses.
  The Meta XR SDK gives you a poke interactor on your hand,
  and you mark the panel as pokeable. Now your finger just works on it.
on_screen:
  title: Press With a Poke
  bullets: ["Your fingertip is the cursor",
            "Reach out and push the button inward",
            "Meta XR gives a poke interactor on your hand",
            "Mark the panel pokeable — finger just works"]
  layout: bullets
visual: a fingertip approaches a button, pushes it in, and it springs back with a glow
duration_hint_sec: 36

### scene_05_build_panel
narration: |
  Let us build a simple panel.
  You create a world-space canvas, give it a background, and add a button and a label.
  You place it about an arm's length away, at a comfortable height, tilted slightly toward the user.
  You size the buttons big, much bigger than on a phone, because fingers are less precise than a mouse.
  The lab guide has every exact step.
on_screen:
  title: Build a Simple Panel
  bullets: ["World-space canvas + background + a button",
            "Place it about an arm's length away",
            "Comfortable height, tilted toward the user",
            "Make buttons BIG — fingers aren't precise"]
  layout: bullets
visual: a panel assembles — background, then a big button, then a label, at arm's reach
duration_hint_sec: 38

### scene_06_actions
narration: |
  A button is only useful if it does something.
  In Unity, every button has an on-click event. You connect that event to an action.
  Press Calm, and a soft ambient sound fades in. Press Energize, and the lights brighten.
  Press Reset, and the room returns to its start.
  You describe each action to your agent, and it wires the button to the code.
on_screen:
  title: Make Buttons Do Things
  bullets: ["Every button has an on-click event",
            "Connect the event to an action",
            "Calm -> sound; Energize -> bright lights; Reset",
            "Describe each action; the agent wires it"]
  layout: bullets
visual: three buttons each fire a different effect — sound waves, brighter light, a room reset
duration_hint_sec: 38

### scene_07_design_rules
narration: |
  A few design rules keep your VR menus comfortable and usable.
  Make targets big and well spaced, so fingers do not miss.
  Keep the panel about an arm's length away, not in the user's face, not across the room.
  Use high contrast and few words, because reading in VR is harder than on a screen.
  Comfort first. A menu that strains the eyes or arms will not get used.
on_screen:
  title: VR UI Design Rules
  bullets: ["Big, well-spaced targets",
            "Keep it about an arm's length away",
            "High contrast, few words",
            "Comfort first — or it won't get used"]
  layout: bullets
visual: a cramped tiny menu reshapes into a clean, spaced, readable one
duration_hint_sec: 38

### scene_08_agent
narration: |
  Now let your agent do the heavy lifting.
  You say: make a floating panel with three buttons, Calm, Energize, and Reset.
  Calm plays a soft ambience, Energize brightens the lights, Reset returns the room to start.
  Make them pokeable with my finger, and place the panel at arm's length.
  The agent builds the canvas, wires the buttons, and tells you exactly what to attach.
on_screen:
  title: Let the Agent Build It
  bullets: ["\"A floating panel: Calm, Energize, Reset\"",
            "\"Each button changes the room\"",
            "\"Pokeable with my finger, at arm's length\"",
            "Agent builds the canvas + wires the buttons"]
  layout: bullets
visual: a spoken request becomes a finished three-button panel floating in the room
duration_hint_sec: 40

### scene_09_gotchas
narration: |
  A few traps to know.
  If your buttons will not press, the panel is usually missing its pokeable setup, or it is too far to reach.
  If the text looks blurry, your canvas resolution is too low, or the panel is too small.
  And if the menu chases your head around, it is parented to the camera. Fix it in place in the room instead.
  Tell the agent what is wrong, and it walks you through the fix.
on_screen:
  title: UI Gotchas
  bullets: ["Won't press? Missing pokeable, or too far",
            "Blurry text? Canvas too small / low-res",
            "Menu chases your head? Unparent from camera",
            "Describe it to the agent to fix"]
  layout: bullets
visual: an unreachable panel, blurry text, and a head-chasing menu each get a fix marker
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what a menu unlocks.
  Settings. Mode switches. A start screen. A pause menu. A way to choose what happens next.
  This is the line between a tech demo and a real app.
  A demo just shows one thing. An app lets the user decide, and your floating panel is how they decide.
  You just gave your users control.
on_screen:
  title: What a Menu Unlocks
  bullets: ["Settings, mode switches, start + pause screens",
            "The line between a demo and a real app",
            "A demo shows; an app lets the user decide",
            "You just gave your users control"]
  layout: bullets
visual: a single-purpose demo grows menu options and becomes a full app shell
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the UI model and the design rules.
  The lab guide beside it has every exact step to build the panel, and the prompt to wire the three buttons.
  Watch this once, then open the lab guide and build your floating menu.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (model + design rules)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then build your floating menu"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 4. Your app now has a menu the user can reach out and control.
  Next module, we bring it to life with sound. Spatial audio that comes from real places in your room,
  so a chime sounds like it is truly coming from the stone you just touched.
  Open the lab guide. Let's build your menu.
on_screen:
  title: Next — Audio & Ambience
  subtitle: Module 5
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 4 marked complete, node 5 begins to glow; logo outro
duration_hint_sec: 24
