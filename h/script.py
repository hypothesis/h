# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import logging
import os
import sys
import textwrap

from pkg_resources import iter_entry_points

from elasticsearch import helpers as es_helpers
from pyramid import paster
from pyramid.request import Request

from h import __version__
from h import accounts
from h.api.search import config as search_config
from h._compat import PY2, text_type

ANNOTOOL_OPERATIONS = {e.name: e for e in iter_entry_points('h.annotool')}

ENV_OVERRIDES = {
    'MODEL_CREATE_ALL': 'False',
    'MODEL_DROP_ALL': 'False',
    'SECRET_KEY': 'notsecret',
}
os.environ.update(ENV_OVERRIDES)


log = logging.getLogger('h')

parser = argparse.ArgumentParser(
    'hypothesis',
    description='The Hypothesis Project Annotation System')

subparsers = parser.add_subparsers(title='command', dest='command')
subparsers.required = True


def _add_common_args(parser):
    parser.add_argument(
        'config_uri',
        help="the path to your paster config file, for example: "
             "'conf/app.ini'")
    parser.add_argument(
        '--base',
        help="the base URL of your h instance (default: "
             "'http://localhost:5000')",
        default='http://localhost:5000',
        metavar='URL')


def bootstrap(args):
    """
    Bootstrap the application from the given arguments.

    Returns a bootstrapped request object.
    """
    paster.setup_logging(args.config_uri)
    request = Request.blank('/', base_url=args.base)
    paster.bootstrap(args.config_uri, request=request)
    return request


def initdb(args):
    """Create database tables and elasticsearch indices."""
    # Force model creation using the MODEL_CREATE_ALL env var
    os.environ['MODEL_CREATE_ALL'] = 'True'

    # Start the application, triggering model creation
    bootstrap(args)

parser_initdb = subparsers.add_parser('initdb', help=initdb.__doc__)
_add_common_args(parser_initdb)


def admin(args):
    """Make a user an admin."""
    request = bootstrap(args)
    accounts.make_admin(args.username)
    request.tm.commit()

parser_admin = subparsers.add_parser('admin', help=admin.__doc__)
_add_common_args(parser_admin)
parser_admin.add_argument(
    'username',
    type=lambda s: text_type(s, sys.getfilesystemencoding()) if PY2 else text_type,
    help="the name of the user to make into an admin, e.g. 'fred'")


def annotool(args):
    """
    Perform operations on the annotation database.

    This command provides a way of running named commands across the database
    of annotations and can be used to run data migrations, analytics, etc.

    **NB**: This tool cannot currently be used for making changes to the
    annotation "document" field.
    """
    request = bootstrap(args)

    annotations = es_helpers.scan(request.es.conn,
                                  query={'query': {'match_all': {}}},
                                  index=request.es.index,
                                  doc_type=request.es.t.annotation)

    chunksize = 1000
    state = {'total': 0, 'pending': []}

    def _flush():
        bodies = [{
            '_index': request.es.index,
            '_type': request.es.t.annotation,
            '_op_type': 'update',
            '_id': x['_id'],
            'doc': x['_source'],
        } for x in state['pending']]
        es_helpers.bulk(request.es.conn, bodies)

        state['total'] += len(state['pending'])
        log.info("processed %d annotations", state['total'])
        state['pending'] = []

    for annotation in annotations:
        func = ANNOTOOL_OPERATIONS[args.operation].load()
        func(annotation['_source'])

        state['pending'].append(annotation)

        if len(state['pending']) >= chunksize:
            _flush()

    if state['pending']:
        _flush()

parser_annotool = subparsers.add_parser('annotool', help=annotool.__doc__)
_add_common_args(parser_annotool)
parser_annotool.add_argument(
    'operation',
    choices=ANNOTOOL_OPERATIONS,
    help="the operation to perform on all annotations")


def assets(args):
    """Build the static assets."""
    request = bootstrap(args)
    for bundle in request.webassets_env:
        bundle.urls()

parser_assets = subparsers.add_parser('assets', help=assets.__doc__)
_add_common_args(parser_assets)


def reindex(args):
    """Reindex the annotations into a new Elasticsearch index."""
    request = bootstrap(args)

    # Configure the new index
    search_config.configure_index(request.es, args.target)

    # Reindex the annotations
    es_helpers.reindex(client=request.es.conn,
                       source_index=request.es.index,
                       target_index=args.target)

    if args.update_alias:
        request.es.conn.indices.update_aliases(body={'actions': [
            # Remove all existing aliases
            {"remove": {"index": "*", "alias": request.es.index}},
            # Alias current index name to new target
            {"add": {"index": args.target, "alias": request.es.index}},
        ]})

parser_reindex = subparsers.add_parser('reindex', help=reindex.__doc__)
_add_common_args(parser_reindex)
parser_reindex.add_argument('-u', '--update-alias',
                            action='store_true',
                            help='Whether to assume the current index is an '
                                 'alias and update it on reindex completion')
parser_reindex.add_argument('target', help='The name of the target index')


def token(args):
    """
    Generate an OAuth bearer token for the specified principal.

    This token is suitable for authenticating HTTP requests to the h API.

    For example, to authorize yourself as user seanh to your local dev instance
    of h do:

        hypothesis token --base 'http://localhost:5000' --sub 'acct:seanh@localhost' conf/development-app.ini

    Then copy the output and pass it to the h API as the value of an
    X-Annotator-Auth-Token header.

    """
    from h.auth import get_client, generate_signed_token

    request = bootstrap(args)
    registry = request.registry

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
    'annotool': annotool,
    'initdb': initdb,
    'reindex': reindex,
    'token': token,
    'version': version,
}


def main():
    # Set a flag in the environment that other code can use to detect if it's
    # running in a script rather than a full web application.
    #
    # FIXME: This is a nasty hack and should go when we no longer need to spin
    # up an entire application to build the extensions.
    os.environ['H_SCRIPT'] = 'true'

    args = parser.parse_args()
    COMMANDS[args.command](args)


if __name__ == '__main__':
    main()
