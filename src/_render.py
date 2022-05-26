import moderngl
import glm

from mapType import MapType

def render(self, time_since_start, frametime):
    self.fps_counter.update(frametime)
    self.update(time_since_start, frametime)

    self.ctx.clear()
    self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

    self.compass.render(program=self.program['LINES'])

    self.buffer_boid.bind_to_storage_buffer(0)
    with self.query:
        # self.vao_vs.render(mode=moderngl.TRIANGLES, vertices=self.boid_count*4*3) ## slightly worse than geometry shader approach (on nvidia)
        self.vao_gs.render(mode=moderngl.POINTS, vertices=self.boid_count)
    self.debug_values['boids render'] = self.query.elapsed * 10e-7

    if self.map_type in (MapType.MAP_CUBE, MapType.MAP_CUBE_T):
        self.borders.render(program=self.program['BORDER'])

    self.ctx.wireframe = False
    self.ctx.disable(moderngl.DEPTH_TEST)
    self.gui_newFrame()
    self.gui_draw()
