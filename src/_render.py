import moderngl
import glm

from src._mapType import MapType

def render(self, time_since_start, frametime):
    self.update(time_since_start, frametime)

    self.ctx.clear()
    self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

    for _, program in self.program.items():
        if 'u_viewMatrix' in program:
            program['u_viewMatrix'].write(self.camera.matrix)
        if 'u_projectionMatrix' in program:
            program['u_projectionMatrix'].write(self.camera.projection.matrix)

    self.compass.render(program=self.program['LINES'])
    self.vao_1.render(instances=self.boid_count)

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
