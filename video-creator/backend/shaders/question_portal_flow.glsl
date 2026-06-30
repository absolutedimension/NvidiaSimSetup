#version 330
precision highp float;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms, u_bass, u_treble, u_onset;
out vec4 fragColor;

#define PI  3.1415926
#define TAU 6.2831853
#define MAX_BUBBLES 6

// studio base values (Question Portal panel)
const float uSphereRadius = 0.13;
const float uGlowFalloff  = 1.80;
const float uRingSpacing  = 0.13;
const float uRingThickness= 0.01;
const float uRaysCount    = 16.0;
const float uShockSpeed   = 0.40;
const float uBubbleSize   = 0.10;
const float uBubbleSpread = 0.05;
const float uBubbleAlpha  = 1.00;
const float uImpactBoost  = 1.10;
const float uVoicePulse   = 1.10;
const float uOnsetShockwave=1.00;
const float uCentroidGlow = 0.85;
const float uBandsRingMix = 1.00;
const float uHighsSparkle = 0.75;
const float uSilenceBreath= 0.50;
const float uRaysIntensity= 0.65;
const float uSaturation   = 1.40;
const float uBrightness   = 1.00;
const float uBubbleCount  = 4.0;
// yellow / blue / teal palette
const vec3 uColA = vec3(0.80, 0.70, 0.40);
const vec3 uColB = vec3(0.30, 0.40, 0.52);
const vec3 uColC = vec3(0.50, 0.72, 0.80);
const vec3 uColD = vec3(0.10, 0.20, 0.42);

vec3 palette(float t){ return uColA + uColB * cos(TAU * (uColC * t + uColD)); }
vec2 rot2D(vec2 p, float a){ float c=cos(a), s=sin(a); return vec2(c*p.x-s*p.y, s*p.x+c*p.y); }
float hash21(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }

void main() {
  float uTime=u_time; vec2 uRes=u_resolution;
  float uSubBass=u_bass, uBass=u_bass, uMids=u_rms, uHighs=u_treble, uBeat=u_onset;
  float uRMS=u_rms, uCentroid=u_treble, uFlatness=u_treble*0.5, uOnset=u_onset;
  float uSilence=clamp(1.0-u_rms*2.0,0.0,1.0);
  float E = clamp(u_rms*1.2 + u_bass*0.5, 0.0, 1.2);
  float uBands[8];
  uBands[0]=u_bass; uBands[1]=u_bass*0.85; uBands[2]=mix(u_bass,u_rms,0.5);
  uBands[3]=u_rms;  uBands[4]=u_rms*0.9;   uBands[5]=mix(u_rms,u_treble,0.5);
  uBands[6]=u_treble; uBands[7]=u_treble*0.8;

  // === DYNAMIC controls ===
  float uColorSpeed    = 0.05 + E*0.05;
  float uRotationSpeed = 0.0  + 0.008*sin(uTime*0.011);
  float uBubbleSpeed   = 0.08 + E*0.04;          // questions arrive faster at peaks
  float uRingCount     = 2.0 + E*2.0;            // more rings bloom at peaks

  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / min(uRes.x, uRes.y);
  vec2 p  = rot2D(uv, uTime * uRotationSpeed);
  float r = length(p);
  float theta = atan(p.y, p.x);

  float bcount = max(1.0, min(uBubbleCount, float(MAX_BUBBLES)));
  float impactBoost = 0.0;
  for (int i = 0; i < MAX_BUBBLES; i++) {
    if (float(i) >= bcount) break;
    float phase = fract(uTime * uBubbleSpeed + float(i) / bcount);
    if (phase > 0.92) impactBoost += smoothstep(0.92,0.98,phase)*(1.0-smoothstep(0.98,1.005,phase));
  }
  impactBoost *= uImpactBoost * (1.0 + uOnset * uOnsetShockwave * 0.5);

  float vocalEnergy = clamp(uRMS*0.6 + uMids*0.45 + (uBands[2]+uBands[3])*0.30, 0.0, 1.2);
  float pulse = uVoicePulse * vocalEnergy + impactBoost * 0.6;
  float sphereR = uSphereRadius;
  float core = exp(-(r*r)/(sphereR*sphereR*(1.0+pulse*1.6)));
  vec2 hOff = vec2(-sphereR*0.30, sphereR*0.30);
  float highlight = exp(-dot(p-hOff,p-hOff)/(sphereR*sphereR*0.18));
  float sphereMask = 1.0 - smoothstep(sphereR*0.85, sphereR*1.08, r);
  float haloRad = sphereR * uGlowFalloff * (1.0 + uCentroidGlow*uCentroid*0.9);
  float halo = exp(-(r*r)/(haloRad*haloRad*0.30)) * (0.30 + pulse*0.55);

  float rings=0.0, ringTC=0.0; int maxRings=int(min(uRingCount,8.0));
  for (int i=0;i<8;i++){ if(i>=maxRings) break; float fi=float(i);
    float Ri=sphereR+(fi+1.0)*uRingSpacing; float band=uBands[i];
    float bw=uRingThickness*(1.0+band*uBandsRingMix*6.0);
    float ring=smoothstep(bw,0.0,abs(r-Ri));
    ring*=0.45+band*uBandsRingMix+uBeat*0.20+impactBoost*0.5;
    rings+=ring; ringTC+=ring*(fi/max(1.0,float(maxRings))); }

  float wp1=fract(uTime*uShockSpeed), wp2=fract(uTime*uShockSpeed*0.65+0.5);
  float shock = exp(-pow((r-wp1*2.0)*5.5,2.0))*(0.25+uOnset*uOnsetShockwave+impactBoost*0.6)
              + exp(-pow((r-wp2*2.0)*6.5,2.0))*(0.15+uBeat*0.55+impactBoost*0.4);
  float rays = pow(0.5+0.5*cos(theta*uRaysCount),5.0)*exp(-(r-sphereR)*2.4)*step(sphereR*0.9,r)*uRaysIntensity*(0.35+pulse*1.6);
  float impactFlash = exp(-r*r*14.0)*impactBoost*2.4;

  vec2 cellId=floor(p*(180.0+uHighs*60.0)+uTime*6.0);
  float ringBand=smoothstep(sphereR, sphereR+uRingSpacing*float(maxRings)+uRingSpacing*0.5, r);
  float sparkle=step(0.92,hash21(cellId))*ringBand*uHighs*uHighsSparkle*(0.30+uCentroid*0.70);
  float breath=(sin(uTime*0.7)*0.5+0.5)*uSilence*uSilenceBreath;
  float ambient=exp(-(r*r)/(haloRad*haloRad*0.55))*breath*0.45;

  float intensity = core*(1.0+pulse*1.4) + sphereMask*(0.55+highlight*1.55+pulse*0.45)
    + halo*0.65 + rings*1.30 + shock*1.20 + rays*0.80 + sparkle*1.40 + ambient + impactFlash;
  float colorT = r*0.55 + ringTC*0.45 + uCentroid*0.35 + uTime*uColorSpeed;
  vec3 col = palette(colorT) * intensity;
  col += vec3(highlight*sphereMask)*(0.45+pulse*0.55);
  col += vec3(1.0,0.95,0.85)*impactFlash*0.6;

  // bubbles (incoming "questions")
  vec3 waterTint=mix(uColC,uColB,0.5), questionTint=uColA;
  float coreVoiceBoost=1.0+uMids*0.7+uRMS*0.4;
  for (int i=0;i<MAX_BUBBLES;i++){ if(float(i)>=bcount) break; float fi=float(i);
    float phase=fract(uTime*uBubbleSpeed+fi/bcount);
    float angle=(fi/bcount)*TAU+0.43; vec2 spawn=vec2(cos(angle),sin(angle))*1.55;
    vec2 perpDir=vec2(-sin(angle),cos(angle));
    vec2 pos=mix(spawn,vec2(0.0),phase)+perpDir*sin(phase*PI*1.7+fi*1.3)*uBubbleSpread*(1.0-phase);
    float bsize=uBubbleSize*(0.55+0.65*(1.0-phase));
    vec2 bd=p-pos; float bl=length(bd); if(bl>bsize*1.20) continue;
    float fill=1.0-smoothstep(bsize*0.92,bsize*1.0,bl);
    float rim=smoothstep(bsize*0.78,bsize*0.92,bl)*(1.0-smoothstep(bsize*0.96,bsize*1.0,bl));
    vec2 specOff=pos+vec2(-bsize*0.30,bsize*0.30);
    float spec=exp(-dot(p-specOff,p-specOff)/(bsize*bsize*0.045));
    float bcore=exp(-bl*bl/(bsize*bsize*0.08))*(0.50+0.50*sin(uTime*5.0+fi*2.4));
    bcore*=1.0+smoothstep(0.55,0.95,phase)*2.5; bcore*=coreVoiceBoost;
    float life=smoothstep(0.0,0.06,phase)*(1.0-smoothstep(0.96,1.0,phase));
    vec3 emit=waterTint*(fill*0.35+rim*0.85)+vec3(1.0)*spec*0.55+questionTint*bcore*1.6;
    float a=(fill*0.40+rim*0.90+spec*0.65+bcore*0.85)*uBubbleAlpha*life;
    col=1.0-(1.0-col)*(1.0-clamp(emit*a,0.0,1.0));
  }

  float grain=hash21(gl_FragCoord.xy+uTime); col+=(grain-0.5)*uFlatness*0.06;
  float gray=dot(col,vec3(0.299,0.587,0.114)); col=mix(vec3(gray),col,uSaturation); col*=uBrightness;
  col = col / (1.0 + col * 0.55); col *= 1.25;   // soft tone-map
  fragColor=vec4(col,1.0);
}
