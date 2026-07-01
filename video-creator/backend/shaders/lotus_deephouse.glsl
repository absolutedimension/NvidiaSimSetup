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

// ---- baked tuning params (tuned for calm rich deep-house lotus; edit to taste) ----
const float uPetals        = 8.0;
const float uLayers        = 6.0;
const float uZoom          = 2.2;
const float uBloom         = 0.5;
const float uRotationSpeed = 0.06;
const float uColorSpeed    = 0.05;
const float uBassBloom     = 1.0;
const float uMidsTwist     = 1.0;
const float uHighsSparkle  = 0.45;
const float uBeatPulse     = 1.0;
const float uSaturation    = 1.05;
const float uBrightness    = 1.0;

// ---- cosine palette (calm jewel: violet / blue / teal, slow meditative cycle) ----
const vec3 uColA = vec3(0.50, 0.45, 0.55);
const vec3 uColB = vec3(0.45, 0.25, 0.45);
const vec3 uColC = vec3(1.0, 1.0, 1.0);
const vec3 uColD = vec3(0.00, 0.20, 0.55);

#define PI  3.1415926
#define TAU 6.2831853

vec3 palette(float t) {
  return uColA + uColB * cos(TAU * (uColC * t + uColD));
}

vec2 rot2D(vec2 p, float a) {
  float c = cos(a), s = sin(a);
  return vec2(c*p.x - s*p.y, s*p.x + c*p.y);
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
  float r = length(p);
  float ang = atan(p.y, p.x);

  // VR-stable: bass drives bloom (a local radial effect — petals brighten/expand from
  // their drawn positions). Mids drive color cycle speed (in colorT below), not rotation.
  float bloom = 0.6 + uBass * uBassBloom * 1.2;
  ang += uTime * uRotationSpeed;

  float sumLayer = 0.0;
  for (int i = 0; i < 8; i++) {
    if (float(i) >= uLayers) break;
    float layerOffset = float(i) * 0.7;
    float layerScale = 1.0 + float(i) * 0.45;
    float petalShape = cos(ang * uPetals + layerOffset + uTime * 0.3);
    petalShape = pow(max(petalShape, 0.0), 2.5);
    float radial = exp(-pow(r * layerScale - bloom * (0.6 + float(i) * 0.25), 2.0) * (8.0 - uBloom * 4.0));
    sumLayer += petalShape * radial * pow(0.78, float(i));
  }

  float halo = exp(-r * r * 1.5) * (0.4 + uSubBass * 0.6);
  float sparkle = sin(ang * 96.0 + uTime * 5.0) * sin(r * 80.0 - uTime * 3.0);
  sparkle = sparkle * sparkle * uHighs * uHighsSparkle * 0.5;

  float intensity = sumLayer * 1.4 + halo + sparkle;
  // Beat adds a CENTRAL pulse only (halo region), not whole-image flash
  intensity += uBeat * uBeatPulse * exp(-r * r * 6.0) * 0.7;

  // Mids drive color cycle speed (smooth color flow without geometry motion)
  float colorT = uTime * uColorSpeed * (1.0 + uMids * uMidsTwist * 0.5) + r * 0.6 + intensity * 0.25;
  vec3 col = palette(colorT) * intensity;

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;

  fragColor = vec4(col, 1.0);
}
