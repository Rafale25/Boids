// flat xyz index
uint hash(ivec3 cell_index, uint count) {
    const uint MAX_SIZE = uint(pow(count, 1.0/3.0)); // cube root of the amount of boids
    uint i = (cell_index.z * MAX_SIZE*MAX_SIZE) +
            (cell_index.y * MAX_SIZE) +
            cell_index.x;

    return i % count;
}

// 3 by 3 snake-curve // slightly worse
// uint hash(ivec3 cell_index, uint count) {
//     const uint MAX_SIZE = uint(pow(count, 1.0/3.0));
//     const uint MAX_SIZE3 = MAX_SIZE / 3;
//
//     uint big_i =
//             ((cell_index.z / 3) * MAX_SIZE3*MAX_SIZE3) +
//             ((cell_index.y / 3) * MAX_SIZE3) +
//             (cell_index.x / 3);
//
//     uint small_i =
//         ((cell_index.z % 3) * 3*3) +
//         ((cell_index.y % 3) * 3) +
//         ((cell_index.x % 3));
//
//     return (big_i * 27 + small_i) % count;
// }

// uint expandBits(uint v)
// {
//     v = (v * 0x00010001u) & 0xFF0000FFu;
//     v = (v * 0x00000101u) & 0x0F00F00Fu;
//     v = (v * 0x00000011u) & 0xC30C30C3u;
//     v = (v * 0x00000005u) & 0x49249249u;
//     return v;
// }
//
// uint hash(ivec3 cell_index, uint count) // z-order curve
// {
//     const int MAX_SIZE = 1024;//int(pow(count, 1.0/3.0));
//     cell_index.x %= MAX_SIZE;
//     cell_index.y %= MAX_SIZE*MAX_SIZE;
//     cell_index.z %= MAX_SIZE*MAX_SIZE*MAX_SIZE;
//     // x = min(max(x * 1024.0f, 0.0f), 1023.0f);
//     // y = min(max(y * 1024.0f, 0.0f), 1023.0f);
//     // z = min(max(z * 1024.0f, 0.0f), 1023.0f);
//     uint xx = expandBits(uint(cell_index.x));
//     uint yy = expandBits(uint(cell_index.y));
//     uint zz = expandBits(uint(cell_index.z));
//     return (xx * 4 + yy * 2 + zz) % count;
// }

// z-order curve (not working)
/*
uint hash(ivec3 cell_index, uint count) {
    // cell_index = abs(cell_index);
    const int MAX_SIZE = 128;//int(pow(count, 1.0/3.0));//64;
    const uint maskx = MAX_SIZE-1;
    const uint masky = MAX_SIZE-1;
    const uint maskz = MAX_SIZE-1;
    const uint width = MAX_SIZE;
    const uint width_height = MAX_SIZE*MAX_SIZE;
    return ((cell_index.x&maskx)+(cell_index.y&masky)*width+(cell_index.z&maskz)*width_height ) % count;
}
*/

/*
// hash with large primes
uint hash(ivec3 cell_index) {
    const int h = (cell_index.x * 92837111) ^ (cell_index.y * 689287499) ^ (cell_index.z * 283923481);
    return abs(h) % total_grid_cell_count;
}
*/
