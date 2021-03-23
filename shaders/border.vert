#version 330

uniform mat4 projection;
uniform mat4 modelview;
uniform float map_size;

in vec3 in_vert;
in vec3 in_color;

out vec3 v_color;

void main()
{
	vec4 pos = projection * modelview * vec4(in_vert * map_size, 1.0);

	gl_Position = pos;
	v_color = in_color;
}
