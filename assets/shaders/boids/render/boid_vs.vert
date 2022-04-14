#version 430

#define PI 3.1415926538

#include shaders/utils.glsl

#include shaders/boids/boid_struct.glsl

layout(std430, binding=0) restrict readonly buffer buffer_boids {
    Boid boids[];
};

uniform mat4 u_projectionMatrix;
uniform mat4 u_viewMatrix;

out vec3 f_color;

void main() {
    const int boid_index = gl_VertexID / (4 * 3); // 0-boid_count
    const int triangle_id = (gl_VertexID / 3) % 4; // 0-3
    const int vertex_id = gl_VertexID % 3; // 0-2

    const vec3 position = boids[boid_index].pos;
    const vec3 forward = boids[boid_index].dir;

    const float yaw = atan(forward.z, forward.x);
    const float pitch = abs(atan(sqrt(forward.x*forward.x + forward.z*forward.z), forward.y)) - 3.141592/2;

    const float pi3 = ((2.0 * PI) / 3.0);
    const float radius = 1.2 * 0.1;

    const mat4 mvp = u_projectionMatrix * u_viewMatrix;
    const mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));

    vec4 p;


    switch (triangle_id) {
        // back triangle
        case 0:

            f_color = vec3(1.0, 0.0, 0.0);
            if (vertex_id == 0)
                p = vec4(-radius, (cos(pi3 * 0.0)) * radius*0.5, (sin(pi3 * 0.0)) * radius*0.5, 1.0);
            else if (vertex_id == 1)
                p = vec4(-radius, (cos(pi3 * 2.0)) * radius*0.5, (sin(pi3 * 2.0)) * radius*0.5, 1.0);
            else if (vertex_id == 2)
                p = vec4(-radius, (cos(pi3 * 1.0)) * radius*0.5, (sin(pi3 * 1.0)) * radius*0.5, 1.0);
            break;

        // side triangle 1
        case 1:
            f_color = vec3(0.0, 1.0, 0.0);
            if (vertex_id == 0)
                p = vec4(radius*2, 0, 0, 1.0);
            else if (vertex_id == 1)
                p = vec4(-radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5, 1.0);
            else if (vertex_id == 2)
                p = vec4(-radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5, 1.0);
            break;

        // side triangle 2
        case 2:
            f_color = vec3(0.0, 0.0, 1.0);
            if (vertex_id == 0)
                p = vec4(radius*2, 0, 0, 1.0);
            else if (vertex_id == 1)
                p = vec4(-radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5, 1.0);
            else if (vertex_id == 2)
                p = vec4(-radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5, 1.0);
            break;

        // side triangle 3
        case 3:
            f_color = vec3(0.0, 1.0, 1.0);
            if (vertex_id == 0)
                p = vec4(radius*2, 0, 0, 1.0);
            else if (vertex_id == 1)
                p = vec4(-radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5, 1.0);
            else if (vertex_id == 2)
                p = vec4(-radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5, 1.0);
            break;
    }

    gl_Position = mvp * rotation_translation_mat * p;
}
