#version 330
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // mids / overall
uniform float u_bass;    // 20-300 Hz
uniform float u_treble;  // 2-8 kHz
uniform float u_onset;   // beat
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// ---------------- noise / fbm (earth surface texture) ----------------
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i + vec2(0,0)), hash(i + vec2(1,0)), u.x),
             mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++){ v += a * vnoise(p); p *= 2.02; a *= 0.5; }
  return v;
}

// ---------------- LOTUS (center — small, near, fixed, animating) ----------------
const float uPetals = 6.0;
const float uLayers = 5.0;
const float uZoom   = 3.4;            // higher zoom => smaller on screen
const float uBloom  = 0.5;
const float uRotationSpeed = 0.10;
const float uColorSpeed    = 0.30;
const float uBassBloom   = 1.2;
const float uMidsTwist   = 1.0;
const float uHighsSparkle= 1.0;
const float uBeatPulse   = 1.0;
const float uSaturation  = 1.15;
const float uBrightness  = 1.55;
const vec3 uColA = vec3(0.5);
const vec3 uColB = vec3(0.5);
const vec3 uColC = vec3(1.0);
const vec3 uColD = vec3(0.50, 0.20, 0.80);

vec3 palette(float t) { return uColA + uColB * cos(TAU * (uColC * t + uColD)); }

vec3 lotus(vec2 uv, float subBass, float bass, float mids, float highs, float beat) {
  vec2 p = uv * uZoom;
  float r = length(p);
  float ang = atan(p.y, p.x);
  float bloom = 0.6 + bass * uBassBloom * 1.2;
  ang += u_time * uRotationSpeed;

  float sumLayer = 0.0;
  for (int i = 0; i < 8; i++) {
    if (float(i) >= uLayers) break;
    float layerOffset = float(i) * 0.7;
    float layerScale  = 1.0 + float(i) * 0.45;
    float petalShape = cos(ang * uPetals + layerOffset + u_time * 0.3);
    petalShape = pow(max(petalShape, 0.0), 2.5);
    float radial = exp(-pow(r * layerScale - bloom * (0.6 + float(i) * 0.25), 2.0) * (8.0 - uBloom * 4.0));
    sumLayer += petalShape * radial * pow(0.78, float(i));
  }
  float halo = exp(-r * r * 1.5) * (0.4 + subBass * 0.6);
  float sparkle = sin(ang * 96.0 + u_time * 5.0) * sin(r * 80.0 - u_time * 3.0);
  sparkle = sparkle * sparkle * highs * uHighsSparkle * 0.5;

  float intensity = sumLayer * 1.4 + halo + sparkle;
  intensity += beat * uBeatPulse * exp(-r * r * 6.0) * 0.7;

  float colorT = u_time * uColorSpeed * (1.0 + mids * uMidsTwist * 0.5) + r * 0.6 + intensity * 0.25;
  vec3 col = palette(colorT) * intensity;
  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;
  return col;
}

// ---------------- EARTH TUNNEL + MULTICOLOR GATES ----------------
// Perspective tunnel (depth = K/r). Walls are a real earth/rock surface (fbm),
// scrolling toward the viewer. Bright neon gate-rings at intervals, each a
// different color. No reflection.
vec3 tunnel(vec2 uv, float bass, float treble) {
  float r   = length(uv) + 0.0020;
  float ang = atan(uv.y, uv.x);
  float depth = 0.34 / r;                 // perspective depth (big near center)
  float flow  = u_time * 0.30;            // walls scroll forward

  // ---- earth/rock wall (fills the frame — no black) ----
  // sample on cos/sin so the texture wraps seamlessly around the tunnel (no atan seam)
  float seg = depth * 1.4 + flow;                  // scroll along the tunnel
  vec2 cc = vec2(cos(ang), sin(ang)) * 1.8;
  float n  = fbm(cc * 1.6 + vec2(seg, seg * 0.6));
  float n2 = fbm(cc * 4.5 + vec2(seg * 1.3, -seg) + 13.0);
  vec3 rock = mix(vec3(0.06, 0.045, 0.035), vec3(0.34, 0.24, 0.16), n);  // dark crevice -> dirt
  rock = mix(rock, vec3(0.45, 0.33, 0.22), n2 * 0.45);                    // lighter grit
  rock += vec3(0.05, 0.03, 0.015) * pow(n2, 3.0);                         // sparse highlights
  // depth lighting: near (edges) lit, far (center) dim — but never pure black
  float lite = clamp(0.30 + 0.85 * exp(-depth * 0.22), 0.16, 1.10);
  vec3 wall = rock * lite * (0.9 + bass * 0.25);

  // ---- multicolor neon gates ----
  float phase  = depth * 2.1 + u_time * 0.42;
  float gateId = floor(phase);
  float s      = 0.5 + 0.5 * sin(phase * TAU);
  float core   = pow(s, 8.0);
  float guard  = smoothstep(0.05, 0.16, r);            // kill aliasing at dead center
  // each gate a distinct hue (golden-ratio spacing)
  float hue  = fract(gateId * 0.1397 + 0.07);
  vec3  gcol = 0.55 + 0.45 * cos(TAU * (hue + vec3(0.0, 0.33, 0.67)));
  float energy = 0.85 + bass * 0.9;
  vec3 gate = gcol * core * guard * energy * 1.7;
  gate += gcol * core * guard * treble * 0.5;          // treble shimmer

  return wall + gate;
}

void main() {
  vec2 res = u_resolution;
  vec2 uv = (gl_FragCoord.xy - 0.5 * res) / res.y;   // aspect-correct, center origin

  float bass   = u_bass;
  float treble = u_treble;
  float mids   = u_rms;
  float beat   = clamp(u_onset + u_bass * 0.25, 0.0, 1.0);

  // earth tunnel fills the whole frame (no reflection, no black background)
  vec3 col = tunnel(uv, bass, treble);

  // lotus — small, near, fixed at center, animating in place
  vec3 lo = lotus(uv, bass, bass, mids, treble, beat);
  float lm = smoothstep(0.26, 0.015, length(uv));    // small central mask
  lo *= lm;
  col = 1.0 - (1.0 - clamp(col, 0.0, 1.0)) * (1.0 - clamp(lo, 0.0, 1.0));  // screen blend on top

  // light corner vignette only
  float vig = smoothstep(1.55, 0.85, length(uv));
  col *= 0.88 + 0.12 * vig;

  col *= 1.0 + beat * 0.06;
  fragColor = vec4(col, 1.0);
}
