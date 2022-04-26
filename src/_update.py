import struct
from math import ceil, floor
from array import array
from time import perf_counter

from OpenGL import GL

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

    self.program[self.map_type]['map_size'] = self.map_size
    self.program[self.map_type]['cell_spacing'] = self.cell_spacing
    self.program[self.map_type]['total_grid_cell_count'] = self.total_grid_cell_count

    self.program['RESET_CELLS']['boid_count'] = self.boid_count

    self.program['INCREMENT_CELL_COUNTER']['boid_count'] = self.boid_count

    self.program['UPDATE_BOID_CELL_INDEX']['boid_count'] = self.boid_count
    self.program['UPDATE_BOID_CELL_INDEX']['cell_spacing'] = self.cell_spacing
    self.program['UPDATE_BOID_CELL_INDEX']['total_grid_cell_count'] = self.total_grid_cell_count
    self.program['UPDATE_BOID_CELL_INDEX']['map_size'] = self.map_size

    self.program['PREFIX_SUM']['boid_count'] = self.boid_count

    self.program['ATOMIC_INCREMENT_CELL_COUNT']['boid_count'] = self.boid_count

    x = ceil(float(self.boid_count) / self.local_size_x) ## number of threads to run

    self.buffer_cell_count.bind_to_storage_buffer(0)
    with self.query:
        self.program['RESET_CELLS'].run(x)
    self.debug_values['RESET_CELLS'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    with self.query:
        self.program['UPDATE_BOID_CELL_INDEX'].run(x)
    self.debug_values['UPDATE_BOID_CELL_INDEX'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_cell_count.bind_to_storage_buffer(1)
    with self.query:
        self.program['INCREMENT_CELL_COUNTER'].run(x)
    self.debug_values['INCREMENT_CELL_COUNTER'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    self.buffer_cell_count.bind_to_storage_buffer(0)
    with self.query:
        self.program['PREFIX_SUM'].run(x)
    self.debug_values['PREFIX_SUM'] = self.query.elapsed * 10e-7

    # self.ctx.finish()

    self.buffer_boid.bind_to_storage_buffer(0)
    self.buffer_boid_tmp.bind_to_storage_buffer(1)
    self.buffer_cell_count.bind_to_storage_buffer(2)
    with self.query:
        self.program['ATOMIC_INCREMENT_CELL_COUNT'].run(x)
    self.debug_values['ATOMIC_INCREMENT_CELL_COUNT'] = self.query.elapsed * 10e-7

    # self.ctx.finish()
    #
    # data = self.buffer_boid_tmp.read_chunks(chunk_size=8*4, start=0, step=8*4, count=self.boid_count)
    # data = struct.iter_unpack('fffIffff', data)
    # data = [v for v in data]
    # for d in data:
    #     print(d)
    # print()

    # data = self.buffer_cell_count.read_chunks(chunk_size=1*4, start=0, step=1*4, count=self.boid_count)
    # data = struct.iter_unpack('I', data)
    # data = [v[0] for v in data]
    # print(data)
    # print(sum(data))

    # is_sorted = all(data[i] <= data[i+1] for i in range(len(data) - 1))
    # print("sorted: {}".format(is_sorted))

    # exit()

    #TODO: THE PREFIX SUM SEEMS TO BE WORKING, THE BOIDS ARE ORDERED IN buffer_boid_tmp, but the simulation is totally broken

    self.buffer_boid_tmp.bind_to_storage_buffer(0)
    self.buffer_boid.bind_to_storage_buffer(1)
    self.buffer_cell_count.bind_to_storage_buffer(2)
    # self.buffer_cell_start.bind_to_storage_buffer(2)

    with self.query:
        self.program[self.map_type].run(x, 1, 1)
    self.debug_values['boids compute'] = self.query.elapsed * 10e-7


# self.program['SPATIAL_HASH_1']['cell_spacing'] = self.cell_spacing
# self.program['SPATIAL_HASH_1']['boid_count'] = self.boid_count
# self.program['SPATIAL_HASH_1']['total_grid_cell_count'] = self.total_grid_cell_count
# self.program['SPATIAL_HASH_1']['map_size'] = self.map_size
#
# self.program['SET_BOIDS_BY_INDEX_LIST']['boid_count'] = self.boid_count
# self.program['SET_CELL_START']['boid_count'] = self.boid_count

# self.buffer_boid.bind_to_storage_buffer(0)
# self.buffer_indices.bind_to_storage_buffer(1)
# with self.query:
#     self.program['SPATIAL_HASH_1'].run(x)
# self.debug_values['spatial hash 1'] = self.query.elapsed * 10e-7


# GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);
# self.ctx.finish() # wait for compute shader to finish

# self.buffer_indices.bind_to_storage_buffer(0)
# t1 = perf_counter()
# self.sort(program=self.program['BITONIC_MERGE_SORT'], n=self.boid_count)
# self.ctx.finish() # wait for compute shader to finish
# t2 = perf_counter()
# self.debug_values['bitonic merge sort'] = (t2 - t1) * 1000
# print(f"Took {t:.3f}ms to sort {self.boid_count} elements\n")


## choose next boid buffer as 1
# self.buffer_boid.bind_to_storage_buffer(0)
# self.buffer_boid_tmp.bind_to_storage_buffer(1)
# self.buffer_indices.bind_to_storage_buffer(2)
# with self.query:
#     self.program['SET_BOIDS_BY_INDEX_LIST'].run(x)
# self.debug_values['set boid at index from indices buffer'] = self.query.elapsed * 10e-7



# self.buffer_indices.bind_to_storage_buffer(0)
# self.buffer_cell_start.bind_to_storage_buffer(1)
# with self.query:
#     self.program['SET_CELL_START'].run(x)
# self.debug_values['spatial hash 2'] = self.query.elapsed * 10e-7

# self.ctx.finish()

"""
Boid algorithm pseudo code

Boid {
    vec3 pos;
    uint cell_index;
    vec3 dir;
    uint padding; // unused
}

Pair {
    uint boid_index;
    uint cell_index;
}

buffer_boid : [Boid]
buffer_boid_tmp : [Boid]
buffer_cell_start : [uint] buffer_pairs : [Pair]


## update loop

bind (buffer_boid, 0)
bind (buffer_pairs, 1)
dispatchCall() -> {
    index = gl_GlobalInvocationID.x
    cell_index = compute boid cell_index

    boid.cell_index = cell_index

    pair.boid_index = index
    pair.cell_index = cell_index
}

bind (buffer_pairs, 0)
dispatchCall() -> {
    sort buffer_pairs by cell_index
}

bind (buffer_boid, 0)
bind (buffer_boid_tmp, 1)
bind (buffer_pairs, 2)
dispatchCall() -> {
    use buffer_pairs to set boids from buffer_boid to their sorted place in buffer_boid_tmp
}  

bind (buffer_boid_tmp, 0)
bind (buffer_cell_start, 1)
dispatchCall() -> {
    find and set cell_start in buffer_cell_start by using boid.cell_start
}

bind (buffer_boid_tmp, 0)
bind (buffer_boid, 1)
bind (buffer_cell_start, 2)
dispatchCall() -> {
    boids computation
}
"""
