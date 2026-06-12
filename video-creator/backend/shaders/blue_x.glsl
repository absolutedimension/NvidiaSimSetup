#version 330
precision highp float;

// TrigunAI pipeline shader contract
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_rms;     // voice volume
uniform float u_bass;
uniform float u_treble;
uniform float u_onset;   // syllable hits

out vec4 fragColor;

// Two-tone blue "X / bowtie" pattern (matches reference attachment):
//  - top & bottom wedges  -> darker blue   (the central hourglass)
//  - left & right wedges  -> lighter cyan
// The split lines run corner-to-center (the diagonals of the frame).
void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    // distance from center along each axis, normalized to [0,1]
    float ax = abs(uv.x - 0.5) * 2.0;
    float ay = abs(uv.y - 0.5) * 2.0;

    // reference palette
    vec3 lighter = vec3(0.110, 0.624, 0.839);   // ~#1C9FD6  (left/right)
    vec3 darker  = vec3(0.055, 0.431, 0.722);   // ~#0E6EB8  (top/bottom)

    // crisp edge with a touch of anti-aliasing along the diagonals
    float aa = 2.0 / u_resolution.y;
    float e  = smoothstep(-aa, aa, ay - ax);     // 1 in top/bottom wedge
    vec3 col = mix(lighter, darker, e);

    // very subtle life so it doesn't look like a frozen still on video:
    // a faint sheen creeping outward along the diagonals + gentle voice pulse.
    float diag = abs(ay - ax);
    float sheen = 0.04 * smoothstep(0.06, 0.0, abs(diag - fract(u_time * 0.05)));
    col += sheen;
    col *= 1.0 + 0.05 * u_rms + 0.04 * u_onset;

    fragColor = vec4(col, 1.0);
}
