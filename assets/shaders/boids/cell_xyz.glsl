ivec3 cell_xyz(vec3 pos)
{
    return ivec3(floor(pos/cell_spacing));
}
