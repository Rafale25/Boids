#version 460 core
#extension GL_NV_mesh_shader : require

layout(local_size_x=8) in;
layout(triangles, max_vertices = 3*8, max_primitives = 8) out;

uniform mat4 u_mvp;

const vec3[] vertices = {
    vec3(0.0, 0.0, 0.0),
    vec3(0.0, 1.0, 0.0),
    vec3(0.0, 0.0, 1.0)
};

void main()
{
    uint thread_id = gl_LocalInvocationID.x;

    vec3 offset_pos = vec3(1.0, 0.0, 0.0) * thread_id;
    uint offset_vertex = 3*thread_id;

    gl_MeshVerticesNV[offset_vertex + 0].gl_Position = u_mvp * vec4(vertices[0] + offset_pos, 1.0);
    gl_MeshVerticesNV[offset_vertex + 1].gl_Position = u_mvp * vec4(vertices[1] + offset_pos, 1.0);
    gl_MeshVerticesNV[offset_vertex + 2].gl_Position = u_mvp * vec4(vertices[2] + offset_pos, 1.0);

    gl_PrimitiveIndicesNV[offset_vertex + 0] = 0;
    gl_PrimitiveIndicesNV[offset_vertex + 1] = 1;
    gl_PrimitiveIndicesNV[offset_vertex + 2] = 2;

    gl_PrimitiveCountNV = 8;
}