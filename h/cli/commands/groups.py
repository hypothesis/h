# -*- coding: utf-8 -*-

import click


@click.group()
def groups():
    """Manage groups."""


@groups.command()
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True, help="The authority which the group is associated with")
@click.pass_context
def add_publisher_group(ctx, name, authority):
    """
    Create a new "publisher" group.

    ** This command is intended for dev environments only. **

    This consists of an authority, an admin user and the main group for the
    publisher's annotations.
    """
    request = ctx.obj['bootstrap']()

    # Add an admin user for the group. This is needed because groups must
    # currently be associated with a creator.
    signup_service = request.find_service(name='user_signup')
    creator = signup_service.signup(username=u'admin',
                                    email=u'admin@localhost',
                                    authority=authority,
                                    require_activation=False)

    # Add a main group for the publisher's annotations.
    group_svc = request.find_service(name='group')
    group_svc.create(name=name, authority=authority, userid=creator.userid,
                     type_='publisher')

    request.tm.commit()
