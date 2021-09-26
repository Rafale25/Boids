import moderngl
import glm

from src._mapType import MapType

def on_draw(self):
	self.gui_newFrame()

	self.ctx.clear()
	self.ctx.enable_only(moderngl.CULL_FACE | moderngl.DEPTH_TEST)

	mat_rotx = glm.rotate(glm.mat4(1.0), -self.camera_roty, glm.vec3(1.0, 0.0, 0.0))
	mat_roty = glm.rotate(glm.mat4(1.0), self.camera_rotx, glm.vec3(0.0, 1.0, 0.0))
	mat_rotz = glm.rotate(glm.mat4(1.0), 0.0, glm.vec3(0.0, 0.0, 1.0))

	translate = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, self.camera_z))
	modelview = translate * mat_rotx * mat_roty * mat_rotz

	self.program_boids['modelview'].write(modelview)
	self.program_border['modelview'].write(modelview)
	self.program_lines['modelview'].write(modelview)

	self.compass.render(mode=moderngl.LINES)
	self.vao_1.render(instances=self.boid_count)

	if (self.map_type == MapType.MAP_CUBE or self.map_type == MapType.MAP_CUBE_T):
		self.borders.render(mode=moderngl.LINES)

	self.gui_draw()

	# back to default pipeline
	# gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
	# gl.glUseProgram(0)
	# gl.glBindVertexArray(0)
