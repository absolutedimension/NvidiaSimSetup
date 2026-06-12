#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }
float h1(float x){ return fract(sin(x*127.1)*43758.5453); }

// glowing diagonal seam: bright core + soft bloom
float seam(float diag, float pos, float core, float bloom){
    float dd = abs(diag - pos);
    return exp(-dd*core) + 0.45*exp(-dd*bloom);
}

void main(){
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec2 p = uv - 0.5;
    p.x *= u_resolution.x / u_resolution.y;     // aspect correct
    float t = u_time * 0.05;

    // diagonal axis (panels run at ~ -30 deg)
    vec2 d = rot(-0.52) * p;
    float diag = d.x * 1.5 + d.y * 0.5;

    // --- dark beveled panels: big, subtle facets ---
    float band = diag * 1.15 + t * 0.18;
    float pid = floor(band);
    float frac = fract(band);
    float shade = 0.6 + 0.9 * h1(pid);                 // each panel slightly different dark
    vec3 col = vec3(0.035, 0.045, 0.075) * shade;
    col *= 0.78 + 0.34 * frac;                          // soft bevel gradient across each panel
    col += vec3(0.018, 0.026, 0.05) * (1.0 - uv.y);     // gentle top-light gradient

    // --- the neon edge-glows (the stars — blue + magenta, slowly drifting) ---
    vec3 BLUE = vec3(0.28, 0.55, 1.05);
    vec3 MAG  = vec3(1.05, 0.18, 0.70);
    float react = 0.85 + 0.45 * u_rms;

    // primary blue seam (upper-right), primary magenta seam (lower-left)
    col += BLUE * seam(diag,  0.70 + 0.10*sin(t*0.6), 52.0, 10.0) * 0.95 * react;
    col += MAG  * seam(diag, -0.66 + 0.10*cos(t*0.5), 52.0, 10.0) * 0.92 * react;
    // a softer secondary pair, further out
    col += BLUE * 0.42 * seam(diag,  1.20 + 0.08*sin(t*0.4+1.0), 66.0, 16.0) * react;
    col += MAG  * 0.42 * seam(diag, -1.16 + 0.08*cos(t*0.45),    66.0, 16.0) * react;

    // faint thin highlight lines on a few panel seams (the crisp edges in the ref)
    float seamEdge = min(frac, 1.0-frac);
    float active = step(0.62, h1(pid+3.0));
    vec3 lineCol = (h1(pid+7.0) > 0.5) ? BLUE : MAG;
    col += lineCol * exp(-seamEdge*90.0) * active * 0.35 * react;

    // vignette + slight lift
    col *= 1.0 - 0.42 * dot(p, p);
    col = pow(max(col, 0.0), vec3(0.92));

    fragColor = vec4(col, 1.0);
}
