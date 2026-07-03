#version 330
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // mids/overall
uniform float u_bass;    // 20-300 Hz
uniform float u_treble;  // 2-8 kHz
uniform float u_onset;   // beat
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// ---- baked params (tune here) ----
const float uMirrors      = 6.0;
const float uIterations   = 5.0;
const float uZoom         = 1.3;
const float uPatternScale = 1.2;
const float uRotSpeed     = 0.05;
const float uColSpeed     = 0.12;
const float uBassStretch  = 1.0;
const float uMidsTwist    = 1.0;
const float uHighsBright  = 1.0;
const float uBeatPunch    = 1.0;
const float uSaturation   = 1.10;
const float uBrightness   = 0.90;
// cosmic blue/cyan/violet palette
const vec3 uColA = vec3(0.5, 0.5, 0.5);
const vec3 uColB = vec3(0.5, 0.5, 0.5);
const vec3 uColC = vec3(1.0, 1.0, 1.0);
const vec3 uColD = vec3(0.00, 0.12, 0.30);

vec3 palette(float t) { return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a) { float c=cos(a), s=sin(a); return vec2(c*p.x - s*p.y, s*p.x + c*p.y); }
float hash21(vec2 p) { p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float noise2(vec2 p) {
  vec2 i=floor(p), f=fract(p);
  float a=hash21(i), b=hash21(i+vec2(1,0)), c=hash21(i+vec2(0,1)), d=hash21(i+vec2(1,1));
  vec2 u=f*f*(3.0-2.0*f);
  return mix(a,b,u.x) + (c-a)*u.y*(1.0-u.x) + (d-b)*u.x*u.y;
}
float fbm(vec2 p) { float v=0.0,amp=0.5; for(int i=0;i<4;i++){v+=amp*noise2(p);p*=2.02;amp*=0.5;} return v; }
vec2 kaleidoFold(vec2 p, float N) {
  float r=length(p), a=atan(p.y,p.x), wedge=TAU/N;
  a=abs(mod(a+wedge*100.0,wedge)-wedge*0.5);
  return vec2(cos(a),sin(a))*r;
}

void main() {
  // ---- audio mapping (custom bands -> pipeline's 4) ----
  float uTime=u_time; vec2 uRes=u_resolution;
  float uSubBass=u_bass, uBass=u_bass, uMids=u_rms, uHighs=u_treble, uBeat=u_onset;
  float uOnset=u_onset;

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p = uv * uZoom;
  p = rot2D(p, uTime * uRotSpeed);

  vec2 q = p;
  float energy = 0.0;
  for (int i = 0; i < 8; i++) {
    if (float(i) >= uIterations) break;
    q = kaleidoFold(q, uMirrors);
    q = q * uPatternScale - vec2(0.5, 0.3);
    q = rot2D(q, uTime * 0.3 + float(i) * 0.7);
    energy += abs(sin(length(q) * 6.0 - uTime * (1.5 + float(i) * 0.4))) * pow(0.5, float(i));
  }

  float fbmDetail = pow(fbm(p * 3.0 + uTime * 0.1), 1.5);
  float intensity = energy * 0.8 + fbmDetail * 0.4;
  intensity *= 1.0 + uSubBass * 0.3;

  float colorT = uTime * uColSpeed * (1.0 + uMids * uMidsTwist * 0.6) + length(p) * 0.4 + intensity * 0.3;
  vec3 col = palette(colorT) * (0.40 + intensity * 0.85);

  // central bloom — the music-reactive heart (toned down so it never blows out)
  float distFromCenter = length(uv);
  float bloomCore = exp(-distFromCenter * distFromCenter * 5.5);
  float bloomAmt = (uBass * uBassStretch + uOnset * 0.5) * bloomCore;
  vec3 bloomColor = palette(uTime * uColSpeed * 1.4 + 0.2);
  col += bloomColor * bloomAmt * 0.6;

  // sparkle
  float sparkle = sin(atan(p.y, p.x) * 80.0 + uTime * 6.0) * sin(length(p) * 100.0 - uTime * 4.0);
  col += sparkle * sparkle * uHighs * uHighsBright * 0.22;

  // beat pulse (center only)
  col += bloomColor * uBeat * uBeatPunch * bloomCore * 0.35;

  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;

  // soft tone-map so peaks roll off instead of clipping to white
  col = col / (1.0 + col * 0.55);
  col *= 1.25;   // restore overall level after the roll-off

  fragColor = vec4(col, 1.0);
}
