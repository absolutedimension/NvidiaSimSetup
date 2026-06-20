---
title: "Module 10 — Polish & Performance"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_10_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, your app will run smooth and steady, and feel finished.
  No stutters, no dropped frames, no moment that makes a player want to stop.
  This is the difference between a project and a product.
  Performance is not a nice-to-have in VR. It is comfort, and comfort is everything.
on_screen:
  title: Polish & Performance
  subtitle: Module 10
  body: Make it run smooth and feel finished
  layout: center
visual: a stuttering frame counter steadies into a smooth, locked line
duration_hint_sec: 22

### scene_02_why
narration: |
  Here is why performance matters more in VR than anywhere else.
  On a flat screen, a dropped frame is a small glitch. In VR, it can make a person physically sick.
  Your app is strapped to someone's face, filling their whole view, twice, once per eye.
  If the frame rate drops, the world stutters, and the body rebels.
  Smooth is not about looking good. It is about not making people ill.
on_screen:
  title: Why Performance Is Comfort
  bullets: ["A dropped frame on a screen is a glitch",
            "In VR it can make someone sick",
            "It fills their whole view, twice, per eye",
            "Smooth isn't pretty — it's not making people ill"]
  layout: bullets
visual: a steady framerate keeps a horizon level; a drop makes it lurch sickeningly
duration_hint_sec: 38

### scene_03_framerate
narration: |
  So your target is a steady frame rate. On Quest, that is 72 frames per second or higher, never dropping.
  A mobile headset is a powerful phone, not a gaming PC.
  Every frame, it has to draw your whole world, twice. That is a tight budget.
  The whole game of optimization is simple to state. Do less work per frame,
  so the headset always finishes in time. Everything else is detail.
on_screen:
  title: Hit a Steady Frame Rate
  bullets: ["Target 72 fps or higher on Quest, never dropping",
            "The headset is a powerful phone, not a PC",
            "It draws your whole world, twice, every frame",
            "Optimization = do less work per frame"]
  layout: bullets
visual: a frame-time budget bar fills; staying under the line keeps the world smooth
duration_hint_sec: 38

### scene_04_profiler
narration: |
  Before you fix anything, you measure. You never guess at performance.
  Unity's profiler and the on-headset stats show you where each frame's time actually goes.
  Is it the graphics, drawing too much? Is it the code, doing too much per frame?
  Measure first, find the real bottleneck, then fix that one thing.
  Optimizing the wrong thing wastes days. The profiler points you at the right thing.
on_screen:
  title: Measure Before You Fix
  bullets: ["Never guess at performance",
            "Use the profiler + on-headset stats",
            "Is it graphics, or is it code?",
            "Find the real bottleneck, fix that one thing"]
  layout: bullets
visual: a profiler graph highlights the single tallest spike as the true culprit
duration_hint_sec: 38

### scene_05_graphics
narration: |
  Most VR performance problems are graphics. Here are the big levers.
  Draw calls. Every separate object and material is work, so combine them where you can.
  Texture size. Huge textures eat memory and bandwidth, so shrink them to what you actually need.
  Polygons. Fewer triangles mean faster frames, so simplify heavy models.
  Small, dense scenes run better than big, wasteful ones.
on_screen:
  title: The Graphics Levers
  bullets: ["Draw calls — combine objects and materials",
            "Texture size — shrink to what you need",
            "Polygons — simplify heavy models",
            "Small and dense beats big and wasteful"]
  layout: bullets
visual: many objects merge, a texture downsizes, a model simplifies — the budget bar drops
duration_hint_sec: 40

### scene_06_lighting
narration: |
  Lighting is one of the biggest costs, and one of the biggest wins.
  Real-time lights and shadows are expensive, recalculated every single frame.
  The trick is baking. You compute the lighting once, ahead of time, and store it into the scene.
  Now your room looks beautifully lit, but the headset is barely doing any lighting work at runtime.
  For a mostly static scene like ours, baked lighting is almost free beauty.
on_screen:
  title: Bake Your Lighting
  bullets: ["Real-time lights + shadows are expensive",
            "Baking computes the lighting once, ahead of time",
            "Stored into the scene — almost free at runtime",
            "Static scenes get beautiful light, nearly free"]
  layout: bullets
visual: a flickering real-time light freezes into a baked, glowing, cost-free room
duration_hint_sec: 40

### scene_07_agent
narration: |
  Let your agent help you optimize.
  You say: profile my scene and tell me the biggest performance cost,
  then help me reduce draw calls, shrink oversized textures, and set up baked lighting for the static room.
  Keep it looking good while hitting a steady 72 frames per second.
  The agent suggests targeted fixes, and you apply them and re-measure.
on_screen:
  title: Let the Agent Optimize
  bullets: ["\"Profile and tell me the biggest cost\"",
            "\"Reduce draw calls, shrink textures\"",
            "\"Set up baked lighting for the static room\"",
            "Apply the fixes, then re-measure"]
  layout: bullets
visual: a request triggers targeted fixes; the framerate climbs and locks at 72
duration_hint_sec: 40

### scene_08_polish
narration: |
  Performance gets you comfort. Polish gets you delight. The small touches matter.
  A gentle fade from black when the app starts, instead of a jarring pop-in.
  Smooth transitions between states. Buttons that respond instantly.
  A loading moment that is calm, not a frozen screen.
  Polish is the difference between an app that works and an app that feels cared for.
on_screen:
  title: Polish — The Small Touches
  bullets: ["A gentle fade-in, not a jarring pop",
            "Smooth transitions between states",
            "Instantly responsive buttons",
            "Polish = an app that feels cared for"]
  layout: bullets
visual: rough cuts and pops smooth into gentle fades and responsive feedback
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what polish and performance unlock.
  A player who forgets they are wearing a headset, because nothing breaks the spell.
  Good reviews, because people feel comfortable, not queasy.
  And acceptance into the store, because Meta tests for a steady frame rate before they will publish you.
  This is the module that makes everything you built actually shippable.
on_screen:
  title: What Polish Unlocks
  bullets: ["A player who forgets the headset is there",
            "Good reviews — comfortable, not queasy",
            "Store acceptance — Meta tests frame rate",
            "It makes everything you built shippable"]
  layout: bullets
visual: a smooth, polished app earns a happy player and a green store checkmark
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you what to measure and what to fix.
  The lab guide beside it has every exact step to read the profiler, reduce draw calls,
  bake lighting, and hit a steady frame rate.
  Watch this once, then open the lab guide and make your app smooth.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (measure + fix)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then make your app smooth"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 10. Your app now runs smooth, comfortable, and finished.
  Next module is the last one, and the one almost nobody teaches. Shipping.
  We package your app and submit it to the Meta Store, so the world can actually download
  and play what you built. Open the lab guide. Let's make it smooth.
on_screen:
  title: Next — Ship to Meta's Store
  subtitle: Module 11
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 10 marked complete, node 11 begins to glow; logo outro
duration_hint_sec: 24
