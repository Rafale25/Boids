from math import ceil
import struct
from array import array

def update(self, time_since_start, frametime):
    for _, program in self.program.items():
        if 'u_viewMatrix' in program:
            program['u_viewMatrix'].write(self.camera.matrix)
        if 'u_projectionMatrix' in program:
            program['u_projectionMatrix'].write(self.camera.projection.matrix)

    if not self.pause:
        self.program['BORDER']['map_size'] = self.map_size

        self.program[self.map_type]['boid_count'] = self.boid_count
        self.program[self.map_type]['speed'] = self.speed
        self.program[self.map_type]['map_size'] = self.map_size
        self.program[self.map_type]['view_distance'] = self.view_distance
        self.program[self.map_type]['view_angle'] = self.view_angle

        self.program[self.map_type]['separation_force'] = self.separation_force * 0.01
        self.program[self.map_type]['alignment_force'] = self.alignment_force * 0.03
        self.program[self.map_type]['cohesion_force'] = self.cohesion_force * 0.07

        # self.program[self.map_type]['SH_size'] = self.SH_size

        self.program['SPATIAL_HASH_1']['SH_size'] = self.SH_size
        self.program['SPATIAL_HASH_1']['map_size'] = self.map_size
        # self.program['SPATIAL_HASH_1']['boid_count'] = self.boid_count

        # self.program['SPATIAL_HASH_2']['SH_size'] = self.SH_size
        # self.program['SPATIAL_HASH_2']['map_size'] = self.map_size
        # self.program['SPATIAL_HASH_2']['boid_count'] = self.boid_count


        self.buffer_cell_id.clear()
        self.buffer_cell_info.clear()
        self.buffer_sorted_id.clear()

        x = ceil(self.boid_count / 512)

        # TODO: bind right buffer depending on self.a and self.b
        self.buffer_1.bind_to_storage_buffer(0)

        self.buffer_cell_id.bind_to_storage_buffer(1)
        self.buffer_cell_info.bind_to_storage_buffer(2)
        self.buffer_sorted_id.bind_to_storage_buffer(3)

        self.program['SPATIAL_HASH_1'].run(x, 1, 1)

        # -------
        SH_size3 = self.SH_size**3

        data = self.buffer_cell_info.read_chunks(chunk_size=4, start=4, step=8, count=SH_size3)
        data = list(struct.iter_unpack('I', data))

        offset = 0
        offset_l = [0] * SH_size3
        for i in range(1, SH_size3):
            offset += data[i - 1][0]
            offset_l[i] = offset
        offset_l = array('I', offset_l)

        self.buffer_cell_info.write_chunks(data=offset_l, start=0, step=8, count=SH_size3)
        # -------
        # self.ctx.finish()

        self.program['SPATIAL_HASH_2'].run(x, 1, 1)

        # with self.query:
            # self.program['SPATIAL_HASH'].run(x, 1, 1)
        # self.query_debug_values['Spatial Hash'] = self.query.elapsed * 10e-7

        # data = self.buffer_cell_id.read()
        # data = list(struct.iter_unpack('I', data))
        # print(data)

        # data = self.buffer_cell_info.read()
        # data = list(struct.iter_unpack('II', data))
        # total_index = sum((y for x,y in data))
        # print(data)
        # print("total:", total_index)
        # print()

        # data = self.buffer_sorted_id.read()
        # data = list(struct.iter_unpack('I', data))
        # print(data)
        # --

        self.buffer_cell_info.bind_to_storage_buffer(2)
        self.buffer_sorted_id.bind_to_storage_buffer(3)

        self.buffer_1.bind_to_storage_buffer(self.a)
        self.buffer_2.bind_to_storage_buffer(self.b)
        self.vao_1, self.vao_2 = self.vao_2, self.vao_1
        self.a, self.b = self.b, self.a

        with self.query:
            self.program[self.map_type].run(x, 1, 1)
        self.query_debug_values['boids compute'] = self.query.elapsed * 10e-7
