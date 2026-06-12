# Cinematographer Demo Journey — Handoff for the GurulokInnerJourney Agent

**Date:** 2026-05-25
**From:** Deepak (working in `NvidiaSimSetup/` on Mac)
**For:** the Claude Code agent running in `C:\Users\unity-t4-tesla\GurulokInnerJourney`
**Reference:** the project's own `CLAUDE_FlowArtdance_VR.md` is authoritative — this doc only describes the new addition

---

## TL;DR

Add a new **"Cinematographer Demo"** journey to the GurulokInnerJourney Unity app. The journey places **Daphne** (a CC4 character, 14 MB GLB) on a virtual stage with **6 switchable HDRI skyboxes** (concert arena, jazz club, stadium, rave, empty theater, fashion runway). A **trained AI cinematographer** drives the camera along a 90-second trajectory that circles, orbits, and dynamically frames the performer. Voice commands switch between 6 lighting/environment modes in real time. The user can watch the AI-directed show from the camera's POV, or break free and look around the scene themselves. **Build a new APK, push to alpha.**

This is the **v1 product demo** for TrigunAI's AI Cinematographer — the first time a customer could experience the trained camera policy in VR rather than watching a flat video.

---

## Why this matters

TrigunAI trains RL-based cinematography policies that control a virtual drone camera around a live performer. The output so far has been flat MP4 renders from Blender. Showing this in VR is transformative:

1. **Immersion** — feel the camera swoops and mode transitions with your whole visual field
2. **Recording from VR** — Quest's built-in screen recording captures VR footage that looks 10x more impressive than Blender renders for demos/pitches
3. **Interactive** — the user can voice-command mode switches live, not just watch a pre-recorded sequence
4. **Product validation** — proves the pipeline works end-to-end: training → trajectory → VR playback

---

## What's already done (Mac side)

| Item | Status | File |
|---|---|---|
| Daphne CC4 character (trimmed mesh, 14 MB GLB) | ✅ | `models/daphne.glb` |
| 6 HDRI equirectangular skyboxes (8K JPGs, Blockade Labs) | ✅ | `hdri/*.jpg` |
| 90-second trained camera trajectory (4500 frames @ 50fps) | ✅ | `demo_90s_trajectory.json` |
| Voice command script (11 commands, mode switches + controls) | ✅ | `demo_script.json` |
| SRT subtitles for voice commands | ✅ | `demo_commands.srt` |
| Music track (cosmic-hypnotic) | ✅ | Already in Gurulok at `Assets/_Core/Audio/cosmic-hypnotic.mp3` |
| Reference flat render (90s, 1080p, music+subtitles) | ✅ | `reference_render.mp4` — watch this to understand what the VR version should look like |
| 6 × 25s single-mode rendered videos (trained camera per mode) | ✅ | `mode_videos/mode_*.mp4` — one per environment, can play as video panels or reference |
| 28s pitch video with TTS narration + text overlays | ✅ | `pitch_video_final.mp4` — Deepgram Aura TTS, spliced mode footage |

---

## File transfer

All files are in the `cinematographer_vr_handoff/` directory alongside this doc (90 MB total):

```
cinematographer_vr_handoff/
├── CINEMATOGRAPHER_VR_HANDOFF.md    ← this file
├── reference_render.mp4              ← 17 MB — 90s full demo (watch first)
├── pitch_video_final.mp4             ← 7.4 MB — 28s pitch with TTS narration
├── demo_90s_trajectory.json          ← 1.5 MB — camera path (4500 frames)
├── demo_script.json                  ← 1.4 KB — voice command timing
├── demo_commands.srt                 ← 547 B — subtitle file
├── models/
│   └── daphne.glb                    ← 14 MB — CC4 character (trimmed, 1024px textures)
├── hdri/
│   ├── hero_hdri.jpg                 ← 5.5 MB — massive concert arena, red/gold pyrotechnics
│   ├── intimate_hdri.jpg             ← 5.3 MB — warm jazz club, amber spotlights
│   ├── epic_hdri.jpg                 ← 4.1 MB — Olympic stadium, lasers, LED walls
│   ├── energy_hdri.jpg               ← 4.8 MB — underground rave, neon strobes
│   ├── solitude_hdri.jpg             ← 4.7 MB — empty theater, ghost light
│   └── beauty_hdri.jpg               ← 5.2 MB — fashion runway, chandeliers, pink/gold
└── mode_videos/
    ├── mode_hero_25s.mp4             ← 4.1 MB — HERO mode (concert arena, dramatic camera)
    ├── mode_intimate_25s.mp4         ← 2.8 MB — INTIMATE mode (jazz club, close framing)
    ├── mode_epic_25s.mp4             ← 3.5 MB — EPIC mode (stadium, wide sweeps)
    ├── mode_energy_25s.mp4           ← 4.8 MB — ENERGY mode (rave, dynamic motion)
    ├── mode_solitude_25s.mp4         ← 4.1 MB — SOLITUDE mode (empty theater, slow orbit)
    └── mode_beauty_25s.mp4           ← 1.2 MB — BEAUTY mode (fashion runway, elegant glide)
```

**Where to put them on the Windows machine:**
```
GurulokInnerJourney/Assets/_App/CinematographerJourney/
├── Models/daphne.glb
├── HDRI/hero_hdri.jpg
├── HDRI/intimate_hdri.jpg
├── HDRI/epic_hdri.jpg
├── HDRI/energy_hdri.jpg
├── HDRI/solitude_hdri.jpg
├── HDRI/beauty_hdri.jpg
├── Data/demo_90s_trajectory.json
├── Data/demo_script.json
└── Audio/  (cosmic-hypnotic.mp3 already in _Core/Audio/)
```

---

## Data formats

### Trajectory JSON (`demo_90s_trajectory.json`)

```json
{
  "fps": 50.0,
  "num_frames": 4500,
  "coordinate_system": "isaac_sim_z_up",
  "mode_schedule": "0:BEAUTY,400:HERO,1000:INTIMATE,1500:EPIC,2000:ENERGY,2750:SOLITUDE,3250:BEAUTY,3750:HERO",
  "frames": [
    {
      "t": 0.0,
      "drone_pos": [-2.81, 5.21, 1.98],
      "drone_quat": [0.002, 0.007, 0.003, 1.0],
      "dancer_pos": [-0.88, 1.49, 0.85],
      "mode": "BEAUTY"
    },
    ...
  ]
}
```

**Coordinate system:** Isaac Sim Z-up, right-handed. Convert to Unity (Y-up, left-handed):
- Position: `(x, y, z)` → Unity `(x, z, y)`
- Quaternion: `(qx, qy, qz, qw)` → Unity `(qx, qz, qy, -qw)` (negate w for handedness flip)

**Frame rate:** trajectory is at 50 fps. Unity should sample at its own frame rate and interpolate (lerp positions, slerp quaternions). With 4500 frames at 50fps = 90 seconds.

### Voice Script (`demo_script.json`)

```json
{
  "commands": [
    {"time": 0.0,  "mode": "BEAUTY",   "display": "\"Beauty\""},
    {"time": 8.0,  "mode": "HERO",     "display": "\"Hero\""},
    {"time": 15.0, "param": "distance", "delta": -0.5, "display": "\"Closer\""},
    {"time": 20.0, "mode": "INTIMATE", "display": "\"Intimate\""},
    {"time": 30.0, "mode": "EPIC",     "display": "\"Epic\""},
    {"time": 40.0, "mode": "ENERGY",   "display": "\"Energy\""},
    {"time": 55.0, "mode": "SOLITUDE", "display": "\"Solitude\""},
    {"time": 65.0, "mode": "BEAUTY",   "display": "\"Beauty\""},
    {"time": 75.0, "mode": "HERO",     "display": "\"Hero\""},
    {"time": 82.0, "control": "pause",  "display": "\"Hold\""},
    {"time": 85.0, "control": "play",   "display": "\"Resume\""}
  ]
}
```

### HDRI Skyboxes

All 6 are **8K equirectangular JPGs** from Blockade Labs. In Unity:
1. Import as Texture2D
2. Set **Texture Shape = Cube** and **Mapping = Latitude-Longitude Layout (Cylindrical)**
3. Create a Material with **Skybox/Panoramic** shader, assign the texture
4. Switch `RenderSettings.skybox` at each mode change
5. Call `DynamicGI.UpdateEnvironment()` after switching for proper reflection probes

---

## What to build

### Directory structure
```
Assets/_App/CinematographerJourney/
├── Models/daphne.glb
├── HDRI/*.jpg (6 files)
├── Data/*.json (2 files)
├── Materials/
│   ├── Skybox_Hero.mat
│   ├── Skybox_Intimate.mat
│   ├── Skybox_Epic.mat
│   ├── Skybox_Energy.mat
│   ├── Skybox_Solitude.mat
│   └── Skybox_Beauty.mat
├── CinematographerJourneyController.cs
├── CinematographerCameraDriver.cs
└── CinematographerModeManager.cs
```

And one editor setup script at `Assets/_App/Editor/CinematographerJourneySetup.cs`.

---

## Implementation

### 1. `CinematographerJourneyController.cs`

Implements `IJourney`. Mirrors the existing journey pattern (CosmicJourney / DroneJourney).

**OnEnter:**
1. Instantiate `daphne.glb` prefab at world origin, scale to ~1.7m tall
2. Set initial skybox to BEAUTY
3. Start `cosmic-hypnotic.mp3` playback (from `_Core/Audio/`)
4. Start `CinematographerCameraDriver` — begins playing the trajectory
5. Show mode label UI ("BEAUTY") in world-space text above the scene

**OnUpdate:**
- `CinematographerCameraDriver.Tick(deltaTime)` advances the trajectory playback
- `CinematographerModeManager.Tick(currentTime)` checks if a mode switch is due
- Optional: check for voice input (OVRPlugin speech-to-text or just use the pre-scripted timeline)

**OnExit:**
- Destroy Daphne instance
- Restore default skybox
- Stop music

### 2. `CinematographerCameraDriver.cs`

Drives the main camera (or a virtual camera the user can toggle to) along the trained trajectory.

```csharp
public class CinematographerCameraDriver : MonoBehaviour
{
    [Header("Trajectory")]
    public TextAsset trajectoryJson;
    
    private TrajectoryData trajectory;
    private float playbackTime = 0f;
    private bool isPlaying = true;
    
    // Two modes:
    // 1. "AI Camera" — user sees through the trained camera (main camera follows trajectory)
    // 2. "Free Look" — user looks freely, trained camera shown as a visible drone object
    public enum ViewMode { AICamera, FreeLook }
    public ViewMode currentViewMode = ViewMode.AICamera;
    
    void Start()
    {
        trajectory = JsonUtility.FromJson<TrajectoryData>(trajectoryJson.text);
        // Or use a custom parser since JsonUtility doesn't handle arrays well
    }
    
    public void Tick(float deltaTime)
    {
        if (!isPlaying) return;
        playbackTime += deltaTime;
        if (playbackTime >= 90f) playbackTime = 0f; // loop
        
        // Find the two surrounding frames and lerp
        float frameFloat = playbackTime * trajectory.fps;
        int f0 = Mathf.FloorToInt(frameFloat);
        int f1 = Mathf.Min(f0 + 1, trajectory.num_frames - 1);
        float t = frameFloat - f0;
        
        // Isaac Sim Z-up → Unity Y-up conversion
        Vector3 pos0 = IsaacToUnity(trajectory.frames[f0].drone_pos);
        Vector3 pos1 = IsaacToUnity(trajectory.frames[f1].drone_pos);
        Quaternion rot0 = IsaacQuatToUnity(trajectory.frames[f0].drone_quat);
        Quaternion rot1 = IsaacQuatToUnity(trajectory.frames[f1].drone_quat);
        
        Vector3 pos = Vector3.Lerp(pos0, pos1, t);
        Quaternion rot = Quaternion.Slerp(rot0, rot1, t);
        
        if (currentViewMode == ViewMode.AICamera)
        {
            Camera.main.transform.position = pos;
            Camera.main.transform.rotation = rot;
            // Make camera always look toward the dancer
            Vector3 dancerPos = IsaacToUnity(trajectory.frames[f0].dancer_pos);
            Camera.main.transform.LookAt(dancerPos);
        }
        else
        {
            // Move a visible "drone" object; user's head is free
            droneVisual.transform.position = pos;
            droneVisual.transform.rotation = rot;
        }
    }
    
    // Coordinate conversion helpers
    static Vector3 IsaacToUnity(float[] p)
    {
        // Isaac (x,y,z) Z-up → Unity (x,z,y) Y-up
        return new Vector3(p[0], p[2], p[1]);
    }
    
    static Quaternion IsaacQuatToUnity(float[] q)
    {
        // Isaac (qx,qy,qz,qw) Z-up RH → Unity (qx,qz,qy,-qw) Y-up LH
        return new Quaternion(q[0], q[2], q[1], -q[3]);
    }
    
    // Voice commands
    public void Pause() { isPlaying = false; }
    public void Resume() { isPlaying = true; }
}
```

**Important:** The trajectory has `dancer_pos` per frame. Use this as the LookAt target so the camera always frames the dancer, matching the trained behavior.

### 3. `CinematographerModeManager.cs`

Manages HDRI skybox switching based on the voice script timeline.

```csharp
public class CinematographerModeManager : MonoBehaviour
{
    [Header("Skybox Materials (assign in inspector)")]
    public Material skyboxHero;
    public Material skyboxIntimate;
    public Material skyboxEpic;
    public Material skyboxEnergy;
    public Material skyboxSolitude;
    public Material skyboxBeauty;
    
    [Header("Mode Label")]
    public TextMeshProUGUI modeLabelText;
    
    private Dictionary<string, Material> modeSkyboxes;
    private List<ModeCommand> commands;
    private int nextCommandIndex = 0;
    private string currentMode = "BEAUTY";
    
    void Start()
    {
        modeSkyboxes = new Dictionary<string, Material>
        {
            {"HERO", skyboxHero}, {"INTIMATE", skyboxIntimate},
            {"EPIC", skyboxEpic}, {"ENERGY", skyboxEnergy},
            {"SOLITUDE", skyboxSolitude}, {"BEAUTY", skyboxBeauty}
        };
        // Parse demo_script.json
        commands = ParseVoiceScript(voiceScriptJson.text);
    }
    
    public void Tick(float currentTime)
    {
        while (nextCommandIndex < commands.Count && 
               commands[nextCommandIndex].time <= currentTime)
        {
            var cmd = commands[nextCommandIndex];
            if (!string.IsNullOrEmpty(cmd.mode))
            {
                SwitchMode(cmd.mode);
            }
            nextCommandIndex++;
        }
    }
    
    void SwitchMode(string mode)
    {
        currentMode = mode;
        if (modeSkyboxes.TryGetValue(mode, out Material mat))
        {
            RenderSettings.skybox = mat;
            DynamicGI.UpdateEnvironment();
        }
        if (modeLabelText != null)
            modeLabelText.text = mode;
    }
}
```

### 4. Skybox crossfade (nice-to-have)

The Blender render uses a 1-second crossfade between HDRIs. To replicate in Unity:

```csharp
// Use a custom Skybox/Blend shader that mixes two cubemaps
// Shader "Skybox/CubemapBlend" with _Tex1, _Tex2, _Blend properties
// Lerp _Blend from 0→1 over 1 second via coroutine
IEnumerator CrossfadeSkybox(Material from, Material to, float duration = 1f)
{
    blendMaterial.SetTexture("_Tex1", from.GetTexture("_Tex"));
    blendMaterial.SetTexture("_Tex2", to.GetTexture("_Tex"));
    RenderSettings.skybox = blendMaterial;
    
    float t = 0;
    while (t < duration)
    {
        t += Time.deltaTime;
        blendMaterial.SetFloat("_Blend", t / duration);
        DynamicGI.UpdateEnvironment();
        yield return null;
    }
    RenderSettings.skybox = to;
    DynamicGI.UpdateEnvironment();
}
```

### 5. `CinematographerJourneySetup.cs` (Editor script)

Mirrors the existing journey setup pattern. Creates the prefab, wires references, adds to the journey menu.

**Critical safeguards** (from CLAUDE_FlowArtdance_VR.md §8):
- v46 menu-rebuild: verify menu entries after adding
- v62 orphan-cleanup: don't leave dangling prefab references
- Always create via the setup script, never manually

---

## User experience flow

1. User opens Gurulok → selects "Cinematographer Demo" from journey menu
2. Scene loads: Daphne standing center stage, BEAUTY skybox (fashion runway), cosmic-hypnotic music starts
3. **AI Camera mode (default):** user's view is driven by the trained camera — they experience cinematic swoops and orbits as if riding the drone
4. Mode switches happen automatically on the timeline: BEAUTY → HERO (t=8s) → INTIMATE (t=20s) → EPIC (t=30s) → ENERGY (t=40s) → SOLITUDE (t=55s) → BEAUTY (t=65s) → HERO (t=75s)
5. Each mode switch changes the skybox (with crossfade) — the entire environment transforms
6. At t=82s "Hold" pauses the camera; at t=85s "Resume" continues
7. At t=90s, loops back to start (or fades to black → journey menu)
8. **Optional: Free Look mode** — user taps a button to detach from the AI camera and look around freely while a visible drone object follows the trajectory

### Recording from VR

Quest's built-in screen recording (hold power + volume down, or use the Quick Settings panel) captures whatever the user sees. In AI Camera mode, this produces footage equivalent to the reference render but experienced from VR — ideal for demos and pitches.

For higher quality: use `scrcpy` from a connected PC, or SideQuest's screen mirror.

---

## Voice command integration (Phase 2 — optional for first build)

The demo_script.json timeline drives mode switches automatically. For **live voice control** (user speaks "hero" and the mode switches):

1. Use Meta's Voice SDK (`com.meta.xr.sdk.voice`) — already available in the Quest SDK
2. Create voice intents for the 6 mode names + "closer", "hold", "resume"
3. On voice trigger, call `CinematographerModeManager.SwitchMode(mode)` directly
4. Override the timeline — voice becomes live control instead of playback

This makes the demo interactive: user says "epic" and the stadium appears, "solitude" and they're in an empty theater. Extremely compelling for customer demos.

---

## Performance notes

- **Daphne GLB (14 MB):** ~75K verts, already trimmed (jacket/tongue/eye-occlusion removed, textures capped at 1024px). Should load fine on Quest 3.
- **HDRI skyboxes:** 8K equirectangular JPGs are large for Quest GPU. **Recommend downscaling to 4K (4096×2048) or even 2K on import** via Unity's texture import settings. The panoramic shader handles the rest.
- **Trajectory interpolation:** 4500 frames is trivial — just two Vector3 lerps and one Quaternion slerp per frame. Zero performance concern.
- **Skybox switching:** the crossfade is the expensive part (two cubemaps sampled simultaneously). If framerate drops, snap-switch instead of crossfade.

---

## Testing checklist

- [ ] Daphne GLB loads and appears at correct scale (~1.7m)
- [ ] All 6 HDRI skyboxes display correctly as panoramic environments
- [ ] Camera trajectory plays smoothly over 90 seconds
- [ ] Mode switches happen at correct times (match reference_render.mp4)
- [ ] Music syncs with the mode switches
- [ ] Quest screen recording captures the experience cleanly
- [ ] Free Look mode (if implemented) lets user detach and look around
- [ ] Journey exits cleanly (Daphne destroyed, skybox restored)
- [ ] No frame drops below 72fps on Quest 3

---

## Reference

Watch `reference_render.mp4` (18 MB, 90s) before building. This is the flat Blender render of exactly the same trajectory + mode switches + music. The VR version should match this experience, but immersive.

---

## What comes next (after v1 ships)

1. **Live voice commands** — real-time mode switching via Meta Voice SDK
2. **Daphne animation** — play back trained AMP dance policy (already have the pipeline from `mocap_handoff/bake_daphne_animation.py`)
3. **Multi-character** — add more performers, each with their own trajectory
4. **Live training feedback** — VR agent sends recording back to Mac agent for VLM evaluation, closing the training loop
5. **Customer demo mode** — polished UI with TrigunAI branding, mode labels, playback controls
