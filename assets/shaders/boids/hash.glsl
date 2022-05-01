// flat xyz index
uint hash(ivec3 cell_index, uint count) {
    const uint MAX_SIZE = uint(pow(count, 1.0/3.0));
    // const uint MAX_SIZE = uint(map_size / cell_spacing); // MAX_SIZE should be the size describe by the lowest to highest boid position
    uint i = (cell_index.z * MAX_SIZE*MAX_SIZE) +
            (cell_index.y * MAX_SIZE) +
            cell_index.x;

    return i % count;
}

/*
// z-order curve
uint hash(ivec3 cell_index) {
    // cell_index = abs(cell_index);
    const int MAX_SIZE = 64;//int(pow(total_grid_cell_count, 1.0/3.0));
    const uint maskx = MAX_SIZE-1;
    const uint masky = MAX_SIZE-1;
    const uint maskz = MAX_SIZE-1;
    const uint width = MAX_SIZE;
    const uint width_height = MAX_SIZE*MAX_SIZE;
    return ((cell_index.x&maskx)+(cell_index.y&masky)*width+(cell_index.z&maskz)*width_height );
}
*/

/*
// hash with large primes
uint hash(ivec3 cell_index) {
    const int h = (cell_index.x * 92837111) ^ (cell_index.y * 689287499) ^ (cell_index.z * 283923481);
    return abs(h) % total_grid_cell_count;
}
*/
