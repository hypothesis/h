# -*- coding: utf-8 -*-

import click

from h import models


@click.group()
def user():
    """Manage users."""


@user.command()
@click.argument('username')
@click.option('--on/--off', default=True)
@click.pass_context
def admin(ctx, username, on):
    """
    Make a user an admin.

    You must specify the username of a user which you wish to give
    administrative privileges.
    """
    request = ctx.obj['bootstrap']()
    user = models.User.get_by_username(request.db, username)
    if user is None:
        raise click.ClickException('no user with username "{}"'.format(username))

    user.admin = on
    request.tm.commit()

    click.echo("{username} is now {status}an administrator"
               .format(username=username,
                       status='' if on else 'NOT '),
               err=True)
