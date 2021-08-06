from dataclasses import dataclass

from h.models import Organization
from h.security.acl import ACL
from h.traversal.root import RootFactory


class OrganizationRoot(RootFactory):
    """Root factory for routes which deal with organizations."""

    def __getitem__(self, pubid):
        organization = self.request.find_service(name="organization").get_by_public_id(
            pubid
        )
        if organization is None:
            raise KeyError()

        return OrganizationContext(organization=organization)


@dataclass
class OrganizationContext:
    """Context for organization-based views."""

    organization: Organization = None

    @classmethod
    def __acl__(cls):
        return ACL.for_admin_pages()
