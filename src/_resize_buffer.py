from array import array

def resize_boids_buffer(self, new_count):
    bytes1 = self.buffer_1.read()[0:new_count * 32]
    bytes2 = self.buffer_2.read()[0:new_count * 32]

    self.buffer_1.orphan(new_count * 32)
    self.buffer_2.orphan(new_count * 32)

    ## resize hash buffers too
    # self.table_size = int(new_count * 1)
    self.table_size = new_count
    self.buffer_table.orphan(2*4*self.table_size)
    self.buffer_cell_start.orphan(4*self.table_size)

    if new_count > self.boid_count:
        b_new_boids = array('f', self.gen_initial_data(new_count - self.boid_count))

        bytes1 += b_new_boids
        bytes2 += b_new_boids

    self.buffer_1.write(bytes1)
    self.buffer_2.write(bytes2)

    self.boid_count = new_count
