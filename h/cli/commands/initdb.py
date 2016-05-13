# -*- coding: utf-8 -*-

import os

import click


@click.command()
@click.pass_context
def initdb(ctx):
    """Create database tables and elasticsearch indices."""
    # Settings to autocreate database tables and indices
    os.environ['MODEL_CREATE_ALL'] = 'true'
    os.environ['SEARCH_AUTOCONFIG'] = 'true'

    # Start the application
    bootstrap = ctx.obj['bootstrap']
    bootstrap()
