# -*- coding: utf-8 -*-

import click


@click.command()
@click.pass_context
def initdb(ctx):
    """Create database tables and elasticsearch indices."""
    # Start the application, triggering model creation
    bootstrap = ctx.obj['bootstrap']
    bootstrap(create_db=True)
