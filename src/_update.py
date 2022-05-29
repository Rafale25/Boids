import struct
from math import ceil, log2, isnan, fmod
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
    group_x = ceil(float(self.boid_count) / 512) ## number of workgroups to run

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

        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

        c = 1 - c

    # if the number of iterations is odd, swap buffers to get the final one
    if iteration_count % 2 == 1:
        self.buffer_cell_count_1, self.buffer_cell_count_2 = self.buffer_cell_count_2, self.buffer_cell_count_1

def parallel_prefix_scan_flag(self):
    group_x = ceil(float(self.boid_count) / 512)

    n = self.get_boid_buffer_size()
    self.program['PREFIX_SUM']['SIZE'] = n

    c = 1
    iteration_count = int(log2(n))
    for i in range(iteration_count):
        if c:
            self.buffer_flag_1.bind_to_storage_buffer(0)
            self.buffer_flag_2.bind_to_storage_buffer(1)
        else:
            self.buffer_flag_1.bind_to_storage_buffer(1)
            self.buffer_flag_2.bind_to_storage_buffer(0)

        self.program['PREFIX_SUM']['n'] = 2**i

        # with self.query:
        self.program['PREFIX_SUM'].run(group_x)
        # self.debug_values[f'PREFIX SUM {i}'] = self.query.elapsed * 10e-7

        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

        c = 1 - c

    # if the number of iterations is odd, swap buffers to get the final one
    if iteration_count % 2 == 1:
        self.buffer_flag_1, self.buffer_flag_2 = self.buffer_flag_2, self.buffer_flag_1

def update(self, time_since_start, frametime):
    for _, program in self.program.items():
        if 'u_viewMatrix' in program:
            program['u_viewMatrix'].write(self.camera.matrix)
        if 'u_projectionMatrix' in program:
            program['u_projectionMatrix'].write(self.camera.projection.matrix)

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

    self.program['FLAG']['SIZE'] = self.boid_count
    self.program['SCATTER']['SIZE'] = self.boid_count

    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run

    self.buffer_cell_count_1.bind_to_storage_buffer(0)
    with self.query:
        self.program['RESET_CELLS'].run(x)
    self.debug_values['RESET_CELLS'] = self.query.elapsed * 10e-7
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    with self.query:
        self.program['UPDATE_BOID_CELL_INDEX'].run(x)
    self.debug_values['UPDATE_BOID_CELL_INDEX'] = self.query.elapsed * 10e-7
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_cell_count_1.bind_to_storage_buffer(1)
    with self.query:
        self.program['INCREMENT_CELL_COUNTER'].run(x)
    self.debug_values['INCREMENT_CELL_COUNTER'] = self.query.elapsed * 10e-7
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);



    # WORK HERE
    self.buffer_cell_count_1.bind_to_storage_buffer(0)
    self.buffer_flag_1.bind_to_storage_buffer(1)
    with self.query:
        self.program['FLAG'].run(x)
    self.debug_values['FLAG'] = self.query.elapsed * 10e-7
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);

    # scan
    self.parallel_prefix_scan_flag()
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);

    maximum = struct.unpack('I', self.buffer_flag_1.read(size=4, offset=self.buffer_flag_1.size - 4))[0] # read last value
    # why the fuck reading for this improves performances

    self.buffer_compact_cells.bind_to_storage_buffer(0)
    self.buffer_flag_1.bind_to_storage_buffer(1)
    self.program['SCATTER'].run(x)
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);

    # data = self.buffer_compact_cells.read_chunks(chunk_size=4, start=0, step=4, count=self.boid_count)
    # data = struct.iter_unpack('I', data)
    # data = [v[0] for v in data]
    # print(data)
    # print(maximum)
    # print()

    """
    flag
    scan (flag)
    get max value (last value)
    compact it (scatter)
    """


    t1 = perf_counter()
    self.parallel_prefix_scan()
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()
    # self.ctx.finish()
    t2 = perf_counter()
    self.debug_values['PARALLEL PREFIX SCAN'] = (t2 - t1) * 1000


    ## at 1.0 view distance, only half of the grid cells have a least 1 boid
    ## at 2.0 view distance, only a quarter (or even less) of the grid cells have a least 1 boid
    ## NOTE: To compact a buffer, i need to do a prefix scan


    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)
    with self.query:
        self.program['ATOMIC_INCREMENT_CELL_COUNT'].run(x)
    self.debug_values['ATOMIC_INCREMENT_CELL_COUNT'] = self.query.elapsed * 10e-7
    GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()
    # self.ctx.finish()

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.buffer_cell_count_1.bind_to_storage_buffer(2)
    self.buffer_compact_cells.bind_to_storage_buffer(3)

    with self.query:
        self.program[self.map_type].run( ceil(float(self.boid_count) / 32) )
    self.debug_values['boids compute'] = self.query.elapsed * 10e-7



# self.ctx.finish()
# data = self.buffer_cell_count_1.read_chunks(chunk_size=4, start=0, step=4, count=self.boid_count)
# data = struct.iter_unpack('I', data)
# data = [v[0] for v in data]
#
# nb = 0
# for i in range(1, len(data)):
#     # if data[i] != data[i - 1]:
#     nb += data[i] != data[i - 1]
# print(nb)



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
