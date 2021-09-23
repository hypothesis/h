from dataclasses import dataclass

from h.models import Organization


@dataclass
class OrganizationContext:
    """Context for organization-based views."""

    organization: Organization = None


class OrganizationRoot:
    """Root factory for routes which deal with organizations."""

    def __init__(self, request):
        self.request = request

    def __getitem__(self, pubid):
        organization = self.request.find_service(name="organization").get_by_public_id(
            pubid
        )
        if organization is None:
            raise KeyError()

        return OrganizationContext(organization=organization)
