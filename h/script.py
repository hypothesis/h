# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import os
import sys
import textwrap

import transaction
from elasticsearch import Elasticsearch
from pyramid import paster
from pyramid.request import Request

from h import __version__
from h import reindexer
from h import accounts


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
    parser.add_argument(
        'config_uri',
        help="the path to your paster config file, for example: "
             "'conf/development.ini'")
    parser.add_argument(
        '--base',
        help="the base URL of your h instance (default: "
             "'http://localhost:5000')",
        default='http://localhost:5000',
        metavar='URL')


def init_db(args):
    """Create database tables and elasticsearch indices."""
    # Force model creation using the MODEL_CREATE_ALL env var
    os.environ['MODEL_CREATE_ALL'] = 'True'

    # Start the application, triggering model creation
    paster.setup_logging(args.config_uri)
    paster.bootstrap(args.config_uri)

parser_init_db = subparsers.add_parser('init_db', help=init_db.__doc__)
_add_common_args(parser_init_db)


def admin(args):
    """Make a user an admin."""
    paster.bootstrap(args.config_uri, request=Request.blank(''))
    accounts.make_admin(unicode(args.username, sys.getfilesystemencoding()))
    transaction.commit()


parser_admin = subparsers.add_parser('admin', help=admin.__doc__)
parser_admin.add_argument(
    'username',
    help="the name of the user to make into an admin, e.g. 'fred'")
parser_admin.add_argument('config_uri', help='paster configuration URI')


def assets(args):
    """Build the static assets."""
    paster.setup_logging(args.config_uri)
    request = Request.blank('', base_url=args.base)
    env = paster.bootstrap(args.config_uri, request=request)
    assets_env = env['request'].webassets_env
    for bundle in assets_env:
        bundle.urls()

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


def token(args):
    """
    Generate an OAuth bearer token for the specified principal.

    This token is suitable for authenticating HTTP requests to the h API.

    For example, to authorize yourself as user seanh to your local dev instance
    of h do:

        hypothesis token --base 'http://localhost:5000' --sub 'acct:seanh@localhost' conf/development.ini

    Then copy the output and pass it to the h API as the value of an
    X-Annotator-Auth-Token header.

    """
    from h.auth import get_client, generate_signed_token

    request = Request.blank("/", base_url=args.base)

    paster.setup_logging(args.config_uri)
    env = paster.bootstrap(args.config_uri, request=request)
    registry = env['registry']

    request.client = get_client(request, registry.settings['h.client_id'])
    request.user = args.sub
    request.expires_in = args.ttl
    request.extra_credentials = {}

    token = generate_signed_token(request)

    print(token)

parser_token = subparsers.add_parser(
    'token', description=textwrap.dedent(token.__doc__),
    formatter_class=argparse.RawDescriptionHelpFormatter)
_add_common_args(parser_token)
parser_token.add_argument(
    '--sub',
    help="subject (userid, group, etc.) of the token, for example: "
         "'acct:seanh@127.0.0.1'")
parser_token.add_argument(
    '--ttl', type=int, default=3600,
    help='token time-to-live in seconds, for example: 60 (default: 3600, '
         'one hour)')


def version(args):
    """Print the package version"""
    print('{prog} {version}'.format(prog=parser.prog, version=__version__))

parser_version = subparsers.add_parser('version', help=version.__doc__)


COMMANDS = {
    'assets': assets,
    'admin': admin,
    'extension': extension,
    'init_db': init_db,
    'reindex': reindex,
    'token': token,
    'version': version,
}


def main():
    args = parser.parse_args()
    COMMANDS[args.command](args)


if __name__ == '__main__':
    main()
