from random import uniform
from math import pi, cos, sin

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

	return (x, y, z)
