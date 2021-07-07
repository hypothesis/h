class OrganizationJSONPresenter:
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization, request):
        self.request = request
        self.organization = organization

    def asdict(self, summary=False):
        """
        Create a dict of the organization.

        :param summary: Return the name and logo only (used in activity stream)
        """
        model = {
            "name": self.organization.name,
            "logo": (
                self.request.route_url(
                    "organization_logo", pubid=self.organization.pubid
                )
                if self.organization.logo
                else None
            ),
        }

        if not summary:
            model["id"] = self.organization.pubid
            model["default"] = self.organization.is_default

        return model
