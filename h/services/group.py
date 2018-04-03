# -*- coding: utf-8 -*-

from functools import partial

import sqlalchemy as sa

from h import session
from h.models import Group, GroupScope, Organization, User
from h.models.group import ReadableBy, OPEN_GROUP_TYPE_FLAGS, PRIVATE_GROUP_TYPE_FLAGS, RESTRICTED_GROUP_TYPE_FLAGS


class GroupService(object):

    """A service for manipulating groups and group membership."""

    def __init__(self, session, user_fetcher, publish):
        """
        Create a new groups service.

        :param session: the SQLAlchemy session object
        :param user_fetcher: a callable for fetching users by userid
        :param publish: a callable for publishing events
        """
        self.session = session
        self.user_fetcher = user_fetcher
        self.publish = publish

    def create_private_group(self, name, userid, description=None):
        """
        Create a new private group.

        A private group is one that only members can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param description: the description of the group

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=PRIVATE_GROUP_TYPE_FLAGS,
                            add_creator_as_member=True,
                            )

    def create_open_group(self, name, userid, origins, description=None):
        """
        Create a new open group.

        An open group is one that anyone in the same authority can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param origins: the list of origins that the group will be scoped to
        :param description: the description of the group

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=OPEN_GROUP_TYPE_FLAGS,
                            origins=origins,
                            add_creator_as_member=False,
                            )

    def create_restricted_group(self, name, userid, origins, description=None):
        """
        Create a new restricted group.

        A restricted group is one that anyone in the same authority can read but
        only members can write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param origins: the list of origins that the group will be scoped to
        :param description: the description of the group

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=RESTRICTED_GROUP_TYPE_FLAGS,
                            origins=origins,
                            add_creator_as_member=True,
                            )

    def member_join(self, group, userid):
        """Add `userid` to the member list of `group`."""
        user = self.user_fetcher(userid)

        if user in group.members:
            return

        group.members.append(user)

        self.publish('group-join', group.pubid, userid)

    def member_leave(self, group, userid):
        """Remove `userid` from the member list of `group`."""
        user = self.user_fetcher(userid)

        if user not in group.members:
            return

        group.members.remove(user)

        self.publish('group-leave', group.pubid, userid)

    def groupids_readable_by(self, user):
        """
        Return a list of pubids for which the user has read access.

        If the passed-in user is ``None``, this returns the list of
        world-readable groups.
        """
        readable = (Group.readable_by == ReadableBy.world)

        if user is not None:
            readable_member = sa.and_(Group.readable_by == ReadableBy.members, Group.members.any(User.id == user.id))
            readable = sa.or_(readable, readable_member)

        return [record.pubid for record in self.session.query(Group.pubid).filter(readable)]

    def groupids_created_by(self, user):
        """
        Return a list of pubids which the user created.

        If the passed-in user is ``None``, this returns an empty list.
        """
        if user is None:
            return []

        return [g.pubid for g in self.session.query(Group.pubid).filter_by(creator=user)]

    def _create(self, name, userid, description, type_flags, origins=[], add_creator_as_member=False):
        """
        Create a group and save it to the DB.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param description: the description of the group
        :param type_flags: the type of this group
        :param origins: the list of origins that the group will be scoped to
        :param add_creator_as_member: if the group creator should be added as a member
        """
        creator = self.user_fetcher(userid)
        scopes = [GroupScope(origin=o) for o in origins]

        group = Group(name=name,
                      authority=creator.authority,
                      creator=creator,
                      description=description,
                      joinable_by=type_flags.joinable_by,
                      readable_by=type_flags.readable_by,
                      writeable_by=type_flags.writeable_by,
                      scopes=scopes,
                      organization=Organization.default(self.session),
                      )
        self.session.add(group)

        if add_creator_as_member:
            group.members.append(group.creator)

            # Flush the DB to generate group.pubid before publish()ing it.
            self.session.flush()

            self.publish('group-join', group.pubid, group.creator.userid)

        return group


def groups_factory(context, request):
    """Return a GroupService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return GroupService(session=request.db,
                        user_fetcher=user_service.fetch,
                        publish=partial(_publish, request))


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user({
        'type': event_type,
        'session_model': session.model(request),
        'userid': userid,
        'group': groupid,
    })
