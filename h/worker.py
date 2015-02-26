"""
The worker runner is used to run worker processes outside of the web
application. A worker is simply a callable python object which accepts a single
argument, an instance of :py:class:`pyramid.request.Request` which is
preconfigured with a dummy request. This request can be used to interrogate the
routing table, fetch parts of the application, etc.

Workers are registered under the setuptools entry point ``h.worker``.
"""
import argparse
import logging
import os

from pkg_resources import iter_entry_points

from pyramid import paster
from pyramid.request import Request

log = logging.getLogger('h.worker')

ENTRYPOINTS = {e.name: e for e in iter_entry_points('h.worker')}

parser = argparse.ArgumentParser('hypothesis-worker')
parser.add_argument('config_uri',
                    help='paster configuration URI')
parser.add_argument('worker',
                    choices=ENTRYPOINTS,
                    help='name of worker to run')


def main():
    args = parser.parse_args()

    paster.setup_logging(args.config_uri)

    base_url = os.environ.get('APP_URL')
    if base_url is None:
        base_url = 'http://localhost'
        log.warn('APP_URL not found in environment, using default: %s',
                 base_url)

    request = Request.blank('/', base_url=base_url)
    env = paster.bootstrap(args.config_uri, request=request)
    request.root = env['root']

    entrypoint = ENTRYPOINTS[args.worker]
    worker_func = entrypoint.load()
    worker_func(request)


if __name__ == '__main__':
    main()
