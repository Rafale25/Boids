import struct
from math import ceil, log2
from time import perf_counter

from OpenGL import GL

# def program_run(self, program, x=0, y=1, z=1, debug=None):
#     if self.query_enabled:
#         with self.query:
#             program.run(x, y, z)
#         self.debug_values[debug] = self.query.elapsed * 10e-7
#     else:
#         program.run(x, y, z)
#         self.debug_values[debug] = 0

def parallel_prefix_scan(self):
    n = self.get_boid_buffer_size()#self.boid_count
    self.program['PREFIX_SUM']['SIZE'] = n

    group_x = ceil(float(n) / 512) ## number of threads to run

    c = 1
    iteration_count = int(log2(n))
    for i in range(iteration_count):
        if c:
            self.buffer_cell_count_1.bind_to_storage_buffer(0)
            self.buffer_cell_count_2.bind_to_storage_buffer(1)
        else:
            self.buffer_cell_count_1.bind_to_storage_buffer(1)
            self.buffer_cell_count_2.bind_to_storage_buffer(0)

        self.program['PREFIX_SUM']['n'] = 2**i

        # with self.query:
        self.program['PREFIX_SUM'].run(group_x)
        # self.debug_values[f'PREFIX SUM {i}'] = self.query.elapsed * 10e-7

        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

        c = 1 - c

    # if the number of iterations is odd, swap buffers to get the final one
    if iteration_count % 2 == 1:
        self.buffer_cell_count_1, self.buffer_cell_count_2 = self.buffer_cell_count_2, self.buffer_cell_count_1

def update(self, time_since_start, frametime):
    for _, program in self.program.items():
        if 'u_viewMatrix' in program:
            program['u_viewMatrix'].write(self.camera.matrix)
        if 'u_projectionMatrix' in program:
            program['u_projectionMatrix'].write(self.camera.projection.matrix)

    if self.pause:
        return

    self.cell_spacing = max(0.5, self.view_distance)

    self.program['BOIDS_VS']['u_boidSize'] = self.boid_size
    self.program['BORDER']['map_size'] = self.map_size

    self.program[self.map_type]['boid_count'] = self.boid_count
    self.program[self.map_type]['speed'] = self.speed
    self.program[self.map_type]['map_size'] = self.map_size
    self.program[self.map_type]['view_distance'] = self.view_distance
    self.program[self.map_type]['view_angle'] = self.view_angle

    self.program[self.map_type]['separation_force'] = self.separation_force * 0.01
    self.program[self.map_type]['alignment_force'] = self.alignment_force * 0.03
    self.program[self.map_type]['cohesion_force'] = self.cohesion_force * 0.07

    self.program[self.map_type]['map_size'] = self.map_size
    self.program[self.map_type]['cell_spacing'] = self.cell_spacing

    self.program['BOIDS_GS']['u_boidSize'] = self.boid_size

    self.program['RESET_CELLS']['boid_count'] = self.boid_count

    self.program['INCREMENT_CELL_COUNTER']['boid_count'] = self.boid_count

    self.program['UPDATE_BOID_CELL_INDEX']['boid_count'] = self.boid_count
    self.program['UPDATE_BOID_CELL_INDEX']['cell_spacing'] = self.cell_spacing

    self.program['ATOMIC_INCREMENT_CELL_COUNT']['boid_count'] = self.boid_count

    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run

    self.buffer_cell_count_1.bind_to_storage_buffer(0)
    # with self.query:
    self.program['RESET_CELLS'].run(x)
    # self.debug_values['RESET_CELLS'] = self.query.elapsed * 10e-7

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    # with self.query:
    self.program['UPDATE_BOID_CELL_INDEX'].run(x)
    # self.debug_values['UPDATE_BOID_CELL_INDEX'] = self.query.elapsed * 10e-7
    # self.program_run(self.program['UPDATE_BOID_CELL_INDEX'], x=x, debug='UPDATE_BOID_CELL_INDEX')

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_cell_count_1.bind_to_storage_buffer(1)
    # with self.query:
    self.program['INCREMENT_CELL_COUNTER'].run(x)
    # self.debug_values['INCREMENT_CELL_COUNTER'] = self.query.elapsed * 10e-7

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

    # t1 = perf_counter()
    self.parallel_prefix_scan()
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()
    # self.ctx.finish()
    # t2 = perf_counter()
    # self.debug_values['PARALLEL PREFIX SCAN'] = (t2 - t1) * 1000


    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)
    # with self.query:
    self.program['ATOMIC_INCREMENT_CELL_COUNT'].run(x)
    # self.debug_values['ATOMIC_INCREMENT_CELL_COUNT'] = self.query.elapsed * 10e-7

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()
    # self.ctx.finish()

    # data = self.buffer_boid_tmp.read_chunks(chunk_size=8*4, start=0, step=8*4, count=self.boid_count)
    # data = struct.iter_unpack('fffIffff', data)
    # data = [v for v in data]
    # for d in data:
    #     print(d)

    # data = self.buffer_cell_count_1.read_chunks(chunk_size=1*4, start=0, step=1*4, count=self.boid_count)
    # data = struct.iter_unpack('I', data)
    # data = [v[0] for v in data]
    # print(data)
    # print(sum(data))

    # is_sorted = all(data[i] <= data[i+1] for i in range(len(data) - 1))
    # print("sorted: {}".format(is_sorted))

    # exit()

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)

    # with self.query:
    self.program[self.map_type].run(x, 1, 1)
    # self.debug_values['boids compute'] = self.query.elapsed * 10e-7
