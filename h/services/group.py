# -*- coding: utf-8 -*-

from functools import partial

import sqlalchemy as sa

from h import session
from h.models import Annotation, Group, User
from h.models.group import JoinableBy, ReadableBy, WriteableBy


def authority_is_primary_for_request(request, authority):
    """is the provided authority the one we'd consider the "hypothes.is" authority in production?"""
    return request.domain == authority


GROUP_TYPES = {
    'private': {
        'description': 'Anyone can join. Members can read/write.',
        'creator_is_immediate_member': True
    },
    'publisher': {
        'description': 'Anyone can read. Anyone in authority can write. Intended for 3rd-party namespaces.',
        'creator_is_immediate_member': False,
        'matches_request': lambda group, request: not authority_is_primary_for_request(request, group.authority),
    },
    'public': {
        'description': 'Anyone can read. Members can write. Group creator can invite members.',
        'creator_is_immediate_member': True
    },
    'open': {
        'description': 'Anyone can read. Anyone in authority can write. Intended for h namespace.',
        'creator_is_immediate_member': True,
        'matches_request': lambda group, request: authority_is_primary_for_request(request, group.authority),
    }
}

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
    },
    # https://docs.google.com/document/d/1tsyUGDfLLaQsa4Pmc-loHRcYCIe4Q56meery6Be6CoA/edit#heading=h.ge43xo9poyis
    'public': {
        'joinable_by': None,
        'readable_by': ReadableBy.world,
        'writeable_by': WriteableBy.members,
    },
    'open': {
        'joinable_by': None,
        'readable_by': ReadableBy.world,
        'writeable_by': WriteableBy.authority,
    }
}


def get_group_type(group, request=None):
    """given a Group, try to figure out what 'type' it is"""
    for group_type_name, access_flags in GROUP_ACCESS_FLAGS.items():
        has_correct_access_flags = all((getattr(group, field) == value) for (
            field, value) in access_flags.items())
        if not has_correct_access_flags:
            continue
        # has correct access flags for this group_type_name
        # some group types (open/publisher) can only be discriminated based on an incomig web request
        matches_request = GROUP_TYPES.get(
            group_type_name, {}).get('matches_request')
        if request and callable(matches_request):
            if not matches_request(group, request):
                continue
        return group_type_name
    return None


class GroupService(object):

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

        if GROUP_TYPES[type_].get('creator_is_immediate_member'):
            group.members.append(creator)

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

    def groupids_readable_by(self, user):
        """
        Return a list of pubids for which the user has read access.

        If the passed-in user is ``None``, this returns the list of
        world-readable groups.
        """
        readable = (Group.readable_by == ReadableBy.world)

        if user is not None:
            readable_member = sa.and_(
                Group.readable_by == ReadableBy.members, Group.members.any(User.id == user.id))
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
