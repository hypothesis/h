# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models.organization import Organization


class ListOrganizationsService(object):

    """
    A service for providing a list of organizations.
    """

    def __init__(self, session):
        """
        Create a new list_organizations service.

        :param session: the SQLAlchemy session object
        """
        self._session = session

    def organizations(self, authority=None):
        """
        Return a list of organizations filtered on authority and
        sorted by name. If authority is None, return a list of
        all organizations.
        """
        filter_args = {}
        if authority:
            filter_args["authority"] = authority

        return (
            self._session.query(Organization)
            .filter_by(**filter_args)
            .order_by(Organization.name.asc())
            .all()
        )


def list_organizations_factory(context, request):
    """
    Return a ListOrganizationsService instance for the passed
    context.
    """
    return ListOrganizationsService(session=request.db)
