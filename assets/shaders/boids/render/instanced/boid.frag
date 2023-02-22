#version 440 core

flat in int f_color;

out vec4 fragColor;

#include shaders/utils.glsl

void main() {
    fragColor = vec4(unpackColor(f_color), 1.0);
}
