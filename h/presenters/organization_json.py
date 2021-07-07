class OrganizationJSONPresenter:
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization, request):
        self.request = request
        self.organization = organization

    def asdict(self):
        logo = (
            self.request.route_url("organization_logo", pubid=self.organization.pubid)
            if self.organization.logo
            else None
        )

        return {
            "id": self.organization.pubid,
            "default": self.organization.is_default,
            "logo": logo,
            "name": self.organization.name,
        }
