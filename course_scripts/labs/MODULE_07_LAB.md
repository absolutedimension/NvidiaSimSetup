# Module 7 — Lab Guide

**Saving & Persistence — Make Your App Remember**

> Use this alongside the Module 7 video. The video is the map (what + how to save); this guide is
> the terrain (every exact step). By the end, your comfort settings and object positions survive a
> full app restart.
>
> **Time:** ~40 min. **You need:** ZenSpace (Modules 1–6), Claude Code in the project, your Quest.

---

## Step 0 — Decide what to save

For ZenSpace, save:
- [ ] Comfort settings (teleport vs smooth, vignette on/off)
- [ ] The position of the stone(s) the user arranged

Don't save: temporary effects, hover glows, anything that should reset each launch.

---

## Step 1 — PlayerPrefs for a simple setting

PlayerPrefs is Unity's tiny built-in store for single values.

Write (when a setting changes):
```csharp
PlayerPrefs.SetString("ComfortMode", "Teleport");
PlayerPrefs.SetFloat("Volume", 0.8f);
PlayerPrefs.Save();
```

Read (at startup):
```csharp
string mode = PlayerPrefs.GetString("ComfortMode", "Teleport"); // 2nd arg = default
float vol   = PlayerPrefs.GetFloat("Volume", 0.8f);
```

> Ask the agent: *"Wire my comfort toggle and volume slider to PlayerPrefs so they save on
> change and load at startup, with sensible defaults."*

---

## Step 2 — A JSON save file for richer state

For object positions and bigger data, save a file. Have the agent build it:

```
Create a save system using JSON:
- a [Serializable] SaveData class holding the comfort settings and a list of stone
  positions (Vector3) + rotations
- SaveGame(): gather current state, JsonUtility.ToJson, write to
  Application.persistentDataPath
- LoadGame(): if the file exists, read + JsonUtility.FromJson, then apply positions;
  if not, use defaults
Tell me the exact file path on the Quest and where to call Save and Load.
```

> `Application.persistentDataPath` is the safe per-app folder that survives app restarts on Quest.

---

## Step 3 — Call save at the right moments

Hook saving to:
- **On change** — right after the user moves a stone or flips a setting
- **On quit / focus loss** — `OnApplicationPause(bool paused)` and `OnApplicationQuit()`
  (the user can remove the headset any time)

Ask the agent:
```
Call SaveGame() whenever a stone is released after moving and in OnApplicationPause(true)
and OnApplicationQuit(). Call LoadGame() once in Start(), before the scene is shown.
```

---

## Step 4 — Test the round trip

1. **Build and Run.** Move a stone, change a comfort setting.
2. **Fully quit** the app on the Quest (not just headset off — close it).
3. **Relaunch.** The stone should be where you left it; the setting should be remembered.

🎉 Your app now remembers across sessions.

---

## Step 5 — Handle the edge cases

Ask the agent to make the save system robust:
```
Make the save system safe: handle the first-run case where no file exists (use defaults,
no error), add an integer version field to SaveData so future changes don't break old
saves, and wrap file reads/writes in try/catch so a corrupt file never crashes the app.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Nothing persists | No save on quit, or app killed before write — save in `OnApplicationPause`/`OnApplicationQuit` and call `PlayerPrefs.Save()`. |
| Crash on first launch | No save file yet — `LoadGame()` must handle the missing-file case with defaults. |
| Old saves break after a data change | Add a `version` int to SaveData and migrate/ignore older versions. |
| File not found on Quest | Use `Application.persistentDataPath`, not a hard-coded PC path. |
| Positions load but look wrong | You saved world vs local space inconsistently — pick one and be consistent. |

---

## ✅ Module 7 complete — you now have:

- PlayerPrefs saving simple settings
- A JSON save file for object positions + richer state
- Saves triggered on change and on quit, load at startup
- Robust handling of first-run, versioning, and corrupt files
- An app that remembers across sessions and days

**Next module:** multiplayer — two users share the same VR space in real time. See you there.
