#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // Ultra slow time
    float t = u_time * 0.02;

    // Deep dark background
    vec3 base = vec3(0.015, 0.015, 0.035);

    // Flowing streams — like knowledge currents moving upward, ultra slow
    float stream = 0.0;
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float x = 0.15 + fi * 0.14;
        // Each stream has slight wave
        float wave = sin(uv.y * 3.0 + t * (0.5 + fi * 0.1) + fi * 2.0) * 0.02;
        float d = abs(uv.x - x - wave);
        // Stream width reacts very gently to voice
        float width = 0.008 + u_rms * 0.002;
        stream += smoothstep(width, 0.0, d) * 0.04;
    }

    // Stream color — subtle blue/cyan, ultra dim
    vec3 streamColor = vec3(0.04, 0.08, 0.18) * stream;

    // Floating dots — like data points drifting upward, very slow
    float dots = 0.0;
    for (int i = 0; i < 15; i++) {
        float fi = float(i);
        float seed = fi * 3.17;
        vec2 dotPos = vec2(
            hash(vec2(seed, 1.0)),
            fract(hash(vec2(seed, 2.0)) + t * (0.3 + hash(vec2(seed, 3.0)) * 0.2))
        );
        float d = length(uv - dotPos);
        float size = 0.002 + u_rms * 0.0005;
        dots += smoothstep(size + 0.001, size, d) * 0.3;
    }
    vec3 dotColor = vec3(0.08, 0.15, 0.30) * dots;

    // Central soft glow — knowledge center
    float centerDist = length(uv - vec2(0.5, 0.5));
    float centerGlow = 0.02 / (centerDist + 0.2);
    // Voice makes it breathe — almost imperceptible
    centerGlow *= (1.0 + u_rms * 0.08);

    vec3 glowColor = vec3(0.04, 0.06, 0.15) * centerGlow;

    // Compose
    vec3 color = base + streamColor + dotColor + glowColor;

    // Subtle vignette
    color *= 1.0 - centerDist * 0.25;

    fragColor = vec4(color, 1.0);
}
