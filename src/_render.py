import moderngl

from ._mapType import MapType

def render(self, time_since_start, frametime):
    self.fps_counter.update(frametime)
    self.update(time_since_start, frametime)

    self.ctx.clear()
    self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

    # self.ctx.enable_only(moderngl.NOTHING)
    self.compass.render(program=self.program['LINES'])

    self.buffer_boid.bind_to_storage_buffer(0)
    with self.query:
        self.vao_gs.render(mode=moderngl.POINTS, vertices=self.boid_count)
        # self.vao_vs.render(mode=moderngl.TRIANGLES, vertices=self.boid_count*4*3) ## slightly worse than geometry shader approach
    self.debug_values['boids render'] = self.query.elapsed * 10e-7

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
