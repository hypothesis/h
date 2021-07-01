import sqlalchemy.orm

from h.models import Organization
from h.traversal.root import Root, RootFactory


class OrganizationRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.OrganizationContext`.

    FIXME: This class should return OrganizationContext objects, not Organization
    objects.

    """

    def __getitem__(self, pubid):
        try:
            org = self.request.db.query(Organization).filter_by(pubid=pubid).one()

            # Inherit global ACL. See comments in :py:class`h.traversal.AuthClientRoot`.
            org.__parent__ = Root(self.request)

            return org
        except sqlalchemy.orm.exc.NoResultFound:
            raise KeyError()


class OrganizationLogoRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.OrganizationLogoContext`.

    FIXME: This class should return OrganizationLogoContext objects, not
    organization logos.

    """

    def __init__(self, request):
        super().__init__(request)
        self.organization_factory = OrganizationRoot(self.request)

    def __getitem__(self, pubid):
        # This will raise KeyError if the organization doesn't exist.
        organization = self.organization_factory[pubid]

        if not organization.logo:
            raise KeyError()

        return organization.logo


class OrganizationContext:
    """Context for organization-based views."""

    def __init__(self, organization, request):
        # TODO Links service
        self.organization = organization
        self.request = request

    @property
    def links(self):
        # TODO
        return {}

    @property
    def logo(self):
        if self.organization.logo:
            return self.request.route_url(
                "organization_logo", pubid=self.organization.pubid
            )
        return None
