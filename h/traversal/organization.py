from h.traversal.root import Root, RootFactory


class OrganizationRoot(RootFactory):
    """Root factory for routes whose context is an `OrganizationContext`."""

    def __getitem__(self, pubid):
        organization = self.request.find_service(name="organization").get_by_public_id(
            pubid
        )
        if organization is None:
            raise KeyError()

        return OrganizationContext(organization, self.request)


class OrganizationContext:
    """Context for organization-based views."""

    def __init__(self, organization, request):
        # Inherit global ACL. See comments in :py:class`h.traversal.AuthClientRoot`.
        self.__parent__ = Root(request)

        self.organization = organization
        self.request = request

    @property
    def logo_url(self):
        if self.organization.logo:
            return self.request.route_url(
                "organization_logo", pubid=self.organization.pubid
            )
        return None
