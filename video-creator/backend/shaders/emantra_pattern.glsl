#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
uniform float u_bands[8];
uniform sampler2D u_bg;      // contextual background image (melted behind the pattern)
uniform float u_seed;        // per-chapter flowering seed (different geometry sequence)
uniform vec3  u_tint;        // per-chapter subtle color tint (default white)
uniform float u_foldlo;      // per-chapter symmetry fold floor
uniform float u_foldn;       // per-chapter fold spread (maps 0..this -> extra folds)
out vec4 fragColor;

#define PI  3.14159265
#define TAU 6.2831853

vec3 warm(float t){ return vec3(0.50,0.26,0.09) + vec3(0.48,0.22,0.07)*cos(TAU*(t + vec3(0.0,0.06,0.11))); }
vec2 rot2D(vec2 p, float a){ float c=cos(a),s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }
float hash11(float n){ return fract(sin(n*127.1)*43758.5453); }
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){ float v=0.,a=0.5; for(int i=0;i<4;i++){v+=a*noise(p);p=rot2D(p,0.7)*2.0;a*=0.5;} return v;}

// each PARAM holds, then morphs on its own period (staggered) -> permutations over the track
float sched(float period, float seed, float lo, float hi){
  float ph=u_time/period; float pf=floor(ph); float pt=smoothstep(0.55,1.0,fract(ph));
  return mix(lo + hash11((pf+u_seed)*seed)*(hi-lo), lo + hash11((pf+1.0+u_seed)*seed)*(hi-lo), pt);
}

void main(){
  vec2 uRes=u_resolution;
  vec2 uv=(gl_FragCoord.xy - 0.5*uRes)/min(uRes.x,uRes.y);
  float bLow =clamp(u_bands[0]+u_bands[1]+u_bands[2],0.0,1.6);
  float bMid =clamp(u_bands[3]+u_bands[4]+u_bands[5],0.0,1.6);
  float bHigh=clamp(u_bands[6]+u_bands[7],0.0,1.6);

  // ================= MELTED CONTEXTUAL BACKGROUND (2-level domain warp = liquid flow) =========
  vec2 buv = gl_FragCoord.xy/uRes;
  vec2 q  = vec2(fbm(buv*3.0 + u_time*0.03), fbm(buv*3.0 + vec2(5.2,1.3) + u_time*0.04));
  vec2 r2 = vec2(fbm(buv*3.0 + 4.0*q + u_time*0.02), fbm(buv*3.0 + 4.0*q + vec2(8.3,2.8) + u_time*0.03));
  vec2 buv2 = buv + (r2-0.5)*0.16;
  vec3 bgcol = texture(u_bg, buv2).rgb;
  bgcol = pow(bgcol, vec3(1.1)) * vec3(1.10,0.92,0.72) * 0.55;   // warm, darkened so the pattern reads

  // ================= PATTERN PARAMS: base schedule + audio modulation =========================
  float baseRings = sched(10.0, 1.7,  2.0, 4.6);
  float baseRad   = sched(13.0, 2.3,  0.15, 0.30);
  float baseZoom  = sched( 9.0, 3.1,  0.95, 1.45);
  float baseLW    = sched(11.0, 4.5,  0.008, 0.016);
  float baseRot   = sched(15.0, 5.9, -0.03, 0.03);
  float fold      = u_foldlo + 2.0*floor(sched(12.0, 6.7, 0.0, u_foldn));
  float colCyc    = sched(14.0, 7.3,  0.02, 0.09);

  float rings  = baseRings + bLow*1.4;             // KICK multiplies the rings
  float radius = baseRad * (1.0 + bHigh*0.55);     // HIGHS grow the circle size
  float zoom   = baseZoom + bLow*0.10;             // bass zoom pulse
  float lineW  = baseLW * (1.0 + bMid*0.6);        // MIDS thicken the lines
  float rotV   = baseRot + bMid*0.020;             // mids add rotation

  vec2 p = uv*zoom;
  p = rot2D(p, u_time*rotV*3.0);
  float ang=atan(p.y,p.x), rad=length(p), seg=TAU/fold;
  ang=mod(ang,seg); ang=abs(ang-seg*0.5);
  vec2 kp=vec2(cos(ang),sin(ang))*rad;

  // flower-of-life field + soft GLOW halo (bloom)
  float lw=lineW, field=0.0, glow=0.0;
  float d0=abs(length(kp)-radius);
  field=smoothstep(lw,lw*0.4,d0); glow+=exp(-d0*d0*900.0);
  for(int ring=1;ring<=5;ring++){
    if(float(ring) > rings+0.5) break;
    float fade=clamp(rings-float(ring)+1.0,0.0,1.0);
    float rr=float(ring)*radius;
    for(int k=0;k<6;k++){ for(int j=0;j<4;j++){ if(j>=ring)break;
      float n=float(k)+float(j)/float(ring); float a=TAU*n/6.0;
      vec2 c=vec2(cos(a),sin(a))*rr;
      float d=abs(length(kp-c)-radius);
      field=max(field, smoothstep(lw,lw*0.4,d)*fade);
      glow+=exp(-d*d*900.0)*fade; }}}
  glow=clamp(glow,0.0,3.0);

  float intensity = field * (1.0 + bLow*0.35 + bHigh*0.25);
  float colorT = u_time*colCyc + rad*0.5 + field*0.3;

  // ================= COMPOSITE: melted bg + glowing pattern on top ============================
  vec3 col = bgcol;
  col += warm(colorT+0.05) * glow * 0.14;          // bloom halo
  col += warm(colorT) * intensity * 1.15;          // crisp glowing lines on top

  col = mix(vec3(dot(col,vec3(0.299,0.587,0.114))), col, 1.4);   // saturation
  col *= vec3(1.05,0.94,0.80) * u_tint;                          // warm bias + per-chapter tint
  col *= smoothstep(1.35,0.30,length(uv));                       // vignette
  col = col/(1.0+col*0.5); col*=1.32;                            // tone-map
  fragColor=vec4(col,1.0);
}
