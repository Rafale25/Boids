import struct
from math import ceil, floor
from array import array
from time import perf_counter

from OpenGL import GL

# def hash(x, y, z):
#     h = int(x * 92837111) ^ int(y * 689287499) ^ int(z * 283923481)
#     return abs(h)
#
# def cell_xyz(x, y, z, spacing):
#     return floor(x/spacing), floor(y/spacing), floor(z/spacing)


def update(self, time_since_start, frametime):
    for _, program in self.program.items():
        if 'u_viewMatrix' in program:
            program['u_viewMatrix'].write(self.camera.matrix)
        if 'u_projectionMatrix' in program:
            program['u_projectionMatrix'].write(self.camera.projection.matrix)

    if self.pause:
        return


    self.program['BORDER']['map_size'] = self.map_size

    self.program[self.map_type]['boid_count'] = self.boid_count
    self.program[self.map_type]['speed'] = self.speed
    self.program[self.map_type]['map_size'] = self.map_size
    self.program[self.map_type]['view_distance'] = self.view_distance
    self.program[self.map_type]['view_angle'] = self.view_angle

    self.program[self.map_type]['separation_force'] = self.separation_force * 0.01
    self.program[self.map_type]['alignment_force'] = self.alignment_force * 0.03
    self.program[self.map_type]['cohesion_force'] = self.cohesion_force * 0.07

    self.program[self.map_type]['cell_spacing'] = self.cell_spacing
    self.program[self.map_type]['map_size'] = self.map_size
    self.program[self.map_type]['total_grid_cell_count'] = self.total_grid_cell_count

    self.program['SPATIAL_HASH_1']['cell_spacing'] = self.cell_spacing
    self.program['SPATIAL_HASH_1']['boid_count'] = self.boid_count
    self.program['SPATIAL_HASH_1']['total_grid_cell_count'] = self.total_grid_cell_count
    self.program['SPATIAL_HASH_1']['map_size'] = self.map_size

    self.program['SPATIAL_HASH_2']['boid_count'] = self.boid_count

    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run
    # print(x)

    # self.buffer_table.clear()
    # self.buffer_cell_start.clear()


    self.buffer_1.bind_to_storage_buffer(0)
    # self.buffer_table.bind_to_storage_buffer(1)

    with self.query:
        self.program['SPATIAL_HASH_1'].run(x)
    self.debug_values['spatial hash 1'] = self.query.elapsed * 10e-7

    # GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);
    self.ctx.finish() # wait for compute shader to finish


    if self.b:
        self.buffer_1.bind_to_storage_buffer(0)
    else:
        self.buffer_2.bind_to_storage_buffer(0)
    t1 = perf_counter()
    self.sort(program=self.program['BITONIC_MERGE_SORT'], n=self.boid_count)
    # GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);
    t2 = perf_counter()
    t = (t2 - t1) * 1000
    self.debug_values['bitonic merge sort'] = t
    print(f"Took {t:.3f}ms to sort {self.table_size} elements\n")

    self.ctx.finish()

    with self.query:
        self.program['SPATIAL_HASH_2'].run(x)
    self.debug_values['spatial hash 2'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    # self.buffer_table.bind_to_storage_buffer(0)
    # self.buffer_cell_start.bind_to_storage_buffer(1)
    # with self.query:
    #     self.program['SPATIAL_HASH_2'].run(x)
    # self.debug_values['spatial hash 2'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    data = self.buffer_1.read_chunks(chunk_size=32, start=0, step=32, count=self.boid_count)
    data = struct.iter_unpack('ffff fffI', data)
    data = [v[7] for v in data]
    # for v in data:
    #     print(v)
    print(data)
    # print()

    # data = self.buffer_cell_start.read_chunks(chunk_size=4*1, start=0, step=4*1, count=self.table_size)
    # data = struct.iter_unpack('I', data)
    # data = [v[0] for v in data]
    # data = [(i, v[0]) for i, v in enumerate(data)]
    # print(data)


    # is_sorted = all(data[i] <= data[i+1] for i in range(len(data) - 1))
    # print("sorted: {}".format(is_sorted))

    # if len(self.is_sorted_count) >= 100:
    #     print(self.boid_count)
    #     print(f"is_sorted_count: {self.is_sorted_count}")
    #     print("percentage of good sort {}%".format((sum(self.is_sorted_count) / 100.0) * 100))
    #     exit()

    # data = self.buffer_cell_start.read_chunks(chunk_size=4*1, start=0, step=4*1, count=self.table_size)
    # data = struct.iter_unpack('I', data)
    # data = [v[0] for v in data]
    # print(data)

    exit()

    # bind correct boid buffer
    self.buffer_1.bind_to_storage_buffer(self.a)
    self.buffer_2.bind_to_storage_buffer(self.b)
    self.vao_1, self.vao_2 = self.vao_2, self.vao_1
    self.a, self.b = self.b, self.a

    self.buffer_table.bind_to_storage_buffer(2)
    self.buffer_cell_start.bind_to_storage_buffer(3)

    with self.query:
        self.program[self.map_type].run(x, 1, 1)
    self.debug_values['boids compute'] = self.query.elapsed * 10e-7
