# -*- coding: utf-8 -*-

import click

from h.celery import start


@click.command(
    add_help_option=False,  # --help is passed through to Celery
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.pass_context
def celery(ctx):
    """
    Run Celery commands.

    This command delegates to the celery-worker command, giving access to the
    full Celery CLI.
    """
    argv = [ctx.command_path] + list(ctx.args)
    start(argv=argv, bootstrap=ctx.obj["bootstrap"])
