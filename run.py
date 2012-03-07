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

        'sqlalchemy.url': 'sqlite:///hypothesis.db'
    }

    config = Configurator(settings=settings)
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
