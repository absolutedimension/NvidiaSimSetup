# Module 8 — Lab Guide

**Multiplayer — Share Your VR Room With Another Person**

> Use this alongside the Module 8 video. The video is the map (how shared VR works); this guide is
> the terrain (every exact step). By the end, two players join the same room, see each other's head +
> hands, and share a grabbable stone.
>
> **Time:** ~60–90 min (the hardest module). **You need:** ZenSpace (Modules 1–7), Claude Code,
> **two** test devices ideally (your Quest + a second Quest, or Quest + the Editor in play mode).

---

## Step 0 — Pick a networking library

For a beginner-friendly Quest setup, **Photon Fusion** or **Normcore** are the gentlest (free tiers
exist). Unity **Netcode for GameObjects** is also solid. This guide uses generic steps — your agent
adapts them to the library you choose.

- [ ] Create a free account on your chosen service (e.g. Photon dashboard)
- [ ] Copy your **App ID / API key** — you'll paste it into Unity

---

## Step 1 — Install the library

1. Import the library's package (Asset Store or a provided `.unitypackage` / UPM URL).
2. Paste your **App ID / API key** into its settings asset.
3. Let the agent confirm setup:
   *"I installed [library] and added my App ID. Confirm the project is configured to connect, and
   list anything missing."*

---

## Step 2 — Connect two players into one room

Ask the agent:
```
Using [my networking library], add a simple connector that, on app start, connects to the
service and joins a shared room called "ZenSpaceRoom" (auto-create if it doesn't exist).
Cap it at 2 players. Log the connection state so I can see when a second player joins.
```

Test: run on your Quest **and** in the Editor's Play mode → both should report "joined ZenSpaceRoom".

---

## Step 3 — Give each player a body (avatar)

```
For each connected player, spawn a simple avatar: a small cube for the head and a cube for
each hand. Drive the LOCAL player's avatar from the OVRCameraRig head + hand positions, and
sync those transforms over the network so REMOTE players see them move. Keep it minimal.
```

Now when the second player moves, you should see their head + hands move in your headset.

---

## Step 4 — Make the stone a shared (networked) object

```
Make the Stone a networked object: sync its position and rotation across both players, and
add ownership so whoever grabs it controls it (transfer ownership on grab, release on let go).
When one player lifts it, the other should see it lift.
```

---

## Step 5 — Test with two real participants

1. Build to your Quest; run the second instance on a second Quest (or the Editor).
2. Confirm:
   - You see the other player's head + hands move
   - When you grab the stone, they see it move in your hand
   - When they grab it, you see it move in theirs

🎉 Your room is now a shared space.

---

## Step 6 — Smooth it out

```
Add interpolation/smoothing to remote avatars and the networked stone so their movement
looks smooth despite network updates arriving in steps. Keep it subtle.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Second player never appears | Both not joined to the **same room name / same App ID / same region** — check all three. |
| Remote movement is jumpy | Normal network lag — add interpolation (Step 6); some delay is unavoidable. |
| Grabbed stone jitters / snaps back | Two clients both think they own it — enforce ownership transfer on grab. |
| Works in Editor, not on Quest | Build settings / internet permission — confirm the Quest has network access and the build includes the library. |
| Avatars at wrong positions | Local vs world space mismatch when syncing transforms — be consistent. |

> ⚠️ Test with a real second device **early**. The Editor alone hides most multiplayer bugs.

---

## ✅ Module 8 complete — you now have:

- A networking library connected and configured
- Two players joining one shared room
- Visible head + hand avatars for each player
- A networked, ownership-managed grabbable stone
- The judgment to test with real devices and smooth network motion

**Next module:** mixed reality — your virtual objects in your real room through passthrough. See you there.
