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
    vec2 center = vec2(0.5);
    float dist = length(uv - center);

    // Base breathing glow
    float breathe = 0.5 + 0.5 * sin(u_time * 0.8);
    float glow = 0.015 / (dist + 0.08) * (0.3 + breathe * 0.2);

    // Audio-reactive expanding ring
    float ringRadius = 0.25 + u_rms * 0.2 + u_bass * 0.15;
    float ring = 0.008 / (abs(dist - ringRadius) + 0.005);
    ring *= u_rms * 0.8 + 0.2;

    // Second ring (delayed)
    float ring2Radius = 0.15 + u_rms * 0.15;
    float ring2 = 0.005 / (abs(dist - ring2Radius) + 0.005);
    ring2 *= u_bass * 0.6 + 0.1;

    // Onset flash
    float flash = u_onset * 0.4 * exp(-dist * 4.0);

    // Treble sparkles
    float angle = atan(uv.y - 0.5, uv.x - 0.5);
    float sparkle = u_treble * 0.1 * pow(sin(angle * 8.0 + u_time * 3.0), 8.0);
    sparkle *= smoothstep(0.3, 0.5, dist) * smoothstep(0.7, 0.5, dist);

    // Color mixing
    vec3 blue = vec3(0.08, 0.20, 0.85);
    vec3 purple = vec3(0.55, 0.15, 0.85);
    vec3 white = vec3(0.9, 0.9, 1.0);

    vec3 baseColor = mix(blue, purple, u_bass * 0.7 + sin(u_time * 0.3) * 0.3);
    vec3 color = baseColor * (glow + ring + ring2) + white * (flash + sparkle);

    // Subtle vignette
    float vignette = 1.0 - dist * 0.5;
    color *= vignette;

    fragColor = vec4(color, 1.0);
}
