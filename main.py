#! /usr/bin/python3

import sys
from boids import MyWindow

def main():

	nb_boids = int(sys.argv[1])

	app = MyWindow(
		max_boids=nb_boids,
		map_size=50,
		width=1280,
		height=720,
		caption="Boids Simulation 3D",
		fullscreen=False,
		resizable=True,
		vsync=False
	).run()


if __name__ == "__main__":
	main()
