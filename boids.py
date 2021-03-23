#! /usr/bin/python3

import numpy as np
import pyglet, moderngl, imgui, glm, math, random, struct, time
from pyglet import gl

from imgui.integrations.pyglet import PygletProgrammablePipelineRenderer

from math import pi, cos, sin
from random import uniform
from array import array

def read_file(path):
	data = None
	with open(path, 'r') as file:
		data = file.read()
	return data

def fclamp(x, min_x, max_x):
	return (max(min(x, max_x), min_x))

def random_uniform_vec3(): # vector from 2 angles
	yaw = uniform(-pi, pi)
	pitch = uniform(-pi/2, pi/2)

	x = cos(yaw) * cos(pitch);
	z = sin(yaw) * cos(pitch);
	y = sin(pitch);

	return [x, y, z]

class MyWindow(pyglet.window.Window):
	def __init__(self, max_boids, map_size, *args, **kwaargs):
		super(MyWindow, self).__init__(*args, **kwaargs)

		self.ctx = moderngl.create_context(require=430)

		pyglet.clock.schedule_interval(self.update, 1.0 / 144.0)

		self.fps_update = 0
		self.fps_draw = 0
		self.ltime_update = 0.0;
		self.ltime_draw = 0.0;

		self.pause = False

		self.map_size = map_size
		self.boid_count = max_boids
		self.view_angle = pi/2
		self.view_distance = 2.0;
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


		# update boids program -----
		self.program_update_boids = self.ctx.compute_shader(
			read_file("shaders/boid_update.comp"))


		# --------------------------------------------------------
		# Boids geometry
		pi3 = (2*pi / 3)
		radius = 1.0

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
		# Lines + color
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
		mp2 = map_size/2
		vertices = array('f',
		[
			-mp2, -mp2, -mp2,
			mp2, -mp2, -mp2,

			-mp2, -mp2, mp2,
			mp2, -mp2, mp2,

			-mp2, mp2, mp2,
			mp2, mp2, mp2,

			-mp2, mp2, -mp2,
			mp2, mp2, -mp2,

			-mp2, -mp2, -mp2,
			-mp2, mp2, -mp2,

			-mp2, -mp2, mp2,
			-mp2, mp2, mp2,

			mp2, -mp2, -mp2,
			mp2, mp2, -mp2,

			mp2, -mp2, mp2,
			mp2, mp2, mp2,

			-mp2, -mp2, -mp2,
			-mp2, -mp2, mp2,

			-mp2, mp2, -mp2,
			-mp2, mp2, mp2,

			mp2, -mp2, -mp2,
			mp2, -mp2, mp2,

			mp2, mp2, -mp2,
			mp2, mp2, mp2,
		])
		color = array('f', [0.25, 0.25, 0.25]*24)

		self.borders = self.ctx.vertex_array(
			self.program_lines,
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

	# def on_mouse_motion(self, x, y, dx, dy):
	# 	pass

	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		if (buttons == pyglet.window.mouse.RIGHT):
			self.camera_rotx += dx * 0.002
			self.camera_roty += dy * 0.002

			self.camera_rotx %= 2*pi
			self.camera_roty = fclamp(self.camera_roty, -pi/2, pi/2)

	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		self.camera_z += scroll_y
		self.camera_z = fclamp(self.camera_z, -self.map_size*2, 0.0)

	def on_key_press(self, symbol, modifiers):
		if (symbol == pyglet.window.key.ESCAPE):
			self.close()

		if (symbol == pyglet.window.key.SPACE):
			if (self.pause):
				self.pause = False
			else:
				self.pause = True

	def on_resize(self, width, height): # is called at start
		# Set up viewport and projection
		self.ctx.viewport = 0, 0, int(width), int(height)
		aspect_ratio = width / height

		mat_perspective = np.array(glm.perspective(-80, aspect_ratio, 0.1, 1000)).flatten()
		self.program_boids['projection'] = tuple(mat_perspective)
		self.program_lines['projection'] = tuple(mat_perspective)

	def set_custom_profile_1(self):
		self.speed=0.020
		self.view_distance=2.0
		self.view_angle=1.48
		self.separation_force=0.65
		self.alignment_force=1.0
		self.cohesion_force=1.0
		self.view_distance = 2.0;

	def gui_newFrame(self):
		imgui.new_frame()
		imgui.begin("Properties", True)

		changed, self.speed = imgui.drag_float(
			label="Speed",
			value=self.speed,
			change_speed=0.0005,
			min_value=0.001,
			max_value=0.5,
			format="%.3f")

		changed, self.view_distance = imgui.drag_float(
			label="View Distance",
			value=self.view_distance,
			change_speed=0.001,
			min_value=0.0,
			max_value=10.0,
			format="%.2f")

		changed, self.view_angle = imgui.drag_float(
			label="View Angle",
			value=self.view_angle,
			change_speed=0.001,
			min_value=0.0,
			max_value=pi,
			format="%.2f")

		changed, self.separation_force = imgui.drag_float(
			label="Separation Force",
			value=self.separation_force,
			change_speed=0.002,
			min_value=0.0,
			max_value=10.0,
			format="%.2f")

		changed, self.alignment_force = imgui.drag_float(
			label="Aligment Force",
			value=self.alignment_force,
			change_speed=0.002,
			min_value=0.0,
			max_value=10.0,
			format="%.2f")

		changed, self.cohesion_force = imgui.drag_float(
			label="Cohesion Force",
			value=self.cohesion_force,
			change_speed=0.002,
			min_value=0.0,
			max_value=10.0,
			format="%.2f")

		clicked, self.pause = imgui.checkbox("Paused", self.pause)

		imgui.new_line()
		imgui.begin_group()
		imgui.text("Custom profiles:")
		if (imgui.button("Profile 1")):
			self.set_custom_profile_1()
		imgui.end_group()

		imgui.end()

	def gui_draw(self):
		imgui.render()
		self.impl.render(imgui.get_draw_data())

	def on_draw(self):
		self.gui_newFrame()

		# self.fps_draw += 1
		# t = time.time()
		# if (t - self.ltime_draw > 1.0):
		# 	self.ltime_draw = t
		# 	print("draw: %d fps" % self.fps_draw)
		# 	self.fps_draw = 0

		self.ctx.clear()
		self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

		mat_rotx = glm.rotate(glm.mat4(1.0), -self.camera_roty, glm.vec3(1.0, 0.0, 0.0))
		mat_roty = glm.rotate(glm.mat4(1.0), self.camera_rotx, glm.vec3(0.0, 1.0, 0.0))
		mat_rotz = glm.rotate(glm.mat4(1.0), 0.0, glm.vec3(0.0, 0.0, 1.0))

		translate = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, self.camera_z))
		modelview = np.array(translate * mat_rotx * mat_roty * mat_rotz).flatten()

		self.program_boids['modelview'] = tuple(modelview)
		self.program_lines['modelview'] = tuple(modelview)

		self.vao_1.render(instances=self.boid_count)

		self.compass.render(mode=moderngl.LINES)
		self.borders.render(mode=moderngl.LINES)

		self.gui_draw()

		# back to default pipeline
		# gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
		# gl.glUseProgram(0)
		# gl.glBindVertexArray(0)
		# self.fps_display.draw()


	def update(self, dt):
		# self.fps_update += 1
		# t = time.time()
		# if (t - self.ltime_update > 1.0):
		# 	self.ltime_update = t
		# 	print("update: %d fps" % self.fps_update)
		# 	self.fps_update = 0

		if not (self.pause):
			self.program_update_boids['boid_count'] = self.boid_count
			self.program_update_boids['speed'] = self.speed
			self.program_update_boids['map_size'] = self.map_size
			self.program_update_boids['view_distance'] = self.view_distance
			self.program_update_boids['view_angle'] = self.view_angle

			self.program_update_boids['separation_force'] = self.separation_force
			self.program_update_boids['alignment_force'] = self.alignment_force
			self.program_update_boids['cohesion_force'] = self.cohesion_force

			# query = self.ctx.query(time=True)
			#
			# with query:
			x = math.ceil(self.boid_count / 512)
			self.program_update_boids.run(x, 1, 1)
			# print("Update boids: %.2f ms\n" % (query.elapsed * 10e-7))

			# print( struct.unpack('{}vf'.format(256 * 8), self.buffer_2.read()) )

			self.vao_1, self.vao_2 = self.vao_2, self.vao_1

			self.a, self.b = self.b, self.a
			self.buffer_1.bind_to_storage_buffer(self.a)
			self.buffer_2.bind_to_storage_buffer(self.b)

	def run(self):
		pyglet.app.run()
		# while True:
		# 	pyglet.clock.tick()
		#
		# 	self.switch_to()
		# 	self.dispatch_events()
		# 	# self.dispatch_event('on_draw')
		# 	# self.on_draw()
		# 	self.flip()
