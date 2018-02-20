# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.models import group
from h._compat import urlparse


class ListGroupsService(object):

    """
    A service for providing filtered lists of groups.

    This service filters groups by user session, scope, etc.

    ALl public methods return a list of relevant group model objects.
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

        Return a list of groups filtered on user and authority. All open
        groups matching the authority will be included.
        """
        all_open_groups = self._open_groups(user, authority)
        private_groups = self._private_groups(user)

        return all_open_groups + private_groups

    def request_groups(self, authority, user=None, document_uri=None):
        """
        Return a list of groups relevant to this request and user combination.

        Return a list of groups filtered on user, authority, document_uri.
        Include all types of relevant groups (open and private).

        Open groups will be filtered by scope (via document_uri).
        """
        scoped_open_groups = self._scoped_open_groups(authority, document_uri)

        world_group = self._world_group(authority)
        world_group = [world_group] if world_group else []

        private_groups = self._private_groups(user)

        return scoped_open_groups + world_group + private_groups

    def _open_groups(self, user=None, authority=None):
        """
        Return all open groups for the authority.
        """

        authority = self._authority(user, authority)
        groups = (self._session.query(models.Group)
                      .filter_by(authority=authority,
                                 readable_by=group.ReadableBy.world)
                      .all())
        return self._sort(groups)

    def _private_groups(self, user=None):
        """Return this user's private groups per user.groups."""

        if user is None:
            return []
        return self._sort(user.groups)

    def _parse_origin(self, uri):
        """
        Return the origin of a URI or None if empty or invalid.

        Per https://tools.ietf.org/html/rfc6454#section-7 :
        Return ``<scheme> + '://' + <host> + <port>``
        for a URI.

        :param uri: URI string
        """

        if uri is None:
            return None
        parsed = urlparse.urlsplit(uri)
        # netloc contains both host and port
        origin = urlparse.SplitResult(parsed.scheme, parsed.netloc, '', '', '')
        return origin.geturl() or None

    def _scoped_open_groups(self, authority, document_uri):
        """Return scoped groups for the URI and authority"""
        origin = self._parse_origin(document_uri)
        if not origin:
            return []

        groups = (self._session.query(models.GroupScope, models.Group)
                      .filter(models.Group.id == models.GroupScope.group_id)
                      .filter(models.GroupScope.origin == origin)
                      .filter(models.Group.authority == authority)
                      .all())

        scoped_groups = [group for groupscope, group in groups]
        return self._sort(scoped_groups)

    def _sort(self, groups):
        """ sort a list of groups of a single type """
        return sorted(groups, key=lambda group: (group.name.lower(), group.pubid))

    def _world_group(self, authority):
        """
        Return the world group for the given authority, if any.

        Return the so-called 'world-readable Public group' (or channel) for
        the indicated authority.

        The Public group is special: at present its metadata makes it look
        identical to any non-scoped open group. Its only distinguishing
        characteristic is its unique and predictable ``pubid``
        """
        return (self._session.query(models.Group)
                    .filter_by(authority=authority,
                               readable_by=group.ReadableBy.world,
                               pubid=u'__world__')
                    .one_or_none())


def list_groups_factory(context, request):
    """Return a ListGroupsService instance for the passed context and request."""
    return ListGroupsService(session=request.db,
                             request_authority=request.authority)
