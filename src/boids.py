#! /usr/bin/python3

from math import pi, cos, sin, ceil
from random import uniform
from array import array
import logging

import moderngl
import imgui

import moderngl_window
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.scene.camera import OrbitCamera
from moderngl_window.opengl.vao import VAO

from pathlib import Path

from utils import *

from _mapType import MapType

class MyWindow(moderngl_window.WindowConfig):
    title = 'Boids Simulation 3D'
    gl_version = (4, 3)
    window_size = (1920, 1080)
    fullscreen = False
    resizable = True
    vsync = False
    resource_dir = (Path(__file__) / "../../assets").resolve()

    # log_level = logging.ERROR

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.ctx.gc_mode = "auto"

        self.pause = False

        self.local_size_x = 512 ## smaller value is better when boids are close to each others, and bigger when they are far appart
        self.min_boids = self.local_size_x
        self.max_boids = 2**20#self.local_size_x * 150
        self.map_size = 140
        self.map_type = MapType.MAP_CUBE

        self.boid_count = 2**22 ## must be a power of 2 or it the sort will not work
        self.view_angle = pi/2
        self.view_distance = 2.0
        self.speed = 0.0 #0.050

        self.separation_force = 1.0
        self.alignment_force = 1.0
        self.cohesion_force = 1.0

        self.camera = OrbitCamera(
            target=(0., 0., 0.),
            radius=self.map_size,
            angles=(-90, -90),
            fov=60.0,
            aspect_ratio=self.wnd.aspect_ratio,
            near=0.1,
            far=1000.0,
        )
        self.camera.mouse_sensitivity = 1.0
        self.camera.zoom_sensitivity = 0.5
        self._shift = False

        ## Debug
        self.fps_counter = FpsCounter()
        self.debug_values = {}
        self.query = self.ctx.query(samples=False, time=True)


        ## ImGui --
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)


        self.program = {
            'BOIDS':
                self.load_program(
                    vertex_shader='./shaders/boids/render/boid.vert',
                    fragment_shader='./shaders/boids/render/boid.frag'),

            'BOIDS_GS':
                self.load_program(
                    vertex_shader='./shaders/boids/render/boid_gs.vert',
                    geometry_shader='./shaders/boids/render/boid_gs.geom',
                    fragment_shader='./shaders/boids/render/boid.frag'),
            'BOIDS_VS':
                self.load_program(
                    vertex_shader='./shaders/boids/render/boid_vs.vert',
                    fragment_shader='./shaders/boids/render/boid.frag'),

            'RESET_CELLS':
                self.load_compute_shader(
                    path='./shaders/boids/compute/reset_cells.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'UPDATE_BOID_CELL_INDEX':
                self.load_compute_shader(
                    path='./shaders/boids/compute/update_boid_cell_index.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'INCREMENT_CELL_COUNTER':
                self.load_compute_shader(
                    path='./shaders/boids/compute/increment_cell_counter.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'PREFIX_SUM':
                self.load_compute_shader(
                    path='./shaders/boids/compute/prefix_sum/prefix_sum.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'ATOMIC_INCREMENT_CELL_COUNT':
                self.load_compute_shader(
                    path='./shaders/boids/compute/atomic_increment_cell_count.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),


            MapType.MAP_CUBE_T:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update.comp',
                    defines={'CUBE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_CUBE:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update.comp',
                    defines={'CUBE': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE_T:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update.comp',
                    defines={'SPHERE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update.comp',
                    defines={'SPHERE': 1, 'LOCAL_SIZE_X': self.local_size_x}),

            'BORDER':
                self.load_program(
                    vertex_shader='./shaders/border/border.vert',
                    fragment_shader='./shaders/border/border.frag'),
            'LINES':
                self.load_program(
                    vertex_shader='./shaders/line/line.vert',
                    fragment_shader='./shaders/line/line.frag'),
        }

        ## Boids --------------------------------------------------------
        self.buffer_boid = self.ctx.buffer(data=array('f', self.gen_initial_data(self.boid_count)))
        self.buffer_boid_tmp = self.ctx.buffer(reserve=self.buffer_boid.size)
        self.ctx.copy_buffer(dst=self.buffer_boid_tmp, src=self.buffer_boid) ##copy buffer_boid into buffer_boid_tmp

        self.cell_spacing = 1.0
        self.total_grid_cell_count = self.boid_count

        self.buffer_cell_count = self.ctx.buffer(reserve=4*self.total_grid_cell_count)
        self.buffer_cell_count_tmp = self.ctx.buffer(reserve=self.buffer_cell_count.size)


        # can't do that yet because x4/i not supported by moderngl-window==2.4.0
        # self.vbo = self.ctx.buffer(vertices)
        # self.vao = VAO(mode=moderngl.TRIANGLES)
        # self.vao.buffer(self.boid_vertices, '3f', ['in_position'])
        # self.vao.buffer(self.boid_color, '3f', ['in_color'])
        # self.vao.buffer(self.buffer_1, '3f x4 3f x4/i', ['in_pos', 'in_for'])

        ## geometry shader
        self.vao_gs = self.ctx.vertex_array(
            self.program['BOIDS_GS'],
            [
                (self.buffer_boid, '3f 1x4 3f 1x4', 'in_pos', 'in_for')
            ],
        )
        ## vertex pulling
        # self.vao_vs = self.ctx.vertex_array(self.program['BOIDS_VS'], [])


        ## Compass --------------------------------------------------------
        vertices = array('f',
        [
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,

            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,

            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0,
        ])

        color = array('f',
        [
            1.0, 0.0, 0.0,
            1.0, 0.0, 0.0,

            0.0, 1.0, 0.0,
            0.0, 1.0, 0.0,

            0.0, 1.0, 1.0,
            0.0, 1.0, 1.0,
        ])

        self.compass = VAO(mode=moderngl.LINES)
        self.compass.buffer(self.ctx.buffer(vertices), '3f', ['in_position'])
        self.compass.buffer(self.ctx.buffer(color), '3f', ['in_color'])


        ## Borders --------------------------------------------------------
        vertices = array('f',
        [
            -0.5, -0.5, -0.5,
            0.5, -0.5, -0.5,

            -0.5, -0.5, 0.5,
            0.5, -0.5, 0.5,

            -0.5, 0.5, 0.5,
            0.5, 0.5, 0.5,

            -0.5, 0.5, -0.5,
            0.5, 0.5, -0.5,

            -0.5, -0.5, -0.5,
            -0.5, 0.5, -0.5,

            -0.5, -0.5, 0.5,
            -0.5, 0.5, 0.5,

            0.5, -0.5, -0.5,
            0.5, 0.5, -0.5,

            0.5, -0.5, 0.5,
            0.5, 0.5, 0.5,

            -0.5, -0.5, -0.5,
            -0.5, -0.5, 0.5,

            -0.5, 0.5, -0.5,
            -0.5, 0.5, 0.5,

            0.5, -0.5, -0.5,
            0.5, -0.5, 0.5,

            0.5, 0.5, -0.5,
            0.5, 0.5, 0.5,
        ])
        color = array('f', [0.30, 0.30, 0.30]*24)

        self.borders = VAO(mode=moderngl.LINES)
        self.borders.buffer(self.ctx.buffer(vertices), '3f', ['in_position'])
        self.borders.buffer(self.ctx.buffer(color), '3f', ['in_color'])

    def gen_initial_data(self, count):
        for _ in range(count):
            yield uniform(-self.map_size/2, self.map_size/2)  # x
            yield uniform(-self.map_size/2, self.map_size/2)  # y
            yield uniform(-self.map_size/2, self.map_size/2)  # z
            yield 0 # "fuck that shit" actually its cell_id now

            dir = random_uniform_vec3()
            yield dir[0]  # fx
            yield dir[1]  # fy
            yield dir[2]  # fz

            yield 42 # fuck that too

    from _resize_buffer import resize_boids_buffer
    from _events import resize, key_event, mouse_position_event, mouse_drag_event, mouse_scroll_event, mouse_press_event, mouse_release_event, unicode_char_entered
    from _custom_profiles import set_custom_profile_1
    from _gui import gui_newFrame, gui_draw

    from _render import render
    from _update import update, parallel_prefix_scan

    from _sort import sort

    from _cleanup import cleanup

if __name__ == "__main__":
    MyWindow.run()
