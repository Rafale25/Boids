from math import ceil
from OpenGL import GL

def resize_boids_buffer(self, new_count):
    self.buffer_boid_tmp.orphan(new_count * 32)

    x = ceil(float(new_count) / self.local_size_x)

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.program['RESIZE']['map_size'] = self.map_size
    self.program['RESIZE']['u_old_boid_count'] = self.boid_count
    self.program['RESIZE']['u_new_boid_count'] = new_count
    self.program['RESIZE'].run(x)

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);

    self.buffer_boid.orphan(new_count * 32)

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.program['COPY']['u_boid_count'] = new_count
    self.program['COPY'].run(x)

    ## TODO: orphan to next power of 2, and never orphan to smaller size
    ## Note: orphan is actually very fast
    self.buffer_cell_count_1.orphan(new_count * 4)
    self.buffer_cell_count_2.orphan(new_count * 4)

    self.boid_count = new_count
