from array import array
from math import ceil

def resize_boids_buffer(self, new_count):
    self.buffer_boid_tmp.orphan(new_count * 32)

    x = ceil(float(new_count) / self.local_size_x)

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.program['RESIZE']['map_size'] = self.map_size
    self.program['RESIZE']['u_old_boid_count'] = self.boid_count
    self.program['RESIZE']['u_new_boid_count'] = new_count
    self.program['RESIZE'].run(x)

    self.ctx.finish()

    self.buffer_boid.orphan(new_count * 32)

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.program['COPY']['u_boid_count'] = new_count
    self.program['COPY'].run(x)
    ## BUG: random value is too bad in compute shader
    ## TODO: checker si 2 boids ont la même position et direction, si oui, les écarter

    self.ctx.finish()

    ## TODO: orphan to next power of 2, and never orphan to smaller size
    self.buffer_cell_count_1.orphan(new_count * 4)
    self.buffer_cell_count_2.orphan(new_count * 4)

    self.boid_count = new_count


# def resize_boids_buffer(self, new_count):
#     read_size = min(new_count, self.boid_count)
#     bytes1 = self.buffer_boid.read()[0:read_size * 32]
#     bytes2 = self.buffer_boid_tmp.read()[0:read_size * 32]
#     ## orphaning buffer don't garant
#
#     self.buffer_boid.orphan(new_count * 32)
#     self.buffer_boid_tmp.orphan(new_count * 32)
#
#     self.buffer_cell_count_1.orphan(new_count * 4)
#     self.buffer_cell_count_2.orphan(new_count * 4)
#
#     if new_count > self.boid_count:
#         b_new_boids = array('f', self.gen_initial_data(new_count - self.boid_count))
#
#         bytes1 += b_new_boids
#         bytes2 += b_new_boids
#
#     self.buffer_boid.write(bytes1)
#     self.buffer_boid_tmp.write(bytes2)
#
#     self.boid_count = new_count
