# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from functools import partial

from h import session
from h.models import Group, GroupScope
from h.models.group import (
    OPEN_GROUP_TYPE_FLAGS,
    PRIVATE_GROUP_TYPE_FLAGS,
    RESTRICTED_GROUP_TYPE_FLAGS,
)


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

    def create_private_group(self, name, userid, **kwargs):
        """
        Create a new private group.

        A private group is one that only members can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param kwargs: optional attributes to set on the group, as keyword
            arguments

        :returns: the created group
        """
        return self._create(
            name=name,
            userid=userid,
            type_flags=PRIVATE_GROUP_TYPE_FLAGS,
            scopes=[],
            add_creator_as_member=True,
            **kwargs
        )

    def create_open_group(self, name, userid, scopes, **kwargs):
        """
        Create a new open group.

        An open group is one that anyone in the same authority can read or write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param scopes: the list of URIs that the group will be scoped to
        :type scopes: list(str)
        :param kwargs: optional attributes to set on the group, as keyword
            arguments

        :returns: the created group
        """
        return self._create(
            name=name,
            userid=userid,
            type_flags=OPEN_GROUP_TYPE_FLAGS,
            scopes=scopes,
            add_creator_as_member=False,
            **kwargs
        )

    def create_restricted_group(self, name, userid, scopes, **kwargs):
        """
        Create a new restricted group.

        A restricted group is one that anyone in the same authority can read but
        only members can write.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param scopes: the list of URIs that the group will be scoped to
        :type scopes: list(str)
        :param kwargs: optional attributes to set on the group, as keyword
            arguments

        :returns: the created group
        """
        return self._create(
            name=name,
            userid=userid,
            type_flags=RESTRICTED_GROUP_TYPE_FLAGS,
            scopes=scopes,
            add_creator_as_member=True,
            **kwargs
        )

    def _create(
        self, name, userid, type_flags, scopes, add_creator_as_member, **kwargs
    ):
        """
        Create a group and save it to the DB.

        :param name: the human-readable name of the group
        :param userid: the userid of the group creator
        :param type_flags: the type of this group
        :param scopes: the list of scopes (URIs) that the group will be scoped to
        :type scopes: list(str)
        :param add_creator_as_member: if the group creator should be added as a member
        :param kwargs: optional attributes to set on the group, as keyword
            arguments
        """
        if scopes is None:
            scopes = []

        creator = self.user_fetcher(userid)

        group_scopes = [GroupScope(scope=s) for s in scopes]

        if "organization" in kwargs:
            self._validate_authorities_match(
                creator.authority, kwargs["organization"].authority
            )

        group = Group(
            name=name,
            authority=creator.authority,
            creator=creator,
            joinable_by=type_flags.joinable_by,
            readable_by=type_flags.readable_by,
            writeable_by=type_flags.writeable_by,
            scopes=group_scopes,
            **kwargs
        )
        self.session.add(group)

        if add_creator_as_member:
            group.members.append(group.creator)

            # Flush the DB to generate group.pubid before publish()ing it.
            self.session.flush()

            self.publish("group-join", group.pubid, group.creator.userid)

        return group

    def _validate_authorities_match(self, group_authority, org_authority):
        if group_authority != org_authority:
            raise ValueError(
                "Organization's authority {} must match the group creator's authority {}.".format(
                    org_authority, group_authority
                )
            )


def group_create_factory(context, request):
    """Return a GroupCreateService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return GroupCreateService(
        session=request.db,
        user_fetcher=user_service.fetch,
        publish=partial(_publish, request),
    )


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user(
        {
            "type": event_type,
            "session_model": session.model(request),
            "userid": userid,
            "group": groupid,
        }
    )
