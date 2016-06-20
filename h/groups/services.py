# -*- coding: utf-8 -*-

from functools import partial

from h import session
from h.accounts import get_user
from h.models import Group


class GroupsService(object):

    """A service for manipulating groups and group membership."""

    def __init__(self, session, user_fetcher, publish=None):
        """
        Create a new groups service.

        :param session: the SQLAlchemy session object
        :param user_fetcher: a callable for fetching users by userid
        :param publish: a callable for publishing events
        """
        self.session = session
        self.user_fetcher = user_fetcher
        self.publish = publish

    def create(self, name, userid):
        """
        Create a new group.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator

        :returns: the created group
        """
        creator = self.user_fetcher(userid)
        group = Group(name=name, creator=creator)
        self.session.add(group)
        self.session.flush()

        if self.publish:
            self.publish('group-join', group.pubid, userid)

        return group

    def member_join(self, group, userid):
        """Add `userid` to the member list of `group`."""
        user = self.user_fetcher(userid)

        if user in group.members:
            return

        group.members.append(user)

        if self.publish:
            self.publish('group-join', group.pubid, userid)

    def member_leave(self, group, userid):
        """Remove `userid` from the member list of `group`."""
        user = self.user_fetcher(userid)

        if user not in group.members:
            return

        group.members.remove(user)

        if self.publish:
            self.publish('group-leave', group.pubid, userid)


def groups_factory(context, request):
    """Return a GroupsService instance for the passed context and request."""
    def user_fetcher(userid):
        return get_user(userid, request)
    return GroupsService(session=request.db,
                         user_fetcher=user_fetcher,
                         publish=partial(_publish, request))


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user({
        'type': event_type,
        'session_model': session.model(request),
        'userid': userid,
        'group': groupid,
    })
