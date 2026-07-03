#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
uniform float u_bands[8];   // per-frequency-band energy: each mandala wedge dances on its own band
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// E-Mantra warm palette: amber / gold / deep orange / red (fire tones)
const vec3 uColA = vec3(0.50, 0.26, 0.09);
const vec3 uColB = vec3(0.48, 0.22, 0.07);
const vec3 uColC = vec3(1.00, 1.00, 1.00);
const vec3 uColD = vec3(0.00, 0.06, 0.11);
const float uCircleRadius = 0.27;
const float uLineWidth    = 0.011;
const float uSaturation   = 1.42;
const float uBrightness   = 1.05;

vec3 palette(float t){ return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a){ float c=cos(a), s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }
float hash11(float n){ return fract(sin(n*127.1)*43758.5453); }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
float fbm(vec2 p){ float v=0.0, a=0.5; for(int i=0;i<5;i++){ v+=a*noise(p); p=rot2D(p,0.7)*2.0; a*=0.5; } return v; }

void main() {
  float uTime=u_time; vec2 uRes=u_resolution;
  float uBass=u_bass, uMids=u_rms, uHighs=u_treble, uBeat=u_onset;

  // --- pattern schedule: HOLD ~4.5s, then a long GRACEFUL morph ~6s into a new one ---
  float E = clamp(u_rms + u_bass*0.4, 0.0, 1.2);
  float pdur = 11.0;
  float ph = uTime / pdur;
  float pf = floor(ph);
  float pt = smoothstep(0.42, 0.95, fract(ph));               // brief hold, then graceful morph over most of the phase
  float s0=hash11(pf), s1=hash11(pf+1.0);
  float s0b=hash11(pf+50.0), s1b=hash11(pf+51.0);
  float rings  = mix(2.0 + floor(s0*3.0), 2.0 + floor(s1*3.0), pt);        // 2..4 rings
  float fold   = mix(6.0 + 2.0*floor(s0*4.0), 6.0 + 2.0*floor(s1*4.0), pt); // 6..12 -fold symmetry (more variety)
  float pradius= mix(0.22 + s0b*0.10, 0.22 + s1b*0.10, pt);                // the mandala SCALE morphs too
  float rotDir = mix(sign(s0-0.5), sign(s1-0.5), pt);
  float zoomB  = mix(1.0 + s0*0.4, 1.0 + s1*0.4, pt);

  vec2 uv = (gl_FragCoord.xy - 0.5*uRes) / min(uRes.x, uRes.y);
  float zoom = zoomB + 0.12*sin(uTime*0.02) + uBass*0.06 + E*0.08;  // slow breathe + gentle expand on the rise
  vec2 p = uv * zoom;
  p = rot2D(p, rotDir * uTime * 0.02);                        // slow steady rotation

  // --- KALEIDOSCOPE with slowly-morphing fold ---
  float ang = atan(p.y, p.x);
  float rad = length(p);
  float seg = TAU / fold;
  // each WEDGE gets its own frequency band -> that area dances on its beat (unique personality)
  float wedge = floor(mod(ang + TAU, TAU) / seg);
  int   bi = int(mod(wedge, 8.0));
  float bandE = u_bands[bi];
  float bandHue = wedge * 0.035;                 // slight per-wedge hue -> each area a distinct character
  ang = mod(ang, seg);
  ang = abs(ang - seg*0.5);
  vec2 kp = vec2(cos(ang), sin(ang)) * rad;

  // --- FRACTAL FILAMENTS (organic roots/branches behind), slow drift ---
  float fil = pow(fbm(kp*3.5 + vec2(uTime*0.03, 0.0)), 1.8);
  float filGlow = fil * (0.22 + uMids*0.3 + uBass*0.2);

  // --- FLOWER-OF-LIFE MANDALA rings (geometry set by the SLOW schedule, not the beat) ---
  float radius = pradius, lw = uLineWidth;
  float field = smoothstep(lw, lw*0.4, abs(length(kp) - radius));
  for (int ring = 1; ring <= 4; ring++) {
    if (float(ring) > rings) break;
    float ringR = float(ring) * radius;
    for (int k = 0; k < 6; k++) {
      for (int j = 0; j < 4; j++) {
        if (j >= ring) break;
        float n = float(k) + float(j)/float(ring);
        float a = TAU * n / 6.0;
        vec2 c = vec2(cos(a), sin(a)) * ringR;
        field = max(field, smoothstep(lw, lw*0.4, abs(length(kp - c) - radius)));
      }
    }
  }

  // per-wedge band dance (form stays on the slow schedule; each wedge's LUMINANCE follows its band)
  float r = length(uv);
  float lowBand = clamp(u_bands[0] + u_bands[1], 0.0, 1.5);
  float halo = exp(-r*r*1.4) * (0.28 + uBass*0.4 + uBeat*0.3 + lowBand*0.7);   // core pulses on kick/sub
  float ripple = sin(length(kp)*14.0 - uTime*1.8 - uMids*4.0)*0.5 + 0.5;
  float glow = uHighs*0.35;
  field *= (1.0 + uBass*0.22);
  float wedgeMod = 0.45 + bandE*1.05;                                          // THIS wedge lights up on its beat
  float intensity = (field*(1.1+glow) + field*ripple*0.22 + filGlow)*wedgeMod + halo + field*bandE*0.55;

  // --- particle dust (slow drift) ---
  float dust = 0.0;
  vec2 gp = uv*24.0;
  for (int i=0;i<2;i++){
    vec2 q = gp + float(i)*13.0 + vec2(0.0, uTime*(0.2+float(i)*0.12));
    vec2 id = floor(q); vec2 fp = fract(q)-0.5;
    float h = hash(id + float(i)*7.0);
    dust += smoothstep(0.06, 0.0, length(fp)) * step(0.93, h) * (0.5+0.5*sin(uTime*1.2+h*30.0));
  }

  float colorT = uTime*0.05 + r*0.5 + field*0.3 + fil*0.2 + bandHue;   // slow drift + per-wedge character
  vec3 col = palette(colorT) * intensity;
  col += palette(colorT+0.2) * dust * 0.55;

  float gray = dot(col, vec3(0.299,0.587,0.114));
  col = mix(vec3(gray), col, uSaturation);
  col *= uBrightness;
  col *= vec3(1.07, 0.93, 0.78);                              // warm bias (kills any green/olive)

  float vig = smoothstep(1.25, 0.35, length(uv));            // dark vignette edges
  col *= vig;

  col = col/(1.0+col*0.55); col *= 1.25;                     // soft tone-map
  fragColor = vec4(col, 1.0);
}
