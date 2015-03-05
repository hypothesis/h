# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import sys

from elasticsearch import Elasticsearch
from pyramid import paster
import webassets.script

from h import __version__, reindexer


ENV_OVERRIDES = {
    'MODEL_CREATE_ALL': 'False',
    'MODEL_DROP_ALL': 'False',
    'SECRET_KEY': 'notsecret',
}
os.environ.update(ENV_OVERRIDES)


parser = argparse.ArgumentParser(
    'hypothesis',
    description='The Hypothesis Project Annotation System')

subparsers = parser.add_subparsers(title='command', dest='command')
subparsers.required = True


def _add_common_args(parser):
    parser.add_argument('config_uri', help='paster configuration URI')


def init_db(args):
    """Create database tables and elasticsearch indices."""
    # Force model creation using the MODEL_CREATE_ALL env var
    os.environ['MODEL_CREATE_ALL'] = 'True'

    # Start the application, triggering model creation
    paster.setup_logging(args.config_uri)
    paster.bootstrap(args.config_uri)

parser_init_db = subparsers.add_parser('init_db', help=init_db.__doc__)
_add_common_args(parser_init_db)


def assets(args):
    """Build the static assets."""
    paster.setup_logging(args.config_uri)
    env = paster.bootstrap(args.config_uri)

    assets_env = env['request'].webassets_env
    webassets.script.main(['build'], assets_env)

parser_assets = subparsers.add_parser('assets', help=assets.__doc__)
_add_common_args(parser_assets)


def extension(args):
    print('This command has been removed. Please use the hypothesis-buildext '
          'tool instead.', file=sys.stderr)
    sys.exit(1)

parser_extension = subparsers.add_parser('extension', help='DEPRECATED.')


def reindex(args):
    """Reindex the annotations into a new Elasticsearch index."""
    paster.setup_logging(args.config_uri)
    env = paster.bootstrap(args.config_uri)

    if 'es.host' in env['registry'].settings:
        host = env['registry'].settings['es.host']
        conn = Elasticsearch([host])
    else:
        conn = Elasticsearch()

    r = reindexer.Reindexer(conn, interactive=True)

    r.reindex(args.old_index, args.new_index)

    if args.alias is not None:
        r.alias(args.new_index, args.alias)

parser_reindex = subparsers.add_parser('reindex', help=reindex.__doc__)
_add_common_args(parser_reindex)
parser_reindex.add_argument('old_index', help='The index to read from')
parser_reindex.add_argument('new_index', help='The index to write to')
parser_reindex.add_argument('alias', nargs='?',
                            help='Alias to repoint to new_index when '
                                 'reindexing is complete')


def version(args):
    """Print the package version"""
    print('{prog} {version}'.format(prog=parser.prog, version=__version__))

parser_version = subparsers.add_parser('version', help=version.__doc__)


COMMANDS = {
    'assets': assets,
    'extension': extension,
    'init_db': init_db,
    'reindex': reindex,
    'version': version,
}


def main():
    args = parser.parse_args()
    COMMANDS[args.command](args)


if __name__ == '__main__':
    main()
