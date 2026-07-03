#version 330
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // mids/overall  (energy proxy: low in intro/breakdown, high at peak)
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// ---- studio base values (from the Shader Studio panel) ----
const float Z_RIPPLE = 3.10;   // ripple speed
const float Z_ZOOM   = 4.00;   // zoom
const float Z_HARM   = 0.59;   // harmonic density
const float uDamping = 0.75;
const float Z_ROT    = 0.00;   // rotation (kept 0 — VR-unstable)
const float Z_COL    = 0.06;   // color cycle
const float uFluxRipple  = 0.23;
const float uOnsetSpawn  = 1.74;
const float uSilenceFade = 0.27;
const float uSaturation  = 1.40;
const float uBrightness  = 1.00;
const vec3 uColA = vec3(0.5, 0.5, 0.5);
const vec3 uColB = vec3(0.5, 0.5, 0.5);
const vec3 uColC = vec3(1.0, 1.0, 1.0);
const vec3 uColD = vec3(0.00, 0.10, 0.22);

vec3 palette(float t) { return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a) { float c=cos(a), s=sin(a); return vec2(c*p.x - s*p.y, s*p.x + c*p.y); }

void main() {
  float uTime=u_time; vec2 uRes=u_resolution;
  float uSubBass=u_bass, uBass=u_bass, uMids=u_rms, uHighs=u_treble;
  float uRMS=u_rms, uCentroid=u_treble, uFlatness=u_treble*0.5;
  float uFlux=u_onset, uOnset=u_onset, uSilence=clamp(1.0-u_rms*2.0,0.0,1.0);
  float E = clamp(u_rms*1.2 + u_bass*0.5, 0.0, 1.2);   // overall energy (drives the dynamics)

  // ===== DYNAMIC CONTROLS — animate the studio values over the track =====
  // slow LFOs (a few cycles across the whole track) + energy so the look evolves with the music.
  float lfo1 = sin(uTime * 0.010);             // ~10 min period
  float lfo2 = sin(uTime * 0.023 + 1.7);
  float uZoom        = Z_ZOOM + 1.8*lfo1 + uBass*1.2;          // zoom breathes slowly + pulses on bass
  float uRippleSpeed = Z_RIPPLE * (0.5 + E*0.9) + 0.4*lfo2;    // ripples speed up at peaks, slow in breakdowns
  float uHarmonics   = Z_HARM + E*1.1;                          // more overtones at peak
  float uColorSpeed  = Z_COL + E*0.10;                          // colors flow faster with energy
  float uRotationSpeed = Z_ROT + 0.012*lfo1;                    // very slight slow drift (near 0)

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p = uv * uZoom;
  p = rot2D(p, uTime * uRotationSpeed);
  float r = length(p);

  // 8 mel-ish bands spread low->high from the 4 available
  float uBands[8];
  uBands[0]=u_bass; uBands[1]=u_bass*0.85; uBands[2]=mix(u_bass,u_rms,0.5);
  uBands[3]=u_rms;  uBands[4]=u_rms*0.9;   uBands[5]=mix(u_rms,u_treble,0.5);
  uBands[6]=u_treble; uBands[7]=u_treble*0.8;

  float wave = 0.0;
  float t = uTime * uRippleSpeed;
  for (int i = 0; i < 8; i++) {
    float fi = float(i);
    float spatialFreq = 4.0 + fi * (3.0 + uHarmonics * 0.6);
    float phaseSpeed = 0.6 + fi * 0.35;
    float amp = uBands[i] * pow(uDamping, fi);
    wave += amp * sin(r * spatialFreq - t * phaseSpeed - uFlux * uFluxRipple * 4.0);
  }

  float onsetRipple = uOnset * uOnsetSpawn * exp(-pow(r * 2.0 - 0.4, 2.0) * 6.0);
  float gradient = mix(1.0 - r, smoothstep(0.0, 1.4, r), uCentroid);
  float ambient = (1.0 - uSilenceFade * uSilence) * (0.18 + uRMS * 0.5);

  float intensity = wave * 1.4 + onsetRipple * 1.2 + gradient * ambient + 0.12;
  intensity += exp(-r * r * 9.0) * (0.4 + uSubBass * 0.7);

  float colorT = uTime * uColorSpeed + r * 0.4 + uCentroid * 0.5;
  vec3 col = palette(colorT) * intensity;

  float grain = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  col += (grain - 0.5) * uFlatness * 0.10;

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;

  // soft tone-map so peaks roll off instead of clipping to white
  col = col / (1.0 + col * 0.55);
  col *= 1.25;

  fragColor = vec4(col, 1.0);
}
