# -*- coding: utf-8 -*-

from functools import partial

from h import session
from h.models import Group
from h.models.group import JoinableBy, ReadableBy, WriteableBy

GROUP_ACCESS_FLAGS = {
    'private': {
        'joinable_by': JoinableBy.authority,
        'readable_by': ReadableBy.members,
        'writeable_by': WriteableBy.members,
     },
    'publisher': {
        'joinable_by': None,
        'readable_by': ReadableBy.world,
        'writeable_by': WriteableBy.authority,
    }
}


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

    def create(self, name, authority, userid, description=None, type_='private'):
        """
        Create a new group.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param description: the description of the group
        :param type_: the type of group (private or publisher) which sets the
                      appropriate access flags

        :returns: the created group
        """
        creator = self.user_fetcher(userid)
        group = Group(name=name,
                      authority=authority,
                      creator=creator,
                      description=description)

        access_flags = GROUP_ACCESS_FLAGS.get(type_)
        if access_flags is None:
            raise ValueError('Invalid group type %s' % type_)
        for attr, value in access_flags.iteritems():
            setattr(group, attr, value)

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
    user_service = request.find_service(name='user')
    return GroupsService(session=request.db,
                         user_fetcher=user_service.fetch,
                         publish=partial(_publish, request))


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user({
        'type': event_type,
        'session_model': session.model(request),
        'userid': userid,
        'group': groupid,
    })
