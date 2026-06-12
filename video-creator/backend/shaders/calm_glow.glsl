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

    // Multiple soft orbs drifting slowly
    float light = 0.0;
    for (int i = 0; i < 5; i++) {
        float fi = float(i);
        vec2 orbPos = vec2(
            0.3 + 0.4 * sin(u_time * 0.15 + fi * 1.3),
            0.3 + 0.4 * cos(u_time * 0.12 + fi * 1.7)
        );
        float d = length(uv - orbPos);
        float size = 0.08 + u_rms * 0.04 + fi * 0.01;
        light += size / (d * d + 0.01);
    }
    light *= 0.003;

    // Gentle color shift over time
    float hueShift = sin(u_time * 0.1) * 0.5 + 0.5;
    vec3 warm = vec3(0.15, 0.08, 0.25);
    vec3 cool = vec3(0.05, 0.12, 0.30);
    vec3 baseColor = mix(warm, cool, hueShift);

    // Voice adds brightness
    float voiceGlow = u_rms * 0.3;

    // Subtle onset response (gentle, not harsh)
    float gentleOnset = u_onset * 0.1 * (1.0 - length(uv - vec2(0.5)) * 1.5);

    vec3 color = baseColor + vec3(light + voiceGlow + gentleOnset);

    // Soft grain for texture
    float grain = fract(sin(dot(uv, vec2(12.9898, 78.233)) + u_time) * 43758.5453);
    color += grain * 0.01;

    fragColor = vec4(color, 1.0);
}
