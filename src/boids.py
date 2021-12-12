#! /usr/bin/python3

import time

from math import pi, cos, sin, ceil
from random import uniform
from array import array

import pyglet
import moderngl
import imgui
import glm

import moderngl_window
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.scene import KeyboardCamera
from moderngl_window.scene.camera import OrbitCamera
from moderngl_window.opengl.vao import VAO

from pathlib import Path

from utils import *

from src._mapType import MapType

class MyWindow(moderngl_window.WindowConfig):
    title = 'Boids Simulation 3D'
    gl_version = (4, 3)
    window_size = (1280, 720)
    fullscreen = False
    resizable = True
    vsync = True
    resource_dir = Path(__file__).parent.parent.resolve()
    print(resource_dir)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.ctx.gc_mode = "auto"

        self.pause = False

        self.max_boids = 50_000
        self.map_size = 20
        self.map_type = MapType.MAP_CUBE;

        self.boid_count = 1000
        self.view_angle = pi/2
        self.view_distance = 2.0
        self.speed = 0.015;

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
            far=200.0,
        )
        self.camera.mouse_sensitivity = 1.0
        self.camera.zoom_sensitivity = 0.5

        # ImGui --
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)

        # Boid -----
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
            MapType.MAP_CUBE_T:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'CUBE_T': 1}),
            MapType.MAP_CUBE:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'CUBE': 1}),
            MapType.MAP_SPHERE_T:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'SPHERE_T': 1}),
            MapType.MAP_SPHERE:
                self.load_compute_shader(
                    path='./shaders/boids/boid_update.comp',
                    defines={'SPHERE': 1}),
        }

        ## --------------------------------------------------------
        ## Boids geometry
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

        self.compass = VAO(mode=moderngl.LINES)
        self.compass.buffer(self.ctx.buffer(vertices), '3f', ['in_position'])
        self.compass.buffer(self.ctx.buffer(color), '3f', ['in_color'])

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

        self.borders = VAO(mode=moderngl.LINES)
        self.borders.buffer(self.ctx.buffer(vertices), '3f', ['in_position'])
        self.borders.buffer(self.ctx.buffer(color), '3f', ['in_color'])

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
    from src._events import resize, key_event, mouse_position_event, mouse_drag_event, mouse_scroll_event, mouse_press_event, mouse_release_event, unicode_char_entered
    from src._custom_profiles import set_custom_profile_1, set_custom_profile_2
    from src._gui import gui_newFrame, gui_draw

    from src._render import render
    from src._update import update

    from src._cleanup import cleanup
