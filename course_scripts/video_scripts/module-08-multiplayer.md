---
title: "Module 8 — Multiplayer"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_08_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, a second person will join your VR room.
  You will see their head and hands move in real time, and you will interact in the same space.
  This is the leap from a place you visit alone to a place you share.
  Multiplayer is what turns an app into a world with other people in it.
on_screen:
  title: Multiplayer
  subtitle: Module 8
  body: A second person joins your VR room — live
  layout: center
visual: a second floating headset-and-hands avatar fades into the room and waves
duration_hint_sec: 22

### scene_02_why
narration: |
  Why add other people?
  Because presence with others is VR's superpower. Sharing a space with a friend who feels truly there
  is something a flat screen can never do.
  Social apps, multiplayer games, training together, virtual meetings, all of it needs this.
  Multiplayer is also the hardest thing in this course, so we will keep our first version simple.
on_screen:
  title: Why Multiplayer
  bullets: ["Shared presence is VR's superpower",
            "A friend who feels truly there",
            "Social, games, training, meetings",
            "It's the hardest piece — we start simple"]
  layout: bullets
visual: two avatars share a space; a flat screen beside them looks lonely by comparison
duration_hint_sec: 38

### scene_03_networking
narration: |
  First, the core idea. Networking.
  Each player runs the app on their own headset. The challenge is keeping those copies in sync,
  so when you move your hand, the other person sees your hand move, almost instantly.
  A networking library does the hard part. It sends each player's position and actions over the internet
  and keeps everyone's world matching. You do not write that from scratch.
on_screen:
  title: The Core Idea — Networking
  bullets: ["Each player runs the app on their headset",
            "The challenge: keep the copies in sync",
            "Your hand moves -> they see it move",
            "A networking library does the hard part"]
  layout: bullets
visual: two headsets exchange little packets of position data across a globe
duration_hint_sec: 38

### scene_04_pick_library
narration: |
  You do not build networking yourself. You pick a proven library.
  For Quest, common choices are Photon Fusion, Unity's Netcode for GameObjects, and Normcore.
  They handle the hard parts. Connecting players into a room, syncing positions, and managing who owns what.
  We will use one of these and let it carry the weight,
  so you focus on what your shared world does, not on raw network code.
on_screen:
  title: Pick a Networking Library
  bullets: ["Don't build networking yourself",
            "Photon Fusion, Unity Netcode, Normcore",
            "They handle rooms, sync, and ownership",
            "You focus on the world, not the wiring"]
  layout: bullets
visual: three library logos line up; one is chosen and connects two players
duration_hint_sec: 38

### scene_05_avatars
narration: |
  When someone joins, they need a body you can see.
  At minimum, that is a head and two hands, floating where their real head and hands are.
  The networking library streams their headset and controller positions,
  and you attach simple shapes or avatar models to those positions.
  Suddenly there is a person across from you, looking around, reaching out. Even simple avatars feel alive.
on_screen:
  title: Give Players a Body
  bullets: ["A joiner needs a visible body",
            "At minimum: a head and two hands",
            "Stream their headset + controller positions",
            "Even simple avatars feel alive"]
  layout: bullets
visual: floating head and hand shapes snap to a remote player's tracked positions
duration_hint_sec: 38

### scene_06_sync_objects
narration: |
  It is not just people you sync. It is the world too.
  If you pick up the stone, the other player should see it lift in your hand.
  To make an object shared, you mark it as a networked object, and the library keeps its position in sync.
  There is also the idea of ownership. Whoever grabs an object controls it, so two people are not
  fighting over the same stone at once. The library manages that handoff.
on_screen:
  title: Sync the World, Not Just People
  bullets: ["Shared objects sync their position too",
            "Mark an object as networked",
            "Ownership: whoever grabs it controls it",
            "The library manages the handoff"]
  layout: bullets
visual: one player lifts a stone; the same stone lifts in the other player's view
duration_hint_sec: 40

### scene_07_agent
narration: |
  Let your agent set up a simple shared room.
  You say: using my chosen networking library, let two players join the same room,
  show each remote player as a head and two hands, and make the stone a networked object
  that either player can pick up. Keep it to two players and keep it simple.
  The agent scaffolds the networking, the avatars, and the synced stone.
on_screen:
  title: Let the Agent Set It Up
  bullets: ["\"Two players join the same room\"",
            "\"Show each player as a head + two hands\"",
            "\"Make the stone a networked, grabbable object\"",
            "Agent scaffolds networking + avatars + sync"]
  layout: bullets
visual: a request produces a two-player room with avatars and a shared stone
duration_hint_sec: 40

### scene_08_gotchas
narration: |
  Multiplayer has the most traps, so go slow.
  If the other player does not appear, you are probably not connected to the same room or server.
  If their movement is jumpy, that is normal network lag. Smoothing helps, but some delay is unavoidable.
  If a grabbed object jitters, two clients are fighting for ownership, so enforce one owner at a time.
  Test with a real second device early. The editor alone hides these problems.
on_screen:
  title: Multiplayer Gotchas
  bullets: ["No one appears? Not in the same room / server",
            "Jumpy movement? Network lag — smooth it",
            "Object jitters? Two owners — enforce one",
            "Test with a real second device early"]
  layout: bullets
visual: a missing player, a jittery avatar, and a contested object each get a fix marker
duration_hint_sec: 40

### scene_10_unlocks
narration: |
  Think about what multiplayer unlocks.
  Co-op games. Social hangouts. Training where an instructor stands beside you.
  Virtual meetings that feel like a real room instead of a grid of faces.
  The moment another real person shares your space, your app stops being a tool
  and becomes a place. That is the most powerful thing VR can do.
on_screen:
  title: What Multiplayer Unlocks
  bullets: ["Co-op games and social hangouts",
            "Training with an instructor beside you",
            "Meetings that feel like a real room",
            "Your app becomes a place, not a tool"]
  layout: bullets
visual: a single-user app blooms into a shared social space full of avatars
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you how shared VR works.
  The lab guide beside it has every exact step to set up a networking library and a two-player room,
  and the prompt to make a shared, grabbable stone.
  Watch this once, then open the lab guide and invite someone in.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (how shared VR works)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then invite someone in"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 8, the hardest one, behind you. Your room can now hold more than one person.
  Next module, we step into the real world. Mixed reality,
  where your virtual objects appear in your actual room, on your real desk, through Quest passthrough.
  Open the lab guide. Let's invite someone in.
on_screen:
  title: Next — Mixed Reality
  subtitle: Module 9
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 8 marked complete, node 9 begins to glow; logo outro
duration_hint_sec: 24
