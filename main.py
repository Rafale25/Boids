#! /usr/bin/python3

import sys
from boids import MyWindow

def main():

	app = MyWindow(
		max_boids=1000,
		map_size=50,
		width=1280,
		height=720,
		caption="Boids Simulation 3D",
		fullscreen=False,
		resizable=True,
		vsync=True
	).run()


if __name__ == "__main__":
	main()
