from h.traversal import OrganizationContext


class OrganizationJSONPresenter:
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization, request):
        self.context = OrganizationContext(organization, request)
        self.organization = organization

    def asdict(self):
        return {
            "id": self.organization.pubid,
            "default": self.organization.is_default,
            "logo": self.context.logo_url,
            "name": self.organization.name,
        }
