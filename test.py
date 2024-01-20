# import OpenGL as GL
import OpenGL
# from OpenGL.GL.ARB.draw_elements_base_vertex import *
from OpenGL.GL.NV.mesh_shader import glDrawMeshTasksNV
from OpenGL.GL.NV.mesh_shader import GL_MESH_SHADER_NV, GL_TASK_SHADER_NV

print(glDrawMeshTasksNV)

# print(GL.OpenGL.extensions.has)
print(GL_MESH_SHADER_NV)

# print(OpenGL.GL.GL_VERSION, OpenGL.GL.GL_EXTENSIONS)
print(OpenGL.GL.glGetString(OpenGL.GL.GL_VERSION))

# import glcontext

# backend = glcontext.default_backend()
# ctx = backend(mode='standalone', glversion=330)

# # Ensure method loading works
# ptr = ctx.load('glDrawMeshTasksNV')
# GL_MESH_SHADER_NV = 0x9559
# GL_TASK_SHADER_NV = 0x955A

# print(ptr)
