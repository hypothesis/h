# -*- coding: utf-8 -*-

import click

from h import accounts


@click.command()
@click.argument('username')
@click.pass_context
def admin(ctx, username):
    """
    Make a user an admin.

    You must specify the username of a user which you wish to give
    administrative privileges.
    """
    request = ctx.obj['bootstrap']()
    accounts.make_admin(username)
    request.tm.commit()
