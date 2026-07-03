#version 330
precision highp float;

// ── Video Creator pipeline contract (bound by shader_service.py) ──
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // voice volume   → chroma split / overall energy
uniform float u_bass;    // low freq       → drip sag
uniform float u_treble;  // high freq      → surface shimmer
uniform float u_onset;   // syllable hits  → pour-point shockwave

out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853

// ── Baked style params (were sliders in Trigun Studio · VocalMelt) ──
const float MELT_SPEED      = 0.5;
const float DRIP_STRENGTH   = 1.0;
const float TRAIL_LENGTH    = 1.0;
const float HAZE_AMOUNT     = 0.4;
const float CHROMA_ABERR    = 0.3;
const float SURFACE_LINE    = 0.6;
const float POOLING         = 0.5;
const float BASS_SAG        = 1.0;
const float MIDS_RIPPLE     = 1.0;
const float HIGHS_SHIMMER   = 1.0;
const float ONSET_SHOCKWAVE = 1.0;
const float COLOR_PULSE     = 0.6;
const float SATURATION      = 1.1;
const float BRIGHTNESS      = 1.0;

// ── Baked IQ cosine palette (cosmic violet) ──
const vec3 COL_A = vec3(0.45, 0.40, 0.55);
const vec3 COL_B = vec3(0.40, 0.35, 0.45);
const vec3 COL_C = vec3(1.0, 1.0, 1.0);
const vec3 COL_D = vec3(0.10, 0.20, 0.45);

vec3 palette(float t) {
  return COL_A + COL_B * cos(TAU * (COL_C * t + COL_D));
}

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

// Per-column drip rate. Each column has its own viscosity (noise of x only)
// blended with a slow time-varying flow so the rate breathes.
float columnDrip(float x, float t) {
  float baseVisc = noise(vec2(x *  7.0, 0.0));
  float flowMod  = noise(vec2(x * 17.0, t * 0.05));
  return baseVisc * 0.65 + flowMod * 0.35;
}

// Procedural source — palette gradient with subtle vertical wave.
vec3 sampleSource(vec2 uv) {
  float t = uv.x * 0.7 + uv.y * 0.3 + u_time * 0.05;
  vec3 c = palette(t);
  float wave = 0.7 + 0.3 * sin(uv.y * 4.0 + u_time * 0.5);
  return c * wave;
}

vec3 sampleWithChroma(vec2 uv, float aberr) {
  if (aberr < 0.001) return sampleSource(uv);
  // Chroma split along the melt axis (vertical); reds drip ahead, blues lag.
  float r = sampleSource(uv + vec2(0.0,  aberr * 0.005)).r;
  float g = sampleSource(uv).g;
  float b = sampleSource(uv - vec2(0.0,  aberr * 0.005)).b;
  return vec3(r, g, b);
}

void main() {
  // Audio aliases (pipeline gives rms/bass/treble/onset; derive mids/beat)
  float aBass  = u_bass;
  float aMids  = clamp((u_bass + u_treble) * 0.5, 0.0, 1.0);
  float aHighs = u_treble;
  float aBeat  = u_onset;
  float aOnset = u_onset;
  float aRMS   = u_rms;

  vec2 uv = gl_FragCoord.xy / u_resolution;
  vec2 px = 1.0 / u_resolution;
  float t = u_time * MELT_SPEED;

  // 1. Per-column drip rate
  float drip = columnDrip(uv.x, u_time);

  // 2. Gravity weight — top drips more than bottom
  float gravity = smoothstep(0.0, 1.0, uv.y);

  // 3. Vertical drip displacement (dominant motion)
  float verticalDrip = drip * gravity * DRIP_STRENGTH * 0.18;

  // 4. Subtle lateral wobble
  float lateralWobble = (noise(vec2(uv.y * 4.0 + t * 0.3, uv.x * 6.0 + t * 0.15)) - 0.5);

  // 5. Audio modulations
  float bassSag = aBass * BASS_SAG * 0.06 * gravity;

  vec2 pourPoint = vec2(0.5 + sin(u_time * 0.25) * 0.32, 0.6 + cos(u_time * 0.31) * 0.25);
  vec2 toPP = uv - pourPoint;
  float distPP = length(toPP);
  vec2 dirPP = distPP > 0.001 ? toPP / distPP : vec2(0.0);
  float pourPull = exp(-distPP * 1.7) * aOnset * ONSET_SHOCKWAVE * 0.045;

  float ripple = sin(uv.y * 22.0 - t * 4.5) * aMids * MIDS_RIPPLE * 0.005;
  float haze   = sin(uv.y * 6.0 + t * 1.0) * HAZE_AMOUNT * 0.004;

  // 6. Composite UV displacement
  vec2 dispUV = uv;
  dispUV.x += lateralWobble * 0.025 + ripple + haze;
  dispUV.y += verticalDrip + bassSag;
  dispUV -= dirPP * pourPull;

  // 7. Sample source with chromatic aberration along melt axis
  float aberr = CHROMA_ABERR * (0.4 + aRMS * 1.2);
  vec3 col = sampleWithChroma(dispUV, aberr);

  // 8. Long drip streaks — 16-tap upward sample, luminance-squared weighted
  float streakLen = TRAIL_LENGTH * (0.4 + drip * 1.6);
  vec3 streakCol = vec3(0.0);
  float streakSum = 0.0;
  for (int i = 1; i <= 16; i++) {
    float fi = float(i);
    float dy = fi * 0.0085 * streakLen;
    vec2 tUV = dispUV + vec2(0.0, dy);
    vec3 above = sampleSource(tUV);
    float lum = dot(above, vec3(0.299, 0.587, 0.114));
    float w = lum * lum * exp(-fi * 0.16);
    streakCol += above * w;
    streakSum += w;
  }
  if (streakSum > 0.01) {
    streakCol /= streakSum;
    col = mix(col, max(col, streakCol * 0.92), 0.55);
  }

  // 9. Edge bleed — soften hard edges with vertical-biased blur
  if (HAZE_AMOUNT > 0.01) {
    vec3 cN = sampleSource(dispUV + vec2(0.0, px.y * 2.5));
    vec3 cS = sampleSource(dispUV - vec2(0.0, px.y * 2.5));
    vec3 cE = sampleSource(dispUV + vec2(px.x * 2.0, 0.0));
    vec3 cW = sampleSource(dispUV - vec2(px.x * 2.0, 0.0));
    vec3 blur = (cN * 1.5 + cS * 0.7 + cE * 0.4 + cW * 0.4) / 3.0;
    col = mix(col, blur, HAZE_AMOUNT * 0.28);
  }

  // 10. Pooling at bottom — accumulated paint brightens lower 25%
  float poolMask = 1.0 - smoothstep(0.0, 0.25, uv.y);
  float poolAmt = poolMask * POOLING;
  if (poolAmt > 0.001) {
    vec3 poolTint = palette(u_time * 0.04 + uv.x * 0.5);
    vec3 poolTintNorm = (poolTint + vec3(0.5)) / 1.5;
    col *= 1.0 + poolAmt * 0.35;
    col = mix(col, col * poolTintNorm * 1.15, poolAmt * 0.4);
  }

  // 11. Surface tension highlights — Sobel edge → wet rim light
  vec3 cR = sampleSource(dispUV + vec2(px.x * 2.0, 0.0));
  vec3 cL = sampleSource(dispUV - vec2(px.x * 2.0, 0.0));
  vec3 cU = sampleSource(dispUV + vec2(0.0, px.y * 2.0));
  vec3 cD = sampleSource(dispUV - vec2(0.0, px.y * 2.0));
  float gradX = dot(cR, vec3(0.299, 0.587, 0.114)) - dot(cL, vec3(0.299, 0.587, 0.114));
  float gradY = dot(cU, vec3(0.299, 0.587, 0.114)) - dot(cD, vec3(0.299, 0.587, 0.114));
  float edge = smoothstep(0.05, 0.4, length(vec2(gradX, gradY)));

  // 12. Shimmer on bright pixels (highs)
  float lum = dot(col, vec3(0.299, 0.587, 0.114));
  float shimmerNoise = hash(uv * 600.0 + u_time * 4.5);
  float shimmer = pow(lum, 3.0) * step(0.7, shimmerNoise) * aHighs * HIGHS_SHIMMER * 1.0;

  // 13. Composite shimmer + surface lines + beat
  col += vec3(1.0, 0.95, 0.85) * shimmer;
  col += vec3(0.95, 0.92, 0.78) * edge * SURFACE_LINE * 0.4;
  col *= 1.0 + aBeat * 0.15;

  // 14. Subtle palette tint on highlights
  vec3 tint = palette(u_time * 0.07 + lum * 0.3);
  vec3 tintNorm = (tint + vec3(0.5)) / 1.5;
  col = mix(col, col * tintNorm * 1.2, lum * COLOR_PULSE * 0.4);

  // 15. Saturation + brightness final
  float gray = dot(col, vec3(0.299, 0.587, 0.114));
  col = mix(vec3(gray), col, SATURATION);
  col *= BRIGHTNESS;

  fragColor = vec4(col, 1.0);
}
