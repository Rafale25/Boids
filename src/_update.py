from math import ceil

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

        x = ceil(self.boid_count / 512)

        # TODO: bind buffer_sorted and buffer_unsorted

        # with self.query:
        # self.program['SPATIAL_HASH'].run(x, 1, 1)
        # self.query_debug_values['Spatial Hash'] = self.query.elapsed * 10e-7

        with self.query:
            self.program[self.map_type].run(x, 1, 1)
        self.query_debug_values['boids compute'] = self.query.elapsed * 10e-7

        self.vao_1, self.vao_2 = self.vao_2, self.vao_1
        self.a, self.b = self.b, self.a
        self.buffer_1.bind_to_storage_buffer(self.a)
        self.buffer_2.bind_to_storage_buffer(self.b)
