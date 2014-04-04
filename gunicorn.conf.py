import os

# Smart detect heroku stack and assume a trusted proxy.
# This is a convenience that should hopefully not be too surprising.
if 'heroku' in os.environ.get('LD_LIBRARY_PATH', ''):
    forwarded_allow_ips = '*'


def post_fork(_server, _worker):
    try:
        import psycogreen.gevent
        psycogreen.gevent.patch_psycopg()
    except ImportError:
        pass
