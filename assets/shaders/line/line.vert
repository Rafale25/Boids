#version 430

uniform mat4 u_projectionMatrix;
uniform mat4 u_viewMatrix;

in vec3 in_position;
in vec3 in_color;

out vec3 f_color;

void main()
{
    vec4 pos = u_projectionMatrix * u_viewMatrix * vec4(in_position, 1.0);

    gl_Position = pos;
    f_color = in_color;
}
