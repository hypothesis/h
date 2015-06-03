# -*- coding: utf-8 -*-
import os
import sys
import urlparse

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'

if 'STATSD_PORT' in os.environ:
    statsd_host = urlparse.urlparse(os.environ['STATSD_PORT_8125_UDP']).netloc


def post_fork(_server, _worker):
    # Support back-ported SSL changes on Debian / Ubuntu
    major, minor, micro, _, _ = sys.version_info
    if major == 2 and minor == 7 and micro >= 9:
        import _ssl
        import gevent.hub
        if not hasattr(_ssl, '_sslwrap'):
            gevent.hub.PYGTE279 = True

    try:
        import psycogreen.gevent
        psycogreen.gevent.patch_psycopg()
    except ImportError:
        pass
