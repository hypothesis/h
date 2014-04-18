# -*- coding: utf-8 -*-
import os
import sys

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'


def post_fork(_server, _worker):
    if 'gevent' in sys.modules:
        import gevent.subprocess
        sys.modules['subprocess'] = gevent.subprocess

    try:
        import psycogreen.gevent
        psycogreen.gevent.patch_psycopg()
    except ImportError:
        pass
