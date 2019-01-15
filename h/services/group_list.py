# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.models import group
from h.util import group_scope as scope_util


class GroupListService(object):

    """
    A service for providing filtered lists of groups.

    This service filters groups by user session, scope, etc.

    ALl public methods return relevant group model objects.
    """

    def __init__(self, session, default_authority):
        """
        Create a new group_list service.

        :param session: the SQLAlchemy session object
        :param default_authority: the authority to use as a default
        """
        self._session = session
        self.default_authority = default_authority

    def _authority(self, user=None, authority=None):
        """Determine which authority to use.

           Determine the appropriate authority to use for querying groups.
           User's authority will always supersede if present; otherwise provide
           default value—request.default_authority—if no authority specified.
        """

        if user is not None:
            return user.authority
        return authority or self.default_authority

    def session_groups(self, authority, user=None):
        """
        Return a list of groups relevant to the user-session combination,
        in this order:

        - WORLD GROUP:
          The special world group is returned if `authority` is the default
          authority
        - ALL USER GROUPS:
          "User groups" here means any group that the user is a member of:
          this can include both private and restricted groups.

        This will return all groups that the session's user is a member of
        regardless of group type or scope. No open groups are returned.

        This should return the list of groups that is appropriate for
        activity pages and/or other views on the h service.
        """

        world_group = self.world_group(authority)
        world_group = [world_group] if world_group else []
        user_groups = self.user_groups(user)

        return world_group + user_groups

    def associated_groups(self, user=None):
        """
        Return a list of groups associated with a user.

        Relevant groups include groups the user is a
        creator/moderator/member of.

        If the user is None it returns an empty list.
        """
        if user is None:
            return []
        world_readable_groups = [
            group
            for group in self._readable_by_world_groups(user, None)
            if group.creator == user or user in group.members
        ]
        private_groups = self.private_groups(user)

        return world_readable_groups + private_groups

    def request_groups(self, authority, user=None, document_uri=None):
        """
        Return a list of groups relevant to this request context.

        Return a list of groups filtered on user, authority, document_uri.
        Groups are returned in this order:

        - OPEN AND RESTRICTED GROUPS:
          Only those open or restricted group that match scope of document_uri
          will be returned (if document_uri is missing, no open or restricted
          groups will be returned)
        - WORLD GROUP:
          The special world group is returned if `authority` is the default
          authority
        - PRIVATE GROUPS:
          All private groups for the user will be returned

          This should return a list of groups appropriate to the client
          via the API.
        """
        scoped_groups = self.scoped_groups(authority, document_uri)

        world_group = self.world_group(authority)
        world_group = [world_group] if world_group else []

        private_groups = self.private_groups(user)

        return scoped_groups + world_group + private_groups

    def user_groups(self, user=None):
        """
        Return a sorted list of a user's groups.

        Return a list of all groups for which the given user is a member of,
        regardless of group type or other considerations. Returned groups will
        be sorted by name.

        The returned list will be empty if no ``user`` is provided.

        :type user: :class:~h.models.user or None
        :rtype: list of :class:`h.models.group`
        """

        if user is None:
            return []
        return self._sort(user.groups)

    def private_groups(self, user=None):
        """
        Return all private groups for this user.

        Retrieve all private groups that this user is a member of. List will
        be empty if no ``user`` provided. Groups will be sorted by name.

        :type user: :class:`~h.models.user`
        :rtype: list of :class:`h.models.group`
        """

        user_groups = self.user_groups(user)
        return [group for group in user_groups if group.type == "private"]

    def scoped_groups(self, authority, document_uri):
        """
        Return scoped groups for the URI and authority

        Only open and restricted groups are "supposed" to have scope, but
        technically this query is agnostic to the group's type—it will return
        any group who has a scope that matches the document_uri's scope.

        Note: If private groups are ever allowed to be scoped, this needs
        attention.

        :param authority: Filter groups by this authority
        :type authority: string
        :arg document_uri: Use this URI to find groups with matching scopes
        :type document_uri: string
        :rtype: list of :class:`h.models.group`
        """
        origin = scope_util.uri_scope(document_uri)
        if not origin:
            return []

        groups = (
            self._session.query(models.GroupScope, models.Group)
            .filter(models.Group.id == models.GroupScope.group_id)
            .filter(models.GroupScope.origin == origin)
            .filter(models.Group.authority == authority)
            .all()
        )

        scoped_groups = [group for groupscope, group in groups]
        return self._sort(scoped_groups)

    def world_group(self, authority):
        """
        Return the world group for the given authority, if any.

        Retrieve the so-called 'world-readable Public group' (or channel) for
        the indicated authority.

        The Public/World group is special: at present its metadata makes it look
        identical to any non-scoped open group. Its only distinguishing
        characteristic is its unique and predictable ``pubid``

        An authority may not have a world group, in which case this will
        return ``None``.

        :type authority: string
        :rtype: :class:`h.models.group` or None
        """
        return (
            self._session.query(models.Group)
            .filter_by(
                authority=authority,
                readable_by=group.ReadableBy.world,
                pubid="__world__",
            )
            .one_or_none()
        )

    def _readable_by_world_groups(self, user=None, authority=None):
        """
        Return all groups readable by world for the authority.
        """

        authority = self._authority(user, authority)
        groups = (
            self._session.query(models.Group)
            .filter_by(authority=authority, readable_by=group.ReadableBy.world)
            .all()
        )
        return self._sort(groups)

    def _sort(self, groups):
        """ sort a list of groups of a single type """
        return sorted(groups, key=lambda group: (group.name.lower(), group.pubid))


def group_list_factory(context, request):
    """Return a GroupListService instance for the passed context and request."""
    return GroupListService(
        session=request.db, default_authority=request.default_authority
    )
