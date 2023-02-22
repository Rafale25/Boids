from enum import IntEnum#, auto

class MapType(IntEnum):
    MAP_CUBE_T = 0
    MAP_CUBE = 1
    MAP_SPHERE = 2
    MAP_SPHERE_T = 3

class RenderMode(IntEnum):
    GEOMETRY_SHADER = 0
    VERTEX_SHADER = 1
    MESH_SHADER = 2
    INSTANCED = 3