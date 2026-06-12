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
    float t = u_time * 0.015;

    // Deep dark base
    vec3 base = vec3(0.01, 0.015, 0.03);

    // Circuit board traces — orthogonal lines, very subtle
    float gridScale = 30.0;
    vec2 gridUV = uv * gridScale;
    vec2 gridID = floor(gridUV);
    vec2 gridF = fract(gridUV);

    // Horizontal traces
    float hLine = smoothstep(0.01, 0.0, abs(gridF.y - 0.5) - 0.48);
    // Vertical traces (only some cells)
    float hasVert = step(0.6, hash(gridID));
    float vLine = smoothstep(0.01, 0.0, abs(gridF.x - 0.5) - 0.48) * hasVert;

    float traces = max(hLine, vLine);

    // Traces glow — ultra dim, barely visible
    float traceGlow = traces * 0.025;

    // Nodes at intersections — tiny dots
    float hasNode = step(0.7, hash(gridID + vec2(100.0)));
    float nodeDist = length(gridF - vec2(0.5));
    float node = smoothstep(0.08, 0.02, nodeDist) * hasNode;

    // Some nodes pulse — ultra slowly
    float nodePulse = sin(t * 3.0 + hash(gridID) * 20.0) * 0.5 + 0.5;
    node *= 0.6 + nodePulse * 0.4;
    // Voice activates nodes slightly
    node *= (1.0 + u_rms * 0.15);

    // Traveling light along traces — a single pulse moving slowly
    float travelX = fract(t * 0.2 + hash(gridID.yy) * 5.0);
    float travelPulse = smoothstep(0.05, 0.0, abs(gridF.x - travelX)) * hLine;
    float travelY = fract(t * 0.15 + hash(gridID.xx + vec2(50.0)) * 5.0);
    float travelPulseV = smoothstep(0.05, 0.0, abs(gridF.y - travelY)) * vLine * hasVert;
    float travel = max(travelPulse, travelPulseV) * 0.06;

    // Colors — deep tech blue/cyan, ultra subtle
    vec3 traceColor = vec3(0.03, 0.06, 0.12) * traceGlow;
    vec3 nodeColor = vec3(0.06, 0.12, 0.25) * node * 0.08;
    vec3 travelColor = vec3(0.08, 0.18, 0.35) * travel;

    // Central focus area — slightly brighter
    float centerDist = length(uv - vec2(0.5));
    float focus = 0.015 / (centerDist + 0.25);
    vec3 focusColor = vec3(0.02, 0.04, 0.10) * focus;

    // Compose
    vec3 color = base + traceColor + nodeColor + travelColor + focusColor;

    // Vignette
    color *= 1.0 - centerDist * 0.3;

    fragColor = vec4(color, 1.0);
}
