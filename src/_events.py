from math import pi

import glm
import pyglet

from utils import *

def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
	if (buttons == pyglet.window.mouse.RIGHT):
		self.camera_rotx += dx * 0.002
		self.camera_roty += dy * 0.002

		self.camera_rotx %= 2*pi
		self.camera_roty = fclamp(self.camera_roty, -pi/2, pi/2)

def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
	self.camera_z += scroll_y
	self.camera_z = fclamp(self.camera_z, -self.map_size*3.0, 0.0)

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
	mat_perspective = glm.perspective(-80, aspect_ratio, 0.1, 1000)

	self.program_boids['projection'].write(mat_perspective)
	self.program_border['projection'].write(mat_perspective)
	self.program_lines['projection'].write(mat_perspective)
