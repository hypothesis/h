# -*- coding: utf-8 -*-

import click

from h import models
from h.security import token_urlsafe


@click.group()
def authclient():
    """Manage OAuth clients."""


@authclient.command()
@click.option('--name', prompt=True, help="The name of the client")
@click.option('--authority', prompt=True, help="The authority (domain name) of the resources managed by the client")
@click.option('--type', 'type_', type=click.Choice(['public', 'confidential']), prompt=True, help="The OAuth client type (public, or confidential)")
@click.pass_context
def add(ctx, name, authority, type_):
    """
    Create a new OAuth client.
    """
    request = ctx.obj['bootstrap']()

    authclient = models.AuthClient(name=name, authority=authority)
    if type_ == 'confidential':
        authclient.secret = token_urlsafe()
    request.db.add(authclient)
    request.db.flush()

    id_ = authclient.id
    secret = authclient.secret

    request.tm.commit()

    message = ('OAuth client for {authority} created\n'
               'Client ID: {id}')
    if type_ == 'confidential':
        message += '\nClient Secret: {secret}'

    click.echo(message.format(authority=authority, id=id_, secret=secret))
