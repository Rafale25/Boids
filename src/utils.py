from random import uniform
from math import pi, cos, sin, log2, pow, ceil

def next_power_of_2(x):
    return int(pow(2, ceil(log2(x)/log2(2))))

def random_uniform_vec3(): # vector from 2 angles
    yaw = uniform(-pi, pi)
    pitch = uniform(-pi/2, pi/2)

    x = cos(yaw) * cos(pitch)
    z = sin(yaw) * cos(pitch)
    y = sin(pitch)

    return (x, y, z)

class FpsCounter:
    NB_SAMPLE = 40

    def __init__(self):
        self.fps_data = [0] * FpsCounter.NB_SAMPLE
        self.next_sample_indice = 0

    def update(self, fps_sample):
        self.fps_data[self.next_sample_indice] = fps_sample
        self.next_sample_indice = (self.next_sample_indice + 1) % FpsCounter.NB_SAMPLE

    def get_fps(self):
        n = sum(self.fps_data) / FpsCounter.NB_SAMPLE
        if n == 0.0:
            return 0.0
        return 1.0 / n
