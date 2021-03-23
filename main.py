#! /usr/bin/python3

from boids import MyWindow

def main():

	app = MyWindow(
		max_boids=30000,
		map_size=50,
		width=1920,
		height=1080,
		caption="Boids Simulation 3D",
		fullscreen=False,
		resizable=False,
		vsync=False
	).run()


if __name__ == "__main__":
	main()
