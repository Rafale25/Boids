#version 440 core

in PerVertexData
{
    flat int color;
} fragIn;

out vec4 fragColor;

vec3 unpackColor(int rgb) {
    vec3 color;
    color.r = (rgb >> 16) & 255;
    color.g = (rgb >> 8) & 255;
    color.b = (rgb) & 255;
    return color / 255.0;
}

void main() {
    fragColor = vec4(unpackColor(fragIn.color), 1.0);
}
