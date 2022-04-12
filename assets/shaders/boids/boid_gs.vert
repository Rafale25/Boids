#version 430

in vec3 in_pos;
in vec3 in_for;

out vec3 g_for;

void main() {
    vec4 pos = vec4(in_pos, 1.0);

    gl_Position = pos;
    g_for = in_for;
}
