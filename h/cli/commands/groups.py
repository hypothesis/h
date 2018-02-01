# -*- coding: utf-8 -*-

import click


@click.group()
def groups():
    """Manage groups."""


@groups.command('add-open-group')
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True, help="The authority which the group is associated with")
@click.option('--creator', prompt=True, help="The username of the group's creator")
@click.pass_context
def add_open_group(ctx, name, authority, creator):
    """
    Create a new open group.

    Create a new group that everyone can read and any logged-in user belonging
    to the same authority as the group and write to.
    """
    request = ctx.obj['bootstrap']()

    creator_userid = u'acct:{username}@{authority}'.format(username=creator,
                                                           authority=authority)
    group_svc = request.find_service(name='group')
    group_svc.create_open_group(name=name, userid=creator_userid)

    request.tm.commit()
