# -*- coding: utf-8 -*-

import click

from h import models


@click.group()
def authclient():
    """Manage OAuth clients."""


@authclient.command()
@click.option('--name', prompt=True, help="The name of the client")
@click.option('--authority', prompt=True, help="The authority (domain name) for the client")
@click.pass_context
def add(ctx, name, authority):
    """
    Create a new OAuth client.

    Create a new OAuth client for a "publisher" account, which can be used to
    create and manage resources within a given namespace ("authority").
    """
    request = ctx.obj['bootstrap']()

    # Create a new auth client.
    authclient = models.AuthClient(name=name, authority=authority)
    request.db.add(authclient)
    request.db.flush()

    id_ = authclient.id
    secret = authclient.secret

    request.tm.commit()

    click.echo('OAuth client for {authority} created\n'
               'Client ID: {id}\n'
               'Client Secret: {secret}'.format(authority=authority, id=id_,
                                                secret=secret))


@authclient.command()
@click.argument('authority')
@click.pass_context
def secret(ctx, authority):
    """
    Display client ID and secret.

    Display the client ID and secret for making API requests to manage the
    users associated with a publisher.
    """
    request = ctx.obj['bootstrap']()

    authclient = request.db.query(models.AuthClient).filter(
                     models.AuthClient.authority == authority).first()

    if authclient is None:
        msg = 'no publisher with authority "{}" exists'.format(authority)
        raise click.ClickException(msg)

    click.echo('ID: {id}\nSecret: {secret}'
               .format(id=authclient.id, secret=authclient.secret))
