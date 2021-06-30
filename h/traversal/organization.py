from h.traversal.root import Root, RootFactory


class OrganizationRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.OrganizationContext`.

    FIXME: This class should return OrganizationContext objects, not Organization
    objects.
    """

    def __getitem__(self, pubid):
        organization = self.request.find_service(name="organization").get_by_public_id(
            pubid
        )
        if organization is None:
            raise KeyError()

        # Inherit global ACL. See comments in :py:class`h.traversal.AuthClientRoot`.
        organization.__parent__ = Root(self.request)

        return organization


class OrganizationContext:
    """Context for organization-based views."""

    def __init__(self, organization, request):
        # TODO Links service
        self.organization = organization
        self.request = request

    @property
    def logo_url(self):
        if self.organization.logo:
            return self.request.route_url(
                "organization_logo", pubid=self.organization.pubid
            )
        return None
