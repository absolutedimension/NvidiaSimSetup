#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

float noise(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * f * (f * (f * 6.0 - 15.0) + 10.0); // quintic smooth
    float a = noise(i);
    float b = noise(i + vec2(1.0, 0.0));
    float c = noise(i + vec2(0.0, 1.0));
    float d = noise(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * smoothNoise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // Ultra slow time — ocean moves very gradually
    float t = u_time * 0.01;

    // Deep ocean base
    vec3 deep = vec3(0.01, 0.02, 0.05);

    // Layered water caustics — ultra slow undulation
    float caustic1 = fbm(uv * 4.0 + vec2(t, t * 0.7));
    float caustic2 = fbm(uv * 6.0 + vec2(-t * 0.5, t * 0.3));
    float caustics = caustic1 * caustic2;

    // Caustic light patterns — very dim
    vec3 causticColor = vec3(0.03, 0.06, 0.12) * caustics * 0.5;

    // Gentle wave motion across the screen — horizontal ripple
    float wave = sin(uv.x * 8.0 + t * 5.0 + uv.y * 3.0) * 0.5 + 0.5;
    wave *= sin(uv.x * 12.0 - t * 3.0 + uv.y * 5.0) * 0.5 + 0.5;
    vec3 waveColor = vec3(0.02, 0.04, 0.10) * wave * 0.15;

    // Light shaft from above — very gentle, slightly off-center
    float shaftX = 0.45 + sin(t * 2.0) * 0.03; // ultra slow drift
    float shaft = smoothstep(0.15, 0.0, abs(uv.x - shaftX));
    shaft *= smoothstep(1.0, 0.0, uv.y); // stronger at top
    shaft *= 0.04;
    // Voice makes shaft gently brighten
    shaft *= (1.0 + u_rms * 0.1);
    vec3 shaftColor = vec3(0.04, 0.08, 0.15) * shaft;

    // Floating particles — like plankton, ultra slow rise
    float particles = 0.0;
    for (int i = 0; i < 10; i++) {
        float fi = float(i);
        vec2 pPos = vec2(
            noise(vec2(fi * 7.13, 1.0)),
            fract(noise(vec2(fi * 3.71, 2.0)) + t * (1.0 + noise(vec2(fi)) * 0.5))
        );
        float d = length(uv - pPos);
        particles += smoothstep(0.003, 0.001, d) * 0.15;
    }
    vec3 particleColor = vec3(0.06, 0.10, 0.20) * particles;

    // Compose
    vec3 color = deep + causticColor + waveColor + shaftColor + particleColor;

    // Depth fog — darker at bottom
    color *= 0.7 + 0.3 * (1.0 - uv.y);

    // Subtle vignette
    float vig = 1.0 - length(uv - vec2(0.5)) * 0.25;
    color *= vig;

    fragColor = vec4(color, 1.0);
}
