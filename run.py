from os import environ
from os.path import join
"""
If a virtual environment is active, make sure it's being used.
Globally-installed console scripts use an absolute shebang path which
prevents them from importing virtualenv packages. Detect that case here
and correct for it.
"""
try:
    activate = join(environ['VIRTUAL_ENV'], 'bin', 'activate_this.py')
    execfile(activate, dict(__file__=activate))
except KeyError:
    pass

from pyramid.paster import bootstrap, setup_logging

cfname = environ.get('HYPO_CONF', 'development.ini')
setup_logging(cfname)
env = bootstrap(cfname)
application = env['app']
env['closer']()

if __name__ == '__main__':
    """Runs the hypothes.is server.

    The value of the 'HYPO_CONF' environment variable may be a path to a file
    which is interpreted as an alternative paster configuration.

    When invoked from the command line, this module uses waitress or wsgiref
    to serve the application. The included 'development.ini' file will launch
    the server using the paste built-in server. Alternatively, this module is
    also a valid gunicorn application module which can be started
    via `gunicorn run`.
    """

    try:
        from functools import partial
        from waitress import serve
        run = partial(serve, application, host='0.0.0.0', port=5000)
    except ImportError:
        from wsgiref.simple_server import make_server
        run = make_server('0.0.0.0', 5000, application).serve_forever
        print 'serving on http://0.0.0.0:5000'

    try:
        run()
    except KeyboardInterrupt:
        pass

    print "\nTerminated."
