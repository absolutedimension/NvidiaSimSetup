---
title: "Module 5 — Audio & Ambience"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_05_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, when you grab the stone, the chime will sound like it is
  truly coming from the stone, off to your left or right, exactly where it sits.
  Your room will have a living soundscape instead of dead silence.
  Sound is what turns a space you see into a place you believe.
on_screen:
  title: Audio & Ambience
  subtitle: Module 5
  body: Sound that comes from real places in your room
  layout: center
visual: a stone glows; a sound wave ripples out from its exact position, panning across
duration_hint_sec: 22

### scene_02_why_audio
narration: |
  Here is something most beginners underestimate. Sound is half of presence.
  You can have beautiful visuals, but in silence, a VR room feels dead and fake.
  Add the right sound, and your brain believes it is in a real place, instantly.
  Audio is the cheapest, fastest way to make your world feel alive.
  Never ship a VR app in silence.
on_screen:
  title: Sound Is Half of Presence
  bullets: ["Silence makes a VR room feel dead",
            "The right sound makes your brain believe",
            "Audio is the cheapest path to immersion",
            "Never ship a VR app in silence"]
  layout: bullets
visual: a silent room looks flat; sound waves fill it and it visibly comes alive
duration_hint_sec: 36

### scene_03_spatial
narration: |
  The magic word is spatial audio, also called 3D audio.
  A normal sound just plays in your ears. A spatial sound has a position in the room.
  As you walk toward it, it gets louder. When the source is on your left, you hear it on your left.
  The headset does all the math from your head position.
  Your job is simply to tell each sound where it lives.
on_screen:
  title: Spatial 3D Audio
  bullets: ["A spatial sound has a position in the room",
            "Walk closer, it gets louder",
            "Source on your left, you hear it on your left",
            "The headset does the math from your head"]
  layout: bullets
visual: a sound icon sits in 3D space; the listener moves and the volume + pan shift
duration_hint_sec: 38

### scene_04_audiosource
narration: |
  In Unity, sound comes from an AudioSource component.
  You put an AudioSource on an object, give it an audio clip, and it can play.
  The one setting that matters most is spatial blend.
  Set it to 3D, and the sound now lives at that object's position in the room.
  Leave it at 2D, and it just plays flat in your ears, with no sense of place.
on_screen:
  title: AudioSource + Spatial Blend
  bullets: ["Sound comes from an AudioSource component",
            "Put it on an object, give it a clip",
            "Spatial Blend = 3D -> lives at that position",
            "2D -> flat in your ears, no sense of place"]
  layout: bullets
visual: an AudioSource drops onto an object; a 2D/3D slider flips and the sound localizes
duration_hint_sec: 38

### scene_05_stone_voice
narration: |
  Let us give the stone a voice.
  You add an AudioSource to the stone, set its spatial blend to 3D, and assign the chime clip.
  Then, when you grab the stone, you play that source.
  Now the chime is not coming from inside your head. It is coming from the stone, in the world.
  Pick it up with your left hand, and you hear it from your left. That is the moment it clicks.
on_screen:
  title: Give the Stone a Voice
  bullets: ["Add an AudioSource to the stone",
            "Spatial Blend = 3D, assign the chime",
            "Play it on grab",
            "Now the chime comes from the stone, not your head"]
  layout: bullets
visual: the stone gets a small speaker icon; on grab, sound emits from its exact spot
duration_hint_sec: 38

### scene_06_ambient
narration: |
  Next, fill the silence with an ambient bed.
  This is a soft, looping background. A gentle wind, a low drone, distant room tone.
  It plays quietly under everything, and it is usually not spatial. It surrounds you evenly.
  A good ambient bed is one you barely notice, but the moment you mute it, the room feels empty.
  It is the floor that all your other sounds stand on.
on_screen:
  title: The Ambient Bed
  bullets: ["A soft, looping background sound",
            "Gentle wind, low drone, room tone",
            "Quiet, even, usually not spatial",
            "Barely noticed — but the room feels empty without it"]
  layout: bullets
visual: a faint waveform loops softly across the whole room as a base layer
duration_hint_sec: 38

### scene_07_reactive
narration: |
  Then add reactive sound, tied to what the user does.
  A soft hum when a hand hovers an object. A click when a button is poked. A chime on a grab.
  These are the audio version of the feedback you learned earlier.
  Every important action should make a sound, so the user hears that the world responded.
  Sound confirms. Without it, actions feel uncertain.
on_screen:
  title: Reactive Sound
  bullets: ["Tied to what the user does",
            "Hover hum, button click, grab chime",
            "The audio version of feedback",
            "Every action makes a sound — the world responded"]
  layout: bullets
visual: hover, click, and grab each fire a small distinct sound icon
duration_hint_sec: 38

### scene_08_agent
narration: |
  Let your agent build the whole soundscape.
  You say: give every grabbable object a 3D chime when grabbed, add a soft hover hum,
  add a calm ambient loop that plays under everything, and a gentle click on every button.
  Keep the volumes balanced so nothing is harsh.
  The agent adds the audio sources, wires the events, and tells you which clips to assign.
on_screen:
  title: Let the Agent Build the Soundscape
  bullets: ["\"3D chime on every grabbable\"",
            "\"Soft hover hum + button clicks\"",
            "\"A calm ambient loop under everything\"",
            "Agent adds the sources, wires events, names the clips"]
  layout: bullets
visual: one request spreads sound icons across every interactive object in the room
duration_hint_sec: 40

### scene_09_gotchas
narration: |
  A few audio traps to avoid.
  If a sound is the same volume everywhere, its spatial blend is still 2D. Set it to 3D.
  If everything is too loud and harsh, lower the volumes. VR audio should sit gently, not blast.
  If sound crackles, you may have too many sources at once, or clips that are clipping.
  And keep the ambient bed quiet. It supports the scene. It should never compete with it.
on_screen:
  title: Audio Gotchas
  bullets: ["Same volume everywhere? Blend is still 2D",
            "Too loud and harsh? Lower the volumes",
            "Crackling? Too many sources, or clipping clips",
            "Keep the ambient bed quiet — it supports, not competes"]
  layout: bullets
visual: a flat-volume sound, a blasting sound, and a crackle each get a fix marker
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what sound gives you.
  Immersion, so the room feels real. Emotion, because music and tone set a mood instantly.
  And direction, because a sound off to your side makes you turn and look.
  Audio quietly guides where the user pays attention.
  This is the difference between a silent slideshow and a place you can feel.
on_screen:
  title: What Sound Unlocks
  bullets: ["Immersion — the room feels real",
            "Emotion — tone sets a mood instantly",
            "Direction — a sound makes you turn and look",
            "A silent slideshow vs a place you can feel"]
  layout: bullets
visual: a quiet scene gains depth, mood color, and a turning listener following a sound
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the layers of a VR soundscape.
  The lab guide beside it has every exact step to make the stone sound spatial,
  and the prompt to give your whole room a living soundscape.
  Watch this once, then open the lab guide and bring sound to your world.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (the audio layers)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then bring sound to your world"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 5. Your room now sounds alive. Objects speak from their own positions,
  and a gentle ambience fills the air.
  Next module, we let the user move. Teleporting and gliding through a space far bigger than the room they stand in,
  without ever feeling sick.
  Open the lab guide. Let's bring sound to your world.
on_screen:
  title: Next — Movement & Locomotion
  subtitle: Module 6
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 5 marked complete, node 6 begins to glow; logo outro
duration_hint_sec: 24
