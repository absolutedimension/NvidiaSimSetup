#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// studio base values (Enso panel) — those marked * animate dynamically in main()
const float uStrokeWidth = 0.03;
const float uOpenAngle   = 0.50;
const float uInkSpread   = 0.70;
const float uPaperGrain  = 0.40;
const float uOnsetEcho   = 1.00;
const float uVoiceGlow   = 0.80;
const float uBeatBrush   = 0.60;
const float uSaturation  = 1.50;
const float uBrightness  = 1.00;
// classic ink-gold enso palette
const vec3 uColA = vec3(0.10, 0.078, 0.063);
const vec3 uColB = vec3(0.81, 0.65, 0.36);
const vec3 uColC = vec3(0.88, 0.88, 0.88);
const vec3 uColD = vec3(0.04, 0.04, 0.04);

vec3 palette(float t){ return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a){ float c=cos(a), s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }
float hash(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f);
  float a=hash(i),b=hash(i+vec2(1,0)),c=hash(i+vec2(0,1)),d=hash(i+vec2(1,1));
  return mix(mix(a,b,u.x),mix(c,d,u.x),u.y); }
float fbm(vec2 p){ float v=0.0,amp=0.5; for(int i=0;i<4;i++){v+=amp*noise(p);p*=2.05;amp*=0.55;} return v; }

void main() {
  float uTime=u_time; vec2 uRes=u_resolution;
  float uSubBass=u_bass, uBass=u_bass, uMids=u_rms, uHighs=u_treble, uBeat=u_onset;
  float uRMS=u_rms, uCentroid=u_treble, uFlatness=u_treble*0.5, uFlux=u_onset;
  float uZCR=u_treble, uOnset=u_onset, uSilence=clamp(1.0-u_rms*2.0,0.0,1.0);
  float E = clamp(u_rms*1.2 + u_bass*0.5, 0.0, 1.2);

  // === DYNAMIC controls (studio base + slow LFO + energy) ===
  float uRadius        = 0.45 + 0.05*sin(uTime*0.018) + E*0.06;   // the ring breathes
  float uColorSpeed    = 0.04 + E*0.05;
  float uRotationSpeed = 0.0  + 0.010*sin(uTime*0.012);

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p = rot2D(uv, uTime * uRotationSpeed);
  float r = length(p);
  float ang = atan(p.y, p.x);

  float wobble = fbm(vec2(ang * 2.0, uTime * 0.4)) - 0.5;
  float audioSwell = 0.06 * uRMS + 0.04 * uBass;
  float ringR = uRadius + wobble * 0.04 + audioSwell;
  float dist = abs(r - ringR);

  float thicken = uBeatBrush * uBeat * 0.012;
  float lw = uStrokeWidth + thicken;
  float gap = smoothstep(uOpenAngle - 0.3, uOpenAngle, abs(ang - 0.0));
  float ink = smoothstep(lw, lw * 0.3, dist) * gap;

  float echo = uOnset * uOnsetEcho * smoothstep(0.04, 0.0, abs(r - ringR - 0.14)) * gap;
  float voiceLike = smoothstep(0.6, 0.2, uZCR) * uRMS * uVoiceGlow;
  float interior = exp(-r * r * 3.5) * voiceLike * 0.7;
  float paper = fbm(uv * 6.0 + 12.34) * uPaperGrain;

  float intensity = ink * 1.6 + echo + interior + paper * 0.08 + 0.02;
  intensity = mix(intensity, max(intensity, 0.06), uSilence);
  float bleed = noise(p * 9.0 + uTime * 0.3) * uFlatness * uInkSpread * 0.25;

  float colorT = uTime * uColorSpeed + r * 0.3 + uCentroid * 0.4;
  vec3 col = palette(colorT) * (intensity + bleed);

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;
  col = col / (1.0 + col * 0.55); col *= 1.25;   // soft tone-map (no blowout)
  fragColor = vec4(col, 1.0);
}
