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
    # Serve using waitress or wsgiref if executed directly.
    # This file is also readable by gunicorn.
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
