# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h.models import Organization


class OrganizationService(object):

    """A service for manipulating organizations."""

    def __init__(self, session):
        """
        Create a new organizations service.

        :param session: the SQLAlchemy session object
        """
        self.session = session

    def create(self, name, authority, logo=None):
        """
        Create a new organization.

        An organization is a group of groups.

        :param name: the human-readable name of the organization
        :param authority: the authority to which the organization belongs
        :param logo: the logo of the organization in svg format

        :returns: the created organization
        """
        organization = Organization(name=name, authority=authority, logo=logo)
        self.session.add(organization)
        return organization


def organization_factory(context, request):
    """Return a OrganizationService instance for the request."""
    return OrganizationService(session=request.db)
