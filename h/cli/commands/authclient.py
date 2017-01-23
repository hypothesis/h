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
