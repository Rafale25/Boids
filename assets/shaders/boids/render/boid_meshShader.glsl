#version 460 core
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

#define N_BOIDS 16 // number of boid per work group
layout(local_size_x = N_BOIDS) in; // 64 vertices output recommended -> 16 boids // // 32 = size of a nvidia warp
layout(triangles, max_vertices = 4*N_BOIDS, max_primitives = 4*N_BOIDS) out;

// Custom vertex output block
layout (location = 0) out PerVertexData
{
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
    // if (gl_GlobalInvocationID.x > 16) // boid_count ## ADD THIS
    //     return;

    uint boid_id = gl_GlobalInvocationID.x;
    uint thread_id = gl_LocalInvocationID.x;

    vec3 position = boids[boid_id].pos;
    vec3 forward = boids[boid_id].dir;

    float yaw = atan(forward.z, forward.x);
    float pitch = abs(atan(sqrt(forward.x*forward.x + forward.z*forward.z), forward.y)) - (PI/2.0);
    mat4 rotation_translation_mat = calcTranslateMat4(position) * (calcRotateMat4Y(yaw) * calcRotateMat4Z(pitch));
    mat4 mvp_rot_scale = u_mvp * rotation_translation_mat * calcScaleMat(u_boidSize);

    uint offset_vertex = thread_id * 4;
    uint offset_index = thread_id * 12;

    // Vertices position
    gl_MeshVerticesNV[offset_vertex + 0].gl_Position = mvp_rot_scale * vertices[0];
    gl_MeshVerticesNV[offset_vertex + 1].gl_Position = mvp_rot_scale * vertices[1];
    gl_MeshVerticesNV[offset_vertex + 2].gl_Position = mvp_rot_scale * vertices[2];
    gl_MeshVerticesNV[offset_vertex + 3].gl_Position = mvp_rot_scale * vertices[3];

    // Vertices color
    v_out[offset_vertex + 0].color = colors[0];
    v_out[offset_vertex + 1].color = colors[2];
    v_out[offset_vertex + 2].color = colors[1];
    v_out[offset_vertex + 3].color = colors[3];

    // Triangle indices
    gl_PrimitiveIndicesNV[offset_index + 0] = offset_vertex + 1;
    gl_PrimitiveIndicesNV[offset_index + 1] = offset_vertex + 2;
    gl_PrimitiveIndicesNV[offset_index + 2] = offset_vertex + 0;

    gl_PrimitiveIndicesNV[offset_index + 3] = offset_vertex + 3;
    gl_PrimitiveIndicesNV[offset_index + 4] = offset_vertex + 0;
    gl_PrimitiveIndicesNV[offset_index + 5] = offset_vertex + 2;

    gl_PrimitiveIndicesNV[offset_index + 6] = offset_vertex + 3;
    gl_PrimitiveIndicesNV[offset_index + 7] = offset_vertex + 2;
    gl_PrimitiveIndicesNV[offset_index + 8] = offset_vertex + 1;

    gl_PrimitiveIndicesNV[offset_index + 9] = offset_vertex + 1;
    gl_PrimitiveIndicesNV[offset_index + 10] = offset_vertex + 0;
    gl_PrimitiveIndicesNV[offset_index + 11] = offset_vertex + 3;

    // Number of triangles
    gl_PrimitiveCountNV = 4*N_BOIDS;
}