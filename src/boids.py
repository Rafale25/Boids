#! /usr/bin/python3

from math import pi, cos, sin
from random import uniform
from array import array
# import numpy
# import time
import struct

# import pyglet
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
    vsync = True
    resource_dir = (Path(__file__) / "../../assets").resolve()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.ctx.gc_mode = "auto"

        self.pause = False

        self.local_size_x = 512 ## smaller value is better when boids are close to each others, and bigger when they are far appart
        self.min_boids = self.local_size_x
        self.max_boids = 2**17#self.local_size_x * 150
        self.map_size = 100
        self.map_type = MapType.MAP_CUBE

        self.boid_count = 2**20 ## must be a power of 2 or it the sort will not work
        self.view_angle = pi/2
        self.view_distance = 2.0
        self.speed = 0.0 #0.050

        self.separation_force = 1.0
        self.alignment_force = 1.0
        self.cohesion_force = 1.0

        self.a, self.b = 0, 1

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


        ## Boid -----
        self.program = {
            'BOIDS':
                self.load_program(
                    vertex_shader='./shaders/boids/boid.vert',
                    fragment_shader='./shaders/boids/boid.frag'),
            'BORDER':
                self.load_program(
                    vertex_shader='./shaders/border/border.vert',
                    fragment_shader='./shaders/border/border.frag'),
            'LINES':
                self.load_program(
                    vertex_shader='./shaders/line/line.vert',
                    fragment_shader='./shaders/line/line.frag'),

            'SPATIAL_HASH_1':
                self.load_compute_shader(
                    path='./shaders/boids/boid_spatialHash_1.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'SPATIAL_HASH_2':
                self.load_compute_shader(
                    path='./shaders/boids/boid_spatialHash_2.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'BITONIC_MERGE_SORT':
                self.load_compute_shader(
                    path='./shaders/boids/bitonic_merge_sort.comp'),
            'SET_BOIDS_BY_INDEX_LIST':
                self.load_compute_shader(
                    path='./shaders/boids/boid_spatialHash_ok.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),

            MapType.MAP_CUBE_T:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'CUBE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_CUBE:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'CUBE': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE_T:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'SPHERE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'SPHERE': 1, 'LOCAL_SIZE_X': self.local_size_x}),
        }

        ## Boids
        ## --------------------------------------------------------
        pi3 = (2*pi / 3)
        radius = 1.2 *0.85
        vertices = array('f',
            [
                # back triangle
                -radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5,
                -radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5,
                -radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5,
                # side triangle 1
                radius*2, 0, 0,
                -radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5,
                -radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5,

                # side triangle 2
                radius*2, 0, 0,
                -radius, (cos(pi3 * 1)) * radius*0.5, (sin(pi3 * 1)) * radius*0.5,
                -radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5,

                # side triangle 3
                radius*2, 0, 0,
                -radius, (cos(pi3 * 2)) * radius*0.5, (sin(pi3 * 2)) * radius*0.5,
                -radius, (cos(pi3 * 0)) * radius*0.5, (sin(pi3 * 0)) * radius*0.5,
            ])

        color = array('f',
        [
            1, 0, 0,
            1, 0, 0,
            1, 0, 0,

            0, 1, 0,
            0, 1, 0,
            0, 1, 0,

            0, 0, 1,
            0, 0, 1,
            0, 0, 1,

            0, 1, 1,
            0, 1, 1,
            0, 1, 1,
        ])

        self.buffer_1 = self.ctx.buffer(data=array('f', self.gen_initial_data(self.boid_count)))
        self.buffer_2 = self.ctx.buffer(reserve=self.buffer_1.size)
        self.ctx.copy_buffer(dst=self.buffer_2, src=self.buffer_1) ##copy buffer_1 into buffer_2
        self.buffer_indices = self.ctx.buffer(reserve=2*4*self.boid_count)

        self.boid_vertices = self.ctx.buffer(data=vertices)
        self.boid_color = self.ctx.buffer(data=color)

        # self.buffer_1.bind_to_storage_buffer(0)
        # self.buffer_2.bind_to_storage_buffer(1)

        # can't do that yet because x4/i not supported by moderngl-window==2.4.0
        # self.vbo = self.ctx.buffer(vertices)
        # self.vao_1 = VAO(mode=moderngl.TRIANGLES)
        # self.vao_1.buffer(self.boid_vertices, '3f', ['in_position'])
        # self.vao_1.buffer(self.boid_color, '3f', ['in_color'])
        # self.vao_1.buffer(self.buffer_1, '3f x4 3f x4/i', ['in_pos', 'in_for'])

        self.vao_1 = self.ctx.vertex_array(
            self.program['BOIDS'],
            [
                (self.boid_vertices, '3f', 'in_position'),
                (self.boid_color, '3f', 'in_color'),
                (self.buffer_1, '3f 1x4 3f 1x4/i', 'in_pos', 'in_for')
            ],
        )

        self.vao_2 = self.ctx.vertex_array(
            self.program['BOIDS'],
            [
                (self.boid_vertices, '3f', 'in_position'),
                (self.boid_color, '3f', 'in_color'),
                (self.buffer_2, '3f 1x4 3f 1x4/i', 'in_pos', 'in_for')
            ],
        )


        ## Spatial Hash
        ## --------------------------------------------------------
        self.cell_spacing = 1.0
        self.total_grid_cell_count = self.boid_count#int(self.map_size**3 / self.cell_spacing)
        self.buffer_cell_start = self.ctx.buffer(reserve=4*self.total_grid_cell_count, dynamic=True)

        ## Compass
        ## --------------------------------------------------------
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


        ## Borders
        ## --------------------------------------------------------
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
    from _update import update, get_previous_boid_buffer, get_next_boid_buffer, swap_boid_buffers

    from _sort import sort

    from _cleanup import cleanup

if __name__ == "__main__":
    MyWindow.run()
