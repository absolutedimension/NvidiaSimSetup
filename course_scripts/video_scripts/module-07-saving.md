---
title: "Module 7 — Saving & Persistence"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_07_LAB.md
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, your app will remember.
  The user takes off the headset, comes back tomorrow, and their world is exactly as they left it.
  The stone they moved is still there. The settings they chose are still set.
  An app that forgets everything feels like a toy. An app that remembers feels real.
on_screen:
  title: Saving & Persistence
  subtitle: Module 7
  body: Your app remembers between sessions
  layout: center
visual: a scene fades out as a headset is removed, then fades back identical when worn again
duration_hint_sec: 22

### scene_02_why
narration: |
  Think about why this matters.
  Every meaningful app keeps state. Your progress in a game. Your settings. Your saved work.
  Without saving, every session starts from zero, and nothing the user does ever sticks.
  Saving is the difference between an experience and a real product.
  It is what makes your app worth coming back to.
on_screen:
  title: Why Persistence Matters
  bullets: ["Every real app keeps state",
            "Progress, settings, saved work",
            "Without it, every session starts from zero",
            "Persistence makes an app worth returning to"]
  layout: bullets
visual: a counter resets to zero again and again, then sticks once saving turns on
duration_hint_sec: 36

### scene_03_what_to_save
narration: |
  First, decide what is worth saving.
  Not everything. You save the things the user would be annoyed to lose.
  Their comfort settings. Their progress or unlocks. The position of objects they arranged.
  You do not save things that should reset, like a temporary animation or a one-time effect.
  Choosing what to persist is half the work.
on_screen:
  title: Decide What to Save
  bullets: ["Save what the user would hate to lose",
            "Settings, progress, arranged objects",
            "Don't save things that should reset",
            "Choosing what to persist is half the work"]
  layout: bullets
visual: items sort into a "save" box and a "let it reset" box
duration_hint_sec: 36

### scene_04_playerprefs
narration: |
  For small, simple values, Unity gives you PlayerPrefs.
  It is a tiny built-in store for single settings. A volume level. A chosen comfort mode. A high score.
  You write a value with a key, like comfort equals teleport, and read it back next time.
  It is perfect for a handful of simple settings, and it takes one line of code each.
  For anything bigger, you will want a save file.
on_screen:
  title: PlayerPrefs — For Small Values
  bullets: ["Unity's tiny built-in settings store",
            "Volume, comfort mode, a high score",
            "Write with a key, read it back next time",
            "One line each — but only for small values"]
  layout: bullets
visual: a few labeled keys drop into a small box and are read back later
duration_hint_sec: 38

### scene_05_json
narration: |
  For richer state, you save a file, usually in a format called JSON.
  JSON is just structured text. You gather your data, the positions of objects, the player's progress,
  into a small object, turn it into JSON text, and write it to a file on the headset.
  Next launch, you read that file back and rebuild the scene from it.
  This is how real save systems work, and your agent can write the whole thing.
on_screen:
  title: JSON — For Richer State
  bullets: ["Save a structured file, usually JSON",
            "Gather your data into one object",
            "Write it to a file on the headset",
            "Next launch, read it back and rebuild"]
  layout: bullets
visual: scene data collapses into a JSON document, saves, then reinflates the scene
duration_hint_sec: 38

### scene_06_when
narration: |
  When do you actually save?
  Save when something important changes, so a crash never loses much. After a setting is changed.
  After the user arranges an object. And always save when the app loses focus or quits,
  because the user might take the headset off at any moment.
  Then load once, at startup, before the scene is shown.
on_screen:
  title: When to Save & Load
  bullets: ["Save when something important changes",
            "Save when the app loses focus or quits",
            "The user can stop at any moment",
            "Load once, at startup, before the scene shows"]
  layout: bullets
visual: a timeline marks save points at each change and at quit; one load at launch
duration_hint_sec: 38

### scene_07_agent
narration: |
  Let your agent build the save system.
  You say: save the user's comfort settings and the positions of the stones to a file when they change
  and when the app quits, and load them back when the app starts.
  Use JSON, and tell me where the file lives on the Quest.
  The agent writes the save and load code, hooks it to the right moments, and explains it.
on_screen:
  title: Let the Agent Build It
  bullets: ["\"Save settings + object positions to a file\"",
            "\"On change and on quit; load at startup\"",
            "\"Use JSON; tell me where the file lives\"",
            "Agent writes save/load + hooks the moments"]
  layout: bullets
visual: a spoken request produces a save file that survives an app restart
duration_hint_sec: 40

### scene_08_gotchas
narration: |
  A few persistence traps.
  If nothing saves, you probably forgot to save on quit, or the app was killed before writing.
  If the file will not load, it may be missing on first run. Always handle the no-file-yet case gracefully.
  If old saves break after you change your data, you need a version number in the file.
  And never save secrets in plain text. Tell the agent, and it handles these cases.
on_screen:
  title: Persistence Gotchas
  bullets: ["Nothing saves? You forgot to save on quit",
            "Won't load? Handle the no-file-yet case",
            "Old saves break? Add a version number",
            "Never store secrets in plain text"]
  layout: bullets
visual: a missing file, a broken old save, and a leaked secret each get a fix marker
duration_hint_sec: 38

### scene_09_anchors
narration: |
  There is one kind of persistence unique to mixed reality. Spatial anchors.
  A spatial anchor remembers a real-world spot, so a virtual object you placed on your real desk
  is still on that desk when you come back, even days later.
  Quest saves these anchors for you. You will use them in the mixed reality module.
  For now, just know that the place itself can be saved, not only the data.
on_screen:
  title: Spatial Anchors — Saving Places
  bullets: ["A persistence kind unique to mixed reality",
            "Remembers a real-world spot",
            "A virtual object stays on your real desk",
            "The place itself is saved, not only data"]
  layout: bullets
visual: a virtual object pinned to a real desk reappears in the same spot next session
duration_hint_sec: 38

### scene_10_unlocks
narration: |
  Think about what saving unlocks.
  Real progress, so effort is never wasted. Personalization, because the app remembers each user's choices.
  And trust, because nothing the user does disappears.
  This is the quiet feature that makes an app feel professional.
  Nobody praises good saving. Everyone notices when it is missing.
on_screen:
  title: What Saving Unlocks
  bullets: ["Real progress — effort is never wasted",
            "Personalization — it remembers each user",
            "Trust — nothing disappears",
            "Unnoticed when good, glaring when missing"]
  layout: bullets
visual: a user returns to a personalized, remembered world that greets them by state
duration_hint_sec: 36

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you what to save and how.
  The lab guide beside it has every exact step for PlayerPrefs and a JSON save file,
  and the prompt to build a save system for your room.
  Watch this once, then open the lab guide and make your app remember.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (what + how to save)",
            "The Lab Guide = the TERRAIN (exact steps)",
            "Watch once, then make your app remember"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 7. Your app now remembers, between sessions, across days.
  Next module, we open it up to other people. Multiplayer,
  where two users share the same VR space, see each other, and interact in real time.
  Open the lab guide. Let's make your app remember.
on_screen:
  title: Next — Multiplayer
  subtitle: Module 8
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 7 marked complete, node 8 begins to glow; logo outro
duration_hint_sec: 24
