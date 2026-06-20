# Module 2 — Lab Guide

**Your AI Coding Partner — Set Up Claude Code for VR Development**

> Use this guide alongside the Module 2 video. The video is the map (the workflow + mindset).
> This guide is the terrain (every exact command). By the end, Claude Code is wired into your
> ZenSpace project and you've shipped your first interactive feature — a grabbable, chiming stone.
>
> **Time:** ~30–45 min. **You need:** the ZenSpace Unity project from Module 1, your Quest, and a
> Claude account (claude.ai).

---

## Step 0 — Before you start

- [ ] ZenSpace project from Module 1 opens cleanly in Unity 6
- [ ] You can build to your Quest (you did this in Module 1)
- [ ] A Claude account — sign up free at **claude.ai** if you don't have one

---

## Step 1 — Install Claude Code

Claude Code is a command-line tool that runs on your computer.

1. **Install Node.js** (if you don't have it): download the LTS version from **nodejs.org** and install.
   - Verify in a terminal: `node --version` → should print a version number.
2. **Install Claude Code:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
3. **Verify:**
   ```bash
   claude --version
   ```
   - Windows tip: use **PowerShell** or **Windows Terminal**, not the old cmd.exe.

---

## Step 2 — Open Claude Code inside your project

The agent can only help with files it can see — so you run it *from inside your project folder*.

1. Open a terminal and navigate to your ZenSpace folder:
   ```bash
   cd path/to/ZenSpace
   ```
   *(In Unity: right-click any asset → "Show in Explorer/Finder" to find the path.)*
2. Start the agent:
   ```bash
   claude
   ```
3. The first time, it opens your browser to log in to your Claude account. Approve it. Done.

> You now have a chat prompt sitting *inside* your project. Anything you ask, it answers in the
> context of your actual files.

---

## Step 3 — Give it context (do this once)

Tell the agent the rules of your world so it writes Quest-correct code.

Paste this as your first message:

```
This is a Unity 6 project for the Meta Quest, built with the Meta XR All-in-One SDK
and URP. The player is an OVRCameraRig. I'm a beginner — when you write C#, keep it
simple, add short comments, and tell me exactly which GameObject to attach each
script to. Always explain what you changed.
```

> Optional but recommended: ask it to save that as a `CLAUDE.md` file in your project so it
> remembers across sessions: *"Save those project rules to a CLAUDE.md file."*

---

## Step 4 — Your first real task: make the stone grabbable

Remember the grey meditation stone from Module 1. Let's make it interactive.

Type this to the agent:

```
In my ZenSpace scene there is a Sphere called "Stone". Make it grabbable with the
Meta XR Interaction SDK so I can pick it up with my hands or controllers. When I grab
it, play a soft chime sound and trigger a short haptic buzz in the controller. Tell me
every step to wire it up in the Unity Editor.
```

The agent will:
- Write one or more C# scripts (e.g. `GrabbableStone.cs`)
- Tell you which components to add (Grabbable, hand/controller interactors, an AudioSource)
- Tell you exactly which GameObject to attach each script to

**Follow its Editor steps exactly.** If it references an audio clip, drag any short chime `.wav`
into your project and assign it (the agent will tell you where).

---

## Step 5 — Test on your Quest

1. Save the scene (Ctrl/Cmd+S) and the project.
2. **Build and Run** to your Quest (same as Module 1).
3. Put on the headset, reach out, and grab the stone.
   - You should hear the chime and feel the controller buzz.

🎉 You just shipped a feature without hand-typing a line of code.

---

## Step 6 — The four habits that make this work

1. **Read what it writes.** Open the generated `.cs` file. Don't understand a line? Ask:
   *"Explain line 14 of GrabbableStone.cs in plain English."*
2. **Be specific.** ❌ "make it nicer" → ✅ "make the stone glow brighter while I'm holding it."
3. **One feature at a time.** Ship grabbing first, *then* ask for the glow, *then* the chime variation.
4. **Feed errors back.** When Unity shows a red error:
   - Copy the full error text from **Window → Console**.
   - Paste it to the agent: *"I got this error when I pressed Play: <paste>. I was doing X. Fix it."*
   - It reads the error and patches the script.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `claude: command not found` | Node/npm global bin isn't on PATH. Reopen the terminal; on Windows use PowerShell. Re-run `npm install -g @anthropic-ai/claude-code`. |
| Agent edits the wrong file | You started it outside the project folder. `cd` into ZenSpace, then run `claude` again. |
| "Type or namespace not found" (Oculus/Meta) | The Meta XR SDK isn't imported in this project — redo Module 1 Step 3, then ask the agent to retry. |
| Stone doesn't grab in headset | Tell the agent: "the grab isn't triggering — what interactor components does the OVRCameraRig need?" and follow its checklist. |
| No sound | Confirm the stone has an AudioSource with a clip assigned, and ask the agent to verify the play call. |

---

## ✅ Module 2 complete — you now have:

- Claude Code installed and running inside your ZenSpace project
- Project context saved so it writes Quest-correct code
- A grabbable stone that chimes and buzzes — your first AI-built interactive feature
- The four habits: read, be specific, one-at-a-time, feed errors back

**Next module:** real hand tracking and grabbing across your whole room. See you there.
