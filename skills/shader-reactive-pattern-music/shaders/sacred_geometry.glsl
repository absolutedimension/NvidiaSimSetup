#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec2 center = uv - vec2(0.5);
    float dist = length(center);
    float angle = atan(center.y, center.x);

    // Ultra slow rotation
    float t = u_time * 0.008;

    // Deep dark base
    vec3 base = vec3(0.012, 0.012, 0.03);

    // Concentric circles — ultra thin, ultra dim, slowly expanding
    float circles = 0.0;
    for (int i = 1; i <= 6; i++) {
        float fi = float(i);
        float radius = fi * 0.07 + t * 0.3; // ultra slow expansion
        radius = fract(radius); // loop
        float ring = smoothstep(0.003, 0.0, abs(dist - radius));
        // Fade as they expand
        ring *= smoothstep(0.6, 0.1, radius);
        circles += ring * 0.02;
    }
    vec3 circleColor = vec3(0.04, 0.06, 0.15) * circles;

    // Flower of life pattern — 6 petals, ultra subtle
    float petals = 0.0;
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float petalAngle = fi * 3.14159 / 3.0 + t * 2.0; // ultra slow rotation
        vec2 petalCenter = vec2(cos(petalAngle), sin(petalAngle)) * 0.15;
        float petalDist = length(center - petalCenter);
        float petal = smoothstep(0.003, 0.0, abs(petalDist - 0.15));
        petals += petal * 0.015;
    }
    // Voice makes geometry slightly brighter
    petals *= (1.0 + u_rms * 0.08);
    vec3 petalColor = vec3(0.05, 0.04, 0.12) * petals;

    // Central dot — the seed, gently pulsing
    float seed = smoothstep(0.015, 0.005, dist);
    float seedPulse = 0.8 + 0.2 * sin(u_time * 0.15); // very slow pulse
    seed *= seedPulse * 0.06;
    vec3 seedColor = vec3(0.08, 0.10, 0.25) * seed;

    // Radial lines — 12 spokes, ultra thin, ultra dim
    float spokes = 0.0;
    for (int i = 0; i < 12; i++) {
        float fi = float(i);
        float spokeAngle = fi * 3.14159 / 6.0 + t * 1.5;
        float spoke = smoothstep(0.005, 0.0, abs(sin(angle - spokeAngle)));
        spoke *= smoothstep(0.0, 0.05, dist); // fade near center
        spoke *= smoothstep(0.5, 0.3, dist); // fade at edges
        spokes += spoke * 0.008;
    }
    vec3 spokeColor = vec3(0.03, 0.04, 0.10) * spokes;

    // Compose
    vec3 color = base + circleColor + petalColor + seedColor + spokeColor;

    // Vignette
    color *= 1.0 - dist * 0.3;

    fragColor = vec4(color, 1.0);
}
