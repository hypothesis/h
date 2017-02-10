# -*- coding: utf-8 -*-
import os
import socket

if 'GUNICORN_TIMEOUT' in os.environ:
    timeout = int(os.environ['GUNICORN_TIMEOUT'])

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'

if not os.environ.get('GUNICORN_STATS_DISABLE', None):
    if 'STATSD_PORT_8125_UDP_ADDR' in os.environ and \
       'STATSD_PORT_8125_UDP_PORT' in os.environ:
            _host = os.environ['STATSD_PORT_8125_UDP_ADDR']
            _port = os.environ['STATSD_PORT_8125_UDP_PORT']
            statsd_host = '{}:{}'.format(_host, _port)

    elif 'STATSD_HOST' in os.environ:
        _host = os.environ['STATSD_HOST']
        _port = os.environ.get('STATSD_PORT', '8125')
        statsd_host = '{}:{}'.format(_host, _port)

    if 'STATSD_PREFIX' in os.environ:
        statsd_prefix = os.environ['STATSD_PREFIX']


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


def when_ready(server):
    name = server.proc_name
    if name == 'web' and 'WEB_NUM_WORKERS' in os.environ:
        server.num_workers = int(os.environ['WEB_NUM_WORKERS'])
    elif name == 'websocket' and 'WEBSOCKET_NUM_WORKERS' in os.environ:
        server.num_workers = int(os.environ['WEBSOCKET_NUM_WORKERS'])
