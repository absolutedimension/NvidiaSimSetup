#version 330
precision highp float;

// pipeline-bound uniforms (shader_service binds only these)
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;
out vec4 fragColor;

#define PI       3.1415926
#define TAU      6.2831853
#define MAX_PARTICLES 16

// ---- tuning params (baked constants; tweak here) ----
const float uCenterRadius = 0.07;
const float uHaloFalloff  = 3.5;
const float uRotationSpeed= 0.06;
const float uColorSpeed   = 0.12;
const float uBreathPeriod = 9.0;
const float uInhaleFraction = 0.34;
const float uHoldFraction   = 0.14;
const float uExhaleFraction = 0.40;
const float uInhaleSize = 0.05;
const float uExhaleSize = 0.055;
const float uTailLength = 3.2;
const float uInhaleSpeed = 0.22;
const float uExhaleSpeed = 0.28;
const float uRMSPulse    = 1.1;
const float uMidsCenter  = 1.0;
const float uOnsetSparkle= 1.2;
const float uCentroidHalo= 0.8;
const float uSilenceBreath = 0.8;
const float uParticleAlpha = 0.95;
const float uSaturation  = 1.25;
const float uBrightness  = 1.35;
// palette / tint colors (dual-use, as in the source shader)
const vec3 uColA = vec3(1.00, 0.62, 0.20);  // warm gold  (exhale)
const vec3 uColB = vec3(0.55, 0.30, 0.85);  // purple amp
const vec3 uColC = vec3(0.20, 0.80, 1.00);  // cool cyan  (inhale)
const vec3 uColD = vec3(0.10, 0.20, 0.40);

vec3 palette(float t) { return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a) { float c=cos(a), s=sin(a); return vec2(c*p.x - s*p.y, s*p.x + c*p.y); }
float hash11(float n) { return fract(sin(n * 78.233) * 43758.5453); }
float hash21(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

float cometShape(vec2 p, vec2 pos, vec2 velDir, float ps, float tailMul) {
  vec2 toP = p - pos;
  float headD = length(toP);
  if (headD > ps * (1.0 + tailMul)) return 0.0;
  float head = exp(-headD * headD / (ps * ps * 0.32));
  vec2 perpDir = vec2(-velDir.y, velDir.x);
  float along = dot(toP, velDir);
  float perp  = abs(dot(toP, perpDir));
  float tailLen = ps * tailMul;
  float tail = 0.0;
  if (along < ps * 0.4 && along > -tailLen) {
    float alongNorm = clamp((-along) / tailLen, 0.0, 1.0);
    float tailWidth = ps * (1.0 - alongNorm * 0.7);
    float perpFade  = 1.0 - smoothstep(0.0, tailWidth, perp);
    float alongFade = pow(1.0 - alongNorm, 1.6);
    tail = perpFade * alongFade;
  }
  return head * 1.6 + tail * 0.85;
}

void main() {
  // map pipeline audio (4 bands) -> the source shader's expected fields
  float uTime    = u_time;
  vec2  uRes     = u_resolution;
  float uSubBass = u_bass;
  float uBass    = u_bass;
  float uMids    = u_rms;
  float uHighs   = u_treble;
  float uBeat    = u_onset;
  float uRMS     = u_rms;
  float uCentroid= u_treble;                       // brightness proxy
  float uFlatness= u_treble * 0.5;
  float uOnset   = u_onset;
  float uSilence = clamp(1.0 - u_rms * 2.0, 0.0, 1.0);

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p  = rot2D(uv, uTime * uRotationSpeed);
  float r = length(p);

  float cycleT = mod(uTime, uBreathPeriod) / uBreathPeriod;
  float inhaleEnd = uInhaleFraction;
  float holdEnd   = inhaleEnd + uHoldFraction;
  float exhaleEnd = holdEnd   + uExhaleFraction;
  float inhaleVis = smoothstep(0.00, 0.05, cycleT) * (1.0 - smoothstep(inhaleEnd - 0.03, inhaleEnd + 0.02, cycleT));
  float holdVis   = smoothstep(inhaleEnd - 0.02, inhaleEnd + 0.03, cycleT) * (1.0 - smoothstep(holdEnd - 0.02, holdEnd + 0.03, cycleT));
  float exhaleVis = smoothstep(holdEnd - 0.02, holdEnd + 0.05, cycleT) * (1.0 - smoothstep(exhaleEnd - 0.04, exhaleEnd + 0.01, cycleT));
  float holdGlow = holdVis * (1.0 - abs(((cycleT - inhaleEnd) / max(0.0001, uHoldFraction)) - 0.5) * 2.0);
  holdGlow = max(0.0, holdGlow);
  float colorPhase = smoothstep(holdEnd - 0.05, holdEnd + 0.05, cycleT);

  float centerR = uCenterRadius;
  float centerCore = exp(-(r * r) / (centerR * centerR * (1.0 + holdGlow * 1.4)));
  float haloRad   = centerR * uHaloFalloff * (1.0 + uCentroidHalo * uCentroid * 0.8);
  float centerHalo = exp(-(r * r) / (haloRad * haloRad * 0.30)) * (0.25 + holdGlow * 0.65 + uMids * uMidsCenter * 0.5 + uRMS * uRMSPulse * 0.4);

  float ringField = 0.0;
  for (int i = 0; i < 4; i++) {
    float fi = float(i);
    float ringR = centerR + (fi + 1.0) * centerR * 1.4;
    float ringW = centerR * 0.04;
    float ring  = smoothstep(ringW, 0.0, abs(r - ringR));
    ring *= holdGlow * (1.0 - fi * 0.18);
    ringField += ring;
  }

  float silentBreath = (sin(uTime * 0.6) * 0.5 + 0.5) * uSilence * uSilenceBreath;
  centerHalo += silentBreath * 0.3 * exp(-(r * r) / (haloRad * haloRad * 0.6));

  vec3 coolTint = mix(uColC, uColB, 0.55);
  vec3 warmTint = uColA;
  vec3 centerCol = mix(coolTint, warmTint, colorPhase);
  vec3 paletteCol = palette(r * 0.5 + uTime * uColorSpeed);
  centerCol = mix(centerCol, paletteCol, 0.15);

  vec3 col = centerCol * (centerCore * 1.5 + centerHalo * 0.6 + ringField * 0.9);
  col += vec3(1.0, 0.95, 0.85) * centerCore * (0.3 + holdGlow * 0.7) * 0.6;

  vec3 inhaleTint = mix(uColC, uColB, 0.5);
  for (int i = 0; i < MAX_PARTICLES; i++) {
    if (inhaleVis < 0.01) break;
    float fi = float(i);
    float phase = fract(uTime * uInhaleSpeed + fi / float(MAX_PARTICLES));
    float ang = hash11(fi * 1.317) * TAU;
    vec2  dir = vec2(cos(ang), sin(ang));
    vec2  pos = dir * (1.55 - phase * 1.55);
    vec2  perpD = vec2(-dir.y, dir.x);
    pos += perpD * sin(phase * PI * 0.8 + fi) * 0.04;
    float ps = uInhaleSize * (0.35 + 0.85 * phase);
    vec2  velDir = -dir;
    float life = smoothstep(0.0, 0.06, phase) * (1.0 - smoothstep(0.92, 1.0, phase));
    float audioBoost = 1.0 + uRMS * uRMSPulse * 0.6;
    float shape = cometShape(p, pos, velDir, ps, uTailLength);
    float a = shape * inhaleVis * life * audioBoost * uParticleAlpha;
    vec3 pc = inhaleTint + paletteCol * 0.10;
    col = 1.0 - (1.0 - col) * (1.0 - clamp(pc * a, 0.0, 1.0));
  }

  vec3 exhaleTint = mix(uColA, vec3(1.0, 0.85, 0.55), 0.35);
  for (int i = 0; i < MAX_PARTICLES; i++) {
    if (exhaleVis < 0.01) break;
    float fi = float(i);
    float phase = fract(uTime * uExhaleSpeed + fi / float(MAX_PARTICLES));
    float ang = hash11(fi * 2.731 + 5.0) * TAU;
    vec2  dir = vec2(cos(ang), sin(ang));
    vec2  pos = dir * phase * 1.55;
    vec2  perpD = vec2(-dir.y, dir.x);
    pos += perpD * sin(phase * PI * 0.8 + fi * 1.7) * 0.04;
    float ps = uExhaleSize * (0.30 + 0.95 * phase);
    vec2  velDir = dir;
    float life = smoothstep(0.00, 0.08, phase) * (1.0 - smoothstep(0.65, 1.0, phase));
    float onsetBurst = 1.0 + uOnset * uOnsetSparkle * 0.8;
    float shape = cometShape(p, pos, velDir, ps, uTailLength);
    float a = shape * exhaleVis * life * onsetBurst * uParticleAlpha;
    vec3 pc = exhaleTint + paletteCol * 0.10;
    col = 1.0 - (1.0 - col) * (1.0 - clamp(pc * a, 0.0, 1.0));
  }

  float grain = hash21(gl_FragCoord.xy + uTime);
  col += (grain - 0.5) * uFlatness * 0.05;

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;

  fragColor = vec4(col, 1.0);
}
