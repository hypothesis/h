# -*- coding: utf-8 -*-

import click

from h import models


@click.group()
def publisher():
    """Manage publisher accounts."""


@publisher.command()
@click.option('--name', prompt=True, help="The name of the publisher")
@click.option('--authority', prompt=True, help="The authority (domain name) for the publisher")
@click.pass_context
def add(ctx, name, authority):
    """
    Create a new publisher account.

    ** This command is intended for dev environments only. **

    This consists of an authority, an admin user and the main group for the
    publisher's annotations.
    """
    request = ctx.obj['bootstrap']()

    # Create a new auth client.
    authclient = models.AuthClient(name=name, authority=authority)
    request.db.add(authclient)

    # Add an admin user for the publisher's group. This is needed because groups
    # must currently be associated with a creator.
    signup_service = request.find_service(name='user_signup')
    creator = signup_service.signup(username=u'admin',
                                    email=u'admin@localhost',
                                    authority=authority,
                                    require_activation=False)

    # Add a main group for the publisher's annotations.
    group_svc = request.find_service(name='group')
    group_svc.create(name=name, authority=authority, userid=creator.userid,
                     type_='publisher')

    id = authclient.id
    secret = authclient.secret

    request.tm.commit()

    click.echo('Publisher account for {authority} created'.format(authority=authority))
    click.echo('Client ID: {id}\nClient Secret: {secret}'
               .format(id=id, secret=secret))


@publisher.command()
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
