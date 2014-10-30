# -*- coding: utf-8 -*-
import os
import urlparse

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'

if 'NUM_WORKERS' in os.environ:
    workers = int(os.environ['NUM_WORKERS'])

if 'STATSD_PORT' in os.environ:
    statsd_host = urlparse.urlparse(os.environ['STATSD_PORT_8125_UDP']).netloc


def post_fork(_server, _worker):
    try:
        import psycogreen.gevent
        psycogreen.gevent.patch_psycopg()
    except ImportError:
        pass
