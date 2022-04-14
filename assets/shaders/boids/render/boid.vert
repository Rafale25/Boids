#version 430

uniform mat4 u_projectionMatrix;
uniform mat4 u_viewMatrix;

in vec3 in_position;
in vec3 in_color;

// instanced data
in vec3 in_pos;
in vec3 in_for;

out vec3 f_color;

void main() {
    float yaw = atan(in_for.z, in_for.x);
    float pitch = abs(atan(sqrt(in_for.x*in_for.x + in_for.z*in_for.z), in_for.y)) - 3.141592/2;

    mat3 roty = mat3(
        cos(yaw), 0.0, sin(yaw),
        0.0, 1.0, 0.0,
        -sin(yaw), 0.0, cos(yaw)
    );

    mat3 rotz = mat3(
        cos(pitch), -sin(pitch), 0.0,
        sin(pitch), cos(pitch), 0.0,
        0.0, 0.0, 1.0
    );

    vec3 p = ( (roty * rotz) * vec3(in_position * 0.1) ) + in_pos;
    vec4 pos = u_projectionMatrix * u_viewMatrix * vec4(p, 1.0);

    gl_Position = pos;
    f_color = in_color;
}
