#! /usr/bin/python3

import time

from math import pi, cos, sin, ceil
from random import uniform
from array import array

import pyglet
import moderngl
import imgui
import glm

from imgui.integrations.pyglet import PygletProgrammablePipelineRenderer

from utils import *

from src._mapType import MapType

# class BoidConfig:
#     Max = 100_000
#     N = 1000
#
# class MapConfig:
#     size = 25
#     type = MapType.MAP_CUBE

class MyWindow(pyglet.window.Window):
    def __init__(self, max_boids, map_size, *args, **kwaargs):
        super(MyWindow, self).__init__(*args, **kwaargs)

        self.ctx = moderngl.create_context(require=430)
        # self.ctx.gc_mode = "auto"

        pyglet.clock.schedule_interval(self.update, 1.0 / 144.0)

        self.pause = False

        self.max_boids = max_boids
        self.map_size = map_size
        self.map_type = MapType.MAP_CUBE;

        self.boid_count = 1000
        self.view_angle = pi/2
        self.view_distance = 2.0
        self.speed = 0.015;

        self.separation_force = 1.0
        self.alignment_force = 1.0
        self.cohesion_force = 1.0

        self.camera_z = -8.0
        self.camera_rotx = 0.0
        self.camera_roty = 0.0

        self.a = 0
        self.b = 1

        # ImGui --
        imgui.create_context()
        self.impl = PygletProgrammablePipelineRenderer(self)

        # Boid -----
        self.program_boids = self.ctx.program(
            vertex_shader=read_file("shaders/boid.vert"),
            fragment_shader=read_file("shaders/boid.frag"))

        # print(MapType.MAP_CUBE_T)
        # exit()

        # update boids program -----
        self.program_update_boids = [None]*4
        self.program_update_boids[MapType.MAP_CUBE_T] = self.ctx.compute_shader(read_file("shaders/boids_compute/boid_update_cubeT.comp"));
        self.program_update_boids[MapType.MAP_CUBE] = self.ctx.compute_shader(read_file("shaders/boids_compute/boid_update_cube.comp"));
        self.program_update_boids[MapType.MAP_SPHERE_T] = self.ctx.compute_shader(read_file("shaders/boids_compute/boid_update_sphereT.comp"));
        self.program_update_boids[MapType.MAP_SPHERE] = self.ctx.compute_shader(read_file("shaders/boids_compute/boid_update_sphere.comp"));
        #
        # self.program = {
        #     MapType.MAP_CUBE_T:
        #         self.load_program(
        #             vertex_shader='./shaders/model/shader.vert',
        #             fragment_shader='./shaders/model/shader.frag'),
        # }

        # --------------------------------------------------------
        # Boids geometry

        pi3 = (2*pi / 3)
        radius = 1.2

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

        #--------------------------------------------
        self.buffer_1 = self.ctx.buffer(data=array('f', self.gen_initial_data(self.boid_count)))

        self.buffer_2 = self.ctx.buffer(reserve=self.buffer_1.size)
        self.boid_vertices = self.ctx.buffer(data=vertices)
        self.boid_color = self.ctx.buffer(data=color)

        self.buffer_1.bind_to_storage_buffer(0)
        self.buffer_2.bind_to_storage_buffer(1)
        # ----------------------------------------------

        self.vao_1 = self.ctx.vertex_array(
            self.program_boids,
            [
                (self.boid_vertices, '3f', 'in_vert'),
                (self.boid_color, '3f', 'in_color'),
                (self.buffer_1, '3f 1x4 3f 1x4/i', 'in_pos', 'in_for')
            ],
        )

        self.vao_2 = self.ctx.vertex_array(
            self.program_boids,
            [
                (self.boid_vertices, '3f', 'in_vert'),
                (self.boid_color, '3f', 'in_color'),
                (self.buffer_2, '3f 1x4 3f 1x4/i', 'in_pos', 'in_for')
            ],
        )

        # --------------------------------------------
        # border + color
        self.program_border = self.ctx.program(
            vertex_shader=read_file("shaders/border.vert"),
            fragment_shader=read_file("shaders/line.frag"))

        self.program_lines = self.ctx.program(
            vertex_shader=read_file("shaders/line.vert"),
            fragment_shader=read_file("shaders/line.frag"))

        # --------------------------------------------------------
        # Compass geometry
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

        self.compass = self.ctx.vertex_array(
            self.program_lines,
            [
                (self.ctx.buffer(data=vertices), '3f', 'in_vert'),
                (self.ctx.buffer(data=color), '3f', 'in_color'),
            ],
        )

        # --------------------------------------------------------
        # Borders
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

        self.borders = self.ctx.vertex_array(
            self.program_border,
            [
                (self.ctx.buffer(data=vertices), '3f', 'in_vert'),
                (self.ctx.buffer(data=color), '3f', 'in_color'),
            ],
        )

    def gen_initial_data(self, count):
        for _ in range(count):
            yield uniform(-self.map_size/2, self.map_size/2)  # x
            yield uniform(-self.map_size/2, self.map_size/2)  # y
            yield uniform(-self.map_size/2, self.map_size/2)  # z
            yield 42.0 # fuck that shit

            dir = random_uniform_vec3()
            yield dir[0]  # fx
            yield dir[1]  # fy
            yield dir[2]  # fz
            yield 69.0 # fuck that too

    from src._resize_buffer import resize_boids_buffer
    from src._events import on_mouse_drag, on_mouse_scroll, on_key_press, on_resize
    from src._custom_profiles import set_custom_profile_1, set_custom_profile_2
    from src._gui import gui_newFrame, gui_draw

    from src._on_draw import on_draw
    from src._update import update

    from src._cleanup import cleanup

    def run(self):
        pyglet.app.run()
        self.cleanup()
