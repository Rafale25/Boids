from OpenGL.GL import *

class Query:
    def __init__(self):
        self.query = glGenQueries(1)
        self.active = False
        # GL_TIME_ELAPSED
        # GL_PRIMITIVES_GENERATED
        # GL_SAMPLES_PASSED
        # GL_ANY_SAMPLES_PASSED

    def __enter__(self):
        self.active = True
        glBeginQuery(GL_TIME_ELAPSED, self.query[0])

    def __exit__(self, type, value, traceback):
        glEndQuery(GL_TIME_ELAPSED)
        self.active = False

    @property
    def elapsed(self):
        return glGetQueryObjectiv(self.query[0], GL_QUERY_RESULT)

    @property
    def ready(self):
        return glGetQueryObjectiv(self.query[0], GL_QUERY_RESULT_AVAILABLE)