Session (flup-compatible), caching, memoizing, and HTTP cache control middleware for WSGI. Supports memory, filesystem, database, and memcached based backends.

Simple memoization example::

    from wsgistate.memory import memoize

    @memoize()
    def app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Hello World!']

    if __name__ == '__main__':
         from wsgiref.simple_server import make_server
         http = make_server('', 8080, app)
         http.serve_forever()

Simple session example::

    from wsgistate.memory import session

    @session()
    def app(environ, start_response):
         session = environ['com.saddi.service.session'].session
         count = session.get('count', 0) + 1
         session['count'] = count
         start_response('200 OK', [('Content-Type', 'text/plain')])
         return ['You have been here %d times!' % count]

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        http = make_server('', 8080, app)
        http.serve_forever()