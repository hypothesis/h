# -*- coding: utf-8 -*-

from h.accounts import get_user
from h.models import Group


class GroupsService(object):

    """A service for manipulating groups and group membership."""

    def __init__(self, session, user_fetcher):
        self.session = session
        self.user_fetcher = user_fetcher

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

        return group

    def member_join(self, group, userid):
        """Add `userid` to the member list of `group`."""
        user = self.user_fetcher(userid)

        if user not in group.members:
            group.members.append(user)

    def member_leave(self, group, userid):
        """Remove `userid` from the member list of `group`."""
        user = self.user_fetcher(userid)

        if user in group.members:
            group.members.remove(user)


def groups_factory(context, request):
    """Return a GroupsService instance for the passed context and request."""
    def user_fetcher(userid):
        return get_user(userid, request)
    return GroupsService(session=request.db, user_fetcher=user_fetcher)
