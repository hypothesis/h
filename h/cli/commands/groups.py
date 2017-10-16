# -*- coding: utf-8 -*-

import click
from h.models import User, Group


@click.group()
def groups():
    """Manage groups."""


@groups.command('add-publisher-group')
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True,
              help="The authority which the group is associated with")
@click.option('--creator', prompt=True,
              help="The username of the group's creator")
@click.pass_context
def add_publisher_group(ctx, name, authority, creator):
    """
    Create a new "publisher" group.

    Create a new group which everyone can read but which only users belonging
    to a given authority can write to.
    """
    _create_group('publisher', ctx, name, authority, creator)


@groups.command('add-public-group')
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True,
              help="The authority which the group is associated with")
@click.option('--creator', prompt=True,
              help="The username of the group's creator")
@click.pass_context
def add_public_group(ctx, name, authority, creator):
    """
    Create a new "public" group.

    Create a new group which everyone can read but which only group members can write to.
    """
    _create_group('public', ctx, name, authority, creator)


@groups.command('add-open-group')
@click.option('--name', prompt=True, help="The name of the group")
@click.option('--authority', prompt=True,
              help="The authority which the group is associated with")
@click.option('--creator', prompt=True,
              help="The username of the group's creator")
@click.pass_context
def add_open_group(ctx, name, authority, creator):
    """
    Create a new "open" group.

    Create a new group which everyone can read and any logged-in user can write to
    """
    _create_group('open', ctx, name, authority, creator)


def _create_group(type, ctx, name, authority, creator):
    """
    Create a group using group service
    """
    request = ctx.obj['bootstrap']()

    creator_userid = u'acct:{username}@{authority}'.format(username=creator,
                                                           authority=authority)
    group_svc = request.find_service(name='group')
    group_svc.create(name=name, authority=authority, userid=creator_userid,
                     type_=type)

    request.tm.commit()


@groups.command('join')
@click.option('--user', prompt=True, help="username of user to add to a group")
@click.option('--authority', prompt=True,
              help="authority of user to add to group")
@click.option('--group', prompt=True, help="pubid of group to add to")
@click.pass_context
def join(ctx, user, authority, group):
    """
    join a user to a group
    """
    group_id = group
    request = ctx.obj['bootstrap']()

    user = User.get_by_username(request.db, user, authority)
    if not user:
        raise ValueError('Could not find user {0}@{1}'.format(user, authority))

    group = request.db.query(Group).filter_by(pubid=group_id).one_or_none()
    if not group:
        raise ValueError(
            'Could not find group with pubid={0}'.format(group_id))

    groups_service = request.find_service(name='group')
    groups_service.member_join(group, user.userid)

    request.tm.commit()
