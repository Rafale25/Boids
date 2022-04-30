
// TODO: there's a bug with the MAX_SIZE or cell_spacing
uint hash(ivec3 cell_index) {
    const uint MAX_SIZE = uint(map_size / cell_spacing); // MAX_SIZE should be the size describe by the lowest to highest boid position
    uint i = (cell_index.z * MAX_SIZE*MAX_SIZE) +
            (cell_index.y * MAX_SIZE) +
            cell_index.x;

    return i % total_grid_cell_count;
}

/*
uint hash(ivec3 cell_index) {
    const int MAX_SIZE = 64;
    const uint maskx = MAX_SIZE-1;
    const uint masky = MAX_SIZE-1;
    const uint maskz = MAX_SIZE-1;
    const uint width = MAX_SIZE;
    const uint width_height = MAX_SIZE*MAX_SIZE;
    return (cell_index.x&maskx)+(cell_index.y&masky)*width+(cell_index.z&maskz)*width_height;
}
*/

/*
uint hash(ivec3 cell_index) {
    const int h = (cell_index.x * 92837111) ^ (cell_index.y * 689287499) ^ (cell_index.z * 283923481);
    return abs(h) % total_grid_cell_count;
}
*/

/*
uint hash(ivec3 cell_index) {
    const int MAX_SIZE = 64;
    const uint maskx = MAX_SIZE-1;
    const uint masky = MAX_SIZE-1;
    const uint maskz = MAX_SIZE-1;
    const uint width = MAX_SIZE;
    const uint width_height = MAX_SIZE*MAX_SIZE;
    return (cell_index.x&maskx)+(cell_index.y&masky)*width+(cell_index.z&maskz)*width_height;
}
*/
