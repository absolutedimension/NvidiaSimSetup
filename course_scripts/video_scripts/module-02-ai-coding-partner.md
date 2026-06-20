---
title: "Module 2 — Your AI Coding Partner"
video_type: full_lesson
length_target_sec: 420
mode: B
voice: { name: male_confident, speed: 0.78 }
background_shader: circuit_mind
presenter: none
music: ambient_low
aspect: 16:9
# COMPANION: course_scripts/labs/MODULE_02_LAB.md — exact install + setup commands.
---

## scenes

### scene_01_hook
narration: |
  By the end of this module, you will describe a feature in plain English,
  and watch working code appear inside your Unity project.
  No typing C# by hand. You describe. The agent builds. You test in VR.
  This is the skill that changes everything about how you make this app.
on_screen:
  title: Your AI Coding Partner
  subtitle: Module 2
  body: Describe it — and watch the code appear
  layout: center
visual: a plain-English sentence morphs into a code block, then into a glowing VR object
duration_hint_sec: 22

### scene_02_what_is_agent
narration: |
  So what is an AI coding agent?
  It is a tool that lives next to your project, reads your files, and writes code for you.
  We use one called Claude Code. You talk to it in plain language, like a teammate.
  You say what you want. It writes the script, puts it in the right folder, and explains what it did.
  You are still the developer. You are just not the typist anymore.
on_screen:
  title: What Is an AI Coding Agent?
  bullets: ["Lives next to your project, reads your files",
            "We use Claude Code", "You talk to it like a teammate",
            "You stay the developer — not the typist"]
  layout: bullets
visual: a sidebar panel sits beside a project file tree; arrows show it reading files and writing a new one
duration_hint_sec: 36

### scene_03_why_vr
narration: |
  Why does this matter so much for VR?
  VR code is fiddly. Grabbing, hand tracking, events that fire when you touch something,
  lifecycles that run every frame. There is a lot of boilerplate to get right.
  Get one line wrong and your app crashes on the headset.
  The agent handles that boilerplate. You focus on what the feature should do,
  not on remembering the exact name of every Unity method.
on_screen:
  title: Why This Matters for VR
  bullets: ["VR code has a lot of fiddly boilerplate",
            "Grab events, hand tracking, per-frame lifecycles",
            "One wrong line crashes on the headset",
            "Let the agent handle boilerplate — you handle intent"]
  layout: bullets
visual: a tangle of method names untangles into one clean intent label
duration_hint_sec: 38

### scene_04_setup
narration: |
  Setting it up is quick, and the lab guide has every exact command.
  First, you install Claude Code on your computer.
  Then you open it inside your ZenSpace project folder, so it can see your files.
  Then you give it a little context. You tell it: this is a Unity 6 project for Meta Quest,
  using the Meta XR SDK. Now it knows the rules of your world before it writes a line.
on_screen:
  title: Setting It Up
  bullets: ["Install Claude Code on your computer",
            "Open it inside your ZenSpace project folder",
            "Give it context: Unity 6, Meta Quest, Meta XR SDK"]
  layout: bullets
visual: three tiles snap in; a small "→ follow the Lab Guide" tag glows beneath
duration_hint_sec: 34

### scene_05_loop
narration: |
  Here is the core loop you will run all course long.
  You describe a feature. The agent writes the code.
  You go into Unity, press play or build to your Quest, and test it.
  If it is not right, you tell the agent what happened, and it fixes it.
  Describe. Generate. Test. Refine. That is the whole rhythm of building with an agent.
on_screen:
  title: The Core Loop
  body: Describe  →  Generate  →  Test in VR  →  Refine
  layout: center
visual: a four-node circular loop lights up node by node, then cycles
duration_hint_sec: 32

### scene_06_first_task
narration: |
  Let us make it real. Remember the meditation stone from Module 1?
  You will say to the agent: make the stone grabbable, play a soft chime when I pick it up,
  and add a gentle haptic buzz in the controller.
  In a few seconds, it writes a C# script and tells you to attach it to the stone.
  You build to your Quest, reach out, and pick up the stone. It chimes. The controller buzzes.
  You just shipped a feature without writing a line of code yourself.
on_screen:
  title: Your First Real Task
  bullets: ["\"Make the stone grabbable\"",
            "\"Play a chime when I pick it up\"",
            "\"Add a haptic buzz in the controller\"",
            "→ agent writes the C#, you attach + test"]
  layout: bullets
visual: a speech bubble of the request flows into a generated script icon, then a hand grabbing a glowing stone
duration_hint_sec: 42

### scene_07_read_code
narration: |
  Now, one rule I want you to take seriously.
  Read the code it writes. You do not have to understand every line at first,
  but look at it. Ask the agent to explain anything you do not get.
  You are the engineer. The agent is fast, but it can be confidently wrong.
  Reviewing what it writes is how you stay in control, and how you actually learn to code.
on_screen:
  title: Read the Code It Writes
  bullets: ["Always look at what it generated",
            "Ask it to explain anything unclear",
            "It is fast — but it can be confidently wrong",
            "Reviewing keeps you in control, and teaches you"]
  layout: bullets
visual: a code panel with a magnifier passing over it; a checkmark appears after review
duration_hint_sec: 36

### scene_08_prompting
narration: |
  How you ask matters. A few simple habits make the agent far more useful.
  Be specific. Instead of make it nice, say make the stone glow brighter when I hold it.
  Give context. Tell it which object, which script, what you already tried.
  And do one feature at a time. Small, clear requests get clean, correct code.
  Big vague requests get messy results you have to untangle.
on_screen:
  title: How to Ask for Code
  bullets: ["Be specific — name the object and the behavior",
            "Give context — what exists, what you tried",
            "One feature at a time",
            "Small clear asks → clean correct code"]
  layout: bullets
visual: a vague prompt with a red mark transforms into a specific prompt with a green check
duration_hint_sec: 36

### scene_09_errors
narration: |
  And when something breaks, because it will, the fix is simple.
  Copy the red error from the Unity console. Paste it back to the agent.
  Say: I got this error, here is what I was doing. Fix it.
  The agent reads the error and patches the code. This is exactly how I work every day.
  Errors are not failures. They are just the next message in the conversation.
on_screen:
  title: When Something Breaks
  bullets: ["Copy the red error from the Unity console",
            "Paste it back to the agent with context",
            "It reads the error and patches the code",
            "Errors are just the next message, not failures"]
  layout: bullets
visual: a red console error flows into the agent and returns as a green fixed line
duration_hint_sec: 36

### scene_10_leverage
narration: |
  Think about what this gives you.
  You do not need years of C# before you can build.
  You need a clear idea, the patience to describe it well, and the judgment to review the result.
  That is how I built most of EnergyField, my app in Meta's alpha program.
  Description plus review. That is the new way to build, and now it is yours.
on_screen:
  title: What This Gives You
  bullets: ["Build without years of C# first",
            "Clear idea + good description + review",
            "How I built most of EnergyField",
            "Description + judgment — the new way to build"]
  layout: bullets
visual: a single person silhouette with many generated scripts orbiting them
duration_hint_sec: 34

### scene_11_how_module_works
narration: |
  So here is how to use this module. This video is the map. It shows you the workflow and the mindset.
  The lab guide beside it has the exact commands to install and connect Claude Code,
  and the exact first prompt to make the stone grabbable.
  Watch this once, then open the lab guide and set up your own AI coding partner.
on_screen:
  title: How to Use This Module
  bullets: ["This video = the MAP (workflow + mindset)",
            "The Lab Guide = the TERRAIN (exact commands)",
            "Watch once, then set up your own agent"]
  layout: split
visual: a folded map and a checklist side by side; a pointer moves between them
duration_hint_sec: 28

### scene_12_cta
narration: |
  That is Module 2. You now have an AI coding partner wired into your VR project,
  and you have shipped your first interactive feature.
  Next module, we go hands on. Real hand tracking and grabbing, so your whole room becomes interactive.
  Open the lab guide. Let's set up your agent.
on_screen:
  title: Next — Hands & Grabbing
  subtitle: Module 3
  body: Open the Lab Guide and let's start
  layout: center
visual: timeline reappears, node 2 marked complete, node 3 begins to glow; logo outro
duration_hint_sec: 24
