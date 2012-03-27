from pyramid.config import Configurator

from hypothesis import create_app

# Development setup

settings = {
    'reload_all': True,
    'debug_all': True,

    'sqlalchemy.url': 'sqlite:///hypothesis.db',

    'apex.session_secret': '535510n_53cr37',
    'apex.auth_secret': '4u7h_53cr37',
    'apex.came_from_route': 'home',
    'apex.velruse_providers': [],
    'apex.no_csrf': 'apex_callback,store',

    'velruse.endpoint': 'http://localhost:8080/auth/apex_callback',
    'velruse.store': 'velruse.store.sqlstore',
    'velruse.providers': [],

    'hypothesis.api_secret': '00000000-0000-0000-0000-000000000000',
    'hypothesis.consumer_key': 'hypothes.is'
}
config = Configurator(package='hypothesis', settings=settings)
config.include('pyramid_debugtoolbar')
application = create_app(config)

# Serve the demo configuration if run from the command line

if __name__ == '__main__':
    from functools import partial
    try:
        from waitress import serve
        run = partial(serve, application, host='127.0.0.1', port=8080)
    except ImportError:
        from wsgiref.simple_server import make_server
        run = make_server('127.0.0.1', 8080, application).serve_forever
        print 'serving on http://localhost:8080'

    try:
        run()
    except KeyboardInterrupt:
        # Catch this to avoid logging a traceback
        pass

    print "\nTerminated."
