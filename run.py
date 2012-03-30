from hypothesis import create_app
application = create_app('development.ini')

if __name__ == '__main__':
    try:
        from functools import partial
        from waitress import serve
        run = partial(serve, application, host='127.0.0.1', port=8000)
    except ImportError:
        from wsgiref.simple_server import make_server
        run = make_server('127.0.0.1', 8000, application).serve_forever
        print 'serving on http://localhost:8000'

    try:
        run()
    except KeyboardInterrupt:
        # Catch this to avoid logging a traceback
        pass

    print "\nTerminated."
