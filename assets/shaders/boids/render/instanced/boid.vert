#version 430 core

uniform mat4 u_mvp;
uniform float u_boidSize;

in vec3 in_vertex;
in vec3 in_color;

// instanced data
in vec3 in_pos;
in vec3 in_for;

// out vec3 f_color;
flat out int f_color;

#include shaders/utils.glsl

void main() {
    float yaw = atan(in_for.z, in_for.x);
    float pitch = abs(atan(sqrt(in_for.x*in_for.x + in_for.z*in_for.z), in_for.y)) - 3.141592/2;
    mat4 rotation_translation_mat = calcTranslateMat4(in_pos) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));

    gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vec4(in_vertex, 1.0);
    f_color = packColor(in_color);
}