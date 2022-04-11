import struct
from math import ceil, floor
from array import array
from time import perf_counter

from OpenGL import GL

def get_previous_boid_buffer(self):
    if self.a == 0:
        return self.buffer_1
    return self.buffer_2

def get_next_boid_buffer(self):
    if self.a == 0:
        return self.buffer_2
    return self.buffer_1

def swap_boid_buffers(self):
    self.a, self.b = self.b, self.a

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

    self.program['SET_BOIDS_BY_INDEX_LIST']['boid_count'] = self.boid_count

    self.program['SPATIAL_HASH_2']['boid_count'] = self.boid_count


    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run



    ## choose previous boid buffer
    self.get_previous_boid_buffer().bind_to_storage_buffer(0)
    self.buffer_indices.bind_to_storage_buffer(1)

    with self.query:
        self.program['SPATIAL_HASH_1'].run(x)
    self.debug_values['spatial hash 1'] = self.query.elapsed * 10e-7


    # GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);
    # self.ctx.finish() # wait for compute shader to finish

    self.buffer_indices.bind_to_storage_buffer(0)
    t1 = perf_counter()
    self.sort(program=self.program['BITONIC_MERGE_SORT'], n=self.boid_count)
    self.ctx.finish() # wait for compute shader to finish
    t2 = perf_counter()
    self.debug_values['bitonic merge sort'] = (t2 - t1) * 1000
    # print(f"Took {t:.3f}ms to sort {self.boid_count} elements\n")

    # self.ctx.finish() # wait for compute shader to finish

    # exit()



    ## choose next boid buffer as 1
    ## TODO: simplify the ping pong buffer
    self.get_previous_boid_buffer().bind_to_storage_buffer(0)
    self.get_next_boid_buffer().bind_to_storage_buffer(1)
    self.buffer_indices.bind_to_storage_buffer(2)

    with self.query:
        self.program['SET_BOIDS_BY_INDEX_LIST'].run(x)
    self.debug_values['set boid at index from indices buffer'] = self.query.elapsed * 10e-7

    # self.ctx.finish() # wait for compute shader to finish


    self.swap_boid_buffers()


    self.get_previous_boid_buffer().bind_to_storage_buffer(0)
    self.buffer_cell_start.bind_to_storage_buffer(1)

    with self.query:
        self.program['SPATIAL_HASH_2'].run(x)
    self.debug_values['spatial hash 2'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    # data = self.buffer_2.read_chunks(chunk_size=8*4, start=0, step=8*4, count=self.boid_count)
    # # data = struct.iter_unpack('II', data)
    # data = struct.iter_unpack('fffIffff', data)
    # data = [v for v in data]
    # # print(data[0])
    # for d in data:
    #     print(d)


    # is_sorted = all(data[i] <= data[i+1] for i in range(len(data) - 1))
    # print("sorted: {}".format(is_sorted))

    # if len(self.is_sorted_count) >= 100:
    #     print(self.boid_count)
    #     print(f"is_sorted_count: {self.is_sorted_count}")
    #     print("percentage of good sort {}%".format((sum(self.is_sorted_count) / 100.0) * 100))
    #     exit()

    # exit()



    # bind correct boid buffer
    self.get_previous_boid_buffer().bind_to_storage_buffer(0)
    self.get_next_boid_buffer().bind_to_storage_buffer(1)
    # self.vao_1, self.vao_2 = self.vao_2, self.vao_1
    self.swap_boid_buffers()

    self.buffer_cell_start.bind_to_storage_buffer(2)

    with self.query:
        self.program[self.map_type].run(x, 1, 1)
    self.debug_values['boids compute'] = self.query.elapsed * 10e-7

"""
previous_boid_buffer [x, y, z, cell_id, dx, dy, dz, padding]
next_boid_buffer ^
cell_start [uint]
indices [cell_index, boid_index]

---

bind (previous_boid_buffer, 0)
bind (indices, 1)
- set previous_boid_buffer cell_index
    set boid_index, cell_index of indices

bind (indices, 0)
- sort (indices, by cell_index)

bind (previous_boid_buffer, 0)
bind (next_boid_buffer, 1)
bind (indices, 2)
- use indices to set boid of previous_boid_buffer at sorted index in next_boid_buffer

bind (next_boid_buffer, 0)
bind (cell_start, 1)
- set cell_start using next_boid_buffer

"""
