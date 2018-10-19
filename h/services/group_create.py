# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from functools import partial

from h import session
from h.models import Group, GroupScope
from h.models.group import OPEN_GROUP_TYPE_FLAGS, PRIVATE_GROUP_TYPE_FLAGS, RESTRICTED_GROUP_TYPE_FLAGS


class GroupCreateService(object):

    def __init__(self, session, user_fetcher, publish):
        """
        Create a new GroupCreateService.

        :param session: the SQLAlchemy session object
        :param user_fetcher: a callable for fetching users by userid
        :param publish: a callable for publishing events
        """
        self.session = session
        self.user_fetcher = user_fetcher
        self.publish = publish

    def create_private_group(self, name, userid, description=None, organization=None):
        """
        Create a new private group.

        A private group is one that only members can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param description: the description of the group
        :param organization: the organization that this group belongs to
        :type organization: h.models.Organization

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=PRIVATE_GROUP_TYPE_FLAGS,
                            add_creator_as_member=True,
                            organization=organization,
                            )

    def create_open_group(self, name, userid, origins, description=None, organization=None):
        """
        Create a new open group.

        An open group is one that anyone in the same authority can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param origins: the list of origins that the group will be scoped to
        :param description: the description of the group
        :param organization: the organization that this group belongs to
        :type organization: h.models.Organization

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=OPEN_GROUP_TYPE_FLAGS,
                            origins=origins,
                            add_creator_as_member=False,
                            organization=organization,
                            )

    def create_restricted_group(self, name, userid, origins, description=None, organization=None):
        """
        Create a new restricted group.

        A restricted group is one that anyone in the same authority can read but
        only members can write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param origins: the list of origins that the group will be scoped to
        :param description: the description of the group
        :param organization: the organization that this group belongs to
        :type organization: h.models.Organization

        :returns: the created group
        """
        return self._create(name=name,
                            userid=userid,
                            description=description,
                            type_flags=RESTRICTED_GROUP_TYPE_FLAGS,
                            origins=origins,
                            add_creator_as_member=True,
                            organization=organization,
                            )

    def _create(self, name, userid, description, type_flags,
                origins=None, add_creator_as_member=False, organization=None):
        """
        Create a group and save it to the DB.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param description: the description of the group
        :param type_flags: the type of this group
        :param origins: the list of origins that the group will be scoped to
        :param add_creator_as_member: if the group creator should be added as a member
        :param organization: the organization that this group belongs to
        :type organization: h.models.Organization
        """
        if origins is None:
            origins = []

        creator = self.user_fetcher(userid)
        scopes = [GroupScope(origin=o) for o in origins]
        if organization is not None:
            self._validate_authorities_match(creator.authority, organization.authority)
        group = Group(name=name,
                      authority=creator.authority,
                      creator=creator,
                      description=description,
                      joinable_by=type_flags.joinable_by,
                      readable_by=type_flags.readable_by,
                      writeable_by=type_flags.writeable_by,
                      scopes=scopes,
                      organization=organization,
                      )
        self.session.add(group)

        if add_creator_as_member:
            group.members.append(group.creator)

            # Flush the DB to generate group.pubid before publish()ing it.
            self.session.flush()

            self.publish('group-join', group.pubid, group.creator.userid)

        return group

    def _validate_authorities_match(self, group_authority, org_authority):
        if group_authority != org_authority:
            raise ValueError("Organization's authority {} must match the group creator's authority {}."
                             .format(org_authority, group_authority))


def group_create_factory(context, request):
    """Return a GroupCreateService instance for the passed context and request."""
    user_service = request.find_service(name='user')
    return GroupCreateService(session=request.db,
                              user_fetcher=user_service.fetch,
                              publish=partial(_publish, request))


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user({
        'type': event_type,
        'session_model': session.model(request),
        'userid': userid,
        'group': groupid,
    })
