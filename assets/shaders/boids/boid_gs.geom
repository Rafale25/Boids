#version 440

#define PI 3.1415926538

layout (points) in;
layout (triangle_strip, max_vertices = 3*4) out;
// layout (invocations = NB_SEGMENTS) in;

// in vec3 g_color[];
in vec3 g_for[];

out vec3 f_color;

uniform mat4 u_projectionMatrix;
uniform mat4 u_viewMatrix;

mat4 calcRotateMat4Y(float radian) {
    return mat4(
        cos(radian), 0.0, sin(radian), 0.0,
        0.0, 1.0, 0.0, 0.0,
        -sin(radian), 0.0, cos(radian), 0.0,
        0.0, 0.0, 0.0, 1.0
    );
}

mat4 calcRotateMat4Z(float radian) {
    return mat4(
        cos(radian), -sin(radian), 0.0, 0.0,
        sin(radian), cos(radian), 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    );
}
mat4 calcTranslateMat4(vec3 v) {
    return mat4(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        v.x, v.y, v.z, 1.0
    );
}

void main() {
    vec3 position = gl_in[0].gl_Position.xyz;
    // int i = gl_InvocationID.x;

    float yaw = atan(g_for[0].z, g_for[0].x);
    float pitch = abs(atan(sqrt(g_for[0].x*g_for[0].x + g_for[0].z*g_for[0].z), g_for[0].y)) - 3.141592/2;

    float pi3 = ((2.0 * PI) / 3.0);
    float radius = 1.2 * 0.1; // forgot to remove *0.1 from vertex shader

    vec4 p1, p2, p3;

    mat4 mvp = u_projectionMatrix * u_viewMatrix;
    mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));

    // back triangle
    p1 = vec4(-radius, (cos(pi3 * 0.0)) * radius*0.5, (sin(pi3 * 0.0)) * radius*0.5, 1.0);
    p2 = vec4(-radius, (cos(pi3 * 2.0)) * radius*0.5, (sin(pi3 * 2.0)) * radius*0.5, 1.0);
    p3 = vec4(-radius, (cos(pi3 * 1.0)) * radius*0.5, (sin(pi3 * 1.0)) * radius*0.5, 1.0);

    f_color = vec3(1.0, 0.0, 0.0);
    gl_Position = mvp * rotation_translation_mat * p1;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p2;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p3;
    EmitVertex();
    EndPrimitive();


    // side triangle 1
    p1 = vec4(radius*2, 0, 0, 1.0);
    p2 = vec4(-radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5, 1.0);
    p3 = vec4(-radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5, 1.0);

    f_color = vec3(0.0, 1.0, 0.0);
    gl_Position = mvp * rotation_translation_mat * p1;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p2;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p3;
    EmitVertex();
    EndPrimitive();

    // side triangle 2
    p1 = vec4(radius*2, 0, 0, 1.0);
    p2 = vec4(-radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5, 1.0);
    p3 = vec4(-radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5, 1.0);

    f_color = vec3(0.0, 0.0, 1.0);
    gl_Position = mvp * rotation_translation_mat * p1;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p2;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p3;
    EmitVertex();
    EndPrimitive();


    // side triangle 3
    p1 = vec4(radius*2, 0, 0, 1.0);
    p2 = vec4(-radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5, 1.0);
    p3 = vec4(-radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5, 1.0);

    f_color = vec3(0.0, 1.0, 1.0);
    gl_Position = mvp * rotation_translation_mat * p1;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p2;
    EmitVertex();
    gl_Position = mvp * rotation_translation_mat * p3;
    EmitVertex();
    EndPrimitive();
}
