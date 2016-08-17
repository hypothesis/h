# -*- coding: utf-8 -*-

import click
import sqlalchemy

from h import models


@click.group()
def user():
    """Manage users."""


@user.command()
@click.option('--username', prompt=True)
@click.option('--email', prompt=True)
@click.password_option()
@click.pass_context
def add(ctx, username, email, password):
    """Create a new user."""
    request = ctx.obj['bootstrap']()

    signup_service = request.find_service(name='user_signup')

    user = signup_service.signup(username=username,
                                 email=email,
                                 password=password)
    user.activate()

    try:
        request.tm.commit()
    except sqlalchemy.exc.IntegrityError as err:
        upstream_error = '\n'.join('    ' + line
                                   for line in err.message.split('\n'))
        message = ('could not create user due to integrity constraint.\n\n{}'
                   .format(upstream_error))
        raise click.ClickException(message)

    click.echo("{username} created".format(username=username), err=True)


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
