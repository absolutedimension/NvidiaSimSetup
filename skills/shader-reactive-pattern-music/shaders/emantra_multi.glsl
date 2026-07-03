#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
uniform float u_bands[8];     // per-band energy — each LAYER (shader) is driven by its own band group
out vec4 fragColor;

#define PI  3.14159265
#define TAU 6.2831853

vec3 pal(float t, vec3 A, vec3 B, vec3 C, vec3 D){ return A + B*cos(TAU*(C*t+D)); }
vec3 warm(float t){ return pal(t, vec3(0.50,0.26,0.09), vec3(0.48,0.22,0.07), vec3(1.0,1.0,1.0), vec3(0.0,0.06,0.11)); }
vec2 rot2D(vec2 p, float a){ float c=cos(a),s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }
float hash11(float n){ return fract(sin(n*127.1)*43758.5453); }
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){ float v=0.,a=0.5; for(int i=0;i<5;i++){v+=a*noise(p);p=rot2D(p,0.7)*2.0;a*=0.5;} return v;}

// LAYER A — KALEIDOSCOPE FRACTAL (mid band): the flowing background, drifts faster on mids
float layerKaleido(vec2 uv, float fold, float t, float drive){
  vec2 p = uv*(1.25 + 0.12*sin(t*0.03));
  p = rot2D(p, t*0.02);
  float ang=atan(p.y,p.x), rad=length(p), seg=TAU/fold;
  ang=mod(ang,seg); ang=abs(ang-seg*0.5);
  vec2 kp=vec2(cos(ang),sin(ang))*rad;
  float f=pow(fbm(kp*4.0 + vec2(t*(0.05+drive*0.18),0.0)), 1.6);
  return f*(0.35+drive*1.0);
}
// LAYER B — FLOWER OF LIFE (the geometry itself reacts): HIGH beats GROW the circles,
// KICK MULTIPLIES the rings + pulses the whole flower. Band envelopes -> grows & settles.
float layerFlower(vec2 uv, float rings, float radius, float t, float dLow, float dHigh){
  float sc = 1.0 - dLow*0.10;                       // whole flower pulses in on the kick
  vec2 p = uv*sc; p = rot2D(p, t*0.012);
  float ang=atan(p.y,p.x), rad=length(p), seg=TAU/8.0;
  ang=mod(ang,seg); ang=abs(ang-seg*0.5);
  vec2 kp=vec2(cos(ang),sin(ang))*rad;
  float rr0 = radius * (1.0 + dHigh*0.55);          // circles GROW / multiply size on HIGH beats
  float ringsD = rings + dLow*1.4;                  // more rings MULTIPLY on the kick
  float lw=0.010;
  float field=smoothstep(lw,lw*0.4,abs(length(kp)-rr0));
  for(int ring=1;ring<=5;ring++){
    if(float(ring) > ringsD+0.5) break;
    float fade = clamp(ringsD - float(ring) + 1.0, 0.0, 1.0);   // new rings fade in smoothly
    float rr=float(ring)*rr0;
    for(int k=0;k<6;k++){ for(int j=0;j<4;j++){ if(j>=ring)break;
      float n=float(k)+float(j)/float(ring); float a=TAU*n/6.0;
      vec2 c=vec2(cos(a),sin(a))*rr;
      field=max(field, smoothstep(lw,lw*0.4,abs(length(kp-c)-rr0))*fade); }}}
  return field*(0.6 + dLow*1.2 + dHigh*0.5);
}
// LAYER C — PORTAL RIPPLES (high band): concentric rings emanate outward on the hats
float layerPortal(vec2 uv, float t, float drive){
  float r=length(uv);
  float ring=smoothstep(0.72,1.0, sin(r*22.0 - t*3.0 - drive*7.0));
  float fall=exp(-r*r*2.2);
  float core=exp(-r*r*7.0)*(0.4+drive*1.6);
  return ring*fall*(0.15+drive*1.0) + core;
}

void main(){
  float t=u_time; vec2 uRes=u_resolution;
  vec2 uv=(gl_FragCoord.xy-0.5*uRes)/min(uRes.x,uRes.y);

  // band groups: LOW (kick/sub/bass) / MID (stab/mids) / HIGH (hats/air)
  float bLow =clamp(u_bands[0]+u_bands[1]+u_bands[2],0.0,1.6);
  float bMid =clamp(u_bands[3]+u_bands[4]+u_bands[5],0.0,1.6);
  float bHigh=clamp(u_bands[6]+u_bands[7],0.0,1.6);

  // slow pattern schedule (hold ~4.5s -> graceful morph ~6s)
  float pdur=11.0, ph=t/pdur, pf=floor(ph), pt=smoothstep(0.42,0.95,fract(ph));
  float s0=hash11(pf),s1=hash11(pf+1.0), s0b=hash11(pf+50.),s1b=hash11(pf+51.);
  float fold  =mix(6.0+2.0*floor(s0*4.0),6.0+2.0*floor(s1*4.0),pt);
  float rings =mix(2.0+floor(s0*3.0),2.0+floor(s1*3.0),pt);
  float radius=mix(0.22+s0b*0.10,0.22+s1b*0.10,pt);

  float A=layerKaleido(uv, fold, t, bMid);     // mids
  float B=layerFlower(uv, rings, radius, t, bLow, bHigh);   // kick multiplies rings, highs grow size
  float C=layerPortal(uv, t, bHigh);           // hats

  // each layer a distinct warm hue, composited additively
  vec3 col = vec3(0.0);
  col += warm(0.03 + t*0.015) * A * 0.55;      // background kaleido-fractal: deep amber/red
  col += warm(0.28) * B * 1.05;                // flower rings: gold
  col += (warm(0.5)*0.6 + vec3(1.0,0.92,0.72)*0.5) * C * 0.9;  // portal: hot yellow-white

  // particle dust
  float dust=0.0; vec2 gp=uv*24.0;
  for(int i=0;i<2;i++){ vec2 q=gp+float(i)*13.0+vec2(0.0,t*(0.2+float(i)*0.12));
    vec2 id=floor(q),fp=fract(q)-0.5; float h=hash(id+float(i)*7.0);
    dust+=smoothstep(0.06,0.0,length(fp))*step(0.93,h)*(0.5+0.5*sin(t*1.2+h*30.0)); }
  col += warm(0.45)*dust*0.5;

  col *= vec3(1.06,0.93,0.78);                  // warm bias
  float vig=smoothstep(1.28,0.35,length(uv)); col*=vig;
  col=col/(1.0+col*0.5); col*=1.3;              // soft tone-map
  fragColor=vec4(col,1.0);
}
