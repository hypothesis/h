from dataclasses import dataclass
from functools import cached_property

from pyramid.request import Request

from h.models import Organization
from h.traversal.root import Root, RootFactory


class OrganizationRoot(RootFactory):
    """Root factory for routes which deal with organizations."""

    def __getitem__(self, pubid):
        organization = self.request.find_service(name="organization").get_by_public_id(
            pubid
        )
        if organization is None:
            raise KeyError()

        return OrganizationContext(request=self.request, organization=organization)


@dataclass
class OrganizationContext:
    """Context for organization-based views."""

    request: Request
    organization: Organization = None

    @cached_property
    def __parent__(self):
        return Root(self.request)
