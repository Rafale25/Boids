from array import array

# need to be re-written
def resize_boids_buffer(self, new_count):
    bytes1 = self.buffer_boid.read()[0:new_count * 32]
    bytes2 = self.buffer_boid_tmp.read()[0:new_count * 32]

    self.buffer_boid.orphan(new_count * 32)
    self.buffer_boid_tmp.orphan(new_count * 32)

    self.buffer_cell_count_1.orphan(new_count * 4)
    self.buffer_cell_count_2.orphan(new_count * 4)

    if new_count > self.boid_count:
        b_new_boids = array('f', self.gen_initial_data(new_count - self.boid_count))

        bytes1 += b_new_boids
        bytes2 += b_new_boids

    self.buffer_boid.write(bytes1)
    self.buffer_boid_tmp.write(bytes2)

    self.boid_count = new_count
