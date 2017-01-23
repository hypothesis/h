# -*- coding: utf-8 -*-

import click

from h import models


@click.group()
def authclient():
    """Manage OAuth clients."""


@authclient.command()
@click.option('--name', prompt=True, help="The name of the client")
@click.option('--authority', prompt=True, help="The authority (domain name) of the resources managed by the client")
@click.pass_context
def add(ctx, name, authority):
    """
    Create a new OAuth client.
    """
    request = ctx.obj['bootstrap']()

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

    Display the ID and secret for an OAuth client associated with a given
    authority.
    """
    request = ctx.obj['bootstrap']()

    authclient = request.db.query(models.AuthClient).filter(
                     models.AuthClient.authority == authority).first()

    if authclient is None:
        msg = 'no authclient exists for the authority "{}"'.format(authority)
        raise click.ClickException(msg)

    click.echo('ID: {id}\nSecret: {secret}'
               .format(id=authclient.id, secret=authclient.secret))
