# -*- coding: utf-8 -*-

import os

import click


@click.command()
@click.pass_context
def initdb(ctx):
    """Create database tables and elasticsearch indices."""
    # Force model creation using the MODEL_CREATE_ALL env var
    os.environ['MODEL_CREATE_ALL'] = 'True'

    # Start the application, triggering model creation
    bootstrap = ctx.obj['bootstrap']
    bootstrap()
