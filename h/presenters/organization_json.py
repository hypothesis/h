class OrganizationJSONPresenter:
    """Present an organization in the JSON format returned by API requests."""

    def __init__(self, organization_context):
        self.context = organization_context
        self.organization = organization_context.organization

    def asdict(self):
        return {
            "id": self.organization.pubid,
            "default": self.organization.is_default,
            "logo": self.context.logo,
            "name": self.organization.name,
        }
