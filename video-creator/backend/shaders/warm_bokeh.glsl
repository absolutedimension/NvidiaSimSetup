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

    // Warm dark background
    vec3 bg = mix(vec3(0.04, 0.02, 0.01), vec3(0.02, 0.01, 0.02), uv.y);

    // Bokeh circles (out of focus lights)
    float bokeh = 0.0;
    vec3 bokehColor = vec3(0.0);

    for (int i = 0; i < 15; i++) {
        float fi = float(i);
        float seed = fi * 7.31;

        // Position: slowly drifting
        vec2 pos = vec2(
            hash(vec2(seed, 1.0)) + sin(u_time * 0.1 + seed) * 0.05,
            hash(vec2(seed, 2.0)) + cos(u_time * 0.08 + seed * 1.3) * 0.04
        );

        float d = length(uv - pos);

        // Size: varies per circle, reacts to voice
        float baseSize = 0.05 + hash(vec2(seed, 3.0)) * 0.08;
        float size = baseSize + u_rms * 0.02;

        // Bokeh shape: soft circle with bright edge
        float circle = smoothstep(size, size * 0.7, d);
        float ring = smoothstep(size * 0.95, size, d) * smoothstep(size * 1.05, size, d);
        float b = circle * 0.3 + ring * 0.7;

        // Brightness: pulses gently
        float brightness = 0.3 + 0.2 * sin(u_time * 0.5 + seed * 2.0);
        brightness += u_rms * 0.2;
        b *= brightness;

        // Color: warm palette (amber, gold, soft pink)
        vec3 c;
        float colorSeed = hash(vec2(seed, 4.0));
        if (colorSeed < 0.33) {
            c = vec3(1.0, 0.7, 0.3); // amber
        } else if (colorSeed < 0.66) {
            c = vec3(1.0, 0.85, 0.5); // gold
        } else {
            c = vec3(1.0, 0.6, 0.5); // soft pink
        }

        bokeh += b;
        bokehColor += c * b;
    }

    // Onset: warm flash
    float flash = u_onset * 0.15 * exp(-length(uv - vec2(0.5)) * 3.0);
    vec3 flashColor = vec3(1.0, 0.8, 0.5) * flash;

    // Subtle floating dust
    float dust = 0.0;
    for (int i = 0; i < 20; i++) {
        float fi = float(i);
        vec2 dustPos = vec2(
            fract(fi * 0.127 + u_time * 0.02),
            fract(fi * 0.269 + u_time * 0.01 * (0.5 + hash(vec2(fi))))
        );
        float d = length(uv - dustPos);
        dust += 0.0005 / (d + 0.002);
    }
    vec3 dustColor = vec3(0.8, 0.7, 0.5) * dust;

    vec3 color = bg + bokehColor + flashColor + dustColor;

    fragColor = vec4(color, 1.0);
}
