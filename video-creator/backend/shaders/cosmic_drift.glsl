#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

// Hash function for pseudo-random
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// Value noise
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// Fractal Brownian Motion
float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 5; i++) {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // Slow rotation
    float angle = u_time * 0.05;
    vec2 rotUV = vec2(
        (uv.x - 0.5) * cos(angle) - (uv.y - 0.5) * sin(angle) + 0.5,
        (uv.x - 0.5) * sin(angle) + (uv.y - 0.5) * cos(angle) + 0.5
    );

    // Nebula clouds
    float n1 = fbm(rotUV * 3.0 + u_time * 0.02);
    float n2 = fbm(rotUV * 5.0 - u_time * 0.03 + vec2(10.0));
    float nebula = n1 * n2;

    // Stars
    float stars = 0.0;
    for (int i = 0; i < 3; i++) {
        vec2 starUV = uv * (20.0 + float(i) * 30.0);
        float h = hash(floor(starUV));
        if (h > 0.985) {
            float d = length(fract(starUV) - 0.5);
            float twinkle = 0.5 + 0.5 * sin(u_time * 2.0 + h * 100.0);
            stars += (0.003 / (d + 0.001)) * twinkle;
        }
    }

    // Voice-reactive brightness
    float voicePulse = u_rms * 0.3;
    float onsetFlash = u_onset * 0.15;

    // Colors
    vec3 deep = vec3(0.02, 0.01, 0.06);
    vec3 purple = vec3(0.15, 0.05, 0.25);
    vec3 blue = vec3(0.05, 0.10, 0.30);

    vec3 nebulaColor = mix(deep, mix(purple, blue, n1), nebula * (0.8 + voicePulse));
    vec3 starColor = vec3(0.8, 0.85, 1.0) * stars;

    vec3 color = nebulaColor + starColor + vec3(onsetFlash * 0.1);

    // Subtle bass-reactive glow at center
    float centerGlow = u_bass * 0.05 / (length(uv - vec2(0.5)) + 0.2);
    color += vec3(0.1, 0.05, 0.2) * centerGlow;

    fragColor = vec4(color, 1.0);
}
