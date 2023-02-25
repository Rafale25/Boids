#! /usr/bin/python3

from array import array
from math import pi
from pathlib import Path
import logging

import moderngl
import imgui

import OpenGL as GL
from OpenGL.GL import *

from OpenGL.GL.NV.mesh_shader import GL_MESH_SHADER_NV, GL_TASK_SHADER_NV

import moderngl_window
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.scene.camera import OrbitCamera
from moderngl_window.opengl.vao import VAO

from ._enums import MapType, RenderMode
from .utils import *
from .query_manager import QueryManager

import glfw

class MyWindow(moderngl_window.WindowConfig):
    title = 'Boids Simulation 3D'
    gl_version = (4, 3)
    window_size = (1280, 720) ## TODO: Fix resolution with high DPI
    fullscreen = False
    resizable = True
    vsync = True
    resource_dir = (Path(__file__) / "../../assets").resolve()
    aspect_ratio = None
    # log_level = logging.ERROR

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('-BOID_COUNT', metavar='BOID_COUNT', type=int, default=1024, required=False)
        parser.add_argument('-MAP_SIZE', metavar='MAP_SIZE', type=int, default=20, required=False)
        # https://stackoverflow.com/questions/55324449/how-to-specify-a-minimum-or-maximum-float-value-with-argparse

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ctx.gc_mode = "auto"

        print(self.wnd.pixel_ratio)
        print(self.wnd.size)

        monitor = glfw.get_primary_monitor()
        self.monitor_content_scale = glfw.get_monitor_content_scale(monitor)[0]

        self.pause = False

        self.local_size_x = 512 ## smaller value is better when boids are close to each others, and bigger when they are far appart
        self.min_boids = 1
        self.max_boids = 2**22
        self.map_size = self.argv.MAP_SIZE
        self.map_type = MapType.MAP_CUBE

        self.boid_count = self.argv.BOID_COUNT
        self.view_angle = pi/2
        self.view_distance = 2.0
        self.speed = 0.0 #0.050
        self.boid_size = 0.12
        self.cell_spacing = self.view_distance

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
        self.render_mode = RenderMode.MESH_SHADER ## mesh shader if support otherwise geometry shader

        ## Debug
        self.fps_counter = FpsCounter()
        self.query_manager = QueryManager(ctx=self.ctx)
        self.query_enabled = True

        ## ImGui --
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)

        self.program = {
            'BOIDS_INSTANCED':
                self.load_program(
                    vertex_shader='./shaders/boids/render/instanced/boid.vert',
                    fragment_shader='./shaders/boids/render/instanced/boid.frag'),

            'BOIDS_GS':
                self.load_program(
                    vertex_shader='./shaders/boids/render/geometry_shader/boid.vert',
                    geometry_shader='./shaders/boids/render/geometry_shader/boid.geom',
                    fragment_shader='./shaders/boids/render/boid.frag'),
            'BOIDS_VS':
                self.load_program(
                    vertex_shader='./shaders/boids/render/vertex_shader/boid.vert',
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

            'RESIZE':
                self.load_compute_shader(
                    path='./shaders/boids/compute/resize/init.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'COPY':
                self.load_compute_shader(
                    path='./shaders/boids/compute/resize/copy.comp',
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
        self.buffer_boid = self.ctx.buffer(reserve=32*self.boid_count, dynamic=True)
        self.buffer_boid_tmp = self.ctx.buffer(reserve=self.buffer_boid.size, dynamic=True)

        self.buffer_cell_count_1 = self.ctx.buffer(reserve=4*self.get_boid_buffer_size(), dynamic=True)
        self.buffer_cell_count_2 = self.ctx.buffer(reserve=self.buffer_cell_count_1.size, dynamic=True)

        ## init the boid buffer
        self.program['RESIZE']['u_time'] = 1.0
        self.resize_boids_buffer(old_count=0, new_count=self.boid_count)

        # ----

        def check_compile_error(id, type):
            if type != 'PROGRAM':
                status = glGetShaderiv(id, GL_COMPILE_STATUS)
                if not status:
                    print(glGetShaderInfoLog(id))
            else:
                status = glGetProgramiv(id, GL_LINK_STATUS)
                if not status:
                    print(glGetProgramInfoLog(id))


        mesh_shader = glCreateShader(GL_MESH_SHADER_NV) # GL_TASK_SHADER_NV
        glShaderSource(
            mesh_shader,
            Path('./assets/shaders/boids/render/mesh_shader/boid.mesh').read_text(),
        )
        glCompileShader(mesh_shader)
        check_compile_error(mesh_shader, 'MESH')

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(
            fragment_shader,
            Path('./assets/shaders/boids/render/mesh_shader/boid.frag').read_text(),
        )
        glCompileShader(fragment_shader)
        check_compile_error(fragment_shader, 'FRAGMENT')

        self.meshProgram = glCreateProgram()
        glAttachShader(self.meshProgram, mesh_shader)
        glAttachShader(self.meshProgram, fragment_shader)
        glLinkProgram(self.meshProgram)

        check_compile_error(self.meshProgram, 'PROGRAM')
        # ----

        ## geometry shader
        self.vao_gs = VAO(mode=moderngl.POINTS)
        self.vao_gs.buffer(self.buffer_boid, '4f 4f', ['in_pos', 'in_for'])
        # self.vao_gs.buffer(self.buffer_boid, '3f 1x4 3f 1x4', ['in_pos', 'in_for'])  # can't do that yet because x4/i not supported by moderngl-window==2.4.2

        ## vertex shader pulling
        self.vao_vs = self.ctx.vertex_array(self.program['BOIDS_VS'], [])

        ## instancing
        pi3 = (2*pi / 3)
        vertices = array('f',
            [
                -1.0, (cos(pi3 * 0.0)) * 0.5, (sin(pi3 * 0.0)) * 0.5, #corner 1
                -1.0, (cos(pi3 * 2.0)) * 0.5, (sin(pi3 * 2.0)) * 0.5, #corner 2
                -1.0, (cos(pi3 * 1.0)) * 0.5, (sin(pi3 * 1.0)) * 0.5, #corner 3
                2.0, 0.0, 0.0, #TOP
            ])
        indices = array('i',
            [
                1, 2, 0,
                3, 0, 2,
                3, 2, 1,
                1, 0, 3,
            ])
        colors = array('f',
        [
            1, 0, 0,
            0, 0, 1,
            0, 1, 0,
            0, 1, 1,
        ])

        self.vao_instanced = VAO(mode=moderngl.TRIANGLES)
        self.vao_instanced.buffer(self.ctx.buffer(vertices), '3f', ['in_vertex'])
        self.vao_instanced.buffer(self.ctx.buffer(colors), '3f', ['in_color'])
        self.vao_instanced.index_buffer(self.ctx.buffer(indices))
        self.vao_instanced.buffer(self.buffer_boid, '4f 4f/i', ['in_pos', 'in_for'])


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
        ])
        indices = array('i',
        [
            0, 1,
            0, 2,
            1, 3,
            2, 3,

            0, 6,
            1, 7,
            2, 4,
            3, 5,

            6, 7,
            5, 7,
            4, 5,
            4, 6,
        ])

        self.borders = VAO(mode=moderngl.LINES)
        self.borders.buffer(self.ctx.buffer(vertices), '3f', ['in_position'])
        # self.borders.buffer(self.ctx.buffer(color), '3f', ['in_color'])
        self.borders.index_buffer(self.ctx.buffer(indices))

    def get_boid_buffer_size(self):
        return next_power_of_2(self.boid_count)

    from ._resize_buffer import resize_boids_buffer
    from ._events import resize, key_event, mouse_position_event, mouse_drag_event, mouse_scroll_event, mouse_press_event, mouse_release_event, unicode_char_entered
    from ._custom_profiles import set_custom_profile_1
    from ._gui import gui_newFrame, gui_draw

    from ._render import render
    from ._update import update, parallel_prefix_scan

