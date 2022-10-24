#version 440 core

flat in int f_color;

out vec4 fragColor;

vec3 unpackColor(int rgb) {
    vec3 color;
    color.r = (rgb >> 16) & 255;
    color.g = (rgb >> 8) & 255;
    color.b = (rgb) & 255;
    return color / 255.0;
}

void main() {
    fragColor = vec4(unpackColor(f_color), 1.0);
}
