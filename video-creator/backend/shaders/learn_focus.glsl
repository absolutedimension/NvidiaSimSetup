#version 330
precision highp float;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_rms;
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;

out vec4 fragColor;

// Smooth noise
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // smooth interpolation
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // Ultra slow time — everything evolves over 30+ seconds
    float slowTime = u_time * 0.03;
    float medTime = u_time * 0.08;

    // Deep dark base — almost black with hint of navy
    vec3 base = vec3(0.02, 0.02, 0.04);

    // Gentle flowing gradient — like deep water
    float flow = noise(uv * 2.0 + vec2(slowTime, slowTime * 0.7));
    float flow2 = noise(uv * 3.0 + vec2(-slowTime * 0.5, slowTime * 0.3));
    float combined = flow * flow2;

    // Very subtle color — barely visible movement
    vec3 deepBlue = vec3(0.03, 0.05, 0.12);
    vec3 deepPurple = vec3(0.06, 0.03, 0.10);
    vec3 flowColor = mix(deepBlue, deepPurple, combined) * 0.8;

    // Single gentle focus light — very soft, centered
    float focusDist = length(uv - vec2(0.5, 0.45));
    float focusGlow = 0.03 / (focusDist + 0.15);
    // Voice makes focus light breathe — very gently
    float voiceBreath = u_rms * 0.015;
    focusGlow *= (1.0 + voiceBreath);

    vec3 focusColor = vec3(0.06, 0.10, 0.25) * focusGlow;

    // Subtle notebook grid lines — barely visible
    float gridX = smoothstep(0.005, 0.0, abs(fract(uv.x * 20.0) - 0.5) - 0.495);
    float gridY = smoothstep(0.005, 0.0, abs(fract(uv.y * 12.0) - 0.5) - 0.495);
    float grid = max(gridX, gridY) * 0.015;
    vec3 gridColor = vec3(0.10, 0.12, 0.20) * grid;

    // Compose
    vec3 color = base + flowColor + focusColor + gridColor;

    // Ultra subtle vignette
    float vig = 1.0 - focusDist * 0.3;
    color *= vig;

    fragColor = vec4(color, 1.0);
}
