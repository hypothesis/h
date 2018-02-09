# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.models import group


class ListGroupsService(object):

    """
    A service for providing filtered lists of groups.

    This service filters groups by user session, scope, etc.

    ALl public methods return a list of relevant groups,
    as dicts (see _group_model) for consumption by e.g. API services.
    """

    def __init__(self, session, request_authority):
        """
        Create a new list_groups service.

        :param _session: the SQLAlchemy session object
        :param _request_authority: the authority to use as a default
        """
        self._session = session
        self.request_authority = request_authority

    def _authority(self, user=None, authority=None):
        """Determine which authority to use.

           Determine the appropriate authority to use for querying groups.
           User's authority will always supersede if present; otherwise provide
           default value—request.authority—if no authority specified.
        """

        if user is not None:
            return user.authority
        return authority or self.request_authority

    def all_groups(self, user=None, authority=None, document_uri=None):
        """
        Return a list of groups relevant to this session/profile (i.e. user).

        Return a list of groups filtered on user, authority, document_uri.
        Include all types of relevant groups (open and private).
        """
        open_groups = self.open_groups(user, authority, document_uri)
        private_groups = self.private_groups(user)

        return open_groups + private_groups

    def open_groups(self, user=None, authority=None, document_uri=None):
        """
        Return all matching open groups for the authority and target URI.

        Return matching open groups for the authority (or request_authority
        default), filtered by scope as per ``document_uri``.
        """

        authority = self._authority(user, authority)
        # TODO This is going to change once scopes and model updates in place
        groups = (self._session.query(models.Group)
                      .filter_by(authority=authority,
                                 readable_by=group.ReadableBy.world)
                      .all())
        return self._sort(groups)

    def private_groups(self, user=None):
        """Return this user's private groups per user.groups."""

        if user is None:
            return []
        return self._sort(user.groups)

    def _sort(self, groups):
        """ sort a list of groups of a single type """
        return sorted(groups, key=lambda group: (group.name.lower(), group.pubid))


def list_groups_factory(context, request):
    """Return a ListGroupsService instance for the passed context and request."""
    return ListGroupsService(session=request.db,
                             request_authority=request.authority)
