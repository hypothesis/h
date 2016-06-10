# -*- coding: utf-8 -*-

import click

from h import models


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
    user = models.User.get_by_username(request.db, username)
    if user is None:
        raise click.ClickException('no user with username "{}"'.format(username))
    else:
        user.admin = True
    request.tm.commit()
