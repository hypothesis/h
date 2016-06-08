# -*- coding: utf-8 -*-
from __future__ import print_function

import functools
import logging
import os

import click
from pyramid import paster
from pyramid import path
from pyramid.request import Request

from h import __version__

log = logging.getLogger('h')

SUBCOMMANDS = (
    'h.cli.commands.admin.admin',
    'h.cli.commands.celery.celery',
    'h.cli.commands.devserver.devserver',
    'h.cli.commands.initdb.initdb',
    'h.cli.commands.migrate.migrate',
    'h.cli.commands.move_uri.move_uri',
    'h.cli.commands.reindex.reindex',
)


def bootstrap(app_url, dev=False):
    """
    Bootstrap the application from the given arguments.

    Returns a bootstrapped request object.
    """
    # Set a flag in the environment that other code can use to detect if it's
    # running in a script rather than a full web application.
    #
    # FIXME: This is a nasty hack and should go when we no longer need to spin
    # up an entire application to build the extensions.
    os.environ['H_SCRIPT'] = 'true'

    # In development, we will happily provide a default APP_URL, but it must be
    # set in production mode.
    if not app_url:
        if dev:
            app_url = 'http://localhost:5000'
        else:
            raise click.ClickException('the app URL must be set in production mode!')

    config = 'conf/development-app.ini' if dev else 'conf/app.ini'

    paster.setup_logging(config)
    request = Request.blank('/', base_url=app_url)
    env = paster.bootstrap(config, request=request)
    request.root = env['root']
    return request


@click.group()
@click.option('--app-url',
              help="The base URL for the application",
              envvar='APP_URL',
              metavar='URL')
@click.option('--dev',
              help="Use defaults suitable for development?",
              default=False,
              is_flag=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, app_url, dev):
    ctx.obj['bootstrap'] = functools.partial(bootstrap, app_url, dev)


def main():
    resolver = path.DottedNameResolver()
    for cmd in SUBCOMMANDS:
        cli.add_command(resolver.resolve(cmd))
    cli(prog_name='hypothesis', obj={})


if __name__ == '__main__':
    main()
