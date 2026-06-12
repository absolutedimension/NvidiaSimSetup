# Advanced Video Layers — Shader Effects + Environment Skybox

> Two new layers that make every frame ALIVE. Nothing is static.
> Fits into the Video Creator pipeline as Step 3.5 (between Visuals and Music).

---

## THE CORE IDEA

Current video pipeline produces slides with text + particles. It's decent but still
feels like a slideshow. These two layers transform it into a **living, breathing visual
experience** — like the viewer is INSIDE an environment, not watching a PowerPoint.

```
CURRENT PIPELINE:
  Script → Voice → [Slides] → Music → Render
                      ↑
                   Static-ish (particles help but still flat)

NEW PIPELINE:
  Script → Voice → [Slides] → [SHADER FX] → [SKYBOX ENV] → Music → Render
                                    ↑              ↑
                              Audio-reactive    3D environment
                              visual effects    wrapping the content
                              (alive, pulsing)  (classroom, stage, cosmos)
```

---

## LAYER 1: SHADER EFFECTS (Audio-Reactive Visual Energy)

### What it is:
GLSL fragment shaders rendered on GPU that create animated visual effects
BEHIND and AROUND the content. Effects react to the voice audio — when the
speaker talks, the visuals pulse. When there's a pause, they settle.

### Effect Templates (user picks one per scene):

| Template | Look | When to use | Shader type |
|---|---|---|---|
| **Calm Glow** | Soft pulsing light orbs, gentle color waves | Teaching, explanation, calm scenes | Perlin noise + sine waves |
| **Energy Pulse** | Sharp light bursts synced to speech | Reveals, exciting moments, CTAs | Audio FFT → brightness |
| **Matrix Flow** | Flowing lines/particles moving upward | Code/tech topics, AI coding | Particle field + velocity |
| **Cosmic Drift** | Stars, nebula, slow rotation | Inspirational, vision, big-picture | Fractal noise + rotation |
| **Neon Grid** | Retro-futuristic grid with glow | Gaming, VR, tech-forward | Grid lines + bloom |
| **Warm Bokeh** | Out-of-focus light circles, warm tones | Personal stories, credibility | Circle SDF + blur |
| **Liquid Glass** | Smooth, refractive color shifts | Premium feel, transitions | Voronoi + color gradient |
| **Classroom Board** | Subtle chalk dust, warm wood texture | Traditional teaching moments | Noise + warm palette |
| **Fire Particles** | Rising embers, warm glow | Energy, passion, motivation | Particle system + heat |
| **Ocean Waves** | Gentle wave motion, blue depths | Meditation, VR wellness topics | Wave function + fog |

### Audio-Reactivity:
The shader receives audio analysis data per frame:
- **RMS (volume)** → controls overall brightness/scale
- **FFT bass** → controls low-frequency effects (pulses, waves)
- **FFT treble** → controls high-frequency effects (sparkles, sharpness)
- **Onset detection** → triggers flash effects on speech syllables
- **Silence detection** → effects settle/dim during pauses

```python
# Per frame, audio analysis feeds into shader uniforms:
uniform float u_rms;       # 0.0-1.0, current volume
uniform float u_bass;      # 0.0-1.0, low frequency energy
uniform float u_treble;    # 0.0-1.0, high frequency energy  
uniform float u_onset;     # 0.0 or 1.0, speech onset detected
uniform float u_time;      # seconds elapsed
uniform vec2  u_resolution; # 1920x1080
```

### Technical Implementation:

```
ModernGL (Python) — headless GPU rendering
  ├── Load GLSL fragment shader from template library
  ├── Analyze audio frame-by-frame (librosa FFT)
  ├── Pass audio uniforms to shader each frame
  ├── Render 1920x1080 frame on GPU (~0.5ms per frame)
  ├── Pipe raw pixels to ffmpeg
  └── Output: shader_bg.mp4 (just the animated background)

Then composite:
  ffmpeg -i shader_bg.mp4 -i slides.mp4 -filter_complex "overlay" → combined.mp4
```

**Performance:** ModernGL renders at ~2000fps on A10G for simple shaders.
A 3-minute video at 30fps = 5,400 frames = ~3 seconds of GPU time.
This is essentially FREE compared to voice/avatar generation.

---

## LAYER 2: SKYBOX ENVIRONMENT (3D Space Around Content)

### What it is:
A 360° environment image (HDRI/equirectangular) projected as a virtual room
around the content. The "camera" slowly moves within this environment,
creating parallax and depth — the viewer feels INSIDE a space, not looking
at a flat screen.

### Environment Templates:

| Template | Look | When to use |
|---|---|---|
| **Modern Classroom** | Clean room, whiteboard, warm lighting | Core teaching, tutorials |
| **Tech Lab** | Dark room, blue/purple monitors, neon accents | Coding, AI, tech topics |
| **Cozy Studio** | Bookshelf, desk lamp, warm wood | Personal, storytelling |
| **Concert Stage** | Arena, spotlights, dramatic | Hype, reveals, CTAs |
| **Meditation Room** | Zen garden, soft light, plants | Wellness, VR meditation |
| **Cosmic Space** | Stars, galaxies, nebulae | Vision, big-picture, inspiration |
| **Minimalist White** | Clean infinite white with soft shadows | Apple-keynote style |
| **Library** | Books, columns, scholarly | Academic, math, theory |
| **Workshop Garage** | Tools, workbench, industrial | Building, hands-on, robotics |
| **Futuristic HQ** | Sci-fi control room, holograms | Gaming, VR, metaverse |

### How it works:

```
1. User picks an environment template (or uploads custom HDRI)
2. System projects the HDRI as a spherical background
3. A virtual camera slowly orbits/pans within the space
4. Content (slides, text) floats INSIDE this 3D space
5. Parallax effect: background moves slower than foreground
6. Result: feels like you're IN a room watching a presentation
```

### Technical Implementation:

**Option A: Blender headless (highest quality)**
```
Blender Python script:
  1. Create a sphere with HDRI material (the environment)
  2. Create a plane in front of camera (the slide content)
  3. Animate camera: slow orbit, subtle zoom breathe
  4. Render each frame with EEVEE (fast) or Cycles (beautiful)
  5. Output: environment_bg.mp4
```

**Option B: ModernGL shader (faster, simpler)**
```
GLSL shader:
  1. Sample equirectangular HDRI texture
  2. Apply camera rotation matrix (slow orbit)
  3. Composite slide content as a floating plane
  4. Add depth of field blur on background
  5. Render frame-by-frame → pipe to ffmpeg
```

**Option C: Three.js pre-render (web-based)**
```
Headless Three.js (Puppeteer):
  1. Load HDRI as scene background
  2. Place slide as a 3D plane
  3. Animate camera orbit
  4. Capture screenshots → ffmpeg
```

**Recommendation: Option B (ModernGL)** for consistency with shader layer.
Both layers use the same rendering engine.

### Source for HDRIs:
- **Blockade Labs** — AI-generated 360° HDRIs (we already have 6)
- **Poly Haven** — free CC0 HDRIs (real photography)
- **Stable Diffusion panorama** — generate custom environments
- **User upload** — custom classroom/studio photos

---

## HOW BOTH LAYERS COMPOSE

```
FINAL FRAME COMPOSITION (back to front):

┌──────────────────────────────────────────┐
│                                          │
│  Layer 0: SKYBOX ENVIRONMENT             │  ← 3D room / space / classroom
│  (360° HDRI with camera orbit)           │     slowly rotating, parallax
│                                          │
│  ┌──────────────────────────────────┐    │
│  │                                  │    │
│  │  Layer 1: SHADER EFFECTS         │    │  ← audio-reactive glow, particles
│  │  (GLSL animated background)      │    │     pulsing with speech
│  │                                  │    │
│  │  ┌──────────────────────────┐    │    │
│  │  │                          │    │    │
│  │  │  Layer 2: SLIDE CONTENT  │    │    │  ← text, diagrams, code
│  │  │  (title, body, bullets)  │    │    │     appearing with animation
│  │  │                          │    │    │
│  │  └──────────────────────────┘    │    │
│  │                                  │    │
│  │  ┌────────┐                      │    │
│  │  │Presenter│ Layer 3: AVATAR     │    │  ← circular photo or lip-sync
│  │  │  (PiP)  │ (corner overlay)    │    │     (future: Hallo2 when ready)
│  │  └────────┘                      │    │
│  │                                  │    │
│  └──────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘

+ Audio track: F5-TTS voice + background music (mixed)
```

### Example: "AI Coding Reveal" scene

```
Skybox:   Tech Lab (dark room, blue monitors, neon)
Shader:   Energy Pulse — bursts of light when speaker says "AI" or "code"
Slide:    "NO MANUAL CODING" text, glowing
Avatar:   Presenter photo in bottom-right corner
Voice:    female_excited tone, F5-TTS
Music:    Energetic tech ambient, 8% volume

Result:   Viewer feels like they're in a tech lab, energy pulses
          with the speaker's voice, the text glows and appears
          with animation, everything is ALIVE.
```

### Example: "Module 9 — Mixed Reality" scene

```
Skybox:   Cosmic Space (stars, nebulae, deep purple)
Shader:   Cosmic Drift — slow star rotation, nebula swirl
Slide:    "Mixed Reality & Passthrough" with purple glow
Avatar:   Presenter, slightly larger (important moment)
Voice:    female_excited — this is THE highlight
Music:    Emotional piano swell, 10% volume

Result:   Viewer feels like floating in space while learning
          about MR. The cosmic environment amplifies the
          "this changes everything" feeling.
```

---

## UPDATED VIDEO CREATOR UI — STEP 3: VISUAL BUILDER (ADVANCED)

```
┌─────────────────────────────────────────────────────┐
│  Step 3: Visual Builder                             │
│                                                     │
│  ┌─── Basic ───┐  ┌─── Advanced ───┐               │
│  │ Slide Title  │  │                │               │
│  │ Body Text    │  │ 🌊 SHADER FX   │  ← NEW       │
│  │ Accent Color │  │ Pick template: │               │
│  │ Layout       │  │ [Energy Pulse▾]│               │
│  │              │  │ Reactivity: 🔊 │               │
│  │              │  │ [███████░░] 70% │               │
│  │              │  │                │               │
│  │              │  │ 🏠 ENVIRONMENT  │  ← NEW       │
│  │              │  │ Pick skybox:   │               │
│  │              │  │ [Tech Lab   ▾] │               │
│  │              │  │ Camera speed:  │               │
│  │              │  │ [███░░░░░] 30% │               │
│  │              │  │                │               │
│  └──────────────┘  └────────────────┘               │
│                                                     │
│  [👁️ Live Preview]  — shows all layers composited    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## RENDER PIPELINE (UPDATED)

```
For each scene:
  1. Analyze voice audio → extract RMS, FFT, onsets per frame
  2. Render SKYBOX layer → environment_bg.mp4 (ModernGL, ~3s)
  3. Render SHADER layer → shader_fx.mp4 (ModernGL + audio data, ~3s)
  4. Render SLIDE layer → slide frames (Pillow, ~2s)
  5. Composite all layers → scene.mp4 (ffmpeg filter_complex, ~5s)
  6. Add voice audio → scene_with_voice.mp4

Then:
  7. Concat all scenes → full_video_no_music.mp4
  8. Mix background music → final.mp4
```

**Total render time for a 3-min video:**
- Audio analysis: ~1s
- Skybox renders: ~3s per scene × 7 scenes = 21s
- Shader renders: ~3s per scene × 7 scenes = 21s
- Slide renders: ~2s per scene × 7 scenes = 14s
- Compositing: ~5s per scene × 7 scenes = 35s
- Concat + music: ~10s
- **Total: ~100 seconds** for a full video with all 4 layers

---

## BUILD PLAN

| Day | Task |
|---|---|
| 1 | Build shader template library (10 GLSL shaders) + ModernGL renderer |
| 2 | Build audio analyzer (librosa FFT per frame) + wire to shader uniforms |
| 3 | Build skybox renderer (HDRI projection + camera orbit) |
| 4 | Build compositor (ffmpeg multi-layer assembly) |
| 5 | Add to Video Creator UI (Advanced panel in Visual Builder) |

---

## SHADER CODE EXAMPLE — "Energy Pulse"

```glsl
#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;      // voice volume 0-1
uniform float u_bass;     // bass energy 0-1
uniform float u_onset;    // speech onset 0 or 1

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec2 center = vec2(0.5);
    float dist = length(uv - center);
    
    // Base glow — always present, gentle
    float glow = 0.02 / (dist + 0.1);
    
    // Audio-reactive pulse — expands with voice volume
    float pulse = u_rms * 0.15 / (abs(dist - 0.3 - u_bass * 0.2) + 0.01);
    
    // Onset flash — bright burst on speech start
    float flash = u_onset * 0.3 * exp(-dist * 3.0);
    
    // Color: blue base, shifts to purple with bass
    vec3 color = mix(
        vec3(0.1, 0.3, 0.9),   // blue
        vec3(0.6, 0.2, 0.9),   // purple
        u_bass
    );
    
    // Time-based rotation
    float angle = u_time * 0.3;
    vec2 rotUV = vec2(
        (uv.x - 0.5) * cos(angle) - (uv.y - 0.5) * sin(angle),
        (uv.x - 0.5) * sin(angle) + (uv.y - 0.5) * cos(angle)
    );
    
    // Noise-like variation
    float noise = sin(rotUV.x * 20.0 + u_time) * sin(rotUV.y * 15.0 + u_time * 0.7);
    noise = noise * 0.5 + 0.5;
    
    float brightness = glow + pulse + flash + noise * 0.02;
    vec3 finalColor = color * brightness;
    
    fragColor = vec4(finalColor, 1.0);
}
```

This shader creates a pulsing blue/purple glow that:
- Gently breathes at all times (never static)
- Expands when the speaker's voice gets louder
- Flashes bright white when a new word starts
- Shifts from blue to purple based on bass energy
- Slowly rotates with subtle noise patterns

The result: **the background is ALIVE** and responds to speech.
