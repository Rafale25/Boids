from OpenGL import GL

class Algorithm:
    LocalBitonicMergeSortExample = 0
    LocalDisperse = 1
    BigFlip = 2
    BigDisperse = 3

def sort(self, program, n=-1, max_workgroup_size=1024):
    workgroup_size_x = 1

    if n < max_workgroup_size * 2:
        workgroup_size_x = n // 2;
    else:
        workgroup_size_x = max_workgroup_size;

    h = workgroup_size_x * 2
    assert (h <= n)
    assert (h % 2 == 0)

    workgroup_count = n // ( workgroup_size_x * 2 );

    program['u_h'] = h
    program['u_algorithm'] = Algorithm.LocalBitonicMergeSortExample
    # with self.query:
    program.run(group_x=workgroup_count)
    # self.queries.append(self.query.elapsed * 10e-7)
    # print("query time LocalBitonicMergeSortExample: {:.3f}ms".format(self.query.elapsed * 10e-7))
    h *= 2

    while (h <= n):
        GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT); ## way better than ctx.finish()

        program['u_h'] = h
        program['u_algorithm'] = Algorithm.BigFlip
        # with self.query:
        program.run(group_x=workgroup_count)
        # self.queries.append(self.query.elapsed * 10e-7)
        # print("query time BigFlip: {:.3f}ms".format(self.query.elapsed * 10e-7))

        hh = h // 2
        while hh > 1:
            GL.glMemoryBarrier(GL.GL_SHADER_STORAGE_BARRIER_BIT);

            if hh <= workgroup_size_x * 2:
                program['u_h'] = hh
                program['u_algorithm'] = Algorithm.LocalDisperse
                # with self.query:
                program.run(group_x=workgroup_count)
                # self.queries.append(self.query.elapsed * 10e-7)
                # print("query time LocalDisperse: {:.3f}ms".format(self.query.elapsed * 10e-7))
                break
            else:
                program['u_h'] = hh
                program['u_algorithm'] = Algorithm.BigDisperse
                # with self.query:
                program.run(group_x=workgroup_count)
                # self.queries.append(self.query.elapsed * 10e-7)
                # print("query time BigDisperse: {:.3f}ms".format(self.query.elapsed * 10e-7))

            hh //= 2

        h *= 2
