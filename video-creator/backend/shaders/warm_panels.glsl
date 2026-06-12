#version 330
precision highp float;

// TrigunAI pipeline shader contract
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;
out vec4 fragColor;

// Original "warm panels on a perspective floor" — inspired by the editing-bg style,
// NOT a copy of any clip. Warm gradient bars of varying heights stand on a glowing
// horizon above a perspective floor that recedes to a vanishing point. Audio reactive.

vec3 palette(float t){
    t = fract(t);
    vec3 c1 = vec3(1.00, 0.78, 0.25);  // warm yellow
    vec3 c2 = vec3(1.00, 0.45, 0.12);  // orange
    vec3 c3 = vec3(0.92, 0.16, 0.24);  // red
    vec3 c4 = vec3(0.68, 0.12, 0.42);  // magenta
    vec3 c5 = vec3(0.40, 0.13, 0.55);  // purple
    if (t < 0.25) return mix(c1, c2, t / 0.25);
    if (t < 0.50) return mix(c2, c3, (t - 0.25) / 0.25);
    if (t < 0.75) return mix(c3, c4, (t - 0.50) / 0.25);
    return mix(c4, c5, (t - 0.75) / 0.25);
}
float hash(float n){ return fract(sin(n * 127.1) * 43758.5453); }

void main(){
    vec2 uv = gl_FragCoord.xy / u_resolution;   // 0..1, y up
    vec3 col = vec3(0.02, 0.02, 0.035);         // near-black base

    float horizon = 0.56;
    float scroll  = u_time * 0.05;              // panels drift sideways
    float barW    = 0.34;                       // ~6 lanes across

    if (uv.y < horizon) {
        // ---- perspective floor (lanes converge toward horizon) ----
        float d = max(horizon - uv.y, 1e-3);
        float depth = 0.16 / d;
        float fx = (uv.x - 0.5) * depth + scroll;
        float lane = floor(fx / barW);
        float frac = fract(fx / barW);
        vec3 lc = palette(lane * 0.137 + 0.1);
        float seam = step(0.97, frac) + step(frac, 0.03);   // dark seams
        float fade = clamp(d * 1.8, 0.0, 1.0);              // darker near horizon
        col = lc * (1.0 - seam) * fade;
        col *= 0.55 + 0.45 * fade;                          // glossy gradient
    } else {
        // ---- standing bars above the horizon ----
        float bx = (uv.x - 0.5) * 1.9 + scroll;
        float lane = floor(bx / barW);
        float frac = fract(bx / barW);
        vec3 lc = palette(lane * 0.137 + 0.1);
        float h = 0.16 + 0.55 * hash(lane * 1.7);
        h += 0.05 * sin(u_time * 0.5 + lane * 1.3);         // gentle bob
        h += 0.12 * u_bass;                                 // audio reactive height
        float topY = horizon + h;
        float seam = step(0.97, frac) + step(frac, 0.03);
        float under = step(uv.y, topY);
        float vshade = mix(1.0, 0.5, (uv.y - horizon) / max(h, 1e-3)); // base bright -> top dark
        col = lc * (1.0 - seam) * under * vshade;
        col += lc * 0.4 * smoothstep(0.012, 0.0, abs(uv.y - topY)) * under; // top highlight
    }

    // glowing horizon line where bars meet floor
    col += palette(0.35 + 0.2 * sin(u_time * 0.2)) * 0.25 * smoothstep(0.03, 0.0, abs(uv.y - horizon));

    // voice reactivity + vignette
    col *= 1.0 + 0.10 * u_rms + 0.12 * u_onset;
    vec2 q = uv - 0.5;
    col *= 1.0 - 0.45 * dot(q, q);

    fragColor = vec4(max(col, 0.0), 1.0);
}
