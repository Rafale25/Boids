ivec3 cell_xyz(vec3 pos, float spacing)
{
    return ivec3(floor(pos/spacing));
}
