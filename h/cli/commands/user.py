# -*- coding: utf-8 -*-

import click
import sqlalchemy

from h import models


@click.group()
def user():
    """Manage users."""


@user.command()
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--authority")
@click.password_option()
@click.pass_context
def add(ctx, username, email, password, authority):
    """Create a new user."""
    request = ctx.obj["bootstrap"]()

    signup_service = request.find_service(name="user_signup")

    signup_kwargs = {
        "username": username,
        "email": email,
        "password": password,
        "require_activation": False,
    }
    if authority:
        signup_kwargs["authority"] = authority

    signup_service.signup(**signup_kwargs)

    try:
        request.tm.commit()
    except sqlalchemy.exc.IntegrityError as err:
        upstream_error = "\n".join("    " + line for line in err.message.split("\n"))
        message = "could not create user due to integrity constraint.\n\n{}".format(
            upstream_error
        )
        raise click.ClickException(message)

    click.echo("{username} created".format(username=username), err=True)


@user.command()
@click.argument("username")
@click.option("--authority")
@click.option("--on/--off", default=True)
@click.pass_context
def admin(ctx, username, authority, on):
    """
    Make a user an admin.

    You must specify the username of a user which you wish to give
    administrative privileges.
    """
    request = ctx.obj["bootstrap"]()

    if not authority:
        authority = request.default_authority

    user = models.User.get_by_username(request.db, username, authority)
    if user is None:
        msg = 'no user with username "{}" and authority "{}"'.format(
            username, authority
        )
        raise click.ClickException(msg)

    user.admin = on
    request.tm.commit()

    click.echo(
        "{username} is now {status}an administrator".format(
            username=username, status="" if on else "NOT "
        ),
        err=True,
    )


@user.command()
@click.argument("username")
@click.option("--authority")
@click.password_option()
@click.pass_context
def password(ctx, username, authority, password):
    """
    Change user's password.

    You must specify the username of a user whose password you want to change.
    """
    request = ctx.obj["bootstrap"]()

    password_service = request.find_service(name="user_password")

    if not authority:
        authority = request.default_authority

    user = models.User.get_by_username(request.db, username, authority)
    if user is None:
        msg = 'no user with username "{}" and authority "{}"'.format(
            username, authority
        )
        raise click.ClickException(msg)

    password_service.update_password(user, password)
    request.tm.commit()

    click.echo("Password changed for {}".format(username), err=True)


@user.command()
@click.argument("username")
@click.option("--authority")
@click.pass_context
def delete(ctx, username, authority):
    """
    Deletes a user with all their group memberships and annotations.

    You must specify the username of a user to delete.
    """
    request = ctx.obj["bootstrap"]()

    if not authority:
        authority = request.default_authority

    user = models.User.get_by_username(request.db, username, authority)
    if user is None:
        msg = 'no user with username "{}" and authority "{}"'.format(
            username, authority
        )
        raise click.ClickException(msg)

    svc = request.find_service(name="delete_user")
    svc.delete(user)
    request.tm.commit()

    click.echo("User {} deleted.".format(username), err=True)
