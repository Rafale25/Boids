#! /usr/bin/python3

import sys, pyglet, platform
from boids import MyWindow

def main():

	if platform.system() == "Darwin":
		pyglet.options["shadow_window"] = False

	config = pyglet.gl.Config(
		major_version=4,
		minor_version=3,
		forward_compatible=True,
		depth_size=24,
		double_buffer=True,
		sample_buffers=1,
		samples=4,
	)

	app = MyWindow(
		max_boids=100_000,
		map_size=30,
		width=1280,
		height=720,
		caption="Boids Simulation 3D",
		fullscreen=False,
		resizable=True,
		vsync=False,
		config=config
	).run()

if __name__ == "__main__":
	main()
