import moderngl

from typing import List, Tuple

class QueryManager:
    def __init__(self, ctx):
        self.ctx = ctx
        self.query_pool: moderngl.Query = []
        self.in_use_queries: List[Tuple[str, dict, moderngl.Query]] = []
        self.enabled = True

        self.args = dict()
        self.current_query = None

        self.queries_result = []


    def create_query(self):
        query = self.ctx.query(**self.args['kwargs'])
        self.query_pool.append(query)

    def use_query(self):
        if len(self.query_pool) == 0:
            self.create_query()
        query = self.query_pool.pop()
        self.current_query = query
        return query

    def __call__(self, name, **kwargs):
        self.args = {
            'name': name,
            'kwargs': kwargs
        }
        return self

    def __enter__(self):
        query = self.use_query()
        self.in_use_queries.append( (self.args['name'], self.args['kwargs'], query) )

        self.current_query.mglo.begin()

    def __exit__(self, type, value, traceback):
        self.current_query.mglo.end()
        self.ctx.error ## silence the glInvalidOperation error ## TODO: remove when error fixed
        self.current_query = None

    def query_all(self):
        result = []

        if self.enabled:
            for name, kwargs, query in self.in_use_queries:
                r = {'name': name}

                if 'time' in kwargs:
                    r['elapsed'] = query.elapsed * 10e-7
                if 'primitives' in kwargs:
                    r['primitives'] = query.primitives

                result.append(r)

        self.query_pool.extend( [x[2] for x in self.in_use_queries] ) #put queries back into pool
        self.in_use_queries = []

        self.queries_result = result

