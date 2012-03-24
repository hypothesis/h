from pyramid.config import Configurator

from hypothesis import create_app

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    log = logging.getLogger(__file__)
    log.setLevel(logging.DEBUG)
    
    from wsgiref.simple_server import make_server

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
    
    config = Configurator(settings=settings)
    config.include('pyramid_debugtoolbar')
    app = create_app(config)

    log.info("Starting server...")
    server = make_server('127.0.0.1', 8080, app)
    log.info("Serving at http://localhost:8080/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # Catch this to avoid logging a traceback
        pass

    log.info("Terminated.")
