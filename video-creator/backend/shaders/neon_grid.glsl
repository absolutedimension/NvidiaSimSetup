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

    // Perspective grid (vanishing point at center-top)
    vec2 gridUV = uv;
    gridUV.y = pow(gridUV.y, 2.5) * 3.0; // perspective stretch
    gridUV.x = (gridUV.x - 0.5) * (1.0 + gridUV.y * 0.5) + 0.5;

    // Scroll grid forward
    gridUV.y += u_time * 0.3 + u_bass * 0.5;

    // Grid lines
    float gridX = abs(fract(gridUV.x * 10.0) - 0.5);
    float gridY = abs(fract(gridUV.y * 4.0) - 0.5);
    float lineX = smoothstep(0.02, 0.0, gridX);
    float lineY = smoothstep(0.02, 0.0, gridY);
    float grid = max(lineX, lineY);

    // Fade grid toward horizon
    float horizon = smoothstep(0.0, 0.5, uv.y);
    grid *= horizon;

    // Audio-reactive line brightness
    float pulse = 0.4 + u_rms * 0.6;
    grid *= pulse;

    // Neon glow color
    vec3 neonCyan = vec3(0.0, 0.8, 1.0);
    vec3 neonPink = vec3(1.0, 0.1, 0.6);
    vec3 gridColor = mix(neonCyan, neonPink, sin(u_time * 0.5) * 0.5 + 0.5);

    // Bloom effect
    float bloom = grid * 0.5;

    // Background gradient (dark purple to black)
    vec3 bg = mix(vec3(0.02, 0.0, 0.05), vec3(0.0), uv.y);

    // Onset: horizon flash
    float horizonFlash = u_onset * 0.3 * exp(-abs(uv.y - 0.3) * 10.0);

    // Sun/moon at horizon
    float sun = 0.02 / (length(uv - vec2(0.5, 0.25)) + 0.01);
    sun *= 0.05;
    vec3 sunColor = vec3(1.0, 0.5, 0.3) * sun;

    // Scanlines (retro feel)
    float scanline = sin(uv.y * u_resolution.y * 0.5) * 0.02;

    vec3 color = bg + gridColor * (grid + bloom) + sunColor + vec3(horizonFlash);
    color += scanline;

    // Treble sparkles on grid intersections
    if (lineX > 0.5 && lineY > 0.5) {
        color += vec3(u_treble * 0.3);
    }

    fragColor = vec4(color, 1.0);
}
