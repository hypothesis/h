from pyramid.security import Allow

from h.auth.util import client_authority
from h.security.permissions import Permission
from h.traversal.root import RootFactory


class BulkAPIRoot(RootFactory):
    """Root factory for the Bulk API."""

    def __acl__(self):
        """Return ACL for bulk end-points."""

        if authority := client_authority(self.request):
            # Currently only LMS uses this end-point
            if authority.startswith("lms.") and authority.endswith(".hypothes.is"):
                return [
                    (Allow, f"client_authority:{authority}", Permission.API.BULK_ACTION)
                ]

        return []
