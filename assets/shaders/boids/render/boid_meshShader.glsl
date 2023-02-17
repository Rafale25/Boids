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
// layout(local_size_x = 16) in; // 64 vertices output recommended -> 16 boids
// layout(local_size_x = 32) in; // 32 = size of a nvidia warp
layout(triangles, max_vertices = 4, max_primitives = 4) out;

// Custom vertex output block
layout (location = 0) out PerVertexData
{
    // vec4 color;
    flat int color;
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

int packColor(vec3 color) {
    int packedColor = 0;
    packedColor |= int(color.r*255) << 16;
    packedColor |= int(color.g*255) << 8;
    packedColor |= int(color.b*255);

    return packedColor;
}

uniform mat4 u_mvp;
uniform float u_boidSize = 0.12;

const vec4[] vertices = {
    vec4(-1.0, (cos(PI3 * 0.0)) * 0.5, (sin(PI3 * 0.0)) * 0.5, 1.0), // corner 1
    vec4(-1.0, (cos(PI3 * 2.0)) * 0.5, (sin(PI3 * 2.0)) * 0.5, 1.0), // corner 2
    vec4(-1.0, (cos(PI3 * 1.0)) * 0.5, (sin(PI3 * 1.0)) * 0.5, 1.0), // corner 3
    vec4(2.0, 0.0, 0.0, 1.0), // TOP
};

const int[] colors = {
// const vec3[] colors = {
    // back triangle
    packColor(vec3(1.0, 0.0, 0.0)),

    // side triangle 1
    packColor(vec3(0.0, 1.0, 0.0)),

    // side triangle 2
    packColor(vec3(0.0, 0.0, 1.0)),

    // side triangle 3
    packColor(vec3(0.0, 1.0, 1.0)),
};

void main()
{
    // uint boid_id = gl_GlobalInvocationID.x;
    uint boid_id = gl_WorkGroupID.x;
    // uint id = gl_LocalInvocationID.x;

    vec3 position = boids[boid_id].pos;
    vec3 forward = boids[boid_id].dir;

    float yaw = atan(forward.z, forward.x);
    float pitch = abs(atan(sqrt(forward.x*forward.x + forward.z*forward.z), forward.y)) - (PI/2.0);

    mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));
    // rotation_translation_mat = calcScaleMat(u_boidSize) * rotation_translation_mat;

    // Vertices position
    gl_MeshVerticesNV[0].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[0];
    gl_MeshVerticesNV[1].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[1];
    gl_MeshVerticesNV[2].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[2];
    gl_MeshVerticesNV[3].gl_Position = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize) * vertices[3];

    // Vertices color
    v_out[0].color = colors[0];
    v_out[1].color = colors[1];
    v_out[2].color = colors[2];
    v_out[3].color = colors[3]; // can't have color per triangle with indices, need to find a solution

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