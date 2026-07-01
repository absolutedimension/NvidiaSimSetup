#version 330
precision highp float;

// ---- pipeline contract: the ONLY 6 bound uniforms ----
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // overall / mids
uniform float u_bass;    // 20-300 Hz
uniform float u_treble;  // 2-8 kHz
uniform float u_onset;   // beat (0/1)
out vec4 fragColor;

// ---- baked tuning params (tuned for dark neon driving techno; edit to taste) ----
const float uViscosity     = 1.0;
const float uTurbulence    = 0.6;
const float uZoom          = 2.5;
const float uFlowSpeed     = 0.30;
const float uRotationSpeed = 0.05;
const float uColorSpeed    = 0.08;
const float uBassRipple    = 1.2;
const float uMidsWarp      = 1.2;
const float uHighsShimmer  = 1.0;
const float uBeatSplash    = 1.3;
const float uSaturation    = 1.15;
const float uBrightness    = 1.0;

// ---- cosine palette (dark neon: electric blue / magenta / violet, green killed) ----
const vec3 uColA = vec3(0.30, 0.08, 0.45);
const vec3 uColB = vec3(0.40, 0.10, 0.45);
const vec3 uColC = vec3(1.0, 1.0, 1.0);
const vec3 uColD = vec3(0.00, 0.25, 0.35);

#define PI  3.1415926
#define TAU 6.2831853

vec3 palette(float t) {
  return uColA + uColB * cos(TAU * (uColC * t + uColD));
}

vec2 rot2D(vec2 p, float a) {
  float c = cos(a), s = sin(a);
  return vec2(c*p.x - s*p.y, s*p.x + c*p.y);
}

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  float a = hash(i),
        b = hash(i + vec2(1.0, 0.0)),
        c = hash(i + vec2(0.0, 1.0)),
        d = hash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0, amp = 0.5;
  for (int i = 0; i < 5; i++) { v += amp * noise(p); p = p * 2.04 + vec2(1.7, -3.1); amp *= 0.55; }
  return v;
}

void main() {
  // ---- map bound audio uniforms onto the shader's original audio names ----
  float uTime    = u_time;
  vec2  uRes     = u_resolution;
  float uSubBass = u_bass;
  float uBass    = u_bass;
  float uMids    = u_rms;
  float uHighs   = u_treble;
  float uBeat    = u_onset;

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p = uv * uZoom;
  p = rot2D(p, uTime * uRotationSpeed);

  float t = uTime * uFlowSpeed;
  float warp = 1.5 + uMids * uMidsWarp;

  vec2 q = p + vec2(fbm(p * (1.0 + uTurbulence) + t),
                    fbm(p * (1.0 + uTurbulence) - t * 0.7));
  vec2 r = p + warp * (q + vec2(fbm(q + t * 1.3), fbm(q - t * 0.9)));

  float ripple = sin(length(p) * 18.0 - t * 4.0 - uBass * uBassRipple * 6.0);
  ripple = ripple * 0.5 + 0.5;

  float fluid = fbm(r * (1.0 + uViscosity * 0.4));
  float metal = pow(fluid, 2.0 + uViscosity);

  float shimmer = fbm(r * 12.0 + t * 2.0) * uHighs * uHighsShimmer;
  float splash = uBeat * uBeatSplash * exp(-length(p) * 1.6) * 1.2;

  float intensity = metal + ripple * 0.15 + shimmer * 0.3 + splash;
  intensity = clamp(intensity, 0.0, 2.5);

  float colorT = uTime * uColorSpeed + fluid * 0.8 + uSubBass * 0.4;
  vec3 col = palette(colorT) * (0.18 + intensity * 1.5);

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;

  fragColor = vec4(col, 1.0);
}
