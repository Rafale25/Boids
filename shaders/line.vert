#version 430

uniform mat4 projection;
uniform mat4 modelview;

in vec3 in_vert;
in vec3 in_color;

out vec3 v_color;

void main()
{
	vec4 pos = projection * modelview * vec4(in_vert, 1.0);

	gl_Position = pos;
	v_color = in_color;
}
