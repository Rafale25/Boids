#version 440 core

#define PI 3.1415926538
#define PI3 ((2.0 * PI) / 3.0)

layout (points) in;
layout (triangle_strip, max_vertices = 3*4) out;

in vec3 g_for[];

// flat out vec3 f_color;
flat out int f_color;

// uniform mat4 u_projectionMatrix;
// uniform mat4 u_viewMatrix;
uniform mat4 u_mvp;

uniform float u_boidSize = 0.12;

#include shaders/utils.glsl

void main() {
    const vec3 position = gl_in[0].gl_Position.xyz;

    const float yaw = atan(g_for[0].z, g_for[0].x);
    const float pitch = abs(atan(sqrt(g_for[0].x*g_for[0].x + g_for[0].z*g_for[0].z), g_for[0].y)) - 3.141592/2;

    // const float PI3 = ((2.0 * PI) / 3.0);

    const mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));
    const mat4 mvp = u_mvp * rotation_translation_mat;

    vec4 p1, p2, p3;

    // back triangle
    p1 = vec4(-u_boidSize, (cos(PI3 * 0.0)) * u_boidSize*0.5, (sin(PI3 * 0.0)) * u_boidSize*0.5, 1.0);
    p2 = vec4(-u_boidSize, (cos(PI3 * 2.0)) * u_boidSize*0.5, (sin(PI3 * 2.0)) * u_boidSize*0.5, 1.0);
    p3 = vec4(-u_boidSize, (cos(PI3 * 1.0)) * u_boidSize*0.5, (sin(PI3 * 1.0)) * u_boidSize*0.5, 1.0);

    f_color = packColor(vec3(1.0, 0.0, 0.0));
    gl_Position = mvp * p1;
    EmitVertex();
    gl_Position = mvp * p2;
    EmitVertex();
    gl_Position = mvp * p3;
    EmitVertex();
    EndPrimitive();


    // side triangle 1
    p1 = vec4(u_boidSize*2, 0, 0, 1.0);
    p2 = vec4(-u_boidSize, (cos(PI3 * 0)) * u_boidSize*0.5, (sin(PI3 * 0)) * u_boidSize*0.5, 1.0);
    p3 = vec4(-u_boidSize, (cos(PI3 * 1)) * u_boidSize*0.5, (sin(PI3 * 1)) * u_boidSize*0.5, 1.0);

    f_color = packColor(vec3(0.0, 1.0, 0.0));
    gl_Position = mvp * p1;
    EmitVertex();
    gl_Position = mvp * p2;
    EmitVertex();
    gl_Position = mvp * p3;
    EmitVertex();
    EndPrimitive();

    // side triangle 2
    p1 = vec4(u_boidSize*2, 0, 0, 1.0);
    p2 = vec4(-u_boidSize, (cos(PI3 * 1)) * u_boidSize*0.5, (sin(PI3 * 1)) * u_boidSize*0.5, 1.0);
    p3 = vec4(-u_boidSize, (cos(PI3 * 2)) * u_boidSize*0.5, (sin(PI3 * 2)) * u_boidSize*0.5, 1.0);

    f_color = packColor(vec3(0.0, 0.0, 1.0));
    gl_Position = mvp * p1;
    EmitVertex();
    gl_Position = mvp * p2;
    EmitVertex();
    gl_Position = mvp * p3;
    EmitVertex();
    EndPrimitive();


    // side triangle 3
    p1 = vec4(u_boidSize*2, 0, 0, 1.0);
    p2 = vec4(-u_boidSize, (cos(PI3 * 2)) * u_boidSize*0.5, (sin(PI3 * 2)) * u_boidSize*0.5, 1.0);
    p3 = vec4(-u_boidSize, (cos(PI3 * 0)) * u_boidSize*0.5, (sin(PI3 * 0)) * u_boidSize*0.5, 1.0);

    f_color = packColor(vec3(0.0, 1.0, 1.0));
    gl_Position = mvp * p1;
    EmitVertex();
    gl_Position = mvp * p2;
    EmitVertex();
    gl_Position = mvp * p3;
    EmitVertex();
    EndPrimitive();
}
