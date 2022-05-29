#! /usr/bin/python3

import logging
from array import array
from random import uniform
from math import pi, cos, sin, ceil
from pathlib import Path

import moderngl
import imgui

import moderngl_window
from moderngl_window.integrations.imgui import ModernglWindowRenderer
from moderngl_window.scene.camera import OrbitCamera
from moderngl_window.opengl.vao import VAO

from mapType import MapType
from utils import *

# class

class MyWindow(moderngl_window.WindowConfig):
    title = 'Boids Simulation 3D'
    gl_version = (4, 3)
    window_size = (1920, 1080)
    fullscreen = False
    resizable = True
    vsync = True
    resource_dir = (Path(__file__) / "../../assets").resolve()
    log_level = logging.ERROR

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('-BOID_COUNT', metavar='BOID_COUNT', type=int, default=1024, required=False)
        parser.add_argument('-MAP_SIZE', metavar='MAP_SIZE', type=int, default=20, required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.ctx.gc_mode = "auto"

        self.pause = False

        self.local_size_x = 512 ## smaller value is better when boids are close to each others, and bigger when they are far appart
        self.min_boids = 1
        self.max_boids = 2**22
        self.map_size = self.argv.MAP_SIZE
        self.map_type = MapType.MAP_CUBE

        self.boid_count = self.argv.BOID_COUNT#next_power_of_2(self.argv.BOID_COUNT)#2**16 ## must be a power of 2
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

        ## Debug
        self.fps_counter = FpsCounter()
        self.debug_values = {}
        self.query = self.ctx.query(samples=False, time=True)
        self.query_enabled = True

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

            'RESIZE':
                self.load_compute_shader(
                    path='./shaders/boids/compute/resize/init.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'COPY':
                self.load_compute_shader(
                    path='./shaders/boids/compute/resize/copy.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),

            'FLAG':
                self.load_compute_shader(
                    path='./shaders/boids/compute/prefix_sum/flag.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),
            'SCATTER':
                self.load_compute_shader(
                    path='./shaders/boids/compute/prefix_sum/scatter.comp',
                    defines={'LOCAL_SIZE_X': self.local_size_x}),


            MapType.MAP_CUBE_T:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update_sharedmemory.comp',
                    defines={'CUBE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_CUBE:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update_sharedmemory.comp',
                    defines={'CUBE': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE_T:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update_sharedmemory.comp',
                    defines={'SPHERE_T': 1, 'LOCAL_SIZE_X': self.local_size_x}),
            MapType.MAP_SPHERE:
                self.load_compute_shader(
                    path='./shaders/boids/compute/boid_update_sharedmemory.comp',
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

        self.buffer_flag_1 = self.ctx.buffer(reserve=4*self.boid_count, dynamic=True)
        self.buffer_flag_2 = self.ctx.buffer(reserve=self.buffer_flag_1.size, dynamic=True)
        self.buffer_flag_1.clear()
        self.buffer_flag_2.clear()

        self.buffer_compact_cells = self.ctx.buffer(reserve=4*self.boid_count, dynamic=True)

        ## init the boid buffer
        self.program['RESIZE']['u_time'] = 1.0
        self.resize_boids_buffer(old_count=0, new_count=self.boid_count)

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
        self.vao_vs = self.ctx.vertex_array(self.program['BOIDS_VS'], [])


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

    def get_boid_buffer_size(self):
        return next_power_of_2(self.boid_count)

    from _resize_buffer import resize_boids_buffer
    from _events import resize, key_event, mouse_position_event, mouse_drag_event, mouse_scroll_event, mouse_press_event, mouse_release_event, unicode_char_entered
    from _custom_profiles import set_custom_profile_1
    from _gui import gui_newFrame, gui_draw

    from _render import render
    from _update import update, parallel_prefix_scan, parallel_prefix_scan_flag

    from _sort import sort

    from _cleanup import cleanup

if __name__ == "__main__":
    MyWindow.run()
