import moderngl
import glm

from _mapType import MapType

def render(self, time_since_start, frametime):
    self.fps_counter.update(frametime)
    self.update(time_since_start, frametime)

    self.ctx.clear()
    self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

    # self.ctx.enable_only(moderngl.NOTHING)
    self.compass.render(program=self.program['LINES'])

    with self.query:
        self.vao.render(instances=self.boid_count)
    self.debug_values['boids render'] = self.query.elapsed * 10e-7

    if (self.map_type == MapType.MAP_CUBE or self.map_type == MapType.MAP_CUBE_T):
        self.borders.render(program=self.program['BORDER'])

    self.ctx.wireframe = False
    self.ctx.disable(moderngl.DEPTH_TEST)
    self.gui_newFrame()
    self.gui_draw()


    # back to default pipeline
    # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    # gl.glUseProgram(0)
    # gl.glBindVertexArray(0)
