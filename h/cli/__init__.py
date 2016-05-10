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
    'h.cli.commands.devserver.devserver',
    'h.cli.commands.initdb.initdb',
    'h.cli.commands.reindex.reindex',
)


def bootstrap(config):
    """
    Bootstrap the application from the given arguments.

    Returns a bootstrapped request object.
    """
    paster.setup_logging(config)
    request = Request.blank('/')
    paster.bootstrap(config, request=request)
    return request


@click.group()
@click.option('--dev',
              help="Use defaults suitable for development?",
              default=False,
              is_flag=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, dev):
    # Set a flag in the environment that other code can use to detect if it's
    # running in a script rather than a full web application.
    #
    # FIXME: This is a nasty hack and should go when we no longer need to spin
    # up an entire application to build the extensions.
    os.environ['H_SCRIPT'] = 'true'

    # Override other important environment variables
    os.environ['MODEL_CREATE_ALL'] = 'False'
    os.environ['MODEL_DROP_ALL'] = 'False'
    os.environ['SECRET_KEY'] = 'notsecret'

    config = 'conf/development-app.ini' if dev else 'conf/app.ini'
    ctx.obj['bootstrap'] = functools.partial(bootstrap, config)


def main():
    resolver = path.DottedNameResolver()
    for cmd in SUBCOMMANDS:
        cli.add_command(resolver.resolve(cmd))
    cli(prog_name='hypothesis', obj={})


if __name__ == '__main__':
    main()
