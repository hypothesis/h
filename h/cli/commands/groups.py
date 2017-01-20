# -*- coding: utf-8 -*-

import click


@click.group()
def groups():
    """Manage groups."""


@groups.command()
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True, help="The authority which the group is associated with")
@click.option('--creator', prompt=True, help="The username of the group's creator")
@click.pass_context
def add_publisher_group(ctx, name, authority, creator):
    """
    Create a new "publisher" group.

    ** This command is intended for dev environments only. **

    This consists of an authority, an admin user and the main group for the
    publisher's annotations.
    """
    request = ctx.obj['bootstrap']()

    creator_userid = u'acct:{username}@{authority}'.format(username=creator,
                                                           authority=authority)
    group_svc = request.find_service(name='group')
    group_svc.create(name=name, authority=authority, userid=creator_userid,
                     type_='publisher')

    request.tm.commit()
