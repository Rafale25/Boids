import imgui

from math import pi

def gui_newFrame(self):
    imgui.new_frame()

    imgui.begin('Properties', True)

    imgui.text('fps: {:.2f}'.format(self.fps_counter.get_fps()))
    for query, value in self.debug_values.items():
        imgui.text('{}: {:.3f} ms'.format(query, value))

    changed, self.pause = imgui.checkbox('Paused', self.pause)

    changed, state = imgui.checkbox('Fullscreen', self.wnd.fullscreen)
    if changed:
        self.wnd.fullscreen = state

    changed, state = imgui.checkbox('Vsync', self.wnd.vsync)
    if changed:
        self.wnd.vsync = state

    # changed, self.query_enabled = imgui.checkbox('Query', self.query_enabled)

    imgui.new_line()

    changed, self.map_type = imgui.combo(
        'Map Type', self.map_type, ['CubeT', 'Cube', 'Sphere', 'SphereT']
    )

    changed, self.render_mode = imgui.combo(
        'Render mode', self.render_mode, ['geometry_shader', 'mesh_shader']
    )

    changed, self.map_size = imgui.drag_int(
        label='Map Size',
        value=self.map_size,
        change_speed=0.1,
        min_value=5,
        max_value=500
    )

    changed, new_boid_count = imgui.drag_int(
        label='Boid Count',
        value=self.boid_count,
        change_speed=512,
        min_value=self.min_boids,
        max_value=self.max_boids)
    if changed:
        self.resize_boids_buffer(old_count=self.boid_count, new_count=new_boid_count)

    imgui.new_line()

    imgui.text('Cell spacing: {:.2f}'.format(self.cell_spacing))

    imgui.new_line()

    changed, self.boid_size = imgui.drag_float(
        label='boid size',
        value=self.boid_size,
        change_speed=0.001,
        min_value=0.05,
        max_value=1.0,
        format='%.2f')

    changed, self.speed = imgui.drag_float(
        label='Speed',
        value=self.speed,
        change_speed=0.0005,
        min_value=0.001,
        max_value=0.5,
        format='%.3f')

    changed, self.view_distance = imgui.drag_float(
        label='View Distance',
        value=self.view_distance,
        change_speed=0.001,
        min_value=0.0,
        max_value=10.0,
        format='%.2f')

    changed, self.view_angle = imgui.drag_float(
        label='View Angle',
        value=self.view_angle,
        change_speed=0.001,
        min_value=0.0,
        max_value=pi,
        format='%.2f')

    changed, self.separation_force = imgui.drag_float(
        label='Separation Force',
        value=self.separation_force,
        change_speed=0.002,
        min_value=0.0,
        max_value=10.0,
        format='%.2f')

    changed, self.alignment_force = imgui.drag_float(
        label='Aligment Force',
        value=self.alignment_force,
        change_speed=0.002,
        min_value=0.0,
        max_value=10.0,
        format='%.2f')

    changed, self.cohesion_force = imgui.drag_float(
        label='Cohesion Force',
        value=self.cohesion_force,
        change_speed=0.002,
        min_value=0.0,
        max_value=10.0,
        format='%.2f')

    imgui.new_line()
    imgui.begin_group()
    imgui.text('Custom profiles:')
    if (imgui.button('Profile 1')):
        self.set_custom_profile_1()
    imgui.end_group()

    imgui.set_window_font_scale(2.0)
    imgui.end()

def gui_draw(self):
    imgui.render()
    self.imgui.render(imgui.get_draw_data())
