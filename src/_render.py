import moderngl

from ._mapType import MapType

from OpenGL.GL import *
from OpenGL.GL.NV.mesh_shader import glDrawMeshTasksNV

from math import ceil

def render(self, time_since_start, frametime):
    self.fps_counter.update(frametime)
    self.update(time_since_start, frametime)

    self.ctx.clear()
    self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST) #moderngl.NOTHING

    self.compass.render(program=self.program['LINES'])


    if self.render_mode == 0:

        self.buffer_boid.bind_to_storage_buffer(0)
        with self.query:
            self.ctx.error
            self.vao_gs.render(mode=moderngl.POINTS, vertices=self.boid_count)
            # self.vao_vs.render(mode=moderngl.TRIANGLES, vertices=self.boid_count*4*3) ## slightly worse than geometry shader approach
        self.debug_values['boids render'] = self.query.elapsed * 10e-7
        self.ctx.error

    elif self.render_mode == 1:

        self.buffer_boid.bind_to_storage_buffer(0)
        glUseProgram(self.meshProgram)

        mvp_loc = glGetUniformLocation(self.meshProgram, "u_mvp")
        boidsize_loc = glGetUniformLocation(self.meshProgram, "u_boidSize")
        glUniformMatrix4fv(mvp_loc, 1, GL_FALSE, self.camera.projection.matrix * self.camera.matrix)
        glUniform1f(boidsize_loc, self.boid_size)

        num_workgroups = ceil(float(self.boid_count) / 16)

        with self.query:
            self.ctx.error
            glDrawMeshTasksNV(0, num_workgroups)
        self.ctx.error

        self.debug_values['boids render'] = self.query.elapsed * 10e-7
        # print(self.query.primitives)

    if self.map_type in (MapType.MAP_CUBE, MapType.MAP_CUBE_T):
        self.borders.render(program=self.program['BORDER'])

    self.ctx.wireframe = False
    self.ctx.disable(moderngl.DEPTH_TEST)
    self.gui_newFrame()
    self.gui_draw()




    # back to default pipeline
    # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    # gl.glUseProgram(0)
    # gl.glBindVertexArray(0)
