#version 430 core

#define PI 3.1415926538
#define PI3 ((2.0 * PI) / 3.0)

#include shaders/utils.glsl
#include shaders/boids/boid_struct.glsl

layout(std430, binding=0) restrict readonly buffer buffer_boids {
    Boid boids[];
};

// uniform mat4 u_projectionMatrix;
// uniform mat4 u_viewMatrix;
uniform mat4 u_mvp;

uniform float u_boidSize = 0.12;

flat out int f_color;

const vec4[] vertices = {
    vec4(-1.0, 0.5, 0.0, 1.0),
    vec4(-1.0, -0.24999999987863702, -0.43301270196228825, 1.0),
    vec4(-1.0, -0.25000000006068146, 0.4330127018571849, 1.0),

    vec4(2.0, 0.0, 0.0, 1.0),
    vec4(-1.0, 0.5, 0.0, 1.0),
    vec4(-1.0, -0.25000000006068146, 0.4330127018571849, 1.0),

    vec4(2.0, 0.0, 0.0, 1.0),
    vec4(-1.0, -0.25000000006068146, 0.4330127018571849, 1.0),
    vec4(-1.0, -0.24999999987863702, -0.43301270196228825, 1.0),

    vec4(2.0, 0.0, 0.0, 1.0),
    vec4(-1.0, -0.24999999987863702, -0.43301270196228825, 1.0),
    vec4(-1.0, 0.5, 0.0, 1.0)

    // // back triangle
    // vec4(-1.0, (cos(PI3 * 0.0)) * 0.5, (sin(PI3 * 0.0)) * 0.5, 1.0),
    // vec4(-1.0, (cos(PI3 * 2.0)) * 0.5, (sin(PI3 * 2.0)) * 0.5, 1.0),
    // vec4(-1.0, (cos(PI3 * 1.0)) * 0.5, (sin(PI3 * 1.0)) * 0.5, 1.0),

    // // side triangle 1
    // vec4(2.0, 0.0, 0.0, 1.0),
    // vec4(-1.0, (cos(PI3 * 0.0)) * 0.5, (sin(PI3 * 0.0)) * 0.5, 1.0),
    // vec4(-1.0, (cos(PI3 * 1.0)) * 0.5, (sin(PI3 * 1.0)) * 0.5, 1.0),

    // // side triangle 2
    // vec4(2.0, 0.0, 0.0, 1.0),
    // vec4(-1.0, (cos(PI3 * 1.0)) * 0.5, (sin(PI3 * 1.0)) * 0.5, 1.0),
    // vec4(-1.0, (cos(PI3 * 2.0)) * 0.5, (sin(PI3 * 2.0)) * 0.5, 1.0),

    // // side triangle 3
    // vec4(2.0, 0.0, 0.0, 1.0),
    // vec4(-1.0, (cos(PI3 * 2.0)) * 0.5, (sin(PI3 * 2.0)) * 0.5, 1.0),
    // vec4(-1.0, (cos(PI3 * 0.0)) * 0.5, (sin(PI3 * 0.0)) * 0.5, 1.0),
};

const int[] colors = {
// const vec3[] colors = {
    // back triangle
    packColor(vec3(1.0, 0.0, 0.0)),
    // vec3(1.0, 0.0, 0.0),

    // side triangle 1
    packColor(vec3(0.0, 1.0, 0.0)),
    // vec3(0.0, 1.0, 0.0),

    // side triangle 2
    packColor(vec3(0.0, 0.0, 1.0)),
    // vec3(0.0, 0.0, 1.0),

    // side triangle 3
    packColor(vec3(0.0, 1.0, 1.0)),
    // vec3(0.0, 1.0, 1.0),
};

void main() {
    const int boid_index = gl_VertexID / (4 * 3); // [0, boid_count-1]
    const int triangle_id = (gl_VertexID / 3) % 4; // [0, 3]
    const int vertex_id = gl_VertexID % 3; // [0, 2]

    const vec3 position = boids[boid_index].pos;
    const vec3 forward = boids[boid_index].dir;

    // computing rotation matrices per vertex instead of per instance is probably what's causing the performance loss
    const float yaw = atan(forward.z, forward.x);
    const float pitch = abs(atan(sqrt(forward.x*forward.x + forward.z*forward.z), forward.y)) - (PI/2.0);

    // const mat4 mvp = u_projectionMatrix * u_viewMatrix;
    const mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));

    vec4 p;

    switch (triangle_id) {
        // back triangle
        case 0:
            f_color = colors[0];
            p = vertices[0 + vertex_id];
            break;

        // side triangle 1
        case 1:
            f_color = colors[1];
            p = vertices[3 + vertex_id];
            break;

        // side triangle 2
        case 2:
            f_color = colors[2];
            p = vertices[6 + vertex_id];
            break;

        // side triangle 3
        case 3:
            f_color = colors[3];
            p = vertices[9 + vertex_id];
            break;
    }

    gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * p;
}
