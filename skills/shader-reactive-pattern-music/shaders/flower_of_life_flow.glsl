#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// studio base values (Flower of Life panel)
const float uCircleRadius = 0.27;
const float uLineWidth    = 0.01;
const float uBassExpand   = 0.80;  // Bass -> Line Glow
const float uMidsRipple   = 0.60;
const float uHighsGlow    = 1.00;  // Highs -> Edge Glow
const float uBeatPulse    = 0.60;  // Beat -> Center Pulse
const float uSaturation   = 1.50;
const float uBrightness   = 1.05;
// blue -> violet -> pink palette
const vec3 uColA = vec3(0.55, 0.45, 0.60);
const vec3 uColB = vec3(0.45, 0.38, 0.52);
const vec3 uColC = vec3(1.00, 1.00, 1.00);
const vec3 uColD = vec3(0.55, 0.62, 0.78);

vec3 palette(float t){ return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a){ float c=cos(a), s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }

void main() {
  float uTime=u_time; vec2 uRes=u_resolution;
  float uSubBass=u_bass, uBass=u_bass, uMids=u_rms, uHighs=u_treble, uBeat=u_onset;
  float E = clamp(u_rms*1.2 + u_bass*0.5, 0.0, 1.2);

  // === DYNAMIC controls ===
  float uRings        = 2.0 + E*1.5;                              // more rings bloom at peaks (2 -> ~3.5)
  float uZoom         = 1.20 + 0.35*sin(uTime*0.012) + uBass*0.30; // slow zoom breathe + bass
  float uColorSpeed   = 0.08 + E*0.06;
  float uRotationSpeed= 0.0  + 0.010*sin(uTime*0.010);

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p = uv * uZoom;
  p = rot2D(p, uTime * uRotationSpeed);

  float radius = uCircleRadius;
  float lw = uLineWidth;

  float field = 0.0;
  field = max(field, smoothstep(lw, lw * 0.4, abs(length(p) - radius)));
  for (int ring = 1; ring <= 4; ring++) {
    if (float(ring) > uRings) break;
    float ringR = float(ring) * radius;
    for (int k = 0; k < 6; k++) {
      for (int j = 0; j < 4; j++) {
        if (j >= ring) break;
        float n = float(k) + float(j) / float(ring);
        float a = TAU * n / 6.0;
        vec2 c = vec2(cos(a), sin(a)) * ringR;
        float d = abs(length(p - c) - radius);
        field = max(field, smoothstep(lw, lw * 0.4, d));
      }
    }
  }

  float ripple = sin(length(p) * 14.0 - uTime * 2.5 - uMids * uMidsRipple * 8.0);
  float rippleFx = ripple * 0.5 + 0.5;
  float r = length(p);
  float halo = exp(-r * r * 1.2) * (0.3 + uSubBass * 0.5 + uBass * uBassExpand * 1.4 + uBeat * uBeatPulse * 0.6);
  float glow = uHighs * uHighsGlow * 0.4;
  field = field * (1.0 + uBass * uBassExpand * 0.5);
  float intensity = field * (1.2 + glow) + halo + field * rippleFx * 0.25;

  float colorT = uTime * uColorSpeed + r * 0.5 + field * 0.3;
  vec3 col = palette(colorT) * intensity;

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;
  col = col / (1.0 + col * 0.55); col *= 1.25;   // soft tone-map
  fragColor = vec4(col, 1.0);
}
