#version 450 core

#extension GL_NV_mesh_shader : require

#define PI 3.1415926538
#define PI3 ((2.0 * PI) / 3.0)

struct Boid {
    vec3 pos;
    uint cell_index;
    vec3 dir;
    uint padding;
};

layout(std430, binding=0) restrict readonly buffer buffer_boids {
    Boid boids[];
};

layout(local_size_x = 1) in;
layout(triangles, max_vertices = 4, max_primitives = 4) out;

// Custom vertex output block
layout (location = 0) out PerVertexData
{
    vec4 color;
} v_out[]; // [max_vertices]

mat4 calcScaleMat(float scale) {
    return mat4(
        scale, 0.0, 0.0, 0.0,
        0.0, scale, 0.0, 0.0,
        0.0, 0.0, scale, 0.0,
        0.0, 0.0, 0.0, 1.0
    );
}

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


uniform mat4 u_mvp;
uniform float u_boidSize = 0.12;

const vec4[] vertices = {
    vec4(-1.0, (cos(PI3 * 0.0)) * 0.5, (sin(PI3 * 0.0)) * 0.5, 1.0), // corner 1
    vec4(-1.0, (cos(PI3 * 2.0)) * 0.5, (sin(PI3 * 2.0)) * 0.5, 1.0), // corner 2
    vec4(-1.0, (cos(PI3 * 1.0)) * 0.5, (sin(PI3 * 1.0)) * 0.5, 1.0), // corner 3
    vec4(2.0, 0.0, 0.0, 1.0), // TOP
};

// const int[] colors = {
const vec3[] colors = {
    // back triangle
    vec3(1.0, 0.0, 0.0),

    // side triangle 1
    vec3(0.0, 1.0, 0.0),

    // side triangle 2
    vec3(0.0, 0.0, 1.0),

    // side triangle 3
    vec3(0.0, 1.0, 1.0),
};

void main()
{
    vec3 position = boids[].pos;
    vec3 forward = boids[].dir;

    // computing rotation matrices per vertex instead of per instance is probably what's causing the performance loss
    float yaw = atan(forward.z, forward.x);
    float pitch = abs(atan(sqrt(forward.x*forward.x + forward.z*forward.z), forward.y)) - (PI/2.0);

    mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));
    // rotation_translation_mat = calcScaleMat(u_boidSize) * rotation_translation_mat


    // Vertices position
    gl_MeshVerticesNV[0].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[0];
    gl_MeshVerticesNV[1].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[1];
    gl_MeshVerticesNV[2].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[2];
    gl_MeshVerticesNV[3].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[3];

    // Vertices color
    v_out[0].color = vec4(colors[0], 1.0);
    v_out[1].color = vec4(colors[1], 1.0);
    v_out[2].color = vec4(colors[2], 1.0);
    v_out[3].color = vec4(colors[3], 1.0);

    // Triangle indices
    gl_PrimitiveIndicesNV[0] = 0;
    gl_PrimitiveIndicesNV[1] = 1;
    gl_PrimitiveIndicesNV[2] = 2;

    gl_PrimitiveIndicesNV[3] = 3;
    gl_PrimitiveIndicesNV[4] = 0;
    gl_PrimitiveIndicesNV[5] = 2;

    gl_PrimitiveIndicesNV[6] = 3;
    gl_PrimitiveIndicesNV[7] = 2;
    gl_PrimitiveIndicesNV[8] = 1;

    gl_PrimitiveIndicesNV[9] = 3;
    gl_PrimitiveIndicesNV[10] = 1;
    gl_PrimitiveIndicesNV[11] = 0;

    // Number of triangles
    gl_PrimitiveCountNV = 4;
}