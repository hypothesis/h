# -*- coding: utf-8 -*-
import os
from h._compat import urlparse

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'

if 'STATSD_PORT' in os.environ:
    statsd_host = urlparse.urlparse(os.environ['STATSD_PORT_8125_UDP']).netloc


def post_fork(server, worker):
    # Support back-ported SSL changes on Debian / Ubuntu
    import _ssl
    import gevent.hub
    if hasattr(_ssl, 'SSLContext') and not hasattr(_ssl, '_sslwrap'):
        gevent.hub.PYGTE279 = True

    # Patch psycopg2 if we're asked to by the worker class
    if getattr(server.worker_class, 'use_psycogreen', False):
        import psycogreen.gevent
        psycogreen.gevent.patch_psycopg()
        worker.log.info("Made psycopg green")
