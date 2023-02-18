from OpenGL import GL
from math import ceil, log2, fmod

# import struct
# from time import perf_counter

def parallel_prefix_scan(self):
    group_x = ceil(float(self.boid_count) / 512) ## number of threads to run

    n = self.get_boid_buffer_size()
    self.program['PREFIX_SUM']['SIZE'] = n

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

        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT) ## way better than ctx.finish()

        c = 1 - c

    # if the number of iterations is odd, swap buffers to get the final one
    if iteration_count % 2 == 1:
        self.buffer_cell_count_1, self.buffer_cell_count_2 = self.buffer_cell_count_2, self.buffer_cell_count_1

def update(self, time_since_start, frametime):
    for _, program in self.program.items():
        # if 'u_viewMatrix' in program:
        #     program['u_viewMatrix'].write(self.camera.matrix)
        # if 'u_projectionMatrix' in program:
        #     program['u_projectionMatrix'].write(self.camera.projection.matrix)
        if 'u_mvp' in program:
            program['u_mvp'].write(self.camera.projection.matrix * self.camera.matrix)

    self.program['RESIZE']['u_time'] = fmod(time_since_start, 1.0) ## need modulo or risk of losing float precision

    self.program['BOIDS_VS']['u_boidSize'] = self.boid_size
    self.program['BOIDS_GS']['u_boidSize'] = self.boid_size
    self.program['BORDER']['map_size'] = self.map_size

    if self.pause:
        return

    self.cell_spacing = max(0.5, self.view_distance)

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

    self.program['RESET_CELLS']['boid_count'] = self.boid_count

    self.program['INCREMENT_CELL_COUNTER']['boid_count'] = self.boid_count

    self.program['UPDATE_BOID_CELL_INDEX']['boid_count'] = self.boid_count
    self.program['UPDATE_BOID_CELL_INDEX']['cell_spacing'] = self.cell_spacing

    self.program['ATOMIC_INCREMENT_CELL_COUNT']['boid_count'] = self.boid_count

    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run

    self.buffer_cell_count_1.bind_to_storage_buffer(0)
    with self.query_manager(name='reset (computeShader)', time=True):
        self.program['RESET_CELLS'].run(x)

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT) ## way better than ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    with self.query_manager(name='update boid cell index (computeShader)', time=True):
        self.program['UPDATE_BOID_CELL_INDEX'].run(x)

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT)

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_cell_count_1.bind_to_storage_buffer(1)
    with self.query_manager(name='increment cell counter (computeShader)', time=True):
        self.program['INCREMENT_CELL_COUNTER'].run(x)

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT)

    # t1 = perf_counter()
    self.parallel_prefix_scan()
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT)
    # self.ctx.finish()
    # t2 = perf_counter()
    # self.debug_values['PARALLEL PREFIX SCAN'] = (t2 - t1) * 1000

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)
    with self.query_manager(name='atomic increment cell count (computeShader)', time=True):
        self.program['ATOMIC_INCREMENT_CELL_COUNT'].run(x)

    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT) ## way better than ctx.finish()
    # self.ctx.finish()

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)

    with self.query_manager(name='boid simulation (computeShader)', time=True):
        self.program[self.map_type].run(x, 1, 1)


# data = self.buffer_boid_tmp.read_chunks(chunk_size=8*4, start=0, step=8*4, count=self.boid_count)
# data = struct.iter_unpack('fffIffff', data)
# data = [v for v in data]
# if any(isnan(x[0]) for x in data):
#     print('ISNAN')
#     exit()
# for d in data:
#     print(d)
# print(data)

# data = self.buffer_cell_count_1.read_chunks(chunk_size=1*4, start=0, step=1*4, count=self.boid_count)
# data = struct.iter_unpack('I', data)
# data = [v[0] for v in data]
# print(data)
# print(sum(data))

# is_sorted = all(data[i] <= data[i+1] for i in range(len(data) - 1))
# print("sorted: {}".format(is_sorted))
