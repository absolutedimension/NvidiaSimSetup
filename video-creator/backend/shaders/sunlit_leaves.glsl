#version 330
precision highp float;

uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // gentle extra sway
uniform float u_bass;
uniform float u_treble;  // subtle light shimmer
uniform float u_onset;

out vec4 fragColor;

#define PI 3.14159265

float hash(vec2 p){ p = fract(p * vec2(127.1, 311.7)); p += dot(p, p + 34.5); return fract(p.x * p.y); }

float noise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++){ v += a * noise(p); p *= 2.02; a *= 0.5; }
  return v;
}

// Ovate leaf, leaf-local space: base at origin (0,0), tip at (0,1), +y = along leaf.
float leafSDF(vec2 p){
  float y = p.y;
  float body = sin(clamp(y, 0.0, 1.0) * PI);   // 0 at base & tip, 1 at middle
  float w = 0.34 * pow(body, 0.62);            // fuller body, gently pointed tip
  float d = abs(p.x) - w;
  float yb = max(-y, y - 1.0);                 // clamp to 0..1 length
  return max(d, yb);
}

// Soft shadow contribution of one leaf pointing along world angle `ang`.
float leafShadow(vec2 p, vec2 base, float ang, float sz){
  vec2 ldir = vec2(cos(ang), sin(ang));
  vec2 lperp = vec2(-ldir.y, ldir.x);
  vec2 rel = (p - base) / sz;
  vec2 lp = vec2(dot(rel, lperp), dot(rel, ldir));   // x = across, y = along leaf
  return smoothstep(0.13, -0.05, leafSDF(lp));        // soft penumbra
}

// Distance from p to segment a-b (for the twig).
float segDist(vec2 p, vec2 a, vec2 b){
  vec2 pa = p - a, ba = b - a;
  float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
  return length(pa - ba * h);
}

// A branch: a twig with leaves splaying alternately off it.
float branch(vec2 p, vec2 anchor, vec2 dir, float len, float baseSize, float wind, float strength){
  float stemAng = atan(dir.y, dir.x);
  vec2 tip = anchor + dir * len;
  float sh = smoothstep(0.014, 0.0, segDist(p, anchor, tip)) * 0.55;  // twig
  for (int i = 0; i < 7; i++){
    float t = float(i) / 6.0;
    vec2 base = anchor + dir * (t * len);
    float side = (mod(float(i), 2.0) < 0.5) ? 1.0 : -1.0;
    float ang = stemAng + side * 1.15 + wind * (0.4 + t) * side;       // ~66 deg off twig, tips sway more
    float sz = baseSize * (1.0 - 0.45 * t);
    sh = max(sh, leafShadow(p, base, ang, sz));
  }
  return sh * strength;
}

void main(){
  vec2 res = u_resolution;
  vec2 uv  = gl_FragCoord.xy / res;
  float asp = res.x / res.y;
  vec2 p = vec2(uv.x * asp, uv.y);          // aspect-correct space

  // Wind — slow base + gusts, faint voice boost.
  float wind = sin(u_time * 0.40) * 0.06 + (fbm(vec2(u_time * 0.15, 0.0)) - 0.5) * 0.10;
  wind += u_rms * 0.03;

  // --- Sage plaster wall ---
  vec3 wall = vec3(0.60, 0.70, 0.57);
  wall *= 0.92 + 0.10 * fbm(p * 1.5 + 10.0);                 // soft tonal variation
  wall += (noise(gl_FragCoord.xy * 0.5) - 0.5) * 0.015;      // fine plaster grain

  // --- Dappled sunlight: drifting soft bright bands ---
  vec2 ld = p * 1.6 + vec2(u_time * 0.03, -u_time * 0.015);
  float light = smoothstep(0.45, 0.85, fbm(ld));
  float sweep = smoothstep(0.0, 1.4, uv.x * 0.5 + (1.0 - uv.y) * 0.8);  // brighter top-left
  light *= 0.6 + 0.4 * sweep;
  wall += vec3(0.16, 0.16, 0.12) * light;                   // warm highlight
  wall += vec3(0.04) * u_treble * light;                    // subtle shimmer

  // --- Leaf shadows ---
  float shadow = 0.0;
  shadow = max(shadow, branch(p, vec2(0.06 * asp, 0.99), normalize(vec2(1.0, -0.55)),
                              0.65, 0.20, wind, 1.0));        // primary, upper-left
  shadow = max(shadow, branch(p, vec2(0.99 * asp, 0.04), normalize(vec2(-0.7, 0.7)),
                              0.55, 0.16, wind, 0.55));       // fainter, lower-right

  // Shadow darkens + cools the wall slightly.
  vec3 shadowCol = wall * vec3(0.58, 0.69, 0.57);
  vec3 col = mix(wall, shadowCol, shadow * 0.82);

  // Gentle vignette.
  col *= 0.90 + 0.10 * smoothstep(1.2, 0.2, length(uv - 0.5));

  fragColor = vec4(col, 1.0);
}
