# -*- coding: utf-8 -*-

from h import models
from h.groups import util
from h.models import group


class AuthorityGroupService(object):

    """A service for listing groups under a particular authority."""

    def __init__(self, session, auth_domain):
        """
        Create a new authority group service.

        :param session: the current database session
        :param auth_domain: the authority domain for the current site

        """
        self._session = session
        self._auth_domain = auth_domain

    def public_groups(self, authority):
        if authority == self._auth_domain:
            return [util.WorldGroup(self._auth_domain)]
        else:
            return (self._session.query(models.Group)
                    .filter_by(authority=authority,
                               readable_by=group.ReadableBy.world)
                    .all())


def authority_group_factory(context, request):
    """Return a AuthorityGroupService for the passed context and request."""
    return AuthorityGroupService(session=request.db,
                                 auth_domain=request.auth_domain)
